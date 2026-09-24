---
title: Server routes
type: reference
updated: 2026-09-24
code:
  - app/studio/archive.py
  - app/studio/server.py
  - app/studio/settings_api.py
  - app/studio/orders.py
  - app/studio/library.py
  - app/studio/creator.py
  - app/studio/profit.py
  - app/studio/etsy.py
  - app/studio/printify.py
  - app/studio/gelato.py
  - app/studio/sendlog.py
  - app/studio/textcheck.py
  - app/studio/drops.py
  - app/studio/mockups.py
  - app/studio/workshop.py
---
# Server routes

> All the `@route` routes, one to one. The wiki-check script compares this table against the code: a
> new, changed, or removed route has to be reflected here.
> Access: `token` — a session header, `media` — `?t=` in the link, `none` — no token.
> Pattern — the regular expression from the code (the `|` character is escaped).

## App — [server.py](../../app/studio/server.py), [settings_api.py](../../app/studio/settings_api.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/ping` | none | `_ping` | lib.js ("connection lost" check), main.py (a second copy of the program) |
| POST | `/api/app/heartbeat` | token | `_heartbeat` | app.js every 20 s |
| POST | `/api/app/bye` | none | `_bye` | app.js when the window closes (token in the body) |
| GET | `/api/jobs/([0-9a-f]{12})` | token | `_job` | lib.js `runJob` (a job's error also carries `errorExtra` — e.g. a key's `code`) |
| GET | `/api/app` | token | `_app` | app.js `refreshInfo` |
| GET | `/api/settings` | token | `_settings` | settings.js |
| POST | `/api/settings/ui` | token | `_ui` | app.js (theme, animations) |
| POST | `/api/settings/etsy` | token | `_etsy_settings` | settings.js (the return address) |
| POST | `/api/secrets` | token | `_secret` | settings.js (save / delete a key) |
| POST | `/api/settings/legacy/import` | token | `_legacy_import` | settings.js (keys from the old programs) |
| POST | `/api/app/open-data` | token | `_open_data` | settings.js |
| POST | `/api/app/open-url` | token | `_open_url` | lib.js `openExternal` (Etsy is blocked, except for sign-in) |
| POST | `/api/app/pick-folder` | token | `_pick_folder` | book.js, library.js |

## Orders — [orders.py](../../app/studio/orders.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/orders` | token | `_list` | orders.js (the queue) |
| GET | `/api/orders/(\d{5,20})` | token | `_one` | orders.js (the card; `earlierSends` — sends of this order that never became a print-shop order) |
| POST | `/api/orders/(\d{5,20})/files` | token | `_files` | orders.js `arrange` (laying out pages; for Gelato — also whether it prints that many pages in this format) |

