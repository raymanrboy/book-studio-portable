---
title: When orders are refreshed
type: rule
updated: 2026-09-26
code:
  - app/studio/profit.py
  - app/web/js/order-bits.js
---
# When orders are refreshed

> **Only ever twice: once automatically on launch, and after that only by button.**
> Pages never load anything on their own (the owner's requirement, 2026-09-15).

## How it works

- On launch, `main()` calls `startup_sync()`: if Etsy or Printify is connected, a background job
  `profit-sync` starts.
- The "Orders" page and picking an order in the Order Creator both ask `GET /api/profit/sync` when
  opened: if a sync is running, they show its steps and refresh the list once it's done (one shared
  function for both, `orderSync()` in `order-bits.js`).
- The "Update orders" button → `POST /api/profit/sync`; if a sync is already running, the server returns
  that same one (`jobId`) instead of starting a second.
- Between runs, the last snapshot is shown (`data/profit/snapshot.json`) with an "Updated … ago" time.

## What a sync does (`_sync()`)

1. **Etsy**: only receipts changed since the previous sync (with a 1-hour overlap); a full re-read
   happens on the first sync, once a week, with a different shop, or on request (`full`). An Etsy
   failure = a failure of the whole sync. A full read keeps each receipt once (`merge_receipts()`): Etsy pages
   by offset, so an order placed while the pages are read made one receipt come twice — a doubled queue row
   and doubled money (the 2026-09-26 audit).
2. **Printify**: every order in the shop (with tracking numbers). A failure → a warning, the previous
   data stays.
3. **Gelato**: every order (orders and drafts). The search doesn't return tracking numbers, so for
   shipped orders the program reads each order individually (`attach_shipments()`): **once** per order,
   read again only while it has no tracking number and its status has changed; tracking numbers already
   found carry over from the previous snapshot; no more than 60 reads per refresh. A read that fails →
   a warning, tried again on the next refresh. A search failure → a warning, the previous data stays.
4. Saving the snapshot and recomputing the view cache (`cached_view()`). In the snapshot, `loaded` — for
   Etsy, Printify, and Gelato separately — records when their list last **loaded in full**: a list that
   failed to load keeps its old time; a list that stopped at its cap (Etsy 20,000 receipts, Printify 400
   pages, Gelato 5000) does too, and the sync warns "only the latest N were loaded". This time decides
   whether the archive trusts an order's absence (since 2026-09-23).
5. Checking the [order archive](../features/archive.md) (`archive.refresh_quietly()`): with the fresh
   stages and printer statuses, books whose 14 days are up get deleted. On its own, this loads nothing —
   it only reads the snapshot just saved.

The view cache updates based on a write counter, `_writes` (plus the files' modified time): two writes
within one Windows clock "tick" get the same modified time — a bug fixed on 2026-09-16.

## Where in the code

- [app/studio/profit.py](../../app/studio/profit.py) — `startup_sync()`, `_start_sync()`, `_sync_state()`, `_sync()`, `merge_receipts()`, `cached_view()`, `_save()`, `FULL_SYNC_EVERY`, `SYNC_OVERLAP`
- [app/studio/gelato.py](../../app/studio/gelato.py) — `attach_shipments()`, `TRACKING_READS`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `syncOrders()`, `runningSync()`, `watchSync()`
- [app/web/js/pages/orders.js](../../app/web/js/pages/orders.js) — `refresh()`
- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — `refresh()`
- [app/studio/main.py](../../app/studio/main.py) — `main()`
- [app/studio/archive.py](../../app/studio/archive.py) — `refresh_quietly()`
- Tests: [app/tests/test_orders.py](../../app/tests/test_orders.py) (`SyncOnlyAtStartOrByHand`), [app/tests/test_states.py](../../app/tests/test_states.py) (`IncrementalSync`)

## Related

- [Stages](order-stages.md) · [Etsy](../integrations/etsy.md) · [Decisions](../decisions.md)
