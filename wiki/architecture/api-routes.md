---
title: Server routes
type: reference
updated: 2026-10-06
code:
  - app/studio/gelato_accounts.py
  - app/studio/archive.py
  - app/studio/server.py
  - app/studio/settings_api.py
  - app/studio/orders.py
  - app/studio/library.py
  - app/studio/creator/
  - app/studio/profit.py
  - app/studio/etsy.py
  - app/studio/printify.py
  - app/studio/gelato.py
  - app/studio/sendlog.py
  - app/studio/textcheck/
  - app/studio/drops.py
  - app/studio/mockups.py
  - app/studio/slides/routes.py
  - app/studio/workshop/routes.py
---
# Server routes

> All the `@route` routes, one to one. The wiki-check script compares this table against the code: a
> new, changed, or removed route has to be reflected here.
> Access: `token` — a session header, `media` — `?t=` in the link (the pictures' key, kept across launches, or the session token), `none` — no token.
> Pattern — the regular expression from the code (the `|` character is escaped).

## App — [server.py](../../app/studio/server.py), [settings_api.py](../../app/studio/settings_api.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/ping` | none | `_ping` | lib.js ("connection lost" check), main.py (a second copy of the program) |
| POST | `/api/app/heartbeat` | token | `_heartbeat` | app.js every 20 s |
| POST | `/api/app/bye` | none | `_bye` | app.js when the window closes (token in the body) |
| POST | `/api/app/log` | token | `_page_log` | app.js — an error nobody caught in the page, into `app.log` (at most 100 a launch) |
| GET | `/api/jobs/([0-9a-f]{12})` | token | `_job` | lib.js `runJob` (a job's error also carries `errorExtra` — e.g. a key's `code`) |
| GET | `/api/app` | token | `_app` | app.js `refreshInfo` |
| GET | `/api/settings` | token | `_settings` | settings.js |
| POST | `/api/settings/ui` | token | `_ui` | app.js (theme, animations) |
| POST | `/api/settings/etsy` | token | `_etsy_settings` | settings.js (the return address) |
| POST | `/api/secrets` | token | `_secret` | settings.js (save / delete a key) |
| POST | `/api/settings/legacy/import` | token | `_legacy_import` | settings.js (keys from the old programs) |
| POST | `/api/app/open-data` | token | `_open_data` | settings.js |
| POST | `/api/app/open-url` | token | `_open_url` | lib.js `openExternal` (Etsy is blocked, except for sign-in; Gelato and Canva open in the browser profile from settings, `_open_in_profile()`) |
| POST | `/api/app/pick-folder` | token | `_pick_folder` | book.js, library.js |

## Backup — [backup.py](../../app/studio/backup.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/backup` | token | `_status` | settings.js (password set, the Drive folder, the last copy or error, a running job) |
| POST | `/api/backup/password` | token | `_password` | settings.js (the archive's password into the vault) |
| POST | `/api/backup/run` | token | `_run_now` | settings.js «Зробити копію зараз» (a background job) |
| POST | `/api/backup/open` | token | `_open` | settings.js (the copies' folder in Explorer) |
| POST | `/api/transfer/export` | token | `_export` | settings.js «Експорт у файл» (save dialog, then the settings and keys in one 7-Zip) |
| GET | `/api/modules` | token | `_list` | settings.js, modules-ui.js (the optional modules and whether each is installed) |
| POST | `/api/modules/(\w+)/install` | token | `_install` | modules-ui.js (a background job: download, check, unpack, the model) |
| POST | `/api/modules/(\w+)/install-from-file` | token | `_install_from_file` | settings.js «з файлу» (a ZIP picked in the Windows dialog) |
| POST | `/api/modules/(\w+)/remove` | token | `_remove` | settings.js (the module's folder under `runtime/`) |
| POST | `/api/transfer/import` | token | `_import` | settings.js «Імпорт із файлу» (open dialog; body `password`) |

## Orders — [orders.py](../../app/studio/orders.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/orders` | token | `_list` | orders.js (the queue), creator-picker.js `pickEtsyOrder` (the same list; its own `/api/creator/etsy-orders` went on 2026-09-27) |
| GET | `/api/orders/(\d{5,20})` | token | `_one` | orders.js (the card; `earlierSends` — sends of this order that never became a print-shop order) |
| GET | `/api/orders/(\d{5,20})/history` | token | `_history` | order-history.js `mountHistory` (the card's history of a placed Gelato order, read from Gelato when the card opens; `?fresh=1` asks again) |
| POST | `/api/orders/(\d{5,20})/files` | token | `_files` | orders.js `arrange` (laying out pages; for Gelato — also whether it prints that many pages in this format; `provider: "files"` — a hardcover, the length picks the printer) |

## Text check — [textcheck/routes.py](../../app/studio/textcheck/routes.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| POST | `/api/orders/(\d{5,20})/textcheck` | token | `_check` | orders.js `startCheck` (a background job; off in Settings → `{off: true}`) |
| POST | `/api/orders/(\d{5,20})/textcheck/cancel` | token | `_cancel` | orders.js `dropCheck` (the card closed, other files, another book; `{jobId}` — only this job's check) |
| GET | `/api/textcheck/status` | token | `_status` | settings.js `loadTextcheck` (enabled, model, whether Ollama answers) |
| POST | `/api/settings/textcheck` | token | `_save_settings` | settings.js (the switch, the model) |
| POST | `/api/textcheck/start` | token | `_start` | settings.js "Start" Ollama |
| POST | `/api/textcheck/warm` | token | `_warm` | orders.js `warmModel` (the card took files — the model loads onto the GPU ahead of time) |
| POST | `/api/textcheck/mark` | token | `_mark` | orders.js `keepMark` (the owner's "Not an error" into that check's journal, `{journal, id}` → `{kept}`; for the next calibration) |
| POST | `/api/textcheck/passport` | token | `_passport` | orders.js `learnPassport` (the cover's and spreads' texts into the book passport — only on the owner's click; with `preview` it only shows what they'd become, without saving anything) |

## Library — [library.py](../../app/studio/library.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/library/books` | token | `_list` | library.js, workshop-book.js (the passing-on dialog's duplicate check) |
| POST | `/api/library/books` | token | `_create` | add-book.js `openAddBook` |
| GET | `/api/library/guide` | token | `_guide` | library.js `copyGuide` |
| POST | `/api/library/guide/save` | token | `_guide_save` | library.js `saveGuide` |
| GET | `/api/library/books/([0-9a-f]{32})` | token | `_get` | book.js |
| PATCH | `/api/library/books/([0-9a-f]{32})` | token | `_patch` | book.js (title, Canva, texts; checks `rev`) |
| DELETE | `/api/library/books/([0-9a-f]{32})` | token | `_delete` | book.js (moves it to trash; answers `trashName`) |
| POST | `/api/library/trash/restore` | token | `_restore` | book.js «Скасувати» (`{name}` — the trash folder goes back to its own place, never over a book that is there) |
| POST | `/api/library/books/([0-9a-f]{32})/archive` | token | `_archive` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/refresh-listing` | token | `_refresh_listing` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/thumbnail-from-listing` | token | `_thumb_from_listing` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/assets` | token | `_upload_asset` | book.js (`?slot=&name=&auto=`, body — the file) |
| DELETE | `/api/library/books/([0-9a-f]{32})/assets` | token | `_remove_asset` | book.js (the file is set aside in `data/library/trash-assets/<book>/` with a note of its slot; answers `trashAsset`) |
| POST | `/api/library/books/([0-9a-f]{32})/assets/restore` | token | `_restore_asset` | book.js «Скасувати» (`{name}` — back into its own slot, only if that slot is empty now) |
| POST | `/api/library/books/([0-9a-f]{32})/swap` | token | `_swap_halves` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/text` | token | `_import_text` | book.js |
| GET | `/api/library/books/([0-9a-f]{32})/text.json` | token | `_text_json` | book.js ("copy as JSON") |
| POST | `/api/library/books/([0-9a-f]{32})/folder-scan` | token | `_folder_scan` | book.js `importFolder` |
| POST | `/api/library/books/([0-9a-f]{32})/folder-import` | token | `_folder_import` | book.js `importFolder` (background job) |
| POST | `/api/library/books/([0-9a-f]{32})/export` | token | `_export` | book.js (background job) |
| POST | `/api/library/books/([0-9a-f]{32})/open-folder` | token | `_open_folder` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/open-original` | token | `_open_original` | lightbox.js via book.js |
| GET | `/media/book/([0-9a-f]{32})/([0-9a-f]{32}\.(?:png\|jpg\|jpeg\|webp))` | media | `_media` | library.js, book.js, orders.js (`?w=` — preview) |

## The Workshop — [workshop/routes.py](../../app/studio/workshop/routes.py)

The books in development (the Workshop) — the book pipeline's folders ([features/workshop.md](../features/workshop.md));
`<book>` is a book's folder name (`41.some-book`). The page asks `sig` every 1.5 s and redraws on a change.

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/workshop/books` | token | `_list` | workshop.js (the gallery: `{books, folder, sig, gen}`) |
| GET | `/api/workshop/sig` | token | `_sig` | workshop-live.js (`?book=` — one book's files only; `{sig, gen}` — what changed, the generation mode's state) |
| GET | `/api/workshop/books/([^/]+)` | token | `_get` | workshop-book.js (`{book, sig, gen}` — the strip, the rows, the cover, the variants, the check, every picture's version, `book.upscale` — the switch, the queue, the picture in work, what failed, what's left; `book.leftBehind` — the pictures put into `originals/` by hand, not cut yet, by variant) |
| DELETE | `/api/workshop/books/([^/]+)` | token | `_delete` | workshop-book.js «Видалити книгу» (the folder onto the shelf, then the Recycle Bin, `undo` for «Скасувати»; a wait for its picture stops) |
| GET | `/api/workshop/books/([^/]+)/file` | token | `_file` | workshop-book.js (`?name=` — one of the agent's text files, for the step's panel) |
| POST | `/api/workshop/books/([^/]+)/mark` | token | `_mark` | workshop-book.js (`{step, on}` — Canva, the mockups, the photo mockups with a category skipped) |
| POST | `/api/workshop/open` | token | `_open` | workshop.js, workshop-book.js, lightbox.js (`{book, what: books\|folder\|pictures\|originals\|mockups\|etsy\|agent, name, variant}` — Explorer, or one file in its program; `variant` — a hero variant's picture) |
| POST | `/api/workshop/agent` | token | `_agent` | workshop.js «+», workshop-book.js «Відкрити агента» (Antigravity on `pipeline/`; «нова книга» / «Продовжуємо книгу …» into the clipboard) |
| POST | `/api/workshop/books/([^/]+)/to-library` | token | `_to_library` | add-book.js `openAddBook` in its passing-on form (`{listing}` checked, or `{listingRef}`; `useListingImage` → `{jobId}`; a listing another library book has → 409 with its `bookId`) |
| POST | `/api/workshop/books/([^/]+)/place` | token | `_place` | workshop-book.js (`?key=&name=&variant=`, body — the picture: cut, flipped, two pages; the cover goes on to wait for its margins; `key=photo:<category>` — a finished photo mockup into `etsy/`, `key=canva-cover` — the photo mockups' Canva cover) |
| POST | `/api/workshop/books/([^/]+)/adopt` | token | `_adopt` | workshop-book.js «Підхопити з папки» (`{variant}` — the pictures put into `originals/` by hand, the usual way → `{jobId}`; nothing new → an error) |
| POST | `/api/workshop/books/([^/]+)/flip` | token | `_flip` | workshop-book.js ⇄ (`{key, variant}`) |
| POST | `/api/workshop/books/([^/]+)/remove` | token | `_remove` | workshop-book.js (`{key, variant}` — into `.replaced/`) |
| POST | `/api/workshop/books/([^/]+)/restore` | token | `_restore` | workshop-book.js «Скасувати» after «Прибрати» (`{undo}` as `/remove` handed it out) |
| POST | `/api/workshop/books/([^/]+)/no-margins` | token | `_no_margins` | workshop-book.js «Без полів» |
| POST | `/api/workshop/books/([^/]+)/copy-picture` | token | `_copy_picture` | workshop-book.js «Копіювати картинку» (`{key}`) |
| POST | `/api/workshop/books/([^/]+)/copy-hero` | token | `_copy_hero` | workshop-book.js «Героя в буфер» (`{variant}`) |
| POST | `/api/workshop/books/([^/]+)/upscale` | token | `_upscale_on` | workshop-book.js the switch «Апскейл ×2» (`{on}` — the whole book; on by default, off drops its queue) |
| POST | `/api/workshop/books/([^/]+)/upscale/start` | token | `_upscale_start` | workshop-book.js «Апскейлити решту» / «Перерізати з великих оригіналів» (`{keys}` — the tab's rows; `{}` — all), a picture's ✦ «Апскейлити ще раз» (`{key}`) |
| POST | `/api/workshop/books/([^/]+)/save-as` | token | `_save_as` | workshop-book.js «Зберегти як…» (`{area, name, variant}`; the Windows dialog) |
| GET | `/media/workshop/([^/]+)/(agent\|pictures\|originals\|mockups\|etsy)(?:/v/([^/]+))?/([^/]+)` | media | `_media` | workshop.js, workshop-book.js (`?w=` — a preview; `?v=` — the version: kept for good; `mockups`, `etsy` — the photo mockups' references and photos) |
| GET | `/api/workshop/gen` | token | `_gen` | workshop-live.js — the generation mode alone, while no Workshop page is on screen (no book is walked; an idle mode starts nothing) |
| POST | `/api/workshop/gen/start` | token | `_gen_start` | workshop-live.js `startGen` (`{book, key, variant, series}`) |
| POST | `/api/workshop/gen/stop` | token | `_gen_stop` | the generation bar «Стоп» |
| POST | `/api/workshop/gen/next` | token | `_gen_next` | the generation bar «Далі» (F8 does the same on the server) |
| POST | `/api/workshop/gen/again` | token | `_gen_again` | the generation bar «покласти ще раз» |
| POST | `/api/workshop/gen/photo` | token | `_gen_photo` | workshop-live.js `startPhoto` (`{book, category, template}` — the template, the book's reference, the prompt into the clipboard; without `book` — the template and the prompt, nothing caught) |
| POST | `/api/workshop/books/([^/]+)/photos/remove` | token | `_book_photo_remove` | workshop-book.js, a photo card's 🗑 (`{category}` — into `.replaced/`) |
| GET | `/api/photos` | token | `_photos` | photos.js, workshop-book.js `templatesOf` (`{categories, folder, sig, gen}` — the photo mockups' templates with their sizes) |
| GET | `/api/photos/sig` | token | `_photos_sig` | workshop-live.js for photos.js (`{sig, gen}` — the templates' folders and the generation mode) |
| GET | `/media/photos/([^/]+)/([^/]+)` | media | `_photo_media` | photos.js, workshop-book.js (`?w=&v=` — a template's preview) |
| POST | `/api/photos/add` | token | `_photo_add` | photos.js (`?category=&name=`, body — a photo → a new template `<category>-NN`) |
| POST | `/api/photos/remove` | token | `_photo_remove` | photos.js × (`{category, name}` — onto the shelf, then the Recycle Bin; `undo` — the token for «Скасувати») |
| POST | `/api/aside/restore` | token | `_restore` | photos.js, workshop-book.js — the toast's «Скасувати» (`{token}`: a Workshop book or a photo template back from the shelf, `aside.py`) |
| POST | `/api/photos/open` | token | `_photo_open` | photos.js (`{category}` — its folder; none — all templates) |
| POST | `/api/photos/prompt` | token | `_photo_prompt` | photos.js, workshop-book.js (`{category}` — its JSON prompt into the clipboard) |

## Order Creator and files — [creator/routes.py](../../app/studio/creator/routes.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/creator/status` | token | `_status` | creator.js |
| POST | `/api/creator/validate` | token | `_validate` | creator.js, orders.js (background job) |
| POST | `/api/creator/pick-file` | token | `_pick_file` | orders.js / creator.js `replacePage` (the native Windows dialog: a single picture from the computer) |
| POST | `/api/creator/replace-page` | token | `_replace_page` | orders.js / creator.js `replacePage` (a new page in place of one in the print folder) |
| POST | `/api/creator/restore-page` | token | `_restore_page` | orders.js / creator.js `restorePage` (undo the previous page) |
| POST | `/api/creator/pick-folder` | token | `_pick` | creator.js, orders.js |
| POST | `/api/creator/printify/create` | token | `_create_printify` | creator.js (background job; from 1 October 2026 — refused, 403) |
| POST | `/api/creator/printify/reprint` | token | `_reprint_printify` | creator.js `create` in reprint-from-archive mode (background job; a new order for the same book; from a send that never became an order — 409; from 1 October 2026 — refused, 403) |
| POST | `/api/creator/gelato/create` | token | `_create_gelato` | creator.js (background job; with `reprintOf` — a reprint draft from the archive's files, only from a book that really went to print) |
| GET | `/api/creator/gelato/page-counts` | token | `_gelato_page_counts` | creator.js `loadPageCounts` (how many pages Gelato prints in each format — from its catalog; `problems` — ready-made text for each length it doesn't print) |
| POST | `/api/creator/gelato/close-tunnel` | token | `_close_tunnel` | creator.js |
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
| POST | `/api/mockups/make` | token | `_make` | mockups.js `make` (background job `mockups`; `{book, picks, folder, only?}` — `only`: the ticked templates; the job shares every template's progress; with `workshop` — the demo book's cover kept as the book's `mockups/canva-cover.*`) |
| POST | `/api/mockups/finish` | token | `_finish` | mockups.js «Зберегти відкриті й закрити» (`{run}` → background job `mockups`: the second script saves and closes the templates left open) |
| POST | `/api/mockups/cancel` | token | `_stop` | mockups.js (the × while it runs) |
| POST | `/api/mockups/close` | token | `_close` | mockups.js «×» in the header — «Завершити» (`{run}`: the demo book goes, a run waiting for «Зберегти відкриті» is no longer offered; refused while a run goes on) |
| POST | `/api/mockups/open-folder` | token | `_open_folder` | mockups.js (the result's folder button) |
| POST | `/api/mockups/open-picture` | token | `_open_picture` | mockups.js, the viewer's "original" button (`{job, i}` — only a picture that job saved) |
| POST | `/api/mockups/attention` | token | `_attention` | mockups.js `tellDone` (a run ended while Book Studio's window was behind: the taskbar button flashes, Windows' sound) |
| GET | `/media/mockups/template/([a-zA-Z0-9]+)` | media | `_template_media` | mockups.js (`?w=` — a template's own preview, read from the PSD) |
| GET | `/media/mockups/out/([0-9a-f]{12})/([0-9]+)` | media | `_out_media` | mockups.js (`?w=` — a picture a job saved, by its number) |
| GET | `/media/mockups/([0-9a-f]{16})/(cover\|page\|spread)` | media | `_media` | mockups.js (`?n=&w=` / `?n=&h=` — a page, the cover, a spread glued together) |

## Listing slides — [slides/routes.py](../../app/studio/slides/routes.py)

Since 2026-09-29 — see [features/slides.md](../features/slides.md). `w` — a Workshop book's folder name, an older set's id or `template` (the default scheme), `s` — `slide1…7` (7 — the hero's looks, only for a book that has two or more, 2026-10-02). `/api/slides/make` and `/api/slides/cutouts` take `workshop` (a book) instead of `folder`; `/api/slides/make` also takes `slides` (only these slides, 09.10.2026); `/api/mockups/make` takes `workshop` too.

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/slides/state` | token | `_state` | slides-editor.js, mockups-slides.js `refresh` (`?w=`: name, folder, numbers, slides — 7 only with the hero's looks, the baked pictures, slots — `hero:1…7` with the look's name, signature; a Workshop book's looks made after its slides are taken here — `work.sync_heroes()`) |
| GET | `/api/slides/scene` | token | `_scene` | slides-editor.js (`?w=&s=` → `{scene, version}`) |
| GET | `/media/slides/scene` | media | `_scene` | slides/render.html — the page headless Edge bakes |
| GET | `/api/slides/assets` | token | `_assets` | slides-editor.js (the slots' pictures — the looks with their names and `aspect`, where the books sit, the numbers with `looks`) |
| GET | `/media/slides/assets` | media | `_assets` | slides/render.html |
| GET | `/media/slides/file/([^/]+)/(books\|pictures)/([\w.-]+\.png)` | media | `_file` | engine.js (a set's — a Workshop book's or an older one's — cut-out book, its shadow, a flat picture) |
| GET | `/api/slides/sig` | token | `_sig` | slides-editor.js `watch` every 1.5 s (a scene changed by an agent shows up) |
| POST | `/api/slides/scene` | token | `_save` | slides-editor.js `flush` (`{w, s, scene, base}` — a stale `base` → 409 with the scene as it is now) |
| POST | `/api/slides/reset` | token | `_reset` | no longer the editor's button since 2026-09-30 (it resets in the session — see [slides](../features/slides.md)); kept for agents |
| GET | `/api/slides/presets` | token | `_presets` | slides-editor.js «Схема ▾» (the schemes and the other Workshop books' slides, the one put on, the default) |
| POST | `/api/slides/apply` | token | `_apply` | slides-editor.js — a scheme (or `book:<id>`) put on all six (`{w, key}`) |
| POST | `/api/slides/save-scheme` | token | `_save_scheme` | slides-editor.js «Зберегти ці слайди як схему…» (`{w, name, default}`) |
| POST | `/api/slides/default-scheme` | token | `_default_scheme` | slides-editor.js «Нові книги — зі схеми …» |
| POST | `/api/slides/numbers` | token | `_numbers` | slides-editor.js (the book's «Сторінок» / «Віршів») |
| POST | `/api/slides/picture` | token | `_picture` | slides-editor.js «Інша картинка…» (the Windows dialog → a set's `dedication` / `page30`) |
| GET | `/api/slides/cutouts` | token | `_cutouts` | mockups-slides.js (`?folder=` — which mockups are cut out without background) |
| POST | `/api/slides/make` | token | `_make` | mockups-slides.js «Зробити слайди» (job `slides`: `{folder, order, book, numbers}` → a set, the six baked) |
| POST | `/api/slides/bake` | token | `_bake` | slides-editor.js «Зберегти картинки» (job `slides`: the set's slides into the same files) |
| GET | `/media/slides/out/([^/]+)/(slide[1-7])` | media | `_out` | mockups-slides.js (`?w=&v=` — a baked slide's preview) |
| POST | `/api/slides/open-picture` | token | `_open_picture` | mockups-slides.js, the viewer's "original" button |
| POST | `/api/slides/open-folder` | token | `_open_folder` | (a set's folder — a Workshop book's `etsy/`, where its slides are; `noBg` — its cut-outs, `no-background/`) |

## Sync — [sync.py](../../app/studio/sync.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| POST | `/api/profit/sync` | token | `_start_sync` | order-bits.js `syncOrders`, profit.js (joins a sync already running) |
| GET | `/api/profit/sync` | token | `_sync_state` | order-bits.js `runningSync` |

## Accounting — [profit.py](../../app/studio/profit.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| GET | `/api/profit/data` | token | `_data` | profit.js (only sales from `ACCOUNTING_FROM`, 1 October 2026; `accountingFrom`) |
| GET | `/api/profit/row` | token | `_row` | profit.js (an older sale — 404) |
| GET | `/api/profit/candidates` | token | `_candidates` | profit.js (print orders from 1 October only) |
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
| POST | `/api/gelato/test` | token | `_test` | settings.js (`{account: "old"}` — the old account's key) |

## His own Gelato account — [gelato_accounts.py](../../app/studio/gelato_accounts.py)

| Method | Pattern | Access | Function | Who calls it |
|---|---|---|---|---|
| POST | `/api/gelato/switch` | token | `_switch` | settings.js `switchGelato` (`{key}`: checked by reading one order; the current key becomes the old, read-only one; refused on the preview server, during a sync, with the same key, or while an old key is kept) |
| POST | `/api/gelato/old/forget` | token | `_forget` | settings.js `forgetOldGelato` (the old key goes; its orders stay as last seen) |

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
