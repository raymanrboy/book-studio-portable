---
title: Book library and a book's passport
type: feature
updated: 2026-09-27
code:
  - app/studio/library.py
  - app/web/js/pages/library.js
  - app/web/js/pages/book.js
  - app/studio/images.py
---
# Book library

> The reference version of every book in the shop: one book = one Etsy listing. A cover, 16 illustration
> slots, texts, a link to the Canva template. The order card finds a book by its listing number.
> A book's structure — [rules/book-structure.md](../rules/book-structure.md). A new book can also be made
> in the Listings mode's [Workshop](workshop.md) and passed here with its listing (since 2026-09-24).
> The library is the Orders mode's; it never lists a Workshop book.

## Gallery (`#/library`)

- Toolbar (`.lib-toolbar`): search (title or listing ID; Ctrl+F or `/`), a switch "In progress /
  Archive", sorting (recently changed, added, by title, incomplete first), an **agent guide** (save to a
  file or copy), a "+" button (a new book, key N) — the same height as the rest.
- A card: the thumbnail (or the cover), the title, `#listing`, a shield (the listing has been checked),
  readiness strips (cover, illustrations, texts, Canva), a check mark (the book is complete).
- Cards are built once; searching/filtering/sorting only hides and rearranges them with an animation
  (`flip()`), so pictures never reload. The chosen filter and sort are remembered (`bs-lib-view`).

## A new book

