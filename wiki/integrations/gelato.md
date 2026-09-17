---
title: Gelato і тимчасове посилання
type: integration
updated: 2026-09-17
code:
  - app/studio/gelato.py
  - app/studio/tunnel.py
---
# Gelato

> Друкує **усе, крім хардкаверів у США**: хардкавери в інші країни і софткавери будь-куди (30 сторінок).
> Програма створює лише **чернетки** замовлень. API: `order.gelatoapis.com/v4`, `product.gelatoapis.com/v3`,
> ключ у заголовку `X-API-KEY`.

## Формати (`settings.gelato.formats`)

| Ключ | Назва | Коли |
|---|---|---|
| `hardcover_8x8` | Hardcover 8×8 | хардкавер не в США |
| `softcover_8x8` | Softcover 8×8 | софткавер |
| `softcover_5x5` | Softcover 5.5×5.5 | софткавер, якщо в полях є «5.5» |

Кожен має `productUid` фотокниги (матова ламінація). Сторінок — 30 (`pageCount`); Gelato вміє від 30
(можливо колись 28 — [плани](../plans/roadmap.md)).

## Файл книги

Фотокнига в Gelato приймає **один багатосторінковий PDF** типу `default`: обкладинка (задня + корінець +
лицьова), порожній форзац, сторінки, порожній нахзац. Розміри сторінок у мм беруться з каталогу
(`photobook_geometry()`). Тип `inside` — лише для листівок: колись через нього Gelato заповнив усі
сторінки обкладинкою (виправлено, див. [рішення](../decisions.md)).

## Тимчасове посилання

Gelato забирає файли **тільки за URL** і лише тоді, коли чернетку відкривають у Dashboard.
Тому `FileTunnel`:
1. піднімає локальний сервер, що віддає рівно `book.pdf` (без списку файлів);
2. запускає `app/bin/cloudflared.exe tunnel --url …` (Cloudflare quick tunnel, без акаунта) і чекає
   адресу `https://*.trycloudflare.com`, потім перевіряє, що файл справді віддається;
3. `TunnelRegistry.keep()` тримає посилання 15 хв (`tunnelKeepAliveSeconds`), потім закриває його і
   стирає `data/tmp/gelato/<сеанс>`. Кнопка «Файли забрано» закриває раніше.
Програма не завершиться, поки посилання активне. Немає `cloudflared.exe` → Order Creator попереджає.

## Чернетка

`orderType: draft` (примусово), `orderReferenceId: <чек>-<сеанс>` — за ним синхронізація знаходить
чек, і замовлення переходить у «В роботі». Чернетки в обліку не рахуються як витрата.

## Синхронізація

`all_orders()` — пошук замовлень (`orders:search`) по 100, до 5000; `slim_order()`. Вартість у EUR
перераховується за курсом `eurUsdRate` (1.085).

## Де в коді

- [app/studio/gelato.py](../../app/studio/gelato.py) — `ORDER_API`, `PRODUCT_API`, `_FORBIDDEN`, `_allowed()`, `call()`, `search_orders()`, `all_orders()`, `slim_order()`, `photobook_geometry()`, `create_draft_order()`, `get_order()`
- [app/studio/tunnel.py](../../app/studio/tunnel.py) — `CLOUDFLARED`, `FileTunnel`, `TunnelRegistry`, `cleanup_stale()`
- [app/studio/creator.py](../../app/studio/creator.py) — `create_gelato_draft()`, `build_photobook_pdf()`, `_one_idat()`
- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — `renderTunnels()`, `startCountdown()`
- Тести: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`GelatoDraftFlow`), [app/tests/test_library_creator.py](../../app/tests/test_library_creator.py) (`SafetyRails`)

## Пов'язане

- [Order Creator](../features/order-creator.md) · [Безпека](../security.md) · [Правило друкарні](../rules/printer-rule.md)
