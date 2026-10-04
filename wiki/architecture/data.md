---
title: Program data — the app/data folder
type: architecture
updated: 2026-10-03
code:
  - app/studio/core.py
  - app/studio/vault.py
  - app/studio/images.py
  - app/studio/records.py
---
# Program data

> Everything the program remembers lives in `app/data/` (gigabytes: the order archive and the library are
> the biggest parts, then the preview cache; not in git). Every 3 days the program backs it up to
> Google Drive itself, with the whole program folder ([backup](../features/backup.md)). The `BOOK_STUDIO_DATA` environment variable swaps in a different folder (tests, preview).

## What lives where

| Path in `app/data/` | What it is | Who writes it |
|---|---|---|
| `settings.json` (+`.bak`) | Non-secret settings: theme, Etsy (shop, return address), Printify (shop, Master, sizes, `manualApprovalConfirmedAt`), Gelato (formats, the EUR→USD rate, `pageCounts` 28 and 30; after the move to his own account — `switchedAt` and `firstAccount`, the account id of orders kept from before they carried theirs), `textcheck` (enabled, model, Ollama address — 127.0.0.1 only), `backup` (the last copy or error) | `core.settings` |
| `vault.json` (+`.bak`) | Etsy/Printify/Gelato keys (after the move to his own Gelato account also the old account's, `gelato_old_api_key`, until he removes it), Etsy tokens, the backup's password (`backup_password`), DPAPI-encrypted. **Never read or print** | `Vault` |
| `library/books/<id>/book.json` | The book model ([features/library.md](../features/library.md)); a book passed on from the [Workshop](../features/workshop.md) notes it (`"workshop": "<folder>"`) | `library.save()` |
| `library/books/<id>/assets/<uuid>.png` | The book's illustrations (originals); a book passed on from the Workshop keeps its cover and pages in the Workshop's `pipeline/books/<folder>/pictures/` instead (`"pagesFrom": "workshop"`, since 2026-09-27) — only its thumbnail is here | `library._store_asset()` |
| `library/trash/` | Deleted books (can be restored by hand) | `library._delete()` |
| `profit/snapshot.json` | A snapshot of the last sync: Etsy receipts, Printify and Gelato orders (slim; each Gelato order with `account` — the hash of the key it was read with), the sync cursor, `loaded` — when each of the three lists last loaded in full (the archive only trusts a fresh one). Read from disk once per file change (`load_snapshot()`) | `profit._sync()` |
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
| `work-browser/` | The portable copy's Edge profile for Gelato and Canva (the logins; left out of the backup) | Edge |
| `portable-state.json` | The portable copy's own notes: the computers it has run on, `repo` (where its paths were last rebased), the «no» answers to the system installs | [portable.py](../../app/studio/portable.py) |
| `rebase-backup/`, `import-backup/` | The data files as they were before a move of the folder / before a settings import | `portable.rebase_paths()`, `transfer._save_current()` |
| `tmp/modules/` | The module downloads while they are made (`.part`, then checked) | [modules.py](../../app/studio/modules.py) |
| `mockups/` | **The [Mockups](../features/mockups.md)' files** (the separate utility's data folder 2026-09-23…24, now Book Studio's `data_path("mockups", …)`): `book/<id>/` (the unpacked demo book, `BOOKS` — one at a time, apart from the orders' `tmp/dropped/`, gone on launch and close), `places.json` (where the templates / Photoshop are when not in the usual place, the last output folder `lastOut`, the last ZIP's folder `lastZip`), `work/<time>-<id>/` — one run: `templates/` (copies of the six templates; the three left open in Photoshop stay, the rest go right after the run), `pictures/` (gone right after the script), `mockups.jsx`, `job.json`, `status.json`, `finish.jsx`, `finish.json`, `finish-status.json`. A run folder goes after «Зберегти відкриті», at once when Photoshop is closed, else after a day (a copy the owner saved himself — a week). Left from the separate utility: `logs/` (its log; Book Studio's own is `logs/app.log` above); its `tmp/`, `cache/`, `window-profile/` went on the first launch after the move (that cleaning was removed on 2026-09-27, when nothing of them was left). A Photoshop started from here keeps its temp files in `tmp/photoshop/` (emptied once Photoshop is closed) | [mockups](../features/mockups.md) |
| `slides/` | **The [listing slides](../features/slides.md)** (since 2026-09-29): `schemes/<key>/` — the schemes (Nature — the default, Night, the owner's own: `scheme.json` + six scenes; `design/` — the old template, became Nature); a Workshop book's slides live in its own folder (`pipeline/books/<n>.<slug>/mockups/slides/`); `sets/<time>-<id>/` — slides made before that (`set.json`, `scenes/`, `books/` the cut-out books and their shadows, `pictures/`), the last 12 kept; `cuts/<key>/` — every mockup cut once (the book, its shadow, `info.json`) — gone at launch and close. The browser that bakes keeps its profile in `tmp/slides-browser/` and a picture in `tmp/slides/` only while it draws | [slides](../features/slides.md) |

## Outside `app/data`: the Workshop's books

The [Workshop](../features/workshop.md)'s books are the book pipeline's folders, **`pipeline/books/<n>.<slug>/`**
(since 2026-09-26; `core.WORKSHOP_BOOKS`), next to the agents' rules — the agents in Antigravity write there, so the
folder has to be inside the one Antigravity opens. Not in git (`.gitignore`): every book's pictures, the originals and
`.replaced/`. A book's own `book.json` is the Workshop's state (not the library's model). In the sandbox (the preview,
the tests) the books are made-up ones in the data folder's `workshop-books/`, and so are its `downloads/`,
`clipboard/`, `recycle-bin/` and `saved/`. `settings.json` keeps `workshop.saveDir` — where «Зберегти як…» last saved
— and `workshop.upscayl` — where the owner's Upscayl engine was found (`upscale.engine()`). A book's `book.json` notes
each row's upscaling (`rows.<key>.upscaled`) and `"upscale": false` when the book is left without it.

## Rules

- Writes only go through `core.write_json()` (atomic, with a `.bak` copy). `.bak` is only read in place
  of a **damaged** file, not a deleted one (`read_json()`).
- `SAMPLE` (`BOOK_STUDIO_SAMPLE=1`, set by `app/tools/dev_server.py`): made-up data, no key gets saved
  (`Vault.set()` refuses).
- The preview cache is keyed to a file's full path: after moving the data folder, previews are rebuilt
  once (the old cache files just sit there unused).
- The Order Creator remembers nothing between visits (the owner's decision). What older versions kept
  (`settings.creator`, `creator/history.json`) was cleared on launch until 2026-09-27; the owner's PC had nothing
  left, so that cleaning is gone.
- The test folder is created in the system temp directory and deleted after the tests.

## Where in the code

- [app/studio/core.py](../../app/studio/core.py) — `DATA_DIR`, `SAMPLE`, `data_path()`, `ensure_dirs()`, `write_json()`, `read_json()`, `Settings`
- [app/studio/vault.py](../../app/studio/vault.py) — `Vault`, `SECRET_NAMES`, `readable()`
- [app/studio/images.py](../../app/studio/images.py) — `preview()`, `_cached()`
- [app/studio/library.py](../../app/studio/library.py) — `BOOKS_DIR`, `TRASH_DIR`
- [app/studio/records.py](../../app/studio/records.py) — `SNAPSHOT`, `LINKS`, `STATES`, `SENDS`, `load_snapshot()`, `remember_print_order()`
- [app/studio/creator/printify_send.py](../../app/studio/creator/printify_send.py) — `UPLOAD_CACHE`, `UPLOADS_KEPT`
- [app/studio/drops.py](../../app/studio/drops.py) — `DROPS`, `clear_drops()`
- [app/studio/mockups.py](../../app/studio/mockups.py) — `PLACES`, `WORK`, `BOOKS`, `PHOTOSHOP_TEMP`, `KEEP_RUNS`, `clean_runs()`, `clear_books()`
- [app/studio/core.py](../../app/studio/core.py) — `PIPELINE_DIR`, `WORKSHOP_BOOKS`, `SANDBOX`
- [app/studio/archive.py](../../app/studio/archive.py) — `ROOT`, `store()`, `refresh()`
- [app/tests/__init__.py](../../app/tests/__init__.py) — `BOOK_STUDIO_DATA` for tests

## Related

- [Server](server.md) · [Security](../security.md) · [Library](../features/library.md)
