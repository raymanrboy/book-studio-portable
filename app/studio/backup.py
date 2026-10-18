"""Backup of the whole program to Google Drive (the owner, 27.09.2026): every few days, when the program starts, the
Book Studio folder and the mockup templates go into one 7-Zip archive with a password (AES-256, the names hidden too)
in a folder of Google Drive for desktop, which uploads it on its own. The keys go inside readable, so a restore on
another computer works at once (the vault opens only for this Windows user); the password is the owner's, kept in the
vault for the schedule. Old copies go by a rule (the last 7, and one a month for a year) — to Drive's trash."""
from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from . import core, portable
from .jobs import Job, JobError, jobs
from .server import ApiError, Request, route
from .vault import vault

SEVEN_ZIP = core.BIN_DIR / "7za.exe"
PROGRAM_DIR = core.ROOT.parent                 # the whole "Book Studio" folder: the code, app/data, the Workshop's books
PASSWORD = "backup_password"                   # its name in the vault
EVERY_DAYS = 3                                 # the owner: "раз на 2–3 дні"
KEEP_LAST = 7                                  # the last 7 copies,
KEEP_MONTHS = 12                               # and the newest of each month for a year
START_DELAY = 120                              # seconds after launch: the orders' sync and the first pages go first
CHECK_EVERY = 6 * 3600                         # and again every 6 hours: a program left open for days still makes its copy
FOLDER_NAME = "Book Studio — резервні копії"
def family() -> str:
    """The ordinary and the portable Book Studio share the Drive folder: each keeps, prunes and cleans only its own copies."""
    return "Book Studio Portable" if portable.root() else "Book Studio"


def _name_re() -> "re.Pattern[str]":
    return re.compile(r"^" + re.escape(family()) + r" (\d{4}-\d{2}-\d{2} \d{2}-\d{2})\.7z$")
# Left out: what Edge holds open while the window is up, and the temp folders (they are emptied anyway).
# The spare copy of the templates (the owner, 29.09.2026) is left out too: the templates themselves are in every copy.
SKIP = (r"app\data\window-profile", r"app\data\work-browser", r"app\data\tmp", ".tmp", "Трафарети мастхев (копія)")
KEYS_FILE = "Ключі (відкрито).json"
README_FILE = "Як відновити.txt"
README = """Резервна копія Book Studio.

1. Розпакуйте архів (7-Zip, з тим самим паролем) у будь-яке місце, напр. на Робочий стіл.
2. Папка "Book Studio" — уся програма з даними. Папка "Трафарети мастхев" (в портативній версії вони лежать у runtime/Templates) — трафарети мокапів.
3. Якщо це інший комп'ютер або інший користувач Windows, ключі зі сховища там не відкриються.
   Їх поверне команда (у папці Book Studio):
       python app/tools/restore_keys.py "шлях до файлу Ключі (відкрито).json"
   (в портативній версії замість python — ../runtime/python/python.exe; або просто Налаштування → Перенесення налаштувань)
   Після цього файл з ключами краще видалити.
4. Ярлик на робочому столі: python app/tools/make_shortcut.py
"""

_WIN = os.name == "nt"
_QUIET = 0x08000000 | 0x4000 if _WIN else 0      # no window, and below normal priority: the program stays smooth while it packs


# ---------------------------------------------------------------- where the copies go

def _label(root: str) -> str:
    if not _WIN:
        return ""
    import ctypes
    buf = ctypes.create_unicode_buffer(261)
    ok = ctypes.windll.kernel32.GetVolumeInformationW(root, buf, 261, None, None, None, None, 0)
    return buf.value if ok else ""


def drive_root() -> Path | None:
    """"My Drive" of Google Drive for desktop: its disk is labelled "Google Drive" (G: unless taken). None when Drive
    is not running or nobody signed in."""
    if core.SANDBOX:  # the preview and the tests: a made-up Drive in the data folder
        root = core.data_path("google-drive", "My Drive")
        root.mkdir(parents=True, exist_ok=True)
        return root
    if not _WIN:
        return None
    import string
    for letter in string.ascii_uppercase[3:]:
        root = f"{letter}:\\"
        if not os.path.exists(root) or _label(root) != "Google Drive":
            continue
        try:
            folders = [p for p in Path(root).iterdir() if p.is_dir() and not p.name.startswith((".", "$"))]
        except OSError:
            continue
        # "My Drive" in English, "Мій диск" in Ukrainian; the others there are shared drives and other computers.
        for p in folders:
            if p.name.lower() in ("my drive", "мій диск", "мой диск", "mój dysk"):
                return p
        return folders[0] if len(folders) == 1 else None
    return None


def target() -> Path | None:
    root = drive_root()
    return root / FOLDER_NAME if root else None


