---
title: Маршрути сервера
type: reference
updated: 2026-09-19
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
---
# Маршрути сервера

> Усі маршрути `@route` один до одного. Скрипт перевірки вікі порівнює цю таблицю з кодом:
> новий, змінений чи видалений маршрут треба відобразити тут.
> Доступ: `token` — заголовок сесії, `media` — `?t=` у посиланні, `none` — без токена.
> Шаблон — регулярний вираз із коду (символ `|` екрановано).

## Програма — [server.py](../../app/studio/server.py), [settings_api.py](../../app/studio/settings_api.py)

| Метод | Шаблон | Доступ | Функція | Хто викликає |
|---|---|---|---|---|
| GET | `/api/ping` | none | `_ping` | lib.js (перевірка «зв'язок втрачено»), main.py (друга копія програми) |
| POST | `/api/app/heartbeat` | token | `_heartbeat` | app.js кожні 20 с |
| POST | `/api/app/bye` | none | `_bye` | app.js при закритті вікна (токен у тілі) |
| GET | `/api/jobs/([0-9a-f]{12})` | token | `_job` | lib.js `runJob` |
| GET | `/api/app` | token | `_app` | app.js `refreshInfo` |
| GET | `/api/settings` | token | `_settings` | settings.js |
| POST | `/api/settings/ui` | token | `_ui` | app.js (тема, анімації) |
| POST | `/api/settings/etsy` | token | `_etsy_settings` | settings.js (адреса повернення) |
| POST | `/api/settings/gelato` | token | `_gelato_settings` | не викликається з інтерфейсу (лишився після спрощення Налаштувань) |
| POST | `/api/settings/printify` | token | `_printify_settings` | не викликається з інтерфейсу (лишився після спрощення Налаштувань) |
| POST | `/api/secrets` | token | `_secret` | settings.js (зберегти / видалити ключ) |
| POST | `/api/settings/legacy/import` | token | `_legacy_import` | settings.js (ключі зі старих програм) |
| POST | `/api/app/open-data` | token | `_open_data` | settings.js |
| POST | `/api/app/open-url` | token | `_open_url` | lib.js `openExternal` (Etsy заблоковано, крім входу) |
| POST | `/api/app/pick-folder` | token | `_pick_folder` | book.js, library.js |

## Замовлення — [orders.py](../../app/studio/orders.py)

| Метод | Шаблон | Доступ | Функція | Хто викликає |
|---|---|---|---|---|
| GET | `/api/orders` | token | `_list` | orders.js (черга) |
| GET | `/api/orders/(\d{5,20})` | token | `_one` | orders.js (картка; `earlierSends` — відправки цього замовлення, що не стали замовленням у друкарні) |
| POST | `/api/orders/(\d{5,20})/files` | token | `_files` | orders.js `arrange` (розстановка сторінок; для Gelato — ще й чи друкує він стільки сторінок у цьому форматі) |

## Перевірка тексту — [textcheck.py](../../app/studio/textcheck.py)

| Метод | Шаблон | Доступ | Функція | Хто викликає |
|---|---|---|---|---|
| POST | `/api/orders/(\d{5,20})/textcheck` | token | `_check` | orders.js `startCheck` (фонова задача; вимкнено в Налаштуваннях → `{off: true}`) |
| GET | `/api/textcheck/status` | token | `_status` | settings.js `loadTextcheck` (увімкнено, модель, чи відповідає Ollama) |
| POST | `/api/settings/textcheck` | token | `_save_settings` | settings.js (вмикач, модель) |
| POST | `/api/textcheck/start` | token | `_start` | settings.js «Запустити» Ollama |
| POST | `/api/textcheck/passport` | token | `_passport` | orders.js `learnPassport` (тексти обкладинки й розворотів у паспорт книги — лише кліком власника) |

## Бібліотека — [library.py](../../app/studio/library.py)

| Метод | Шаблон | Доступ | Функція | Хто викликає |
|---|---|---|---|---|
| GET | `/api/library/books` | token | `_list` | library.js |
| POST | `/api/library/books` | token | `_create` | library.js `openAddBook` |
| GET | `/api/library/guide` | token | `_guide` | library.js `copyGuide` |
| POST | `/api/library/guide/save` | token | `_guide_save` | library.js `saveGuide` |
| GET | `/api/library/books/([0-9a-f]{32})` | token | `_get` | book.js |
| PATCH | `/api/library/books/([0-9a-f]{32})` | token | `_patch` | book.js (назва, Canva, тексти; перевірка `rev`) |
| DELETE | `/api/library/books/([0-9a-f]{32})` | token | `_delete` | book.js (переносить у кошик) |
| POST | `/api/library/books/([0-9a-f]{32})/archive` | token | `_archive` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/refresh-listing` | token | `_refresh_listing` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/thumbnail-from-listing` | token | `_thumb_from_listing` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/assets` | token | `_upload_asset` | book.js (`?slot=&name=&auto=`, тіло — файл) |
| DELETE | `/api/library/books/([0-9a-f]{32})/assets` | token | `_remove_asset` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/swap` | token | `_swap_halves` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/text` | token | `_import_text` | book.js |
| GET | `/api/library/books/([0-9a-f]{32})/text.json` | token | `_text_json` | book.js («скопіювати як JSON») |
| POST | `/api/library/books/([0-9a-f]{32})/folder-scan` | token | `_folder_scan` | book.js `importFolder` |
| POST | `/api/library/books/([0-9a-f]{32})/folder-import` | token | `_folder_import` | book.js `importFolder` (фонова задача) |
| POST | `/api/library/books/([0-9a-f]{32})/export` | token | `_export` | book.js (фонова задача) |
| POST | `/api/library/books/([0-9a-f]{32})/open-folder` | token | `_open_folder` | book.js |
| POST | `/api/library/books/([0-9a-f]{32})/open-original` | token | `_open_original` | lightbox.js через book.js |
| GET | `/media/book/([0-9a-f]{32})/([0-9a-f]{32}\.(?:png\|jpg\|jpeg\|webp))` | media | `_media` | library.js, book.js, orders.js (`?w=` — прев'ю) |

## Order Creator і файли — [creator.py](../../app/studio/creator.py)

| Метод | Шаблон | Доступ | Функція | Хто викликає |
|---|---|---|---|---|
| GET | `/api/creator/status` | token | `_status` | creator.js |
| POST | `/api/creator/validate` | token | `_validate` | creator.js, orders.js (фонова задача) |
| POST | `/api/creator/pick-folder` | token | `_pick` | creator.js, orders.js |
| POST | `/api/creator/printify/create` | token | `_create_printify` | creator.js (фонова задача) |
| POST | `/api/creator/printify/reprint` | token | `_reprint_printify` | creator.js `create` у режимі передруку з архіву (фонова задача; нове замовлення на ту саму книгу; з відправки, що не стала замовленням, — 409) |
| POST | `/api/creator/gelato/create` | token | `_create_gelato` | creator.js (фонова задача; з `reprintOf` — чернетка-передрук з файлів архіву, лише з книги, що справді друкувалась) |
| GET | `/api/creator/gelato/page-counts` | token | `_gelato_page_counts` | creator.js `loadPageCounts` (скільки сторінок Gelato друкує в кожному форматі — з його каталогу) |
| POST | `/api/creator/gelato/close-tunnel` | token | `_close_tunnel` | creator.js |
| GET | `/api/creator/etsy-orders` | token | `_etsy_orders` | creator.js `fromEtsy` |
| POST | `/api/creator/open-folder` | token | `_open_folder` | creator.js, book.js |
| POST | `/api/creator/drop/file` | token | `_drop_file` | order-bits.js `receiveDrop` |
| POST | `/api/creator/drop/zip` | token | `_drop_zip` | order-bits.js `receiveDrop` |
| POST | `/api/creator/drop/done` | token | `_drop_done` | order-bits.js `receiveDrop` |
| GET | `/media/folder` | media | `_folder_media` | order-bits.js, creator.js, orders.js (`?path=&file=&w=`) |
| GET | `/media/folder-spread` | media | `_folder_spread` | order-bits.js `folderViewerItems` (`?path=&left=&right=&h=`) |

## Облік і синхронізація — [profit.py](../../app/studio/profit.py)

| Метод | Шаблон | Доступ | Функція | Хто викликає |
|---|---|---|---|---|
| POST | `/api/profit/sync` | token | `_start_sync` | order-bits.js `syncOrders`, profit.js (приєднується до вже запущеної) |
| GET | `/api/profit/sync` | token | `_sync_state` | order-bits.js `runningSync` |
| GET | `/api/profit/data` | token | `_data` | profit.js |
| GET | `/api/profit/row` | token | `_row` | profit.js |
| GET | `/api/profit/candidates` | token | `_candidates` | profit.js |
| POST | `/api/profit/links` | token | `_set_link` | profit.js |
| DELETE | `/api/profit/links` | token | `_delete_link` | profit.js |
| POST | `/api/profit/state` | token | `_set_state` | profit.js |

## Etsy — [etsy.py](../../app/studio/etsy.py)

| Метод | Шаблон | Доступ | Функція | Хто викликає |
|---|---|---|---|---|
| GET | `/api/etsy/status` | token | `_status` | settings.js (очікування входу) |
| POST | `/api/etsy/oauth/start` | token | `_oauth_start` | settings.js `oauthFlow` |
| POST | `/api/etsy/oauth/complete` | token | `_oauth_complete` | settings.js (вставлена адреса з київського ПК) |
| GET | `/etsy/callback` | none | `_oauth_callback` | браузер після входу в Etsy |
| POST | `/api/etsy/session/import` | token | `_session_import` | settings.js (лінк доступу) |
| GET | `/api/etsy/session/export` | token | `_session_export` | settings.js |
| POST | `/api/etsy/disconnect` | token | `_disconnect` | settings.js |
| GET | `/api/etsy/listing` | token | `_listing` | library.js (перевірка лістингу) |

## Printify і Gelato — [printify.py](../../app/studio/printify.py), [gelato.py](../../app/studio/gelato.py)

| Метод | Шаблон | Доступ | Функція | Хто викликає |
|---|---|---|---|---|
| POST | `/api/printify/test` | token | `_test` | settings.js |
| POST | `/api/printify/manual-approval` | token | `_manual_approval` | creator.js `confirmManualApproval` |
| GET | `/api/printify/shops` | token | `_shops` | settings.js `pickMaster` |
| GET | `/api/printify/products` | token | `_products` | settings.js `pickMaster` |
| POST | `/api/printify/master/analyze` | token | `_analyze` | settings.js `pickMaster` |
| POST | `/api/printify/master/save` | token | `_save_master` | settings.js `pickMaster` |
| POST | `/api/gelato/test` | token | `_test` | settings.js |

## Архів замовлень — [archive.py](../../app/studio/archive.py)

| Метод | Шаблон | Доступ | Функція | Хто викликає |
|---|---|---|---|---|
| GET | `/api/archive` | token | `_list` | archive.js (список; лише книги, чиє замовлення в друкарні оформлене й оплачене, та «Не видаляти») |
| GET | `/api/archive/(\d{8}-\d{6}-[0-9a-f]{6})` | token | `_one` | archive.js (сторінка книги; прихованої — 404) |
| POST | `/api/archive/(\d{8}-\d{6}-[0-9a-f]{6})/keep` | token | `_keep` | archive.js «Не видаляти» |
| POST | `/api/archive/(\d{8}-\d{6}-[0-9a-f]{6})/reuse` | token | `_reuse` | orders.js `takeEarlier` (робоча копія файлів минулої відправки в `tmp/dropped`) |

## Журнал відправок — [sendlog.py](../../app/studio/sendlog.py)

| Метод | Шаблон | Доступ | Функція | Хто викликає |
|---|---|---|---|---|
| POST | `/api/sends/open` | token | `_open` | creator.js `sendLogButton` (виділяє запис у Провіднику або відкриває папку) |

## Пов'язане

- [Сервер](server.md) · [Безпека](../security.md) · [Карта коду](../code-map.md)
