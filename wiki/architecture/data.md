---
title: Program data — the app/data folder
type: architecture
updated: 2026-09-23
code:
  - app/studio/core.py
  - app/studio/vault.py
  - app/studio/images.py
---
# Program data

> Everything the program remembers lives in `app/data/` (≈6.6 GB as of 2026-09-22: the order archive
> 4.0 GB, the library 1.6 GB, the preview cache 364 MB; not in git). For a backup it's enough to copy
> this folder. The `BOOK_STUDIO_DATA` environment variable swaps in a different folder (tests, preview).

## What lives where

| Path in `app/data/` | What it is | Who writes it |
|---|---|---|
| `settings.json` (+`.bak`) | Non-secret settings: theme, Etsy (shop, return address), Printify (shop, Master, sizes, `manualApprovalConfirmedAt`), Gelato (formats, the EUR→USD rate, `pageCounts` 28 and 30; on launch `_upgrade()` removes the old `pageCount` and switches Gelato's "inch" products to metric), `textcheck` (enabled, model, Ollama address — 127.0.0.1 only) | `core.settings` |
| `vault.json` (+`.bak`) | Etsy/Printify/Gelato keys, Etsy tokens, and a Gemini key (`gemini_api_key`, for a planned text check — not used yet), DPAPI-encrypted. **Never read or print** | `Vault` |
| `library/books/<id>/book.json` | The book model ([features/library.md](../features/library.md)) | `library.save()` |
| `library/books/<id>/assets/<uuid>.png` | The book's illustrations (originals) | `library._store_asset()` |
| `library/trash/` | Deleted books (can be restored by hand) | `library._delete()` |
| `profit/snapshot.json` | A snapshot of the last sync: Etsy receipts, Printify and Gelato orders (slim), the sync cursor, `loaded` — when each of the three lists last loaded in full (the archive only trusts a fresh one). Read from disk once per file change (`load_snapshot()`) | `profit._sync()` |
| `profit/links.json` | Manual links: "receipt → print order" or "no cost" | `profit._set_link()` |
| `profit/states.json` | Manual states: cancellation, refund, replacement (reprints from the order archive go here too) | `profit._set_state()`, `profit.mark_reprint()` |
| `profit/print-orders.json` | Which print orders this program itself created for which receipt (a receipt's books can go in two batches, or to two printers) | `profit.remember_print_order()` |
| `creator/upload-cache.json` | A file's SHA-256 → its Printify image ID (so it isn't uploaded twice); keeps the last 5000 (`UPLOADS_KEPT`), older ones are forgotten | `creator._remember_upload()` |
| `creator/master-snapshots/` | Snapshots of the Master product before every book creation | `create_printify_draft()` |
| `cache/thumbs/` | JPEG previews (keyed by path, modified time, size, preview size); unneeded after 21 days — deleted on launch (since 2026-09-19; a preview used while working refreshes its date once a day) | `images.preview()`, `images.prune_cache()` |
| `tmp/dropped/` | Copies of dragged folders and ZIPs; wiped on launch | `drops._drop_file()` |
| `tmp/gelato/<session>/` | PDFs for Gelato while the temporary link is up | `create_gelato_draft()` |
| `tmp/system/` | The temp folder of the program and everything it starts (the Edge window, the Windows dialogs, cloudflared) instead of Windows' `%TEMP%` on drive C (since 2026-09-23, the owner keeps C clean); emptied on launch and on close | `core.own_temp()`, `core.clear_own_temp()` |
| `logs/` | `app.log`, `printify.log`, `gelato.log`, `startup-error.txt` | logs |
| `logs/sends/` | One JSON per send to Printify/Gelato (last 400; with addresses, no keys) | [send journal](../features/send-journal.md) |
| `logs/checks/` | One JSON per text check: what the model read, what should have been there, problems (last 400; with children's names) | [text check](../features/text-check.md) |
| `archive/<id>/` | Order archive: `Cover.png` + the pages that went to print, and `entry.json` (what, where, when, address). **Deletes itself** 14 days after "Sent" (30 if the order can't be tracked), except "Keep" | [order archive](../features/archive.md) |
| `window-profile/` | The Edge window profile (≈0.5 GB) | Edge |
| `mockups/` | **The mockups utility's own data folder** (its `DATA_DIR`, since 2026-09-23): `logs/`, `window-profile/`, `tmp/dropped/` (the demo book — one at a time, gone on close), `tmp/system/`, `tmp/photoshop/` (the temp folder of a Photoshop started from here — emptied once Photoshop is closed), `cache/thumbs/` (also the templates' previews and the saved pictures'), `places.json` (where the templates / Photoshop are when not in the usual place, the last output folder `lastOut`, the last ZIP's folder `lastZip`), `work/<time>-<id>/` — one run: `templates/` (copies of the six templates; the three left open in Photoshop stay, the rest go right after the run), `pictures/` (gone right after the script), `mockups.jsx`, `job.json`, `status.json`, `finish.jsx`, `finish.json`, `finish-status.json`. A run folder goes after «Зберегти відкриті», at once when Photoshop is closed, else after a day (a copy the owner saved himself — a week). Nothing of Book Studio's (no keys, orders or library) | [mockups](../features/mockups.md) |

## Rules

- Writes only go through `core.write_json()` (atomic, with a `.bak` copy). `.bak` is only read in place
  of a **damaged** file, not a deleted one (`read_json()`).
- `SAMPLE` (`BOOK_STUDIO_SAMPLE=1`, set by `app/tools/dev_server.py`): made-up data, no key gets saved
  (`Vault.set()` refuses).
- The preview cache is keyed to a file's full path: after moving the data folder, previews are rebuilt
  once (the old cache files just sit there unused).
- The Order Creator remembers nothing between visits (the owner's decision): `forget_old_form()` clears
  leftovers from older versions (`settings.creator`, `creator/history.json`).
- The test folder is created in the system temp directory and deleted after the tests.

## Where in the code

- [app/studio/core.py](../../app/studio/core.py) — `DATA_DIR`, `SAMPLE`, `data_path()`, `ensure_dirs()`, `write_json()`, `read_json()`, `Settings`
- [app/studio/vault.py](../../app/studio/vault.py) — `Vault`, `SECRET_NAMES`
- [app/studio/images.py](../../app/studio/images.py) — `preview()`, `_cached()`
- [app/studio/library.py](../../app/studio/library.py) — `BOOKS_DIR`, `TRASH_DIR`
- [app/studio/profit.py](../../app/studio/profit.py) — `SNAPSHOT`, `LINKS`, `STATES`, `SENDS`, `load_snapshot()`, `remember_print_order()`
- [app/studio/creator.py](../../app/studio/creator.py) — `UPLOAD_CACHE`, `UPLOADS_KEPT`, `forget_old_form()`
- [app/studio/drops.py](../../app/studio/drops.py) — `DROPS`, `clear_drops()`
- [app/studio/mockups.py](../../app/studio/mockups.py) — `PLACES`, `WORK`, `KEEP_RUNS`, `clean_runs()`
- [app/studio/archive.py](../../app/studio/archive.py) — `ROOT`, `store()`, `refresh()`
- [app/tests/__init__.py](../../app/tests/__init__.py) — `BOOK_STUDIO_DATA` for tests

## Related

- [Server](server.md) · [Security](../security.md) · [Library](../features/library.md)