The `openAddBook()` dialog: a listing link or ID → checked via the Etsy API (keys are needed, sign-in
isn't) → title, photo, status, shop; a warning if the listing belongs to another shop. Without keys, or
on an error — a book can still be added without checking, by giving a title. Optional: a Canva link, the
listing's photo as a thumbnail. A duplicate by listing isn't created (the existing book opens instead).

The same dialog, with a book given to it (`openAddBook(existing, transfer)`), is the Workshop's **«Передати в
бібліотеку»** (since 2026-09-24): no title or Canva fields, what the book still lacks on top, the listing field
and its check as here, «Передати в бібліотеку» → `POST /api/workshop/books/<id>/to-library`
([workshop](workshop.md#передати-в-бібліотеку)). The Workshop's books are not library books: they live in
`pipeline/books/`, and the library book is made only at this moment (since 2026-09-26).

## A book's passport (`#/book/<id>`)

- **Header**: the thumbnail (can be taken from the listing's main photo), the title (edited in place), a
  `#listing` chip (**text only, not a link** — so Etsy is never opened by accident), a Canva button (open
  or add a link), the listing's status, "in archive", readiness indicators.
- **Cover** + the cover text.
- **Texts — the reference for the [text check](text-check.md)**: they have to match the Canva template
  word for word (headings, the order of the verses, capitalization). If they don't, the order card
  offers "Update passport" — the cover's and spreads' texts are taken from the printed book
  (2026-09-19; `update_texts()`).
- **Pages**: 16 rows — the dedication (1), spreads 2–15, the afterword (30). Each row: text on the left
  (copy, edit; `{Name}`/`{Gifter}` highlighted) and an illustration on the right: either a whole spread,
  or the left/right page separately (can be swapped). The endpapers are shown empty.
- **Actions** (top right): import from a folder, add files, the book's text (upload/paste JSON, copy the
  whole text or as JSON), "More": refresh from Etsy, the listing's photo as a thumbnail, a Canva link,
  export files to a folder, open the book's folder, archive, delete (to trash; refused while the book's folder
  import still runs — it would make the folder again without its `book.json`, the 2026-09-26 audit).
- **Drag and drop**: a picture onto a slot → goes there (a ZIP or a folder dropped on a slot is an import, like
  anywhere else on the page — it was refused as «не зображення» until the 2026-09-26 audit); a wide picture onto half a spread → becomes the
  whole spread; two files onto a spread → left and right; a single `.json` → text. **A folder, ZIP, or
  several files** (dropped, or via "Add files") → a copy into the program → the same "Import from
  folder" dialog and the same server rules (`scan_folder()`) as the "Import from folder" button
  (`importDropped()`). Before 2026-09-23, dropping had its own copy of the rules in the page
  (`mapFiles()`) and laid things out differently: it took whichever `.json` came last, and pictures from
  any subfolder (the 2026-09-22 audit).
- **A partial set** is normal: whatever's there goes into place; whatever's missing stays empty
  (pictures with no text, only some of the pages, Upscayl tails in file names).
- **Viewer**: click a picture; T — the page's text; a button — open the original in Windows.
- Esc — back to the library (if nothing is being edited).

Removed per the owner's decision: book notes (since 2026-09-27 not in the model or the API either; an old
`book.json` may still carry the field — it is left alone),
illustration filters, opening the Etsy listing. See [decisions](../decisions.md).

## The book model (`book.json`)

```json
{ "id": "<32 hex>", "schema": 1, "rev": 3, "title": "…", "createdAt": "…", "updatedAt": "…",
  "listing": {"id", "title", "state", "shopId", "url", "imageUrl", "verifiedAt"},
  "canvaUrl": "", "archived": false, "archivedAt": null,
  "cover": <asset|null>, "thumbnail": <asset|null>,
  "slots": { "page1": {"image"}, "spread2": {"image", "left", "right"}, …, "page30": {"image"} },
  "text":  { "cover", "page1", "spread2" … "spread15", "page30" },
  "workshop": "41.slug" }
```
`workshop` only on a book passed from the [Workshop](workshop.md) (since 2026-09-26): the folder of the Workshop
book it was made from, in `pipeline/books/`. (From 2026-09-24 to 26 a Workshop book was itself a library book
marked `"stage": "workshop"`, with its prompts; that model is gone.)
Asset: `{id, file, originalName, width, height, bytes, addedAt, lqip}`. `rev` guards against two windows
changing the same book at once (a `PATCH` with a stale `rev` → 409).

The passport redraws itself in place (since 2026-09-26): a saved text changes its own row, and a changed region
keeps the pictures it already showed — the whole row of pictures and the hero used to fade in again.

A picture is decoded and its previews made **outside the library's lock** (`_put_asset()`, since 2026-09-26): two
pictures dropped on one spread, or a text edit meanwhile, no longer wait up to ~1.5 s per picture.

**Write order** (since 2026-09-22): `book.json` is saved first, and only then is the old picture deleted
from disk. It used to be the other way around — if the write failed (disk, permissions), the picture was
already gone while the book still pointed at it (found by the audit). Now a failed write never costs a
single file.

## Agent guide

`agent_guide()` builds Markdown from the same rules as import: a table of file names (`Cover.png`,
`Thumbnail.png`, `1.png`, `2-3.png` or `2.png`+`3.png` … `30.png`), the `book-text.json` format
(`cover`, `page1`, `spreads` with keys "2"–"15", `page30`; `{Name}`, `{Gifter}`; `\n` for line breaks).
A test guarantees the guide and the importer never drift apart.

## Where in the code

- [app/studio/library.py](../../app/studio/library.py) — `load()`, `save()`, `summary()`, `completeness()`, `all_books()`, `create_book()`, `listing_of()`, `take_listing_image()`, `_store_asset()`, `_set_asset()`, `_parse_slot()`, `import_pictures()`, `scan_folder()`, `parse_text_json()`, `export_text_json()`, `export_book()`, `agent_guide()`, `_backfill_lqip()`, `SLOT_KEYS`, `TEXT_KEYS`, `LISTING_FIELDS`, `GUIDE_NAME`
- [app/web/js/pages/library.js](../../app/web/js/pages/library.js) — `mount()`, `card()`, `apply()`, `openAddBook()`, `saveGuide()`, `copyGuide()`, `SORTS`
- [app/web/js/pages/book.js](../../app/web/js/pages/book.js) — `mount()`, `renderHero()`, `renderCover()`, `rowHtml()`, `editText()`, `uploadTo()`, `importDropped()`, `importFolder()`, `importTextJson()`, `canvaDialog()`, `lightboxItems()`, `onDrop()`
- [app/studio/images.py](../../app/studio/images.py) — `preview()`, `lqip()`, `display_size()`, `compose_spread()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `dropContents()`, `receiveDrop()` (with `withText`: the JSON comes along too, and the return value is the dropped folder itself)
- Tests: [app/tests/test_library_creator.py](../../app/tests/test_library_creator.py) (`TextJson`, `FolderScan`), [app/tests/test_orders.py](../../app/tests/test_orders.py) (`PreparationGuide`, `PartialBookImport`), [app/tests/test_workshop.py](../../app/tests/test_workshop.py) (a Workshop book never in the library's list)

## Related

- [Book structure](../rules/book-structure.md) · [File naming](../rules/file-naming.md) · [Filling the library](../flows/book-import.md)
