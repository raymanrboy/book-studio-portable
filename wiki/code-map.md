---
title: Code map
type: reference
updated: 2026-09-23
code:
  - app/studio/__init__.py
  - app/requirements.txt
---
# Code map

> Every file in the program: what it's for and its main functions. Links lead to the file, function
> names are for searching (line numbers are deliberately omitted: they shift).
> Which wiki page describes a file — `python app/tools/wiki_check.py --map`.

## Launch

| File | Purpose | Main |
|---|---|---|
| [app/Book Studio.pyw](<../app/Book Studio.pyw>) | A double-click: checks packages, starts the server with no console, shows a launch error | `_message()` |
| [app/Запуск з консоллю.bat](<../app/Запуск з консоллю.bat>) | The same, with a console — to see the error | — |
| [app/Mockups.pyw](<../app/Mockups.pyw>) | A double-click: the [listing-mockups utility](features/mockups.md), its own data folder `app/data/mockups` | `_message()` |
| [app/tools/make_shortcut.py](../app/tools/make_shortcut.py) | Creates the "Book Studio" and "Мокапи" shortcuts on the desktop | `main()`, `SHORTCUTS` |
| [app/tools/wiki_check.py](../app/tools/wiki_check.py) | Checks the wiki against the code (including stale numbers in the text) | `check()`, `stale_numbers()`, `coverage()`, `changed_files()` |
| [app/tools/dev_server.py](../app/tools/dev_server.py) | A server for previewing the interface on temporary data (including a two-book order and a receipt with two print orders); writes only to its own folder, never takes keys (`BOOK_STUDIO_SAMPLE`); `--mockups` — the mockups utility with made-up templates and a pretend Photoshop | `main()`, `claim()`, `seed()`, `main_mockups()`, `pretend_photoshop()` |
| [app/requirements.txt](../app/requirements.txt) | Pillow, img2pdf, cryptography (the tested versions are in a comment) | — |

## Server: `app/studio/`

