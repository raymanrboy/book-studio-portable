"""What an Etsy order finally earns: its Etsy money after a cancellation or a refund, and what its print orders cost —
the one matching found, the others this program sent for it, and replacement reprints. The one place the money of a
row is worked out (until 2026-09-26 three functions rewrote the same fields in turn).

Etsy rules (Etsy Help, 2026):
- cancelling a paid order refunds the buyer in full and credits the seller for the
  listing, transaction and payment-processing fees of that order -> Etsy net is 0;
- a refund without cancellation credits the transaction and processing fees in
  proportion to the refunded share of what the buyer paid; the $0.20 listing fee is
  not credited;
- a replacement is a reprint the seller pays for: revenue stays, the reprint cost is added.

Only a placed and paid print order costs money (owner, 18.09.2026; counted in the money since 26.09.2026): a
cancelled one, a Gelato draft never ordered, an order on hold or awaiting payment cost nothing (yet). A normal order
whose print order is placed keeps the Profit Calculator's numbers.
"""
from __future__ import annotations

from . import reconcile
from .fees import r1, r2
from .printorders import all_facts

STATES = ("normal", "canceled", "refund_full", "refund_partial", "replacement")


def auto_state(receipt: dict) -> str:
    """State Etsy itself reports for the receipt."""
    status = str(receipt.get("status") or "").lower()
    refunded = receipt.get("refund_total") or 0
    gross = (receipt.get("fee_breakdown") or {}).get("gross") or receipt.get("etsy_gross") or 0
    if status == "canceled":
        return "canceled"
    if status == "fully refunded" or (refunded and gross and refunded >= gross - 0.005):
        return "refund_full"
    if status == "partially refunded" or refunded > 0:
        return "refund_partial"
    return "normal"


def reserved_orders(states: dict) -> set[str]:
    """Print orders marked as replacement reprints: kept out of automatic matching and out of a sale's own cost."""
    return {f"{ref.get('provider')}:{ref.get('orderId')}"
            for entry in states.values() if entry.get("status") == "replacement"
            for ref in entry.get("replacementOrders") or []}


def unpaid(f: dict) -> str | None:
    """Why a print order costs nothing: "canceled", "draft" (a Gelato draft never ordered), "unpaid" (on hold or
    awaiting payment) — None when it is placed and paid."""
    return f["dead"] or (None if f["placed"] else "unpaid")


def order_info(f: dict) -> dict:
    """A print order as the pickers and the replacement list show it: `fullCost` is the whole order in dollars (0 for
    a currency without a rate), `cost` what it costs this sale now."""
    full = r2(f["cost"] or 0)
    return {"provider": f["provider"], "id": f["id"], "label": f["label"], "name": f["name"] or "Без імені",
            "cost": 0.0 if unpaid(f) else full, "fullCost": full, "status": f["status"], "dead": unpaid(f),
            "createdAt": f["created"]}


def rows(receipts: list, printify: list, gelato: list, links: dict, states: dict, sent: dict, rates: dict) -> list:
    """Every receipt's row: matched (reconcile.match()), then its money (apply())."""
    reserved = reserved_orders(states)
    out = reconcile.match(receipts, printify, gelato, links, rates, reserved=reserved, sent=sent)
    orders = all_facts({"printify": printify, "gelato": gelato}, rates)
    shared: dict[str, int] = {}  # one print order this program sent for two receipts is split between them
    for refs in (sent or {}).values():
        for ref in refs or []:
            key = f"{ref.get('provider')}:{ref.get('orderId')}"
            shared[key] = shared.get(key, 0) + 1
    by_id = {str(r["receipt_id"]): r for r in receipts}
    for row in out:
        apply(row, by_id[row["id"]], states.get(row["id"]), orders, shared, reserved)
    return out


