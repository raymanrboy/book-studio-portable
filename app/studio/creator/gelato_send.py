"""Gelato: a draft order for the books of an Etsy order — each book one PDF on a temporary link (Cloudflare
Tunnel), its length checked against Gelato's catalog."""
from __future__ import annotations

import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .. import archive, core, gelato, sendlog, tunnel
from ..jobs import JobError
from ..server import ApiError
from .printfolder import gelato_page_options
from .sending import (_to_archive, _unknown_outcome, books_of, checked_files, joint_title, journaled_send, mark_books,
                      record_order, validate_address)
from .photobook import build_photobook_pdf


GELATO_PLACEHOLDER_PHONE = "+1 555 555 0100"  # a made-up number (555-01xx is reserved for fiction)


def gelato_page_counts() -> dict[str, list[int] | None]:
    """For every Gelato format, the page counts its catalog accepts (read only). None where the catalog
    could not be read (no key, no internet): the draft checks again before anything is made."""
    formats = core.settings.section("gelato").get("formats") or {}

    def one(fmt: dict) -> list[int] | None:
        try:
            return gelato.page_counts(fmt["productUid"]) or None
        except ApiError:
            return None

    with ThreadPoolExecutor(max_workers=3) as pool:
        return dict(zip(formats, pool.map(one, formats.values())))


def _pages_problem(label: str, valid: list[int] | None, count: int) -> str | None:
    """The one wording of "Gelato does not print this length" — the order card and the Order Creator both show
    it (the page gets it ready-made from the page-counts route, 22.09.2026 audit)."""
    if not valid or count in valid:
        return None
    text = f"Gelato не друкує {label} на {count} сторінках (можна від {valid[0]})."
    other = next((n for n in gelato_page_options() if n in valid), None)
    return text + (f" Скачайте з Canva {other} сторінок." if other else "")


def gelato_pages_problem(format_key: str, count: int) -> str | None:
    """Why Gelato would refuse a book of `count` pages in this format; None when it is fine or unknown."""
    fmt = (core.settings.section("gelato").get("formats") or {}).get(format_key)
    if not fmt:
        return None
    try:
        valid = gelato.page_counts(fmt["productUid"])
    except ApiError:
        return None
    return _pages_problem(fmt.get("label") or format_key, valid, count)


def _journal_readback(log: dict, order_id: str, sizes: list[int]) -> None:
    """What Gelato itself recorded for the new draft (read only): usually it has already fetched the PDFs.
    The draft exists by now, so nothing here may fail the send."""
    try:
        items = gelato.get_order(order_id).get("items") or []
    except Exception as err:
        sendlog.step(log, "readback", error=str(err))
        return
    for item in items:
        files = [{k: f.get(k) for k in ("type", "mimeType", "sizeBytes")} for f in item.get("files") or []]
        sendlog.step(log, "readback", productUid=item.get("productUid"), pageCount=item.get("pageCount"),
                     status=item.get("fulfillmentStatus"), files=files,
                     fileFetched=any(f.get("sizeBytes") in sizes for f in files),
                     events=item.get("eventLog"), refusal=item.get("refusalReason"))


def create_gelato_draft(books, address: dict, job, reprint_of: str | None = None, again: bool = False) -> dict:
    """A Gelato draft order for the books of one Etsy order — several books travel as items of one draft to
    one address. Every attempt is written to the send journal.
    reprint_of: the archived book this draft reprints (then the folder is that book's archive folder);
    again: a reprint of an order already printed, with new files (the Order Creator's «Передрук» tick, 18.10.2026 —
    a book fixed after the buyer's complaint): recorded as a replacement like one from the archive."""
    books = books_of(books)
    return journaled_send("gelato", "reprint" if reprint_of or again else "draft", joint_title(books),
                          (b["folder"] for b in books),
                          lambda log: _gelato_draft(books, address, job, log, reprint_of, again))


