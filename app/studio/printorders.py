"""A print order at Printify or Gelato, read one way everywhere: what it costs in dollars, whether it is only a draft
or cancelled, whether it is really placed, whose name it carries, its label and its tracking. Matching
(reconcile), money (outcomes), the order stages and the archive all read an order through `facts()`, so they never
disagree about one (the 2026-09-26 audit found each fact worked out in 3–4 places, each its own way)."""
from __future__ import annotations

import math

from . import core
from .fees import r2

CANCELLED = ("canceled", "cancelled")
# Only a placed and paid print order counts (owner, 18.09.2026): a draft, an order on hold or awaiting payment, or a
# cancelled one neither moves its Etsy order on, nor puts its book in the order archive, nor costs money yet.
# Printify charges when an order goes to production; on-hold and pending ones are not paid.
PRINTIFY_NOT_PLACED = ("on-hold", "pending", "payment-not-received") + CANCELLED
GELATO_NOT_PAID = ("draft", "pending", "refused") + CANCELLED
# A Gelato order that has left the printer (https://dashboard.gelato.com/docs/orders/order_details/).
GELATO_SHIPPED = ("shipped", "in_transit", "delivered", "returned")
# A print order that has left the printer: Printify marks it fulfilled, Gelato shipped / in transit / …
SENT_STATUSES = ("fulfilled", "partially-fulfilled") + GELATO_SHIPPED
CARRIERS = {"usps": "USPS", "ups": "UPS", "dhl": "DHL", "fedex": "FedEx", "dpd": "DPD", "gls": "GLS",
            "royal-mail": "Royal Mail", "canada-post": "Canada Post", "australia-post": "Australia Post"}
# Dollars for one unit of a currency Gelato bills in. Fixed approximations (like the Profit Calculator's euro rate),
# kept in the settings' gelato section; a currency not here is never counted as dollars — its cost is unknown.
RATE_KEYS = {"EUR": "eurUsdRate", "CZK": "czkUsdRate", "GBP": "gbpUsdRate", "PLN": "plnUsdRate"}


def js_round(value: float) -> float:
    """JavaScript Math.round for plain numbers (the Profit Calculator's rounding)."""
    return math.floor(value + 0.5)


def num(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def full_name(first: str | None, last: str | None) -> str:
    return f"{first or ''} {last or ''}".strip()


def carrier_label(code: str) -> str:
    """Printify gives a carrier code ("usps"), Gelato a shipment method name ("UPS Surepost")."""
    code = str(code or "").strip()
    return CARRIERS.get(code.lower()) or (code.upper() if len(code) <= 4 else code)


def rates() -> dict:
    """The settings' dollar rates of the currencies Gelato bills in."""
    cfg = core.settings.section("gelato")
    defaults = core.DEFAULT_SETTINGS["gelato"]
    return {cur: float(cfg.get(key) or defaults[key]) for cur, key in RATE_KEYS.items()}


def to_usd(amount: float, currency: str | None, rates: dict) -> float | None:
    """A Gelato amount in dollars; None for a currency without a rate (never counted as dollars — until 26.09.2026
    five orders in Czech crowns were)."""
    cur = (currency or "USD").upper()
    if not amount:
        return 0.0
    if cur == "USD":
        return amount
    rate = rates.get(cur)
    return r2(amount * rate) if rate else None


def dead(provider: str, order: dict) -> str | None:
    """Why a print order is not the book's order at all: "canceled", or "draft" (a Gelato draft never ordered)."""
    if provider == "printify":
        return "canceled" if str(order.get("status") or "").lower() in CANCELLED else None
    if str(order.get("fulfillmentStatus") or "").lower() in CANCELLED:
        return "canceled"
    return "draft" if str(order.get("orderType") or "").lower() == "draft" else None


def is_placed(provider: str, order: dict) -> bool:
    """Whether a print order is really placed: ordered, paid and not cancelled."""
    if provider == "printify":
        return str(order.get("status") or "").lower() not in PRINTIFY_NOT_PLACED
    return (str(order.get("orderType") or "order").lower() == "order"
            and str(order.get("fulfillmentStatus") or "").lower() not in CANCELLED + ("draft",)
            and str(order.get("financialStatus") or "").lower() not in GELATO_NOT_PAID)


def facts(provider: str, order: dict, rates: dict) -> dict:
    """One print order as every part of the program reads it. `cost` is the whole order in dollars (None when its
    currency has no rate); `prod` and `ship` split a Printify order's cost; `label` is what the owner calls it."""
    if provider == "printify":
        addr = order.get("address_to") or {}
        prod, ship, tax = num(order.get("total_price")), num(order.get("total_shipping")), num(order.get("total_tax"))
        cost = js_round(prod + ship + tax) / 100
        return {"key": f"printify:{order.get('id')}", "provider": provider, "id": str(order.get("id")),
                "name": full_name(addr.get("first_name"), addr.get("last_name")), "created": order.get("created_at"),
                "status": order.get("status"), "shown": shown_status(provider, order),
                "dead": dead(provider, order), "placed": is_placed(provider, order), "cost": cost, "prod": prod / 100, "ship": ship / 100, "raw_cost": cost, "currency": "USD",
                "label": order.get("app_order_id") or str(order.get("id"))[-6:].upper(),
                "tracking": _tracking(order.get("shipments")), "order": order}
    raw = num(order.get("totalInclVat"))
    return {"key": f"gelato:{order.get('id')}", "provider": provider, "id": str(order.get("id")),
            "name": full_name(order.get("firstName"), order.get("lastName")), "created": order.get("createdAt"),
            "status": order.get("fulfillmentStatus"), "shown": shown_status(provider, order), "dead": dead(provider, order), "placed": is_placed(provider, order),
            "payment": str(order.get("financialStatus") or "").lower(),  # "refused" — Gelato could not take the money
            "cost": to_usd(raw, order.get("currency"), rates), "prod": 0.0, "ship": 0.0, "raw_cost": raw,
            "currency": order.get("currency") or "USD",
            "label": order.get("orderReferenceId") or str(order.get("id"))[-8:].upper(),
            "tracking": _tracking(order.get("shipments")), "order": order}


def shown_status(provider: str, order: dict) -> str:
    """The printer's status as the queue and the archive show it. Printify's "fulfilled" only means shipped, so
    it reads as Gelato's words: "in_transit", and "delivered" once the carrier has delivered every parcel
    (owner, 28.09.2026: "Fulfilled" beside Gelato's "Delivered" looked inconsistent). Stages keep `status`."""
    if provider != "printify":
        return order.get("fulfillmentStatus") or ""
    status = order.get("status") or ""
    if status.lower() != "fulfilled":
        return status
    shipments = [s for s in order.get("shipments") or [] if s.get("number")]
    return "delivered" if shipments and all(s.get("delivered_at") for s in shipments) else "in_transit"


def _tracking(shipments) -> list[dict]:
    return [{"carrier": carrier_label(s.get("carrier")), "number": str(s["number"]), "url": s.get("url") or ""}
            for s in shipments or [] if s.get("number")]


def all_facts(snap: dict, rates: dict) -> dict:
    """Every print order of a snapshot by "provider:id"."""
    out = {f["key"]: f for f in (facts("printify", p, rates) for p in snap.get("printify") or [])}
    out.update({f["key"]: f for f in (facts("gelato", g, rates) for g in snap.get("gelato") or [])})
    return out
