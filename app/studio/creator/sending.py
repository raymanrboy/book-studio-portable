"""What every send does the same way, whichever the printer: the books of one Etsy order and their receipt, the
address, the send journal, the archive copy and the local records of the print order — none of the steps after the
printer has the order may fail the send."""
from __future__ import annotations

import re
from pathlib import Path

from .. import archive, core, records, sendlog, stages
from ..jobs import JobError
from ..server import ApiError
from .printfolder import _while_sending, validate


REQUIRED_ADDRESS = ("firstName", "lastName", "addressLine1", "city", "postCode", "country")
STATE_REQUIRED = {"US", "CA", "AU"}


def receipt_for(title: str, given=None) -> str | None:
    """The Etsy receipt a send belongs to: the one the page names (the order it came from), else the number
    in front of the title typed by hand. A title that names another receipt than its order is refused —
    the printer's reference, the archive and the local records must not tell two different orders."""
    given = str(given or "").strip()
    if given and not re.fullmatch(r"\d{6,20}", given):
        raise JobError("Некоректний номер замовлення Etsy.")
    typed = archive.receipt_of(title)
    if given and typed and typed != given:
        raise JobError(f"Назва «{title}» починається з номера {typed}, а книга із замовлення {given}. "
                       f"Виправте номер у назві.")
    return given or typed


def books_of(raw) -> list[dict]:
    """The books of one Etsy order as the page sends them — a folder, a name, its receipt and (Gelato) a format
    each. An order with two or three books goes to the printer as one order to one address (owner, 20.09.2026)."""
    books = []
    for item in raw if isinstance(raw, list) else [raw]:
        item = item if isinstance(item, dict) else {}
        title = str(item.get("title") or "").strip()
        if not title:
            raise JobError("Введіть назву книги.")
        books.append({"folder": str(item.get("folder") or "").strip().strip('"'), "title": title,
                      "format": str(item.get("format") or "").strip(),
                      "receipt": receipt_for(title, item.get("receiptId"))})
    if not books:
        raise JobError("Немає жодної книги для відправки.")
    return books


def joint_title(books: list[dict]) -> str:
    """The name of an order of several books: «4100000001 - Emma, Liam». The receipt number stays in front,
    so the print order still finds its Etsy receipt at the next sync."""
    if len(books) == 1:
        return books[0]["title"]
    receipt = books[0].get("receipt")
    names = [archive.child_of(b["title"]) for b in books]
    return (f"{receipt} - {', '.join(names)}" if receipt else " + ".join(b["title"] for b in books))[:100]


def journaled_send(provider: str, kind: str, title: str, folders, send) -> dict:
    """One send, whichever the printer: every attempt written to the send journal (a failed one too), its print
    folders held while it reads them (a page replaced meanwhile waits), and the journal's name in the result and the
    archive. `send(log)` does the printer's own part."""
    with sendlog.attempt(provider, kind, title) as log, _while_sending(folders):
        result = send(log)
        log["result"] = result
    return _journaled(result, log)


def mark_books(books: list[dict]) -> None:
    """Each book's words in the progress and the errors: « · 4100000001 - Emma» when the order has several."""
    for book in books:
        book["mark"] = f" · {book['title']}" if len(books) > 1 else ""


_JOURNALED = {"printify": ("file", "width", "height", "bytes", "sha256", "ok", "error"),
              "gelato": ("file", "width", "height", "bytes", "ok", "error")}
_CHECK_WORDS = {"printify": "Повна перевірка всіх PNG", "gelato": "Наявність і цілісність PNG"}


def checked_files(mode: str, book: dict, job, log: dict, at: float) -> dict:
    """Every PNG of one book read in full and written to the journal — before anything goes to the printer; files
    that fail stop the send."""
    job.progress(f"Перевірка файлів{book['mark']}…", at, _CHECK_WORDS[mode])
    result = validate(mode, book["folder"], None)
    sendlog.step(log, "files", book=book["title"], folder=str(book["folder"]), ok=result["ok"],
                 pageCount=result.get("pageCount"), errors=result["errors"], warnings=result["warnings"],
                 files=[{k: r.get(k) for k in _JOURNALED[mode]} for r in result["files"]])
    if not result["ok"]:
        raise JobError(f"Файли{book['mark']} не пройшли перевірку:\n" + "\n".join(result["errors"]))
    return result


def record_order(log: dict, warnings: list[str], provider: str, books: list[dict], order_id: str | None,
                 reprint) -> None:
    """The new print order recorded here: as a reprint of its receipt (the queue keeps the first print order) — one
    from the archive, or one with new files (`reprint` true, the Order Creator's «Передрук» tick) — or as the order of
    its books' receipts. Never fails a finished send."""
    if reprint:
        _mark_reprint(log, warnings, books[0].get("receipt"), provider, order_id)
    else:
        _remember_sent(log, warnings, books, provider, order_id)