| File | Purpose | Main |
|---|---|---|
| [main.py](../app/studio/main.py) | Entry point: server, window, shutdown | `main()`, `_running_instance()`, `run_until_closed()` |
| [core.py](../app/studio/core.py) | Paths, atomic JSON, settings, logging | `ROOT`, `DATA_DIR`, `SAMPLE`, `read_json()`, `write_json()`, `Settings`, `DEFAULT_SETTINGS`, `ensure_dirs()` |
| [server.py](../app/studio/server.py) | HTTP server, routing, token, static files; which program and page it serves (`state.app`, `state.page`) | `route()`, `Request`, `json_response()`, `file_response()`, `start()`, `SESSION_TOKEN` |
| [jobs.py](../app/studio/jobs.py) | Background jobs with progress and partial findings | `Jobs`, `Job`, `Job.progress()`, `Job.share()`, `UserError`, `JobError` |
| [httpc.py](../app/studio/httpc.py) | HTTPS client: retries without duplicates, one shared read of printer errors, call logs, incomplete lists | `request()`, `request_json()`, `human()`, `audit_log()`, `HttpError`, `Listing` |
| [vault.py](../app/studio/vault.py) | Keys under Windows DPAPI | `Vault`, `protect()`, `unprotect()`, `unprotect_powershell_securestring()` |
| [desktop.py](../app/studio/desktop.py) | The program window, folder/file picker, Explorer | `open_app_window()`, `pick_folder()`, `pick_file()`, `open_in_explorer()`, `find_browser()` |
| [settings_api.py](../app/studio/settings_api.py) | Settings, keys, opening links, import from old programs | `integrations()`, `_open_url()`, `_legacy_values()`, `legacy_sources()` |
| [etsy.py](../app/studio/etsy.py) | Etsy API v3: OAuth, session, listings, receipts | `start_oauth()`, `complete_oauth()`, `refresh_tokens()`, `get()`, `ensure_shop()`, `fetch_listing()`, `fetch_all_receipts()`, `decode_session_key()` |
| [printify.py](../app/studio/printify.py) | The safe Printify client | `_check()`, `call()`, `all_orders()`, `upload_image()`, `create_product()`, `create_order_on_hold()`, `analyze_master()` |
| [gelato.py](../app/studio/gelato.py) | The safe Gelato client | `_allowed()`, `call()`, `all_orders()`, `page_counts()`, `photobook_geometry()`, `create_draft_order()` |
| [tunnel.py](../app/studio/tunnel.py) | A temporary public link to a PDF for Gelato | `FileTunnel`, `_head_ok_public_dns()`, `TunnelRegistry`, `cleanup_stale()` |
| [sendlog.py](../app/studio/sendlog.py) | The journal of sends to Printify/Gelato (`data/logs/sends/`) | `attempt()`, `step()`, `write()` |
| [wording.py](../app/studio/wording.py) | What the buyer wrote, read the same way by the card and the text check: words, "custom text vs DEFAULT", the child's name | `words()`, `is_default()`, `custom_text()`, `clean_name()` |
| [textcheck.py](../app/studio/textcheck.py) | Text check with a local model (Ollama): a quick page scan, reading, matching against the passport, checking, name rules | `check_order()`, `check_book()`, `run_key()`, `_passes()`, `page_kinds()`, `_second_half()`, `_collect()`, `assign()`, `diff()`, `findings()`, `page_issues()`, `cancel()`, `warm()`, `status()`, `start_ollama()` |
| [archive.py](../app/studio/archive.py) | Order archive: files of books that went to print, auto-deletion, "Keep" | `store()`, `refresh()`, `clock()`, `summary()`, `get()` |
| [images.py](../app/studio/images.py) | Previews, PNG checking, gluing a spread together, cache cleanup, a quick text scan of a page | `preview()`, `check_png()`, `compose_spread()`, `lqip()`, `text_score()`, `image_info()`, `prune_cache()` |
| [library.py](../app/studio/library.py) | Book library: model, import, export, the guide | `load()`, `save()`, `summary()`, `completeness()`, `scan_folder()`, `parse_text_json()`, `agent_guide()`, `export_book()` |
| [creator.py](../app/studio/creator.py) | Order Creator: file checking, Printify, Gelato (one or several books of an order), replacing a single page | `validate()`, `replace_page()`, `restore_page()`, `_backups()`, `_while_sending()`, `books_of()`, `receipt_for()`, `joint_title()`, `gelato_page_options()`, `gelato_pages_problem()`, `create_printify_draft()`, `_printify_product()`, `_printify_order()`, `create_gelato_draft()`, `_gelato_book()`, `build_photobook_pdf()`, `guess_child_name()` |
| [orders.py](../app/studio/orders.py) | Order pipeline: printer, book, laying out pages | `plan_for()`, `page_options()`, `binding_of()`, `books_by_listing()`, `enrich()`, `arrange_pages()` |
| [drops.py](../app/studio/drops.py) | Dragged-in files (saving, unpacking a ZIP, the book folder) and how a Canva export names its files — shared by Book Studio and the mockups | `export_files()`, `page_number()`, `COVER_NAME`, `UPSCAYL_TAIL`, `extract_zip()`, `dropped_folder()`, `dropped_top()`, `clear_drops()`, `DROPS` |
| [mockups.py](../app/studio/mockups.py) | [Listing mockups](features/mockups.md): the demo book, pictures for the smart objects, the run plan, Photoshop | `TEMPLATES`, `read_book()`, `cover_pictures()`, `page_picture()`, `plan()`, `script()`, `launch()`, `watch()`, `make()` |
| [mockups.jsx](../app/studio/mockups.jsx) | The Photoshop script (ExtendScript, CC 2019) the mockups run: fills copies of the templates, saves PNGs | `findLayer()`, `replaceContents()`, `runTemplate()` |
| [mockups_app.py](../app/studio/mockups_app.py) | The mockups utility as a program of its own: port 47831, its own data folder, only its routes | `main()` |
| [profit.py](../app/studio/profit.py) | Sync, snapshot, stages, accounting | `_sync()`, `startup_sync()`, `remember_print_order()`, `normalize_receipt()`, `build_view()`, `cached_view()`, `order_stage()`, `picker_orders()` |
| [reconcile.py](../app/studio/reconcile.py) | Matching Etsy receipts to print orders (one receipt can have several print orders) | `match()`, `_further_orders()`, `cover_label()`, `is_name_match()`, `printify_only_rows()` |
| [outcomes.py](../app/studio/outcomes.py) | Cancellations, refunds, replacements | `apply()`, `auto_state()`, `pod_order_info()` |
| [fees.py](../app/studio/fees.py) | Etsy fees for a Ukrainian seller | `calculate_ukrainian_etsy_fees()`, `r2()`, `money()` |
| [\_\_init\_\_.py](../app/studio/__init__.py) | The package | — |

## Interface: `app/web/`

