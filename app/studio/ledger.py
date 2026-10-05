"""Etsy's payment-account ledger: every credit and debit on the shop's Etsy balance — a sale, its tax and fees, a refund,
the ads, a listing, a payout (read only; the scope transactions_r the program already has). It gives two checks of the
program's own sums (the owner, 2026-10-05): the balance Etsy will pay out next against what the program expects since the
last payout, and each receipt's real money against the fee formula. Pulled with the orders (sync.py), kept in
data/profit/ledger.json; matched to receipts here, when the Profit view is built."""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime

from . import core, etsy, reconcile

LEDGER = core.data_path("profit", "ledger.json")
START = datetime(2026, 9, 14)  # two weeks before the bookkeeping: the payout that covers 1 October starts before it
WINDOW = 31 * 86400            # Etsy answers at most 31 days per request
OVERLAP = 2 * 86400            # entries are read again two days back: one posted late is not missed
PAYMENT_REFS = ("shop_payment", "processing_fee", "payment_adjustment")  # their reference is a payment, not a receipt
PAYOUT = "DISBURSE"            # DISBURSE2 — the money sent to the owner's Payoneer
NEAR = 3                       # seconds: the entries of one sale are posted together
SHOP_TYPES = ("prolist", "listing", "etsy_plus_credit", "renew_sold_auto_refund")  # the ads, a new listing, Etsy Plus, a listing fee given back (it names no receipt) — the shop's

# What a receipt's entries are, in the owner's words (the order's panel lists them).
LABELS = {
    "PAYMENT_GROSS": "Оплата покупця", "sales_tax": "Податок США", "buyer_fee": "Збір штату (платить покупець)",
    "transaction": "Комісія товару", "shipping_transaction": "Комісія доставки", "PAYMENT_PROCESSING_FEE": "Еквайринг",
    "renew_sold_auto": "Лістинг", "offsite_ads_fee": "Offsite Ads", "REFUND_GROSS": "Повернення покупцю",
    "REFUND_PROCESSING_FEE": "Повернення еквайрингу", "transaction_refund": "Повернення комісії товару",
    "shipping_transaction_refund": "Повернення комісії доставки", "sales_tax_refund": "Повернення податку",
    "renew_sold_auto_refund": "Повернення лістингу", "vat": "ПДВ",
}


def load() -> dict:
    return core.read_json(LEDGER, {}) or {}


def _slim(e: dict) -> dict:
    return {"id": e.get("entry_id"), "seq": e.get("sequence_number") or 0, "at": e.get("create_date") or 0,
            "type": e.get("ledger_type") or "", "rtype": e.get("reference_type") or "", "ref": e.get("reference_id"),
            "amount": e.get("amount") or 0, "balance": e.get("balance"), "parent": e.get("parent_entry_id") or 0}


def refresh() -> int:
    """New ledger entries since the last read (two days back), and which receipt each new payment belongs to. Returns how
    many entries came. Raises EtsyError/ApiError — the sync says so and keeps the old ledger."""
    shop_id, _ = etsy.ensure_shop()
    data = load()
    if str(data.get("shopId") or "") != str(shop_id):
        data = {"shopId": shop_id}
    entries = {str(e["id"]): e for e in data.get("entries") or []}
    payments: dict = dict(data.get("payments") or {})
    now = int(time.time())
    start = max(int(START.timestamp()), int(data.get("readTo") or 0) - OVERLAP)
    came = 0
    while start < now:
        end = min(start + WINDOW, now)
        offset = 0
        while True:
            page = etsy.get(f"/shops/{shop_id}/payment-account/ledger-entries",
                            {"min_created": start, "max_created": end, "limit": 100, "offset": offset},
                            action="Журнал платежів Etsy") or {}
            batch = page.get("results") or []
            for e in batch:
                entries[str(e.get("entry_id"))] = _slim(e)
            came += len(batch)
            offset += len(batch)
            if len(batch) < 100:
                break
            time.sleep(0.12)
        start = end
    # Which receipt a payment (its gross, its fee, a refund of it) belongs to — asked once per payment.
    unknown = [e["id"] for e in entries.values() if e["rtype"] in PAYMENT_REFS and str(e["ref"]) not in payments]
    for i in range(0, len(unknown), 50):
        page = etsy.get(f"/shops/{shop_id}/payment-account/ledger-entries/payments",
                        {"ledger_entry_ids": ",".join(str(x) for x in unknown[i:i + 50])},
                        action="Платежі Etsy") or {}
        for p in page.get("results") or []:
            payments[str(p.get("payment_id"))] = str(p.get("receipt_id"))
            for adj in p.get("payment_adjustments") or []:
                payments[str(adj.get("payment_adjustment_id"))] = str(p.get("receipt_id"))
    data.update(shopId=shop_id, readTo=now, payments=payments,
                entries=sorted(entries.values(), key=lambda e: e["seq"]))
    core.write_json(LEDGER, data)
    return came


def _root(e: dict, by_id: dict) -> dict:
    """The entry a VAT line (or a refund of one) is on, up its parents."""
    for _ in range(5):
        if e["parent"] not in by_id:
            break
        e = by_id[e["parent"]]
    return e


