---
title: Order matching and computing profit
type: rule
updated: 2026-10-05
code:
  - app/studio/reconcile.py
  - app/studio/fees.py
  - app/studio/outcomes.py
  - app/studio/printorders.py
  - app/studio/ledger.py
---
# Matching and profit

> For every Etsy receipt, a print order (Printify/Gelato) is looked for — both the queue stage and the
> profit depend on this. The rules and formulas were carried over from the Etsy Profit Calculator and
> match it to the cent, apart from the fixes of 2026-09-26 below (the rule order, the currencies, only paid
> orders counted).

## One reading of a print order (`printorders.facts()`, since 2026-09-26)

Matching, money, the queue's stages and the archive read every Printify/Gelato order through one function: its
cost in dollars, whether it is **dead** (`dead()`: cancelled, or a Gelato draft never ordered), whether it is
**placed** (`is_placed()`: ordered and paid — not on hold, not awaiting payment, not cancelled), the buyer's name,
its label and tracking. Until then each of these was worked out in 3–4 places, each its own way (the code study
of 2026-09-26).

## Matching (`match()`), one receipt at a time

1. **A manual link** (`links.json`): receipt → order, or "no cost" (`none`). A link to an order the last sync
   doesn't have falls back to the rules below.
2. **By receipt number** — first Printify (`metadata.shop_order_id`, or a product's title), then Gelato
   (`orderReferenceId`). The first order that names the receipt wins, a live one before a dead one.
3. **By the recipient's name** — first Printify, then Gelato (`is_name_match()`: identical, the same first and
   last word, or one contains the other from 4 characters on); with several — the closest in time, live ones first.
4. One print order found by several receipts = a **bundled parcel**, the cost is split evenly.

**Both number rules come before either name rule (since 2026-09-26).** Before, Printify-by-name ran before
Gelato-by-number: a receipt whose own Gelato order carried its number was taken by any Printify order with a
similar name ("Ann Lee" is inside "Joann Leeds") — and showed that order's status and tracking; with most orders
going to Gelato this mattered more. Matching finds the same orders wherever the number and the name agree.

Orders marked as a reprint (a replacement) are excluded from automatic matching (`reserved_orders()`).

## One receipt — several print orders (since 2026-09-22)

The steps above find a receipt **one** print order. But a receipt's books can go in **two batches**
(some ready now, the rest later — the card offers this itself), or to **two different printers**. Then
the remaining orders used to fall out of the accounting: a receipt with an $11.95 Printify order and an
$18.00 Gelato order showed a cost of $11.95 and an inflated profit (found by the 2026-09-22 audit).

Now the program **records every send it makes itself** — `data/profit/print-orders.json`
(`records.remember_print_order()`); the money step adds these orders to the receipt's row (`further_orders`):
their cost is included in `pod_total_cost` and the profit, and the "+N more in print" chip shows them in the queue.

