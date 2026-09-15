"""Local HTTP server: routing, security checks, static files and JSON helpers.

Binds to 127.0.0.1 only. Every /api call must carry the per-launch session
token (X-Studio-Token header); media URLs carry it as ?t=. The Host header is
checked to block DNS-rebinding attacks from web pages.
"""
from __future__ import annotations

import json
import mimetypes
import re
import secrets
import shutil
import threading
import time
import traceback
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from . import core
from .httpc import HttpError
from .jobs import JobError, UserError, jobs

SESSION_TOKEN = secrets.token_urlsafe(24)
MAX_JSON_BYTES = 25 * 1024 * 1024

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("image/webp", ".webp")


class ApiError(UserError):
    def __init__(self, message: str, status: int = 400, extra: dict | None = None):
        super().__init__(message)
        self.status = status
        self.extra = extra or {}


class Response:
    def __init__(self, status: int = 200, body: bytes = b"", content_type: str = "application/json; charset=utf-8",
                 headers: dict | None = None, file: Path | None = None):
        self.status = status
        self.body = body
        self.content_type = content_type
        self.headers = headers or {}
        self.file = file


def json_response(obj: Any, status: int = 200) -> Response:
    return Response(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"))


def file_response(path: Path, content_type: str | None = None, cache: str = "no-cache") -> Response:
    ctype = content_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return Response(200, content_type=ctype, headers={"Cache-Control": cache}, file=path)


def html_response(text: str, status: int = 200) -> Response:
    return Response(status, text.encode("utf-8"), "text/html; charset=utf-8", {"Cache-Control": "no-store"})


def redirect(location: str) -> Response:
    return Response(302, b"", headers={"Location": location})


Handler = Callable[["Request"], Any]
ROUTES: list[tuple[str, re.Pattern, Handler, str]] = []


def route(method: str, pattern: str, auth: str = "token"):
    """auth: 'token' (API header), 'media' (?t= query), 'none' (browser callbacks)."""
    def deco(fn: Handler) -> Handler:
        ROUTES.append((method.upper(), re.compile("^" + pattern + "$"), fn, auth))
        return fn
    return deco


class Request:
    def __init__(self, handler: "_Handler", method: str, path: str, query: dict, groups: tuple):
        self.handler = handler
        self.method = method
        self.path = path
        self.query = query
        self.groups = groups
        self._json: Any = None
        self._json_loaded = False

    @property
    def headers(self):
        return self.handler.headers

    def param(self, name: str, default: str | None = None) -> str | None:
        values = self.query.get(name)
        return values[0] if values else default

    def content_length(self) -> int:
        try:
            return int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return 0

    @property
    def json(self) -> Any:
        if not self._json_loaded:
            self._json_loaded = True
            length = self.content_length()
            if length > MAX_JSON_BYTES:
                raise ApiError("Запит завеликий.", 413)
            raw = self.handler.rfile.read(length) if length else b""
            self.handler.body_read += len(raw)
            if raw:
                try:
                    self._json = json.loads(raw.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    raise ApiError("Некоректний JSON у запиті.")
            else:
                self._json = {}
        return self._json

    def body_to_file(self, target: Path, max_bytes: int) -> int:
        length = self.content_length()
        if length <= 0:
            raise ApiError("Порожній файл.")
        if length > max_bytes:
            raise ApiError(f"Файл завеликий (максимум {max_bytes // (1024 * 1024)} МБ).", 413)
        target.parent.mkdir(parents=True, exist_ok=True)
        remaining = length
        with open(target, "wb") as f:
            while remaining > 0:
                chunk = self.handler.rfile.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
                self.handler.body_read += len(chunk)
        if remaining:
            target.unlink(missing_ok=True)
            raise ApiError("Файл передано не повністю.")
        return length


class _State:
    port = core.DEFAULT_PORT
    wanted_port = core.DEFAULT_PORT  # differs from `port` when another program held it at start-up
    last_heartbeat = 0.0
    bye_at = 0.0


state = _State()


def _index_html() -> bytes:
    text = (core.WEB_DIR / "index.html").read_text(encoding="utf-8")
    return text.replace("__STUDIO_TOKEN__", SESSION_TOKEN).encode("utf-8")


class _Handler(BaseHTTPRequestHandler):
    server_version = "BookStudio"
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args) -> None:  # silence default stderr logging
        pass

    # ------------------------------------------------------------ dispatch
    def do_GET(self): self._dispatch("GET")
    def do_POST(self): self._dispatch("POST")
    def do_PUT(self): self._dispatch("PUT")
    def do_PATCH(self): self._dispatch("PATCH")
    def do_DELETE(self): self._dispatch("DELETE")

    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").lower()
        return host in (f"127.0.0.1:{state.port}", f"localhost:{state.port}")

    def _drain_body(self) -> None:
        """Keep-alive safety: unread request bodies would corrupt the next request."""
        try:
            remaining = int(self.headers.get("Content-Length") or 0) - self.body_read
        except ValueError:
            remaining = 0
        if remaining > 0 and remaining <= 64 * 1024 * 1024:
            while remaining > 0:
                chunk = self.rfile.read(min(remaining, 1024 * 1024))
                if not chunk:
                    break
                remaining -= len(chunk)
        elif remaining > 0:
            self.close_connection = True

    def _dispatch(self, method: str) -> None:
        self.body_read = 0
        parsed = urllib.parse.urlsplit(self.path)
        path = urllib.parse.unquote(parsed.path)
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        try:
            if not self._host_ok():
                raise ApiError("Forbidden host", 403)
            response = self._route(method, path, query)
        except ApiError as err:
            response = json_response({"error": str(err), **err.extra}, err.status)
        except JobError as err:
            response = json_response({"error": str(err)}, 409)
        except HttpError as err:
            response = json_response({"error": str(err)}, 502)
        except Exception as err:
            core.log.error("Unhandled error on %s %s:\n%s", method, path, traceback.format_exc())
            response = json_response({"error": f"Внутрішня помилка: {err}"}, 500)
        self._drain_body()
        self._send(response)

    def _route(self, method: str, path: str, query: dict) -> Response:
        if method == "GET" and path in ("/", "/index.html"):
            return Response(200, _index_html(), "text/html; charset=utf-8", {"Cache-Control": "no-store"})
        if method == "GET" and re.match(r"^/(css|js|img|fonts)/", path):
            return self._static(path)
        if method == "GET" and path == "/favicon.ico":
            return self._static("/img/icon.ico")

        path_matched = False
        for r_method, pattern, fn, auth in ROUTES:
            m = pattern.match(path)
            if not m:
                continue
            path_matched = True
            if r_method != method:
                continue
            if auth == "token" and self.headers.get("X-Studio-Token") != SESSION_TOKEN:
                raise ApiError("Сесію не підтверджено. Перезапустіть програму.", 401)
            if auth == "media" and (query.get("t") or [""])[0] != SESSION_TOKEN:
                raise ApiError("Forbidden", 403)
            result = fn(Request(self, method, path, query, m.groups()))
            if isinstance(result, Response):
                return result
            return json_response(result if result is not None else {"ok": True})
        if path_matched:
            raise ApiError("Метод не підтримується.", 405)
        raise ApiError("Не знайдено.", 404)

    def _static(self, path: str) -> Response:
        target = (core.WEB_DIR / path.lstrip("/")).resolve()
        if core.WEB_DIR.resolve() not in target.parents or not target.is_file():
            raise ApiError("Не знайдено.", 404)
        return file_response(target, cache="no-cache")

    # ------------------------------------------------------------ output
    def _send(self, response: Response) -> None:
        try:
            headers = dict(response.headers)
            body = response.body
            if response.file is not None:
                stat = response.file.stat()
                etag = f'"{stat.st_mtime_ns:x}-{stat.st_size:x}"'
                headers.setdefault("ETag", etag)
                if self.headers.get("If-None-Match") == etag:
                    self.send_response(304)
                    for k, v in headers.items():
                        self.send_header(k, v)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                length = stat.st_size
            else:
                length = len(body)
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            for k, v in headers.items():
                self.send_header(k, v)
            self.end_headers()
            if self.command == "HEAD":
                return
            if response.file is not None:
                with open(response.file, "rb") as f:
                    shutil.copyfileobj(f, self.wfile, 1024 * 256)
            elif body:
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass


class StudioServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False


def start(port: int) -> StudioServer:
    state.wanted_port = port
    try:
        httpd = StudioServer(("127.0.0.1", port), _Handler)
    except OSError:
        core.log.warning("Port %s is busy — using a random free port", port)
        httpd = StudioServer(("127.0.0.1", 0), _Handler)
    state.port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, name="http", daemon=True).start()
    core.log.info("Server listening on 127.0.0.1:%s", state.port)
    return httpd


def base_url() -> str:
    return f"http://127.0.0.1:{state.port}"


# ---------------------------------------------------------------- app lifecycle routes

@route("GET", "/api/ping", auth="none")
def _ping(req: Request):
    return {"app": core.APP_NAME, "version": core.APP_VERSION}


@route("POST", "/api/app/heartbeat")
def _heartbeat(req: Request):
    state.last_heartbeat = time.time()
    state.bye_at = 0.0
    return {"ok": True}


@route("POST", "/api/app/bye", auth="none")
def _bye(req: Request):
    # sendBeacon cannot set headers; the token travels in the body instead.
    try:
        payload = req.json if isinstance(req.json, dict) else {}
    except ApiError:
        payload = {}
    if payload.get("t") == SESSION_TOKEN:
        state.bye_at = time.time()
    return {"ok": True}


@route("GET", r"/api/jobs/([0-9a-f]{12})")
def _job(req: Request):
    job = jobs.get(req.groups[0])
    if not job:
        raise ApiError("Задачу не знайдено (програму могли перезапустити).", 404)
    return job.snapshot()
