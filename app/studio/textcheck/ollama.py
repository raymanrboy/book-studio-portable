"""The model on this computer: Ollama answers on 127.0.0.1 only (the pictures never leave the computer) — is it
there, is the model installed and in the graphics card, one call to it, letting it go after a check."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .. import core, portable
from ..jobs import UserError


DEFAULT_MODEL = core.DEFAULT_SETTINGS["textcheck"]["model"]  # gemma4:12b-it-qat — an emptied setting falls back to it
DEFAULT_URL = core.DEFAULT_SETTINGS["textcheck"]["url"]

KEEP_ALIVE = "2m"        # a fallback: the model is let go right after each check (_release_model())
# The same options on every call: another context size would make Ollama load the model again.
OPTIONS = {"temperature": 0, "num_ctx": 8192}

CALL_TIMEOUT = 300       # a call may also load the model: ~4 s from memory, ~70 s from disk
PROBE_TIMEOUT = 1.0      # "is Ollama there": on Windows a refused connection takes 2 s to say so


class ModelError(UserError):
    """Ollama or the model failed; the text says what to do."""


class Unavailable(ModelError):
    """Ollama does not answer at all."""


class TimedOut(ModelError):
    """The model took longer than CALL_TIMEOUT — asking again would only wait as long once more."""


_NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _base() -> str:
    url = (portable.ollama_url() or str(core.settings.section("textcheck").get("url") or DEFAULT_URL)).rstrip("/")
    if (urllib.parse.urlsplit(url).hostname or "") not in ("127.0.0.1", "localhost", "::1"):
        raise ModelError("Перевірка тексту працює лише з моделлю на цьому комп'ютері (адреса 127.0.0.1).")
    return url


def _call(path: str, body: dict | None = None, timeout: float = 10) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(_base() + path, data=data, method="POST" if data is not None else "GET",
                                 headers={"Content-Type": "application/json"})
    try:
        with _NO_PROXY.open(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as err:
        try:
            detail = str(json.loads(err.read().decode("utf-8")).get("error") or "")
        except Exception:
            detail = ""
        finally:
            err.close()
        raise ModelError(f"Ollama відповіла помилкою {err.code}" + (f": {detail}" if detail else "") + ".") from None
    except TimeoutError:
        raise TimedOut("Модель не відповіла вчасно.") from None
    except (urllib.error.URLError, ConnectionError, OSError) as err:
        if isinstance(getattr(err, "reason", None), TimeoutError):
            raise TimedOut("Модель не відповіла вчасно.") from None
        raise Unavailable("Ollama не запущена.") from None


def _settings() -> dict:
    s = core.settings.section("textcheck")
    return {"enabled": bool(s.get("enabled", True)), "model": str(s.get("model") or DEFAULT_MODEL),
            "prescan": bool(s.get("prescan", True))}


def _same_model(a: str, b: str) -> bool:
    return a == b or a.removesuffix(":latest") == b.removesuffix(":latest")


def _ollama_command(hidden: bool = False) -> list[str] | None:
    """How to start Ollama the way the Start menu does: its tray app next to ollama.exe on PATH. In the portable copy only its own
    `runtime/Ollama/ollama.exe serve` — never the PC's. `hidden` (the start with the program): never the tray app — it shows its
    icon and its helpers open black windows (19.10.2026); only `ollama.exe serve`, which nothing of it shows."""
    if portable.root():
        exe = (portable.ollama_folder() or Path()) / "ollama.exe"
        return [str(exe), "serve"] if portable.ollama_folder() and exe.is_file() else None
    found = shutil.which("ollama")
    folders = [portable.ollama_folder()] if portable.ollama_folder() else []
    folders += [Path(found).parent] if found else []
    if os.environ.get("LOCALAPPDATA"):
        folders.append(Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Ollama")
    for folder in folders:
        if not hidden and (folder / "ollama app.exe").is_file():
            return [str(folder / "ollama app.exe")]
        if hidden and (folder / "ollama.exe").is_file():
            return [str(folder / "ollama.exe"), "serve"]
    return [found, "serve"] if found else None


def _alive() -> bool:
    try:
        _call("/api/version", timeout=PROBE_TIMEOUT)
        return True
    except ModelError:
        return False


_start_lock = threading.Lock()
_starting = False        # Ollama is being started right now: the interface says so instead of staying silent


def starting() -> bool:
    return _starting


def start_ollama(wait: float = 40, hidden: bool = False) -> bool:
    """Starts Ollama when it is not running (it stays running after Book Studio closes, like from the
    Start menu). False when it is not installed or did not answer in time. Under a lock: the warm-up and
    the check can both notice it missing at the same moment, and it must be started only once. Never on made-up or test
    data (`core.SANDBOX`): the test run once started the PC's own Ollama (19.10.2026) — one already running is still used."""
    if _alive():
        return True
    if core.SANDBOX:
        return False
    with _start_lock:
        global _starting
        _starting = True
        try:
            return _alive() or _start_ollama(wait, hidden)
        finally:
            _starting = False


