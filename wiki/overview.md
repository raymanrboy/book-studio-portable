---
title: Огляд Book Studio
type: overview
updated: 2026-09-18
code:
  - app/studio/main.py
  - app/studio/core.py
---
# Огляд Book Studio

> Локальна Windows-програма власника магазину персоналізованих дитячих книг на Etsy. Вона веде кожне
> замовлення від Etsy до друку в Printify або Gelato і тримає еталонну бібліотеку книг.

## Бізнес у двох абзацах

Власник продає на Etsy персоналізовані книги: у тексті стоїть ім'я дитини, на першій сторінці —
присвята, наприкінці — «від кого». Покупець заповнює поля персоналізації в Etsy. Власник робить копію
шаблону книги в Canva, підставляє ім'я пошуком із заміною `{Name}`, скачує сторінки PNG і відправляє
книгу в друк: **Printify** (хардкавери в США, 24 сторінки) або **Gelato** (усе інше, 30 сторінок або 28 без одного розвороту) —
див. [правило друкарні](rules/printer-rule.md).

Власник не програміст, пише українською і працює з двох комп'ютерів: **вроцлавського** (щоденна робота,
тут запущена програма) і **віддаленого київського**, де зареєстрований магазин Etsy. Сторінки Etsy
відкриваються лише на київському — див. [безпеку](security.md). Сама програма на київському ПК не
запускається.

## Розділи програми

| Розділ | Що робить | Сторінка вікі |
|---|---|---|
| Замовлення (стартовий екран) | Черга нових замовлень Etsy і картка замовлення: книга, Canva, персоналізація, файли, звірка, передача в друк | [features/orders.md](features/orders.md) |
| Бібліотека книг | Еталон кожної книги: обкладинка, 16 сторінок/розворотів, тексти, посилання на Canva | [features/library.md](features/library.md) |
| Order Creator | Неопублікована книга (і замовлення On hold) у Printify, чернетка замовлення в Gelato | [features/order-creator.md](features/order-creator.md) |
| Архів замовлень | Файли книг, що пішли в друк: звірка й передрук; живуть 14 днів після «Відправлених» | [features/archive.md](features/archive.md) |
| Налаштування | Ключі сервісів, підключення Etsy, шаблон Printify, папка даних | [features/settings.md](features/settings.md) |
| Прибуток (прихований до 1 жовтня) | Аналог Etsy Profit Calculator: Etsy Net мінус собівартість друку | [features/profit.md](features/profit.md) |

## Як влаштовано

- **Сервер** — Python (стандартна бібліотека + Pillow, img2pdf, cryptography) слухає лише `127.0.0.1`.
  Див. [architecture/server.md](architecture/server.md).
- **Інтерфейс** — HTML/CSS/JS без збірки, відкривається як окреме вікно Edge (`--app`).
  Див. [architecture/frontend.md](architecture/frontend.md).
- **Дані** — у `app/data/` (не в git): книги, знімок замовлень, ключі (DPAPI), кеш, журнали.
  Див. [architecture/data.md](architecture/data.md).
- **Запуск і завершення** — [architecture/runtime.md](architecture/runtime.md).
- **Сервіси** — [Etsy](integrations/etsy.md) (лише читання), [Printify](integrations/printify.md),
  [Gelato](integrations/gelato.md), [Canva](integrations/canva.md) (лише посилання).

## Попередні інструменти

Book Studio замінює три старі програми, які лежать поруч на робочому столі:
- **Etsy Profit Calculator** — формули прибутку перенесено один в один і звірено тестами
  ([features/profit.md](features/profit.md));
- **Order Creator Printify** — його логіку створення книги перенесено в Order Creator;
- **Etsy OS** — невдала спроба конвеєра замовлень; досвід врахований у
  [рішеннях](decisions.md) («одне замовлення — один екран»).
Ключі з перших двох можна перенести кнопкою в Налаштуваннях.

## Репозиторій

```
Book Studio/            ← корінь git (приватний GitHub: raymanrboy/book-studio)
  AGENTS.md, CLAUDE.md  ← правила для агентів
  app/                  ← програма (див. карту коду)
  wiki/                 ← ця вікі
```

## Де в коді

- [app/studio/main.py](../app/studio/main.py) — `main()`: точка входу сервера.
- [app/studio/core.py](../app/studio/core.py) — `APP_NAME`, `DEFAULT_PORT`, `ROOT`, `DATA_DIR`.
- Повна карта файлів — [code-map.md](code-map.md).

## Пов'язане

- [Словник](glossary.md) · [Як працювати з власником](owner/working-with-owner.md) · [Рішення](decisions.md)
