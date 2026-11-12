---
title: Intake — dropped files and filling the library
type: flow
updated: 2026-11-12
code:
  - app/studio/drops.py
  - app/web/js/drop.js
  - app/web/js/drop-anywhere.js
  - app/web/js/app.js
  - app/web/js/pages/book.js
  - app/studio/library_files.py
---
# Intake

> The program's window (a browser) does not know where a dragged folder lives on disk, so dropped pictures or a ZIP are first **copied into the program** (a temp folder) and the program works with the copy. The same intake feeds the order card, the Order Creator, the mockups tool and a book's passport. Naming rules: [Book files](../rules/book-files.md).

## How a drop travels
1. During the `drop` event the contents must be read at once, the browser forgets them right after (`dropContents()`).
2. `receiveDrop()` makes a session (32 hex) and sends:
   - a **ZIP**: one `POST /api/drop/zip?session=&name=[&text=1]`; the server unpacks only pictures (and `.json` with `text=1`) into `<session>/<archive name>/`;
   - a **folder or files**: one `POST /api/drop/file?session=&name=<relative path>` per file, 3 at a time, with progress; loose files go to `Files/`.
3. `POST /api/drop/done {session}` returns the working folder (`dropped_folder()`): the least-nested folder with `Cover.png`, else the one folder with pictures, else the session root. For the library (`withText: true`) it is the dropped folder itself (`dropped_top()`), so `generated/`, `pages/` and `book-text.json` are read too.
4. The next step belongs to the page: the order card lays out pages, the Order Creator checks, a passport opens «Import from folder», the mockups tool reads a demo book (`mockups.read_book()`).

## Limits and protection
- `MAX_DROP_FILE` = 400 MB per file, `MAX_DROP_ZIP` = 6 GB unpacked. Paths are sanitized by `_drop_rel()` ([Book files](../rules/book-files.md)).
- `data/tmp/dropped` is wiped on every launch (`clear_drops()`); sessions unused for `KEEP_UNUSED` (24 h) go on the next check. Each check by the Order Creator or a card counts as a use (`drops.touch()`), so a card open all day keeps its folder.
- The mockups tool runs `drops.py` with its own data folder (`app/data/mockups/tmp/dropped`) and keeps one book at a time (`mockups._only_this_book()`); a ZIP picked with its folder button is unpacked in place (`archive_folder()`, `extract_zip()`).
- Drop zones are elements with `data-folder-drop`, highlighted with `drop-hot` (`wireFolderDrop()`).

## Drop anywhere
`installDropAnywhere()` accepts files over the whole window (a veil shows it). The page in view may take the drop (`bs:dropped`: the Order Creator as the current book's folder, the Mockups as the demo book). Otherwise one question «Куди?» offers the two destinations (Mockups, Order Creator); the program never chooses, and nothing is copied until a place is picked. The choice hands the files over (`give('creator'|'mockups', {drop})`) and opens that page, which does its own intake.

## Only files from outside the window
A picture dragged from the page itself reaches the browser as a file (its preview). `app.js` notes a drag that starts in the window (`dragFromPage`, `ownPicture()`) and shuts every drop zone to it, so a Workshop spread never replaces itself. The mockups' own drags carry no files and work as usual.

## Filling the library
A book is added by its Etsy listing and its files can arrive any time, in any pieces. A book made from scratch can start in the [Workshop](../features/workshop.md) and come over with «Передати в бібліотеку» (texts copied once; the pages stay the Workshop's files).
1. **Library → "+"** → listing link → check → "Create book" (`openAddBook()` → `POST /api/library/books`).
2. **Prepare files**: the "Guide" button saves the agent guide to a file (selected in Explorer, ready to drag into an agent chat) or copies it (`saveGuide()`, `copyGuide()`; text from `library_guide.md`). The agent renames pictures and writes `book-text.json`.
3. **Load into the passport**, any way:
   - drag a ZIP, a folder or several files, or "Add files": a copy goes in along with the JSON and the same «Import from folder» dialog opens (`onDrop()`, `importDropped()`);
   - «Import from folder»: pick a folder, the server lays it out and copies it in the background (`importFolder()`, `scan_folder()`, `_folder_import()`);
   - one file onto a specific slot; a `.json` carries text only.
4. The dialog shows what goes where, what will replace existing files and what is skipped; single slots can be unchecked.
5. After import, previews and blurred placeholders are prepared at once, older files in the background.
- A partial set is normal. Originals are never changed: files are copied to `data/library/books/<id>/assets/`; deleting an image removes only the library's copy.

## Why
- A Workshop picture dragged out never drops back into its own frame: the browser hands it over as a file.
- «Куди?» is asked rather than guessed: a book folder or ZIP could be meant for either place.

## Where in the code
- [app/web/js/drop.js](../../app/web/js/drop.js) — `dropContents()`, `receiveDrop()`, `wireFolderDrop()`
- [app/web/js/drop-anywhere.js](../../app/web/js/drop-anywhere.js) — `installDropAnywhere()`, `choose()`
- [app/web/js/app.js](../../app/web/js/app.js) — `dragFromPage`, `ownPicture()`
- [app/studio/drops.py](../../app/studio/drops.py) — `clear_drops()`, `dropped_folder()`, `dropped_top()`, `extract_zip()`, `archive_folder()`, `touch()`, `MAX_DROP_FILE`, `MAX_DROP_ZIP`
- [app/web/js/pages/book.js](../../app/web/js/pages/book.js) — `onDrop()`, `importDropped()`
- [app/studio/library_files.py](../../app/studio/library_files.py) — `scan_folder()`, `_folder_import()`
- Tests: [app/tests/test_flows.py](../../app/tests/test_flows.py) — `DroppedFolders`; [app/tests/test_orders.py](../../app/tests/test_orders.py) — `PartialBookImport`, `PreparationGuide`

## Related
- [Book files](../rules/book-files.md) · [Library](../features/library.md) · [Order Creator](../features/order-creator.md) · [Mockups](../features/mockups.md)