def apply(row: dict, receipt: dict, entry: dict | None, orders: dict, shared: dict, reserved) -> None:
    """The row's state and final money. `orders` — printorders.all_facts(); `shared` — how many receipts' own send
    records name each order."""
    entry = entry or {}
    auto = auto_state(receipt)
    manual = entry.get("status") if entry.get("status") in STATES else None
    state = manual or auto

    # ---- Etsy money after the refund (the buyer's US sales tax goes back from Etsy's side, not the seller's)
    fb = row.get("fee_breakdown") or {}
    gross = fb.get("gross") or 0.0
    tax = fb.get("sales_tax") or 0.0
    variable = r2((fb.get("trans_item_fee") or 0) + (fb.get("vat_trans_item") or 0)
                  + (fb.get("trans_ship_fee") or 0) + (fb.get("vat_trans_ship") or 0)
                  + (fb.get("processing_fee") or 0) + (fb.get("vat_processing") or 0))
    listing = r2((fb.get("listing_renew_fee") or 0) + (fb.get("vat_listing_renew") or 0))
    base_net = row.get("etsy_net") or 0.0
    refund = fee_credit = revenue_back = 0.0
    net = base_net
    if state == "canceled":
        refund, revenue_back, fee_credit, net = gross, r2(gross - tax), r2(variable + listing), 0.0
    elif state == "refund_full":
        refund, revenue_back, fee_credit, net = gross, r2(gross - tax), variable, r2(-listing)
    elif state == "refund_partial":
        amount = entry.get("refundAmount")
        refund = r2(min(gross, max(0.0, float(amount if amount not in (None, "") else receipt.get("refund_total") or 0))))
        share = refund / gross if gross else 0.0
        fee_credit = r2(variable * share)
        revenue_back = r2((gross - tax) * share)
        net = r2(base_net - revenue_back + fee_credit)

    # ---- the print order matching found (its bundle share), unless it costs nothing
    provider = row.get("pod_provider")
    key = f"{provider}:{row.get('printify_order_id') if provider == 'printify' else row.get('gelato_order_id')}"
    found = orders.get(key) if provider else None
    why_free = unpaid(found) if found else None
    matched_cost = row.get("pod_total_cost") or 0.0
    primary = 0.0 if why_free else matched_cost

    # ---- the other print orders this program sent for this receipt: books sent in two goes, or to both printers
    further = []
    for p, oid in row.pop("sent_orders", None) or []:
        k = f"{p}:{oid}"
        o = orders.get(k)
        if k == key or k in reserved or not o or unpaid(o) or o["cost"] is None:
            continue
        further.append({"provider": p, "order_id": oid, "status": o["status"], "app_order_id": o["label"],
                        "cost": r2(o["cost"] / max(1, shared.get(k, 1)))})
    further_cost = r2(sum(f["cost"] for f in further))

    # ---- replacement reprints
    repl_orders = [order_info(orders[k]) for k in (f"{ref.get('provider')}:{ref.get('orderId')}"
                                                   for ref in entry.get("replacementOrders") or []) if k in orders]
    repl_manual = r2(max(0.0, float(entry.get("replacementCost") or 0)))
    repl_cost = r2(sum(o["cost"] for o in repl_orders) + repl_manual) if state == "replacement" else 0.0

    row.update({
        "state": state,
        "state_auto": auto,
        "state_manual": bool(manual),
        "state_note": entry.get("note") or "",
        "refunds": receipt.get("refunds") or [],
        "etsy_refund_total": receipt.get("refund_total") or 0.0,
        "refund_amount": refund,
        "revenue_back": revenue_back,
        "fee_credit": fee_credit,
        "etsy_net_original": base_net,
        "etsy_net": net,
        "pod_dead": why_free,
        "pod_cost_original": matched_cost,
        "further_orders": further,
        "replacement_orders": repl_orders if state == "replacement" else [],
        "replacement_manual": repl_manual if state == "replacement" else 0.0,
        "replacement_cost": repl_cost,
    })

    matched = row.get("match_type") not in (None, "unmatched")
    unknown = matched and bool(row.get("cost_unknown"))
    pod = r2(primary + further_cost)
    if matched and why_free in ("canceled", "draft") and state in ("normal", "replacement") \
            and row.get("match_type") != "manual":
        # Only a cancelled order or a draft was found by name: the real one still has to be linked.
        row.update({"profit": None, "profit_margin": None, "cost_total": 0.0, "impact": 0.0,
                    "pod_total_cost": 0.0, "printify_total_cost": 0.0, "needs_link": True})
    elif (why_free == "unpaid" or unknown) and state == "normal":
        # The book's print order waits at the printer (on hold, awaiting payment), or is billed in a currency
        # without a rate: what the sale earns is not known yet.
        row.update({"profit": None, "profit_margin": None, "cost_total": 0.0, "impact": 0.0,
                    "pod_total_cost": 0.0, "printify_total_cost": 0.0})
    elif state == "normal":
        # The Profit Calculator's numbers — with the other print orders of the sale added.
        profit = r2(net - pod) if matched or further else None
        row.update({"pod_total_cost": pod, "printify_total_cost": pod, "cost_total": pod, "impact": 0.0,
                    "profit": profit,
                    "profit_margin": (r1(profit / net * 100) if net > 0 else 0) if profit is not None else None})
    elif not matched and state != "canceled":
        row.update({"cost_total": r2(further_cost + repl_cost), "impact": -repl_cost if state == "replacement" else 0.0})
    else:
        cost = r2(pod + repl_cost)
        profit = r2(net - cost)
        impact = {"canceled": -cost, "refund_full": r2(-listing - pod), "refund_partial": r2(net - base_net),
                  "replacement": -repl_cost}.get(state, 0.0)
        row.update({"pod_total_cost": pod, "printify_total_cost": pod,
                    "cost_total": cost, "profit": profit, "impact": r2(impact),
                    "profit_margin": r1(profit / net * 100) if net > 0 else None})
