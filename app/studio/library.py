"""Book library: one reference book per Etsy listing.

Book structure (30 physical pages, same as the production pipeline):
  cover                      — full cover spread
  page1                      — dedication (single right-hand page)
  spread2 … spread15         — story spreads, pages 2-3 … 28-29
  page30                     — afterword (single left-hand page)
A spread image is either one combined picture or separate left/right pages.
Everything except the listing is optional and can be added any time.

A book's files in and out — the text JSON, the folder import, the export, the guide for whoever prepares a book —
are in library_files.py.

A book made in the Listings mode's Workshop comes here when it is passed on (workshop/books.py, to_library()): a
library book with its texts and listing that takes its cover and pages from the Workshop book's folder — no copy of
them here ("workshop", "pagesFrom"; below).
"""
from __future__ import annotations

import filecmp
import re
import shutil
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

from . import core, desktop, etsy, images
from .jobs import jobs
from .server import ApiError, Request, file_response, route

BOOKS_DIR = core.data_path("library", "books")
TRASH_DIR = core.data_path("library", "trash")
TRASH_ASSETS = core.data_path("library", "trash-assets")  # a picture the owner removed from a book: kept, with where it was
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


def _read(book_id: str) -> dict:
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


def load(book_id: str) -> dict:
    """A book as it is now — a Workshop book's cover and pages as its folder has them (`follow()`)."""
    book = _read(book_id)
    return follow(book_id, book) if from_workshop(book) else book


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
            path = asset_path(book, asset)
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
    if asset and asset.get("file") and not asset.get("workshop"):  # a Workshop page is the Workshop's file
        try:
            (_book_dir(book_id) / "assets" / asset["file"]).unlink(missing_ok=True)
        except OSError:
            core.log.warning("Could not delete asset %s", asset.get("file"))


def _trash_asset(book_id: str, slot: str, asset: dict | None) -> str | None:
    """«Прибрати картинку» (2026-09-30): the picture is not deleted but set aside, with a note of where it was, so that
    «Скасувати» can put it back (`_restore_asset`). A Workshop page is the Workshop's file — only the record is noted."""
    if not asset:
        return None
    folder = TRASH_ASSETS / book_id
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{time.strftime('%Y%m%d-%H%M%S')}-{asset.get('file') or 'record'}"
    if asset.get("file") and not asset.get("workshop"):
        src = _book_dir(book_id) / "assets" / asset["file"]
        if src.exists():
            shutil.move(str(src), folder / name)
    core.write_json(folder / f"{name}.json", {"slot": slot, "asset": asset})
    return name


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


def _slot_asset(book: dict, slot: str) -> dict | None:
    key, part = _parse_slot(slot)
    return book.get(key) if key in ("cover", "thumbnail") else book["slots"][key].get(part)


# ---------------------------------------------------------------- a Workshop book's pages, where they are
# A book passed on from the Workshop keeps its cover and pages there — no copy of them here (the owner, 27.09.2026:
# "one place, no doubles"). The library book names the Workshop's folder ("workshop") and says its pages are that
# folder's ("pagesFrom": "workshop"): on every load they are the files in its pictures/ as they are now. A page's record
# keeps what is slow to work out (its size, previews, blurred stand-in) until its file changes — then it gets a new id,
# so the page's address changes and no old picture stays cached. Such pages are changed in the Workshop only (it
# mirrors and cuts a spread the way the book needs); the thumbnail stays the library's own.

PAGES_FROM_WORKSHOP = "workshop"
# (slot, the page's file name without its suffix) in a Workshop book's pictures/: Cover, 1, a spread's two pages, 30.
WORKSHOP_PAGES = ([("cover", "Cover"), ("page1", "1")]
                  + [(f"spread{n}:{part}", str(page)) for n in SPREAD_NUMBERS
                     for part, page in zip(("left", "right"), spread_pages(n))]
                  + [("page30", "30")])


def from_workshop(book: dict) -> bool:
    return book.get("pagesFrom") == PAGES_FROM_WORKSHOP


def _workshop_pictures(book: dict) -> Path | None:
    """The pictures/ folder of the Workshop book this one takes its pages from; None for a name that isn't one."""
    from .workshop.books import PICTURES
    name = str(book.get("workshop") or "")
    if not name or name != Path(name).name or name.startswith("."):
        return None
    return core.WORKSHOP_BOOKS / name / PICTURES


def asset_path(book: dict, asset: dict) -> Path:
    """Where an asset's file is: a Workshop page in the Workshop's folder, anything else in the book's assets/."""
    if asset.get("workshop"):
        folder = _workshop_pictures(book)
        if folder is not None:
            return folder / Path(asset["workshop"]).name
    return _book_dir(book["id"]) / "assets" / asset["file"]


