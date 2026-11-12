---
title: When orders are refreshed
type: rule
updated: 2026-11-12
code:
  - app/studio/sync.py
  - app/studio/profit.py
  - app/web/js/order-bits.js
---
# When orders are refreshed

> On launch, then quietly every hour while the program runs, and by the button at any time. A page never starts a sync itself; a page left open only follows a sync that ran or is running.

## How it runs
- `main()` calls `startup_sync()`; a thread (`_every_hour()`, `AUTO_EVERY` = 3600 s) repeats the job `profit-sync` via `_quiet_sync()` unless one is running. Not under `SANDBOX` (preview, tests).
- A sync needs an Etsy sign-in or a Printify token (`_connected()`); otherwise `POST /api/profit/sync` answers `not_configured`.
- The Orders page and the Order Creator's picker ask `GET /api/profit/sync` when opened: if one runs they show its steps and reload the list when done (`orderSync()`, shared); a list left open also notices a newer finished sync.
- The «Оновити замовлення» button calls `POST /api/profit/sync`; if one is already running the server returns its `jobId`.
- Between runs the last snapshot is shown (`data/profit/snapshot.json`) with an "Updated … ago" time.

## What a sync does (`_sync()`)
1. **Side by side**: Etsy (with its payment ledger), Printify and Gelato are read in parallel, each into its own part of the snapshot; the progress bar only moves forward (`_Together`). An Etsy failure fails the whole sync, once the others are through.
2. **Etsy**: only receipts changed since the last sync (`min_last_modified`, `SYNC_OVERLAP` = 1 hour). A full re-read happens on the first sync, every `FULL_SYNC_EVERY` (7 days), with another shop, when an open receipt lacks `ship_by`, or on request (`full`). `merge_receipts()` keeps each receipt once, since Etsy pages by offset and an order placed meanwhile could come twice. The ledger is read next (`ledger.refresh()`); its failure is a warning and the old ledger stays ([Reconciliation](reconciliation.md)).
3. **Printify** (read-only): every order with tracking ([Printify](../integrations/printify.md)). A failure is a warning and the previous data stays; a missing token gives no warning.
4. **Gelato**: orders and drafts of every account with a key; tracking per shipped order, `TRACKING_READS` per sync; an order is dropped only when its own account's list, loaded whole, lacks it (`_gelato_part()`, [Gelato](../integrations/gelato.md)). A failed read is a warning and the previous data stays.
5. The snapshot is saved. `loaded` records, per source, when its list last loaded in full: a failed or capped list keeps its old time (and the sync warns "only the latest N were loaded"). The archive trusts an order's absence only by this time; Gelato's is written only when every account loaded whole.
6. `archive.refresh_quietly()` reads the fresh snapshot (loads nothing) and deletes books whose 14 days are up ([Archive](../features/archive.md)).

## The view cache
`profit.cached_view()` rebuilds only when its key changes: the file stamps (`records.stamp()`: inode, mtime_ns, size) of snapshot, links, states, sends and ledger; the currency rates; whether Etsy tokens exist; and today's date (the ads forecast reaches a new day).

## Why
- Hourly: a refused Gelato payment or a new tracking number should not wait for the button.
- File stamps and not mtime alone: two writes inside one Windows clock tick share an mtime.

## Where in the code
- [app/studio/sync.py](../../app/studio/sync.py) — `startup_sync()`, `_quiet_sync()`, `_sync()`, `_gelato_part()`, `merge_receipts()`, `FULL_SYNC_EVERY`, `SYNC_OVERLAP`
- [app/studio/profit.py](../../app/studio/profit.py) — `cached_view()`
- [app/studio/records.py](../../app/studio/records.py) — `stamp()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `orderSync()`
- Tests: [app/tests/test_orders.py](../../app/tests/test_orders.py) — `SyncAtStartHourlyOrByHand`; [app/tests/test_states.py](../../app/tests/test_states.py) — `IncrementalSync`

## Related
- [Order stages](order-stages.md) · [Etsy](../integrations/etsy.md) · [Orders](../features/orders.md)
