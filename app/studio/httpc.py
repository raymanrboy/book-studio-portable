"""Minimal HTTPS client (stdlib) with retries and readable errors."""
from __future__ import annotations

import http.client
import json
import logging
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from logging.handlers import RotatingFileHandler
from typing import Any

from . import core

USER_AGENT = f"BookStudio/{core.APP_VERSION} (+local desktop tool)"
RETRY_STATUSES = (429, 500, 502, 503, 504)


class HttpError(Exception):
    def __init__(self, message: str, status: int | None = None, body: str = "", url: str = "", ambiguous: bool = False):
        super().__init__(message)
        self.status = status
        self.body = body
        self.url = url
        # True when the request may have done its work on the server anyway: the connection dropped or timed
        # out after sending, or the server failed on its own side (5xx) — a "create" may exist all the same.
        self.ambiguous = ambiguous


class Listing(list):
    """Everything a paged list call returned. `complete` is False when it stopped at its cap: the oldest items
    are then missing, and an item's absence from the list proves nothing."""
    complete = True


# The request never reached the server: nothing can have been done there, so trying again is always safe.
_NOT_SENT = (ConnectionRefusedError, socket.gaierror)


_audit_ready = threading.Lock()


def audit_log(name: str, file: str) -> logging.Logger:
    """A printer's own journal of every call (logs/<file>): what was asked, what was refused."""
    log = logging.getLogger(name)
    with _audit_ready:
        if not log.handlers:
            core.data_path("logs").mkdir(parents=True, exist_ok=True)
            h = RotatingFileHandler(core.data_path("logs", file), maxBytes=2_000_000, backupCount=3, encoding="utf-8")
            h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
            log.addHandler(h)
    return log


def request(
    method: str,
    url: str,
    *,
    headers: dict | None = None,
    json_body: Any = None,
    form: dict | None = None,
    json_bytes: bytes | None = None,
    timeout: float = 60,
    retries: int = 3,
    idempotent: bool | None = None,
) -> tuple[int, bytes]:
    """A request, tried up to `retries` times. A request that changes something (POST) is tried again only
    when it certainly did nothing: never after a timeout or a server-side failure, which could make the same
    thing twice. `idempotent=True` marks a POST that only reads (a search, a token refresh)."""
    if idempotent is None:
        idempotent = method.upper() in ("GET", "HEAD", "PUT", "DELETE", "OPTIONS")
    body: bytes | None = None
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    hdrs.update(headers or {})
    if json_bytes is not None:  # JSON already encoded (an upload's picture: not copied once more here)
        body = json_bytes
        hdrs["Content-Type"] = "application/json; charset=utf-8"
    elif json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        hdrs["Content-Type"] = "application/json; charset=utf-8"
    elif form is not None:
        body = urllib.parse.urlencode(form).encode("utf-8")
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"

    delay = 1.5
    last_error: HttpError | None = None
    for attempt in range(1, max(1, retries) + 1):
        req = urllib.request.Request(url, data=body, headers=hdrs, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as err:
            text = ""
            try:
                text = err.read().decode("utf-8", "replace")
            except Exception:
                pass
            finally:
                err.close()  # the reply's connection goes now, not whenever the error is collected
            # 503 and 429 say the request was turned away; 500/502/504 may come after the work was done.
            ambiguous = err.code >= 500 and err.code != 503
            last_error = HttpError(f"HTTP {err.code}", status=err.code, body=text, url=url, ambiguous=ambiguous)
            if err.code in RETRY_STATUSES and attempt < retries and (idempotent or not ambiguous):
                wait = delay
                if err.code == 429:
                    try:
                        wait = max(wait, float(err.headers.get("Retry-After", "5")))
                    except ValueError:
                        wait = 5
                time.sleep(min(wait, 30))
                delay *= 2
                continue
            raise last_error from None
        # Everything else a connection can do: refused, dropped, timed out, or a reply cut short while it was read
        # (IncompleteRead, an SSL error) — the last ones after the server may have done its work.
        except (http.client.HTTPException, OSError) as err:
            reason = getattr(err, "reason", err)
            ambiguous = not isinstance(reason, _NOT_SENT)
            last_error = HttpError(f"Немає з'єднання: {reason}", url=url, ambiguous=ambiguous)
            if attempt < retries and (idempotent or not ambiguous):
                time.sleep(delay)
                delay *= 2
                continue
            raise last_error from None
    raise last_error or HttpError("Запит не виконано", url=url)


def request_json(method: str, url: str, **kwargs) -> Any:
    status, raw = request(method, url, **kwargs)
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as err:
        raise HttpError(f"Сервер повернув некоректну відповідь ({status})", status=status, url=url) from err


def short_body(text: str, limit: int = 400) -> str:
    text = (text or "").strip().replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + "…"


def human(err: HttpError, service: str, action: str, credential: str, code: str) -> tuple[str, int, dict]:
    """A failed call to a printer in the owner's words — the same reading for Printify and Gelato: the message,
    the status for the page, and extras: "upstream" (the printer's status) and "ambiguous" (the call may have
    done its work anyway — a draft or an order may exist, so it must not simply be sent again)."""
    body = short_body(err.body)
    extra = {"upstream": err.status, "ambiguous": err.ambiguous}
    if err.status == 401:
        return f"{action}: {credential} {service} недійсний або прострочений.", 400, {**extra, "code": code}
    if err.status == 403:
        return f"{action}: {credential} {service} не має потрібних прав.", 400, {**extra, "code": code}
    if err.status == 404:
        return f"{action}: {service} не знайшов об'єкт (404).", 404, extra
    if err.status == 429:
        return f"{action}: перевищено ліміт запитів {service}, спробуйте пізніше.", 429, extra
    if err.status is None:
        return f"{action}: немає з'єднання з {service}. Перевірте інтернет.", 502, extra
    if err.status < 500:
        return f"{action}: {service} відхилив дані ({err.status}). {body}", 400, extra
    return f"{action}: {service} повернув помилку {err.status}. {body}", 502, extra
