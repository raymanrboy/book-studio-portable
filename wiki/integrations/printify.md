---
title: Printify
type: integration
updated: 2026-09-17
code:
  - app/studio/printify.py
---
# Printify

> Друкує **хардкавери для США** (24 сторінки). Магазин CozyCovenant, шаблон «Hardcover 8x8 Template»
> (Master). API `https://api.printify.com/v1`, токен — Personal Access Token.

## Що можна

| Дія | Шлях API | Коли |
|---|---|---|
| Читати магазини, продукти, замовлення, завантаження, каталог | `GET shops.json`, `shops/{id}/products…`, `shops/{id}/orders.json`, `uploads/{id}.json`, `catalog/…` | завжди |
| Завантажити зображення (base64) | `POST uploads/images.json` | створення книги |
| Створити неопублікований продукт | `POST shops/{id}/products.json` | створення книги |
| Створити замовлення «On hold» | `POST shops/{id}/orders.json` | лише `create_order_on_hold()`, після підтвердження Manual |

Усе інше заблоковано в `_check()` ([безпека](../security.md)).

## Як працює замовлення з API

- Замовлення, створене через API, Printify тримає **«On hold»**. У виробництво (і оплата) воно йде
  згідно з налаштуванням магазину *Order submission / Order approval*: **Manual** — лише після
  «Submit order» у Printify; автоматичні варіанти — самі через заданий час. У магазині власника
  стоїть **Manual** (скриншот від 15.09.2026), і програма один раз просить це підтвердити.
- Поля: `external_id` (`<чек>-<8 символів>`), `label` (назва книги), `line_items`
  (`product_id` + `variant_id` матового варіанту + `quantity` 1), `shipping_method: 1` (стандартна),
  `is_printify_express: false`, `send_shipping_notification: false`, `address_to` (`first_name`,
  `last_name`, `address1`, `address2`, `city`, `region`, `zip`, `country`, `phone`).
- Фініш книги **завжди матовий**.
- Перше справжнє замовлення On hold ще не спостерігалось — див. [відкриті питання](../plans/open-questions.md).

## Master

- Налаштування `printify.master`: `productId`, `blueprintId` 2737, `printProviderId` 28, варіанти
  (8x8 Glossy/Matte увімкнені, 11x8.5 вимкнені), `placements` (x/y/scale/angle для `cover` і `page_1…page_24`).
- Розміри artwork: обкладинка 4672×2464, сторінка 4000×4000 (`coverSize`, `pageSize`).
- Нова книга = копія конфігурації Master з новими зображеннями (`build_printify_payload()`).
- Перед кожним створенням — знімок Master, після — перевірка, що він не змінився.

## Кеш завантажень

`data/creator/upload-cache.json`: SHA-256 файлу → ID зображення. Перед повторним використанням
перевіряється, що зображення ще є в Printify (`upload_exists()`).

## Синхронізація

`all_orders()` читає всі замовлення магазину (по 50, до 4 сторінок паралельно); `slim_order()` лишає
тільки поля для зіставлення, статус і (з 17.09.2026) `shipments` — трек-номери після відправки
(`carrier` кодом, напр. `usps`, `number`, `url`; без номера — не зберігаються). Вони вже є у списку
замовлень, окремих запитів не треба. Статус `fulfilled`/`partially-fulfilled` або трек-номер переводить
чек у вкладку з машинкою ([rules/order-stages.md](../rules/order-stages.md)).
Замовлення з номером чека в назві товару чи `shop_order_id` зіставляється
з чеком Etsy ([rules/reconciliation.md](../rules/reconciliation.md)).

## Посилання

- Продукт: `https://printify.com/app/product-details/<id>?fromProductsPage=1`
- Замовлення: `https://printify.com/app/orders` (адресу не перевірено на справжньому замовленні).

## Де в коді

- [app/studio/printify.py](../../app/studio/printify.py) — `_READ`, `_WRITE`, `_check()`, `call()`, `token()`, `shops()`, `product()`, `upload_exists()`, `all_orders()`, `slim_order()`, `upload_image()`, `create_product()`, `create_order_on_hold()`, `manual_approval_confirmed()`, `analyze_master()`, `_manual_approval()`
- [app/studio/creator.py](../../app/studio/creator.py) — `create_printify_draft()`, `build_printify_payload()`, `printify_order_payload()`, `matte_variant()`, `_master_fingerprint()`, `_remember_upload()`
- [app/studio/core.py](../../app/studio/core.py) — `DEFAULT_SETTINGS`
- [app/studio/profit.py](../../app/studio/profit.py) — `carrier_label()`, `CARRIERS`
- Тести: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`FakePrintify`, `PrintifyDraftFlow`), [app/tests/test_states.py](../../app/tests/test_states.py) (`SentStage`)

## Пов'язане

- [Order Creator](../features/order-creator.md) · [Безпека](../security.md) · [Правило друкарні](../rules/printer-rule.md)
