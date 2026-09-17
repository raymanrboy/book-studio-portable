---
title: Зіставлення замовлень і розрахунок прибутку
type: rule
updated: 2026-09-17
code:
  - app/studio/reconcile.py
  - app/studio/fees.py
  - app/studio/outcomes.py
---
# Зіставлення і прибуток

> Для кожного чека Etsy шукається замовлення друку (Printify/Gelato) — від цього залежать і етап
> у черзі, і прибуток. Правила й формули перенесені з Etsy Profit Calculator і збігаються до цента.

## Зіставлення (`match()`), по порядку

1. **Ручні зв'язки** (`links.json`): чек → замовлення, або «без собівартості» (`none`).
2. **Printify за номером чека**: у `metadata.shop_order_id` або в назві товару замовлення.
   Живі замовлення мають перевагу над скасованими; виграє перше в списку Printify.
3. **Printify за іменем одержувача** (`is_name_match()`: однакові, однакові перше й останнє слово,
   або одне містить інше від 4 символів); кілька — найближче за часом, живі першими.
4. **Gelato** за номером чека в `orderReferenceId`, потім за іменем.
5. Одне замовлення друку на кілька чеків = **посилка-бандл**, собівартість ділиться порівну.

Замовлення, позначені як передрук (заміна), у автоматичне зіставлення не беруться.

## Комісії Etsy (український продавець, `calculate_ukrainian_etsy_fees()`)

`Etsy Net = сума з картки − податок США − комісії`, де комісії:
- 6,5% від ціни товару (після знижки) + 20% ПДВ;
- 6,5% від доставки + 20% ПДВ;
- обробка платежу 6% від суми + $0,30, + 20% ПДВ;
- $0,20 за поновлення лістингу на кожен проданий товар + 20% ПДВ.

`Прибуток = Etsy Net − собівартість`; `Маржа = Прибуток / Etsy Net`. Округлення як у JavaScript
(`r2()`: половина вгору).

Собівартість: Printify — `total_price + total_shipping + total_tax` (центи); Gelato — `totalInclVat`,
EUR переводиться за курсом `eurUsdRate`.

## Стани (`outcomes.apply()`)

| Стан | Etsy Net | Собівартість |
|---|---|---|
| звичайне | як є | як є |
| скасовано | 0 (Etsy повертає комісії) | 0, якщо друк скасовано; інакше — втрата |
| повне повернення | −$0,20·1,2 (комісія лістингу не повертається) | лишається |
| часткове повернення | пропорційно повернутій частці | лишається |
| заміна (передрук) | як є | + вартість замовлень-передруків і/або ручна сума |

Скасовані замовлення друку і чернетки Gelato нічого не коштують. Якщо за іменем знайшлось лише
скасоване замовлення — рядок просить ручного зв'язку (`needs_link`).

## Де в коді

- [app/studio/reconcile.py](../../app/studio/reconcile.py) — `match()`, `is_name_match()`, `normalize_name()`, `cover_label()`, `gelato_cost_to_usd()`, `printify_only_rows()`, `_NameIndex`
- [app/studio/fees.py](../../app/studio/fees.py) — `calculate_ukrainian_etsy_fees()`, `r2()`, `money()`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `apply()`, `auto_state()`, `pod_order_info()`, `STATES`, `LABELS`
- [app/studio/profit.py](../../app/studio/profit.py) — `build_view()`, `reserved_orders()`
- Тести: [app/tests/test_profit.py](../../app/tests/test_profit.py) (`ProfitParity` проти `golden_profit.json`), [app/tests/test_states.py](../../app/tests/test_states.py)

## Пов'язане

- [Прибуток](../features/profit.md) · [Етапи](order-stages.md)
