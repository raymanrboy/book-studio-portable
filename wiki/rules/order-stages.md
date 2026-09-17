---
title: Етапи замовлення — нове, в роботі, відправлене
type: rule
updated: 2026-09-17
code:
  - app/studio/profit.py
---
# Етапи замовлення

> Etsy API не віддає власні вкладки продавця (у власника це «In Production»), тому етап виводиться
> з фактів: **«нове» — для чека ще немає замовлення в Printify або Gelato.**

## Правило (`order_stage()`)

| Умова (по порядку) | Етап | У черзі |
|---|---|---|
| Стан у обліку «скасовано» або «повне повернення» | `closed` | не показується |
| Etsy: відправлено (`is_shipped`) | `shipped` | Відправлені |
| Немає зіставленого замовлення друку | `new` (або `work`, якщо вручну позначено «без собівартості») | Нові |
| Зіставлене замовлення друку скасоване | `new` — книгу ще треба зробити | Нові |
| Зіставлене **за іменем** замовлення створене більш ніж на годину раніше за чек | `new` — це старе замовлення покупця, що повернувся | Нові |
| Інакше | `work` (+ яка друкарня) | В роботі |

## Як замовлення стає «в роботі»

- Gelato: `orderReferenceId` чернетки містить номер чека.
- Printify: номер чека в назві книги (`номер чека - ім'я`) і в `external_id` замовлення.
- Після наступної синхронізації ([sync-policy.md](sync-policy.md)) зіставлення ([reconciliation.md](reconciliation.md))
  знаходить замовлення друку — і чек переходить у «В роботі».

Відомий пробіл: книга, створена в Printify **без** замовлення, чек не переводить. Ідея позначки
«товар уже створено» — у [планах](../plans/roadmap.md).

## Де в коді

- [app/studio/profit.py](../../app/studio/profit.py) — `order_stage()`, `picker_orders()`, `HOUR_MS`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `STAGES`, `STAGE_EMPTY`
- [app/studio/creator.py](../../app/studio/creator.py) — `printify_order_payload()`, `create_gelato_draft()`
- Тест: [app/tests/test_states.py](../../app/tests/test_states.py) (`PickerStages`)

## Пов'язане

- [Замовлення](../features/orders.md) · [Зіставлення](reconciliation.md) · [Синхронізація](sync-policy.md)
