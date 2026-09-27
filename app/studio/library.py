"""Book library: one reference book per Etsy listing.

Book structure (30 physical pages, same as the production pipeline):
  cover                      — full cover spread
  page1                      — dedication (single right-hand page)
  spread2 … spread15         — story spreads, pages 2-3 … 28-29
  page30                     — afterword (single left-hand page)
A spread image is either one combined picture or separate left/right pages.
Everything except the listing is optional and can be added any time.

A book made in the Listings mode's Workshop comes here when it is passed on (workshop/books.py, to_library()): a
library book made from its pages and texts, noting the Workshop book it came from ("workshop").
"""
from __future__ import annotations

import json
import os
import re
import shutil
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

from . import core, desktop, drops, etsy, images
from .jobs import jobs
from .server import ApiError, Request, file_response, route

BOOKS_DIR = core.data_path("library", "books")
TRASH_DIR = core.data_path("library", "trash")
MAX_IMAGE_BYTES = 150 * 1024 * 1024
FIRST_SPREAD, LAST_SPREAD = 2, 15
SPREAD_NUMBERS = list(range(FIRST_SPREAD, LAST_SPREAD + 1))
SLOT_KEYS = ["page1"] + [f"spread{n}" for n in SPREAD_NUMBERS] + ["page30"]
TEXT_KEYS = ["cover"] + SLOT_KEYS
LISTING_FIELDS = ("id", "title", "state", "shopId", "url", "imageUrl", "verifiedAt")

_lock = threading.RLock()


# ---------------------------------------------------------------- helpers

def spread_pages(n: int) -> tuple[int, int]:
    return 2 * n - 2, 2 * n - 1


def slot_label(key: str) -> str:
    if key == "cover":
        return "Обкладинка"
    if key == "page1":
        return "Сторінка 1 · присвята"
    if key == "page30":
        return "Сторінка 30 · післяслово"
    n = int(key[6:])
    left, right = spread_pages(n)
    return f"Розворот {n} · стор. {left}–{right}"


