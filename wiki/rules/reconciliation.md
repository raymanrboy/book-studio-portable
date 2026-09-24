---
title: Order matching and computing profit
type: rule
updated: 2026-09-22
code:
  - app/studio/reconcile.py
  - app/studio/fees.py
  - app/studio/outcomes.py
---
# Matching and profit

> For every Etsy receipt, a print order (Printify/Gelato) is looked for — both the queue stage and the
> profit depend on this. The rules and formulas were carried over from the Etsy Profit Calculator and
> match it to the cent.

## Matching (`match()`), in order

1. **Manual links** (`links.json`): receipt → order, or "no cost" (`none`).
2. **Printify by receipt number**: in `metadata.shop_order_id`, or in a product's title. Live orders
   take priority over cancelled ones; the first one in Printify's list wins.
3. **Printify by the recipient's name** (`is_name_match()`: identical, the same first and last word, or
   one contains the other from 4 characters on); with several — the closest in time, live ones first.
4. **Gelato**, by the receipt number in `orderReferenceId`, then by name.
5. One print order for several receipts = a **bundled parcel**, the cost is split evenly.

Orders marked as a reprint (a replacement) are excluded from automatic matching.

## One receipt — several print orders (since 2026-09-22)

The steps above find a receipt **one** print order. But a receipt's books can go in **two batches**
(some ready now, the rest later — the card offers this itself), or to **two different printers**. Then
the remaining orders used to fall out of the accounting: a receipt with an $11.95 Printify order and an
$18.00 Gelato order showed a cost of $11.95 and an inflated profit (found by the 2026-09-22 audit).

Now the program **records every send it makes itself** — `data/profit/print-orders.json`
(`profit.remember_print_order()`), and `match(..., sent=…)` adds these orders to the receipt's row
(`further_orders`): their cost is included in `pod_total_cost` and the profit, and the "+N more in
print" chip shows them in the queue.

**Why this record, and not the receipt number inside a print order's text.** The receipt number also
appears in a **reprint's** line-item title (a product is made from the archived book "receipt -
Name"), so counting from text would count reprints as new costs; two of the owner's real receipts
confirmed this. So the main matching hasn't changed, and `sent` is the only reliable source. Not
counted: reprints (they're replacements), cancelled orders, and unconfirmed Gelato drafts.

**Limit:** sends made by something other than this program (or before 2026-09-22) aren't in this record
— for those, everything works as before, one order per receipt. The owner's manual link (`links.json`)
still takes priority.

## Etsy fees (a Ukrainian seller, `calculate_ukrainian_etsy_fees()`)

`Etsy Net = card total − US tax − fees`, where the fees are:
- 6.5% of the item price (after any discount) + 20% VAT;
- 6.5% of shipping + 20% VAT;
- payment processing, 6% of the total + $0.30, + 20% VAT;
- $0.20 per listing renewal, for every item sold, + 20% VAT.

`Profit = Etsy Net − cost`; `Margin = Profit / Etsy Net`. Rounding follows JavaScript's rules
(`r2()`: round half up).

Cost: Printify — `total_price + total_shipping + total_tax` (in cents); Gelato — `totalInclVat`, EUR
converted at the `eurUsdRate`.

## States (`outcomes.apply()`)

| State | Etsy Net | Cost |
|---|---|---|
| normal | as-is | as-is |
| cancelled | 0 (Etsy refunds the fees) | 0, if the print was cancelled; otherwise — a loss |
| full refund | −$0.20·1.2 (the listing fee isn't refunded) | stays |
| partial refund | proportional to the refunded share | stays |
| replacement (a reprint) | as-is | + the cost of the reprint orders and/or a manual amount |

Cancelled print orders and Gelato drafts cost nothing. If matching by name only finds a cancelled
order, the row asks for a manual link (`needs_link`).

## Where in the code

- [app/studio/reconcile.py](../../app/studio/reconcile.py) — `match()`, `_further_orders()`, `is_name_match()`, `normalize_name()`, `cover_label()`, `gelato_cost_to_usd()`, `printify_only_rows()`, `_NameIndex`
- [app/studio/fees.py](../../app/studio/fees.py) — `calculate_ukrainian_etsy_fees()`, `r2()`, `money()`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `apply()`, `auto_state()`, `pod_order_info()`, `STATES`, `LABELS`
- [app/studio/profit.py](../../app/studio/profit.py) — `build_view()`, `reserved_orders()`, `remember_print_order()`, `load_sends()`, `SENDS`
- Tests: [app/tests/test_profit.py](../../app/tests/test_profit.py) (`ProfitParity` against `golden_profit.json`), [app/tests/test_states.py](../../app/tests/test_states.py)

## Related

- [Profit](../features/profit.md) · [Stages](order-stages.md)