def _gelato_book(book: dict, job, log: dict, cfg: dict, at: float) -> dict:
    """One book of the draft: its files checked, its length taken from the folder and confirmed against
    Gelato's catalog, and the sizes of the book Gelato will print read from the same catalog."""
    fmt = (cfg.get("formats") or {}).get(book["format"])
    if not fmt:
        raise JobError("Оберіть формат книги.")
    result = checked_files("gelato", book, job, log, at)
    pages = [Path(r["path"]) for r in result["files"] if r["position"] != "cover"]
    cover = next(Path(r["path"]) for r in result["files"] if r["position"] == "cover")

    page_count = len(pages)  # 28 or 30, as downloaded from Canva; the catalog below confirms Gelato prints it
    job.progress(f"Розміри книги в Gelato{book['mark']}…", at + 2, f"{fmt.get('label') or book['format']} · {page_count} стор.")
    problem = gelato_pages_problem(book["format"], page_count)
    if problem:
        raise JobError(f"{book['title']}: {problem}" if book["mark"] else problem)
    try:
        geo = gelato.photobook_geometry(fmt["productUid"], page_count)
    except ApiError as err:
        raise JobError(str(err)) from None
    sendlog.step(log, "catalog", book=book["title"], productUid=fmt["productUid"], pageCount=page_count, geometry=geo)
    return {**book, "fmt": fmt, "files": result["files"], "pages": pages, "cover": cover,
            "pageCount": page_count, "geometry": geo}


