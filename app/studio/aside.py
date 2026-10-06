"""«Скасувати» for what goes to the Windows Recycle Bin (06.10.2026). The program cannot take a thing back out of the
Recycle Bin, so a removal used to ask first. Now the thing waits a few minutes on a shelf of the data folder
(`data/aside/<token>/`), the toast's «Скасувати» puts it back where it was, and only then does it go on to the Recycle
Bin — still restorable from there, never deleted for good. Anything left on the shelf when the program closed goes to
the Recycle Bin at the next start, as it was meant to."""
from __future__ import annotations

import re
import shutil
import threading
import time
import uuid
from pathlib import Path

from . import core, desktop
from .server import ApiError, Request, route

SHELF = core.data_path("aside")
KEEP_SECONDS = 120      # far longer than the toast's 9 s: a slow «Скасувати» still finds it
_TOKEN = re.compile(r"[0-9a-f]{12}")
_lock = threading.Lock()


def put(path: Path, what: str) -> str:
    """Takes `path` (a file or a folder) off its place onto the shelf; returns the token «Скасувати» brings it back by."""
    path = Path(path)
    token = uuid.uuid4().hex[:12]
    folder = SHELF / token
    with _lock:
        folder.mkdir(parents=True, exist_ok=True)
        core.write_json(folder / "aside.json", {"from": str(path), "name": path.name, "what": what, "at": time.time()},
                        backup=False)
        try:
            shutil.move(str(path), str(folder / path.name))
        except OSError as err:
            if (folder / path.name).exists():
                raise  # half moved: the shelf's note stays, so «Скасувати» and the Recycle Bin still know where it was
            _forget(folder)
            raise ApiError(f"«{path.name}» не прибрано — можливо, якийсь файл відкритий в іншій програмі. Закрийте "
                           "його і спробуйте ще раз.", 409) from err
    core.log.info("Aside: %s (%s) waits %d s before the Recycle Bin", path.name, what, KEEP_SECONDS)
    timer = threading.Timer(KEEP_SECONDS + 1, flush)
    timer.daemon = True
    timer.start()
    return token


def restore(token: str) -> Path:
    """Puts a shelved thing back on its own place — never over something that stands there now."""
    if not _TOKEN.fullmatch(token or ""):
        raise ApiError("Немає що повертати.", 400)
    folder = SHELF / token
    with _lock:
        meta = core.read_json(folder / "aside.json")
        if not meta or not (folder / meta["name"]).exists():
            raise ApiError("Уже пізно — воно пішло в Кошик Windows (звідти його можна відновити).", 404)
        target = Path(meta["from"])
        if target.exists():
            raise ApiError(f"На місці «{target.name}» уже є інше — нічого не замінено.", 409)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(folder / meta["name"]), str(target))
        _forget(folder)
    core.log.info("Aside: %s put back", target.name)
    return target


def flush(older_than: float = KEEP_SECONDS) -> int:
    """What waited long enough goes on to the Recycle Bin; returns how many went."""
    gone = 0
    if not SHELF.is_dir():
        return 0
    with _lock:
        for folder in sorted(p for p in SHELF.iterdir() if p.is_dir()):
            meta = core.read_json(folder / "aside.json")
            if not meta:
                continue  # not one of ours: left as it is
            if time.time() - float(meta.get("at") or 0) < older_than:
                continue
            item = folder / meta["name"]
            try:
                if item.exists():
                    desktop.to_recycle_bin(item)
                _forget(folder)
                gone += 1
            except OSError:
                core.log.warning("Aside: %s did not go to the Recycle Bin yet", meta["name"], exc_info=True)
    return gone


def _forget(folder: Path) -> None:
    """The shelf's own note and the emptied folder — nothing of the owner's is in them any more."""
    (folder / "aside.json").unlink(missing_ok=True)
    try:
        folder.rmdir()
    except OSError:
        core.log.warning("Aside: %s is not empty — left as it is", folder)


@route("POST", r"/api/aside/restore")
def _restore(req: Request):
    return {"restored": restore(str((req.json or {}).get("token") or "")).name}
