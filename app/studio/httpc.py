"""Minimal HTTPS client (stdlib) with retries and readable errors."""
from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
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
        # True when the request may have reached the server (timeout / dropped connection).
        self.ambiguous = ambiguous


def request(
    method: str,
    url: str,
    *,
    headers: dict | None = None,
    json_body: Any = None,
    form: dict | None = None,
    timeout: float = 60,
    retries: int = 3,
) -> tuple[int, bytes]:
    body: bytes | None = None
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    hdrs.update(headers or {})
    if json_body is not None:
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
            last_error = HttpError(f"HTTP {err.code}", status=err.code, body=text, url=url)
            if err.code in RETRY_STATUSES and attempt < retries:
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
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as err:
            reason = getattr(err, "reason", err)
            last_error = HttpError(f"Немає з'єднання: {reason}", url=url, ambiguous=True)
            if attempt < retries:
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