def _journaled(result: dict, log: dict) -> dict:
    """The journal's file name, known only once the attempt is written, goes to the result and the archive."""
    result["sendLog"] = log["file"]
    for eid in {b.get("archiveId") for b in result.get("books") or []} | {result.get("archiveId")}:
        if eid:
            archive.update(eid, sendLog=log["file"])
    return result


def _to_archive(log: dict, job, warnings: list[str], provider: str, files: list[tuple[Path, str]], meta: dict) -> str | None:
    """Keeps what was just sent in the order archive. A failure here never undoes the send: the book is
    in Printify / Gelato, the result only says the archive copy is missing."""
    job.progress("Збереження в архів замовлень…", 97, f"{len(files)} файлів")
    try:
        eid = archive.store(provider, files, meta)
    except Exception as err:
        core.log.exception("Archive: store failed")
        warnings.append(f"Книгу відправлено, але в архів замовлень її не збережено: {err}")
        sendlog.step(log, "archive", error=str(err))
        return None
    sendlog.step(log, "archive", id=eid)
    return eid


def _remember_sent(log: dict, warnings: list[str], books: list, provider: str, order_id: str | None) -> None:
    """Which print order this program made for which receipt. The books of one order can go in two goes,
    or to two printers, and then one receipt really has two print orders; nothing else proves it, because
    a receipt number in the printer's own text also appears on reprints. Never fails a finished send —
    but a record that could not be written is said, like the reprint mark's."""
    receipts = {b.get("receipt") for b in books}
    try:
        written = [r for r in receipts if r and records.remember_print_order(
            r, provider, order_id, books=sum(1 for b in books if b.get("receipt") == r))]
    except Exception as err:
        core.log.exception("Print order not remembered")
        sendlog.step(log, "printOrderRemembered", ok=False, error=str(err))
        warnings.append(f"Замовлення вже створено в {provider.capitalize()}, але програма не записала, до якого "
                        f"замовлення Etsy воно належить: {err}. Не надсилайте ще раз.")
        return
    sendlog.step(log, "printOrderRemembered", ok=bool(written), receipts=sorted(r for r in receipts if r))


def _mark_reprint(log: dict, warnings: list[str], receipt: str | None, provider: str, order_id: str | None) -> None:
    """A reprint is recorded as a replacement of its Etsy order (the queue keeps the first print order).
    A failure here never undoes the send — but it must not be quiet either: the order is already in the
    printer, so the owner has to know that only the local record is missing, and not send it again."""
    try:
        marked = stages.mark_reprint(receipt, provider, order_id)
    except Exception as err:
        core.log.exception("Reprint mark failed")
        sendlog.step(log, "reprintMarked", ok=False, error=str(err))
        warnings.append(f"Замовлення вже створено в {provider.capitalize()}, але програма не записала його "
                        f"як передрук: {err}. Не надсилайте ще раз — перевірте собівартість вручну.")
        return
    sendlog.step(log, "reprintMarked", ok=marked)
    if not marked and receipt:
        # The receipt's first print is cancelled, or it is marked by hand (cancelled, refunded, «без собівартості»): the
        # draft is not a replacement — said, so its cost is looked at in «Прибуток» (the 18.10.2026 review).
        warnings.append("Чернетку не записано як передрук: перший друк цього замовлення скасований або замовлення позначене "
                        "вручну в «Прибутку». Перевірте там його собівартість.")


def _unknown_outcome(err: ApiError) -> bool:
    """The printer may have done it anyway: the connection dropped after sending, or it failed on its own
    side. Then nothing may be sent again until the owner has looked — a second send makes a second one."""
    extra = err.extra or {}
    return bool(extra.get("ambiguous")) or (extra.get("upstream") or 0) >= 500


def validate_address(address: dict) -> list[str]:
    errors = []
    names = {"firstName": "Ім'я", "lastName": "Прізвище", "addressLine1": "Адреса", "city": "Місто",
             "postCode": "Індекс", "country": "Країна"}
    for key in REQUIRED_ADDRESS:
        if not str(address.get(key) or "").strip():
            errors.append(f"Не заповнено поле «{names[key]}».")
    country = str(address.get("country") or "").strip().upper()
    if country in STATE_REQUIRED and not str(address.get("state") or "").strip():
        errors.append(f"Для країни {country} потрібно вказати штат/провінцію.")
    return errors
