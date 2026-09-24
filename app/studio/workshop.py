"""The Workshop (the Listings mode): books still in development.

The owner (24.09.2026): "a place where I create books before sending them to the library with orders". Every
row of a book — the cover, the dedication, spreads 2–15, the afterword — holds a prompt for its picture, the
picture itself (a 2:1 spread) and the text. Prompts and texts come first, typed in or from one JSON an agent
writes (the instruction for it is made here); the pictures come last, one per frame.

A Workshop book is a library book marked "stage": "workshop" — library.py keeps it, its pictures and previews,
and never shows it to the orders. «Передати в бібліотеку» removes the mark and writes the Etsy listing: nothing
is copied. Plan and agreements: wiki/plans/listings-mode.md.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import core, desktop, etsy, library
from .server import ApiError, Request, route

GUIDE_NAME = "Book Studio — промпти й тексти книги.md"
LISTING_FIELDS = ("id", "title", "state", "shopId", "url", "imageUrl", "verifiedAt")


def create(title: str) -> dict:
    """A new book in the Workshop: a title is all it needs — no Etsy listing yet."""
    title = (title or "").strip()
    if not title:
        raise ApiError("Вкажіть назву книги.")
    with library._lock:
        book_id = core.new_id()
        book = {
            "id": book_id, "schema": 1, "rev": 0, "createdAt": core.now_iso(), "stage": library.WORKSHOP,
            "title": title[:200], "listing": {}, "canvaUrl": "", "notes": "", "archived": False,
            "cover": None, "thumbnail": None, "slots": library._empty_slots(),
            "text": {k: "" for k in library.TEXT_KEYS}, "prompts": {k: "" for k in library.PROMPT_KEYS},
        }
        library._book_dir(book_id).mkdir(parents=True, exist_ok=True)
        library.save(book)
    core.log.info("Workshop: a new book «%s»", book["title"])
    return library.load(book_id)


def _workshop_book(book_id: str) -> dict:
    book = library.load(book_id)
    if not library.is_workshop(book):
        raise ApiError("Ця книга вже в бібліотеці замовлень, а не в Майстерні.", 409)
    return book


def import_json(book_id: str, raw: str, dry_run: bool = False) -> dict:
    """Prompts and texts from one JSON (the Workshop's, or the library's text-only one). dry_run only counts
    what would change: the page asks before anything already written is replaced."""
    text, prompts, no_text, no_prompt, notes = library.parse_book_json(raw)
    if not text and not prompts:
        raise ApiError("У JSON не знайдено ні промптів, ні текстів.")
    with library._lock:
        book = _workshop_book(book_id)
        replaced = lambda old, new: sum(1 for k, v in new.items() if (old.get(k) or "").strip() not in ("", v))  # noqa: E731
        result = {"prompts": len(prompts), "texts": len(text),
                  "replaces": {"prompts": replaced(book["prompts"], prompts), "texts": replaced(book["text"], text)},
                  "missing": {"prompts": no_prompt, "texts": no_text}, "notes": notes}
        if dry_run:
            return result
        book["prompts"].update(prompts)
        book["text"].update(text)
        library.save(book)
    result["book"] = library._book_response(book)
    return result


def to_library(book_id: str, body: dict) -> dict:
    """«Передати в бібліотеку»: the book gets its Etsy listing and leaves the Workshop; from now on orders find
    it. A listing already tied to a library book is refused (the page offers to open that book)."""
    listing = body.get("listing") if isinstance(body.get("listing"), dict) else {}
    listing_id = str(listing.get("id") or "").strip()
    if not listing_id:
        listing_id = etsy.parse_listing_ref(body.get("listingRef") or "")
        listing = {"id": listing_id, "url": f"https://www.etsy.com/listing/{listing_id}"}
    with library._lock:
        book = _workshop_book(book_id)
        other = library._find_by_listing(listing_id)
        if other:
            raise ApiError(f"Лістинг #{listing_id} уже має книга «{other.get('title')}»"
                           + (" (в архіві)." if other.get("archived") else "."), 409, {"bookId": other["id"]})
        book.pop("stage", None)
        book["listing"] = {k: listing.get(k) for k in LISTING_FIELDS}
        book["fromWorkshopAt"] = core.now_iso()
        library.save(book)
    core.log.info("Workshop: «%s» passed to the library, listing %s", book.get("title"), listing_id)
    if body.get("useListingImage") and listing.get("imageUrl"):
        try:
            library._download_listing_image(book, listing["imageUrl"])
        except Exception as err:  # the book is in the library already; only the thumbnail is missing
            core.log.warning("Workshop: the listing's photo was not taken: %s", err)
    return library._book_response(library.load(book_id))


def guide() -> str:
    """The instruction (Markdown) for an AI agent writing a book's prompts and texts: the book's structure and
    the exact JSON the Workshop reads (parse_book_json) — a test keeps the example readable."""
    pages = lambda n: "{}–{}".format(*library.spread_pages(n))  # noqa: E731
    template = json.dumps({
        "cover": {"prompt": "Промпт обкладинки: уся обкладинка 2:1 — задня половина ліворуч, лицьова праворуч",
                  "text": "Назва книги з {Name}"},
        "page1": {"prompt": "Промпт ілюстрації присвяти (сторінка 1)", "text": "Текст присвяти"},
        "spreads": {str(n): {"prompt": f"Промпт розвороту {n}: одна широка ілюстрація 2:1 на сторінки {pages(n)}",
                             "text": f"Текст розвороту {n}"} for n in library.SPREAD_NUMBERS},
        "page30": {"prompt": "Промпт ілюстрації післяслова (сторінка 30)", "text": "Текст післяслова"},
    }, ensure_ascii=False, indent=2)
    return f"""# Промпти й тексти книги для Майстерні Book Studio

