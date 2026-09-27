"""Order archive: the exact files of every book sent to print from Book Studio — to look back at what
really went to the printer and to reprint it quickly.

Each successful send (a Printify book / order, a Gelato draft) copies the Cover.png + 1..N.png it sent
to data/archive/<id>/ together with entry.json: printer, title, receipt, pages, format, ids, the address.
Only a send whose print order is really placed — ordered and paid, not a draft, not on hold, not
cancelled — is shown and counts (owner, 18.09.2026; standing()); one that never goes to print is removed.
Files are removed automatically KEEP_DAYS after the order became "shipped" on Etsy (or was closed) —
the owner's decision (wiki decisions.md, 18.09.2026), a deliberate exception to "never delete the
owner's data". A reprint counts from the moment its printer shipped the reprint itself; a book whose
Etsy order the program cannot see is kept LOST_DAYS from sending. "Keep" holds a book until unmarked.
Only books sent after this feature appeared are here; nothing older is imported.
"""
from __future__ import annotations

import math
import os
import re
import shutil
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

from . import core, drops, images, printorders, records, stages
from .server import ApiError, Request, route

ROOT = core.data_path("archive")
KEEP_DAYS = 14   # after the order became "shipped" (Etsy) or was closed
LOST_DAYS = 30   # a book whose Etsy order the program cannot find (e.g. no receipt number in the title)
DROP_DAYS = 3    # a send that never went to print: its files may still be taken to send the order again
VANISH_DAYS = 2  # a print order still missing from the printer's orders this long after sending: deleted
DAY = 86400
_ID = re.compile(r"\d{8}-\d{6}-[0-9a-f]{6}")
_RECEIPT = re.compile(r"\s*(\d{6,20})\b")  # the Etsy receipt number at the start of "4100000001 - Emma"
_lock = threading.RLock()


def receipt_of(title: str) -> str | None:
    """The receipt number a title typed by hand starts with — only where no order named it (creator.receipt_for)."""
    m = _RECEIPT.match(title or "")
    return m.group(1) if m else None


def child_of(title: str) -> str:
    """"4100000001 - Emma" -> "Emma"; a title without a receipt number in front stays whole."""
    m = re.match(r"\s*\d{6,20}\s*-\s*(.*)$", title or "", re.S)
    return (m.group(1) if m else title or "").strip()


def folder(eid: str) -> Path:
    if not _ID.fullmatch(str(eid or "")):
        raise ApiError("Книгу в архіві не знайдено.", 404)
    return ROOT / eid


def _read(eid: str) -> dict | None:
    entry = core.read_json(folder(eid) / "entry.json", None)
    return entry if isinstance(entry, dict) and entry.get("id") == eid else None


def _write(entry: dict) -> None:
    core.write_json(folder(entry["id"]) / "entry.json", entry, backup=False)


def _ts(iso: str | None) -> float | None:
    try:
        return datetime.fromisoformat(str(iso).replace("Z", "+00:00")).timestamp() if iso else None
    except ValueError:
        return None


def _iso(ts: float) -> str:
    """UTC, the same form as core.now_iso()."""
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ts)) + "Z"


# ---------------------------------------------------------------- storing a send

def store(provider: str, files: list[tuple[Path, str]], meta: dict) -> str:
    """Keeps the files of one successful send; returns the new archive id.

    files: (source path, name to keep it under — "Cover.png", "1.png" …). Files already in the archive
    (a reprint of an archived book) are hard-linked — archive files never change, so it costs no space;
    everything else is copied, never linked: the owner's own folder may be edited later, and the archive
    must keep what was really sent. The folder appears only when complete.
    """
    eid = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    final, tmp = ROOT / eid, ROOT / f".tmp-{eid}"
    tmp.mkdir(parents=True)
    try:
        rows = []
        for src, name in files:
            src, dest = Path(src), tmp / name
            if core.inside(src, ROOT):
                try:
                    os.link(src, dest)
                except OSError:
                    shutil.copyfile(src, dest)
            else:
                shutil.copyfile(src, dest)
            info = images.image_info(dest)
            rows.append({"file": name, "width": info["width"], "height": info["height"], "bytes": dest.stat().st_size})
        entry = {"id": eid, "provider": provider, "title": "", "receiptId": None, "sentAt": core.now_iso(),
                 "pageCount": sum(1 for r in rows if r["file"] != "Cover.png"), "keep": False, "shippedAt": None,
                 "reprintOf": None, **meta, "files": rows}
        entry["receiptId"] = entry.get("receiptId") or receipt_of(entry.get("title") or "")
        core.write_json(tmp / "entry.json", entry, backup=False)
        os.replace(tmp, final)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    core.log.info("Archive: stored %s (%s, %s files)", eid, entry.get("title"), len(rows))
    threading.Thread(target=_warm_previews, args=(final, [(Path(src), name) for src, name in files]),
                     daemon=True).start()
    return eid


