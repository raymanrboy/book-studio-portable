---
title: Order matching and computing profit
type: rule
updated: 2026-10-28
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
> match it to the cent, apart from the rule order, the currencies, and only paid orders being counted.

## One reading of a print order (`printorders.facts()`)

Matching, money, the queue's stages and the archive read every Printify/Gelato order through one function: its
cost in dollars, whether it is **dead** (`dead()`: cancelled, or a Gelato draft never ordered), whether it is
**placed** (`is_placed()`: ordered and paid — not on hold, not awaiting payment, not cancelled), the buyer's name,
its label and tracking.

## Matching (`match()`), one receipt at a time

1. **A manual link** (`links.json`): receipt → order, or "no cost" (`none`). A link to an order the last sync
   doesn't have falls back to the rules below.
2. **By receipt number** — first Printify (`metadata.shop_order_id`, or a product's title), then Gelato
   (`orderReferenceId`). The **earliest** order that names the receipt wins, a live one before a dead one and a placed one before an unpaid or on-hold one (so an unmarked reprint never takes the
   first print's place).
3. **By the recipient's name** — first Printify, then Gelato (`is_name_match()`: identical, the same first and
   last word, or one contains the other from 4 characters on) **and made from 1 day before to 30 days after the receipt**
   (so a repeat buyer's old order is not taken by her new receipt); with several — the closest in
   time, live ones first.
4. One print order found by several receipts = a **bundled parcel**, the cost is split evenly.

**Both number rules come before either name rule**, so a receipt whose own Gelato order carries its number is never
taken by a Printify order with a similar name ("Ann Lee" is inside "Joann Leeds").

Orders marked as a reprint (a replacement) are excluded from automatic matching (`reserved_orders()`).

## One receipt — several print orders

The steps above find a receipt **one** print order. But a receipt's books can go in **two batches**
(some ready now, the rest later — the card offers this itself), or to **two different printers**. The remaining
orders must not fall out of the accounting, so the program **records every send it makes itself** — `data/profit/print-orders.json`
(`records.remember_print_order()`); the money step adds these orders to the receipt's row (`further_orders`):
their cost is included in `pod_total_cost` and the profit, and the "+N more in print" chip shows them in the queue.

**Why this record, and not the receipt number inside a print order's text.** The receipt number also
appears in a **reprint's** line-item title (a product is made from the archived book "receipt -
Name"), so counting from text would count reprints as new costs. The record is the only reliable source. Not
counted: reprints (they're replacements), and orders that aren't placed and paid.

**Limit:** sends made by something other than this program aren't in this record
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
`czkUsdRate`, `gbpUsdRate`, `plnUsdRate` (the ECB's cross rates), all in the settings' `gelato`
section. **A currency without a rate is never counted as dollars**: the row shows
`cost_unknown` and no profit. The owner's own Gelato orders are billed in dollars; the euros and crowns in the
account are mostly other people's orders — they are converted only in case one gets linked to a sale.

## The money of a row (`outcomes.apply()`, worked out once)

| State | Etsy Net | Cost |
|---|---|---|
| normal | as-is | as-is |
| cancelled | 0 (Etsy refunds the fees) | 0, if the print was cancelled; otherwise — a loss |
| full refund | −$0.20·1.2 (the listing fee isn't refunded) | stays |
| partial refund | proportional to the refunded share | stays |
| replacement (a reprint) | as-is | + the cost of the reprint orders and/or a manual amount |

**Only a placed and paid print order costs money** (the owner's decision): a cancelled order, a Gelato draft, an order on hold or awaiting payment cost nothing (`pod_dead`:
`canceled` / `draft` / `unpaid`). A normal sale whose order isn't paid yet shows no profit until it is (it's the
right order — no link is asked for). If matching by name only finds a cancelled order or a draft, the row asks
for a manual link (`needs_link`). A cancelled first order does not take the cost of the sale's other print
orders with it.

## Etsy's ledger — the source of the Etsy money

The sync reads Etsy's payment ledger (`ledger.py`, `data/profit/ledger.json`): every credit and debit on the
shop's Etsy balance, in cents, each with the balance after it. An entry finds its receipt by its reference — a receipt, a payment
(asked once: `ledger-entries/payments` gives the receipt), a sold item (`transaction_id`, kept on each item since then), a listing
renewed by a sale (the latest sale of that listing still owed one); a VAT line follows the fee it is on (`parent_entry_id`); what is
left goes to the one receipt posted the same moment. Ads, new listings, Etsy Plus and listing fees given back stay the shop's.

What the ledger does not carry into the receipt's fees: **Etsy Offsite Ads**, a **state's delivery fee** paid by the buyer, and the **listing fee** Etsy keeps on a cancelled sale — they are `etsy_extra`, below.

**The ledger gives the numbers** ([decisions](../decisions.md)): `outcomes.apply()` takes a receipt's money from
`ledger.view()` — the Etsy Net, the money before a refund, what went back, the fees Etsy gave back, the fees (`etsy_fees` = card
total − US tax − the money before a refund) and Etsy's lines the formula doesn't know (`etsy_extra`: Offsite Ads, a state's fee).
The formula and the state rules above give the **forecast** (`etsy_source: "forecast"`) until Etsy posts the sale; its sum stays
in `etsy_net_formula`. A cancellation or refund the ledger has no refund lines for yet (or one set by hand for money given
back outside Etsy) stays the forecast too, so a cancelled sale never shows its full sale. A VAT line given back points at the fee's
own VAT entry: `view()` puts it with that fee's refund (`is_refund()`), so «до повернення» is exact. `ledger.overhead()` gives what Etsy took outside the orders by day (an ads charge pays for the day before
it; the days not charged yet, up to today, get the last charged day's ads as a forecast; ads not charged for 3 days are off). `ledger.gaps()`
counts the breaks in the chain of running numbers and balances; with one, `refresh()` reads from `START` again next time.

## Where in the code

- [app/studio/printorders.py](../../app/studio/printorders.py) — `facts()`, `all_facts()`, `dead()`, `is_placed()`, `to_usd()`, `rates()`, `RATE_KEYS`, `js_round()`, `CANCELLED`, `PRINTIFY_NOT_PLACED`, `GELATO_NOT_PAID`
- [app/studio/reconcile.py](../../app/studio/reconcile.py) — `match()`, `_find()`, `_Printer`, `_numbers_named()`, `is_name_match()`, `normalize_name()`, `item_format()`, `cover_label()`, `printify_only_rows()`, `_NameIndex`
- [app/studio/fees.py](../../app/studio/fees.py) — `calculate_ukrainian_etsy_fees()`, `r2()`, `money()`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `rows()`, `apply()`, `auto_state()`, `unpaid()`, `order_info()`, `reserved_orders()`, `STATES`
- [app/studio/ledger.py](../../app/studio/ledger.py) — `refresh()`, `assign()`, `view()`, `overhead()`, `gaps()`, `is_refund()`, `FORMULA_TYPES`
- [app/studio/records.py](../../app/studio/records.py) — `remember_print_order()`, `load_sends()`, `SENDS`
- Tests: [app/tests/test_profit.py](../../app/tests/test_profit.py) (`ProfitParity` against `golden_profit.json`), [app/tests/test_states.py](../../app/tests/test_states.py) (`MatchingOrder`, `MoneyRules`)

## Related

- [Profit](../features/profit.md) · [Stages](order-stages.md)
