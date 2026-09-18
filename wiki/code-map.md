---
title: Карта коду
type: reference
updated: 2026-09-18
code:
  - app/studio/__init__.py
  - app/requirements.txt
---
# Карта коду

> Кожен файл програми: навіщо він і які в ньому головні функції. Посилання ведуть у файл,
> назви функцій — для пошуку (номери рядків навмисно не вказуються: вони зсуваються).
> Яка сторінка вікі описує файл — `python app/tools/wiki_check.py --map`.

## Запуск

| Файл | Навіщо | Головне |
|---|---|---|
| [app/Book Studio.pyw](<../app/Book Studio.pyw>) | Подвійний клік: перевіряє пакети, запускає сервер без консолі, показує помилку запуску | `_message()` |
| [app/Запуск з консоллю.bat](<../app/Запуск з консоллю.bat>) | Те саме з консоллю — щоб побачити помилку | — |
| [app/tools/make_shortcut.py](../app/tools/make_shortcut.py) | Створює ярлик «Book Studio» на робочому столі | `main()` |
| [app/tools/wiki_check.py](../app/tools/wiki_check.py) | Перевірка вікі проти коду | `check()`, `coverage()`, `changed_files()` |
| [app/tools/dev_server.py](../app/tools/dev_server.py) | Сервер для перегляду інтерфейсу на тимчасових даних | `main()` |
| [app/requirements.txt](../app/requirements.txt) | Pillow, img2pdf, cryptography | — |

## Сервер: `app/studio/`

| Файл | Навіщо | Головне |
|---|---|---|
| [main.py](../app/studio/main.py) | Точка входу: сервер, вікно, завершення | `main()`, `_running_instance()` |
| [core.py](../app/studio/core.py) | Шляхи, атомарний JSON, налаштування, журнал | `ROOT`, `DATA_DIR`, `read_json()`, `write_json()`, `Settings`, `DEFAULT_SETTINGS`, `ensure_dirs()` |
| [server.py](../app/studio/server.py) | HTTP-сервер, маршрутизація, токен, статика | `route()`, `Request`, `json_response()`, `file_response()`, `start()`, `SESSION_TOKEN` |
| [jobs.py](../app/studio/jobs.py) | Фонові задачі з прогресом | `Jobs`, `Job`, `UserError`, `JobError` |
| [httpc.py](../app/studio/httpc.py) | HTTPS-клієнт із повторами | `request()`, `request_json()`, `HttpError` |
| [vault.py](../app/studio/vault.py) | Ключі під Windows DPAPI | `Vault`, `protect()`, `unprotect()`, `unprotect_powershell_securestring()` |
| [desktop.py](../app/studio/desktop.py) | Вікно програми, вибір папки, Провідник | `open_app_window()`, `pick_folder()`, `open_in_explorer()`, `find_browser()` |
| [settings_api.py](../app/studio/settings_api.py) | Налаштування, ключі, відкриття посилань, імпорт зі старих програм | `integrations()`, `_open_url()`, `_legacy_values()`, `legacy_sources()` |
| [etsy.py](../app/studio/etsy.py) | Etsy API v3: OAuth, сесія, лістинги, чеки | `start_oauth()`, `complete_oauth()`, `refresh_tokens()`, `get()`, `ensure_shop()`, `fetch_listing()`, `fetch_all_receipts()`, `decode_session_key()` |
| [printify.py](../app/studio/printify.py) | Безпечний клієнт Printify | `_check()`, `call()`, `all_orders()`, `upload_image()`, `create_product()`, `create_order_on_hold()`, `analyze_master()` |
| [gelato.py](../app/studio/gelato.py) | Безпечний клієнт Gelato | `_allowed()`, `call()`, `all_orders()`, `page_counts()`, `photobook_geometry()`, `create_draft_order()` |
| [tunnel.py](../app/studio/tunnel.py) | Тимчасове публічне посилання на PDF для Gelato | `FileTunnel`, `_head_ok_public_dns()`, `TunnelRegistry`, `cleanup_stale()` |
| [sendlog.py](../app/studio/sendlog.py) | Журнал відправок у Printify/Gelato (`data/logs/sends/`) | `attempt()`, `step()`, `write()` |
| [archive.py](../app/studio/archive.py) | Архів замовлень: файли книг, що пішли в друк, автовидалення, «Не видаляти» | `store()`, `refresh()`, `clock()`, `summary()`, `get()` |
| [images.py](../app/studio/images.py) | Прев'ю, перевірка PNG, склеювання розвороту | `preview()`, `check_png()`, `compose_spread()`, `lqip()`, `image_info()` |
| [library.py](../app/studio/library.py) | Бібліотека книг: модель, імпорт, експорт, інструкція | `load()`, `save()`, `summary()`, `completeness()`, `scan_folder()`, `parse_text_json()`, `agent_guide()`, `export_book()` |
| [creator.py](../app/studio/creator.py) | Order Creator: перевірка файлів, Printify, Gelato, перетягування | `validate()`, `gelato_page_options()`, `gelato_pages_problem()`, `create_printify_draft()`, `create_gelato_draft()`, `build_photobook_pdf()`, `extract_zip()`, `dropped_folder()`, `guess_child_name()` |
| [orders.py](../app/studio/orders.py) | Конвеєр замовлень: друкарня, книга, розстановка сторінок | `plan_for()`, `page_options()`, `binding_of()`, `books_by_listing()`, `enrich()`, `arrange_pages()`, `page_number()` |
| [profit.py](../app/studio/profit.py) | Синхронізація, знімок, етапи, облік | `_sync()`, `startup_sync()`, `normalize_receipt()`, `build_view()`, `cached_view()`, `order_stage()`, `picker_orders()` |
| [reconcile.py](../app/studio/reconcile.py) | Зіставлення чеків Etsy із замовленнями друку | `match()`, `cover_label()`, `is_name_match()`, `printify_only_rows()` |
| [outcomes.py](../app/studio/outcomes.py) | Скасування, повернення, заміни | `apply()`, `auto_state()`, `pod_order_info()` |
| [fees.py](../app/studio/fees.py) | Комісії Etsy для українського продавця | `calculate_ukrainian_etsy_fees()`, `r2()`, `money()` |
| [\_\_init\_\_.py](../app/studio/__init__.py) | Пакет | — |

