---
title: Dragging folders and ZIP archives
type: flow
updated: 2026-09-26
code:
  - app/web/js/order-bits.js
  - app/web/js/app.js
  - app/studio/drops.py
---
# Dragging folders and ZIPs

> The program's window (a browser) doesn't know where on disk a dragged folder lives. So its pictures
> (or a ZIP) are **copied into the program** first, into a temp folder, and the program works with the
> copy from then on.

## How it happens

1. During the `drop` event, the contents have to be read right away — the browser "forgets" them right
   after ([order-bits.js](../../app/web/js/order-bits.js) `dropContents()`).
2. `receiveDrop()` creates a session (32 hex) and:
   - **ZIP** → one request `POST /api/drop/zip?session=&name=[&text=1]`; the server saves the
     archive alongside and unpacks only pictures (and `.json`, if `text=1`) into
     `<session>/<archive name>/`;
   - **folder / files** → each file its own `POST /api/drop/file?session=&name=<relative path>`,
     3 at a time, with progress; loose files with no folder go into `Files/`.
3. `POST /api/drop/done {session}` → the server returns the working folder: the least-nested
   folder with `Cover.png`, otherwise the one folder with pictures, otherwise the session's root
   (`dropped_folder()`). For the library (`receiveDrop(…, { withText: true })` → `text=1` on every file
   and `whole: true`) — **the dropped folder itself** (`dropped_top()`): import reads its
   `generated/`, `pages/`, and `book-text.json` too. This also clears sessions unused for 24 hours
   (`KEEP_UNUSED`; each check of a folder by the Order Creator or a card counts as a use — `drops.touch()`,
   so a card kept open all day never loses its folder; audit 2026-09-26, it was 2 hours from the drop).
4. Next: in the order card — laying out pages; in the Order Creator — checking; in a book's passport —
   "Import from folder" (the same way for a folder, a ZIP, and several files); in the
   [mockups utility](../features/mockups.md) — reading the demo book (`mockups.read_book()`).

All of this lives in its own module, [drops.py](../../app/studio/drops.py) (since 2026-09-23; before that in
creator.py, with the routes `/api/creator/drop/*`): the mockups utility takes it without the rest of Book
Studio. It runs with its own data folder, so its `tmp/dropped` is `app/data/mockups/tmp/dropped` — Book
Studio's launch never wipes a book dropped into the mockups window, and the other way round. There it
keeps **one book at a time** (the one before goes when another comes in, and all go when the window closes —
`mockups._only_this_book()`), and a ZIP picked with the folder button is unpacked straight from where it
lies, without going through the window (`drops.archive_folder()` names the folder, `extract_zip()` unpacks).

## Limits and protection

- A file up to 400 MB, a ZIP up to 6 GB (unpacked).
- Paths are sanitized (`_drop_rel()`): no `..`, no drive letters, no `__MACOSX`, no `._*`, up to 6 levels
  deep.
- All of `data/tmp/dropped` is wiped on every launch (`clear_drops()`).
- The field files are dragged over lights up (`drop-hot`); the zone is an element with `data-folder-drop`
  ([order-bits.js](../../app/web/js/order-bits.js) `wireFolderDrop()`).
- **Only files from outside the window** (since 2026-09-26): the browser hands a picture dragged from the page
  itself over as a file — its preview — so a Workshop spread dragged a little and let go replaced itself with a
  square of its own (the owner). `app.js` notes a drag that starts in the window (`dragstart`) and, before any page
  sees it, shuts every drop zone to it while it carries files (`dragenter`/`dragover`/`drop` stopped in the capture
  phase: no highlight, no drop). The mockups' own drags (spreads, slots) carry no files — their pictures are
  `draggable="false"` — and work as before.

## Where in the code

- [app/web/js/app.js](../../app/web/js/app.js) — `dragFromPage`, `ownPicture()`: a picture dragged from the window never drops back in
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `dropContents()`, `receiveDrop()`, `dropLabel()`, `wireFolderDrop()`, `collect()`
- [app/studio/drops.py](../../app/studio/drops.py) — `DROPS`, `clear_drops()`, `_drop_root()`, `_drop_rel()`, `extract_zip()`, `archive_folder()`, `dropped_folder()`, `dropped_top()`, `_drop_file()`, `_drop_zip()`, `_drop_done()`, `MAX_DROP_FILE`, `MAX_DROP_ZIP`
- [app/web/js/pages/orders.js](../../app/web/js/pages/orders.js) — `takeDrop()`
- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — `dropFolder()`
- [app/web/js/pages/book.js](../../app/web/js/pages/book.js) — `onDrop()`, `importDropped()`
- [app/web/js/pages/mockups.js](../../app/web/js/pages/mockups.js) — `takeDrop()`
- Tests: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`DroppedFolders`)

## Related

- [File naming](../rules/file-naming.md) · [Filling the library](book-import.md) · [Order Creator](../features/order-creator.md)