def sources() -> list[Path]:
    from . import mockups
    templates = mockups.places()["templates"]
    # The program (with its books, ~20 GB) last: every later addition rewrites what the archive already holds, and packed first it was
    # written twice — once more behind the 1.6 GB of templates (04.10.2026).
    return ([templates] if templates.is_dir() and not core.inside(templates, PROGRAM_DIR) else []) + [PROGRAM_DIR]


# ---------------------------------------------------------------- the copies there

def copies(folder: Path) -> list[tuple[datetime, Path]]:
    """The finished copies in the folder, newest first."""
    found = []
    try:
        for p in folder.iterdir():
            m = _name_re().match(p.name)
            if m and p.is_file():
                found.append((datetime.strptime(m.group(1), "%Y-%m-%d %H-%M"), p))
    except OSError:
        return []
    return sorted(found, reverse=True)


def to_remove(found: list[tuple[datetime, Path]]) -> list[Path]:
    """The last KEEP_LAST stay, and the newest copy of each of the last KEEP_MONTHS months that have one."""
    keep = {p for _, p in found[:KEEP_LAST]}
    months: dict[str, Path] = {}
    for when, p in found:  # newest first: the first of a month is its newest
        months.setdefault(when.strftime("%Y-%m"), p)
    keep |= {months[m] for m in sorted(months, reverse=True)[:KEEP_MONTHS]}
    return [p for _, p in found if p not in keep]


def due(now: float | None = None) -> bool:
    last = ((core.settings.section("backup") or {}).get("last") or {}).get("at")
    if not last:
        return True
    try:
        at = datetime.fromisoformat(last.rstrip("Z")).timestamp() - time.timezone
    except ValueError:
        return True
    return (now or time.time()) - at >= EVERY_DAYS * 86400 - 3600  # an hour's slack: the same time of day counts


# ---------------------------------------------------------------- making one

def _keys() -> bytes:
    values = {name: value for name, value in vault.readable().items() if name != PASSWORD}
    return json.dumps(values, ensure_ascii=False, indent=2).encode("utf-8")


