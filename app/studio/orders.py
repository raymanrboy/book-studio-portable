"""Order pipeline: the Etsy order queue and one order's card (which book, where it is printed, what
the buyer wrote), and turning a Canva export into the file set the Order Creator expects.

Nothing is stored here: every answer is derived from the synced Etsy/Printify/Gelato snapshot and
the library, so opening an order always shows the current truth.
"""
from __future__ import annotations

import os
import re
import shutil
import uuid
from collections import Counter
from pathlib import Path

from . import archive, core, creator, images, library, profit, reconcile, wording
from .server import ApiError, Request, route

PRINTIFY_PAGES = 24
# The small book (14×14 cm): Etsy calls it 5" × 5" (the owner's listings), elsewhere 5.5" or 14 × 14 cm.
_SMALL = re.compile(r'5[.,]5|(?<![\d.,])5\s*(?:"|″|”|&quot;|in\b\.?|inch(?:es)?)?\s*[x×х*]\s*5(?![\d.,])'
                    r"|14\s*(?:cm|см)?\s*[x×х*]\s*14", re.I)
_LAST_NUMBER = re.compile(r"(\d+)(?=\D*$)")


# ---------------------------------------------------------------- where a book is printed

def binding_of(item: dict) -> str | None:
    """"hardcover" / "softcover" from the buyer's choice (variations, SKU or title), None when unclear."""
    label = reconcile.cover_label([item])
    hard, soft = "Hardcover" in label, "Softcover" in label
    return "hardcover" if hard and not soft else "softcover" if soft and not hard else None


def plan_for(item: dict, country_iso: str | None) -> dict:
    """Owner's rule: a hardcover going to the US is printed by Printify (24 pages, reliable there);
    everything else by Gelato (28 or 30 pages; its US hardcovers are slow, the rest is on time)."""
    binding = binding_of(item)
    country = (country_iso or "").upper()
    if binding is None:
        return {"provider": None, "binding": None, "country": country, "pages": None, "format": None}
    if binding == "hardcover" and country == "US":
        return {"provider": "printify", "binding": binding, "country": country, "pages": page_options("printify"),
                "format": None}
    text = " ".join(f"{v.get('name')} {v.get('value')}" for v in item.get("variations") or []) + " " + (item.get("title") or "")
    fmt = "hardcover_8x8" if binding == "hardcover" else ("softcover_5x5" if _SMALL.search(text) else "softcover_8x8")
    gelato = core.settings.section("gelato")
    return {"provider": "gelato", "binding": binding, "country": country, "format": fmt,
            "formatLabel": ((gelato.get("formats") or {}).get(fmt) or {}).get("label"),
            "pages": page_options("gelato")}


def page_options(provider: str) -> list[int]:
    """How many pages a book may have: Printify exactly 24; Gelato as many as were downloaded, 28 or 30."""
    return [PRINTIFY_PAGES] if provider == "printify" else creator.gelato_page_options()


def pages_word(n: int) -> str:
    return "сторінки" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else "сторінок"


# ---------------------------------------------------------------- which book

def books_by_listing() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for book in library.all_books():
        lid = str((book.get("listing") or {}).get("id") or "")
        if lid and (lid not in out or out[lid].get("archived")):  # an active book wins over an archived one
            out[lid] = book
    return out


def book_brief(book: dict | None) -> dict | None:
    if not book:
        return None
    s = library.summary(book)
    return {"id": s["id"], "title": s["title"], "image": s["image"], "lqip": s["lqip"], "archived": s["archived"],
            "canvaUrl": book.get("canvaUrl") or ""}


def enrich(order: dict, books: dict[str, dict]) -> dict:
    country = (order.get("address") or {}).get("country_iso")
    for item in order.get("items") or []:
        item["book"] = book_brief(books.get(item.get("listingId") or ""))
        item["plan"] = plan_for(item, country)
        item["childName"] = creator.guess_child_name([item])
        for v in item.get("variations") or []:
            v["custom"] = wording.custom_text(v)  # «свій текст»: the text check reads it by the same rule
            v["isName"] = bool(item["childName"]) and wording.clean_name(v.get("value")) == item["childName"]
    first = (order.get("items") or [{}])[0]
    order["book"], order["plan"] = first.get("book"), first.get("plan")
    order["childName"] = creator.guess_child_name(order.get("items") or [])
    order["pageOptions"] = {p: page_options(p) for p in ("printify", "gelato")}  # for a printer picked by hand
    return order


# ---------------------------------------------------------------- Canva export -> Cover.png + 1..N.png

def page_number(stem: str) -> int | None:
    """Page number in a file name: "12", "Madelynn - 12", "12_upscayl_4x_ultrasharp" -> 12."""
    stem = library.UPSCAYL_TAIL.sub("", stem)
    m = _LAST_NUMBER.search(stem)
    return int(m.group(1)) if m else None