Інструкція для AI-агента, який пише нову дитячу книгу: промпт для кожної ілюстрації й текст кожної
сторінки. Відповідь — один JSON, який Book Studio заливає в Майстерню одним рухом.

## Будова книги

- **Обкладинка** — одна широка картинка 2:1: задня половина ліворуч, лицьова праворуч.
- **Сторінка 1 — присвята**, **сторінка 30 — післяслово**: поодинокі сторінки.
- **Розвороти 2–15** — це сторінки 2–29 парами: розворот N — сторінки 2N−2 і 2N−1.
- Кожен розворот — **одна широка ілюстрація у пропорції 2:1 на обидві сторінки**, а не дві окремі.

## Формат відповіді

Поверни **лише JSON**, без пояснень до чи після нього. Точна структура — рівно ці ключі, латиницею:

```json
{template}
```

## Правила

1. Верхній рівень — об'єкт із ключами `cover`, `page1`, `spreads`, `page30`.
2. `spreads` — об'єкт із ключами-рядками від `"2"` до `"15"`.
3. Кожне значення — об'єкт із двома рядками: `prompt` (промпт ілюстрації) і `text` (текст сторінки).
4. Промпт розвороту описує одну сцену на весь розворот 2:1.
5. Ім'я дитини всюди пиши як `{{Name}}`, а від кого книга — як `{{Gifter}}`: з фігурними дужками і саме
   таким написанням.
6. Перенос рядка всередині тексту — `\\n`, порожній рядок між абзацами — `\\n\\n`. Лапки всередині —
   `\\"`. Без коментарів і без коми після останнього елемента.

## Як завантажити в Book Studio

Book Studio → режим «Лістинги» → Майстерня → книга → кнопка `{{ }}` → «Вставити JSON» (або перетягни
файл `.json` на сторінку книги).
"""


# ---------------------------------------------------------------- routes

@route("POST", "/api/workshop/books")
def _create(req: Request):
    return library._book_response(create(str((req.json or {}).get("title") or "")))


@route("POST", r"/api/workshop/books/([0-9a-f]{32})/json")
def _import(req: Request):
    body = req.json or {}
    raw = body.get("json")
    if not isinstance(raw, str) or not raw.strip():
        raise ApiError("Порожній JSON.")
    return import_json(req.groups[0], raw, bool(body.get("dryRun")))


@route("GET", r"/api/workshop/books/([0-9a-f]{32})/json")
def _export(req: Request):
    return library.export_book_json(_workshop_book(req.groups[0]))


@route("POST", r"/api/workshop/books/([0-9a-f]{32})/to-library")
def _to_library(req: Request):
    return to_library(req.groups[0], req.json or {})


@route("GET", "/api/workshop/guide")
def _guide(req: Request):
    return {"name": GUIDE_NAME, "text": guide()}


@route("POST", "/api/workshop/guide/save")
def _guide_save(req: Request):
    folder = Path(str((req.json or {}).get("folder") or ""))
    if not folder.is_dir():
        raise ApiError("Папку не знайдено.")
    target = folder / GUIDE_NAME
    target.write_text(guide(), encoding="utf-8")
    try:
        desktop.open_in_explorer(target)  # shows the file selected, ready to drag into a chat with an agent
    except OSError:
        pass
    return {"path": str(target)}
