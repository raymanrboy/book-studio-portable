"""What cancellations, refunds and replacements do to an order's money.

Etsy rules (Etsy Help, 2026):
- cancelling a paid order refunds the buyer in full and credits the seller for the
  listing, transaction and payment-processing fees of that order -> Etsy net is 0;
- a refund without cancellation credits the transaction and processing fees in
  proportion to the refunded share of what the buyer paid; the $0.20 listing fee is
  not credited;
- a replacement is a reprint the seller pays for: revenue stays, the reprint cost is added.

Printify / Gelato orders that were cancelled, and Gelato drafts that were never ordered,
cost nothing. Orders in the normal state keep the original Profit Calculator numbers.
"""
from __future__ import annotations

from .fees import r1, r2
from .reconcile import _js_round, _num, gelato_cost_to_usd

STATES = ("normal", "canceled", "refund_full", "refund_partial", "replacement")
LABELS = {
    "normal": "Звичайне",
    "canceled": "Скасовано",
    "refund_full": "Повне повернення",
    "refund_partial": "Часткове повернення",
    "replacement": "Заміна",
}


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


def printify_dead(p: dict | None) -> str | None:
    if p and str(p.get("status") or "").lower() in ("canceled", "cancelled"):
        return "canceled"
    return None


def gelato_dead(g: dict | None) -> str | None:
    if not g:
        return None
    if str(g.get("fulfillmentStatus") or "").lower() in ("canceled", "cancelled"):
        return "canceled"
    if str(g.get("orderType") or "").lower() == "draft":
        return "draft"
    return None


def pod_order_info(provider: str, order: dict, eur_rate: float) -> dict:
    """Full (not bundle-split) cost of one provider order, in USD."""
    if provider == "printify":
        cost = _js_round(_num(order.get("total_price")) + _num(order.get("total_shipping"))
                         + _num(order.get("total_tax"))) / 100
        addr = order.get("address_to") or {}
        name = f"{addr.get('first_name') or ''} {addr.get('last_name') or ''}".strip()
        dead = printify_dead(order)
        label = order.get("app_order_id") or str(order.get("id"))[-6:].upper()
        status = order.get("status")
    else:
        cost = gelato_cost_to_usd(_num(order.get("totalInclVat")), order.get("currency"), eur_rate)
        name = f"{order.get('firstName') or ''} {order.get('lastName') or ''}".strip()
        dead = gelato_dead(order)
        label = order.get("orderReferenceId") or str(order.get("id"))[-8:].upper()
        status = order.get("fulfillmentStatus")
    return {"provider": provider, "id": str(order.get("id")), "label": label, "name": name or "Без імені",
            "cost": 0.0 if dead else r2(cost), "fullCost": r2(cost), "status": status, "dead": dead,
            "createdAt": order.get("created_at") or order.get("createdAt")}


def apply(row: dict, receipt: dict, entry: dict | None, orders: dict, eur_rate: float) -> None:
    """Adds state fields to a reconciled row and recomputes net, cost and profit when needed.

    `orders` maps "printify:<id>" / "gelato:<id>" to the provider order.
    """
    entry = entry or {}
    auto = auto_state(receipt)
    manual = entry.get("status") if entry.get("status") in STATES else None
    state = manual or auto
    fb = row.get("fee_breakdown") or {}
    gross = fb.get("gross") or 0.0
    tax = fb.get("sales_tax") or 0.0
    variable = r2((fb.get("trans_item_fee") or 0) + (fb.get("vat_trans_item") or 0)
                  + (fb.get("trans_ship_fee") or 0) + (fb.get("vat_trans_ship") or 0)
                  + (fb.get("processing_fee") or 0) + (fb.get("vat_processing") or 0))
    listing = r2((fb.get("listing_renew_fee") or 0) + (fb.get("vat_listing_renew") or 0))
    base_net = row.get("etsy_net") or 0.0

    # ---- the primary provider order
    provider = row.get("pod_provider")
    primary = None
    if provider == "printify":
        primary = orders.get(f"printify:{row.get('printify_order_id')}")
    elif provider == "gelato":
        primary = orders.get(f"gelato:{row.get('gelato_order_id')}")
    dead = (printify_dead(primary) if provider == "printify" else gelato_dead(primary)) if primary else None
    base_cost = row.get("pod_total_cost") or 0.0
    primary_cost = 0.0 if dead else base_cost

    # ---- replacement reprints
    repl_orders = []
    for ref in entry.get("replacementOrders") or []:
        order = orders.get(f"{ref.get('provider')}:{ref.get('orderId')}")
        if order:
            repl_orders.append(pod_order_info(ref["provider"], order, eur_rate))
    repl_manual = r2(max(0.0, float(entry.get("replacementCost") or 0)))
    repl_cost = r2(sum(o["cost"] for o in repl_orders) + repl_manual) if state == "replacement" else 0.0

    # ---- Etsy money after the refund (the buyer's US sales tax goes back from Etsy's side, not the seller's)
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

    row.update({
        "state": state,
        "state_auto": auto,
        "state_manual": bool(manual),
        "state_label": LABELS[state],
        "state_note": entry.get("note") or "",
        "refunds": receipt.get("refunds") or [],
        "etsy_refund_total": receipt.get("refund_total") or 0.0,
        "refund_amount": refund,
        "revenue_back": revenue_back,
        "fee_credit": fee_credit,
        "listing_kept": listing if state == "refund_full" else 0.0,
        "etsy_net_original": base_net,
        "pod_dead": dead,
        "pod_cost_original": base_cost,
        "replacement_orders": repl_orders if state == "replacement" else [],
        "replacement_manual": repl_manual if state == "replacement" else 0.0,
        "replacement_cost": repl_cost,
    })

    matched = row.get("match_type") not in (None, "unmatched")
    if state == "normal" and not dead:
        row["cost_total"] = base_cost if matched else 0.0
        row["impact"] = 0.0
        return  # original Profit Calculator numbers, untouched

    row["etsy_net"] = net
    if matched and dead and state in ("normal", "replacement") and row.get("match_type") != "manual":
        # Only a cancelled/draft provider order was found by name: the real one still has to be linked.
        row.update({"profit": None, "profit_margin": None, "cost_total": 0.0, "impact": 0.0,
                    "pod_total_cost": 0.0, "printify_total_cost": 0.0, "needs_link": True})
        return
    if not matched and state != "canceled":
        row.update({"cost_total": repl_cost, "impact": -repl_cost if state == "replacement" else 0.0})
        return  # the book's own print cost is still unknown — keep asking for a link
    cost = r2(primary_cost + repl_cost)
    profit = r2(net - cost)
    row.update({
        "pod_total_cost": primary_cost,
        "printify_total_cost": primary_cost if provider == "printify" else row.get("printify_total_cost", 0),
        "cost_total": cost,
        "profit": profit,
        "profit_margin": r1(profit / net * 100) if net > 0 else None,
    })
    if state == "canceled":
        row["impact"] = r2(-primary_cost - repl_cost)
    elif state == "refund_full":
        row["impact"] = r2(-listing - primary_cost)
    elif state == "refund_partial":
        row["impact"] = r2(net - base_net)
    elif state == "replacement":
        row["impact"] = r2(-repl_cost)
    else:
        row["impact"] = 0.0
