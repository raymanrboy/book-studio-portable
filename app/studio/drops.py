"""Files the owner drags into a window, and how a Canva export names them.

The window (a browser) never learns where a dragged folder lives on disk, so its pictures (or a ZIP) are
copied into a scratch folder first and the program works with that copy; everything there is wiped when
the program starts. The naming rules — which file is the cover, which number a page has — are one reading
for the order's print folder (orders.arrange_pages), the library import (library_files.scan_folder) and the
listing mockups (mockups.read_book).
"""
from __future__ import annotations

import os
import re
import shutil
import time
import zipfile
from collections import Counter
from pathlib import Path

from . import core, images
from .server import ApiError, Request, route

DROPS = core.data_path("tmp", "dropped")
DROP_IMAGE = re.compile(r"\.(png|jpe?g|webp)$", re.I)
MAX_DROP_FILE = 400 * 1024 * 1024
MAX_DROP_ZIP = 6 * 1024 * 1024 * 1024
_DROP_SESSION = re.compile(r"[0-9a-f]{32}")
# A dropped folder unused this long goes at the next drop (and every one at a restart). An order's card keeps its
# folder for as long as the program runs (decision 2026-09-18), and each check of the folder counts as a use.
KEEP_UNUSED = 24 * 3600

UPSCAYL_TAIL = re.compile(r"_upscayl.*$", re.I)        # "12_upscayl_4x_ultrasharp" -> "12"
COVER_NAME = re.compile(r"cover|cober|обкладин", re.I)  # "Cover", the usual slip "Cober", "Обкладинка"
_LAST_NUMBER = re.compile(r"(\d+)(?=\D*$)")


# ---------------------------------------------------------------- a Canva export's names

def page_number(stem: str) -> int | None:
    """Page number in a file name: "12", "Madelynn - 12", "12_upscayl_4x_ultrasharp" -> 12."""
    stem = UPSCAYL_TAIL.sub("", stem)
    m = _LAST_NUMBER.search(stem)
    return int(m.group(1)) if m else None


def export_files(folder: Path, suffixes: tuple[str, ...] = (".png",)) -> tuple[Path, list[tuple[int, Path]]]:
    """The cover and the numbered pages (sorted by number) of a Canva export, whatever Canva or Upscayl
    called them: the file with "cover" in its name is the cover (else the one wide picture among square
    pages); the rest are ordered by the number in their names."""
    if not folder.is_dir():
        raise ApiError("Папку не знайдено.")
    files = sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in suffixes
                    and not p.name.startswith(".")), key=lambda p: p.name.lower())
    if not files:
        raise ApiError("У папці немає PNG-файлів." if suffixes == (".png",) else "У папці немає зображень.")
    covers = [p for p in files if COVER_NAME.search(UPSCAYL_TAIL.sub("", p.stem))]
    if len(covers) > 1:
        raise ApiError(f"Кілька обкладинок: {', '.join(p.name for p in covers)}. Залиште одну.")
    rest = [p for p in files if p not in covers]
    if not covers:
        wide = []
        for p in rest:
            try:
                info = images.image_info(p)
            except Exception:
                raise ApiError(f"Файл «{p.name}» не читається як зображення.") from None
            if info["width"] >= 1.4 * info["height"]:
                wide.append(p)
        if len(wide) != 1:
            raise ApiError("Не знайшов обкладинку: назвіть її Cover.png.")
        covers, rest = wide, [p for p in rest if p != wide[0]]
    numbered = []
    for p in rest:
        n = page_number(p.stem)
        if n is None:
            raise ApiError(f"У назві «{p.name}» немає номера сторінки.")
        numbered.append((n, p))
    numbered.sort(key=lambda x: (x[0], x[1].name.lower()))
    twice = sorted(n for n, c in Counter(n for n, _ in numbered).items() if c > 1)
    if twice:
        raise ApiError(f"Сторінка {', '.join(map(str, twice))} є двічі.")
    return covers[0], numbered


# ---------------------------------------------------------------- dropped folders and archives

def clear_drops(keep: str | None = None, older_than: float = 0) -> None:
    if not DROPS.is_dir():
        return
    now = time.time()
    for entry in DROPS.iterdir():
        if entry.name == keep:
            continue
        try:
            if now - entry.stat().st_mtime >= older_than:
                shutil.rmtree(entry, ignore_errors=True) if entry.is_dir() else entry.unlink(missing_ok=True)
        except OSError:
            pass


