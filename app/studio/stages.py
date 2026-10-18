"""Where each Etsy order stands — new, in work, sent by the printer, shipped, closed — read from the print order matched
to it: the order queue, the Order Creator's picker and the archive's clock all take it from here. Worked out once per
build of the Profit view (profit.cached_view()), not once per caller. And what a reprint does to its order
(mark_reprint()): kept as a replacement, so the stage does not jump."""
from __future__ import annotations

import threading

from . import core, printorders, profit, records
from .reconcile import parse_time

HOUR_MS = 3_600_000


def _matched_order(row: dict, placed: dict) -> tuple[str | None, dict]:
    """The print order matched to this receipt, unless it is an earlier order of a returning buyer."""
    provider = row.get("pod_provider")
    order_id = row.get("printify_order_id") if provider == "printify" else row.get("gelato_order_id")
    if not provider or not order_id:
        return None, {}
    facts = placed.get(f"{provider}:{order_id}") or {}
    if row.get("match_type") != "manual":
        t_order, t_receipt = parse_time(facts.get("created")), parse_time(row.get("created_at"))
        if t_order is not None and t_receipt is not None and t_order < t_receipt - HOUR_MS:
            return None, {}  # matched by name to an earlier order of a returning buyer
    return provider, facts


def print_order(row: dict, placed: dict) -> tuple[str | None, dict]:
    """The live print order made for this receipt: (provider, facts), or (None, {}) when there is none —
    never ordered, not placed yet (a draft, on hold, awaiting payment), cancelled at the printer, or only
    an earlier order of a returning buyer."""
    provider, facts = _matched_order(row, placed)
    if provider and not facts.get("placed", True):
        return None, {}  # the book still has to be ordered (or ordered again)
    return provider, facts


def waiting_order(row: dict, placed: dict) -> tuple[str | None, dict]:
    """A print order made for this receipt that waits at the printer — a draft, on hold or awaiting payment
    (not cancelled): shown on the order in "new" so a second one is not made by mistake."""
    provider, facts = _matched_order(row, placed)
    if provider and facts and not facts.get("placed", True) \
            and str(facts.get("status") or "").lower() not in printorders.CANCELLED:
        return provider, facts
    return None, {}


def books_in_print(row: dict, placed: dict, refs: list) -> int | None:
    """How many of the receipt's books are in placed print orders, by this program's own send records (each send notes
    its books since 2026-10-14). None — not known: the shown print order was sent before that or made at the printer by
    hand, and is taken to hold every book, as before."""
    provider, shown = print_order(row, placed)
    by_key = {f"{r.get('provider')}:{r.get('orderId')}": r for r in refs or []}
    if not provider or shown.get("key") not in by_key:
        return None
    n = 0
    for key, ref in by_key.items():
        if not (placed.get(key) or {}).get("placed"):
            continue
        if not ref.get("books"):
            return None
        n += int(ref["books"])
    return n


def _pending(refs: list, placed: dict, shown: dict) -> list:
    """The receipt's other sends that wait at the printer (a draft, awaiting payment, a refused payment — not cancelled):
    a second book's refused payment shows on the row too, not only the shown order's (2026-10-14)."""
    out = []
    for ref in refs or []:
        f = placed.get(f"{ref.get('provider')}:{ref.get('orderId')}")
        if not f or f.get("placed") or f.get("key") == shown.get("key") \
                or str(f.get("status") or "").lower() in printorders.CANCELLED:
            continue
        out.append({"provider": f["provider"], "status": f.get("shown") or f.get("status") or "",
                    "payment": f.get("payment") or "", "created": f.get("created")})
    return out


def _shipped_by_printer(facts: dict) -> bool:
    return bool(facts.get("tracking")) or str(facts.get("status") or "").lower() in printorders.SENT_STATUSES


def live_reprint(row: dict, placed: dict) -> dict:
    """The receipt's replacement reprint that is placed at the printer and not shipped by it yet — the newest one —
    or {} when there is none. While it is being made the order is «в роботі» again, whatever Etsy says (owner,
    18.10.2026: a reprint sat among the shipped orders and its own print could not be followed)."""
    if row.get("state") != "replacement":
        return {}
    found = {}
    for ref in row.get("replacement_orders") or []:
        facts = placed.get(f"{ref.get('provider')}:{ref.get('id')}") or {}
        if facts.get("placed") and not _shipped_by_printer(facts) \
                and (facts.get("created") or "") >= (found.get("created") or ""):
            found = facts
    return found