def _seven_zip(args: list[str], password: str, cwd: Path | None = None, stdin: bytes | None = None,
               job: Job | None = None, step: str = "") -> list[str]:
    """Runs 7za; returns the files it could not read (a warning, exit code 1). Anything worse is an error. The
    password goes on its command line — seen only by this Windows user's own processes."""
    command = [str(SEVEN_ZIP), *args, f"-p{password}", "-mhe=on", "-t7z", "-y", "-bsp1", "-bso0", "-bse1",
               "-sccUTF-8"]
    proc = subprocess.Popen(command, cwd=str(cwd) if cwd else None, creationflags=_QUIET,
                            stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if stdin is not None:
        def feed() -> None:
            try:
                proc.stdin.write(stdin)
            except OSError:
                pass
            finally:
                proc.stdin.close()
        threading.Thread(target=feed, daemon=True).start()
    lines: list[str] = []
    tail = ""
    while chunk := proc.stdout.read1(65536):
        text = tail + chunk.decode("utf-8", "replace")
        parts = re.split(r"[\r\n\x08]+", text)
        tail = parts.pop()
        lines += [p.strip() for p in parts if p.strip()]
        if job:
            percents = re.findall(r"(\d{1,3})%", text)
            if percents:
                job.progress(step, float(percents[-1]))
    proc.stdout.close()
    code = proc.wait()
    lines += [tail.strip()] if tail.strip() else []
    if code == 1:  # some files could not be read (held open by another program): the rest is in the copy
        return [l for l in lines if not l.startswith(("WARNING", "Scanning", "Creating", "Updating")) and "%" not in l
                and ("\\" in l or "/" in l)] or ["(невідомо які)"]
    if code:
        detail = next((l for l in reversed(lines) if "ERROR" in l.upper()), "") or f"код {code}"
        raise JobError(f"7-Zip не зміг зробити копію: {detail}")
    return []


def make(job: Job) -> dict:
    password = vault.get(PASSWORD)
    if not password:
        raise JobError("Спершу задайте пароль резервної копії в Налаштуваннях.")
    if not SEVEN_ZIP.exists():
        raise JobError(f"Немає 7-Zip: {SEVEN_ZIP}")
    folder = target()
    if not folder:
        raise JobError("Google Диск не знайдено: запустіть Google Диск і увійдіть у свій акаунт.")
    folder.mkdir(parents=True, exist_ok=True)
    for stale in folder.glob(f"{family()} *.7z.part"):  # left by a copy that was cut off (the PC switched off); a young one may be
        try:                                           # the other program's copy being written right now
            if time.time() - stale.stat().st_mtime > 6 * 3600:
                stale.unlink(missing_ok=True)
        except OSError:
            pass
    started = time.time()
    stamp = datetime.now().strftime("%Y-%m-%d %H-%M")
    part = folder / f"{family()} {stamp}.7z.part"
    final = folder / f"{family()} {stamp}.7z"
    skipped: list[str] = []
    try:
        # The two small files first, from memory (the keys never touch the disk readable); each later addition
        # rewrites what is already in the archive, so the big folders go last.
        job.progress("Ключі й інструкція…", 0)
        _seven_zip(["a", str(part), f"-si{KEYS_FILE}"], password, stdin=_keys())
        _seven_zip(["a", str(part), f"-si{README_FILE}"], password, stdin=README.encode("utf-8"))
        what = sources()
        for n, src in enumerate(what, 1):
            step = f"Пакую «{src.name}» ({n} з {len(what)})…"
            job.progress(step, 0)
            # Run from the folder above, so the archive holds "Book Studio\…" and "Трафарети мастхев\…".
            skip = [f"-x!{src.name}\\{s}" for s in SKIP] + ["-xr!__pycache__"] if src == PROGRAM_DIR else []
            skipped += _seven_zip(["a", str(part), "-mx0", "-ssw", src.name, *skip], password, cwd=src.parent,
                                  job=job, step=step)
        job.progress("Завершую…", 100)
        os.replace(part, final)
    except BaseException:
        part.unlink(missing_ok=True)
        raise
    try:
        _seven_zip(["l", str(final)], password)         # it opens with the password and lists its files: only then may the old ones go
    except JobError as err:
        final.unlink(missing_ok=True)
        raise JobError(f"Нова резервна копія не відкрилась ({err}) — її видалено, старі копії лишено.") from err
    size = final.stat().st_size
    removed = []
    for old in to_remove(copies(folder)):
        try:
            old.unlink()  # Google Drive keeps it in its trash for 30 days
            removed.append(old.name)
        except OSError:
            core.log.warning("Old backup not removed: %s", old, exc_info=True)
    last = {"at": core.now_iso(), "file": final.name, "folder": str(folder), "size": size,
            "seconds": round(time.time() - started), "skipped": skipped[:20], "skippedCount": len(skipped)}
    core.settings.update({"backup": {"last": last, "error": None}})
    core.log.info("Backup done: %s (%d MB, %d s, %d files skipped, %d old removed)", final.name, size >> 20,
                  last["seconds"], len(skipped), len(removed))
    return {**last, "removed": removed}


def _run(job: Job) -> dict:
    try:
        return make(job)
    except Exception as err:
        core.log.warning("Backup failed: %s", err)
        core.settings.update({"backup": {"error": {"at": core.now_iso(), "message": str(err)}}})
        raise


def start() -> Job:
    return jobs.start("backup", _run, exclusive="backup")


def start_if_due() -> None:
    """On launch (after START_DELAY): a copy when the last one is EVERY_DAYS old — and everything is in place."""
    try:
        if core.SANDBOX or jobs.running("backup") or not due():
            return
        if not vault.get(PASSWORD) or not SEVEN_ZIP.exists() or not target():
            core.log.info("Backup is due but not set up (password, 7-Zip or Google Drive missing)")
            return
        start()
    except Exception:
        core.log.exception("Backup not started")


def _watch() -> None:
    time.sleep(START_DELAY)
    while True:
        start_if_due()
        time.sleep(CHECK_EVERY)


def schedule() -> None:
    """On launch, then every CHECK_EVERY while the program runs (until 2026-10-14 only on launch)."""
    threading.Thread(target=_watch, name="backup-watch", daemon=True).start()


# ---------------------------------------------------------------- routes

def status() -> dict:
    saved = core.settings.section("backup") or {}
    folder = target()
    running = jobs.running("backup")
    return {"passwordSet": bool(vault.get(PASSWORD)), "folder": str(folder) if folder else "",
            "driveFound": bool(folder and folder.parent.exists()),
            "sevenZip": SEVEN_ZIP.exists(), "everyDays": EVERY_DAYS, "last": saved.get("last"),
            "error": saved.get("error"), "due": due(), "jobId": running.id if running else None}


@route("GET", "/api/backup")
def _status(req: Request):
    return status()


@route("POST", "/api/backup/password")
def _password(req: Request):
    value = str((req.json or {}).get("value") or "")
    if len(value) < 12:
        raise ApiError("Пароль має бути щонайменше з 12 символів: у копії всі ваші ключі, і вона лежить на Google Диску.")
    if value != value.strip() or '"' in value:
        raise ApiError("Без пробілів на початку й у кінці та без лапок \".")
    vault.set(PASSWORD, value)
    return status()


@route("POST", "/api/backup/run")
def _run_now(req: Request):
    if not vault.get(PASSWORD):
        raise ApiError("Спершу задайте пароль.")
    return {"jobId": start().id}


@route("POST", "/api/backup/open")
def _open(req: Request):
    from . import desktop
    folder = target()
    if not folder:
        raise ApiError("Google Диск не знайдено.")
    folder.mkdir(parents=True, exist_ok=True)
    desktop.open_in_explorer(folder)
    return {"ok": True}


