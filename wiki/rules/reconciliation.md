---
title: Matching and profit
type: rule
updated: 2026-11-12
code:
  - app/studio/reconcile.py
  - app/studio/fees.py
  - app/studio/outcomes.py
  - app/studio/printorders.py
  - app/studio/ledger.py
---
# Matching and profit

> For every Etsy receipt the program looks for its print order (Gelato, or an earlier Printify one); both the queue stage and the profit depend on it. Costs and Etsy money are then computed once per row.

## One reading of a print order (`printorders.facts()`)
Matching, money, stages and the archive read every print order through this function: cost in dollars, whether it is **dead** (`dead()`: cancelled, or a Gelato draft never ordered), whether it is **placed** (`is_placed()`: ordered and paid), the recipient's name, a label and tracking.

## Matching (`match()`), one receipt at a time
1. **A manual link** (`links.json`): receipt → order, or "no cost" (`none`). A link to an order the last sync lacks falls back to the rules below.
2. **By receipt number**: Printify (`metadata.shop_order_id`, then a product title), then Gelato (`orderReferenceId`). The **earliest** order naming the receipt wins; a live one before a dead one, a placed one before an unpaid or on-hold one, so an unmarked reprint never takes the first print's place.
3. **By recipient name** (`is_name_match()`): identical, the same first and last word, or one contains the other from 4 characters on; and the order is dated from 1 day before to 30 days after the receipt. With several, the closest in time wins, live first.
4. One print order found by several receipts is a **bundled parcel**; its cost splits evenly.

Both number rules run before either name rule, so a receipt whose own Gelato order carries its number is never taken by a Printify order with a similar name. Orders marked as reprints are excluded (`reserved_orders()`).

## One receipt, several print orders
A receipt's books can go in two batches or to two printers. The program records every send it makes in `data/profit/print-orders.json` (`records.remember_print_order()`); the money step adds them to the row (`further_orders`): their cost is in `pod_total_cost` and the profit, and a "+N more in print" chip shows in the queue. Not counted: reprints (replacements) and orders not placed and paid. Sends made outside the program are not in this record; one order per receipt applies to them, and the owner's manual link still wins.

## Etsy fees (`calculate_ukrainian_etsy_fees()`)
`Etsy Net = card total − US tax − fees`: 6.5% of the item price (after discount) + 20% VAT; 6.5% of shipping + 20% VAT; payment processing 6% of the total + $0.30, + 20% VAT; $0.20 per listing renewal per item sold, + 20% VAT. `Profit = Etsy Net − cost`, `Margin = Profit / Etsy Net`. Rounding is half up (`r2()`).

**Cost**: Printify `total_price + total_shipping + total_tax` (cents); Gelato `totalInclVat` converted by `to_usd()` with the rates in settings `gelato` (`eurUsdRate` 1.085, `czkUsdRate` 0.0468, `gbpUsdRate` 1.325, `plnUsdRate` 0.2608; `RATE_KEYS`). A currency without a rate is never counted as dollars: the row shows `cost_unknown` and no profit.

## The money of a row (`outcomes.apply()`)
| State | Etsy Net | Cost |
|---|---|---|
| normal | as is | as is |
| cancelled | 0 (Etsy refunds the fees) | 0 if the print was cancelled, otherwise a loss |
| full refund | −$0.20 × 1.2 (listing fee not refunded) | stays |
| partial refund | proportional to the refunded share | stays |
| replacement (reprint) | as is | plus the reprint orders' cost and/or a manual amount |

Only a placed and paid print order costs money: cancelled, draft, on-hold and unpaid ones are `pod_dead` (`canceled` / `draft` / `unpaid`). A normal sale whose order is not paid yet shows no profit until it is. If name matching finds only a cancelled order or a draft, the row asks for a manual link (`needs_link`). A cancelled first order does not take the other print orders' cost with it.

## Etsy's ledger: the source of Etsy money
Each sync reads Etsy's payment ledger (`ledger.py`, `data/profit/ledger.json`, from `START`): every credit and debit on the shop balance, in cents, with the balance after it. An entry finds its receipt by reference (receipt, payment, sold item `transaction_id`, a listing renewed by a sale); a VAT line follows its fee (`parent_entry_id`); the rest goes to the receipt posted the same moment (`assign()`). Ads, new listings, Etsy Plus and fees given back stay the shop's.

- `outcomes.apply()` takes a receipt's money from `ledger.view()`: Etsy Net, money before refund, what went back, `etsy_fees`, and lines the formula does not know (`etsy_extra`: Offsite Ads, a state's delivery fee paid by the buyer, the listing fee Etsy keeps on a cancelled sale).
- The formula and state rules above are the **forecast** (`etsy_source: "forecast"`, sum kept in `etsy_net_formula`) until Etsy posts the sale. A cancellation or refund the ledger has no refund lines for yet, or one set by hand, stays the forecast too. A returned VAT line joins its fee's refund (`is_refund()`).
- `ledger.overhead()` gives what Etsy took outside orders, by day. An ads charge pays for the day before; days not charged yet, up to today, get the last charged day's ads as a forecast; ads uncharged for 3 days are off.
- `ledger.gaps()` counts breaks in the chain of running numbers and balances; with one, `refresh()` reads from `START` again.

## Why
- Number rules before name rules and the −1/+30 day window: repeat buyers' old orders were taken by their new receipts.
- Reprints are counted from the send record and not from receipt numbers in text, because a reprint's product title also carries the number.
- A foreign currency is never treated as dollars; wrong totals are worse than none.

## Where in the code
- [app/studio/printorders.py](../../app/studio/printorders.py) — `facts()`, `dead()`, `is_placed()`, `to_usd()`, `rates()`, `RATE_KEYS`
- [app/studio/reconcile.py](../../app/studio/reconcile.py) — `match()`, `is_name_match()`, `item_format()`
- [app/studio/fees.py](../../app/studio/fees.py) — `calculate_ukrainian_etsy_fees()`, `r2()`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `apply()`, `reserved_orders()`, `STATES`
- [app/studio/ledger.py](../../app/studio/ledger.py) — `START`, `refresh()`, `assign()`, `view()`, `overhead()`, `gaps()`
- [app/studio/records.py](../../app/studio/records.py) — `remember_print_order()`, `load_sends()`
- Tests: [app/tests/test_profit.py](../../app/tests/test_profit.py) — `ProfitParity` (against `golden_profit.json`); [app/tests/test_states.py](../../app/tests/test_states.py) — `MatchingOrder`, `MoneyRules`

## Related
- [Profit](../features/profit.md) · [Order stages](order-stages.md) · [Sync](sync-policy.md)
