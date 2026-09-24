---
title: Profit (hidden until 1 October)
type: feature
updated: 2026-09-18
code:
  - app/web/js/pages/profit.js
  - app/studio/profit.py
  - app/studio/reconcile.py
  - app/studio/outcomes.py
  - app/studio/fees.py
---
# Profit

> A full equivalent of the Etsy Profit Calculator: for every Etsy receipt — net Etsy revenue minus the
> print cost. **The page is hidden**: accounting starts on 1 October 2026. The `profit.py` module still
> runs every day, though — it syncs orders for the queue.

## Status

- `pages/profit.js` exists, but it's in neither `NAV` nor `ROUTES` ([app.js](../../app/web/js/app.js)).
  To show it: add an entry to `NAV` and the route `#/profit` to `ROUTES` ([recipe](../recipes.md)).
- The formulas and matching rules are checked by a test against the original's code
  (`golden_profit.json`, results to the cent) — [rules/reconciliation.md](../rules/reconciliation.md).

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
- For the queue and the archive, only a **confirmed** print order counts (`is_placed()`): not a draft,
  not "on hold", paid, not cancelled. Matching for accounting (`reconcile.match()`) doesn't change this.
- After every sync (`_sync()`), the program checks the order archive — `archive.refresh_quietly()`
  deletes books whose 14 days are up.

## Where in the code

- [app/web/js/pages/profit.js](../../app/web/js/pages/profit.js) — `mount()`, `kpi()`, `renderTable()`, `detailHtml()`, `sync()`, `saveState()`, `orderPicker()`, `openMatch()`, `openReplacement()`, `PERIODS`
- [app/studio/profit.py](../../app/studio/profit.py) — `build_view()`, `cached_view()`, `SLIM_FIELDS`, `_data()`, `_row()`, `_candidates()`, `_set_link()`, `_set_state()`, `_delete_link()`, `mark_reprint()`, `unmark_reprint()`, `is_placed()`, `reserved_orders()`, `_sync()`
- [app/studio/reconcile.py](../../app/studio/reconcile.py) — `match()`, `printify_only_rows()`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `apply()`
- [app/studio/fees.py](../../app/studio/fees.py) — `calculate_ukrainian_etsy_fees()`
- Tests: [app/tests/test_profit.py](../../app/tests/test_profit.py), [app/tests/test_states.py](../../app/tests/test_states.py), [app/tests/test_archive.py](../../app/tests/test_archive.py) (`ReprintMark`)

## Related

- [Matching and profit](../rules/reconciliation.md) · [Sync](../rules/sync-policy.md) · [Open questions](../plans/open-questions.md)