def _workshop_now(book: dict) -> list[tuple[str, Path | None, list | None]]:
    """(slot, its file, [modified, size]) of every page as the Workshop's folder has it now; no file — None."""
    from .workshop.books import _names, picture
    folder = _workshop_pictures(book)
    names = set(_names(folder)) if folder is not None else set()
    out = []
    for slot, page in WORKSHOP_PAGES:
        path = stamp = None
        name = picture(names, page)
        if name:
            try:
                st = (folder / name).stat()
                path, stamp = folder / name, [st.st_mtime_ns, st.st_size]
            except OSError:
                pass
        out.append((slot, path, stamp))
    return out


def _is_now(asset: dict | None, path: Path | None, stamp: list | None) -> bool:
    if path is None:
        return asset is None
    return bool(asset) and asset.get("workshop") == path.name and asset.get("stamp") == stamp


def _workshop_record(path: Path, stamp: list) -> dict | None:
    try:
        info = images.image_info(path)
    except Exception:
        core.log.warning("Library: the Workshop's page %s is not a readable picture", path)
        return None
    asset_id = core.new_id()
    record = {"id": asset_id, "file": f"{asset_id}{path.suffix.lower()}", "originalName": path.name,
              "width": info["width"], "height": info["height"], "bytes": stamp[1], "addedAt": core.now_iso(),
              "workshop": path.name, "stamp": stamp}
    _add_lqip(path, record)
    return record


def follow(book_id: str, book: dict | None = None, progress=None) -> dict:
    """A Workshop book's cover and pages as its folder has them now. Records are made only for new or changed files,
    outside the lock (a page's previews take a moment), and written without a new revision — an edit on an open
    passport isn't refused because a page changed in the Workshop. `progress(i, n)` — each record made."""
    book = book if book is not None else _read(book_id)
    stale = [(slot, path, stamp) for slot, path, stamp in _workshop_now(book)
             if not _is_now(_slot_asset(book, slot), path, stamp)]
    if not stale:
        return book
    made: dict[str, dict | None] = {}
    for i, (slot, path, stamp) in enumerate(stale, 1):
        if path is not None:
            made[slot] = _workshop_record(path, stamp)
        if progress:
            progress(i, len(stale))
    with _lock:
        fresh = _read(book_id)
        if not from_workshop(fresh):
            return fresh
        for slot, path, stamp in _workshop_now(fresh):
            if _is_now(_slot_asset(fresh, slot), path, stamp):
                continue
            record = made.get(slot)
            if path is not None and not _is_now(record, path, stamp):
                continue  # it changed again meanwhile: the next load makes its record
            _set_asset(fresh, slot, record)
        core.write_json(_book_dir(book_id) / "book.json", fresh)
        return fresh


def _workshop_assets(book: dict) -> list[dict]:
    return [a for a in (_slot_asset(book, slot) for slot, _ in WORKSHOP_PAGES) if a and a.get("workshop")]


def workshop_pages(book: dict) -> dict:
    """How many of the Workshop's pages the book shows, and the files it can't (not a readable picture)."""
    shown = {a["workshop"] for a in _workshop_assets(book)}
    files = [path.name for _, path, _ in _workshop_now(book) if path is not None]
    return {"found": len(shown), "unreadable": [f"{name}: не читається як картинка" for name in files if name not in shown]}


def keep_pages(book_id: str) -> int:
    """Before its Workshop book goes to the Recycle Bin: its pages are copied here, and from then on the library
    book keeps them itself, like any book. Returns how many were copied."""
    book = load(book_id)
    if not from_workshop(book):
        return 0
    target = _book_dir(book_id) / "assets"
    target.mkdir(parents=True, exist_ok=True)
    kept: dict[str, dict] = {}
    for slot, _ in WORKSHOP_PAGES:
        asset = _slot_asset(book, slot)
        if asset and asset.get("workshop"):
            own = {k: v for k, v in asset.items() if k not in ("workshop", "stamp")}
            try:
                shutil.copy2(asset_path(book, asset), target / own["file"])
            except OSError as err:
                raise ApiError(f"Не вдалося скопіювати сторінки в бібліотеку ({err}) — книгу з Майстерні не видалено.")
            kept[slot] = own
    with _lock:
        fresh = _read(book_id)
        for slot, _ in WORKSHOP_PAGES:
            asset = _slot_asset(fresh, slot)
            if slot in kept or (asset and asset.get("workshop")):
                _set_asset(fresh, slot, kept.get(slot))
        fresh.pop("pagesFrom", None)
        save(fresh)
    core.log.info("Library: %s keeps its %d pages — its Workshop book is going", book_id, len(kept))
    return len(kept)


