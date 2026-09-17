---
title: Наповнення бібліотеки — нова книга і файли
type: flow
updated: 2026-09-17
code:
  - app/web/js/pages/book.js
  - app/web/js/pages/library.js
---
# Наповнення бібліотеки

> Книга додається за лістингом Etsy, а файли — будь-коли й будь-якими частинами. Готувати файли може
> помічник або AI-агент за «інструкцією для агента».

## Кроки

1. **Бібліотека → «+»** → посилання на лістинг → перевірка → «Створити книгу»
   ([library.js](../../app/web/js/pages/library.js) `openAddBook()` → `POST /api/library/books`).
2. **Підготувати файли**: «Інструкція» (іконка біля сортування) → «Зберегти у файл» (файл виділяється
   в Провіднику, його можна перетягнути в чат агенту) або «Скопіювати»
   ([library.js](../../app/web/js/pages/library.js) `saveGuide()`, `copyGuide()`).
   Агент перейменовує картинки (`Cover.png`, `1.png`, `2-3.png`…`30.png`) і пише `book-text.json`.
3. **Завантажити в паспорт** — будь-який спосіб:
   - перетягнути **ZIP** → розпакування в програму разом із JSON → діалог «Імпорт з папки»
     ([book.js](../../app/web/js/pages/book.js) `onDrop()`, `importFolder()`);
   - перетягнути **папку** або **кілька файлів** → діалог «Розкласти файли по книзі», завантаження по
     одному ([book.js](../../app/web/js/pages/book.js) `importFiles()`, `mapFiles()`);
   - кнопка «Імпорт з папки» → вибір папки → сервер сам розкладає і копіює у фоні
     ([book.js](../../app/web/js/pages/book.js) `importFolder()`; сервер — [library.py](../../app/studio/library.py) `scan_folder()`, `_folder_import()`);
   - один файл на конкретне місце; `.json` — лише текст.
4. У діалозі видно, що куди ляже, що **замінить** наявне і що пропущено; галочками можна зняти окремі місця.
5. Після імпорту — прев'ю й розмиті заглушки готуються одразу; старим файлам — у фоні.

## Правила

- Назви файлів — [rules/file-naming.md](../rules/file-naming.md); будова — [rules/book-structure.md](../rules/book-structure.md).
- Частковий набір — норма (картинки без тексту, лише ілюстраційні сторінки).
- Оригінали на диску не змінюються: файли копіюються в `data/library/books/<id>/assets/`.
- Видалення зображення прибирає лише копію в бібліотеці.

## Де в коді

- [app/studio/library.py](../../app/studio/library.py) — `_create()`, `scan_folder()`, `_folder_scan()`, `_folder_import()`, `_upload_asset()`, `_import_text()`, `_store_asset()`, `_add_lqip()`, `_backfill_lqip()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `receiveDrop()` (ZIP з `withText`), `filesInDrop()`
- [app/studio/creator.py](../../app/studio/creator.py) — `extract_zip()` (з `with_text`)
- Тести: [app/tests/test_orders.py](../../app/tests/test_orders.py) (`PartialBookImport`, `PreparationGuide`)

## Пов'язане

- [Бібліотека](../features/library.md) · [Перетягування файлів](dropped-files.md)
