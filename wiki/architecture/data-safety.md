---
title: Data safety — how the owner's data is kept from being lost
type: architecture
updated: 2026-10-04
code:
  - app/studio/core.py
  - app/studio/records.py
  - app/tools/data_history.py
  - app/tests/test_data_safety.py
  - app/tests/test_sample_guard.py
---
# Data safety

> Born from one accident (2026-10-04): a made-up data set overwrote the real send journal and the shops' snapshot, and only a lucky `.bak`
> brought them back. Now several independent layers make a bad write undoable — whoever makes it (the program, a script, an agent).

## The layers

1. **History of every write** (`core.keep_history()`, called by `write_json()`): before a write replaces an important file, the file as it is
   goes to `app/data/history/<its path>/<time>.json` — the last 20 versions, never the same twice, no more often than the file's rule
   (`HISTORY_RULES`: the send journal, links and states at every change; the settings and the keys' store 5 min; a library book 1 min; an archive entry
   every change; the shops' snapshot hourly). The `.bak` stays (the last version only).
2. **A daily snapshot** (`core.daily_snapshot()`, a thread at the start): every file of those rules — and the Workshop books' `book.json` — into
   `history/daily/<date>/`, the last 14 days. Not in the preview or the tests.
3. **Guards on what costs most** (`records._guard()` via `records.save()`): the send journal (`print-orders.json`) is only ever added to — a
   write that would drop a receipt is refused (`DataGuard`), because losing a send lets the order be sent twice; the shops' snapshot may not shrink
   below half of what it holds.
4. **Tests and the preview cannot reach the real data**: `studio.core` refuses to load under `unittest` without `BOOK_STUDIO_DATA` (the tests set it);
   `tools/sample_data.seed()` refuses unless `studio.core` points at the made-up folder.
5. **Deleted only to the Recycle Bin**: what the owner made — a Workshop book, a library book, a photo template, a slide set — goes through
   `desktop.to_recycle_bin()` (warns instead of deleting for good when Windows cannot recycle). What is deleted for good is derived or temporary
   (caches, previews, runs, the opened keys of an import), the archive after its 14 days (the owner's decision) and a module's own folder.
6. **Putting a version back**: `python app/tools/data_history.py list` / `restore <path> [--version V | --daily DATE]`. A restore first keeps the
   file it replaces as a version of its own.

## Rules for an agent working on this data

- Before **any script** that writes into `app/data` or `pipeline/books`: take a copy of what it will touch (a folder in `app/data/merge-backup/`), and run it
  on a copy first when it can be.
- Never import `studio` in a scratch script without setting `BOOK_STUDIO_DATA` (and `BOOK_STUDIO_SAMPLE=1` for made-up data) **before** the first import:
  `studio.core` fixes the folder at import.
- Start the preview only with `tools/dev_server.py`; never wrap it.
- A wrong write is undone from the history (`data_history.py`), not by guessing: look at `list`, then `restore`.

## Where in the code

- [app/studio/core.py](../../app/studio/core.py) — `HISTORY_RULES`, `keep_history()`, `daily_snapshot()`, `write_json()`, the `unittest` guard on `DATA_DIR`
- [app/studio/records.py](../../app/studio/records.py) — `DataGuard`, `_guard()`, `save()`
- [app/tools/data_history.py](../../app/tools/data_history.py) — `versions()`, `dailies()`, `restore()`
- [app/tests/test_data_safety.py](../../app/tests/test_data_safety.py), [app/tests/test_sample_guard.py](../../app/tests/test_sample_guard.py)

## Related

- [Data folder](data.md) — what lives where · [Security](../security.md) — the owner's hard rules · [Backup](../features/backup.md) — the copy on Google Drive
