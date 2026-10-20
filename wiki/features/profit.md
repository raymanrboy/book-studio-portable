---
title: Profit (counts only sales from 1 October 2026)
type: feature
updated: 2026-10-21
code:
  - app/web/js/pages/profit.js
  - app/web/js/pages/profit-rows.js
  - app/web/js/pages/profit-calendar.js
  - app/studio/profit.py
  - app/studio/reconcile.py
  - app/studio/outcomes.py
  - app/studio/fees.py
  - app/studio/records.py
  - app/studio/ledger.py
---
# Profit

> A full equivalent of the Etsy Profit Calculator: for every Etsy receipt — net Etsy revenue minus the
> print cost. In the rail as «Прибуток» (Alt+3); it counts **only sales from 1 October 2026** (the owner: "it must not
> include earlier orders at all") — before the first one it says «Продажів від 1 жовтня ще немає». The sync behind it (`sync.py`) feeds the queue too.

**How the server side is built (since 2026-09-26, the big cleanup).** Before, one `profit.py` held the sync, the
files, the stages, the Profit view and its routes, and the archive and it loaded each other. Now:
`sync.py` pulls the orders; `records.py` keeps the files (snapshot, links, states, sends); `printorders.py` reads a
print order one way; `reconcile.py` matches, `outcomes.py` works out the money once; `stages.py` gives the queue
its stages; `profit.py` is only the Profit view (`build_view()` → `outcomes.rows()`, cached until one of its files
changes — `records.stamp()`) and its routes.

## Status

- In `PLACES` and `ROUTES` as `#/profit` ([app.js](../../app/web/js/app.js)), Alt+3.
- **No sales in the period** (since 2026-09-30): the four numbers stay grey (`kpi-none`) — green zeros looked earned;
  the average margin has no ink of its own (the orange means an action). The ads of those days still come off (since
  2026-10-13): the «Чистий прибуток» is then a loss, in red (`.kpi-none .kpi.tone-red`).
- **A clean slate on 1 October 2026** (the owner, 25 and 27.09.2026: "it must not include earlier orders at all"):
  `profit.ACCOUNTING_FROM` — midnight of 1 October on this computer's clock; `counted()` decides. The page's rows
  (`/api/profit/data`), one row (`/api/profit/row` — an older one is 404) and the print orders offered for a manual
  link (`/api/profit/candidates`) are only from that day; `accountingFrom` tells the page. **The queue, the stages
  and the archive still read every order** — they take `cached_view()["full"]`, which is not cut; the sync asks
  Etsy and the printers exactly as before (accounting makes no requests of its own). So «Увесь час» means from
  1 October.
- The formulas and matching rules are checked by a test against the original's code
  (`golden_profit.json`, results to the cent) — [rules/reconciliation.md](../rules/reconciliation.md). Where the
  program now differs on purpose (orders in pounds converted, not counted as dollars), the test says so.
- **Ready to be shown (2026-09-26):** the page follows the owner's interface rules — the refresh and «more» as
  icons in one group, the shared tooltips (`data-tip`), no emoji, no English label, no styles written into the
  markup, no explanations under the numbers; it shows an order not paid yet at the printer («Не оплачено», no
  profit until it is) and one billed in a currency without a rate.

## What the page can do

- **Etsy's own ledger gives the Etsy money (since 2026-10-13; from 2026-10-05 it only checked the formula).** The sync also
  reads Etsy's payment ledger (`ledger.refresh()`, read only, the scope `transactions_r` the program has) — see
  [rules/reconciliation.md](../rules/reconciliation.md).
  - **The cards are the period's own** — «На руки (Etsy Net)» with the orders count under it, «Собівартість друку», «Чистий прибуток»,
    «Середня маржа». (From 2026-10-05 to 2026-10-06 the first card was the Etsy balance, «Доступно до виводу», with the program's
    expected sum under it; the owner had it taken off: "return it as it was".)
  - **Each row**: the Etsy Net is Etsy's real money (`etsy_source: "ledger"`); a sale Etsy hasn't posted yet (seconds after it)
    is the formula's forecast — faint, with a clock and the tip «Прогноз за формулою: у журналі Etsy цього ще немає». The fees under
    it are the real ones; when they hold lines the formula doesn't know (`etsy_extra`), they are underlined dotted and the tip
    names them («У т.ч. Offsite Ads -$5.72»). The open row says «За журналом Etsy: $X · формула дала $Y · Offsite Ads …» or
    «збігається з формулою». A partial refund Etsy has posted shows its amount «з журналу Etsy» instead of the amount field.
    (2026-10-05 – 2026-10-13: the formula's sum with an amber mark when the ledger differed.)
  - A break in the ledger's chain (`ledger.gaps()`) is a warning above the table; the next sync reads the ledger again.
  - The header names only the printers connected now: «Gelato» with a Gelato key, «Printify: shop» only with a Printify token.
- **Ads and new listings are counted quietly (since 2026-10-05; from the ledger since 2026-10-13).** Etsy takes money outside
  any order — Etsy Ads and the fee for each new listing. The page gets them by day from the ledger (`overheadDays`,
  `ledger.overhead()`: an ads charge, ~07:40, pays for the day before; the days not charged yet are the last charged day's ads, a
  forecast) and subtracts the days of the chosen period that are inside the books (`periodDays()`, `overhead()`) from the
  «Чистий прибуток» and the margin, on days without sales too — **no card of its own** (the owner didn't want to see it). The table's rows stay per order, so
  their sum is a little above the card. With no ledger at all the old estimate stands in: **$1.38 a day** (`profit.OVERHEAD_PER_DAY`,
  `overheadPerDay`, from the owner's September–October statements).
  **The ads' sum is said under «Собівартість друку»** (2026-10-17, `+ реклама $X`; tooltip: Etsy Ads + Offsite Ads): Etsy Ads from the ledger's
  per-day `ads` (`adsSpend()`; the ads part of the overhead, forecast days included) plus the period's Offsite Ads fees (`kpi().offsite`, already inside the Etsy Net). Only a caption — the profit already has both.

- **Periods (since 2026-10-13, the owner's list):** on view «Сьогодні», «Вчора», «Цей тиждень», «Цей місяць», «Увесь час»; behind
  «Ще ▾» (a menu; the button takes the name of the one picked) «Минулий тиждень», «Минулий місяць», «30 днів», «Свій період» (only
  it opens the two dates). The weeks follow the payouts to Payoneer, not the calendar: «Цей тиждень» from the last payout (its tip
  names it), «Минулий тиждень» between the last two (`payouts` — the ledger's DISBURSE entries); a payout's own day counts its ads
  in the week it closes. With no payouts the weeks are the last 7 days and the 7 before. `range()` in `profit.js` gives every
  period's sales window and its days for the ads; the saved `7d` / `month` (30 days) become `week` / `30d`.
- **«Лістинги»** (since 2026-10-14): a second view of the table (`#pf-view`, icons «Замовлення» / «Лістинги», remembered):
  the period's sales summed by the Etsy listing they came from — books, «На руки», cost, profit and profit a book, best
  first (`listingRows()`, `renderListings()`; the server sends each row's `listings`). An order of books from two listings
  shares its money by the books; a cancelled or fully refunded sale counts its money but no book; the shop's ads are not
  split (the header's tip says so). The page left open loads again after an hourly sync (`watchSyncs()`), unless a row is open. Replaces counting from Etsy's CSV.
- **Offsite Ads for the period** (since 2026-10-14): under «На руки», «N замовлень · Offsite Ads −$X» — the ledger's
  `offsite_ads_fee` lines of the counted rows (already inside the Etsy Net; the tip says for how many sales).
- **The calendar page** (since 2026-10-21, the owner's whiteboard in the program): an arrow in the head (`#pf-flip`, a table and a calendar
  icon beside it, the page shown lit — two bare dots at first didn't say what the pages are; remembered as `screen`) flips the page from the cards and the table to a month calendar. Monday first, a
  **red dot for every sale** (not a cancelled or fully refunded one), the day's circle tinted when it sold; hovering (or focusing)
  a day shows a small card: the day, its profit, the dots and «N продажів · на руки $X», the day's ads and new-listing fees (marked «прогноз» while the
  ledger only forecasts them, «оцінка» with no ledger at all) and how many sales still have no cost (left out of the sum). Each week's profit stands at the end of its
  row, the month's in the head; arrows go back to the month books start in and forward to this month. **The money is the cards'
  own** — `kpi(rows, days)` for that day / week / month, so the month equals «Цей місяць» on the cards (the ads of each day come off,
  a day without sales can be a small loss). The weeks are **calendar weeks** (Mon–Sun, as on the board), not the payout weeks of the
  periods; a week crossing the month counts only the shown month's days, so the weeks add up to the month. On purpose softer than the
  rest of the program (round days, no grid lines, a light rounded hover card with a tail) — the owner asked for it.
- Metrics, a table of 50 rows at a time, search.
- A row expands: a breakdown of fees, cost, state.
- Manual matching to a Printify/Gelato order, or "no cost".
- States: cancelled, full/partial refund (amount), replacement (a reprint order and/or an amount). The replacement picker
  offers every order, the one matching now counts as the receipt's first print too, marked «зараз як перший друк» (one linked
  by hand stays excluded and refused by `_replacement_orders()`) (since
  2026-10-18: two Gelato orders of the same name, and only the first print could be picked as the reprint — the costs
  came out under swapped labels).
- A sync button (and a full one — re-reading every receipt).

## What works even without the page

- **A reprint from the [order archive](archive.md)**, or one with new files (the Order Creator's «Передрук» tick), records a "replacement" state for the receipt on
  its own (`mark_reprint()`): the new print order is added to `replacementOrders`, so matching keeps the
  first print order attached to the receipt (its stage in the queue doesn't jump), and the reprint isn't
  counted as a new sale. A receipt with a "cancelled" or "refund" state isn't touched; neither is a
  receipt whose print order was cancelled at the printer (then the reprint gets matched as a normal
  order instead). A reprint that never became an order clears the mark (`unmark_reprint()`); a
  "replacement" state the archive made, once nothing is left in it, disappears.
- Only a **confirmed** print order counts (`is_placed()`): not a draft, not "on hold", paid, not cancelled — for
  the queue, the archive, and since 2026-09-26 for the money too.
- After every sync (`_sync()`), the program checks the order archive — `archive.refresh_quietly()`
  deletes books whose 14 days are up.

## Where in the code

- [app/web/js/pages/profit.js](../../app/web/js/pages/profit.js) — `mount()`, `listingRows()`, `renderListings()`, `VIEWS`, `range()`, `renderPeriod()`, `setPeriod()`, `weekHint()`, `kpi()`, `periodDays()`, `overhead()`, `renderKpis()`, `renderTable()`, `sync()`, `saveState()`, `orderPicker()`, `openMatch()`, `openReplacement()`, `renderFlip()`, `flip()`, `PERIODS`, `MORE`
- [app/web/js/pages/profit-calendar.js](../../app/web/js/pages/profit-calendar.js) — `makeCalendar()` (`render()`, `show()`), `sold`, `pending`, `MAX_DOTS`
- [app/web/js/pages/profit-rows.js](../../app/web/js/pages/profit-rows.js) — `rowInner()`, `netCell()`, `detailHtml()`, `stateBox()`, `econLines()`, `costOf()`, `DEAD_SHORT`, `STATE_OPTS`
- [app/studio/ledger.py](../../app/studio/ledger.py) — `refresh()`, `assign()`, `view()`, `overhead()`, `gaps()`, `LABELS`, `SHOP_TYPES`
- [app/studio/profit.py](../../app/studio/profit.py) — `ACCOUNTING_FROM`, `OVERHEAD_PER_DAY`, `counted()`, `build_view()`, `cached_view()`, `SLIM_FIELDS`, `_data()`, `_row()`, `_candidates()`, `_set_link()`, `_set_state()`, `_delete_link()`
- [app/studio/stages.py](../../app/studio/stages.py) — `mark_reprint()`
- [app/studio/records.py](../../app/studio/records.py) — `unmark_reprint()`
- [app/studio/printorders.py](../../app/studio/printorders.py) — `is_placed()`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `reserved_orders()`
- [app/studio/sync.py](../../app/studio/sync.py) — `_sync()`
- [app/studio/reconcile.py](../../app/studio/reconcile.py) — `match()`, `printify_only_rows()`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `rows()`, `apply()`, `order_info()`
- [app/studio/records.py](../../app/studio/records.py) — `stamp()`, `load_snapshot()`, `load_links()`, `load_states()`, `load_sends()`, `save()`, `lock`
- [app/studio/fees.py](../../app/studio/fees.py) — `calculate_ukrainian_etsy_fees()`
- Tests: [app/tests/test_profit.py](../../app/tests/test_profit.py) (`BookkeepingStart`), [app/tests/test_ledger.py](../../app/tests/test_ledger.py), [app/tests/test_states.py](../../app/tests/test_states.py), [app/tests/test_archive.py](../../app/tests/test_archive.py) (`ReprintMark`)

## Related

- [Matching and profit](../rules/reconciliation.md) · [Sync](../rules/sync-policy.md) · [Known limits](../dev/limits.md)