def ranges(numbers: list[int]) -> str:
    """[1, 2, 3, 5, 7, 8] -> "1–3, 5, 7–8"."""
    parts, start, prev = [], None, None
    for n in sorted(numbers):
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            parts.append(f"{start}–{prev}" if prev != start else str(start))
            start = prev = n
    if start is not None:
        parts.append(f"{start}–{prev}" if prev != start else str(start))
    return ", ".join(parts)


def arrange_pages(folder: Path, counts: int | list[int]) -> dict:
    """The cover plus exactly one of `counts` pages, whatever Canva or Upscayl called them.

    The file with "cover" in its name is the cover (else the one wide picture among square pages);
    the rest are ordered by the number in their names and become 1..N. Returns the folder to print
    from (the original one when it is already named that way), N and a note on what was renumbered.
    """
    counts = sorted([counts] if isinstance(counts, int) else counts)
    if not folder.is_dir():
        raise ApiError("Папку не знайдено.")
    pngs = sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".png"
                   and not p.name.startswith(".")), key=lambda p: p.name.lower())
    if not pngs:
        raise ApiError("У папці немає PNG-файлів.")
    covers = [p for p in pngs if library.COVER_NAME.search(library.UPSCAYL_TAIL.sub("", p.stem))]
    if len(covers) > 1:
        raise ApiError(f"Кілька обкладинок: {', '.join(p.name for p in covers)}. Залиште одну.")
    rest = [p for p in pngs if p not in covers]
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
    source = [n for n, _ in numbered]
    twice = sorted(n for n, c in Counter(source).items() if c > 1)
    if twice:
        raise ApiError(f"Сторінка {', '.join(map(str, twice))} є двічі.")
    count = len(numbered)
    if count not in counts:
        need = " або ".join(map(str, counts))
        raise ApiError(f"Потрібно {need} {pages_word(counts[-1])}, а тут {count}"
                       + (f" (сторінки {ranges(source)})." if source else "."))

    plan = [(covers[0], "Cover.png")] + [(p, f"{i}.png") for i, (_, p) in enumerate(numbered, 1)]
    renumbered = source != list(range(1, count + 1))
    if all(p.name == name for p, name in plan) and len(pngs) == count + 1:
        return {"path": str(folder), "note": "", "renumbered": False, "pageCount": count}

    # A fresh folder, so the user's own files are never renamed: our dropped copies are moved,
    # anything else is linked (same disk) or copied.
    target = creator.DROPS / uuid.uuid4().hex / folder.name
    target.mkdir(parents=True)
    ours = creator.DROPS.resolve() in folder.resolve().parents
    for src, name in plan:
        dest = target / name
        if ours:
            os.replace(src, dest)
            continue
        try:
            os.link(src, dest)
        except OSError:
            shutil.copy2(src, dest)
    note = f"сторінки {ranges(source)} → 1–{count}" if renumbered else ""
    if covers[0].name != "Cover.png":
        note = (note + "; " if note else "") + f"обкладинка — {covers[0].name}"
    return {"path": str(target), "note": note, "renumbered": renumbered, "pageCount": count}


# ---------------------------------------------------------------- routes

@route("GET", "/api/orders")
def _list(req: Request):
    books = books_by_listing()
    orders = [enrich(o, books) for o in profit.picker_orders()]
    return {"orders": orders, "syncedAt": profit.load_snapshot().get("syncedAt")}


@route("GET", r"/api/orders/(\d{5,20})")
def _one(req: Request):
    rid = req.groups[0]
    order = next((o for o in profit.picker_orders() if o["receiptId"] == rid), None)
    if not order:
        raise ApiError("Замовлення не знайдено або його скасовано.", 404)
    receipt = next((r for r in profit.load_snapshot().get("receipts") or [] if r["receipt_id"] == rid), {})
    order["buyerMessage"] = profit.plain(receipt.get("message_from_buyer"))
    # a send of this order that never went to print (cancelled, a deleted draft): its files can be taken again
    order["earlierSends"] = archive.earlier_sends(rid)
    # a draft or a book of it already at a printer: replacing a page there first asks (the card's own
    # memory of a send is gone after a restart)
    order["atPrinter"] = archive.at_printer(rid)
    return enrich(order, books_by_listing())


@route("POST", r"/api/orders/(\d{5,20})/files")
def _files(req: Request):
    body = req.json or {}
    provider = body.get("provider")
    if provider not in ("printify", "gelato"):
        raise ApiError("Невідомий постачальник.")
    res = arrange_pages(Path(str(body.get("folder") or "").strip().strip('"')), page_options(provider))
    # Told at once when Gelato does not print this length in the order's format (its catalog decides).
    problem = creator.gelato_pages_problem(str(body.get("format") or ""), res["pageCount"]) if provider == "gelato" else None
    if problem:
        raise ApiError(problem)
    return res