def prints(row: dict, placed: dict) -> list[dict]:
    """Every placed print order of the receipt, oldest first: its own («first»), its other books sent in another go
    («more») and its reprints («reprint») — the order card shows each as its own tab (owner, 18.10.2026)."""
    out, seen = [], set()

    def add(provider, order_id, kind):
        facts = placed.get(f"{provider}:{order_id}") or {}
        if not facts.get("placed") or facts["key"] in seen:
            return
        seen.add(facts["key"])
        out.append({"key": facts["key"], "provider": facts["provider"], "id": facts["id"], "kind": kind,
                    "label": facts.get("label"), "createdAt": facts.get("created"),
                    "printStatus": facts.get("shown") or facts.get("status") or "", "tracking": facts.get("tracking") or [],
                    "payment": facts.get("payment") or "", "cost": facts.get("cost")})

    provider, own = _matched_order(row, placed)
    if provider and own:
        add(provider, own["id"], "first")
    for f in row.get("further_orders") or []:
        add(f.get("provider"), f.get("order_id"), "more")
    for ref in row.get("replacement_orders") or []:
        add(ref.get("provider"), ref.get("id"), "reprint")
    return sorted(out, key=lambda p: (p["kind"] == "reprint", p["createdAt"] or ""))


def order_stage(row: dict, placed: dict) -> tuple[str, str | None]:
    """Where an Etsy order stands: ("new" | "work" | "sent" | "shipped" | "closed", provider).

    Etsy keeps the seller's own tabs such as "In Production" out of its API, so the signal is the
    print order: once Printify or Gelato has a placed order carrying the receipt number (not a draft, not on
    hold or unpaid, not cancelled — printorders.is_placed()), the book is in work;
    once the printer has shipped it (tracking or a shipped status), it is "sent" — waiting for the
    owner to mark it shipped on Etsy, after which Etsy's own flag makes it "shipped". A reprint being made puts it
    back "in work" until its printer ships it (live_reprint()).
    placed is printorders.all_facts().
    """
    if row.get("state") in ("canceled", "refund_full"):
        return "closed", None
    reprint = live_reprint(row, placed)
    if reprint:
        return "work", reprint["provider"]
    provider, facts = print_order(row, placed)
    if row.get("is_shipped"):
        return "shipped", provider
    if not provider:
        return ("work", None) if row.get("link_blocked") else ("new", None)
    if _shipped_by_printer(facts):
        return "sent", provider
    return "work", provider


_facts = {"key": None}
_facts_lock = threading.Lock()


def facts() -> dict:
    """Once per build of the Profit view: every print order ("placed": printorders.all_facts()), and for every
    receipt its stage, the print order it shows (a waiting one while it is "new") and its buyer's name."""
    view = profit.cached_view()
    with _facts_lock:
        if _facts["key"] != view["key"]:
            snap = records.load_snapshot()
            placed = printorders.all_facts(snap, printorders.rates())
            sends = records.load_sends()
            receipts = {}
            for r in snap.get("receipts") or []:
                row = view["full"].get(str(r["receipt_id"]))
                if not row:
                    continue
                stage, provider = order_stage(row, placed)
                reprint = live_reprint(row, placed) if stage == "work" else {}
                shown = reprint or (print_order(row, placed)[1] if provider else {})
                if stage == "new":  # a draft or unpaid order waiting at the printer: its status shows, the stage stays
                    provider, shown = waiting_order(row, placed)
                # Some of the receipt's books are ordered, the others not yet (2026-10-14; open since 22.09): the stage
                # stays what the ordered one makes it — the card keeps what went to print — and the queue lists the
                # receipt under «Нові» too («partial»). Counted by the Order Creator's books (one per Etsy item; a
                # partial refund may have dropped one).
                refs = sends.get(str(r["receipt_id"])) or []
                books = len(r.get("items") or [])
                in_print = books_in_print(row, placed, refs) if books > 1 else None
                partial = (stage in ("work", "sent") and in_print is not None and in_print < books
                           and row.get("state") != "refund_partial")
                receipts[str(r["receipt_id"])] = {"stage": stage, "provider": provider, "order": shown,
                                                  "row": row, "receipt": r, "inPrint": in_print, "partial": partial,
                                                  "pending": _pending(refs, placed, shown), "reprint": bool(reprint)}
            _facts.update(key=view["key"], placed=placed, receipts=receipts,
                          loaded=snap.get("loaded") or {}, haveReceipts=bool(snap.get("receipts")))
        return _facts