def _book_dir(book_id: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{32}", book_id or ""):
        raise ApiError("Книгу не знайдено.", 404)
    return BOOKS_DIR / book_id


def _empty_slots() -> dict:
    slots: dict[str, Any] = {"page1": {"image": None}, "page30": {"image": None}}
    for n in SPREAD_NUMBERS:
        slots[f"spread{n}"] = {"image": None, "left": None, "right": None}
    return slots


def load(book_id: str) -> dict:
    data = core.read_json(_book_dir(book_id) / "book.json")
    if not data:
        raise ApiError("Книгу не знайдено.", 404)
    slots = _empty_slots()
    slots.update(data.get("slots") or {})
    data["slots"] = slots
    text = {k: "" for k in TEXT_KEYS}
    text.update({k: v for k, v in (data.get("text") or {}).items() if k in TEXT_KEYS})
    data["text"] = text
    return data


def save(book: dict) -> dict:
    book["updatedAt"] = core.now_iso()
    book["rev"] = int(book.get("rev") or 0) + 1
    core.write_json(_book_dir(book["id"]) / "book.json", book)
    return book


def _all_assets(book: dict) -> list[dict]:
    out = []
    for key in ("cover", "thumbnail"):
        if book.get(key):
            out.append(book[key])
    for slot in book["slots"].values():
        for part in ("image", "left", "right"):
            if slot.get(part):
                out.append(slot[part])
    return out


def completeness(book: dict) -> dict:
    slots = book["slots"]
    illustrated = 0
    for key in SLOT_KEYS:
        s = slots[key]
        if s.get("image") or (s.get("left") and s.get("right")):
            illustrated += 1
    texts = sum(1 for k in TEXT_KEYS if (book["text"].get(k) or "").strip())
    return {
        "cover": bool(book.get("cover")),
        "thumbnail": bool(book.get("thumbnail")),
        "illustrations": illustrated,
        "illustrationsTotal": len(SLOT_KEYS),
        "texts": texts,
        "textsTotal": len(TEXT_KEYS),
        "canva": bool((book.get("canvaUrl") or "").strip()),
        "complete": bool(book.get("cover")) and illustrated == len(SLOT_KEYS) and texts == len(TEXT_KEYS),
    }


def summary(book: dict) -> dict:
    card = book.get("thumbnail") or book.get("cover")
    return {
        "id": book["id"],
        "title": book.get("title") or (book.get("listing") or {}).get("title") or "Без назви",
        "listingId": (book.get("listing") or {}).get("id"),
        "verified": bool((book.get("listing") or {}).get("verifiedAt")),
        "archived": bool(book.get("archived")),
        "createdAt": book.get("createdAt"),
        "updatedAt": book.get("updatedAt"),
        "image": card["file"] if card else None,
        "lqip": card.get("lqip") if card else None,
        "imageIsCover": bool(card) and not book.get("thumbnail"),
        "imageW": card.get("width") if card else None,
        "imageH": card.get("height") if card else None,
        "completeness": completeness(book),
    }



def update_texts(book_id: str, texts: dict[str, str]) -> dict:
    """Replaces some of a book's texts (the text check's «оновити паспорт»); the rest stays as it is."""
    unknown = set(texts) - set(TEXT_KEYS)
    if unknown:
        raise ApiError(f"Невідомі тексти: {', '.join(sorted(unknown))}")
    with _lock:
        book = load(book_id)
        book["text"].update(texts)
        return save(book)


def all_books() -> list[dict]:
    books = []
    if BOOKS_DIR.exists():
        for folder in BOOKS_DIR.iterdir():
            if folder.is_dir() and re.fullmatch(r"[0-9a-f]{32}", folder.name):
                try:
                    books.append(load(folder.name))
                except ApiError as err:
                    # One broken book never hides the others — but it is not dropped silently either.
                    core.log.warning("Library: book %s not loaded (%s) — it is left out of the list", folder.name, err)
    return books


def _find_by_listing(listing_id: str) -> dict | None:
    for book in all_books():
        if str((book.get("listing") or {}).get("id")) == str(listing_id):
            return book
    return None


def _store_asset(book_id: str, source: Path, original_name: str, move: bool = False) -> dict:
    """Copies/moves a file into the book's assets folder and returns its record."""
    ext = source.suffix.lower() if source.suffix.lower() in core.IMAGE_EXTS else ""
    try:
        info = images.image_info(source)
    except Exception:
        raise ApiError(f"Файл «{original_name}» не є зображенням або пошкоджений.")
    fmt = (info.get("format") or "").upper()
    ext = ext or {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}.get(fmt, "")
    if fmt not in ("PNG", "JPEG", "WEBP"):
        raise ApiError(f"Формат {fmt or 'невідомий'} не підтримується. Використовуйте PNG, JPG або WEBP.")
    asset_id = core.new_id()
    target = _book_dir(book_id) / "assets" / f"{asset_id}{ext}"
    target.parent.mkdir(parents=True, exist_ok=True)
    if move:
        shutil.move(str(source), target)
    else:
        shutil.copy2(source, target)
    record = {
        "id": asset_id,
        "file": target.name,
        "originalName": original_name,
        "width": info["width"],
        "height": info["height"],
        "bytes": target.stat().st_size,
        "addedAt": core.now_iso(),
    }
    _add_lqip(target, record)
    return record


def _add_lqip(path: Path, record: dict) -> None:
    """Prepares the display preview now (so the page shows it instantly) and a tiny blurred stand-in."""
    try:
        preview = images.preview(path, images.display_size(record["width"], record["height"]))
        record["lqip"] = images.lqip(preview)
    except Exception:
        core.log.warning("Preview/LQIP failed for %s", path.name)


_lqip_pending: set[str] = set()


def _backfill_lqip(book_id: str) -> None:
    """Older assets get their blurred stand-ins in the background (never bumps the revision)."""
    try:
        book = load(book_id)
        todo = [a for a in _all_assets(book) if not a.get("lqip")]
        made = {}
        for asset in todo:
            path = _book_dir(book_id) / "assets" / asset["file"]
            if path.exists():
                probe = dict(asset)
                _add_lqip(path, probe)
                if probe.get("lqip"):
                    made[asset["file"]] = probe["lqip"]
        if made:
            with _lock:
                fresh = load(book_id)
                for asset in _all_assets(fresh):
                    if asset["file"] in made:
                        asset["lqip"] = made[asset["file"]]
                core.write_json(_book_dir(book_id) / "book.json", fresh)
    except Exception:
        core.log.exception("LQIP backfill failed")
    finally:
        _lqip_pending.discard(book_id)


def _delete_asset_file(book_id: str, asset: dict | None) -> None:
    if asset and asset.get("file"):
        try:
            (_book_dir(book_id) / "assets" / asset["file"]).unlink(missing_ok=True)
        except OSError:
            core.log.warning("Could not delete asset %s", asset.get("file"))


def _parse_slot(slot: str) -> tuple[str, str]:
    """'cover' | 'thumbnail' | 'page1' | 'page30' | 'spread5' | 'spread5:left' -> (key, part)."""
    if slot in ("cover", "thumbnail"):
        return slot, ""
    m = re.fullmatch(r"(page1|page30|spread(\d+))(?::(left|right|image))?", slot or "")
    if not m:
        raise ApiError("Невідома позиція зображення.")
    key = m.group(1)
    if m.group(2) and not (FIRST_SPREAD <= int(m.group(2)) <= LAST_SPREAD):
        raise ApiError("Невідомий номер розвороту.")
    part = m.group(3) or "image"
    if key in ("page1", "page30") and part != "image":
        raise ApiError("Одинарна сторінка має лише одне зображення.")
    return key, part


def _set_asset(book: dict, slot: str, asset: dict | None) -> list[dict]:
    """Places an asset; returns replaced assets that should be deleted."""
    key, part = _parse_slot(slot)
    old: list[dict] = []
    if key in ("cover", "thumbnail"):
        if book.get(key):
            old.append(book[key])
        book[key] = asset
        return old
    s = book["slots"][key]
    if part == "image":
        for p in ("image", "left", "right"):
            if s.get(p):
                old.append(s[p])
                s[p] = None
        s["image"] = asset
    else:
        if s.get("image"):
            old.append(s["image"])
            s["image"] = None
        if s.get(part):
            old.append(s[part])
        s[part] = asset
    return old


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


def agent_guide() -> str:
    """Instruction (Markdown) for a person or an AI agent preparing one book's files: the exact file names
    the batch import understands and the book-text JSON. Built from the same rules the importer uses
    (scan_folder / parse_text_json), so it cannot drift from them."""
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
    table = "\n".join(rows)
    return f"""# Як підготувати книгу для бібліотеки Book Studio

Інструкція для помічника — людини або AI-агента, — який готує файли однієї книги: перейменовує
ілюстрації й оформлює текст. Результат — папка, яку Book Studio завантажує одним рухом і сам розкладає
все по місцях.

## Що має бути в папці

- ілюстрації з назвами за таблицею нижче (PNG — найкраще; також JPG або WEBP);
- один файл тексту `book-text.json` (формат нижче).

Можна дати лише частину файлів — решту додають пізніше.

## Будова книги

30 сторінок: обкладинка, сторінка 1 — присвята, розвороти 2–15 (це сторінки 2–29), сторінка 30 —
післяслово. Розворот N — це сторінки 2N−2 і 2N−1.

| Що | Сторінки | Назва файлу |
|---|---|---|
{table}

## Правила назв файлів

1. Назва — лише номер сторінки (`12.png`) або пара сторінок розвороту через дефіс (`12-13.png`).
   Жодних інших слів, пробілів чи префіксів: `page 12.png` або `Book_12.png` буде пропущено.
2. Розворот дають або однією широкою картинкою (`12-13.png`), або двома сторінками (`12.png` і `13.png`).
3. У парі спершу менший номер — ліва сторінка: `12-13.png`, а не `13-12.png`.
4. Обкладинка — назва зі словом `cover`; найкраще просто `Cover.png`.
5. Заставка для галереї — назва зі словом `thumbnail`; найкраще `Thumbnail.png`.
6. Хвіст назви, який додає Upscayl (`12_upscayl_4x_ultrasharp-4x.png`), можна не прибирати.
7. Не обов'язково давати всі файли: наприклад, лише сторінки-ілюстрації без тексту. Що є — стане на
   своє місце, чого немає — лишиться порожнім.
8. Інших файлів у папку не клади — вони не потрібні й будуть пропущені.

## Текст книги: `book-text.json`

Точна структура — рівно ці ключі, латиницею:

```json
{template}
```

Правила:

1. Верхній рівень — об'єкт із чотирма ключами: `cover`, `page1`, `spreads`, `page30`.
2. `spreads` — об'єкт із ключами-рядками від `"2"` до `"15"`, по одному тексту на розворот.
3. Кожне значення — один рядок JSON. Перенос рядка всередині тексту пиши як `\\n`,
   порожній рядок між абзацами — як `\\n\\n`.
4. Ім'я дитини всюди пиши як `{{Name}}`, а від кого книга — як `{{Gifter}}`: з фігурними дужками і
   саме таким написанням. Book Studio підсвічує їх, а в Canva їх потім замінюють пошуком.
5. Лапки всередині тексту — `\\"`. Без коментарів і без коми після останнього елемента.
6. Кодування файлу — UTF-8.

Приклад того, як виглядає значення з переносами (фрагмент, не весь файл):

```json
"page1": "Dear {{Name}},\\n\\nWishing you a lifetime filled with God's love.\\n\\nWith love,\\n{{Gifter}}"
```

## Як завантажити в Book Studio

Відкрий паспорт книги в бібліотеці й перетягни у вікно всю папку, ZIP-архів або виділені файли —
чи натисни «Імпорт з папки» (перша іконка вгорі праворуч). Програма покаже, що куди ляже, і
попросить підтвердити.

## Перевір себе перед здачею

- [ ] обкладинка — `Cover.png`;
- [ ] сторінки — `1.png`, розвороти `2-3.png` … `28-29.png` (або окремі сторінки), `30.png`;
- [ ] у `book-text.json` є `cover`, `page1`, `spreads` з ключами "2"–"15" і `page30`;
- [ ] ім'я дитини — `{{Name}}`, від кого — `{{Gifter}}`;
- [ ] JSON без помилок (перевір будь-яким валідатором JSON).
"""


# ---------------------------------------------------------------- routes

def _book_response(book: dict) -> dict:
    out = dict(book)
    out["completeness"] = completeness(book)
    out["labels"] = {k: slot_label(k) for k in ["cover"] + SLOT_KEYS}
    return out


@route("GET", "/api/library/books")
def _list(req: Request):
    books = [summary(b) for b in all_books()]
    books.sort(key=lambda b: b.get("updatedAt") or "", reverse=True)
    return {"books": books}


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


def listing_of(body: dict) -> dict:
    """The Etsy listing a new book is tied to: the one the page checked (read only), else the link or the number
    typed in, unchecked."""
    listing = body.get("listing") if isinstance(body.get("listing"), dict) else {}
    listing_id = str(listing.get("id") or "").strip()
    if not listing_id:
        listing_id = etsy.parse_listing_ref(body.get("listingRef") or "")
        listing = {"id": listing_id, "url": f"https://www.etsy.com/listing/{listing_id}"}
    return {k: listing.get(k) for k in LISTING_FIELDS}


def create_book(listing: dict, title: str = "", canva_url: str = "", **extra) -> dict:
    """A new library book tied to its Etsy listing — «Нова книга», and a Workshop book passed on. A listing another
    book already has is refused: 409 with that book's id, so the page can open it."""
    with _lock:
        existing = _find_by_listing(str(listing["id"]))
        if existing:
            raise ApiError(f"Лістинг #{listing['id']} уже має книга «{existing.get('title')}»"
                           + (" (в архіві)." if existing.get("archived") else "."), 409, {"bookId": existing["id"]})
        book_id = core.new_id()
        book = {
            "id": book_id,
            "schema": 1,
            "rev": 0,
            "createdAt": core.now_iso(),
            "title": (title or listing.get("title") or f"Лістинг {listing['id']}").strip(),
            "listing": listing,
            "canvaUrl": canva_url.strip(),
            "archived": False,
            "cover": None,
            "thumbnail": None,
            "slots": _empty_slots(),
            "text": {k: "" for k in TEXT_KEYS},
            **extra,
        }
        _book_dir(book_id).mkdir(parents=True, exist_ok=True)
        return save(book)


def take_listing_image(book: dict) -> None:
    """The listing's main photo as the book's thumbnail — a nicety: a failure only goes to the log."""
    url = (book.get("listing") or {}).get("imageUrl")
    if url:
        try:
            _download_listing_image(book, url)
        except Exception as err:
            core.log.warning("Listing image download failed: %s", err)


@route("POST", "/api/library/books")
def _create(req: Request):
    body = req.json or {}
    book = create_book(listing_of(body), str(body.get("title") or ""), str(body.get("canvaUrl") or ""))
    if body.get("useListingImage"):
        take_listing_image(book)
    return _book_response(load(book["id"]))


@route("GET", r"/api/library/books/([0-9a-f]{32})")
def _get(req: Request):
    book = load(req.groups[0])
    if book["id"] not in _lqip_pending and any(not a.get("lqip") for a in _all_assets(book)):
        _lqip_pending.add(book["id"])
        threading.Thread(target=_backfill_lqip, args=(book["id"],), daemon=True).start()
    return _book_response(book)


@route("PATCH", r"/api/library/books/([0-9a-f]{32})")
def _patch(req: Request):
    body = req.json or {}
    with _lock:
        book = load(req.groups[0])
        if body.get("rev") is not None and int(body["rev"]) != int(book.get("rev") or 0):
            raise ApiError("Книгу змінено в іншому вікні. Оновіть сторінку.", 409)
        for key in ("title", "canvaUrl"):
            if key in body and isinstance(body[key], str):
                book[key] = body[key].strip()
        if isinstance(body.get("text"), dict):
            for key, value in body["text"].items():
                if key in TEXT_KEYS and isinstance(value, str):
                    book["text"][key] = value
        if book.get("title", "").strip() == "":
            raise ApiError("Назва книги не може бути порожньою.")
        save(book)
    return _book_response(book)


@route("POST", r"/api/library/books/([0-9a-f]{32})/archive")
def _archive(req: Request):
    archived = bool((req.json or {}).get("archived", True))
    with _lock:
        book = load(req.groups[0])
        book["archived"] = archived
        book["archivedAt"] = core.now_iso() if archived else None
        save(book)
    return _book_response(book)


@route("DELETE", r"/api/library/books/([0-9a-f]{32})")
def _delete(req: Request):
    book_id = req.groups[0]
    if jobs.running(f"library-{book_id}"):  # its import would make the folder again, without a book.json
        raise ApiError("Книга ще імпортується — видаліть її, коли імпорт завершиться.", 409)
    with _lock:
        book = load(book_id)
        src = _book_dir(book_id)
        TRASH_DIR.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        safe_title = re.sub(r"[^\w\- ]+", "", book.get("title") or "book")[:40].strip() or "book"
        target = TRASH_DIR / f"{stamp} {safe_title} {book_id[:8]}"
        shutil.move(str(src), target)
    return {"ok": True, "trash": str(target)}


@route("POST", r"/api/library/books/([0-9a-f]{32})/refresh-listing")
def _refresh_listing(req: Request):
    with _lock:
        book = load(req.groups[0])
        listing_id = (book.get("listing") or {}).get("id")
        if not listing_id:
            raise ApiError("У книги немає лістингу Etsy.")
    fresh = etsy.fetch_listing(str(listing_id))
    with _lock:
        book = load(req.groups[0])
        old_title = (book.get("listing") or {}).get("title")
        book["listing"] = fresh
        if not book.get("title") or book.get("title") == old_title:
            book["title"] = fresh["title"] or book.get("title")
        save(book)
    return _book_response(book)


def _download_listing_image(book: dict, url: str) -> None:
    if not re.match(r"^https://i\.etsystatic\.com/", url or ""):
        raise ApiError("Некоректне посилання на фото Etsy.")
    tmp = core.data_path("tmp", f"listing-{core.new_id()}.jpg")
    req = urllib.request.Request(url, headers={"User-Agent": "BookStudio"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(tmp, "wb") as f:
        shutil.copyfileobj(resp, f)
    try:
        _put_asset(book["id"], "thumbnail", _store_asset(book["id"], tmp, "etsy-listing.jpg", move=True))
    finally:
        tmp.unlink(missing_ok=True)


def _put_asset(book_id: str, slot: str, asset: dict) -> dict:
    """A picture already stored (decoded, its previews made — the slow part, outside the library's lock since
    26.09.2026: it held every other edit up to ~1.5 s per picture) goes into its slot. The record first: if the write
    fails, the old picture is still there and the new file goes."""
    with _lock:
        try:
            book = load(book_id)
            gone = _set_asset(book, slot, asset)
            save(book)
        except Exception:
            _delete_asset_file(book_id, asset)
            raise
        for old in gone:
            _delete_asset_file(book_id, old)
    return book


@route("POST", r"/api/library/books/([0-9a-f]{32})/thumbnail-from-listing")
def _thumb_from_listing(req: Request):
    book = load(req.groups[0])
    url = (book.get("listing") or {}).get("imageUrl")
    if not url:
        fresh = etsy.fetch_listing(str((book.get("listing") or {}).get("id")))
        url = fresh.get("imageUrl")
    if not url:
        raise ApiError("У лістингу Etsy немає фото.")
    _download_listing_image(book, url)
    return _book_response(load(book["id"]))


@route("POST", r"/api/library/books/([0-9a-f]{32})/assets")
def _upload_asset(req: Request):
    book_id = req.groups[0]
    slot = req.param("slot") or ""
    name = (req.param("name") or "image.png")[:200]
    _parse_slot(slot)
    load(book_id)  # 404 early
    tmp = core.data_path("tmp", f"upload-{core.new_id()}{Path(name).suffix.lower()}")
    try:
        req.body_to_file(tmp, MAX_IMAGE_BYTES)
        if req.param("auto") and re.fullmatch(r"spread\d+:(left|right)", slot):
            # A wide picture dropped on one half is a complete spread, not a single page.
            try:
                info = images.image_info(tmp)
                if info["width"] >= 1.5 * info["height"]:
                    slot = slot.split(":")[0]
            except Exception:
                pass
        book = _put_asset(book_id, slot, _store_asset(book_id, tmp, name, move=True))
    finally:
        tmp.unlink(missing_ok=True)
    return _book_response(book)


@route("DELETE", r"/api/library/books/([0-9a-f]{32})/assets")
def _remove_asset(req: Request):
    book_id = req.groups[0]
    slot = req.param("slot") or ""
    with _lock:
        book = load(book_id)
        key, part = _parse_slot(slot)
        if key in ("cover", "thumbnail"):
            old = _set_asset(book, slot, None)
        else:
            s = book["slots"][key]
            old = [s[part]] if s.get(part) else []
            s[part] = None
        save(book)          # the record first: if the write fails, the picture is still there
        for asset in old:
            _delete_asset_file(book_id, asset)
    return _book_response(book)


@route("POST", r"/api/library/books/([0-9a-f]{32})/swap")
def _swap_halves(req: Request):
    """Swaps left/right pages of a spread (fix for wrongly ordered separate pages)."""
    key = (req.json or {}).get("slot", "")
    with _lock:
        book = load(req.groups[0])
        if not re.fullmatch(r"spread\d+", key) or key not in book["slots"]:
            raise ApiError("Невідомий розворот.")
        s = book["slots"][key]
        s["left"], s["right"] = s.get("right"), s.get("left")
        save(book)
    return _book_response(book)


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


def import_pictures(book_id: str, files: list[tuple[str, Path, str]], job, step: str = "Імпорт ілюстрацій…") -> list[str]:
    """Pictures into a book's slots — (slot, file, its name) — copied and their previews prepared three at a time;
    each lands in the book as soon as it is ready (the progress runs from 5 to 95 %). Returns what wasn't taken."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    errors: list[str] = []
    done = 0
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(_store_asset, book_id, path, name): (slot, name) for slot, path, name in files}
        for fut in as_completed(futures):
            slot, name = futures[fut]
            done += 1
            job.progress(step, 5 + 90 * done / max(len(files), 1), name)
            try:
                _put_asset(book_id, slot, fut.result())
            except (ApiError, OSError) as err:
                errors.append(f"{name}: {err}")
    return errors


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


@route("POST", r"/api/library/books/([0-9a-f]{32})/open-folder")
def _open_folder(req: Request):
    desktop.open_in_explorer(_book_dir(req.groups[0]))
    return {"ok": True}


@route("POST", r"/api/library/books/([0-9a-f]{32})/open-original")
def _open_original(req: Request):
    file = (req.json or {}).get("file") or ""
    if not re.fullmatch(r"[0-9a-f]{32}\.(png|jpg|jpeg|webp)", file):
        raise ApiError("Невідомий файл.")
    desktop.open_image_file(_book_dir(req.groups[0]) / "assets" / file)
    return {"ok": True}


@route("GET", r"/media/book/([0-9a-f]{32})/([0-9a-f]{32}\.(?:png|jpg|jpeg|webp))", auth="media")
def _media(req: Request):
    path = _book_dir(req.groups[0]) / "assets" / req.groups[1]
    if not path.is_file():
        raise ApiError("Не знайдено.", 404)
    if req.param("w"):
        size = req.int_param("w", 480, 64, 4096)
        return file_response(images.preview(path, size), "image/jpeg", cache="private, max-age=31536000, immutable")
    return file_response(path, cache="private, max-age=31536000, immutable")