## Text check — [textcheck.py](../../app/studio/textcheck.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| POST | `/api/orders/(\d{5,20})/textcheck` | token | `_check` | orders.js `startCheck` (a background job; off in Settings → `{off: true}`) |
| POST | `/api/orders/(\d{5,20})/textcheck/cancel` | token | `_cancel` | orders.js `dropCheck` (the card closed, other files, another book; `{jobId}` — only this job's check) |
| GET | `/api/textcheck/status` | token | `_status` | settings.js `loadTextcheck` (enabled, model, whether Ollama answers) |
| POST | `/api/settings/textcheck` | token | `_save_settings` | settings.js (the switch, the model) |
| POST | `/api/textcheck/start` | token | `_start` | settings.js "Start" Ollama |
| POST | `/api/textcheck/warm` | token | `_warm` | orders.js `warmModel` (the card took files — the model loads onto the GPU ahead of time) |
| POST | `/api/textcheck/passport` | token | `_passport` | orders.js `learnPassport` (the cover's and spreads' texts into the book passport — only on the owner's click; with `preview` it only shows what they'd become, without saving anything) |

## Library — [library.py](../../app/studio/library.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/library/books` | token | `_list` | library.js, workshop.js (`?stage=workshop` — the Workshop's books; without it only the library's, never a Workshop book), workshop-book.js (the passing-on dialog's duplicate check) |
| POST | `/api/library/books` | token | `_create` | library.js `openAddBook` |
| GET | `/api/library/guide` | token | `_guide` | library.js `copyGuide` |
| POST | `/api/library/guide/save` | token | `_guide_save` | library.js `saveGuide` |
| GET | `/api/library/books/([0-9a-f]{32})` | token | `_get` | book.js, workshop-book.js |
| PATCH | `/api/library/books/([0-9a-f]{32})` | token | `_patch` | book.js (title, Canva, texts; checks `rev`), workshop-book.js (title, texts, `prompts` — only a book that has them) |
| DELETE | `/api/library/books/([0-9a-f]{32})` | token | `_delete` | book.js, workshop-book.js (moves it to trash) |
| POST | `/api/library/books/([0-9a-f]{32})/archive` | token | `_archive` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/refresh-listing` | token | `_refresh_listing` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/thumbnail-from-listing` | token | `_thumb_from_listing` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/assets` | token | `_upload_asset` | book.js (`?slot=&name=&auto=`, body — the file), workshop-book.js (one picture per frame) |
| DELETE | `/api/library/books/([0-9a-f]{32})/assets` | token | `_remove_asset` | book.js, workshop-book.js |
| POST | `/api/library/books/([0-9a-f]{32})/swap` | token | `_swap_halves` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/text` | token | `_import_text` | book.js |
| GET | `/api/library/books/([0-9a-f]{32})/text.json` | token | `_text_json` | book.js ("copy as JSON") |
| POST | `/api/library/books/([0-9a-f]{32})/folder-scan` | token | `_folder_scan` | book.js `importFolder` |
| POST | `/api/library/books/([0-9a-f]{32})/folder-import` | token | `_folder_import` | book.js `importFolder` (background job) |
| POST | `/api/library/books/([0-9a-f]{32})/export` | token | `_export` | book.js (background job) |
| POST | `/api/library/books/([0-9a-f]{32})/open-folder` | token | `_open_folder` | book.js, workshop-book.js |
| POST | `/api/library/books/([0-9a-f]{32})/open-original` | token | `_open_original` | lightbox.js via book.js and workshop-book.js |
| GET | `/media/book/([0-9a-f]{32})/([0-9a-f]{32}\.(?:png\|jpg\|jpeg\|webp))` | media | `_media` | library.js, book.js, orders.js, workshop.js, workshop-book.js (`?w=` — preview) |

## The Workshop — [workshop.py](../../app/studio/workshop.py)

The Listings mode's books in development ([features/workshop.md](../features/workshop.md)); their pictures,
title, texts and prompts go through the library's routes above.

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| POST | `/api/workshop/books` | token | `_create` | workshop.js `newBook` (`{title}` — no listing) |
| POST | `/api/workshop/books/([0-9a-f]{32})/json` | token | `_import` | workshop-book.js (`{json, dryRun}` — prompts and texts from one JSON; `dryRun` only counts what would be replaced) |
| GET | `/api/workshop/books/([0-9a-f]{32})/json` | token | `_export` | workshop-book.js ("copy the prompts and texts as JSON") |
| POST | `/api/workshop/books/([0-9a-f]{32})/to-library` | token | `_to_library` | library.js `openAddBook` in its passing-on form (`{listing}` checked, or `{listingRef}`; `useListingImage`; a listing another library book has → 409 with its `bookId`) |
| GET | `/api/workshop/guide` | token | `_guide` | workshop.js `copyGuide` (the agent's instruction for prompts and texts) |
| POST | `/api/workshop/guide/save` | token | `_guide_save` | workshop.js `saveGuide` |

## Order Creator and files — [creator.py](../../app/studio/creator.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/creator/status` | token | `_status` | creator.js |
| POST | `/api/creator/validate` | token | `_validate` | creator.js, orders.js (background job) |
| POST | `/api/creator/pick-file` | token | `_pick_file` | orders.js / creator.js `replacePage` (the native Windows dialog: a single picture from the computer) |
| POST | `/api/creator/replace-page` | token | `_replace_page` | orders.js / creator.js `replacePage` (a new page in place of one in the print folder) |
| POST | `/api/creator/restore-page` | token | `_restore_page` | orders.js / creator.js `restorePage` (undo the previous page) |
| POST | `/api/creator/pick-folder` | token | `_pick` | creator.js, orders.js |
| POST | `/api/creator/printify/create` | token | `_create_printify` | creator.js (background job) |
| POST | `/api/creator/printify/reprint` | token | `_reprint_printify` | creator.js `create` in reprint-from-archive mode (background job; a new order for the same book; from a send that never became an order — 409) |
| POST | `/api/creator/gelato/create` | token | `_create_gelato` | creator.js (background job; with `reprintOf` — a reprint draft from the archive's files, only from a book that really went to print) |
| GET | `/api/creator/gelato/page-counts` | token | `_gelato_page_counts` | creator.js `loadPageCounts` (how many pages Gelato prints in each format — from its catalog; `problems` — ready-made text for each length it doesn't print) |
| POST | `/api/creator/gelato/close-tunnel` | token | `_close_tunnel` | creator.js |
| GET | `/api/creator/etsy-orders` | token | `_etsy_orders` | creator.js `fromEtsy` |
| POST | `/api/creator/open-folder` | token | `_open_folder` | creator.js, book.js |
| GET | `/media/folder` | media | `_folder_media` | order-bits.js, creator.js, orders.js (`?path=&file=&w=`) |
| GET | `/media/folder-spread` | media | `_folder_spread` | order-bits.js `folderViewerItems` (`?path=&left=&right=&h=`) |

## Dropped files — [drops.py](../../app/studio/drops.py)

Every page that takes dropped files, the Mockups too (until 2026-09-23 — `/api/creator/drop/*` in creator.py).

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| POST | `/api/drop/file` | token | `_drop_file` | order-bits.js `receiveDrop` (`text=1` — also `.json` for the library) |
| POST | `/api/drop/zip` | token | `_drop_zip` | order-bits.js `receiveDrop` |
| POST | `/api/drop/done` | token | `_drop_done` | order-bits.js `receiveDrop` (`whole` — the dropped folder itself, for the library) |

## Listing mockups — [mockups.py](../../app/studio/mockups.py)

Book Studio's own since 2026-09-24 (until then only the separate utility's server, port 47831, served
them) — see [features/mockups.md](../features/mockups.md).

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/mockups/state` | token | `_state` | pages/mockups.js (templates found, Photoshop found, a run in progress, the last folder, a run whose templates wait for the front cover — `pending`) |
| POST | `/api/mockups/book` | token | `_open_book` | mockups.js `takeDrop` (a folder from `tmp/dropped` only → moved into `mockups/book/` → the book's pages and spreads; the book before it goes) |
| POST | `/api/mockups/pick-zip` | token | `_pick_zip` | mockups.js `pickZip` (the book field's folder button: the Windows dialog for a ZIP, from Downloads / the last ZIP's folder) |
| POST | `/api/mockups/open-zip` | token | `_open_zip` | mockups.js `pickZip` (`{path}` of a `.zip` → unpacked into `mockups/book/`, the ZIP itself only read → the book) |
| POST | `/api/mockups/place` | token | `_place` | mockups.js (the sliders window or the yellow line: where the templates / Photoshop are) |
| POST | `/api/mockups/pick-folder` | token | `_pick_out` | mockups.js `askFolder` (where to save; never the templates folder) |
| POST | `/api/mockups/make` | token | `_make` | mockups.js `make` (background job `mockups`; `{book, picks, folder}`; the job shares every template's progress) |
| POST | `/api/mockups/finish` | token | `_finish` | mockups.js «Зберегти відкриті й закрити» (`{run}` → background job `mockups`: the second script saves and closes the templates left open) |
| POST | `/api/mockups/cancel` | token | `_stop` | mockups.js (the × while it runs) |
| POST | `/api/mockups/open-folder` | token | `_open_folder` | mockups.js (the result's folder button) |
| POST | `/api/mockups/open-picture` | token | `_open_picture` | mockups.js, the viewer's "original" button (`{job, i}` — only a picture that job saved) |
| POST | `/api/mockups/attention` | token | `_attention` | mockups.js `tellDone` (a run ended while Book Studio's window was behind: the taskbar button flashes, Windows' sound) |
| GET | `/media/mockups/template/([a-zA-Z0-9]+)` | media | `_template_media` | mockups.js (`?w=` — a template's own preview, read from the PSD) |
| GET | `/media/mockups/out/([0-9a-f]{12})/([0-9]+)` | media | `_out_media` | mockups.js (`?w=` — a picture a job saved, by its number) |
| GET | `/media/mockups/([0-9a-f]{16})/(cover\|page\|spread)` | media | `_media` | mockups.js (`?n=&w=` / `?n=&h=` — a page, the cover, a spread glued together) |

## Accounting and sync — [profit.py](../../app/studio/profit.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| POST | `/api/profit/sync` | token | `_start_sync` | order-bits.js `syncOrders`, profit.js (joins a sync already running) |
| GET | `/api/profit/sync` | token | `_sync_state` | order-bits.js `runningSync` |
| GET | `/api/profit/data` | token | `_data` | profit.js |
| GET | `/api/profit/row` | token | `_row` | profit.js |
| GET | `/api/profit/candidates` | token | `_candidates` | profit.js |
| POST | `/api/profit/links` | token | `_set_link` | profit.js |
| DELETE | `/api/profit/links` | token | `_delete_link` | profit.js |
| POST | `/api/profit/state` | token | `_set_state` | profit.js |

## Etsy — [etsy.py](../../app/studio/etsy.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/etsy/status` | token | `_status` | settings.js (waiting for sign-in) |
| POST | `/api/etsy/oauth/start` | token | `_oauth_start` | settings.js `oauthFlow` |
| POST | `/api/etsy/oauth/complete` | token | `_oauth_complete` | settings.js (the address pasted from the Kyiv PC) |
| GET | `/etsy/callback` | none | `_oauth_callback` | the browser, after signing in to Etsy |
| POST | `/api/etsy/session/import` | token | `_session_import` | settings.js (the access link) |
| GET | `/api/etsy/session/export` | token | `_session_export` | settings.js |
| POST | `/api/etsy/disconnect` | token | `_disconnect` | settings.js |
| GET | `/api/etsy/listing` | token | `_listing` | library.js (checking a listing) |

## Printify and Gelato — [printify.py](../../app/studio/printify.py), [gelato.py](../../app/studio/gelato.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| POST | `/api/printify/test` | token | `_test` | settings.js |
| POST | `/api/printify/manual-approval` | token | `_manual_approval` | creator.js `confirmManualApproval` |
| GET | `/api/printify/shops` | token | `_shops` | settings.js `pickMaster` |
| GET | `/api/printify/products` | token | `_products` | settings.js `pickMaster` |
| POST | `/api/printify/master/analyze` | token | `_analyze` | settings.js `pickMaster` |
| POST | `/api/printify/master/save` | token | `_save_master` | settings.js `pickMaster` |
| POST | `/api/gelato/test` | token | `_test` | settings.js |

## Order archive — [archive.py](../../app/studio/archive.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/archive` | token | `_list` | archive.js (the list; only books whose print-shop order is confirmed and paid, plus "Keep") |
| GET | `/api/archive/(\d{8}-\d{6}-[0-9a-f]{6})` | token | `_one` | archive.js (a book's page; a hidden one — 404) |
| POST | `/api/archive/(\d{8}-\d{6}-[0-9a-f]{6})/keep` | token | `_keep` | archive.js "Keep" |
| POST | `/api/archive/(\d{8}-\d{6}-[0-9a-f]{6})/reuse` | token | `_reuse` | orders.js `takeEarlier` (a working copy of an earlier send's files in `tmp/dropped`) |

## Send journal — [sendlog.py](../../app/studio/sendlog.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| POST | `/api/sends/open` | token | `_open` | creator.js `sendLogButton` (highlights the record in Explorer, or opens the folder) |

## Related

- [Server](server.md) · [Security](../security.md) · [Code map](../code-map.md)
