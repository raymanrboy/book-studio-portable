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
from pathlib import Path

from . import archive, core, creator, drops, library, printify, reconcile, records, stages, wording
from .server import ApiError, Request, route

PRINTIFY_PAGES = 24
# The small book (14×14 cm): Etsy calls it 5" × 5" (the owner's listings), elsewhere 5.5" or 14 × 14 cm.
_SMALL = re.compile(r'5[.,]5|(?<![\d.,])5\s*(?:"|″|”|&quot;|in\b\.?|inch(?:es)?)?\s*[x×х*]\s*5(?![\d.,])'
                    r"|14\s*(?:cm|см)?\s*[x×х*]\s*14", re.I)


# ---------------------------------------------------------------- where a book is printed

def binding_of(item: dict) -> str | None:
    """"hardcover" / "softcover" from the buyer's choice (variations, SKU or title), None when unclear."""
    return reconcile.item_format(item)


def printing() -> dict:
    """What the printer rule reads from the settings — each printer's page counts, the Gelato formats — read once for
    a whole queue, not three times for every book in it. From 1 October 2026 only Gelato prints (printify.retired())."""
    gelato_only = printify.retired()
    return {"pages": {p: page_options(p) for p in (("gelato",) if gelato_only else ("printify", "gelato"))},
            "formats": core.settings.section("gelato").get("formats") or {}, "gelatoOnly": gelato_only}


def plan_for(item: dict, country_iso: str | None, rules: dict | None = None) -> dict:
    """Owner's rule: a hardcover going to the US is printed by Printify (24 pages, reliable there);
    everything else by Gelato (28 or 30 pages; its US hardcovers are slow, the rest is on time).

    For now (owner, 25.09.2026 — Printify prints faulty books) the owner decides every hardcover himself,
    by the files he downloads: 24 pages → Printify, 28 or 30 → Gelato (`choice`, `provider_by_pages()`).
    The rule's printer stays as the suggestion the queue shows. Softcovers, the small one included, are Gelato's.

    From 1 October 2026 (owner, 29.09.2026) every book is Gelato's, a US hardcover too; a book whose cover type
    could not be read goes to Gelato as well, its format picked in the Order Creator.
    """
    rules = rules or printing()
    binding = binding_of(item)
    country = (country_iso or "").upper()
    if binding is None:
        if rules.get("gelatoOnly"):
            return {"provider": "gelato", "binding": None, "country": country, "pages": rules["pages"]["gelato"],
                    "format": None}
        return {"provider": None, "binding": None, "country": country, "pages": None, "format": None}
    text = " ".join(f"{v.get('name')} {v.get('value')}" for v in item.get("variations") or []) + " " + (item.get("title") or "")
    fmt = "hardcover_8x8" if binding == "hardcover" else ("softcover_5x5" if _SMALL.search(text) else "softcover_8x8")
    plan = {"provider": "gelato", "binding": binding, "country": country, "format": fmt,
            "formatLabel": (rules["formats"].get(fmt) or {}).get("label"), "pages": rules["pages"]["gelato"]}
    if binding == "hardcover" and not rules.get("gelatoOnly"):
        choice = dict(rules["pages"])
        plan.update(choice=choice, pages=sorted({n for pages in choice.values() for n in pages}),
                    provider="printify" if country == "US" else "gelato")
    return plan


def page_options(provider: str) -> list[int]:
    """How many pages a book may have: Printify exactly 24; Gelato as many as were downloaded, 28 or 30."""
    return [PRINTIFY_PAGES] if provider == "printify" else creator.gelato_page_options()


def provider_by_pages(count: int) -> str:
    """A hardcover the owner decides by its files: 24 pages are Printify's, 28 or 30 Gelato's."""
    return "printify" if count == PRINTIFY_PAGES else "gelato"


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


