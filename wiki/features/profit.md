---
title: Profit (hidden until 1 October)
type: feature
updated: 2026-09-27
code:
  - app/web/js/pages/profit.js
  - app/web/js/pages/profit-rows.js
  - app/studio/profit.py
  - app/studio/reconcile.py
  - app/studio/outcomes.py
  - app/studio/fees.py
  - app/studio/records.py
---
# Profit

> A full equivalent of the Etsy Profit Calculator: for every Etsy receipt — net Etsy revenue minus the
> print cost. **The page is hidden**: accounting starts on 1 October 2026. The sync behind it (`sync.py`) runs
> every day, though — it feeds the queue.

**How the server side is built (since 2026-09-26, the big cleanup).** Before, one `profit.py` held the sync, the
files, the stages, the Profit view and its routes, and the archive and it loaded each other. Now:
`sync.py` pulls the orders; `records.py` keeps the files (snapshot, links, states, sends); `printorders.py` reads a
print order one way; `reconcile.py` matches, `outcomes.py` works out the money once; `stages.py` gives the queue
its stages; `profit.py` is only the Profit view (`build_view()` → `outcomes.rows()`, cached until one of its files
changes — `records.stamp()`) and its routes.

## Status

- `pages/profit.js` exists, but it's in neither `MODES.orders.nav` nor `ROUTES` ([app.js](../../app/web/js/app.js)).
  To show it: an entry in `MODES.orders.nav` and the route `#/profit` in `ROUTES` ([recipe](../recipes.md)).
- The formulas and matching rules are checked by a test against the original's code
  (`golden_profit.json`, results to the cent) — [rules/reconciliation.md](../rules/reconciliation.md). Where the
  program now differs on purpose (orders in pounds converted, not counted as dollars), the test says so.
- **Ready to be shown (2026-09-26):** the page follows the owner's interface rules — the refresh and «more» as
  icons in one group, the shared tooltips (`data-tip`), no emoji, no English label, no styles written into the
  markup, no explanations under the numbers; it shows an order not paid yet at the printer («Не оплачено», no
  profit until it is) and one billed in a currency without a rate.

## What the page can do

- Periods (today, 7 days, 30 days, all time, custom), metrics, a table of 50 rows at a time, search.
- A row expands: a breakdown of fees, cost, state.
- Manual matching to a Printify/Gelato order, or "no cost".
- States: cancelled, full/partial refund (amount), replacement (a reprint order and/or an amount).
- A sync button (and a full one — re-reading every receipt).

## What works even without the page

- **A reprint from the [order archive](archive.md)** records a "replacement" state for the receipt on
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

- [app/web/js/pages/profit.js](../../app/web/js/pages/profit.js) — `mount()`, `kpi()`, `renderTable()`, `sync()`, `saveState()`, `orderPicker()`, `openMatch()`, `openReplacement()`, `PERIODS`
- [app/web/js/pages/profit-rows.js](../../app/web/js/pages/profit-rows.js) — `rowInner()`, `detailHtml()`, `stateBox()`, `econLines()`, `costOf()`, `DEAD_SHORT`, `STATE_OPTS`
- [app/studio/profit.py](../../app/studio/profit.py) — `build_view()`, `cached_view()`, `SLIM_FIELDS`, `_data()`, `_row()`, `_candidates()`, `_set_link()`, `_set_state()`, `_delete_link()`
- [app/studio/stages.py](../../app/studio/stages.py) — `mark_reprint()`
- [app/studio/records.py](../../app/studio/records.py) — `unmark_reprint()`
- [app/studio/printorders.py](../../app/studio/printorders.py) — `is_placed()`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `reserved_orders()`
- [app/studio/sync.py](../../app/studio/sync.py) — `_sync()`
- [app/studio/reconcile.py](../../app/studio/reconcile.py) — `match()`, `printify_only_rows()`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `rows()`, `apply()`, `order_info()`
- [app/studio/records.py](../../app/studio/records.py) — `stamp()`, `load_snapshot()`, `load_links()`, `load_states()`, `load_sends()`, `save()`, `lock`
- [app/studio/fees.py](../../app/studio/fees.py) — `calculate_ukrainian_etsy_fees()`
- Tests: [app/tests/test_profit.py](../../app/tests/test_profit.py), [app/tests/test_states.py](../../app/tests/test_states.py), [app/tests/test_archive.py](../../app/tests/test_archive.py) (`ReprintMark`)

## Related

- [Matching and profit](../rules/reconciliation.md) · [Sync](../rules/sync-policy.md) · [Open questions](../plans/open-questions.md)