def _all_placed(one: dict) -> bool:
    """Every book of the order is in a placed print order (an order of several books: by the send records' count)."""
    several = len(one["receipt"].get("items") or []) > 1
    return (one["stage"] in ("work", "sent", "shipped") and not one.get("partial")
            and not (several and one.get("inPrint") is None))


def _picker(one: dict) -> dict:
    """One Etsy order as the queue and the pickers show it."""
    r, row, shown = one["receipt"], one["row"], one["order"]
    return {
        "receiptId": r["receipt_id"],
        "createdAt": r.get("created_at"),
        "name": r.get("customer_shipping_name"),
        "address": dict(r.get("shipping_address") or {}),
        "stage": one["stage"],
        "provider": one["provider"],
        # as Printify / Gelato word it, untranslated (owner's wish); Printify's "fulfilled" as in transit / delivered
        "printStatus": shown.get("shown") or shown.get("status") or "",
        "tracking": shown.get("tracking") or [],
        # books of this receipt sent in another go, or to the other printer: the row describes only the first
        # order, so the card says there is more than one
        "alsoSent": [{"provider": f["provider"], "status": f.get("status") or ""} for f in row.get("further_orders") or []],
        "books": sum(int(i.get("quantity") or 1) for i in r.get("items") or []),
        "booksInPrint": one.get("inPrint"),
        "partial": bool(one.get("partial")),              # some books ordered, some not: listed under «Нові» too
        "pending": one.get("pending") or [],              # its other sends waiting at the printer
        "reprint": bool(one.get("reprint")),              # the print shown is a reprint being made (live_reprint())
        # The Order Creator's «Передрук» for a send of this order (owner, 18.10.2026): offered once its every book is placed
        # at the printer (an order of several books whose count is unknown is not offered: its second book is no reprint);
        # ticked by itself once the book has left the printer — paid but still being made, a new send may be a correction
        # with the first one cancelled.
        "reprintOffered": _all_placed(one),
        "alreadyPrinted": _all_placed(one) and (one["stage"] in ("sent", "shipped") or bool(one.get("reprint"))),
        "shipBy": r.get("ship_by"),                       # Etsy's date to ship by (epoch seconds), or None
        "payment": shown.get("payment") or "",            # Gelato's financial status: "refused" — the money was not taken
        "orderCreated": shown.get("created"),             # when the print order shown was made (a draft's age)
        "items": [{"title": i.get("title"), "quantity": i.get("quantity"), "sku": i.get("sku") or "",
                   "listingId": str(i.get("listing_id") or ""),
                   "variations": [{"name": v.get("name"), "value": v.get("value")} for v in i.get("variations") or []]}
                  for i in r.get("items") or []],
        "coverLabel": row.get("cover_label") or "Книга",
    }


def picker_orders() -> list:
    """Every Etsy order for the order queue and the Order Creator picker, newest first, each with its stage and, once
    ordered, the printer's status and tracking. Cancelled and fully refunded orders are left out. Fresh dicts each
    time: the queue and the card add to them."""
    return [_picker(one) for one in facts()["receipts"].values() if one["stage"] != "closed"]


def picker_order(receipt_id: str) -> dict | None:
    """One Etsy order as picker_orders() gives it (None — unknown, cancelled or fully refunded)."""
    one = facts()["receipts"].get(str(receipt_id))
    return _picker(one) if one and one["stage"] != "closed" else None


def mark_reprint(receipt_id: str | None, provider: str, order_id: str | None) -> bool:
    """A reprint made from the order archive is recorded as a replacement of its receipt, so matching
    keeps the receipt's first print order (the queue stage does not jump) and the reprint is not
    counted as a new sale. A receipt with another manual state (cancelled, refunded) is left as it is.
    So is one whose print order was cancelled at the printer: the reprint is then its only live print
    order and is matched as usual, so the queue moves the order on instead of keeping it in "new".
    Returns whether the reprint was recorded."""
    if not receipt_id or not order_id:
        return False
    try:
        one = facts()["receipts"].get(str(receipt_id))
        if one and print_order(one["row"], facts()["placed"])[0] is None:
            return False
    except Exception:
        core.log.exception("Reprint: the receipt's print order could not be read; recorded as a replacement")
    return records.add_replacement(str(receipt_id), provider, str(order_id))
