"""Moving the settings between computers and between the two Book Studios (the ordinary and the portable one).

One small 7-Zip file under the backup password (AES-256, file names hidden — the same 7-Zip as the backup): the settings,
the keys, the slides' schemes. Not the books, the orders or the pictures (the owner, 2026-10-03: «налаштування + ключі»).
The keys go in decrypted (Windows locks `vault.json` to one user) and straight from memory, never onto the disk readable;
on import Windows encrypts them again for this user. What belongs to one computer — where its Upscayl is, its browser
program, the state of its backup — is left out, the other side has its own.
"""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

from . import backup, core, desktop
from .jobs import JobError
from .server import ApiError, Request, route
from .vault import SECRET_NAMES, vault

SETTINGS_FILE = "Налаштування.json"
KEYS_FILE = "Ключі (відкрито).json"
FOLDERS = ("slides/design", "slides/saved-colours", "slides/schemes")   # under the data folder
NAME = "Налаштування Book Studio {stamp}.7z"


def _computer_bound(data: dict) -> dict:
    """Takes out of a settings dict what must not travel: what belongs to one computer (the backup's state, Upscayl's
    path, the browser program) and the owner's safety switches — «Etsy only from Kyiv» and Printify's read-only date. A file
    made on a colleague's copy (where they are off) must never switch them off on the owner's PC (audit, 2026-10-04)."""
    if not isinstance(data, dict):
        return {}
    for section in ("backup", "workshop", "security"):
        data.pop(section, None)
    if isinstance(data.get("browser"), dict):
        data["browser"].pop("exe", None)
    if isinstance(data.get("printify"), dict):
        for key in ("readOnlyFrom", "manualApprovalConfirmedAt"):
            data["printify"].pop(key, None)
    return data


def _portable_settings() -> dict:
    return _computer_bound(core.read_json(core.data_path("settings.json"), {}) or {})


def sweep() -> None:
    """At the start: an import that was cut short (a crash, a locked file) leaves the opened keys in `tmp/import-*`."""
    tmp = core.data_path("tmp")
    if tmp.is_dir():
        for old in tmp.glob("import-*"):
            shutil.rmtree(old, ignore_errors=True)


def _keys() -> bytes:
    values = {name: value for name, value in vault.readable().items() if name != backup.PASSWORD}
    return json.dumps(values, ensure_ascii=False, indent=2).encode("utf-8")


def _folders() -> list[str]:
    return [f.replace("/", os.sep) for f in FOLDERS if core.data_path(*f.split("/")).is_dir()]


def _password(given: str | None = None) -> str:
    password = given or vault.get(backup.PASSWORD)
    if not password:
        raise ApiError("Спершу задайте пароль резервної копії в Налаштуваннях — ним закривається й цей файл.")
    return password


def export_to(path: Path, password: str | None = None) -> dict:
    """Writes the file; returns what went in."""
    password = _password(password)
    if not backup.SEVEN_ZIP.exists():
        raise ApiError(f"Немає 7-Zip: {backup.SEVEN_ZIP}")
    path = Path(path)
    part = path.with_name(path.name + ".part")
    part.unlink(missing_ok=True)
    keys = _keys()
    try:
        backup._seven_zip(["a", str(part), f"-si{SETTINGS_FILE}"], password,
                          stdin=json.dumps(_portable_settings(), ensure_ascii=False, indent=2).encode("utf-8"))
        backup._seven_zip(["a", str(part), f"-si{KEYS_FILE}"], password, stdin=keys)
        folders = _folders()
        if folders:
            backup._seven_zip(["a", str(part), "-ssw", *folders], password, cwd=core.DATA_DIR)
        os.replace(part, path)
    except JobError as err:
        raise ApiError(str(err)) from err
    finally:
        part.unlink(missing_ok=True)
    core.log.info("Settings exported: %s (%d keys, %d folders)", path.name, len(json.loads(keys)), len(folders))
    return {"file": str(path), "keys": len(json.loads(keys)), "folders": len(folders), "size": path.stat().st_size}