def link_workshop_books() -> None:
    """Books passed on from the Workshop before 27.09.2026 kept a copy of its pages here. Where every copied page is
    the Workshop's file byte for byte, the book takes its pages from the Workshop instead and the copies go to the
    Recycle Bin; a book with a page that differs (changed here after it was passed on) is left as it is. At start-up,
    in the background; a book done once isn't looked at again."""
    for book in all_books():
        if book.get("workshop") and not from_workshop(book):
            try:
                _link_copied(book)
            except Exception:
                core.log.exception("Library: %s not moved onto its Workshop book's pages", book["id"])


def _link_copied(book: dict) -> bool:
    folder = _workshop_pictures(book)
    if folder is None or not folder.is_dir():
        return False
    if any(s.get("image") for key, s in book["slots"].items() if key.startswith("spread")):
        return False  # a spread in one picture: not how the Workshop keeps it
    now = {slot: path for slot, path, _ in _workshop_now(book)}
    copies = {slot: _slot_asset(book, slot) for slot, _ in WORKSHOP_PAGES}
    for slot, asset in copies.items():
        if asset and not (now[slot] and filecmp.cmp(asset_path(book, asset), now[slot], shallow=False)):
            core.log.info("Library: %s keeps its own pages — %s differs from its Workshop book's", book["id"], slot)
            return False
    with _lock:
        fresh = _read(book["id"])
        if fresh.get("rev") != book.get("rev"):
            return False  # changed meanwhile: looked at again at the next start
        for slot, _ in WORKSHOP_PAGES:
            _set_asset(fresh, slot, None)
        fresh["pagesFrom"] = PAGES_FROM_WORKSHOP
        save(fresh)
    follow(book["id"])
    files = [asset_path(book, a) for a in copies.values() if a]
    if files:
        bin_folder = _book_dir(book["id"]) / f"copied-pages-{time.strftime('%Y%m%d-%H%M%S')}"
        bin_folder.mkdir()
        for f in files:
            shutil.move(str(f), bin_folder / f.name)
        try:
            desktop.to_recycle_bin(bin_folder)
        except OSError as err:
            core.log.warning("Library: the copied pages of %s stay in %s (%s)", book["id"], bin_folder, err)
    core.log.info("Library: %s takes its pages from the Workshop; %d copies went to the Recycle Bin", book["id"],
                  len(files))
    return True


def _own_slot(book: dict, slot: str) -> None:
    """A Workshop book's cover and pages are changed in the Workshop — the passport only shows them."""
    if from_workshop(book) and slot != "thumbnail":
        raise ApiError("Обкладинка й сторінки цієї книги — у Майстерні: змініть їх там.", 409)


# ---------------------------------------------------------------- routes

def _book_response(book: dict) -> dict:
    out = dict(book)
    out["completeness"] = completeness(book)
    out["labels"] = {k: slot_label(k) for k in ["cover"] + SLOT_KEYS}
    if from_workshop(book):
        from .workshop.books import display_name
        folder = _workshop_pictures(book)
        out["workshopName"] = display_name(book["workshop"])
        out["workshopMissing"] = folder is None or not folder.parent.is_dir()  # its folder renamed or gone
    return out


@route("GET", "/api/library/books")
def _list(req: Request):
    books = [summary(b) for b in all_books()]
    books.sort(key=lambda b: b.get("updatedAt") or "", reverse=True)
    return {"books": books}


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
    return {"ok": True, "trash": str(target), "trashName": target.name}


@route("POST", r"/api/library/trash/restore")
def _restore(req: Request):
    """«Скасувати» after a book was removed (2026-09-30): the folder goes back from `data/library/trash`. Only a folder
    that is really in the trash, only to its own place, never over a book that is there now."""
    name = str((req.json or {}).get("name") or "")
    if not name or name != Path(name).name:
        raise ApiError("Невідома книга в кошику.")
    src = TRASH_DIR / name
    if not src.is_dir():
        raise ApiError("Цієї книги вже немає в кошику бібліотеки.", 404)
    book_id = str((core.read_json(src / "book.json") or {}).get("id") or "")
    with _lock:
        dest = _book_dir(book_id)
        if dest.exists():
            raise ApiError("Книга з цим номером уже є в бібліотеці.", 409)
        shutil.move(str(src), dest)
    return {"ok": True, "id": book_id}


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
            _own_slot(book, slot)
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
    _own_slot(load(book_id), slot)  # 404 early; a Workshop book's page is changed there
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
        _own_slot(book, slot)
        if key in ("cover", "thumbnail"):
            old = _set_asset(book, slot, None)
        else:
            s = book["slots"][key]
            old = [s[part]] if s.get(part) else []
            s[part] = None
        save(book)          # the record first: if the write fails, the picture is still there
        trashed = [_trash_asset(book_id, slot, asset) for asset in old]
    out = _book_response(book)
    out["trashAsset"] = next((t for t in trashed if t), None)
    return out


