"""A library book's files in and out: the book's text as JSON (import and export), a folder of pictures and texts
laid into the book's slots, the whole book exported to a folder, and the guide for whoever prepares a book (its words
in library_guide.md). The book itself — library.py."""
from __future__ import annotations

import json
import os
import re
import shutil
import string
from pathlib import Path

from . import core, desktop, drops
from .jobs import jobs
from .library import (FIRST_SPREAD, LAST_SPREAD, SLOT_KEYS, SPREAD_NUMBERS, _book_dir, _book_response, _lock,
                      import_pictures, load, save, spread_pages)
from .server import ApiError, Request, route


# ---------------------------------------------------------------- text import

def parse_text_json(raw: str) -> tuple[dict, list[str], list[str]]:
    """Parses the book-text JSON: {cover, page1, spreads: {"2".."15"}, page30}.

    Lenient: imports every valid field, reports the rest.
    """
    try:
        data = json.loads(raw.lstrip("﻿"))
    except json.JSONDecodeError as err:
        raise ApiError(f"Файл не є коректним JSON (рядок {err.lineno}, позиція {err.colno}).")
    if not isinstance(data, dict):
        raise ApiError("JSON має бути об'єктом із полями cover, page1, spreads, page30.")
    text: dict[str, str] = {}
    problems: list[str] = []
    for key in ("cover", "page1", "page30"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            text[key] = value.strip()
        else:
            problems.append(f"Немає тексту «{key}»")
    spreads = data.get("spreads")
    if not isinstance(spreads, dict):
        problems.append("Немає об'єкта «spreads» з текстами розворотів 2–15")
        spreads = {}
    for n in SPREAD_NUMBERS:
        value = spreads.get(str(n))
        if isinstance(value, str) and value.strip():
            text[f"spread{n}"] = value.strip()
        else:
            problems.append(f"Немає тексту розвороту {n}")
    extra = [k for k in spreads.keys() if not (k.isdigit() and FIRST_SPREAD <= int(k) <= LAST_SPREAD)]
    notes = [f"Пропущено невідомі ключі spreads: {', '.join(extra)}"] if extra else []
    if not text:
        raise ApiError("У JSON не знайдено жодного тексту книги.")
    return text, problems, notes


def export_text_json(book: dict) -> dict:
    t = book["text"]
    return {
        "cover": t.get("cover", ""),
        "page1": t.get("page1", ""),
        "spreads": {str(n): t.get(f"spread{n}", "") for n in SPREAD_NUMBERS},
        "page30": t.get("page30", ""),
    }


# ---------------------------------------------------------------- folder import

_NUM_RE = re.compile(r"^(\d+)(?:\s*[-–_]\s*(\d+))?$")
# File-name rules shared with the order's print folder and the listing mockups: one reading everywhere.
UPSCAYL_TAIL, COVER_NAME = drops.UPSCAYL_TAIL, drops.COVER_NAME


def scan_folder(folder: Path) -> dict:
    """Proposes a mapping of files in a folder onto book slots.

    Understands the pipeline layout (generated/1.png, 2-3.png … 28-29.png, 30.png,
    Cover.*, book-text.json) and separate pages 1.png … 30.png.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise ApiError("Папку не знайдено.")
    roots = [folder]
    for sub in ("generated", "pages"):  # Windows paths are case-insensitive: one spelling is enough
        if (folder / sub).is_dir():
            roots.append(folder / sub)
    files: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        for p in root.iterdir():
            key = os.path.normcase(str(p.resolve()))
            if p.is_file() and key not in seen:
                seen.add(key)
                files.append(p)

    text_file = next((p for p in files if p.name.lower() in ("book-text.json", "text.json", "book.json")), None)
    if not text_file:
        text_file = next((p for p in files if p.suffix.lower() == ".json"), None)

    imgs = [p for p in files if p.suffix.lower() in core.IMAGE_EXTS]
    cover = thumb = None
    singles: dict[int, Path] = {}
    pairs: dict[tuple[int, int], Path] = {}
    unknown: list[str] = []
    # Later roots (generated/) win over the top folder. Upscayl's "_upscayl_4x_…" name tail is ignored.
    for p in imgs:
        stem = UPSCAYL_TAIL.sub("", p.stem).strip().lower()
        if COVER_NAME.search(stem):
            if cover is None or p.suffix.lower() == ".png":
                cover = p
            continue
        if re.search(r"thumb|заставк|preview|gallery", stem):
            thumb = p
            continue
        m = _NUM_RE.match(stem)
        if not m:
            unknown.append(p.name)
            continue
        a = int(m.group(1))
        if m.group(2):
            pairs[(a, int(m.group(2)))] = p
        else:
            singles[a] = p

    mapping: dict[str, dict] = {}
    issues: list[str] = []

    def put(slot: str, path: Path) -> None:
        mapping[slot] = {"path": str(path), "name": path.name}

    if cover:
        put("cover", cover)
    if thumb:
        put("thumbnail", thumb)
    if 1 in singles:
        put("page1", singles[1])
    if 30 in singles:
        put("page30", singles[30])
    for n in SPREAD_NUMBERS:
        left, right = spread_pages(n)
        if (left, right) in pairs:
            put(f"spread{n}", pairs[(left, right)])
        else:
            # Whatever is there goes to its place (often just the illustration page of a spread);
            # what is missing simply stays empty.
            if left in singles:
                put(f"spread{n}:left", singles[left])
            if right in singles:
                put(f"spread{n}:right", singles[right])
    used = {v["path"] for v in mapping.values()}
    leftovers = [p.name for p in imgs if str(p) not in used and p.name not in unknown]
    filled = sum(1 for k in SLOT_KEYS if k in mapping or (f"{k}:left" in mapping and f"{k}:right" in mapping))
    if not mapping and not text_file:
        issues.append("У папці не знайдено файлів книги (Cover, 1, 2-3 … 30 або book-text.json).")
    return {
        "folder": str(folder),
        "mapping": mapping,
        "text": {"path": str(text_file), "name": text_file.name} if text_file else None,
        "slotsFound": filled,
        "slotsTotal": len(SLOT_KEYS),
        "issues": issues,
        "ignored": sorted(set(unknown + leftovers)),
    }


# ---------------------------------------------------------------- export

def export_book(book: dict, target: Path, job) -> dict:
    target.mkdir(parents=True, exist_ok=True)
    src_dir = _book_dir(book["id"]) / "assets"
    plan: list[tuple[dict, str]] = []
    if book.get("cover"):
        plan.append((book["cover"], "Cover"))
    if book.get("thumbnail"):
        plan.append((book["thumbnail"], "Thumbnail"))
    for key in SLOT_KEYS:
        s = book["slots"][key]
        if key in ("page1", "page30"):
            if s.get("image"):
                plan.append((s["image"], key[4:]))
            continue
        n = int(key[6:])
        left, right = spread_pages(n)
        if s.get("image"):
            plan.append((s["image"], f"{left}-{right}"))
        if s.get("left"):
            plan.append((s["left"], str(left)))
        if s.get("right"):
            plan.append((s["right"], str(right)))
    for i, (asset, name) in enumerate(plan, 1):
        job.progress("Експорт файлів…", 100 * i / max(len(plan), 1), f"{name}")
        ext = Path(asset["file"]).suffix
        shutil.copy2(src_dir / asset["file"], target / f"{name}{ext}")
    text = export_text_json(book)
    if any(v for k, v in text.items() if k != "spreads") or any(text["spreads"].values()):
        (target / "book-text.json").write_text(json.dumps(text, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"folder": str(target), "files": len(plan)}


# ---------------------------------------------------------------- guide for whoever prepares a book

GUIDE_NAME = "Book Studio — як підготувати книгу.md"
GUIDE = Path(__file__).with_name("library_guide.md")  # the guide's words, in Markdown


def agent_guide() -> str:
    """Instruction (Markdown) for a person or an AI agent preparing one book's files: the exact file names
    the batch import understands and the book-text JSON. The words are in library_guide.md (the owner may edit
    them); its table of names ($table) and its JSON template ($json) are built here from the same rules the
    importer uses (scan_folder / parse_text_json), so they cannot drift from them."""
    rows = ["| Обкладинка (весь розворот обкладинки) | — | `Cover.png` |",
            "| Заставка для галереї (необов'язково) | — | `Thumbnail.png` |",
            "| Присвята | 1 | `1.png` |"]
    for n in SPREAD_NUMBERS:
        a, b = spread_pages(n)
        rows.append(f"| Розворот {n} | {a}–{b} | `{a}-{b}.png` або `{a}.png` + `{b}.png` |")
    rows.append("| Післяслово | 30 | `30.png` |")
    template = json.dumps({
        "cover": "Текст обкладинки",
        "page1": "Текст присвяти (сторінка 1)",
        "spreads": {str(n): "Текст розвороту {} (сторінки {}–{})".format(n, *spread_pages(n)) for n in SPREAD_NUMBERS},
        "page30": "Текст післяслова (сторінка 30)",
    }, ensure_ascii=False, indent=2)
    return string.Template(GUIDE.read_text(encoding="utf-8")).substitute(table="\n".join(rows), json=template)


# ---------------------------------------------------------------- routes

@route("GET", "/api/library/guide")
def _guide(req: Request):
    return {"name": GUIDE_NAME, "text": agent_guide()}


@route("POST", "/api/library/guide/save")
def _guide_save(req: Request):
    folder = Path(str((req.json or {}).get("folder") or ""))
    if not folder.is_dir():
        raise ApiError("Папку не знайдено.")
    target = folder / GUIDE_NAME
    target.write_text(agent_guide(), encoding="utf-8")
    try:
        desktop.open_in_explorer(target)  # shows the file selected, ready to drag into a chat with an agent
    except OSError:
        pass
    return {"path": str(target)}


@route("POST", r"/api/library/books/([0-9a-f]{32})/text")
def _import_text(req: Request):
    body = req.json or {}
    raw = body.get("json")
    if not isinstance(raw, str) or not raw.strip():
        raise ApiError("Порожній текст.")
    text, problems, notes = parse_text_json(raw)
    with _lock:
        book = load(req.groups[0])
        book["text"].update(text)
        save(book)
    return {"book": _book_response(book), "imported": len(text), "problems": problems, "notes": notes}


@route("GET", r"/api/library/books/([0-9a-f]{32})/text.json")
def _text_json(req: Request):
    return export_text_json(load(req.groups[0]))


@route("POST", r"/api/library/books/([0-9a-f]{32})/folder-scan")
def _folder_scan(req: Request):
    load(req.groups[0])
    return scan_folder(Path((req.json or {}).get("path") or ""))


@route("POST", r"/api/library/books/([0-9a-f]{32})/folder-import")
def _folder_import(req: Request):
    book_id = req.groups[0]
    body = req.json or {}
    scan = scan_folder(Path(body.get("path") or ""))
    include_text = bool(body.get("includeText", True))
    selected = set(body.get("slots") or scan["mapping"].keys())
    load(book_id)

    def run(job) -> dict:
        items = [(slot, Path(info["path"]), info["name"]) for slot, info in scan["mapping"].items() if slot in selected]
        image_errors = import_pictures(book_id, items, job)
        text_result, text_error = None, None
        if include_text and scan.get("text"):
            job.progress("Імпорт тексту…", 97, scan["text"]["name"])
            try:
                raw = Path(scan["text"]["path"]).read_text(encoding="utf-8-sig")
                text, problems, _ = parse_text_json(raw)
                with _lock:
                    book = load(book_id)
                    book["text"].update(text)
                    save(book)
                text_result = {"imported": len(text), "problems": problems}
            except (ApiError, OSError, UnicodeDecodeError) as err:
                text_error = f"{scan['text']['name']}: {err}"
        # Display previews and blurred stand-ins were prepared while storing each file.
        return {"images": len(items) - len(image_errors),
                "errors": image_errors + ([text_error] if text_error else []), "text": text_result}

    job = jobs.start("library-import", run, exclusive=f"library-{book_id}")
    return {"jobId": job.id}


@route("POST", r"/api/library/books/([0-9a-f]{32})/export")
def _export(req: Request):
    book = load(req.groups[0])
    target_raw = (req.json or {}).get("path") or ""
    if not target_raw:
        raise ApiError("Оберіть папку для експорту.")
    safe_title = re.sub(r'[<>:"/\\|?*]+', "", book.get("title") or "book")[:60].strip() or "book"
    target = Path(target_raw) / safe_title
    job = jobs.start("library-export", lambda j: export_book(book, target, j))
    return {"jobId": job.id}