def import_from(path: Path, password: str | None = None) -> dict:
    """Applies a file made by `export_to`. What is replaced is first copied to `import-backup/<time>` in the data folder."""
    given = password
    password = _password(password)
    if '"' in password:
        raise ApiError("Пароль не може містити лапки.", 422)
    path = Path(path)
    if not path.is_file():
        raise ApiError("Файл не знайдено.", 404)
    if not backup.SEVEN_ZIP.exists():
        raise ApiError(f"Немає 7-Zip: {backup.SEVEN_ZIP}")
    work = core.data_path("tmp", f"import-{int(time.time())}")
    work.mkdir(parents=True, exist_ok=True)
    try:
        try:
            backup._seven_zip(["x", str(path), f"-o{work}"], password)
        except JobError as err:
            raise ApiError("Файл не відкрився: неправильний пароль або це не файл налаштувань Book Studio.", 422) from err
        settings_path, keys_path = work / SETTINGS_FILE, work / KEYS_FILE
        if not settings_path.is_file() or not keys_path.is_file():
            raise ApiError("Це не файл налаштувань Book Studio.", 422)
        try:
            incoming = _computer_bound(json.loads(settings_path.read_text(encoding="utf-8")))
            keys = json.loads(keys_path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as err:
            raise ApiError("Це не файл налаштувань Book Studio.", 422) from err
        finally:
            keys_path.unlink(missing_ok=True)          # the opened keys leave the disk as soon as they are read
        if not isinstance(keys, dict):
            raise ApiError("Це не файл налаштувань Book Studio.", 422)
        saved = _save_current()
        core.settings.update(incoming)
        done = []
        for name, value in keys.items():
            if name in SECRET_NAMES and isinstance(value, str) and value and name != backup.PASSWORD:
                vault.set(name, value)
                done.append(name)
        if given and not vault.get(backup.PASSWORD):
            vault.set(backup.PASSWORD, given)     # the file was opened with it: it is this owner's password too
        folders = 0
        for rel in FOLDERS:
            src = work / Path(*rel.split("/"))
            if src.is_dir():
                dst = core.data_path(*rel.split("/"))
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                folders += 1
    finally:
        shutil.rmtree(work, ignore_errors=True)
    core.log.info("Settings imported from %s (%d keys, %d folders); the old ones are in %s", path.name, len(done), folders, saved)
    return {"keys": len(done), "folders": folders, "saved": str(saved)}


def _save_current() -> Path:
    """What an import is about to replace, copied aside (the vault file as it is — it stays encrypted)."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest, n = core.data_path("import-backup", stamp), 1
    while dest.exists():                      # two imports in one second must not mix
        n += 1
        dest = core.data_path("import-backup", f"{stamp}-{n}")
    dest.mkdir(parents=True)
    for name in ("settings.json", "vault.json"):
        src = core.data_path(name)
        if src.is_file():
            shutil.copy2(src, dest / name)
    for rel in FOLDERS:
        src = core.data_path(*rel.split("/"))
        if src.is_dir():
            shutil.copytree(src, dest / Path(*rel.split("/")))
    return dest


@route("POST", "/api/transfer/export")
def _export(req: Request):
    _password()
    if core.SANDBOX:
        raise ApiError("Це тестовий сервер на вигаданих даних — експорт тут не робиться.")
    name = NAME.format(stamp=time.strftime("%Y-%m-%d"))
    path = desktop.save_file("Експорт налаштувань і ключів", name, str(Path.home() / "Desktop"))
    if not path:
        return {"cancelled": True}
    return export_to(Path(path))


@route("POST", "/api/transfer/import")
def _import(req: Request):
    if core.SANDBOX:
        raise ApiError("Це тестовий сервер на вигаданих даних — імпорт тут не робиться.")
    password = str((req.json or {}).get("password") or "") or None
    if not (password or vault.get(backup.PASSWORD)):
        raise ApiError("Введіть пароль, яким закритий файл.", 422)
    path = desktop.pick_7z("Файл налаштувань Book Studio", str(Path.home() / "Desktop"))
    if not path:
        return {"cancelled": True}
    return import_from(Path(path), password)
