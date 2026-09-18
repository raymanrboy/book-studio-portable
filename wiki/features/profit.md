---
title: Прибуток (прихований до 1 жовтня)
type: feature
updated: 2026-09-18
code:
  - app/web/js/pages/profit.js
  - app/studio/profit.py
  - app/studio/reconcile.py
  - app/studio/outcomes.py
  - app/studio/fees.py
---
# Прибуток

> Повний аналог Etsy Profit Calculator: для кожного чека Etsy — чистий виторг Etsy мінус собівартість
> друку. **Сторінка прихована**: облік починається з 1 жовтня 2026. Модуль `profit.py` при цьому
> працює щодня — він синхронізує замовлення для черги.

## Стан

- `pages/profit.js` існує, але його немає ні в `NAV`, ні в `ROUTES` ([app.js](../../app/web/js/app.js)).
  Щоб показати: додати пункт у `NAV` і маршрут `#/profit` у `ROUTES` ([рецепт](../recipes.md)).
- Формули і правила зіставлення перевірені тестом проти коду оригіналу (`golden_profit.json`,
  результати до цента) — [rules/reconciliation.md](../rules/reconciliation.md).

## Що вміє сторінка

- Періоди (сьогодні, 7 днів, 30 днів, увесь час, свій), показники, таблиця по 50 рядків, пошук.
- Рядок розгортається: розбивка комісій, собівартість, стан.
- Ручне зіставлення з замовленням Printify/Gelato або «без собівартості».
- Стани: скасовано, повне/часткове повернення (сума), заміна (замовлення-передрук і/або сума).
- Кнопка синхронізації (і повна — з перечитуванням усіх чеків).

## Що працює й без сторінки

- **Передрук з [архіву замовлень](archive.md)** сам записує стан «заміна» для чека (`mark_reprint()`):
  нове замовлення друку додається в `replacementOrders`, тож зіставлення лишає за чеком перше
  замовлення (етап у черзі не стрибає), а передрук не рахується новим продажем. Чек зі станом
  «скасовано» чи «повернення» не чіпається.
- Після кожної синхронізації (`_sync()`) програма перевіряє архів замовлень —
  `archive.refresh_quietly()` видаляє книги, чиї 14 днів минули.

## Де в коді

- [app/web/js/pages/profit.js](../../app/web/js/pages/profit.js) — `mount()`, `kpi()`, `renderTable()`, `detailHtml()`, `sync()`, `saveState()`, `orderPicker()`, `openMatch()`, `openReplacement()`, `PERIODS`
- [app/studio/profit.py](../../app/studio/profit.py) — `build_view()`, `cached_view()`, `SLIM_FIELDS`, `_data()`, `_row()`, `_candidates()`, `_set_link()`, `_set_state()`, `_delete_link()`, `mark_reprint()`, `reserved_orders()`, `_sync()`
- [app/studio/reconcile.py](../../app/studio/reconcile.py) — `match()`, `printify_only_rows()`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `apply()`
- [app/studio/fees.py](../../app/studio/fees.py) — `calculate_ukrainian_etsy_fees()`
- Тести: [app/tests/test_profit.py](../../app/tests/test_profit.py), [app/tests/test_states.py](../../app/tests/test_states.py), [app/tests/test_archive.py](../../app/tests/test_archive.py) (`ReprintMark`)

## Пов'язане

- [Зіставлення і прибуток](../rules/reconciliation.md) · [Синхронізація](../rules/sync-policy.md) · [Відкриті питання](../plans/open-questions.md)