def _warm_previews(path: Path, files: list[tuple[Path, str]]) -> None:
    """Previews for the archive page and its viewer, ready before it opens: the ones the order card or the Order
    Creator already made of the sent files are copied (the same pixels), only the rest are made."""
    for src, name in files:
        try:
            images.copy_previews(src, path / name)
            for side in images.VIEW_SIDES:
                images.preview(path / name, side)
        except Exception:
            pass


def update(eid: str, **fields) -> None:
    """Adds facts known only after the send (the journal file name); never fails the send."""
    try:
        with _lock:
            entry = _read(eid)
            if entry:
                entry.update(fields)
                _write(entry)
    except Exception:
        core.log.exception("Archive: could not update %s", eid)


def entries() -> list[dict]:
    out = []
    if ROOT.is_dir():
        for path in ROOT.iterdir():
            if path.is_dir() and _ID.fullmatch(path.name):
                entry = _read(path.name)
                if entry:
                    out.append(entry)
    return sorted(out, key=lambda e: (e.get("sentAt") or "", e["id"]), reverse=True)


def get(eid: str) -> dict:
    entry = _read(eid) if folder(eid).is_dir() else None
    if not entry:
        raise ApiError("Книгу в архіві не знайдено — можливо, її вже прибрано.", 404)
    return entry


# ---------------------------------------------------------------- when files go

def _facts() -> dict:
    """What the last sync knows: stage of every Etsy order and every print order (status, tracking) — stages.facts(),
    worked out once per build of the Profit view."""
    known = stages.facts()
    return {"stages": {rid: one["stage"] for rid, one in known["receipts"].items()}, "placed": known["placed"],
            "names": {rid: one["receipt"].get("customer_shipping_name") or "" for rid, one in known["receipts"].items()},
            "sent": printorders.SENT_STATUSES, "haveReceipts": known["haveReceipts"],
            "loaded": {source: _ts(at) for source, at in known["loaded"].items()}}


_NO_FACTS = {"stages": {}, "placed": {}, "names": {}, "sent": (), "haveReceipts": False, "loaded": {}}


def _loaded(entry: dict, facts: dict) -> float | None:
    """When the list this book's standing is read from was last loaded whole: its printer's orders, or the
    Etsy orders for a book made without a print order. None — never, or before this was noted."""
    source = entry.get("provider") if entry.get("orderId") else "etsy"
    return (facts.get("loaded") or {}).get(source)


def _own_order(entry: dict, facts: dict) -> dict:
    if not entry.get("orderId"):
        return {}
    return facts["placed"].get(f"{entry.get('provider')}:{entry.get('orderId')}") or {}


def _reached_buyer(entry: dict, facts: dict) -> bool:
    """The moment the 14 days start: the Etsy order shipped or closed; for a reprint, its own print order
    shipped by the printer (the Etsy order was shipped long before)."""
    if entry.get("reprintOf"):
        own = _own_order(entry, facts)
        return bool(own.get("tracking")) or str(own.get("status") or "").lower() in facts["sent"]
    return facts["stages"].get(entry.get("receiptId") or "") in ("shipped", "closed")


def _unknown(entry: dict, facts: dict) -> bool:
    """The program cannot follow this book's order, so the timer counts from sending instead: no Etsy
    receipt number or a receipt the synced orders do not have — until it shows up."""
    if entry.get("reprintOf"):
        return not entry.get("orderId")
    rid = entry.get("receiptId")
    return not rid or (facts["haveReceipts"] and rid not in facts["stages"])


def standing(entry: dict, facts: dict | None) -> str:
    """Whether this send really went to print — only such books are in the archive (owner, 18.09.2026):
    "counted" — its print order is placed (ordered and paid, not cancelled: printorders.is_placed());
    "waiting" — a draft, on hold or awaiting payment, or not synced yet;
    "dropped" — cancelled, or missing from its printer's orders loaded whole VANISH_DAYS or more after
    sending (a deleted draft). A printer whose orders failed to load since proves nothing: a stale list
    lacks every order made after it (22.09.2026 audit: such a book lost its files after five days).
    Without order facts nothing can be told, and the book counts as before."""
    if facts is None:
        return "counted"
    if not entry.get("orderId"):
        # A Printify book made without an order: it counts once its Etsy order is in print (ordered by
        # hand); one the program cannot follow, or while Etsy is not synced, is kept as before.
        if _unknown(entry, facts) or not facts["haveReceipts"]:
            return "counted"
        stage = facts["stages"].get(entry.get("receiptId"))
        return "counted" if stage in ("work", "sent", "shipped", "closed") else "waiting"
    if not facts["placed"]:
        return "counted"  # no printer's orders synced yet: nothing to tell by, kept as before
    own = _own_order(entry, facts)
    if own:
        if own.get("placed", True):
            return "counted"
        return "dropped" if str(own.get("status") or "").lower() in printorders.CANCELLED else "waiting"
    sent, loaded = _ts(entry.get("sentAt")), _loaded(entry, facts)
    if sent is not None and loaded is not None and loaded - sent >= VANISH_DAYS * DAY:
        return "dropped"
    return "waiting"


