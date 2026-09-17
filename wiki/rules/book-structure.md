---
title: Будова книги — сторінки, розвороти, слоти
type: rule
updated: 2026-09-17
code:
  - app/studio/library.py
  - app/web/js/order-bits.js
---
# Будова книги

> Книга — обкладинка і 30 сторінок. Сторінка 1 — присвята (права, ліворуч форзац), розвороти 2–15 —
> сторінки 2–29, сторінка 30 — післяслово (ліва, праворуч нахзац). **Розворот N = сторінки 2N−2 і 2N−1.**

## Бібліотека (еталон, 30 сторінок)

| Слот (`SLOT_KEYS`) | Сторінки | Що |
|---|---|---|
| `cover` (окремо від слотів) | — | повний розворот обкладинки (задня + лицьова) |
| `thumbnail` (окремо) | — | заставка для галереї |
| `page1` | 1 | присвята, одне зображення |
| `spread2` … `spread15` | 2–3 … 28–29 | цілий розворот (`image`) **або** `left` + `right` |
| `page30` | 30 | післяслово, одне зображення |

Тексти (`TEXT_KEYS`): `cover`, `page1`, `spread2…spread15`, `page30` — 16 місць + обкладинка.
Книга «повна», коли є обкладинка, усі 16 ілюстрацій і всі 17 текстів (`completeness()`).

У кожному розвороті одна сторінка з текстом, друга — лише малюнок (важливо для [планів](../plans/roadmap.md)).

## Друк (папка для Order Creator)

- Файли: `Cover.png` + `1.png … N.png`, де N = 24 (Printify) або 28 чи 30 (Gelato — скільки скачано).
- Розвороти при перегляді (`spreadsOf()`): `[форзац | 1]`, `[2 | 3]`, `[4 | 5]`, …; останній —
  `[N | нахзац]` (24, 28 або 30).
- Для Printify з 30 сторінок шаблону прибираються **рівно 3 розвороти** (6 сторінок), для 28-сторінкової
  книги Gelato — **один** розворот; які саме — власник вирішує в Canva для кожної книги. Тоді номери
  файлів з Canva «з дірками» — програма перенумеровує їх по порядку ([file-naming.md](file-naming.md)).
  Прибирати треба цілий розворот (сторінки 2N−2 і 2N−1), інакше розвороти зсунуться — програма цього
  не перевіряє ([рішення](../decisions.md)).
- У Gelato PDF: обкладинка, порожній форзац, 28 або 30 сторінок, порожній нахзац (31 або 33 сторінки PDF).
  Без порожніх Gelato зсуває книгу на сторінку; у чернетці форзац видно як порожню «Page 0»
  ([integrations/gelato.md](../integrations/gelato.md)).

## Де в коді

- [app/studio/library.py](../../app/studio/library.py) — `SLOT_KEYS`, `TEXT_KEYS`, `SPREAD_NUMBERS`, `spread_pages()`, `slot_label()`, `_empty_slots()`, `completeness()`
- [app/web/js/pages/book.js](../../app/web/js/pages/book.js) — `SPREADS`, `SLOT_KEYS`, `pagesOf()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `spreadsOf()`, `folderViewerItems()`
- [app/studio/creator.py](../../app/studio/creator.py) — `expected_files()`, `build_photobook_pdf()`

## Пов'язане

- [Бібліотека](../features/library.md) · [Назви файлів](file-naming.md) · [Canva](../integrations/canva.md)
