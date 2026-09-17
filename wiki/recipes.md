---
title: Рецепти — як змінити типові речі
type: recipe
updated: 2026-09-17
code: []
---
# Рецепти

> Де саме міняти код для типових завдань і що не забути. Після кожного — тести, `wiki_check.py`,
> оновлені сторінки й запис у журналі ([правила](dev/wiki-rules.md)).

## Змінити правило друкарні
- [app/studio/orders.py](../app/studio/orders.py) — `plan_for()` (і `binding_of()`, якщо змінюється розпізнавання обкладинки)
- Тест `PrinterRule` у [app/tests/test_orders.py](../app/tests/test_orders.py).
- Пояснення в інтерфейсі — [app/web/js/order-bits.js](../app/web/js/order-bits.js) `planText()`.
- Вікі: [rules/printer-rule.md](rules/printer-rule.md), [decisions.md](decisions.md).

## Додати формат Gelato (наприклад, 28 сторінок чи новий розмір)
- [app/studio/core.py](../app/studio/core.py) — `DEFAULT_SETTINGS` (`gelato.formats`: `label`, `productUid`); збережені налаштування зливаються з типовими, тож новий ключ з'явиться сам.
- [app/studio/orders.py](../app/studio/orders.py) — `plan_for()`: коли вибирати формат.
- Кількість сторінок зараз одна на всі формати (`pageCount`) — інша кількість потребує змін у
  [app/studio/creator.py](../app/studio/creator.py) `expected_files()`, `create_gelato_draft()` і [app/studio/orders.py](../app/studio/orders.py) `pages_for()`.
- Order Creator показує формати зі статусу сам (`formatCard()`).

## Показати сторінку «Прибуток»
- [app/web/js/app.js](../app/web/js/app.js) — додати пункт у `NAV` (піктограма `chart`) і маршрут `#/profit` у `ROUTES`; зсунути гарячі клавіші.
- Вікі: [features/profit.md](features/profit.md), [architecture/frontend.md](architecture/frontend.md).

## Нова сторінка інтерфейсу
- Файл `app/web/js/pages/<назва>.js` з `export async function mount(view, params)` → `{ shown?, unmount }`.
- [app/web/js/app.js](../app/web/js/app.js) — `ROUTES` (і `NAV`, якщо потрібна піктограма в панелі).
- Стилі — у [app/web/css/app.css](../app/web/css/app.css), кольори лише з токенів.
- Вікі: нова сторінка в `features/`, рядок у [code-map.md](code-map.md) і `index.md`.

## Новий маршрут сервера
- `@route("METHOD", r"/api/...")` у потрібному модулі ([app/studio/server.py](../app/studio/server.py) `route()`).
- Новий модуль — додати в імпорт у [app/studio/main.py](../app/studio/main.py) `main()`, інакше маршрут не зареєструється.
- Довга дія — через `jobs.start()`, в інтерфейсі `runJob()`.
- Вікі: рядок у [architecture/api-routes.md](architecture/api-routes.md) (перевірка вимагає).

## Нова піктограма
- [app/web/js/icons.js](../app/web/js/icons.js) — додати шлях у мапу `P` (сітка 24×24, обведення 1,6); `icon()` її віддасть.
- Правило: одна піктограма — одне значення; не перевикористовувати наявну для іншого сенсу.

## Новий етап замовлення
- [app/studio/profit.py](../app/studio/profit.py) — `order_stage()`
- [app/web/js/order-bits.js](../app/web/js/order-bits.js) — `STAGES`, `STAGE_EMPTY`
- [app/web/js/pages/orders.js](../app/web/js/pages/orders.js) — `STAGE_LABEL`
- Тест `PickerStages` у [app/tests/test_states.py](../app/tests/test_states.py); вікі [rules/order-stages.md](rules/order-stages.md).

## Що показувати в записці звірки
- [app/web/js/pages/orders.js](../app/web/js/pages/orders.js) — `proofCard()` (фільтр `notes`), `isFormatField()`, `isNameField()`; розміри — `.proof-name`, `.proof-note` в app.css.

## Розмір мініатюр стрічки
- Змінювати **разом**: [app/web/js/pages/orders.js](../app/web/js/pages/orders.js) `STRIP_THUMB` і [app/studio/creator.py](../app/studio/creator.py) `STRIP_PREVIEW` (інакше сервер готуватиме не той розмір).

## Новий ключ сервісу
- [app/studio/vault.py](../app/studio/vault.py) `SECRET_NAMES`; [app/studio/settings_api.py](../app/studio/settings_api.py) `EDITABLE_SECRETS`; [app/web/js/pages/settings.js](../app/web/js/pages/settings.js) `SECRET_LABELS`.

## Нове налаштування
- [app/studio/core.py](../app/studio/core.py) `DEFAULT_SETTINGS` → маршрут у [app/studio/settings_api.py](../app/studio/settings_api.py) → поле в [app/web/js/pages/settings.js](../app/web/js/pages/settings.js) `mount()`.
- Пам'ятати: власник хоче мінімальні Налаштування ([owner/ui-principles.md](owner/ui-principles.md)).

## Дозволити новий виклик Printify або Gelato
- **Лише з прямого дозволу власника** і з оглядом безпеки.
- [app/studio/printify.py](../app/studio/printify.py) `_check()` (списки `_READ`, `_WRITE`); [app/studio/gelato.py](../app/studio/gelato.py) `_allowed()`.
- Тести `SafetyRails` у [app/tests/test_library_creator.py](../app/tests/test_library_creator.py); вікі [security.md](security.md).

## Змінити перевірку файлів Printify/Gelato
- [app/studio/creator.py](../app/studio/creator.py) — `expected_files()`, `validate()`; розміри Printify — у налаштуваннях (`coverSize`, `pageSize`) з аналізу Master.

## Пов'язане

- [Карта коду](code-map.md) · [Словник](glossary.md)
