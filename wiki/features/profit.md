---
title: Profit
type: feature
updated: 2026-11-12
code:
  - app/web/js/pages/profit.js
  - app/web/js/pages/profit-rows.js
  - app/web/js/pages/profit-calendar.js
  - app/studio/profit.py
  - app/studio/ledger.py
---
# Profit

> «Прибуток» (`#/profit`, rail, Alt+3): for every Etsy receipt, the net Etsy money minus the print cost, summed by period. It counts **only sales from 2026-10-01**; before the first one the page says «Продажів від 1 жовтня ще немає». Matching and formulas are in [Reconciliation](../rules/reconciliation.md); the sync that feeds it is in [Sync](../rules/sync-policy.md).

## Accounting start
- `profit.ACCOUNTING_FROM` is midnight of 1 October 2026 on this computer's clock; `counted()` decides. `/api/profit/data`, `/api/profit/row` (an earlier order is 404) and `/api/profit/candidates` are cut the same way, and the response carries `accountingFrom` and `overheadPerDay`. «Увесь час» means from 1 October.
- The queue, stages and archive still read every order (`cached_view()["full"]` is not cut). Accounting makes no requests of its own; the sync asks Etsy and the printers.
- The empty-state text is built from `accountingFrom`.

## Money
- **Etsy Net comes from Etsy's payment ledger** (`ledger.refresh()`, read-only, scope `transactions_r`). A sale Etsy has not posted yet shows the formula's forecast: faint, with a clock and the tip «Прогноз за формулою: у журналі Etsy цього ще немає». Fees under it are the real ones; ledger lines the formula does not know (`etsy_extra`, e.g. Offsite Ads) are underlined dotted and named in the tip. An open row reads «За журналом Etsy: $X · формула дала $Y …» or «збігається з формулою»; a partial refund Etsy has posted shows its amount «з журналу Etsy».
- A break in the ledger's chain (`ledger.gaps()`) is a warning above the table; the next sync reads the ledger again.
- **Ads and new-listing fees** are taken from the ledger by day (`ledger.overhead()` → `overheadDays`): an ads charge at about 07:40 pays for the day before; days not charged yet use the last charged day's ads (forecast). They come off «Чистий прибуток» and the margin for every day of the period inside the books, including days without sales, and have **no card of their own**; table rows stay per order, so their sum is a little above the card. With no ledger at all, `profit.OVERHEAD_PER_DAY` is a flat fallback per day.
- Under «Собівартість друку» a caption «+ реклама $X» (tooltip: Etsy Ads + Offsite Ads): the ledger's per-day ads plus the period's Offsite Ads fees, which are already inside Etsy Net, so it is a caption only. Under «На руки» a line «N замовлень · Offsite Ads −$X».
- A print cost in a foreign currency is converted at the rates in settings, never read as dollars; one with no rate shows no profit ([Reconciliation](../rules/reconciliation.md)). An order not yet paid at the printer shows «Не оплачено» and has no profit.
- The header names the connected printers: «Gelato» with a key, `Printify: <shop>` only with a Printify token.

## Cards and periods
- **Cards:** «На руки (Etsy Net)» (orders count under it), «Собівартість друку», «Чистий прибуток», «Середня маржа». A period with no sales shows the numbers grey (`kpi-none`); the ads of those days still come off, so the profit may be a red loss.
- **Periods** (`PERIODS`, `MORE`, `range()` in `profit.js`): on view «Сьогодні», «Вчора», «Цей тиждень», «Цей місяць», «Увесь час»; behind «Ще ▾»: «Минулий тиждень», «Минулий місяць», «30 днів», «Свій період» (only it opens two dates). Weeks follow **payouts to Payoneer** (`ledger.PAYOUT = "DISBURSE"` entries), not the calendar: «Цей тиждень» runs from the last payout, «Минулий тиждень» between the last two; a payout's own day counts its ads in the week it closes. With no payouts the weeks are the last 7 days and the 7 before.

## Views
- **«Замовлення»** (table): paged, searchable; a row expands to fees, cost, state (`profit-rows.js`). Manual match to a print order or «no cost»; states cancelled, full or partial refund, replacement; the replacement picker offers every order and marks the one matching now «зараз як перший друк». Buttons: sync and full sync (re-reads every receipt).
- **«Лістинги»** (`#pf-view`, remembered): the period's sales summed by Etsy listing: books, «На руки», cost, profit, profit per book, best first (`listingRows()`, `renderListings()`). An order of books from two listings shares its money by books; a cancelled or fully refunded sale counts money but no book; ads are not split. A page left open reloads after an hourly sync unless a row is open (`watchSyncs()`).
- **Calendar** (`#pf-flip`, remembered as `screen`; `makeCalendar()`): a month, Monday first, a red dot per sale (not cancelled or fully refunded), a tinted day when it sold, a hover card with the day's profit, sales, ads and listing fees (marked «прогноз» or «оцінка»), and sales still without a cost. Each week's profit stands at the end of its row, the month's in the head. Money is the cards' own (`kpi(rows, days)`), so the month equals «Цей місяць»; the weeks are **calendar weeks** (Mon–Sun), and a week crossing the month counts only the shown month's days.

## Reprints and the archive
A reprint is recorded as a state "replacement" for its receipt (`stages.mark_reprint()`; `records.unmark_reprint()` clears it): the new print order joins `replacementOrders`, matching keeps the first order, and the reprint is not a new sale. Cancelled or refunded receipts and receipts whose first order was cancelled at the printer are untouched. Only a **placed** print order counts (`printorders.is_placed()`). After each sync `archive.refresh_quietly()` runs ([Archive](archive.md)).

## Why
- Earlier orders are not counted at all; a clean start is the owner's rule.
- Ads and listing fees are a caption, not a card: the profit already contains them.
- Weeks follow payouts because that is the owner's money rhythm; the calendar view uses calendar weeks on purpose.
- "No sales" is grey: green zeros look earned. Orange means an action.
- The calendar is deliberately softer than the rest (round days, no grid, a rounded hover card).
- Formulas are checked against `golden_profit.json` to the cent.
- Not in Profit: payout to card, bank fees, taxes, fixed costs.

## Where in the code
- [app/web/js/pages/profit.js](../../app/web/js/pages/profit.js) — `PERIODS`, `MORE`, `range()`, `kpi()`, `listingRows()`
- [app/web/js/pages/profit-calendar.js](../../app/web/js/pages/profit-calendar.js) — `makeCalendar()`
- [app/web/js/pages/profit-rows.js](../../app/web/js/pages/profit-rows.js) — `rowInner()`, `detailHtml()`
- [app/studio/profit.py](../../app/studio/profit.py) — `ACCOUNTING_FROM`, `OVERHEAD_PER_DAY`, `counted()`, `build_view()`, `cached_view()`
- [app/studio/ledger.py](../../app/studio/ledger.py) — `refresh()`, `overhead()`, `gaps()`, `PAYOUT`
- [app/studio/stages.py](../../app/studio/stages.py) — `mark_reprint()`
- Tests: [app/tests/test_profit.py](../../app/tests/test_profit.py), [app/tests/test_ledger.py](../../app/tests/test_ledger.py)

## Related
- [Reconciliation](../rules/reconciliation.md) · [Sync](../rules/sync-policy.md) · [Order stages](../rules/order-stages.md) · [Archive](archive.md) · [Etsy](../integrations/etsy.md)