| File | Purpose | Main |
|---|---|---|
| [index.html](../app/web/index.html) | The shell: the session token, the theme before the first frame, the "connection lost" placeholder | — |
| [mockups.html](../app/web/mockups.html) | The mockups utility's window: the same, with no sidebar | — |
| [js/mockups-shell.js](../app/web/js/mockups-shell.js) | The mockups window's shell: heartbeat, closing, Book Studio's theme, mounts the page | `boot()`, `applyTheme()` |
| [js/app.js](../app/web/js/app.js) | Sidebar, page routing, theme, heartbeat | `NAV`, `ROUTES`, `navigate()`, `applyTheme()` |
| [js/info.js](../app/web/js/info.js) | Info about the program (`/api/app`) for the shell and the pages | `store`, `refreshInfo()`, `whenInfoChanges()` |
| [js/lib.js](../app/web/js/lib.js) | Shared helpers: templates, API, tooltips, dialogs, menus, animations | `html()`, `api()`, `ib()`, `modal()`, `menu()`, `runJob()`, `upload()`, `toast()`, `segHtml()` |
| [js/icons.js](../app/web/js/icons.js) | Icons | `icon()` |
| [js/lightbox.js](../app/web/js/lightbox.js) | The image viewer | `openLightbox()` |
| [js/handoff.js](../app/web/js/handoff.js) | Passing data between pages in memory | `give()`, `take()`, `waiting()` |
| [js/keep.js](../app/web/js/keep.js) | Saved work on a new order: a hidden card and Order Creator, "draft created" | `stash()`, `unstash()`, `settle()`, `markSent()`, `sentOf()`, `finish()` |
| [js/order-bits.js](../app/web/js/order-bits.js) | Shared by Orders, the order archive and the Order Creator | `STAGES`, `statusChip()`, `alsoSentChip()`, `restorable()`, `trackChips()`, `receiptCopy()`, `isNameField()`, `planText()`, `pagesText()`, `addressFromEtsy()`, `orderSync()`, `holdClicks()`, `childOf()`, `spreadsOf()`, `receiveDrop()`, `wireFolderDrop()`, `smoothWheel()` |
| [js/pages/orders.js](../app/web/js/pages/orders.js) | Orders: the queue and the card (each book of an order worked on separately) | `mountQueue()`, `mountCard()`, `readyBooks()` |
| [js/pages/library.js](../app/web/js/pages/library.js) | The library gallery, a new book, the guide | `mount()`, `openAddBook()`, `saveGuide()` |
| [js/pages/book.js](../app/web/js/pages/book.js) | A book's passport | `mount()` |
| [js/pages/creator.js](../app/web/js/pages/creator.js) | The Order Creator (one draft for every book of an order) | `mount()`, `folderBlock()` |
| [js/pages/archive.js](../app/web/js/pages/archive.js) | Order archive: the list, a book, reprinting | `mount()`, `mountList()`, `mountBook()` |
| [js/pages/settings.js](../app/web/js/pages/settings.js) | Settings | `mount()` |
| [js/pages/mockups.js](../app/web/js/pages/mockups.js) | Mockups: the dropped demo book, spreads, template slots, the run | `mount()` |
| [js/pages/profit.js](../app/web/js/pages/profit.js) | Profit (hidden) | `mount()` |
| [css/app.css](../app/web/css/app.css) | The whole "Prepress" visual system | — |
| `img/` | Program icons (`icon.ico`, `icon.png`, `icon-512.png`; the mockups' `mockups.ico`, `mockups.png`) | — |

## Tests: `app/tests/`

| File | What it checks |
|---|---|
| [\_\_init\_\_.py](../app/tests/__init__.py) | A temporary data folder instead of the real one |
| [test_profit.py](../app/tests/test_profit.py) | Parity with the Profit Calculator (`golden_profit.json`), fees, name matching |
| [test_states.py](../app/tests/test_states.py) | Order states, stages, incremental sync, the states API |
| [test_library_creator.py](../app/tests/test_library_creator.py) | Text JSON, folder import, file checking, Printify/Gelato safeguards |
| [test_flows.py](../app/tests/test_flows.py) | Creating in Printify/Gelato with fakes, drag-and-drop, Etsy protection, OAuth |
| [test_archive.py](../app/tests/test_archive.py) | Order archive: file copies, 14/30 days, "Keep", Printify/Gelato reprints, the replacement mark |
| [test_textcheck.py](../app/tests/test_textcheck.py) | Text check: comparison, name rules, matching pages (24 and 30), a full check with a fake model, updating the passport, 127.0.0.1 only |
| [test_orders.py](../app/tests/test_orders.py) | The printer rule, laying out pages, Gelato book length, the guide, partial import, the sync rule |
| [test_mockups.py](../app/tests/test_mockups.py) | Mockups: the demo book, the cuts, the run plan, following Photoshop, the Photoshop script run by Node.js against a pretend Photoshop |
| [test_wiki.py](../app/tests/test_wiki.py) | The wiki matches the code |

More detail — [dev/testing.md](dev/testing.md).

## Related

- [Server structure](architecture/server.md) · [Interface structure](architecture/frontend.md) · [Routes](architecture/api-routes.md) · [Data](architecture/data.md)
