---
title: Code map
type: reference
updated: 2026-10-03
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
| [app/tools/restore_keys.py](../app/tools/restore_keys.py) | After a restore on another PC: the keys from the backup's JSON back into the vault | `main()` |
| [app/tools/make_shortcut.py](../app/tools/make_shortcut.py) | Creates the "Book Studio" shortcut on the desktop (the «Мокапи» one until 2026-09-24) | `main()`, `SHORTCUTS` |
| [app/tools/make_colleague_copy.py](../app/tools/make_colleague_copy.py) | A clean copy of the portable folder for someone else: no data, keys, books or history; two personal rules off | `main()`, `tracked_files()`, `scrub()` |
| [app/tools/textcheck_replay.py](../app/tools/textcheck_replay.py) | The text-check journal through today's rules: what the card would show for every past check, next to what it showed, and the owner's "Not an error" marks — for calibrating what the check shows | `replay()`, `rebuild()`, `main()` |
| [app/tools/wiki_check.py](../app/tools/wiki_check.py) | Checks the wiki against the code: headers, links, named functions, routes, file coverage | `check()`, `coverage()`, `changed_files()` |
| [app/tools/dev_server.py](../app/tools/dev_server.py) | A server for previewing the interface on temporary data (including a two-book order, a receipt with two print orders, a Workshop book, the mockups' made-up templates and a pretend Photoshop); writes only to its own folder, never takes keys (`BOOK_STUDIO_SAMPLE`) | `main()`, `claim()`, `MARK` |
| [app/tools/archive_dedupe.py](../app/tools/archive_dedupe.py) | The order archive's same pages kept once (hard links; the replaced files to the Recycle Bin) | `main()`, `_running()` |
| [app/tools/sample_data.py](../app/tools/sample_data.py) | The preview's made-up orders, print orders, library book and archived books | `seed()`, `_receipt()`, `_seed_archive()`, `_sample_book()`, `SAMPLE_TEXTS` |
| [app/tools/sample_mockups.py](../app/tools/sample_mockups.py) | The preview's made-up mockup templates, demo book, a pretend Photoshop and a pretend template for the slides' cut-out | `seed_mockups()`, `pretend_photoshop()`, `pretend_template()` |
| [app/tools/slides.py](../app/tools/slides.py) | The listing slides from the command line — the agent's skill and the tests: list, a scene's file, render one, bake, cut out | `main()` |
| [app/requirements.txt](../app/requirements.txt) | Pillow, img2pdf, pikepdf (the Gelato PDF's engine), cryptography (the tested versions are in a comment) | — |

## Server: `app/studio/`

| File | Purpose | Main |
|---|---|---|
| [main.py](../app/studio/main.py) | Entry point: server, window, shutdown | `main()`, `_another_copy_starting()`, `_running_instance()`, `run_until_closed()` |
| [core.py](../app/studio/core.py) | Paths, atomic JSON, settings, logging; what counts as a picture, "inside our folder" | `ROOT`, `DATA_DIR`, `SAMPLE`, `read_json()`, `write_json()`, `Settings`, `DEFAULT_SETTINGS`, `ensure_dirs()`, `IMAGE_EXTS`, `inside()` |
| [server.py](../app/studio/server.py) | HTTP server, routing, token, static files; which program and page it serves (`state.app`, `state.page`) | `route()`, `Request`, `json_response()`, `file_response()`, `start()`, `SESSION_TOKEN` |
| [jobs.py](../app/studio/jobs.py) | Background jobs with progress and partial findings | `Jobs`, `Job`, `Job.progress()`, `Job.share()`, `UserError`, `JobError` |
| [httpc.py](../app/studio/httpc.py) | HTTPS client: retries without duplicates, one shared read of printer errors, call logs, incomplete lists | `request()`, `request_json()`, `human()`, `audit_log()`, `HttpError`, `Listing` |
| [vault.py](../app/studio/vault.py) | Keys under Windows DPAPI | `Vault`, `protect()`, `unprotect()`, `unprotect_powershell_securestring()` |
| [backup.py](../app/studio/backup.py) | The backup to Google Drive: the whole program and the templates in a 7-Zip archive with a password, every 3 days | `make()`, `start_if_due()`, `to_remove()`, `drive_root()`, `status()` |
| [transfer.py](../app/studio/transfer.py) | Settings and keys in one 7-Zip file under the backup password: export, import (what it replaces is kept aside) | `export_to()`, `import_from()`, `_portable_settings()`, `_save_current()` |
| [desktop.py](../app/studio/desktop.py) | The program window, folder/file picker, Explorer | `open_app_window()`, `pick_folder()`, `pick_file()`, `open_in_explorer()`, `find_browser()`, `file_holders()` (which programs hold a file — Restart Manager) |
| [settings_api.py](../app/studio/settings_api.py) | Settings, keys, opening links, import from old programs | `integrations()`, `_open_url()`, `_legacy_values()`, `legacy_sources()` |
| [etsy.py](../app/studio/etsy.py) | Etsy API v3: OAuth, session, listings, receipts | `start_oauth()`, `complete_oauth()`, `refresh_tokens()`, `get()`, `ensure_shop()`, `fetch_listing()`, `fetch_all_receipts()`, `decode_session_key()` |
| [printify.py](../app/studio/printify.py) | The safe Printify client; read-only from 1 October 2026 | `retired()`, `_check()`, `call()`, `all_orders()`, `upload_image()`, `create_product()`, `create_order_on_hold()`, `analyze_master()` |
| [gelato.py](../app/studio/gelato.py) | The safe Gelato client; two keys during the move (the old one only reads) | `_allowed()`, `call()`, `accounts()`, `account_id()`, `check_key()`, `all_orders()`, `page_counts()`, `photobook_geometry()`, `create_draft_order()`, `slot_of()`, `history()`, `cached_history()` |
| [gelato_accounts.py](../app/studio/gelato_accounts.py) | The move to the owner's own Gelato account: the switch, the old account's status, removing its key | `_switch()`, `_forget()`, `status()`, `open_orders()` |
| [tunnel.py](../app/studio/tunnel.py) | A temporary public link to a PDF for Gelato | `FileTunnel`, `_head_ok_public_dns()`, `TunnelRegistry`, `cleanup_stale()` |
| [sendlog.py](../app/studio/sendlog.py) | The journal of sends to Printify/Gelato (`data/logs/sends/`) | `attempt()`, `step()`, `write()` |
| [wording.py](../app/studio/wording.py) | What the buyer wrote, read the same way by the card, the Order Creator and the text check: words, "custom text vs DEFAULT", the child's name | `words()`, `is_default()`, `custom_text()`, `clean_name()`, `guess_child_name()`, `alike()` |
| [textcheck/](../app/studio/textcheck/__init__.py) | [Text check](features/text-check.md) with a local model (Ollama) — a package since 2026-09-27; `__init__.py` gathers what the rest of the program uses | what the parts below give the rest of the program |
| [textcheck/run.py](../app/studio/textcheck/run.py) | One check: the print files, a quick page scan, the read and check passes, answers cached by content, stopping | `check_order()`, `check_book()`, `run_key()`, `_passes()`, `page_kinds()`, `_second_half()`, `_collect()`, `_Run`, `cancel()`, `warm()`, `picture()` |
| [textcheck/rules.py](../app/studio/textcheck/rules.py) | What the card shows: findings, page and book rules, the wrong-book guard | `findings()`, `page_issues()`, `book_issues()`, `_all_issues()`, `_one_alarm()`, `has_text()` |
| [textcheck/texts.py](../app/studio/textcheck/texts.py) | Words compared, the buyer's fields, which page is which library text | `diff()`, `similarity()`, `personalization()`, `fill()`, `assign()`, `COMMON` |
| [textcheck/ollama.py](../app/studio/textcheck/ollama.py) | The model on this computer (127.0.0.1 only) | `status()`, `start_ollama()`, `_ready()`, `_chat()`, `_release_model()` |
| [textcheck/journal.py](../app/studio/textcheck/journal.py) | The journal of every check and the owner's marks | `_journal()`, `mark()`, `CHECKS` |
| [textcheck/routes.py](../app/studio/textcheck/routes.py) | The routes; a printed page turned back into the passport's text | `_check()`, `_passport()`, `as_template()` |
| [archive.py](../app/studio/archive.py) | Order archive: files of books that went to print, auto-deletion, "Keep" | `store()`, `refresh()`, `clock()`, `summary()`, `get()`, `page_key()`, `dedupe()` |
| [images.py](../app/studio/images.py) | Previews, PNG checking, gluing a spread together, cache cleanup, a quick text scan of a page | `preview()`, `check_png()`, `flat_rgb()`, `compose_spread()`, `lqip()`, `text_score()`, `image_info()`, `prune_cache()` |
| [library.py](../app/studio/library.py) | Book library: the model, a new book, its pictures, the book routes | `load()`, `save()`, `all_books()`, `summary()`, `completeness()`, `create_book()`, `listing_of()`, `import_pictures()` |
| [library_files.py](../app/studio/library_files.py) | A book's files in and out: the text JSON, the folder import, the export, the guide (its words in `library_guide.md`, which the owner may edit) | `scan_folder()`, `parse_text_json()`, `export_text_json()`, `agent_guide()`, `export_book()` |
| [workshop/books.py](../app/studio/workshop/books.py) | [The Workshop](features/workshop.md): a book = a folder of the pipeline — the list, the path strip, marks, versions, Antigravity, delete, passing to the library | `all_books()`, `summary()`, `detail()`, `steps()`, `set_mark()`, `signature()`, `agent_words()`, `open_agent()`, `delete_book()`, `to_library()` |
| [workshop/rows.py](../app/studio/workshop/rows.py) | The agents' files read into the book's rows; the cover's template and outpaint prompt; hero variants; the book check (GO) | `book_rows()`, `text_sections()`, `cover_state()`, `template_layout()`, `outpaint_prompt()`, `variants()`, `book_check()` |
| [workshop/pictures.py](../app/studio/workshop/pictures.py) | A picture into its row: cut, flipped, two pages; the cover on the template; ⇄; nothing deleted | `place()`, `two_squares()`, `build_expanded()`, `fit_template()`, `flip()`, `remove()`, `spread_panorama()` |
| [workshop/generate.py](../app/studio/workshop/generate.py) | The generation mode: the clipboard, the Downloads watcher, F8 | `Session`, `session()`, `downloads_folder()` |
| [workshop/upscale.py](../app/studio/workshop/upscale.py) | Upscaling a row's picture ×2 by the owner's Upscayl, in the background, then cut again | `upscale_row()`, `Upscaler`, `engine()`, `status()`, `after_place()`, `set_on()`, `start()` |
| [workshop/check.py](../app/studio/workshop/check.py) | The book check: the old pipeline validator's rules (the agents run it too) | `run()`, `main()` |
| [workshop/routes.py](../app/studio/workshop/routes.py) | The Workshop's routes | — |
| [workshop/\_\_init\_\_.py](../app/studio/workshop/__init__.py) | The package: what the Workshop is, its modules | — |
| [clipboard.py](../app/studio/clipboard.py) | The Windows clipboard filled by the program (text, a picture), F8 taken while needed | `set_text()`, `set_image()`, `Hotkey` |
| [creator/](../app/studio/creator/__init__.py) | [Order Creator](features/order-creator.md) — a package since 2026-09-27; `__init__.py` gathers what the rest of the program uses | what the parts below give the rest of the program |
| [creator/printfolder.py](../app/studio/creator/printfolder.py) | A print folder: what it must hold, its full check, one page replaced and put back, held while a send reads it | `validate()`, `expected_files()`, `gelato_page_options()`, `replace_page()`, `restore_page()`, `_backups()`, `_while_sending()` |
| [creator/sending.py](../app/studio/creator/sending.py) | What every send does the same way: the books and their receipt, the address, the send journal, the archive copy, the print order recorded | `journaled_send()`, `books_of()`, `receipt_for()`, `joint_title()`, `mark_books()`, `checked_files()`, `record_order()`, `validate_address()` |
| [creator/printify_send.py](../app/studio/creator/printify_send.py) | Printify: books from the Master, uploads once, an order «On hold», a reprint | `create_printify_draft()`, `_printify_product()`, `_printify_order()`, `create_printify_reprint()`, `build_printify_payload()` |
| [creator/gelato_send.py](../app/studio/creator/gelato_send.py) | Gelato: a draft for the books of an order, a PDF each on a temporary link | `create_gelato_draft()`, `_gelato_book()`, `gelato_pages_problem()`, `gelato_page_counts()` |
| [creator/photobook.py](../app/studio/creator/photobook.py) | The photobook PDF (the PNGs as they are) | `build_photobook_pdf()`, `_one_idat()` |
| [creator/routes.py](../app/studio/creator/routes.py) | The routes; a print folder's pictures for the page and the viewer | `_status()`, `_create_printify()`, `_create_gelato()`, `_folder_media()`, `_folder_spread()` |
| [orders.py](../app/studio/orders.py) | Order pipeline: printer, book, laying out pages | `plan_for()`, `page_options()`, `binding_of()`, `books_by_listing()`, `enrich()`, `arrange_pages()` |
| [drops.py](../app/studio/drops.py) | Dragged-in files (saving, unpacking a ZIP, the book folder) and how a Canva export names its files — shared by the orders, the library and the mockups | `export_files()`, `page_number()`, `COVER_NAME`, `UPSCAYL_TAIL`, `extract_zip()`, `dropped_folder()`, `dropped_top()`, `clear_drops()`, `DROPS` |
| [photos.py](../app/studio/photos.py) | [Photo mockups](features/photo-mockups.md): the templates by category (`app/data/photo-mockups`), the five JSON prompts, a book's references (`mockups/`) and photos (`etsy/`) | `CATEGORIES`, `REFS`, `PROMPTS`, `templates()`, `add_template()`, `references()`, `items()`, `place()`, `state()`, `set_canva_cover()` |
| [modules.py](../app/studio/modules.py) | Optional modules (the text check, upscaling): installed on request from checked official files into `runtime/`, or from a ZIP; removed | `MODULES`, `installed()`, `listing()`, `download()`, `unpack()`, `start_install()`, `remove()` |
| [portable.py](../app/studio/portable.py) | The portable copy's `runtime/`: where each program is, saved paths taken into it, `PATH`/`OLLAMA_MODELS` | `root()`, `runtime()`, `relocate()`, `antigravity_launch()`, `ffmpeg()`, `env()`, `check()`, `rebase_paths()`, `prerequisites()`, `install()` |
| [mockups.py](../app/studio/mockups.py) | [Listing mockups](features/mockups.md): the demo book (in its own folder), pictures for the smart objects, the run plan, Photoshop | `TEMPLATES`, `BOOKS`, `read_book()`, `clear_books()`, `_take_dropped()`, `cover_pictures()`, `page_picture()`, `plan()`, `script()`, `launch()`, `watch()`, `make()` |
| [mockups.jsx](../app/studio/mockups.jsx) | The Photoshop script (ExtendScript, CC 2019) the mockups run: fills copies of the templates, saves PNGs | `findLayer()`, `replaceContents()`, `runTemplate()` |
| [slides/\_\_init\_\_.py](../app/studio/slides/__init__.py) | [Listing slides](features/slides.md): the package, what's where | — |
| [slides/cutout.py](../app/studio/slides/cutout.py) | A mockup → the book and its real shadow, transparent (the template's mask and Multiply layers, only read; Dedication — the desk and the book, the floor gone); `no-background/` («Без фону»); the background cutter | `kind_of()`, `read_psd()`, `cut()`, `combined()`, `ensure()`, `Cutter`, `cutter`, `READER` |
| [slides/store.py](../app/studio/slides/store.py) | The schemes (Nature, Night, the owner's own) and a book's slides (a Workshop book's in its folder): scenes with their versions (a stale save refused), slots, pictures, the cleaning | `list_schemes()`, `save_scheme()`, `apply_preset()`, `presets()`, `load()`, `save()`, `reset()`, `sig()`, `new_set()`, `mockups_dir()`, `clean_temporary()`, `book_done()` |
| [slides/work.py](../app/studio/slides/work.py) | «Зробити слайди»: the mockups into slots, the set, the six (seven) baked; a re-bake; the hero's looks into slide 7 | `make()`, `bake_set()`, `mockups_in()`, `slots_of()`, `pictures()`, `looks()`, `put_heroes()`, `sync_heroes()` |
| [slides/bake.py](../app/studio/slides/bake.py) | Headless Edge draws `slides/render.html` at 2000², three at once; the names in the owner's folder | `bake()`, `render()`, `outputs()`, `run_browser()` |
| [slides/routes.py](../app/studio/slides/routes.py) | The slides' routes | `assets()`, `_make()`, `_bake()`, `_save()` |
| `slides/design/slide1…6.json`, `slides/design/slide7.json` | The slides' first design (the template's «Скинути» goes back to it); 7 — the hero's looks, on slide 4 (2026-10-02) | — |
| [sync.py](../app/studio/sync.py) | Pulling the orders: Etsy receipts (changed ones, a full read weekly), Printify and Gelato orders, into the snapshot | `_sync()`, `startup_sync()`, `normalize_receipt()`, `merge_receipts()` |
| [records.py](../app/studio/records.py) | What is kept about orders on disk: the snapshot, manual links and states, the print orders this program sent | `load_snapshot()`, `stamp()`, `remember_print_order()`, `add_replacement()`, `unmark_reprint()`, `SNAPSHOT`, `SENDS` |
| [printorders.py](../app/studio/printorders.py) | One reading of a Printify / Gelato order: its cost in dollars, dead or placed, name, label, tracking | `facts()`, `all_facts()`, `is_placed()`, `dead()`, `to_usd()`, `rates()`, `carrier_label()` |
| [ledger.py](../app/studio/ledger.py) | Etsy's payment ledger: the balance, the payouts, each receipt's real money — the check of the program's sums | `refresh()`, `assign()`, `view()`, `window_net()` |
| [reconcile.py](../app/studio/reconcile.py) | Matching Etsy receipts to print orders (numbers before names), the cover a buyer chose | `match()`, `_find()`, `item_format()`, `cover_label()`, `is_name_match()`, `printify_only_rows()` |
| [outcomes.py](../app/studio/outcomes.py) | The money of a row, once: cancellations, refunds, replacements, a sale's other print orders, unpaid orders | `rows()`, `apply()`, `auto_state()`, `order_info()`, `reserved_orders()` |
| [stages.py](../app/studio/stages.py) | Where each Etsy order stands (new / in work / sent / shipped / closed), once per view; a reprint's mark | `facts()`, `order_stage()`, `picker_orders()`, `picker_order()`, `mark_reprint()` |
| [profit.py](../app/studio/profit.py) | The Profit view and its routes (rows, one row, candidates, links, states); only sales from 1 October 2026 | `ACCOUNTING_FROM`, `counted()`, `build_view()`, `cached_view()`, `_set_link()`, `_set_state()` |
| [fees.py](../app/studio/fees.py) | Etsy fees for a Ukrainian seller | `calculate_ukrainian_etsy_fees()`, `r2()`, `money()` |
| [\_\_init\_\_.py](../app/studio/__init__.py) | The package | — |

## Interface: `app/web/`

| File | Purpose | Main |
|---|---|---|
| [index.html](../app/web/index.html) | The shell: the session token, the theme before the first frame, the "connection lost" placeholder | — |
| [js/app.js](../app/web/js/app.js) | The labelled [rail of places and tools](features/modes.md), page routing, the ink of the area, theme, heartbeat | `PLACES`, `ROUTES`, `ALIASES`, `navigate()`, `placeNavPill()`, `applyTheme()` |
| [js/places.js](../app/web/js/places.js) | Where things are: the places, the tools, Settings' blocks — for «Інструменти» and the search | `PLACES`, `TOOLS`, `SETTINGS` |
| [js/palette.js](../app/web/js/palette.js) | Search everywhere (Ctrl+K): orders, books, places, tools | `openPalette()` |
| [js/path.js](../app/web/js/path.js) | An object's path strip (an order's Canva → … → Відправка; a Workshop book's eleven steps) | `pathHtml()`, `pathStep()` |
| [js/book-tile.js](../app/web/js/book-tile.js) | One book on a shelf — the library's and the Workshop's tile, one progress bar | `bookTile()`, `segBar()`, `tickBadge()` |
| [js/pages/tools.js](../app/web/js/pages/tools.js) | «Інструменти» — every tool that works on its own | `mount()` |
| [js/pages/books.js](../app/web/js/pages/books.js) | «Книги» — the Workshop's and the library's galleries as tabs | `mount()` |
| [js/info.js](../app/web/js/info.js) | Info about the program (`/api/app`) for the shell and the pages | `store`, `refreshInfo()`, `whenInfoChanges()` |
| [js/lib.js](../app/web/js/lib.js) | Shared helpers: templates, API, tooltips, dialogs, menus, animations, a detail page's Esc and "could not open", what's missing | `markMissing()`, `html()`, `api()`, `ib()`, `modal()`, `confirmChecked()`, `menu()`, `runJob()`, `upload()`, `toast()`, `segHtml()`, `escBack()`, `notFound()` |
| [js/icons.js](../app/web/js/icons.js) | Icons | `icon()` |
| [js/lightbox.js](../app/web/js/lightbox.js) | The image viewer | `openLightbox()` |
| [js/handoff.js](../app/web/js/handoff.js) | Passing data between pages in memory | `give()`, `take()`, `waiting()` |
| [js/keep.js](../app/web/js/keep.js) | Saved work on a new order: a hidden card and Order Creator, "draft created" | `stash()`, `unstash()`, `settle()`, `markSent()`, `sentOf()`, `finish()` |
| [js/order-bits.js](../app/web/js/order-bits.js) | Shared by Orders, the order archive and the Order Creator | `STAGES`, `proofHtml()`, `filesBadge()`, `checkNotices()`, `fieldsHtml()`, `addressHtml()`, `svcChip()`, `countStages()`, `emptyOrders()`, `statusChip()`, `alsoSentChip()`, `restorable()`, `trackChips()`, `receiptCopy()`, `isNameField()`, `planText()`, `pagesText()`, `addressFromEtsy()`, `orderSync()`, `holdClicks()`, `childOf()`, `spreadsOf()`, `smoothWheel()` |
| [js/order-history.js](../app/web/js/order-history.js) | The printer's history card of a placed Gelato order, asked for when the order card opens | `mountHistory()`, `rows()`, `iconOf()` |
| [js/drop-anywhere.js](../app/web/js/drop-anywhere.js) | Files dropped anywhere outside a page's own drop field: the page may take them (`bs:dropped`), otherwise one question «Куди?» (the Mockups or the Order Creator) and a hand-over | `installDropAnywhere()` |
| [js/drop.js](../app/web/js/drop.js) | Files and folders dragged into the window: read in full (a folder's tree, a ZIP) and copied into the program — the order card, the Order Creator, the passport, the mockups | `dropContents()`, `receiveDrop()`, `dropLabel()`, `wireFolderDrop()` |
| [js/add-book.js](../app/web/js/add-book.js) | «Нова книга» and the Workshop's «Передати в бібліотеку» — one dialog | `openAddBook()` |
| [js/workshop-bits.js](../app/web/js/workshop-bits.js) | What the Workshop's two pages share: a picture's address, the check's word, a step's state in words | `picture()`, `checkWord()`, `STATE_WORDS`, `STATE_TEXT` |
| [js/folder-viewer.js](../app/web/js/folder-viewer.js) | The viewer of a book's print folder, a page replaced and put back there — the order card and the Order Creator | `openFolderViewer()`, `pageNo()`, `pageWord()` |
| [js/pages/orders.js](../app/web/js/pages/orders.js) | Orders: the queue (and the route to a card) | `mount()`, `mountQueue()` |
| [js/pages/order-card.js](../app/web/js/pages/order-card.js) | One order's card (each book of an order worked on separately) | `mountCard()`, `readyBooks()`, `startCheck()`, `print()` |
| [js/pages/library.js](../app/web/js/pages/library.js) | The library gallery, the guide | `mount()`, `saveGuide()` |
| [js/pages/book.js](../app/web/js/pages/book.js) | A book's passport | `mount()` |
| [js/pages/book-dialogs.js](../app/web/js/pages/book-dialogs.js) | The passport's dialogs: «Імпорт з папки», the text JSON, the Canva link; the whole text in one piece; the slots' layout | `importFolder()`, `pasteJsonDialog()`, `canvaDialog()`, `bookText()`, `SLOT_KEYS` |
| [js/pages/creator.js](../app/web/js/pages/creator.js) | The Order Creator (one draft for every book of an order) | `mount()`, `folderBlock()` |
| [js/pages/creator-picker.js](../app/web/js/pages/creator-picker.js) | The Order Creator's «Замовлення Etsy» (the queue's own orders) | `pickEtsyOrder()` |
| [js/pages/gelato-result.js](../app/web/js/pages/gelato-result.js) | A Gelato draft's green card, shared by the Order Creator and the order card; the link's countdown | `gelatoResultHtml()`, `runCountdown()`, `resultAction()` |
| [js/pages/archive.js](../app/web/js/pages/archive.js) | Order archive: the list, a book, reprinting | `mount()`, `mountList()`, `mountBook()` |
| [js/pages/settings.js](../app/web/js/pages/settings.js) | Settings | `mount()` |
| [js/pages/settings-dialogs.js](../app/web/js/pages/settings-dialogs.js) | Settings' dialogs: the Etsy sign-in, the Printify Master | `oauthFlow()`, `pickMaster()` |
| [js/pages/workshop.js](../app/web/js/pages/workshop.js) | The Workshop's gallery: the books with their path, a new book in Antigravity | `mount()` |
| [js/pages/workshop-book.js](../app/web/js/pages/workshop-book.js) | A Workshop book: the path strip and its panel, the rows, the cover's two stages, hero variants, «Передати в бібліотеку» | `mount()` |
| [js/pages/workshop-rows.js](../app/web/js/pages/workshop-rows.js) | A Workshop book's rows drawn: a spread or a page with its prompt, its frame, its text; the parts the cover's card shares | `rowTemplates()`, `waitChip()` |
| [js/workshop-live.js](../app/web/js/workshop-live.js) | The Workshop's live link: what changed, the generation mode's state and bar, the rail's dot and title | `watch()`, `refresh()`, `wake()`, `act()`, `startGen()`, `genBar()` |
| [js/pages/photos.js](../app/web/js/pages/photos.js) | «Фотомокапи» (`#/photos`): the templates by category — a click puts the template, then the prompt into the clipboard; add, remove | `mount()` |
| [js/pages/mockups.js](../app/web/js/pages/mockups.js) | Mockups: the dropped demo book, spreads, template slots, the run; kept when left | `mount()` |
| [js/pages/mockups-run.js](../app/web/js/pages/mockups-run.js) | Mockups, step 3 drawn: the run and Photoshop's question, the result, «Ваша черга», the pictures saved after it | `runView()`, `resultCard()`, `turnCard()`, `finishedCard()` |
| [js/pages/mockups-slides.js](../app/web/js/pages/mockups-slides.js) | Mockups, step 4 — the listing slides: «Без фону», «Зробити слайди», the six, the editor's door | `slidesStep()` |
| [js/pages/slides-editor.js](../app/web/js/pages/slides-editor.js) | The listing slides' editor (loaded only when opened): layers, the slide with its handles, the grouped properties, live saving, an agent's change shown | `mount()`, `SPEC`, `NEW` |
| [js/slides/engine.js](../app/web/js/slides/engine.js) | Draws a slide's scene (torn paper, stickers, fitted Comica, arrows, the cut-out books) — the editor, the bake | `drawScene()`, `drawElement()`, `boxOf()`, `setAssets()`, `ready()` |
| [slides/render.html](../app/web/slides/render.html) | The page headless Edge bakes a slide from | — |
| [js/pages/profit.js](../app/web/js/pages/profit.js) | Profit (hidden): the period, the figures, the table, linking an order by hand | `mount()` |
| [js/pages/profit-rows.js](../app/web/js/pages/profit-rows.js) | Profit: one order's row and its open panel (templates of the order) | `rowInner()`, `detailHtml()`, `stateBox()`, `costOf()` |
| [css/app.css](../app/web/css/app.css) | The "Prepress" visual system: tokens, the shell, the controls, what the pages share | — |
| [css/library.css](../app/web/css/library.css) | The Library and a book's passport | — |
| [css/orders.css](../app/web/css/orders.css) | The Order Creator, the queue and the order card, the archive | — |
| [css/profit.css](../app/web/css/profit.css) | The Profit page | — |
| [css/listings.css](../app/web/css/listings.css) | The Workshop and the listing mockups (their step 4, the slides) | — |
| [css/slides.css](../app/web/css/slides.css) | The listing slides' editor — linked by the editor itself | — |
| [css/motion-mockups.css](../app/web/css/motion-mockups.css) | Motion overrides for the mockup and photo rules of `listings.css` (2026-10-06) | — |
| [css/motion-settings.css](../app/web/css/motion-settings.css) | Motion for Settings: results fading in, secret rows (2026-10-06) | — |
| `fonts/` | Comica (`ComicaRegular.otf`) with its SIL OFL licence — the slides' letters | — |
| `img/` | Program icons (`icon.ico`, `icon.png`, `icon-512.png`) | — |

## Tests: `app/tests/`

| File | What it checks |
|---|---|
| [\_\_init\_\_.py](../app/tests/__init__.py) | A temporary data folder instead of the real one |
| [test_ledger.py](../app/tests/test_ledger.py) | Etsy's ledger: each entry to its receipt, a receipt's real money, the balance against the payouts |
| [test_profit.py](../app/tests/test_profit.py) | Parity with the Profit Calculator (`golden_profit.json`), fees, name matching, the bookkeeping's first day |
| [test_gelato_accounts.py](../app/tests/test_gelato_accounts.py) | Two made-up Gelato accounts: the switch, the old one only read, no order lost |
| [test_gelato_history.py](../app/tests/test_gelato_history.py) | The card's history: reading a full order, one read per card (kept a minute), which orders are asked about |
| [test_states.py](../app/tests/test_states.py) | Order states, stages, incremental sync, the states API |
| [test_library_creator.py](../app/tests/test_library_creator.py) | Text JSON, folder import, file checking, Printify/Gelato safeguards |
| [test_flows.py](../app/tests/test_flows.py) | Creating in Printify/Gelato with fakes, drag-and-drop, Etsy protection, OAuth |
| [test_archive.py](../app/tests/test_archive.py) | Order archive: file copies, 14/30 days, "Keep", Printify/Gelato reprints, the replacement mark |
| [test_textcheck.py](../app/tests/test_textcheck.py) | Text check: comparison, name rules, matching pages (24 and 30), a full check with a fake model, updating the passport, 127.0.0.1 only |
| [test_orders.py](../app/tests/test_orders.py) | The printer rule, laying out pages, Gelato book length, the guide, partial import, the sync rule |
| [test_etsy_rule.py](../app/tests/test_etsy_rule.py) | The owner's own rules as settings: Etsy only from Kyiv, Printify read-only from a date — on by default, off for a copy |
| [test_transfer.py](../app/tests/test_transfer.py) | The settings file: what goes in and what does not, import puts it back and keeps the old, a wrong password changes nothing |
| [test_modules.py](../app/tests/test_modules.py) | The optional modules: install from checked files, a wrong hash, a package that climbs out, removal |
| [test_portable_move.py](../app/tests/test_portable_move.py) | The folder moves: paths inside the data follow it, the quiet install of Windows prerequisites |
| [test_portable.py](../app/tests/test_portable.py) | The portable copy: programs found in `runtime/`, saved paths taken into it, the ordinary install unchanged |
| [test_mockups.py](../app/tests/test_mockups.py) | Mockups: the demo book (its own folder, apart from an order's dropped files), the cuts, the run plan, following Photoshop, the Photoshop script run by Node.js against a pretend Photoshop |
| [test_photos.py](../app/tests/test_photos.py) | Photo mockups: the templates, the five prompts, a book's clipboard order and the photo caught into `etsy/`, the step, without a book, the Canva cover kept |
| [test_slides.py](../app/tests/test_slides.py) | Listing slides: the cut-out and `no-background/`, the background cutter, the template and a set (a stale save refused), «Зробити слайди» with a pretend browser, names, the command line |
| [test_workshop.py](../app/tests/test_workshop.py) | The Workshop: a book by its title, never in the orders, prompts, one JSON (dry run, what's missing), the agent's instruction, passing a book to the library |
| [test_upscale.py](../app/tests/test_upscale.py) | The Workshop's upscaling: ×2 and cut as before, the cover and pages 1/30, the variants (not the hero pictures), the switch, a picture replaced meanwhile, a failure, finding Upscayl by its log |
| [test_wiki.py](../app/tests/test_wiki.py) | The wiki matches the code |

More detail — [dev/testing.md](dev/testing.md).

## Related

- [Server structure](architecture/server.md) · [Interface structure](architecture/frontend.md) · [Routes](architecture/api-routes.md) · [Data](architecture/data.md)
