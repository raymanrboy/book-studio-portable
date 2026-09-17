---
title: Правило друкарні — Printify чи Gelato
type: rule
updated: 2026-09-17
code:
  - app/studio/orders.py
  - app/studio/reconcile.py
---
# Правило друкарні

> **Hardcover з доставкою в США → Printify, 24 сторінки. Усе інше → Gelato, 28 або 30 сторінок.**

| Замовлення | Друкарня | Сторінок | Формат Gelato |
|---|---|---|---|
| Hardcover, США | Printify | 24 | — |
| Hardcover, будь-яка інша країна | Gelato | 28 / 30 | `hardcover_8x8` |
| Softcover 5.5×5.5 (у полях є «5.5» або «5,5»), будь-куди | Gelato | 28 / 30 | `softcover_5x5` |
| Softcover, будь-куди | Gelato | 28 / 30 | `softcover_8x8` |
| Тип обкладинки не прочитався | вирішує власник (перемикач у картці) | 24 / 28–30 | — |

Для Gelato довжину визначають скачані файли (28 чи 30), а чи друкує Gelato 28 у цьому форматі —
його каталог ([integrations/gelato.md](../integrations/gelato.md)). У відповіді сервера `plan.pages` —
список: `[24]` або `[28, 30]` (`page_options()`).

## Чому так (слова власника)

- Printify швидкий і надійний у США, у нього гарні хардкавери; софткавери в Printify погані.
- Gelato чомусь із затримками робить хардкавери в США, а в інші країни і софткавери — вчасно й якісно.
- Кількість сторінок — це просто тип товару: Printify робить лише 24, Gelato — 30, а з 17.09.2026 і 28
  (без одного розвороту), якщо формат це дозволяє.

## Як визначається тип обкладинки

`binding_of()` бере мітку з `cover_label()`: спершу варіації покупця (hardcover / hard cover / hardback /
тверд…, softcover / soft cover / paperback / м'як…), потім SKU (`hard`, `-hc`, `soft`, `-sc`, `pb`…),
потім назву товару. Змішане або невідоме → `None` → друкарню обирає власник.

Країна — `country_iso` адреси доставки з чека Etsy.

## Відкрите питання

Правило збігається з 51 із 54 минулих замовлень. Винятки: 2 софткавери в США і 1 хардкавер у Канаду
друкувались у Printify. Свідомі винятки чи правило ширше — [open-questions.md](../plans/open-questions.md).

## Де в коді

- [app/studio/orders.py](../../app/studio/orders.py) — `plan_for()`, `binding_of()`, `page_options()`, `PRINTIFY_PAGES`, `_SMALL`
- [app/studio/creator.py](../../app/studio/creator.py) — `gelato_page_options()`
- [app/studio/reconcile.py](../../app/studio/reconcile.py) — `cover_label()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `planText()` (пояснення «Hardcover · США → Printify · 24 стор.», «… → Gelato · 28 або 30 стор.»), `pagesText()`
- [app/web/js/pages/orders.js](../../app/web/js/pages/orders.js) — `renderPlan()` (перемикач, коли тип невідомий)
- Тест: [app/tests/test_orders.py](../../app/tests/test_orders.py) (`PrinterRule`)

## Пов'язане

- [Замовлення](../features/orders.md) · [Printify](../integrations/printify.md) · [Gelato](../integrations/gelato.md) · [Рецепти](../recipes.md)