def assign(entries: list, payments: dict, receipts: list) -> dict:
    """entry id -> the receipt it belongs to, for the entries that belong to one. By the reference first (a receipt, a
    payment, a sold item); a VAT line follows the fee it is on; a listing renewed by a sale goes to the latest receipt
    of that listing before it; what is still unknown (a refunded listing fee, a refund) goes to the one receipt whose
    entries were posted the same moment."""
    by_id = {e["id"]: e for e in entries}
    tx: dict = {}
    listings: dict = defaultdict(list)   # listing -> (sold at, receipt) once per item of it sold
    for r in receipts:
        for it in r.get("items") or []:
            if it.get("transaction_id"):
                tx[str(it["transaction_id"])] = r["receipt_id"]
            if it.get("listing_id"):
                listings[str(it["listing_id"])].append((r.get("create_timestamp") or 0, r["receipt_id"]))
    renewed: dict = defaultdict(int)     # (listing, receipt) -> renewals given to it: one per item sold
    own: dict = {}
    for e in entries:
        ref = str(e["ref"])
        if e["rtype"] == "receipt":
            own[e["id"]] = ref
        elif e["rtype"] in PAYMENT_REFS and ref in payments:
            own[e["id"]] = payments[ref]
        elif e["rtype"] == "transaction" and ref in tx:
            own[e["id"]] = tx[ref]
        elif e["type"] == "renew_sold_auto" and ref in listings:
            # The latest sale of that listing before it that has not had all its renewals yet.
            sold = listings[ref]
            before = [r for r in sold if r[0] <= e["at"] + NEAR and e["at"] - r[0] < 3 * 86400
                      and renewed[(ref, r[1])] < sold.count(r)]
            if before:
                rid = max(before)[1]
                renewed[(ref, rid)] += 1
                own[e["id"]] = rid

    def follow_parents() -> None:
        for e in entries:
            if e["id"] not in own and e["parent"] in own:
                own[e["id"]] = own[e["parent"]]

    follow_parents()
    moments: dict = defaultdict(set)
    for eid, rid in own.items():
        moments[by_id[eid]["at"]].add(rid)
    for e in entries:
        base = _root(e, by_id)
        if e["id"] in own or base["type"].startswith(PAYOUT) or base["type"] in SHOP_TYPES                 or base["type"].startswith("vat_") and not base["parent"]:
            continue  # the VAT on an ad or a new listing is the shop's, not a sale's
        near = set().union(*(moments.get(e["at"] + d, set()) for d in range(-NEAR, NEAR + 1)))
        if len(near) == 1:
            own[e["id"]] = next(iter(near))
    follow_parents()
    return own


def view(receipts: list) -> dict:
    """What the Profit view needs from the ledger: each receipt's real money (only receipts whose payment is in the
    ledger), the balance now and the last payouts. {} — no ledger yet."""
    data = load()
    entries = data.get("entries") or []
    if not entries:
        return {}
    own = assign(entries, data.get("payments") or {}, receipts)
    by_id = {e["id"]: e for e in entries}
    per: dict = defaultdict(lambda: {"cents": 0, "lines": defaultdict(int), "paid": False})
    for e in entries:
        rid = own.get(e["id"])
        if not rid:
            continue
        # A VAT line joins the fee it is on, in the panel's list (the fee with its VAT, as the formula shows it).
        kind = e["type"]
        if kind.startswith("vat_on_processing_fees"):
            kind = "REFUND_PROCESSING_FEE" if kind.endswith("refund") else "PAYMENT_PROCESSING_FEE"
        elif kind.startswith("vat_"):
            kind = _root(e, by_id)["type"]
            if kind.startswith("vat_"):
                kind = "vat"
        p = per[rid]
        p["cents"] += e["amount"]
        p["lines"][kind] += e["amount"]
        p["paid"] = p["paid"] or e["type"] == "PAYMENT_GROSS"
    newest = entries[-1]
    payouts = [e for e in entries if e["type"].startswith(PAYOUT)]
    return {
        "receipts": {rid: {"net": p["cents"] / 100,
                           "lines": [{"type": t, "label": LABELS.get(t, t), "amount": c / 100}
                                     for t, c in p["lines"].items() if c]}
                     for rid, p in per.items() if p["paid"]},
        "balance": (newest.get("balance") or 0) / 100,
        "at": newest["at"],
        # A payout does not always empty the balance: Etsy may keep a part back (54.61 after the 28.09.2026 one) — `left`.
        "payouts": [{"at": e["at"], "amount": -e["amount"] / 100, "left": (e.get("balance") or 0) / 100} for e in payouts[-2:]],
        "readTo": data.get("readTo"),
    }


def window_net(rows: dict, start: float, end: float) -> tuple[float, int]:
    """The program's own Etsy Net of the receipts made in (start, end] (epoch seconds) and how many there were — what
    the program expects Etsy to have put on the balance, before the ads and new listings."""
    total, n = 0.0, 0
    for r in rows.values():
        at = (reconcile.parse_time(r.get("created_at")) or 0) / 1000
        if start < at <= end and r.get("etsy_net") is not None:
            total += r["etsy_net"]
            n += 1
    return total, n
