---
title: Book library and a book's passport
type: feature
updated: 2026-11-12
code:
  - app/studio/library.py
  - app/studio/library_files.py
  - app/studio/library_guide.md
  - app/web/js/pages/library.js
  - app/web/js/pages/book.js
  - app/web/js/pages/book-dialogs.js
  - app/web/js/add-book.js
  - app/web/js/book-tile.js
---
# Book library

> The reference version of every book in the shop: one book = one Etsy listing = a cover, 16 illustration slots, texts and a link to the Canva template. The order card finds a book by its listing number. It is the **«Бібліотека»** tab of «Книги» (`#/books/shop`, its archive `#/books/archive`), beside «Майстерня» ([rail](rail.md)). A book made in the [Workshop](workshop.md) and passed on shows its cover and pages from the Workshop's folder.

The `book.json` schema is in [data](../architecture/data.md); file names and import rules in [book files](../rules/book-files.md).

## Gallery
- «Книги» (`pages/books.js`) shows the tabs Майстерня · Бібліотека · Архів with counts; the chosen tab's gallery is drawn without its own head. The library never lists a Workshop book that is not passed on.
- Toolbar: search (title or listing ID; Ctrl+F or `/`), switch In progress / Archive, sort (recently changed, added, title, incomplete first; remembered), **agent guide** (save to a file or copy), «+» (key N).
- A card is the Workshop's tile (`book-tile.js`): square cover, title, `#listing` with a shield when the listing was checked, one bar of four segments (cover, illustrations, texts, Canva), a check on the cover when complete.
- Cards are built once; search, filter and sort only hide and rearrange them, so pictures never reload.

## A new book
`openAddBook()`: a listing link or ID is checked through the Etsy API (keys are needed, sign-in is not) and fills title, photo, status and shop; a listing of another shop gets a warning. Without keys, or on an error, a book can be added by title alone. Optional: a Canva link, the listing photo as thumbnail. A duplicate by listing is not created — the existing book opens. «Створити» always answers: it names what is missing and lights the field.

The same dialog in its passing-on form is the Workshop's «Передати в бібліотеку» ([workshop](workshop.md)).

## A book's passport (`#/book/<id>`)
- **Header**: thumbnail (can be taken from the listing photo), title edited in place, a `#listing` chip, a Canva button (open or add a link), listing status, archive mark, readiness.
- **Texts** are the reference for the [text check](text-check.md): they match the Canva template word for word. When they do not, the order card offers «Update passport».
- **Pages**: 16 rows — dedication (1), spreads 2–15, afterword (30). Each row: text left (`{Name}`/`{Gifter}` lit, editable), illustration right — a whole spread or the left/right page separately. Endpapers show empty.
- **Actions**: import from a folder, add files, the book's text (upload/paste JSON, copy as text or JSON); «More»: refresh from Etsy, listing photo as thumbnail, Canva link, export files, open the folder, archive, delete.
- **Drops**: a picture onto a slot goes there; a wide picture onto half a spread becomes the whole spread; two files onto a spread become left and right; one `.json` is the text; a folder, ZIP or several files open the same «Import from folder» dialog and the same `scan_folder()` rules. A partial set is normal: what is there goes into place, the rest stays empty. Upscayl tails in names are ignored.
- **Viewer**: click a picture; `T` shows the page text; a button opens the original in Windows.
- Esc and «back» return to the book's tab in «Книги» when nothing is being edited.
- **Delete is without a question**: the book goes to the trash at once and a «Скасувати» toast (9 s) restores it (`POST /api/library/trash/restore`). Delete is refused while the book's folder import still runs. A picture's delete is a set-aside: the file goes to `data/library/trash-assets/<book>/` with a note of its slot, and «Скасувати» puts it back only into a slot that is empty now. Nothing in `trash-assets/` is ever deleted by the program.

Not in the program: book notes, illustration filters, opening the Etsy listing.

## Pages from the Workshop (`pagesFrom: "workshop"`)
- The cover and pages are the Workshop book's files in `pictures/`, not a copy. `load()` calls `follow()`, which makes the slots match what the folder holds now: a record is made only for a new or changed file, with a **new id** (so no old picture stays cached), written without a new `rev` (an open passport is not refused because a Workshop page changed). `asset_path()` says where a file is; a Workshop file is never deleted from the library.
- Here they are shown only: no import, add, replace, delete or swap on them, a dropped picture is turned away, and the server refuses a write too (`_own_slot()`, 409). «Змінити в Майстерні» sits beside «Сторінки» and on an empty place; «More» → «Відкрити папку сторінок (Майстерня)»; export takes the pages from there.
- The thumbnail and the texts belong to the passport (the texts are copied once when passing on; the two places do not follow each other).
- The Workshop folder gone (renamed by hand): an amber note replaces the pages; no file is lost.
- **The Workshop book deleted**: `keep_pages()` first copies the pages here (same file names, same addresses); a failed copy stops the deletion. Deleting the library book leaves the Workshop's pages as they are.
- At every launch `link_workshop_books()` runs in the background: a library book that holds its own copy of Workshop pages is moved onto the Workshop's files when every copied page equals the Workshop file byte for byte; the copies go to the Recycle Bin in one folder. A book with a page that differs keeps its own.

## Agent guide
`agent_guide()` builds Markdown from the importer's own rules: a table of file names (`Cover.png`, `Thumbnail.png`, `1.png`, `2-3.png` or `2.png`+`3.png` … `30.png`) and the `book-text.json` format. The wording is in `app/studio/library_guide.md`; `$table` and `$json` are filled in by the code. A test keeps the guide and the importer in step.

## Why
- One place, no doubles: a Workshop book's pages live once, in `pictures/`.
- `book.json` is written before an old picture is deleted, so a failed write never costs a file.
- The listing chip is text, not a link, so Etsy is never opened by accident.
- A picture is decoded and previewed outside the library's lock: two drops or a text edit do not wait for each other.
- `rev` guards two windows editing one book (stale `PATCH` → 409).
- The receipt number is its own field; a different number on upload is rejected.

## Where in the code
- [app/studio/library.py](../../app/studio/library.py) — `load()`, `save()`, `create_book()`, `follow()`, `keep_pages()`, `link_workshop_books()`
- [app/studio/library_files.py](../../app/studio/library_files.py) — `scan_folder()`, `parse_text_json()`, `export_book()`, `agent_guide()`
- [app/web/js/pages/library.js](../../app/web/js/pages/library.js) — `mount()`, `SORTS`
- [app/web/js/pages/book.js](../../app/web/js/pages/book.js) — `mount()`, `importDropped()`
- [app/web/js/add-book.js](../../app/web/js/add-book.js) — `openAddBook()`

## Related
- [Workshop](workshop.md) · [Data](../architecture/data.md) · [Book files](../rules/book-files.md) · [Text check](text-check.md) · [Intake](../flows/intake.md)
