---
title: Program data — the app/data folder
type: architecture
updated: 2026-11-12
code:
  - app/studio/core.py
  - app/studio/vault.py
  - app/studio/images.py
  - app/studio/records.py
  - app/studio/library.py
---
# Program data

> Everything the program remembers lives in `app/data/` (not in git). `BOOK_STUDIO_DATA` swaps in another folder (tests, preview). The whole program folder is backed up to Google Drive ([backup](../features/backup.md)); how a bad write is undone — [data safety](data-safety.md).

## What lives where

| Path in `app/data/` | What it is | Written by |
|---|---|---|
| `settings.json` | Non-secret settings: Etsy (shop, return address), Printify (shop, `readOnlyFrom`, Master), Gelato (formats, `pageCounts`, currency rates, `switchedAt`/`firstAccount` of the two accounts), `textcheck` (enabled, model, Ollama address — 127.0.0.1 only), `backup` (last copy or error), `workshop` (`saveDir`, `upscayl`), `ui` | `core.settings` |
| `vault.json` | Etsy/Printify/Gelato keys (also the old Gelato account's, `gelato_old_api_key`), Etsy tokens, the backup password; DPAPI-encrypted. **Never read or print** | `Vault` |
| `library/books/<id>/book.json` | The book model ([below](#the-book-model-bookjson)) | `library.save()` |
| `library/books/<id>/assets/<uuid>.png` | A book's illustrations (originals) | `library._store_asset()` |
| `library/trash/` | Deleted books (restorable with «Скасувати» or by hand) | `library._delete()` |
| `library/trash-assets/` | A picture removed from a book, kept with a note of where it was | `library.TRASH_ASSETS` |
| `profit/ledger.json` | Etsy payment ledger (slim entries in cents with the balance), `payments` (payment → receipt), `readTo`; re-read two days back at every sync | `ledger.refresh()` |
| `profit/snapshot.json` | Last sync: Etsy receipts, Printify and Gelato orders (slim; Gelato orders carry `account`, the hash of the key), the cursor, `loaded` (when each list last loaded in full; the archive trusts only a fresh one) | `sync._sync()` |
| `profit/links.json` | Manual links "receipt → print order" or "no cost" | `profit._set_link()` |
| `profit/states.json` | Manual states: cancellation, refund, replacement (reprints from the archive too) | `profit._set_state()`, `stages.mark_reprint()` |
| `profit/print-orders.json` | Which print orders this program created for which receipt (the **send journal**: add-only) | `records.remember_print_order()` |
| `creator/upload-cache.json` | File SHA-256 → Printify image id; the last `UPLOADS_KEPT` | `creator/printify_send.py` |
| `creator/master-snapshots/` | Snapshots of the Printify Master product before a book creation | `create_printify_draft()` |
| `cache/thumbs/` | JPEG previews keyed by path, mtime, size, preview size; unused for `CACHE_DAYS` go, over `CACHE_MAX_BYTES` the least recently used go first (checked on launch) | `images.preview()`, `images.prune_cache()` |
| `archive/<id>/` | [Order archive](../features/archive.md): `Cover.png` + printed pages and `entry.json`; deletes itself | `archive.store()` |
| `archive/pages.json` | Which archived pages are the same picture (kept once) | `archive.py` |
| `logs/` | Daily logs and `startup-error.txt` ([runtime](runtime.md#logs)); `sends/` — one JSON per send to a printer (last 400; with addresses, no keys); `checks/` — one JSON per text check (last 400; with children's names) | logging, [order creator](../features/order-creator.md), [text check](../features/text-check.md) |
| `history/`, `aside/` | Versions of important files; the «Скасувати» shelf — [data safety](data-safety.md) | `core.keep_history()`, `aside.put()` |
| `tmp/system/` | Temp of the program and everything it starts ([runtime](runtime.md#temp-folder)) | `core.own_temp()` |
| `tmp/dropped/`, `tmp/gelato/<session>/`, `tmp/modules/`, `tmp/photoshop/`, `tmp/slides-browser/` | Dragged copies ([intake](../flows/intake.md)); PDFs while Gelato's temporary link is up; module downloads (`.part`); Photoshop temp; the slide baker's browser profile | `drops`, `gelato_send`, `modules`, `mockups` |
| `mockups/` | [Mockups](../features/mockups.md) files: `book/<id>/` (the demo book), `places.json` (template/Photoshop places, last output and ZIP folders), `work/<time>-<id>/` (one run) | `mockups.py` |
| `slides/` | [Listing slides](../features/slides.md): `schemes/<key>/`, `sets/<time>-<id>/` (outside a Workshop book), `cuts/<key>/` | `slides` package |
| `window-profile/`, `work-browser/` | Edge profiles: the app window; the portable copy's Gelato/Canva logins (left out of backup) | Edge |
| `media-key.txt` | The `/media/` picture key ([server](server.md)) | `server._media_key()` |
| `portable-state.json`, `rebase-backup/`, `import-backup/` | The portable copy's notes (computers, rebased paths); data files before a folder move / a settings import | [portable.py](../../app/studio/portable.py) |
| `workshop-books/`, `downloads/`, `clipboard/`, `recycle-bin/`, `saved/` | Sandbox stand-ins for the Workshop (preview and tests only) | `core.SANDBOX` |

`DATA_DIR` is `BOOK_STUDIO_DATA` or `app/data`.

## Outside `app/data`: the Workshop's books

The [Workshop](../features/workshop.md)'s books are folders `pipeline/books/<n>.<slug>/` (`core.WORKSHOP_BOOKS`), written by the `book` skills; not in git. A Workshop book's own `book.json` is the Workshop's state, not the library model. In the sandbox they are made-up books in `data/workshop-books/`.

## File writing

- All writes go through `core.write_json()`: atomic (temp file → fsync → replace) with a `.bak` copy of the previous version. If the copy fails, the write still goes through with a warning in the log. `core.replace_file()` retries the move over a file Windows may hold for a moment (antivirus, a viewer); the Workshop's pictures use it too.
- `core.read_json()` reads the `.bak` only in place of a **damaged** file; a **missing** file stays missing.
- `SAMPLE` (`BOOK_STUDIO_SAMPLE=1`, set by `tools/dev_server.py`): made-up data and `Vault.set()` refuses.
- The preview cache is keyed to a file's full path: after a folder move previews are rebuilt once.
- The Order Creator remembers nothing between visits; work on a new order is kept in page memory only ([frontend](frontend.md)).

## The book model (`book.json`)

```json
{ "id": "<32 hex>", "schema": 1, "rev": 3, "title": "…", "createdAt": "…", "updatedAt": "…",
  "listing": {"id", "title", "state", "shopId", "url", "imageUrl", "verifiedAt"},
  "canvaUrl": "", "archived": false, "archivedAt": null,
  "cover": <asset|null>, "thumbnail": <asset|null>,
  "slots": { "page1": {"image"}, "spread2": {"image", "left", "right"}, …, "page30": {"image"} },
  "text":  { "cover", "page1", "spread2" … "spread15", "page30" },
  "workshop": "41.slug", "pagesFrom": "workshop" }
```
- `workshop` exists only on a book passed on from the Workshop: the folder in `pipeline/books/`.
- Asset: `{id, file, originalName, width, height, bytes, addedAt, lqip}`. `rev` guards two windows editing one book (a `PATCH` with a stale `rev` → 409).
- `pagesFrom: "workshop"`: the cover and pages are the Workshop book's files (`WORKSHOP_PAGES`); the assets carry `workshop` (file name in `pictures/`) and `stamp` (mtime and size). Only the thumbnail is stored in the library. How it follows the Workshop and what happens on deletion — [library](../features/library.md).
- Write order: `book.json` is saved first, only then is an old picture deleted, so a failed write never costs a file.

## Why
- `.bak` is never read for a deleted file, so a deletion is not undone by accident.
- The Order Creator keeps nothing between visits: no stale state.

## Where in the code
- [app/studio/core.py](../../app/studio/core.py) — `DATA_DIR`, `data_path()`, `ensure_dirs()`, `write_json()`, `read_json()`, `replace_file()`, `WORKSHOP_BOOKS`
- [app/studio/vault.py](../../app/studio/vault.py) — `Vault`, `SECRET_NAMES`
- [app/studio/images.py](../../app/studio/images.py) — `preview()`, `prune_cache()`, `CACHE_DAYS`, `CACHE_MAX_BYTES`
- [app/studio/library.py](../../app/studio/library.py) — `BOOKS_DIR`, `TRASH_DIR`, `WORKSHOP_PAGES`, `save()`
- [app/studio/records.py](../../app/studio/records.py) — `SNAPSHOT`, `LINKS`, `STATES`, `SENDS`, `remember_print_order()`
- [app/studio/creator/printify_send.py](../../app/studio/creator/printify_send.py) — `UPLOAD_CACHE`, `UPLOADS_KEPT`

## Related
- [Data safety](data-safety.md) · [Server](server.md) · [Runtime](runtime.md) · [Library](../features/library.md) · [Security](../security.md)