def shown(entry: dict, facts: dict | None) -> bool:
    """In the archive: books that really went to print, and any the owner marked «Не видаляти»."""
    return bool(entry.get("keep")) or standing(entry, facts) == "counted"


def clock(entry: dict, facts: dict | None, now: float | None = None) -> tuple[float | None, str]:
    """(when the files go, why): "keep" (never while marked), "dropped" (DROP_DAYS after the program saw
    that it never went to print), "unplaced" (still a draft or unpaid: LOST_DAYS after sending),
    "shipped" (KEEP_DAYS after the order reached the buyer), "unknown" (LOST_DAYS after sending) or
    "waiting" (the 14 days have not started)."""
    if entry.get("keep"):
        return None, "keep"
    state = standing(entry, facts)
    if state == "dropped":
        noted = _ts(entry.get("droppedAt"))
        return (noted if noted is not None else (time.time() if now is None else now)) + DROP_DAYS * DAY, "dropped"
    if state == "waiting":
        sent = _ts(entry.get("sentAt"))
        return (sent + LOST_DAYS * DAY if sent is not None else None), "unplaced"
    facts = facts or _NO_FACTS
    shipped = _ts(entry.get("shippedAt"))
    if shipped is not None:
        return shipped + KEEP_DAYS * DAY, "shipped"
    if _unknown(entry, facts):
        sent = _ts(entry.get("sentAt"))
        return (sent + LOST_DAYS * DAY if sent is not None else None), "unknown"
    return None, "waiting"


def refresh(now: float | None = None) -> list[str]:
    """Notes orders that reached the buyer and removes books whose time is up; returns the removed ids.
    Runs at start-up and after every sync. Without a readable snapshot nothing is removed."""
    now = time.time() if now is None else now
    removed: list[str] = []
    with _lock:
        try:
            facts = _facts()
        except Exception:
            core.log.exception("Archive: order facts unavailable — nothing removed")
            return removed
        for entry in entries():
            if _note(entry, standing(entry, facts), facts, now):
                _write(entry)
            due, why = clock(entry, facts, now)
            if due is not None and now >= due and why in ("dropped", "unplaced") and (_loaded(entry, facts) or 0) < due:
                continue  # "never went to print" is only believed from orders loaded after the time was up
            if due is not None and now >= due:
                if _remove(entry["id"]):
                    core.log.info("Archive: removed %s (%s) — %s", entry["id"], entry.get("title"), why)
                    removed.append(entry["id"])
                else:
                    core.log.warning("Archive: %s is due but a file is in use — trying again next time", entry["id"])
        if ROOT.is_dir():  # halves of a copy interrupted by a crash or power loss
            for tmp in ROOT.glob(".tmp-*"):
                try:
                    if now - tmp.stat().st_mtime > 3600:
                        shutil.rmtree(tmp, ignore_errors=True)
                except OSError:
                    pass
    return removed


def _note(entry: dict, state: str, facts: dict, now: float) -> bool:
    """Writes down what changed since the last look; returns whether the entry changed. A reprint that never
    went to print leaves no replacement mark on its Etsy order (and gets it back if its order reappears)."""
    changed = False
    if state == "dropped" and not entry.get("droppedAt"):
        entry["droppedAt"] = _iso(now)
        changed = True
        if entry.get("reprintOf"):
            _reprint_mark(entry, False)
    elif state != "dropped" and entry.get("droppedAt"):
        entry["droppedAt"] = None
        changed = True
        if entry.get("reprintOf"):
            _reprint_mark(entry, True)
    if state == "counted" and not entry.get("shippedAt") and _reached_buyer(entry, facts):
        entry["shippedAt"] = _iso(now)  # first seen "shipped" — as the owner sees it in the queue
        changed = True
    return changed


def _reprint_mark(entry: dict, on: bool) -> None:
    try:
        args = (entry.get("receiptId"), entry.get("provider"), entry.get("orderId"))
        stages.mark_reprint(*args) if on else records.unmark_reprint(*args)
    except Exception:
        core.log.exception("Archive: the reprint mark of %s could not be changed", entry.get("id"))


def _remove(eid: str) -> bool:
    """Deletes one archived book: the pictures first, entry.json last — so a picture held open by another
    program leaves the book listed (and due), and the next refresh simply tries again."""
    path = folder(eid)
    for item in path.iterdir():
        if item.name != "entry.json":
            try:
                item.unlink()
            except OSError:
                return False
    try:
        (path / "entry.json").unlink(missing_ok=True)
        path.rmdir()
    except OSError:
        return False
    return True


