---
title: When orders are refreshed
type: rule
updated: 2026-10-28
code:
  - app/studio/sync.py
  - app/studio/profit.py
  - app/web/js/order-bits.js
---
# When orders are refreshed

> **On launch, then quietly every hour while the program runs, and by the button at any time** (the
> owner: a refused Gelato payment or a new tracking number should not wait for the button). A page never starts a
> sync itself; one left open only follows a sync that ran or is running.

## How it works

- On launch, `main()` calls `startup_sync()`: if Etsy or Printify is connected, a background job
  `profit-sync` starts; then a thread (`_every_hour()`, `AUTO_EVERY`) runs the same job every hour unless one is
  already running (`_quiet_sync()`) — not in the preview or the tests (`SANDBOX`).
- The "Orders" page and picking an order in the Order Creator both ask `GET /api/profit/sync` when
  opened: if a sync is running, they show its steps and refresh the list once it's done (one shared
  function for both, `orderSync()` in `order-bits.js`; both list the same orders — `GET /api/orders`).
  An Orders list left open also notices a newer finished sync ([orders](../features/orders.md)).
- The "Update orders" button → `POST /api/profit/sync`; if a sync is already running, the server returns
  that same one (`jobId`) instead of starting a second.
- Between runs, the last snapshot is shown (`data/profit/snapshot.json`) with an "Updated … ago" time.

## What a sync does (`_sync()`)

0. **Side by side**: Etsy (with its payment ledger), Printify and Gelato are read in parallel, each into its own part of the snapshot (`ThreadPoolExecutor` in `_sync()`); the progress bar only moves forward (`_Together`). An Etsy failure still fails the whole sync — once the other two are through.
1. **Etsy**: only receipts changed since the previous sync (with a 1-hour overlap); a full re-read
   happens on the first sync, once a week, with a different shop, or on request (`full`). An Etsy
   failure = a failure of the whole sync. A full read keeps each receipt once (`merge_receipts()`): Etsy pages
   by offset, so an order placed while the pages are read could come twice.
2. **Printify** (read-only): every order in the shop, with tracking numbers ([printify](../integrations/printify.md)).
   A failure → a warning, the previous data stays; a missing token gives **no** warning.
3. **Gelato**: every order (orders and drafts), each account the program has a key for; tracking numbers are read
   per shipped order, and an order is dropped only when its own account's list, loaded whole, lacks it
   ([gelato](../integrations/gelato.md)). A failed read or search → a warning, the previous data stays.
4. Saving the snapshot and recomputing the view cache (`cached_view()`). In the snapshot, `loaded` — for
   Etsy, Printify, and Gelato separately — records when their list last **loaded in full**: a list that
   failed to load keeps its old time; a list that stopped at its cap does too, and the sync warns "only the latest N
   were loaded". This time decides whether the archive trusts an order's absence. For Gelato it is written only
   when every account loaded whole.
5. Checking the [order archive](../features/archive.md) (`archive.refresh_quietly()`): with the fresh
   stages and printer statuses, books whose 14 days are up get deleted. On its own, this loads nothing —
   it only reads the snapshot just saved.

The view cache updates based on a write counter, `_writes` (plus the files' modified time): two writes
within one Windows clock "tick" get the same modified time.

## Where in the code

- [app/studio/profit.py](../../app/studio/profit.py) — `cached_view()`
- [app/studio/sync.py](../../app/studio/sync.py) — `startup_sync()`, `_start_sync()`, `_sync_state()`, `_sync()`, `merge_receipts()`, `FULL_SYNC_EVERY`, `SYNC_OVERLAP`
- [app/studio/records.py](../../app/studio/records.py) — `save()`
- [app/studio/gelato.py](../../app/studio/gelato.py) — `attach_shipments()`, `TRACKING_READS`, `accounts()`
- [app/studio/sync.py](../../app/studio/sync.py) — `_gelato_part()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `syncOrders()`, `runningSync()`, `watchSync()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `orderSync()`: the sync button of the queue
  ([orders.js](../../app/web/js/pages/orders.js) `mount()`) and of the Order Creator's picker
  ([creator-picker.js](../../app/web/js/pages/creator-picker.js) `pickEtsyOrder()`)
- [app/studio/main.py](../../app/studio/main.py) — `main()`
- [app/studio/archive.py](../../app/studio/archive.py) — `refresh_quietly()`
- Tests: [app/tests/test_orders.py](../../app/tests/test_orders.py) (`SyncOnlyAtStartOrByHand`), [app/tests/test_states.py](../../app/tests/test_states.py) (`IncrementalSync`)

## Related

- [Stages](order-stages.md) · [Etsy](../integrations/etsy.md) · [Decisions](../decisions.md)

With Etsy connected, every sync also reads Etsy's payment ledger (`ledger.refresh()`); a failure is a warning and the
old ledger stays ([reconciliation](reconciliation.md)).