def touch(folder: Path) -> None:
    """A dropped folder in use (its card or the Order Creator checks it again): its time is now, so the clean-up
    after the next drop leaves it."""
    try:
        rel = folder.resolve().relative_to(DROPS.resolve())
        if rel.parts:
            os.utime(DROPS / rel.parts[0])
    except (ValueError, OSError):
        pass


def _drop_root(session: str | None) -> Path:
    if not _DROP_SESSION.fullmatch(session or ""):
        raise ApiError("Некоректний запит.")
    return DROPS / session


def _drop_rel(name: str, with_text: bool = False) -> Path | None:
    """A relative path from the dropped folder or archive, or None when it is not a picture we can use
    (with_text also lets the library's book-text JSON through)."""
    parts = [p for p in re.split(r"[\\/]+", name or "") if p not in ("", ".")]
    if not parts or len(parts) > 6 or any(p == ".." or ":" in p or p == "__MACOSX" for p in parts):
        return None
    usable = DROP_IMAGE.search(parts[-1]) or (with_text and parts[-1].lower().endswith(".json"))
    if parts[-1].startswith("._") or not usable:
        return None
    return Path(*[re.sub(r'[<>"|?*\x00-\x1f]', "_", p).rstrip(" .") or "_" for p in parts])


def extract_zip(archive: Path, target: Path, with_text: bool = False) -> int:
    try:
        zf = zipfile.ZipFile(archive)
    except (zipfile.BadZipFile, OSError):
        raise ApiError("Архів пошкоджений або це не ZIP.") from None
    count = total = 0
    with zf:
        for info in zf.infolist():
            rel = None if info.is_dir() else _drop_rel(info.filename, with_text)
            if rel is None:
                continue
            total += info.file_size
            if total > MAX_DROP_ZIP:
                raise ApiError("Архів завеликий.")
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(dest, "wb") as out:
                shutil.copyfileobj(src, out, 1024 * 1024)
            count += 1
    if not count:
        raise ApiError("В архіві немає зображень PNG." if not with_text else "В архіві немає ні зображень, ні тексту книги.")
    return count


def dropped_top(root: Path) -> Path:
    """The dropped folder itself (the library's importer reads its generated/ and pages/ too): down through
    folders that hold nothing but one folder."""
    folder = root
    while True:
        items = list(folder.iterdir())
        if len(items) != 1 or not items[0].is_dir():
            return folder
        folder = items[0]


def dropped_folder(root: Path) -> Path:
    """The folder with Cover.png in what was dropped (the shallowest one), else the folder holding the pictures."""
    files = [p for p in root.rglob("*") if p.is_file()]
    covers = sorted({p.parent for p in files if p.name.lower() == "cover.png"}, key=lambda d: len(d.parts))
    if covers:
        return covers[0]
    holders = {p.parent for p in files}
    return holders.pop() if len(holders) == 1 else root


@route("POST", "/api/drop/file")
def _drop_file(req: Request):
    root = _drop_root(req.param("session"))
    rel = _drop_rel(req.param("name") or "", with_text=req.param("text") == "1")
    if rel is None:
        raise ApiError("Перетягніть папку з PNG-файлами або ZIP-архів.")
    req.body_to_file(root / rel, MAX_DROP_FILE)
    return {"ok": True}


def archive_folder(name: str) -> str:
    """The folder a ZIP is unpacked into: its own name, safe for Windows."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", Path(name or "archive.zip").stem).strip(" .")[:80] or "archive"


@route("POST", "/api/drop/zip")
def _drop_zip(req: Request):
    root = _drop_root(req.param("session"))
    archive = DROPS / f"{root.name}.zip"  # beside the folder, never inside it
    try:
        req.body_to_file(archive, MAX_DROP_ZIP)
        extract_zip(archive, root / archive_folder(req.param("name")), with_text=req.param("text") == "1")
    finally:
        archive.unlink(missing_ok=True)
    return {"ok": True}


@route("POST", "/api/drop/done")
def _drop_done(req: Request):
    body = req.json or {}
    session = str(body.get("session") or "")
    root = _drop_root(session)
    if not root.is_dir():
        raise ApiError("Файли не отримано — перетягніть папку ще раз.")
    clear_drops(keep=session, older_than=KEEP_UNUSED)
    return {"path": str(dropped_top(root) if body.get("whole") else dropped_folder(root))}