@route("POST", r"/api/library/books/([0-9a-f]{32})/assets/restore")
def _restore_asset(req: Request):
    """«Скасувати» after a picture was removed from a book: the file and its place come back — only into a place that
    is empty now, never over another picture."""
    book_id = req.groups[0]
    name = str((req.json or {}).get("name") or "")
    if not name or name != Path(name).name:
        raise ApiError("Невідома картинка в кошику.")
    folder = TRASH_ASSETS / _book_dir(book_id).name
    meta = core.read_json(folder / f"{name}.json")
    if not meta or not meta.get("slot") or not isinstance(meta.get("asset"), dict):
        raise ApiError("Цієї картинки вже немає в кошику.", 404)
    slot, asset = meta["slot"], meta["asset"]
    with _lock:
        book = load(book_id)
        _own_slot(book, slot)
        key, part = _parse_slot(slot)
        if key in ("cover", "thumbnail"):
            taken = bool(book.get(key))
        else:
            s = book["slots"][key]
            taken = any(s.get(p) for p in ("image", "left", "right")) if part == "image" else bool(s.get(part) or s.get("image"))
        if taken:
            raise ApiError("Це місце вже зайняла інша картинка.", 409)
        if asset.get("file") and not asset.get("workshop"):
            src, dest = folder / name, _book_dir(book_id) / "assets" / asset["file"]
            if not src.exists():
                raise ApiError("Файл картинки вже немає в кошику.", 404)
            if dest.exists():
                raise ApiError("Файл із такою назвою вже є в книзі.", 409)
            shutil.move(str(src), dest)
        _set_asset(book, slot, asset)
        save(book)
        (folder / f"{name}.json").unlink(missing_ok=True)
    return _book_response(book)


@route("POST", r"/api/library/books/([0-9a-f]{32})/swap")
def _swap_halves(req: Request):
    """Swaps left/right pages of a spread (fix for wrongly ordered separate pages)."""
    key = (req.json or {}).get("slot", "")
    with _lock:
        book = load(req.groups[0])
        if not re.fullmatch(r"spread\d+", key) or key not in book["slots"]:
            raise ApiError("Невідомий розворот.")
        _own_slot(book, key)
        s = book["slots"][key]
        s["left"], s["right"] = s.get("right"), s.get("left")
        save(book)
    return _book_response(book)


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


@route("POST", r"/api/library/books/([0-9a-f]{32})/open-folder")
def _open_folder(req: Request):
    book = load(req.groups[0])
    pages = _workshop_pictures(book) if from_workshop(book) else None
    desktop.open_in_explorer(pages if pages is not None and pages.is_dir() else _book_dir(book["id"]))
    return {"ok": True}


@route("POST", r"/api/library/books/([0-9a-f]{32})/open-original")
def _open_original(req: Request):
    file = (req.json or {}).get("file") or ""
    if not re.fullmatch(r"[0-9a-f]{32}\.(png|jpg|jpeg|webp)", file):
        raise ApiError("Невідомий файл.")
    desktop.open_image_file(_file_of(req.groups[0], file))
    return {"ok": True}


def _file_of(book_id: str, name: str) -> Path:
    """An asset's file by its name: in the book's assets/, or a Workshop page in the Workshop's folder."""
    path = _book_dir(book_id) / "assets" / name
    if path.is_file():
        return path
    book = load(book_id)
    asset = next((a for a in _workshop_assets(book) if a["file"] == name), None)
    return asset_path(book, asset) if asset else path


@route("GET", r"/media/book/([0-9a-f]{32})/([0-9a-f]{32}\.(?:png|jpg|jpeg|webp))", auth="media")
def _media(req: Request):
    path = _file_of(req.groups[0], req.groups[1])
    if not path.is_file():
        raise ApiError("Не знайдено.", 404)
    if req.param("w"):
        size = req.int_param("w", 480, 64, 4096)
        return file_response(images.preview(path, size), "image/jpeg", cache="private, max-age=31536000, immutable")
    return file_response(path, cache="private, max-age=31536000, immutable")