**Why this record, and not the receipt number inside a print order's text.** The receipt number also
appears in a **reprint's** line-item title (a product is made from the archived book "receipt -
Name"), so counting from text would count reprints as new costs; two of the owner's real receipts
confirmed this. So the main matching hasn't changed, and the record is the only reliable source. Not
counted: reprints (they're replacements), and orders that aren't placed and paid.

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

Cost: Printify — `total_price + total_shipping + total_tax` (in cents); Gelato — `totalInclVat` in dollars
(`to_usd()`): euros at `eurUsdRate` (1.085, the Profit Calculator's), Czech crowns, pounds and zlotys at
`czkUsdRate`, `gbpUsdRate`, `plnUsdRate` (the ECB's cross rates of 25.09.2026), all in the settings' `gelato`
section. **A currency without a rate is never counted as dollars** (until 2026-09-26 anything but euros was — five
orders in crowns in the Gelato account, June 2026, and two in pounds among the Profit Calculator's): the row shows
`cost_unknown` and no profit. The owner's own Gelato orders are billed in dollars (28 of his 30 by 2026-09-27; two
of 5 August in euros); the euros and crowns in the account are mostly other people's orders — they are converted
only in case one gets linked to a sale.

## The money of a row (`outcomes.apply()`, worked out once)

| State | Etsy Net | Cost |
|---|---|---|
| normal | as-is | as-is |
| cancelled | 0 (Etsy refunds the fees) | 0, if the print was cancelled; otherwise — a loss |
| full refund | −$0.20·1.2 (the listing fee isn't refunded) | stays |
| partial refund | proportional to the refunded share | stays |
| replacement (a reprint) | as-is | + the cost of the reprint orders and/or a manual amount |

**Only a placed and paid print order costs money** (the 2026-09-18 decision, counted in the money since
2026-09-26): a cancelled order, a Gelato draft, an order on hold or awaiting payment cost nothing (`pod_dead`:
`canceled` / `draft` / `unpaid`). A normal sale whose order isn't paid yet shows no profit until it is (it's the
right order — no link is asked for). If matching by name only finds a cancelled order or a draft, the row asks
for a manual link (`needs_link`). A cancelled first order no longer takes the cost of the sale's other print
orders with it (until 2026-09-26 it did).

## The check against Etsy's ledger

Since 2026-10-05 the sync reads Etsy's payment ledger (`ledger.py`, `data/profit/ledger.json`): every credit and debit on the
shop's Etsy balance, in cents, each with the balance after it. An entry finds its receipt by its reference — a receipt, a payment
(asked once: `ledger-entries/payments` gives the receipt), a sold item (`transaction_id`, kept on each item since then), a listing
renewed by a sale (the latest sale of that listing still owed one); a VAT line follows the fee it is on (`parent_entry_id`); what is
left goes to the one receipt posted the same moment. Ads, new listings, Etsy Plus and listing fees given back stay the shop's.

**What it showed on the owner's real data (5 October 2026, 70 receipts of the last 31 days):** the formula is right — 58 receipts
to the cent, 6 more within 1–4 cents (rounding). What it does not count: **Etsy Offsite Ads** (3 sales in September, −$4.16…−$6.32
each), a **state's delivery fee** paid by the buyer (Colorado, −$0.31), and on a cancelled sale the **$0.24 listing fee** Etsy
keeps. The payout of 5 October ($606.68) against the program: $54.61 the payout of 28 September had left on the balance + the
program's sum for the 21 sales between, less the ads a day = $606.63 — 5 cents off. A payout does not always empty the balance
(Etsy kept $54.61 and $35.12 back twice), so the check starts from what the last one left.

## Where in the code

- [app/studio/printorders.py](../../app/studio/printorders.py) — `facts()`, `all_facts()`, `dead()`, `is_placed()`, `to_usd()`, `rates()`, `RATE_KEYS`, `js_round()`, `CANCELLED`, `PRINTIFY_NOT_PLACED`, `GELATO_NOT_PAID`
- [app/studio/reconcile.py](../../app/studio/reconcile.py) — `match()`, `_find()`, `_Printer`, `_numbers_named()`, `is_name_match()`, `normalize_name()`, `item_format()`, `cover_label()`, `printify_only_rows()`, `_NameIndex`
- [app/studio/fees.py](../../app/studio/fees.py) — `calculate_ukrainian_etsy_fees()`, `r2()`, `money()`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `rows()`, `apply()`, `auto_state()`, `unpaid()`, `order_info()`, `reserved_orders()`, `STATES`
- [app/studio/ledger.py](../../app/studio/ledger.py) — `refresh()`, `assign()`, `view()`, `window_net()`
- [app/studio/records.py](../../app/studio/records.py) — `remember_print_order()`, `load_sends()`, `SENDS`
- Tests: [app/tests/test_profit.py](../../app/tests/test_profit.py) (`ProfitParity` against `golden_profit.json`), [app/tests/test_states.py](../../app/tests/test_states.py) (`MatchingOrder`, `MoneyRules`)

## Related

- [Profit](../features/profit.md) · [Stages](order-stages.md)
