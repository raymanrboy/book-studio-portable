---
title: Журнал відправок у Printify і Gelato
type: feature
updated: 2026-09-20
code:
  - app/studio/sendlog.py
---
# Журнал відправок

> Кожна спроба щось відправити в друкарню — книга/замовлення в Printify, чернетка в Gelato —
> записується окремим файлом: що пішло, які файли й PDF, що відповів сервіс, де зламалось.
> Попросив власник 17.09.2026, щоб «налаштувати механізм в ідеал». Ключів у журналі немає.

## Де

`app/data/logs/sends/РРРР-ММ-ДД_ГГХХСС_<printify|gelato>_<назва>.json`, останні 400 файлів
(`KEEP`). Відкрити — піктограма списку з крапками в Order Creator:
- **завжди** — у шапці, ліворуч від перемикача Printify/Gelato («Журнал відправок»): Провідник
  виділяє найновіший запис (`latest()`; власник не знайшов кнопку, коли вона була лише в картках);
- у картці результату — виділяє запис саме цієї відправки; у картці помилки — найновіший.

## Що в записі

| Поле | Що |
|---|---|
| `provider`, `kind`, `title`, `at`, `seconds` | куди (`printify` / `gelato`), що (`book`, `book+order`, `draft`), назва, час, тривалість |
| `ok`, `error`, `errorType` | чи вдалося; текст помилки, яку побачив власник |
| `folder`, `format`, `books` | папка з файлами і формат Gelato (першої книги); `books` — усі книги відправки (назва, папка, формат) |
| `steps` | кроки по порядку (нижче) |
| `request`, `response` | тіло запиту на створення і відповідь сервісу повністю (з адресою) |
| `orderRequest`, `orderResponse`, `orderError` | Printify: замовлення On hold |
| `result` | те, що побачив власник у картці результату |

Кроки: **Gelato** — `files` (кожен PNG: розмір у px, байти, помилки) → `catalog` (товар, кількість
сторінок, розміри з каталогу) → `pdf` (сторінок у PDF, байти, розмір обкладинки в px, на скільки мм
обріжеться) → `link` (адреси всіх PDF, `reachable`) → `readback` (що Gelato записав у чернетці: товар,
сторінки, файл і чи вже забраний — `fileFetched`). **Printify** — `files` (з SHA-256) → `master` →
`uploads` (перевикористані / нові, ID зображень за позиціями) → `product` (запит і відповідь на
створення) → `verify` (позиції) → `masterSafe` (Master не змінився).

**Замовлення з кількох книг** (з 20.09.2026) — один запис на всю відправку: покнижкові кроки
повторюються, і в кожного є поле `book` з назвою книги (`files`, `uploads`, `product`, `verify`,
`catalog`, `pdf`, `archive`); `orderRequest` один — замовлення спільне.

Запис робиться й тоді, коли відправка зупинилась на перевірці — тоді кроків менше, а `request` немає
(нічого не пішло). Якщо журнал не вдалося записати, відправка все одно відбувається.

## Безпека

- Ключі й токени в журнал не потрапляють: вони лише в заголовках запитів (перевіряють тести).
- Адреси покупців — так, тому журнал лише в `app/data` (не в git, [security.md](../security.md)).

## Де в коді

- [app/studio/sendlog.py](../../app/studio/sendlog.py) — `SENDS`, `KEEP`, `write()`, `attempt()`, `step()`, `latest()`, `_open()`
- [app/studio/creator.py](../../app/studio/creator.py) — `create_gelato_draft()`, `_gelato_draft()`, `_gelato_book()`, `_journal_readback()`, `create_printify_draft()`, `_printify_draft()`, `_printify_files()`, `_printify_images()`, `_printify_product()`, `_printify_order()`
- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — `renderSwitch()` (піктограма в шапці), `sendLogButton()`
- [app/web/css/app.css](../../app/web/css/app.css) — `.cr-tools`, `.mode-switch`
- [app/web/js/icons.js](../../app/web/js/icons.js) — піктограма `sendLog`
- Тести: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`PrintifyDraftFlow`, `GelatoDraftFlow` — у т. ч. `test_journal_button_shows_the_newest_record`)

## Пов'язане

- [Order Creator](order-creator.md) · [Gelato](../integrations/gelato.md) · [Printify](../integrations/printify.md) · [Дані](../architecture/data.md)
