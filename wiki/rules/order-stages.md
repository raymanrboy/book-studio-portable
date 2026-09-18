---
title: Етапи замовлення — нове, в роботі, відправлено друкарнею, відправлене
type: rule
updated: 2026-09-18
code:
  - app/studio/profit.py
---
# Етапи замовлення

> Etsy API не віддає власні вкладки продавця (у власника це «In Production»), тому етап виводиться
> з фактів: **«нове» — для чека ще немає оформленого й оплаченого замовлення в Printify або Gelato.**
> Чернетка, «on hold», неоплачене чи скасоване **не рахуються** (рішення власника 18.09.2026).
> Шлях: **Нові → В роботі (годинник) → машинка → Відправлені (коробка)**.

## Правило (`order_stage()`)

Спершу `print_order()` знаходить «живе» замовлення друку для чека: зіставлене, **оформлене**
(`is_placed()`: Printify — не `on-hold`, не `pending`, не `payment-not-received`, не скасоване; Gelato —
`orderType: order`, не чернетка, `financialStatus` не `draft` / `pending` / `canceled` / `refused`) і не
старе замовлення покупця, що повернувся (зіставлене **за іменем** і створене більш ніж на годину раніше
за чек). Далі:

| Умова (по порядку) | Етап | У черзі |
|---|---|---|
| Стан у обліку «скасовано» або «повне повернення» | `closed` | не показується |
| Etsy: відправлено (`is_shipped`) | `shipped` (+ друкарня, якщо є) | Відправлені (коробка) |
| Немає живого замовлення друку | `new` (або `work`, якщо вручну позначено «без собівартості») | Нові |
| Друкарня відправила: є трек-номер **або** статус із `SENT_STATUSES` | `sent` (+ друкарня) | машинка |
| Інакше | `work` (+ друкарня) | В роботі (годинник) |

`SENT_STATUSES`: Printify — `fulfilled`, `partially-fulfilled`; Gelato — `shipped`, `in_transit`,
`delivered`, `returned` (`gelato.SHIPPED`).

## Машинка (`sent`) — з 17.09.2026

Навіщо: бачити замовлення, які **вже можна позначати відправленими в Etsy** (рішення власника).
Власник позначає їх в Etsy вручну (на київському ПК) → після наступного оновлення Etsy віддає
`is_shipped` → замовлення йде в коробку. Статус `delivered` у друкарні з машинки **не** забирає —
лише позначка в Etsy.

## Як замовлення стає «в роботі»

- Gelato: `orderReferenceId` чернетки містить номер чека. Printify: номер чека в назві книги
  (`номер чека - ім'я`) і в `external_id` замовлення.
- Створена чернетка (Gelato) чи замовлення «On hold» (Printify) **ще не переводить** чек: він лишається
  в «Нових» з чипом статусу друкарні (`Draft`, `On hold`, `Created`…) — видно, що книгу вже відправлено
  і її треба підтвердити (`waiting_order()`). Скасоване в друкарні чипа не має.
- Власник підтверджує й оплачує в Printify («Submit order») чи Gelato → «Оновити»
  ([sync-policy.md](sync-policy.md)) → зіставлення ([reconciliation.md](reconciliation.md)) знаходить
  оформлене замовлення — і чек переходить у «В роботі».

Відомий пробіл: книга, створена в Printify **без** замовлення, чек не переводить. Ідея позначки
«товар уже створено» — у [планах](../plans/roadmap.md).

## Передрук етап не змінює (з 18.09.2026)

Передрук з [архіву замовлень](../features/archive.md) записується як заміна (`mark_reprint()`), а
замовлення-заміни не беруть участі в автоматичному зіставленні (`reserved_orders()`). Тому чек лишається
на своєму етапі (зазвичай «Відправлені» — книга вже була в покупця), а друге замовлення друку не
займає місце першого. Виняток — перше замовлення скасоване в друкарні: тоді передрук заміною не
позначається, зіставляється як звичайне, і чек переходить з «Нових» у «В роботі».

## Статус і трек-номер для черги

`picker_orders()` віддає для кожного замовлення з живим замовленням друку (а в «Нових» — для чернетки
чи неоплаченого, що чекає підтвердження в друкарні):
- `printStatus` — статус **рівно так, як його пише Printify чи Gelato**, англійською, без перекладу
  (бажання власника); окремих позначок для чернеток немає (Gelato `draft`, Printify `on-hold` — як є);
- `tracking` — `[{carrier, number, url}]`; перевізник Printify приходить кодом (`usps`) і
  перетворюється на назву (`carrier_label()`: USPS, FedEx, Royal Mail…), у Gelato це назва способу
  доставки («UPS Surepost»). Звідки береться — [Printify](../integrations/printify.md),
  [Gelato](../integrations/gelato.md).

## Де в коді

- [app/studio/profit.py](../../app/studio/profit.py) — `order_stage()`, `print_order()`, `waiting_order()`, `_matched_order()`, `is_placed()`, `PRINTIFY_NOT_PLACED`, `GELATO_NOT_PAID`, `placed_orders()`, `picker_orders()`, `carrier_label()`, `SENT_STATUSES`, `CARRIERS`, `HOUR_MS`, `mark_reprint()`, `reserved_orders()`
- [app/studio/gelato.py](../../app/studio/gelato.py) — `SHIPPED`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `STAGES`, `STAGE_EMPTY`, `STAGE_LABEL`
- [app/studio/creator.py](../../app/studio/creator.py) — `printify_order_payload()`, `create_gelato_draft()`
- Тести: [app/tests/test_states.py](../../app/tests/test_states.py) (`PickerStages` — чернетки, «on hold», неоплачене, `SentStage`)

## Пов'язане

- [Замовлення](../features/orders.md) · [Зіставлення](reconciliation.md) · [Синхронізація](sync-policy.md)