def enrich(order: dict, books: dict[str, dict], rules: dict | None = None) -> dict:
    rules = rules or printing()
    country = (order.get("address") or {}).get("country_iso")
    for item in order.get("items") or []:
        item["book"] = book_brief(books.get(item.get("listingId") or ""))
        item["plan"] = plan_for(item, country, rules)
        item["childName"] = wording.guess_child_name([item])
        for v in item.get("variations") or []:
            v["custom"] = wording.custom_text(v)  # «свій текст»: the text check reads it by the same rule
            v["isName"] = bool(item["childName"]) and wording.clean_name(v.get("value")) == item["childName"]
    first = (order.get("items") or [{}])[0]
    order["book"], order["plan"] = first.get("book"), first.get("plan")
    order["childName"] = next((i["childName"] for i in order.get("items") or [] if i.get("childName")), "")
    order["pageOptions"] = rules["pages"]  # for a printer picked by hand
    return order


# ---------------------------------------------------------------- Canva export -> Cover.png + 1..N.png

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
    cover, numbered = drops.export_files(folder)
    source = [n for n, _ in numbered]
    count = len(numbered)
    if count not in counts:
        need = ", ".join(map(str, counts[:-1])) + " або " + str(counts[-1]) if len(counts) > 1 else str(counts[0])
        raise ApiError(f"Потрібно {need} {pages_word(counts[-1])}, а тут {count}"
                       + (f" (сторінки {ranges(source)})." if source else "."))

    plan = [(cover, "Cover.png")] + [(p, f"{i}.png") for i, (_, p) in enumerate(numbered, 1)]
    renumbered = source != list(range(1, count + 1))
    pngs = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".png" and not p.name.startswith(".")]
    if all(p.name == name for p, name in plan) and len(pngs) == count + 1:
        return {"path": str(folder), "note": "", "renumbered": False, "pageCount": count}

    # A fresh folder, so the user's own files are never renamed: our dropped copies are moved,
    # anything else is linked (same disk) or copied.
    target = drops.DROPS / uuid.uuid4().hex / folder.name
    target.mkdir(parents=True)
    ours = core.inside(folder, drops.DROPS)
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
    if cover.name != "Cover.png":
        note = (note + "; " if note else "") + f"обкладинка — {cover.name}"
    return {"path": str(target), "note": note, "renumbered": renumbered, "pageCount": count}


# ---------------------------------------------------------------- routes

@route("GET", "/api/orders")
def _list(req: Request):
    books, rules = books_by_listing(), printing()
    orders = [enrich(o, books, rules) for o in stages.picker_orders()]
    return {"orders": orders, "syncedAt": records.load_snapshot().get("syncedAt")}


@route("GET", r"/api/orders/(\d{5,20})")
def _one(req: Request):
    rid = req.groups[0]
    order = stages.picker_order(rid)
    if not order:
        raise ApiError("Замовлення не знайдено або його скасовано.", 404)
    order["buyerMessage"] = stages.facts()["receipts"][rid]["receipt"].get("message_from_buyer") or ""
    # a send of this order that never went to print (cancelled, a deleted draft): its files can be taken again;
    # a draft or a book of it already at a printer: replacing a page there first asks (the card's own memory of
    # a send is gone after a restart)
    order.update(archive.card_facts(rid))
    return enrich(order, books_by_listing())


@route("POST", r"/api/orders/(\d{5,20})/files")
def _files(req: Request):
    body = req.json or {}
    provider = body.get("provider")
    if provider not in ("printify", "gelato", "files"):
        raise ApiError("Невідомий постачальник.")
    if printify.retired():
        if provider == "printify":
            raise ApiError(printify.RETIRED_TEXT)
        if provider == "files":
            provider = "gelato"  # a card opened before 1 October: only Gelato's lengths now
    # "files": a hardcover whose printer the downloaded files decide (plan_for's `choice`).
    counts = sorted({*page_options("printify"), *page_options("gelato")}) if provider == "files" else page_options(provider)
    res = arrange_pages(Path(str(body.get("folder") or "").strip().strip('"')), counts)
    if provider == "files":
        provider = provider_by_pages(res["pageCount"])
    res["provider"] = provider
    # Told at once when Gelato does not print this length in the order's format (its catalog decides).
    problem = creator.gelato_pages_problem(str(body.get("format") or ""), res["pageCount"]) if provider == "gelato" else None
    if problem:
        raise ApiError(problem)
    return res
