"""A print folder: what it must hold (Cover.png + 1..N.png), its full check, one page replaced by hand and put
back, and the folder held while a send reads it."""
from __future__ import annotations

import contextlib
import os
import re
import shutil
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .. import core, drops, images
from ..jobs import JobError
from ..server import ApiError


REPLACED = ".replaced"          # the pages a new one was put over, kept here so «Повернути» can work
# (mode, folder) -> the number of the newest check the page asked for: an older one of the same folder stops
# (new files or a replaced page start a new check; two full checks of one folder need not run side by side).
_validating: dict[tuple, int] = {}
_validating_lock = threading.Lock()


def _natural_key(name: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def _files_by_lower(folder: Path) -> dict[str, Path]:
    return {p.name.lower(): p for p in folder.iterdir() if p.is_file()}


def _backups(folder: Path, name: str) -> list[Path]:
    """The previous versions of one page, oldest first: what «Повернути» can put back."""
    keep = folder / REPLACED
    return sorted(keep.glob(f"{name}.*")) if keep.is_dir() else []


_sending: Counter[str] = Counter()  # print folder -> sends reading it right now (two printers at once: 2)
_sending_lock = threading.Lock()


@contextlib.contextmanager
def _while_sending(folders):
    """A send checks the files, then uploads them, builds the PDF and copies them to the archive — all by
    reading the same paths again. While that runs, the pages must not change under it, or what the printer
    gets is not what passed the check. Replacing a page waits for the send to finish."""
    mine = {str(Path(f).resolve()) for f in folders if f}
    with _sending_lock:
        _sending.update(mine)
    try:
        yield
    finally:
        with _sending_lock:
            _sending.subtract(mine)
            for key in mine:
                if _sending[key] <= 0:
                    del _sending[key]


@contextlib.contextmanager
def _not_while_sending(folder: Path):
    """A page changes only while no send reads its folder — and no send starts until the change is done."""
    with _sending_lock:
        if _sending.get(str(folder.resolve())):
            raise ApiError("Книга саме відправляється в друкарню — зачекайте, поки відправка завершиться.")
        yield


def gelato_page_options() -> list[int]:
    """How long a Gelato book may be: as long as the Canva export — 30 pages, or 28 without one spread."""
    return sorted(int(n) for n in core.settings.section("gelato").get("pageCounts") or [28, 30])


def _gelato_page_count(present: dict[str, Path]) -> int:
    """The book length a Gelato folder is meant for: the shortest allowed one that holds its highest page."""
    options = gelato_page_options()
    top = max((int(m.group(1)) for name in present if (m := re.fullmatch(r"(\d+)\.png", name))), default=0)
    return next((n for n in options if n >= top), options[-1])


def expected_files(mode: str, count: int | None = None) -> list[dict]:
    if mode == "printify":
        cfg = core.settings.section("printify")
        count = int(cfg.get("pageCount") or 24)
        cover, page = cfg.get("coverSize") or [4672, 2464], cfg.get("pageSize") or [4000, 4000]
        out = [{"file": "Cover.png", "position": "cover", "size": cover}]
        out += [{"file": f"{i}.png", "position": f"page_{i}", "size": page} for i in range(1, count + 1)]
        return out
    count = count or gelato_page_options()[-1]
    out = [{"file": "Cover.png", "position": "cover", "size": None}]
    out += [{"file": f"{i}.png", "position": f"page_{i}", "size": None} for i in range(1, count + 1)]
    return out


def validate(mode: str, folder_raw: str, job=None) -> dict:
    """The full check of a print folder, each file read once per version of it (images.check_png()). With a job
    (the page asked): a newer check of the same folder stops this one, and the pages' previews are made from the
    same decode. A send's own check (no job) is never stopped and makes no previews: the PDF or the uploads that
    follow read every file anyway, and on Windows a second reader kept a page open while its folder was being
    removed (a flaky test, 25.09.2026)."""
    folder = Path((folder_raw or "").strip().strip('"'))
    if not folder_raw or not folder.is_dir():
        expected = expected_files(mode)
        return {"ok": False, "folder": str(folder), "errors": ["Папку не знайдено або шлях некоректний."],
                "warnings": [], "files": [], "found": 0, "expected": len(expected), "pageCount": len(expected) - 1}
    drops.touch(folder)
    present = _files_by_lower(folder)
    expected = expected_files(mode, _gelato_page_count(present) if mode == "gelato" else None)
    slot = (mode, str(folder.resolve()))
    ticket = None
    if job is not None:
        with _validating_lock:
            ticket = _validating[slot] = _validating.get(slot, 0) + 1

    def superseded() -> bool:
        return ticket is not None and _validating.get(slot) != ticket

    errors: list[str] = []
    warnings: list[str] = []
    missing = [e["file"] for e in expected if e["file"].lower() not in present]
    expected_lower = {e["file"].lower() for e in expected}
    extra = sorted((p.name for n, p in present.items() if n not in expected_lower and not n.startswith(".")
                    and n not in ("thumbs.db", "desktop.ini")), key=_natural_key)
    if missing:
        pretty = ", ".join(m.replace(".png", "") if m[0].isdigit() else m for m in missing)
        errors.append(f"Відсутні файли ({len(missing)} шт.): {pretty}")
    if extra:
        warnings.append(f"Додаткові файли не буде використано ({len(extra)} шт.): {', '.join(extra[:12])}"
                        + ("…" if len(extra) > 12 else ""))

    rows: list[dict] = []
    todo = [e for e in expected if e["file"].lower() in present]
    previews = images.VIEW_SIDES if job is not None else ()

    def check(entry: dict) -> dict:
        if superseded():
            raise JobError("Цю перевірку замінила новіша.")
        path = present[entry["file"].lower()]
        info, err = images.check_png(path, previews)
        row = {"file": entry["file"], "position": entry["position"], "path": str(path), "ok": err is None,
               "error": err}
        if info:
            row.update({"width": info["width"], "height": info["height"], "bytes": info["bytes"]})
            if info.get("frames", 1) != 1:
                row["ok"], row["error"] = False, "анімований PNG не підтримується"
            size = entry.get("size")
            if row["ok"] and size and (info["width"], info["height"]) != tuple(size):
                row["ok"] = False
                row["error"] = (f"розмір {info['width']}×{info['height']} px, очікується рівно {size[0]}×{size[1]} px")
        if row["ok"] and mode == "printify":
            row["sha256"] = images.digest(path)
        # «Повернути» is offered from what is on disk, so it survives leaving the card and a restart.
        row["replaced"] = bool(_backups(folder, entry["file"]))
        return row

    with ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(check, todo):  # in the expected order
            rows.append(row)
            if job:
                job.progress("Перевірка файлів…", 100 * len(rows) / max(len(todo), 1), row["file"])
    for row in rows:
        if not row["ok"]:
            label = "Обкладинка" if row["position"] == "cover" else f"Сторінка {row['file'][:-4]}"
            errors.append(f"{label} ({row['file']}): {row['error']}")
    if mode == "printify":
        seen: dict[str, str] = {}
        for row in rows:
            sha = row.get("sha256")
            if sha and sha in seen:
                warnings.append(f"Файли {seen[sha]} і {row['file']} однакові (дублікат зображення).")
            elif sha:
                seen[sha] = row["file"]
    return {
        "ok": not errors,  # a missing file is an error too
        "folder": str(folder),
        "errors": errors,
        "warnings": warnings,
        "files": rows,
        "found": len(rows),
        "expected": len(expected),
        "pageCount": len(expected) - 1,
        "totalBytes": sum(r.get("bytes", 0) for r in rows),
    }


# ---------------------------------------------------------------- one page replaced by hand

_PAGE_NAME = re.compile(r"(?:cover|\d{1,3})\.png", re.I)


def _print_page(folder_raw: str, file: str) -> tuple[Path, Path]:
    """The print folder and the page inside it, as they are really named on disk."""
    folder = Path(str(folder_raw or "").strip().strip('"'))
    if not folder.is_dir():
        raise ApiError("Папку з файлами не знайдено — перетягніть їх ще раз.", 404)
    if not _PAGE_NAME.fullmatch(str(file or "")):
        raise ApiError("Так сторінка книги не називається.")
    page = _files_by_lower(folder).get(str(file).lower())
    if not page:
        raise ApiError(f"У папці немає {file}.", 404)
    return folder, page


def replace_page(folder_raw: str, file: str, source_raw: str) -> dict:
    """Puts a page downloaded from Canva in place of one in the print folder (the owner fixed it in the
    template and wants only that page changed). The old one waits in `.replaced` for «Повернути»; the
    checks that follow are the usual ones, so a page of the wrong size is caught there."""
    folder, page = _print_page(folder_raw, file)
    source = Path(str(source_raw or "").strip().strip('"'))
    if not source.is_file():
        raise ApiError("Файл не знайдено.", 404)
    if source.resolve() == page.resolve():
        raise ApiError("Це той самий файл, що вже в папці.")
    info, error = images.check_png(source)
    if error or not info:
        raise ApiError(f"Це не придатний PNG: {error or 'файл не читається'}.")
    with _not_while_sending(folder):
        keep = folder / REPLACED
        keep.mkdir(exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        kept = keep / f"{page.name}.{stamp}"
        for n in range(2, 100):     # two replacements of one page within the same second keep both
            if not kept.exists():
                break
            kept = keep / f"{page.name}.{stamp}-{n}"
        shutil.copy2(page, kept)
        tmp = page.with_name(page.name + ".new")
        shutil.copy2(source, tmp)
        os.replace(tmp, page)   # the page is never half-written: it changes in one step
    core.log.info("Page %s replaced from %s", page.name, source.name)
    return {"file": page.name, "width": info["width"], "height": info["height"], "bytes": info["bytes"],
            "canRestore": True}


def restore_page(folder_raw: str, file: str) -> dict:
    """«Повернути»: the page that was there before the last replacement comes back."""
    folder, page = _print_page(folder_raw, file)
    with _not_while_sending(folder):
        kept = _backups(folder, page.name)
        if not kept:
            raise ApiError("Немає чого повертати.", 404)
        os.replace(kept[-1], page)
    core.log.info("Page %s restored", page.name)
    return {"file": page.name, "canRestore": bool(_backups(folder, page.name))}