def _gelato_draft(books: list[dict], address: dict, job, log: dict, reprint_of: str | None = None,
                  again: bool = False) -> dict:
    reprint = bool(reprint_of or again)
    if reprint_of:
        log["reprintOf"] = reprint_of
    if reprint:
        log["reprint"] = True
    cfg = core.settings.section("gelato")
    mark_books(books)
    log["format"] = books[0]["format"]
    log["folder"] = str(books[0]["folder"])
    log["books"] = [{"title": b["title"], "folder": str(b["folder"]), "format": b["format"]} for b in books]
    gelato.api_key()
    address = {k: str(v).strip() for k, v in (address or {}).items() if v is not None and str(v).strip()}
    if address.get("country"):
        address["country"] = address["country"].upper()
    problems = validate_address(address)
    if problems:
        raise JobError("\n".join(problems))
    # Gelato will not let a draft be ordered without a phone; Etsy gives none, and a made-up one is the
    # owner's usual practice (18.09.2026).
    address.setdefault("phone", GELATO_PLACEHOLDER_PHONE)

    ready = [_gelato_book(book, job, log, cfg, 4 + 8 * i / len(books)) for i, book in enumerate(books)]
    title = joint_title(books)
    session = uuid.uuid4().hex[:12]
    session_dir = core.data_path("tmp", "gelato", session)
    session_dir.mkdir(parents=True, exist_ok=True)
    link: tunnel.FileTunnel | None = None
    kept = False                   # the link and the folder went to the registry (Gelato still fetches the PDFs)
    try:
        for i, book in enumerate(ready, 1):
            book["pdfName"] = "book.pdf" if len(ready) == 1 else f"book-{i}.pdf"
            job.progress(f"Збирання книги в один PDF{book['mark']}…", 15 + 15 * (i - 1) / len(ready),
                         f"обкладинка + {book['pageCount']} сторінок, без перестиснення")
            book["pdf"] = build_photobook_pdf(book["cover"], book["pages"], session_dir / book["pdfName"], book["geometry"])
            sendlog.step(log, "pdf", book=book["title"], file=book["pdfName"], **book["pdf"])

        job.progress("Відкриття тимчасового доступу до файлів…", 35, "Cloudflare Tunnel")
        link = tunnel.FileTunnel(session_dir, tuple(b["pdfName"] for b in ready))
        try:
            base = link.start()
        except tunnel.TunnelError as err:
            raise JobError(str(err)) from None
        sendlog.step(log, "link", urls=[f"{base}/{b['pdfName']}" for b in ready], reachable=link.reachable)

        # The order's name in Gelato is the book's title, "4100000001 - Emma", as the owner names his own
        # orders; its receipt number matches the order to its receipt at the next sync.
        payload = {
            "orderType": "draft",
            "orderReferenceId": title[:100],
            "customerReferenceId": f"local-review-{session}",
            "currency": cfg.get("currency") or "USD",
            "items": [{
                "itemReferenceId": f"item-{session}" if len(ready) == 1 else f"item-{session}-{i}",
                "productUid": book["fmt"]["productUid"],
                "pageCount": book["pageCount"],  # inner pages only, as in the owner's own orders; covers are extra
                "quantity": 1,
                # A photo book takes one multi-page PDF of type "default" (cover sheet, blank, pages, blank).
                # ("inside" only exists for folded cards — Gelato then filled every page with the cover.)
                "files": [{"type": "default", "url": f"{base}/{book['pdfName']}"}],
            } for i, book in enumerate(ready, 1)],
            "shippingAddress": address,
            "metadata": [
                {"key": "title", "value": title[:100]},
                {"key": "format", "value": ", ".join(sorted({b["format"] for b in ready}))},
                {"key": "source", "value": "book-studio"},
            ],
        }
        log["request"] = payload
        job.progress("Створення чернетки в Gelato…", 70, "Очікування відповіді")
        keep = int(cfg.get("tunnelKeepAliveSeconds") or 900)
        try:
            created = gelato.create_draft_order(payload)
        except ApiError as err:
            if not _unknown_outcome(err):
                raise JobError(f"Gelato відхилив створення чернетки: {err}") from None
            # Gelato may have made the draft all the same and fetch its PDF in a moment: the link stays up
            # as for a made one, and the owner looks before sending again (22.09.2026 audit).
            log["outcome"] = "unknown"
            tunnel.registry.keep(f"unknown-{session}", link, session_dir, keep)
            link = None
            kept = True
            raise JobError("Зв'язок з Gelato обірвався під час створення чернетки — результат невідомий. НЕ надсилайте "
                           "повторно одразу: спершу перевірте Gelato → Orders → Drafts, чи з'явилась чернетка "
                           f"«{title}». Файли для неї доступні ще {max(1, keep // 60)} хв.") from None
        log["response"] = created
        order_id = created.get("id")
        # The draft exists from here on and Gelato still has to fetch its PDFs: the link goes to the registry
        # first, so nothing that fails after this point can take the files away from it.
        tunnel.registry.keep(order_id or f"unknown-{session}", link, session_dir, keep)
        link = None
        kept = True
        if not order_id:
            log["outcome"] = "unknown"
            raise JobError("Gelato прийняв чернетку, але не повернув її номер. НЕ надсилайте повторно: спершу "
                           f"перевірте Gelato → Orders → Drafts, чи є там «{title}».")
        _journal_readback(log, order_id, [b["pdf"]["pdfBytes"] for b in ready])
        warnings = [f"{b['title']}: {w}" if b["mark"] else w for b in ready for w in b["pdf"]["warnings"]]
        record_order(log, warnings, "gelato", ready, order_id, reprint)
        for book in ready:
            book["archiveId"] = _to_archive(log, job, warnings, "gelato",
                                            [(Path(r["path"]), r["file"]) for r in book["files"]],
                                            {"title": book["title"], "receiptId": book.get("receipt"),
                                             "format": book["format"],
                                             "formatLabel": book["fmt"].get("label"),
                                             "productUid": book["fmt"]["productUid"], "orderId": order_id,
                                             "orderReferenceId": payload["orderReferenceId"], "address": address,
                                             # with new files: the book's first print in the archive, while it is there
                                             "reprintOf": reprint_of or (archive.printed_before(book.get("receipt"), book["title"])
                                                                         if again else None),
                                             "reprint": reprint})
        first = ready[0]
        return {"archiveId": first["archiveId"], "orderId": order_id, "orderReferenceId": payload["orderReferenceId"],
                "fulfillmentStatus": created.get("fulfillmentStatus"), "orderType": created.get("orderType"),
                "format": first["fmt"].get("label"), "keepAliveSeconds": keep, "title": title, "warnings": warnings,
                "pdfPages": first["pdf"]["pdfPages"], "pageCount": first["pageCount"], "reprint": reprint,
                "books": [{"title": b["title"], "archiveId": b["archiveId"], "format": b["fmt"].get("label"),
                           "pageCount": b["pageCount"], "pdfPages": b["pdf"]["pdfPages"]} for b in ready]}
    finally:
        if link is not None:
            link.stop()
        if not kept:                    # a failure before the hand-over must not leave a half-built PDF behind
            shutil.rmtree(session_dir, ignore_errors=True)
