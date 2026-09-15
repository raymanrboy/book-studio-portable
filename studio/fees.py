"""Etsy fees for a Ukrainian seller account — same formulas as Etsy Profit Calculator.

- 6.5% transaction fee on the real (discounted) item price + 20% VAT
- 6.5% transaction fee on shipping + 20% VAT
- Etsy Payments Ukraine processing: 6.0% of the gross + $0.30, + 20% VAT
- $0.20 listing auto-renewal per sold listing + 20% VAT
- US sales tax is collected and withheld by Etsy (subtracted from gross)
"""
from __future__ import annotations

import math


def r2(value: float) -> float:
    """JavaScript Math.round(x * 100) / 100 (half rounds up, like the original tool)."""
    return math.floor(value * 100 + 0.5) / 100


def r1(value: float) -> float:
    return math.floor(value * 10 + 0.5) / 10


def money(obj) -> float:
    """Etsy money object {amount, divisor} -> float rounded to cents."""
    if not isinstance(obj, dict):
        return 0.0
    amount = obj.get("amount") or 0
    divisor = obj.get("divisor") or 100
    return r2(amount / divisor)


def calculate_ukrainian_etsy_fees(receipt: dict) -> dict:
    raw_item_total = money(receipt.get("total_price"))
    discount_amt = money(receipt.get("discount_amt"))

    item_total = raw_item_total
    subtotal_obj = receipt.get("subtotal")
    if isinstance(subtotal_obj, dict) and subtotal_obj.get("amount"):
        item_total = money(subtotal_obj)
    elif discount_amt > 0:
        item_total = max(0.0, r2(raw_item_total - discount_amt))

    shipping_total = money(receipt.get("total_shipping_cost"))
    grandtotal = money(receipt.get("grandtotal"))
    subtotal = r2(item_total + shipping_total)

    sales_tax = 0.0
    tax_obj = receipt.get("total_tax_cost")
    if isinstance(tax_obj, dict) and tax_obj.get("amount"):
        sales_tax = money(tax_obj)
    elif grandtotal > subtotal:
        sales_tax = r2(grandtotal - subtotal)

    gross = grandtotal if grandtotal > 0 else r2(subtotal + sales_tax)

    trans_item_fee = r2(item_total * 0.065)
    vat_trans_item = r2(trans_item_fee * 0.20)
    trans_ship_fee = r2(shipping_total * 0.065)
    vat_trans_ship = r2(trans_ship_fee * 0.20)
    processing_fee = r2(gross * 0.06 + 0.30)
    vat_processing = r2(processing_fee * 0.20)

    transactions = receipt.get("transactions")
    items_sold = len(transactions) if isinstance(transactions, list) and transactions else 1
    listing_renew_fee = r2(items_sold * 0.20)
    vat_listing_renew = r2(listing_renew_fee * 0.20)

    total_etsy_fees = r2(
        trans_item_fee + vat_trans_item + trans_ship_fee + vat_trans_ship
        + processing_fee + vat_processing + listing_renew_fee + vat_listing_renew
    )
    net_payout = max(0.0, r2(gross - sales_tax - total_etsy_fees))

    return {
        "gross": gross,
        "sales_tax": sales_tax,
        "subtotal": subtotal,
        "item_total": item_total,
        "raw_item_total": raw_item_total,
        "discount_amt": discount_amt,
        "shipping_total": shipping_total,
        "trans_item_fee": trans_item_fee,
        "vat_trans_item": vat_trans_item,
        "trans_ship_fee": trans_ship_fee,
        "vat_trans_ship": vat_trans_ship,
        "processing_fee": processing_fee,
        "vat_processing": vat_processing,
        "listing_renew_fee": listing_renew_fee,
        "vat_listing_renew": vat_listing_renew,
        "total_etsy_fees": total_etsy_fees,
        "net_payout": net_payout,
    }
