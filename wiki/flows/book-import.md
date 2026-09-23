---
title: Filling the library — a new book and its files
type: flow
updated: 2026-09-23
code:
  - app/web/js/pages/book.js
  - app/web/js/pages/library.js
---
# Filling the library

> A book is added by its Etsy listing, and its files can come in at any time, in any pieces. Files can
> be prepared by an assistant or an AI agent, following the "agent guide".

## Steps

1. **Library → "+"** → a listing link → a check → "Create book"
   ([library.js](../../app/web/js/pages/library.js) `openAddBook()` → `POST /api/library/books`).
2. **Prepare the files**: "Guide" (the icon next to sorting) → "Save to file" (the file is highlighted
   in Explorer and can be dragged into an agent's chat), or "Copy"
   ([library.js](../../app/web/js/pages/library.js) `saveGuide()`, `copyGuide()`).
   An agent renames the pictures (`Cover.png`, `1.png`, `2-3.png`…`30.png`) and writes `book-text.json`.
3. **Load them into the passport** — any way works:
   - drag a **ZIP**, a **folder**, or **several files** (or pick them with "Add files") →
     a copy goes into the program along with the JSON → the same "Import from folder" dialog as the
     button ([book.js](../../app/web/js/pages/book.js) `onDrop()`, `importDropped()`, `importFolder()`)
     — one set of naming rules for every method;
   - the "Import from folder" button → pick a folder → the server lays it out and copies it in the
     background ([book.js](../../app/web/js/pages/book.js) `importFolder()`; the server —
     [library.py](../../app/studio/library.py) `scan_folder()`, `_folder_import()`);
   - one file onto a specific slot; `.json` — text only.
4. The dialog shows what goes where, what will **replace** what's already there, and what's skipped;
   individual slots can be unchecked.
5. After importing — previews and blurred placeholders are prepared right away; older files, in the
   background.

## Rules

- File naming — [rules/file-naming.md](../rules/file-naming.md); structure — [rules/book-structure.md](../rules/book-structure.md).
- A partial set is normal (pictures with no text, only illustration pages).
- The originals on disk are never changed: files are copied into `data/library/books/<id>/assets/`.
- Deleting an image only removes the library's copy.

## Where in the code

- [app/studio/library.py](../../app/studio/library.py) — `_create()`, `scan_folder()`, `_folder_scan()`, `_folder_import()`, `_upload_asset()`, `_import_text()`, `_store_asset()`, `_add_lqip()`, `_backfill_lqip()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `receiveDrop()` (a folder, ZIP, or files, with `withText`)
- [app/studio/drops.py](../../app/studio/drops.py) — `extract_zip()` (with `with_text`)
- Tests: [app/tests/test_orders.py](../../app/tests/test_orders.py) (`PartialBookImport`, `PreparationGuide`)

## Related

- [Library](../features/library.md) · [Dragging files](dropped-files.md)