## Інтерфейс: `app/web/`

| Файл | Навіщо | Головне |
|---|---|---|
| [index.html](../app/web/index.html) | Оболонка: токен сесії, тема до першого кадру, заглушка «зв'язок втрачено» | — |
| [js/app.js](../app/web/js/app.js) | Бокова панель, маршрутизація сторінок, тема, серцебиття | `NAV`, `ROUTES`, `navigate()`, `applyTheme()`, `refreshInfo()` |
| [js/lib.js](../app/web/js/lib.js) | Спільні помічники: шаблони, API, підказки, діалоги, меню, анімації | `html()`, `api()`, `ib()`, `modal()`, `menu()`, `runJob()`, `upload()`, `toast()`, `segHtml()` |
| [js/icons.js](../app/web/js/icons.js) | Піктограми | `icon()` |
| [js/lightbox.js](../app/web/js/lightbox.js) | Переглядач зображень | `openLightbox()` |
| [js/handoff.js](../app/web/js/handoff.js) | Передача даних між сторінками в пам'яті | `give()`, `take()`, `waiting()` |
| [js/keep.js](../app/web/js/keep.js) | Збережена робота над новим замовленням: сховані картка й Order Creator, «чернетку створено» | `stash()`, `unstash()`, `settle()`, `markSent()`, `sentOf()` |
| [js/order-bits.js](../app/web/js/order-bits.js) | Спільне для Замовлень, архіву замовлень і Order Creator | `STAGES`, `statusChip()`, `trackChips()`, `receiptCopy()`, `isNameField()`, `planText()`, `pagesText()`, `addressFromEtsy()`, `syncOrders()`, `spreadsOf()`, `receiveDrop()`, `wireFolderDrop()`, `smoothWheel()` |
| [js/pages/orders.js](../app/web/js/pages/orders.js) | Замовлення: черга і картка | `mountQueue()`, `mountCard()` |
| [js/pages/library.js](../app/web/js/pages/library.js) | Галерея бібліотеки, нова книга, інструкція | `mount()`, `openAddBook()`, `saveGuide()` |
| [js/pages/book.js](../app/web/js/pages/book.js) | Паспорт книги | `mount()` |
| [js/pages/creator.js](../app/web/js/pages/creator.js) | Order Creator | `mount()` |
| [js/pages/archive.js](../app/web/js/pages/archive.js) | Архів замовлень: список, книга, передрук | `mount()`, `mountList()`, `mountBook()` |
| [js/pages/settings.js](../app/web/js/pages/settings.js) | Налаштування | `mount()` |
| [js/pages/profit.js](../app/web/js/pages/profit.js) | Прибуток (прихований) | `mount()` |
| [css/app.css](../app/web/css/app.css) | Уся візуальна система «Prepress» | — |
| `img/` | Іконки програми (`icon.ico`, `icon.png`, `icon-512.png`) | — |

## Тести: `app/tests/`

| Файл | Що перевіряє |
|---|---|
| [\_\_init\_\_.py](../app/tests/__init__.py) | Тимчасова папка даних замість справжньої |
| [test_profit.py](../app/tests/test_profit.py) | Паритет з Profit Calculator (`golden_profit.json`), комісії, імена |
| [test_states.py](../app/tests/test_states.py) | Стани замовлень, етапи, інкрементна синхронізація, API станів |
| [test_library_creator.py](../app/tests/test_library_creator.py) | Текст JSON, імпорт папки, перевірка файлів, запобіжники Printify/Gelato |
| [test_flows.py](../app/tests/test_flows.py) | Створення в Printify/Gelato з імітаціями, перетягування, захист Etsy, OAuth |
| [test_archive.py](../app/tests/test_archive.py) | Архів замовлень: копії файлів, 14/30 днів, «Не видаляти», передрук Printify/Gelato, позначка заміни |
| [test_orders.py](../app/tests/test_orders.py) | Правило друкарні, розстановка сторінок, довжина книги Gelato, інструкція, частковий імпорт, правило синхронізації |
| [test_wiki.py](../app/tests/test_wiki.py) | Вікі відповідає коду |

Детальніше — [dev/testing.md](dev/testing.md).

## Пов'язане

- [Будова сервера](architecture/server.md) · [Будова інтерфейсу](architecture/frontend.md) · [Маршрути](architecture/api-routes.md) · [Дані](architecture/data.md)