def _start_ollama(wait: float, hidden: bool = False) -> bool:
    command = _ollama_command(hidden)
    if not command:
        return False
    if portable.root():
        (portable.ollama_folder() / "models").mkdir(exist_ok=True)      # its models go here, nowhere else
    # No console window: with DETACHED_PROCESS every helper process Ollama spawns opened its own black window (it blinked).
    # CREATE_NO_WINDOW gives them all one hidden console to inherit.
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        subprocess.Popen(command, cwd=str(Path(command[0]).parent), creationflags=flags, close_fds=True,
                         env={**os.environ, **portable.env()},
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        core.log.exception("Ollama did not start")
        return False
    core.log.info("Ollama started: %s", command[0])
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        if _alive():
            return True
        time.sleep(0.5)
    return False


def _names(path: str) -> list[str]:
    """What Ollama lists: the installed models (`/api/tags`) or the ones in the graphics card (`/api/ps`)."""
    return [m.get("name") or "" for m in _call(path, timeout=5).get("models") or []]


def _has(names: list[str], model: str) -> bool:
    return any(_same_model(n, model) for n in names)


def status() -> dict:
    """For Settings and the order card: is the check on, does Ollama answer, is the model there."""
    out = {**_settings(), "running": False, "version": None, "models": [], "installed": False, "loaded": False,
           "canStart": bool(_ollama_command()), "starting": _starting}
    try:
        out["version"] = _call("/api/version", timeout=PROBE_TIMEOUT).get("version")
        out["running"] = True
        tags = _call("/api/tags", timeout=5).get("models") or []
        out["models"] = [m.get("name") for m in tags if "vision" in (m.get("capabilities") or ["vision"])]
        out["installed"] = _has(out["models"], out["model"])
        out["loaded"] = _has(_names("/api/ps"), out["model"])
    except ModelError:
        pass
    return out


def _ready(model: str, say) -> None:
    """Ollama running (started when needed), the model installed and loaded into the graphics card."""
    if not _alive():
        say("Запуск Ollama…")
        if not start_ollama(hidden=True):        # started by the program itself: nothing of it is seen (19.10.2026)
            raise Unavailable("Ollama не запущена і не запустилась сама — запустіть її з меню «Пуск».")
    if not _has(_names("/api/tags"), model):
        raise ModelError(f"В Ollama немає моделі {model} — встановіть її або оберіть іншу в Налаштуваннях.")
    if not _has(_names("/api/ps"), model):
        say("Модель завантажується у відеокарту…")
        _call("/api/chat", {"model": model, "messages": [], "keep_alive": KEEP_ALIVE, "options": OPTIONS},
              timeout=CALL_TIMEOUT)


def _chat(model: str, prompt: str, picture: str, schema: dict | None = None, max_tokens: int | None = None) -> str:
    options = {**OPTIONS, **({"num_predict": max_tokens} if max_tokens else {})}
    body = {"model": model, "stream": False, "think": False, "keep_alive": KEEP_ALIVE, "options": options,
            "messages": [{"role": "user", "content": prompt, "images": [picture]}]}
    if schema:
        body["format"] = schema
    return str((_call("/api/chat", body, timeout=CALL_TIMEOUT).get("message") or {}).get("content") or "")


def _release_model(model: str) -> None:
    """Frees the graphics card right after the check (19.09.2026: the model held 9 GB of 12 for five more minutes
    and the Book Studio window, drawn by the same card, lost smoothness). Loading it again takes ~4 s."""
    try:
        _call("/api/generate", {"model": model, "keep_alive": 0}, timeout=10)
    except ModelError:
        pass  # KEEP_ALIVE lets it go a little later anyway
