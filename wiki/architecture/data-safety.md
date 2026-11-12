---
title: Data safety — how the owner's data is kept from being lost
type: architecture
updated: 2026-11-12
code:
  - app/studio/core.py
  - app/studio/aside.py
  - app/studio/records.py
  - app/tools/data_history.py
  - app/tools/sample_data.py
  - app/tests/test_aside.py
  - app/tests/test_data_safety.py
  - app/tests/test_sample_guard.py
---
# Data safety

> Independent layers make a bad write undoable, whoever makes it: the program, a script or an agent.

## The layers

1. **History of every write** (`core.keep_history()`, called by `write_json()`): before a write replaces an important file, the old file goes to `app/data/history/<its path>/<time>.json` — the last `HISTORY_KEEP` (20) versions, never the same twice, no more often than the file's rule in `HISTORY_RULES`: send journal, links, states and archive entries at every change; settings, vault and creator files every 5 min; a library book every minute; the shops' snapshot hourly. The `.bak` stays as well ([data](data.md#file-writing)).
2. **A daily snapshot** (`core.daily_snapshot()`, a thread at start): every file under those rules plus the Workshop books' `book.json` into `history/daily/<date>/`, the last `DAILY_KEEP` (14) days. Not in the preview or tests.
3. **Guards on what costs most** (`records._guard()` via `records.save()`): the send journal (`profit/print-orders.json`) is add-only — a write that would drop a receipt is refused (`DataGuard`), because losing a send lets an order go out twice. The shops' snapshot may not shrink below half of what it holds.
4. **Tests and preview cannot reach real data**: `studio.core` raises under `unittest` if `BOOK_STUDIO_DATA` is unset; the tests make their own temporary folder; `tools/sample_data.seed()` refuses unless `studio.core` points at the made-up folder; the preview server claims only its own marked folder and never takes keys ([preview](../dev/preview.md), [testing](../dev/testing.md)).
5. **Nothing the owner made is deleted for good**: a library book goes to `data/library/trash`; a Workshop book, a photo template and a slide set go through `desktop.to_recycle_bin()` (it warns instead of deleting if Windows cannot recycle). Deleted for good: caches, previews, runs, the opened keys of an import, a module's own folder, and the [order archive](../features/archive.md) after its retention days.
   **The shelf before the Recycle Bin** (`aside.py`): a Workshop book and a photo template first wait `KEEP_SECONDS` in `data/aside/<token>/` with a note of where they were, so the toast's «Скасувати» (`POST /api/aside/restore`) puts them back — never over something standing there now. Then `flush()` sends them on to the Recycle Bin; what the shelf still holds when the program closes goes there at the next start. That is why these removals do not ask first.
6. **Putting a version back**: `python app/tools/data_history.py list` or `restore <path> [--version V | --daily DATE]`. A restore first keeps the file it replaces as a version of its own.

## Rules for an agent working on this data

- Before any script that writes into `app/data` or `pipeline/books`: copy what it will touch into `app/data/merge-backup/`, and run it on a copy first when possible.
- Never import `studio` in a scratch script without setting `BOOK_STUDIO_DATA` (and `BOOK_STUDIO_SAMPLE=1` for made-up data) **before** the first import: `studio.core` fixes the folder at import.
- Start the preview only with `tools/dev_server.py`.
- Undo a wrong write from the history (`list`, then `restore`), not by guessing.

## Why
- Layers are independent so one failing (a missed `.bak`, a bad script) still leaves another.
- The send journal is add-only: a lost record means a duplicate order and a second bill.

## Where in the code
- [app/studio/core.py](../../app/studio/core.py) — `HISTORY_RULES`, `HISTORY_KEEP`, `DAILY_KEEP`, `keep_history()`, `daily_snapshot()`, `write_json()`
- [app/studio/aside.py](../../app/studio/aside.py) — `put()`, `restore()`, `flush()`, `SHELF`, `KEEP_SECONDS`
- [app/studio/records.py](../../app/studio/records.py) — `DataGuard`, `_guard()`, `save()`
- [app/tools/data_history.py](../../app/tools/data_history.py) — `versions()`, `dailies()`, `restore()`
- [app/tools/sample_data.py](../../app/tools/sample_data.py) — `seed()`
- [app/tests/test_data_safety.py](../../app/tests/test_data_safety.py), [app/tests/test_sample_guard.py](../../app/tests/test_sample_guard.py), [app/tests/test_aside.py](../../app/tests/test_aside.py)

## Related
- [Data](data.md) · [Security](../security.md) · [Backup](../features/backup.md) · [Archive](../features/archive.md)
