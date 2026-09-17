"""Journal of every send to a print service: one JSON file per attempt in data/logs/sends/.

What went out (request body, the files and the PDF that was built, sizes from the catalog), what came
back and where it failed — so a book that looks wrong in Printify or Gelato can be traced afterwards.
Keys never get here: they travel only in request headers. Addresses do (the folder is local and
never goes to git). A journal that cannot be written never stops the send itself.
"""
from __future__ import annotations

import re
import time
from contextlib import contextmanager
from pathlib import Path

from . import core
from .server import Request, route

SENDS = core.data_path("logs", "sends")
KEEP = 400
_NAME = re.compile(r"\d{4}-\d{2}-\d{2}_\d{6}_(printify|gelato)_[\w-]{1,60}\.json")


def _slug(text: str) -> str:
    return re.sub(r"[^\w-]+", "-", str(text or ""), flags=re.ASCII).strip("-")[:40] or "book"


def write(entry: dict) -> Path | None:
    """Saves one attempt; the oldest files beyond KEEP are removed."""
    try:
        SENDS.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y-%m-%d_%H%M%S")
        path = SENDS / f"{stamp}_{entry.get('provider')}_{_slug(entry.get('title'))}.json"
        n = 1
        while path.exists():
            n += 1
            path = path.with_name(f"{stamp}_{entry.get('provider')}_{_slug(entry.get('title'))}-{n}.json")
        core.write_json(path, entry, backup=False)
        for old in sorted(SENDS.glob("*.json"))[:-KEEP]:
            old.unlink(missing_ok=True)
        return path
    except Exception:  # the journal must never break a send
        core.log.exception("Send journal not written")
        return None


@contextmanager
def attempt(provider: str, kind: str, title: str):
    """`with attempt("gelato", "draft", title) as entry:` — fill `entry` along the way; it is saved at
    the end, with the error when the send failed. entry["file"] then holds the journal's name."""
    started = time.monotonic()
    entry: dict = {"provider": provider, "kind": kind, "title": title, "at": core.now_iso(), "ok": False, "steps": []}
    try:
        yield entry
        entry["ok"] = True
    except Exception as err:
        entry["error"] = str(err)
        entry["errorType"] = type(err).__name__
        raise
    finally:
        entry["seconds"] = round(time.monotonic() - started, 2)
        path = write(entry)
        entry["file"] = path.name if path else None


def step(entry: dict, name: str, **data) -> None:
    """A named moment of the send (what was checked, asked or received), in order."""
    entry["steps"].append({"step": name, "t": core.now_iso(), **data})


@route("POST", "/api/sends/open")
def _open(req: Request):
    from . import desktop
    name = str((req.json or {}).get("file") or "")
    path = SENDS / name if _NAME.fullmatch(name) else SENDS
    if not path.exists():
        SENDS.mkdir(parents=True, exist_ok=True)
        path = SENDS
    desktop.open_in_explorer(path)
    return {"ok": True, "path": str(path)}
