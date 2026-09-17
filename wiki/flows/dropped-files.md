---
title: Перетягування папок і ZIP-архівів
type: flow
updated: 2026-09-17
code:
  - app/web/js/order-bits.js
  - app/studio/creator.py
---
# Перетягування папок і ZIP

> Вікно програми (браузер) не знає, де на диску лежить перетягнута папка. Тому її картинки (або ZIP)
> спершу **копіюються в програму**, у тимчасову папку, і далі програма працює з копією.

## Як це відбувається

1. Під час події `drop` треба одразу прочитати вміст — потім браузер його «забуває»
   ([order-bits.js](../../app/web/js/order-bits.js) `dropContents()`).
2. `receiveDrop()` створює сеанс (32 hex) і:
   - **ZIP** → одним запитом `POST /api/creator/drop/zip?session=&name=[&text=1]`; сервер зберігає
     архів поруч і розпаковує лише картинки (і `.json`, якщо `text=1`) у `<сеанс>/<назва архіву>/`;
   - **папка / файли** → кожен файл окремо `POST /api/creator/drop/file?session=&name=<відносний шлях>`,
     по 3 одночасно, з прогресом; окремі файли без папки кладуться в `Файли/`.
3. `POST /api/creator/drop/done {session}` → сервер повертає папку для роботи: найменш вкладену папку з
   `Cover.png`, інакше — єдину папку з картинками, інакше — корінь сеансу (`dropped_folder()`).
   Заодно стираються сеанси, старші за 2 години.
4. Далі: у картці замовлення — розстановка сторінок; в Order Creator — перевірка; у паспорті книги —
   «Імпорт з папки».

## Обмеження й захист

- Файл до 400 МБ, ZIP до 6 ГБ (розпаковано).
- Шляхи чистяться (`_drop_rel()`): без `..`, дисків, `__MACOSX`, `._*`, до 6 рівнів.
- Уся `data/tmp/dropped` стирається при кожному запуску (`clear_drops()`).
- Поле, над яким тягнуть файли, підсвічується (`drop-hot`); зона — елемент із `data-folder-drop`
  ([order-bits.js](../../app/web/js/order-bits.js) `wireFolderDrop()`).

## Де в коді

- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `dropContents()`, `receiveDrop()`, `dropLabel()`, `isZipDrop()`, `isFolderDrop()`, `filesInDrop()`, `wireFolderDrop()`, `collect()`
- [app/studio/creator.py](../../app/studio/creator.py) — `DROPS`, `clear_drops()`, `_drop_root()`, `_drop_rel()`, `extract_zip()`, `dropped_folder()`, `_drop_file()`, `_drop_zip()`, `_drop_done()`, `MAX_DROP_FILE`, `MAX_DROP_ZIP`
- [app/web/js/pages/orders.js](../../app/web/js/pages/orders.js) — `takeDrop()`
- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — `dropFolder()`
- [app/web/js/pages/book.js](../../app/web/js/pages/book.js) — `onDrop()`
- Тести: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`DroppedFolders`)

## Пов'язане

- [Назви файлів](../rules/file-naming.md) · [Наповнення бібліотеки](book-import.md) · [Order Creator](../features/order-creator.md)