def refresh_quietly() -> None:
    try:
        refresh()
    except Exception:
        core.log.exception("Archive refresh failed")


def summary(entry: dict, facts: dict | None, now: float | None = None) -> dict:
    """An entry as the archive pages show it: plus its folder, when its files go, the buyer's name and
    the status and tracking of its own print order."""
    now = time.time() if now is None else now
    due, why = clock(entry, facts, now)  # orders unreadable: "keep" and a started countdown still show right
    facts = facts or _NO_FACTS
    own = _own_order(entry, facts)
    return {**entry, "folder": str(folder(entry["id"])),
            "buyer": facts["names"].get(entry.get("receiptId") or "") or "",
            "stage": facts["stages"].get(entry.get("receiptId") or ""),
            "printStatus": own.get("status") or "", "tracking": own.get("tracking") or [],
            "clock": why, "deleteAt": _iso(due) if due else None,
            "daysLeft": max(0, math.ceil((due - now) / DAY)) if due else None, "keepDays": KEEP_DAYS}


def _facts_or_none() -> dict | None:
    try:
        return _facts()
    except Exception:
        core.log.exception("Archive: order facts unavailable")
        return None


# ---------------------------------------------------------------- routes

@route("GET", "/api/archive")
def _list(req: Request):
    facts = _facts_or_none()
    return {"entries": [summary(e, facts) for e in entries() if shown(e, facts)],
            "keepDays": KEEP_DAYS, "lostDays": LOST_DAYS}


def _shown_one(eid: str, facts: dict | None) -> dict:
    entry = get(eid)
    if not shown(entry, facts):
        raise ApiError("Цієї книги немає в архіві: її замовлення в друкарні не оформлене або скасоване.", 404)
    return entry


@route("GET", r"/api/archive/(\d{8}-\d{6}-[0-9a-f]{6})")
def _one(req: Request):
    facts = _facts_or_none()
    return summary(_shown_one(req.groups[0], facts), facts)


@route("POST", r"/api/archive/(\d{8}-\d{6}-[0-9a-f]{6})/keep")
def _keep(req: Request):
    """"Не видаляти": the book stays until unmarked; unmarked, the usual 14 days apply again."""
    keep = bool((req.json or {}).get("keep"))
    facts = _facts_or_none()
    with _lock:
        entry = _shown_one(req.groups[0], facts)
        entry["keep"] = keep
        _write(entry)
    return summary(entry, facts)


def reprintable(eid: str) -> dict:
    """The archived book a reprint is made from: only one that really went to print. A send that never did
    is not reprinted — its Etsy order is simply sent again from its card (card_facts())."""
    entry = get(eid)
    if standing(entry, _facts_or_none()) != "counted":
        raise ApiError("Ця відправка не стала замовленням у друкарні (чернетка, неоплачене чи скасоване "
                       "замовлення) — це не передрук. Відправте замовлення як звичайне з його картки: там "
                       "можна взяти файли з минулої відправки.", 409)
    return entry


def card_facts(receipt_id: str) -> dict:
    """What an order's card needs from the archive, from one read of it:
    "earlierSends" — sends of this Etsy order that never went to print (a draft left unconfirmed, a cancelled
    order, a deleted draft) whose files are still here, newest first: the card offers them to send it again;
    "atPrinter" — a send its printer still has (a book, a draft or an order not cancelled or deleted there): read
    from the archive, so it outlives a restart, unlike the page's own memory of a send."""
    facts = _facts_or_none()
    own = [e for e in entries() if e.get("receiptId") == str(receipt_id)]
    return {"earlierSends": [{k: e.get(k) for k in ("id", "provider", "sentAt", "pageCount", "format", "formatLabel")}
                             for e in own if facts is not None and standing(e, facts) != "counted"],
            "atPrinter": any(standing(e, facts) != "dropped" for e in own)}


_BOOK_FILE = re.compile(r"Cover\.png|\d{1,3}\.png")


@route("POST", r"/api/archive/(\d{8}-\d{6}-[0-9a-f]{6})/reuse")
def _reuse(req: Request):
    """The files of an earlier send as a fresh working copy for the order card (hard links: no extra space,
    and the copy stays whole when the archived book goes)."""
    entry = get(req.groups[0])
    source, target = folder(entry["id"]), drops.DROPS / uuid.uuid4().hex
    target.mkdir(parents=True)
    for row in entry.get("files") or []:
        name = str(row.get("file") or "")
        if not _BOOK_FILE.fullmatch(name):
            continue
        try:
            os.link(source / name, target / name)
        except OSError:
            shutil.copyfile(source / name, target / name)
    return {"path": str(target)}
