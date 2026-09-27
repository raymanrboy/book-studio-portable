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


def order_stage(row: dict, placed: dict) -> tuple[str, str | None]:
    """Where an Etsy order stands: ("new" | "work" | "sent" | "shipped" | "closed", provider).

    Etsy keeps the seller's own tabs such as "In Production" out of its API, so the signal is the
    print order: once Printify or Gelato has a placed order carrying the receipt number (not a draft, not on
    hold or unpaid, not cancelled — printorders.is_placed()), the book is in work;
    once the printer has shipped it (tracking or a shipped status), it is "sent" — waiting for the
    owner to mark it shipped on Etsy, after which Etsy's own flag makes it "shipped".
    placed is printorders.all_facts().
    """
    if row.get("state") in ("canceled", "refund_full"):
        return "closed", None
    provider, facts = print_order(row, placed)
    if row.get("is_shipped"):
        return "shipped", provider
    if not provider:
        return ("work", None) if row.get("link_blocked") else ("new", None)
    if facts.get("tracking") or str(facts.get("status") or "").lower() in printorders.SENT_STATUSES:
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
            receipts = {}
            for r in snap.get("receipts") or []:
                row = view["full"].get(str(r["receipt_id"]))
                if not row:
                    continue
                stage, provider = order_stage(row, placed)
                shown = print_order(row, placed)[1] if provider else {}
                if stage == "new":  # a draft or unpaid order waiting at the printer: its status shows, the stage stays
                    provider, shown = waiting_order(row, placed)
                receipts[str(r["receipt_id"])] = {"stage": stage, "provider": provider, "order": shown,
                                                  "row": row, "receipt": r}
            _facts.update(key=view["key"], placed=placed, receipts=receipts,
                          loaded=snap.get("loaded") or {}, haveReceipts=bool(snap.get("receipts")))
        return _facts


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
        "printStatus": shown.get("status") or "",  # as Printify / Gelato word it, untranslated (owner's wish)
        "tracking": shown.get("tracking") or [],
        # books of this receipt sent in another go, or to the other printer: the row describes only the first
        # order, so the card says there is more than one
        "alsoSent": [{"provider": f["provider"], "status": f.get("status") or ""} for f in row.get("further_orders") or []],
        "books": sum(int(i.get("quantity") or 1) for i in r.get("items") or []),
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
