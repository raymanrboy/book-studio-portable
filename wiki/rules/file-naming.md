---
title: File naming — print and the library
type: rule
updated: 2026-09-23
code:
  - app/studio/orders.py
  - app/studio/library.py
  - app/studio/creator/
  - app/studio/drops.py
---
# File naming

> Two different rule sets: the **print folder** (strictly `Cover.png` + `1…N.png`) and **importing into
> the library** (page numbers, or pairs like `12-13`). The Upscayl tail (`_upscayl…`) is ignored in
> both.

## Canva export → the print folder (`arrange_pages()`)

Steps 1–4 are `drops.export_files()` — one reading shared with the
[mockups utility](../features/mockups.md) (since 2026-09-23; it takes JPG/WEBP too and any page count).

1. PNGs in the folder are collected (hidden ones excluded).
2. **The cover** — a file with `cover`, `cober`, or `обкладин` in its name (the same rule as in the
   library, `COVER_NAME`); if there's none, the one wide picture (width ≥ 1.4 × height). Several covers,
   or none at all → an error, "name it Cover.png". Canva's own ZIP of a book needs no renaming: its
   `1.png` is the wide cover, `2.png…31.png` become pages 1–30.
3. The rest, by the **last number in the name** (`page_number()`: "12", "Madelynn - 12",
   "12_upscayl_4x_ultrasharp" → 12). No number → an error naming the file.
4. Sorted by number; matching numbers → "Page N appears twice".
5. The count has to exactly match what's allowed: Printify — 24, Gelato — 28 or 30 (`page_options()`),
   otherwise — "24 pages needed, found 23 (pages 1–23)" / "28 or 30 pages needed, found 29". The
   response includes `pageCount` — how many pages there were.
6. An already correctly named folder with no extra files is used as-is.
7. Otherwise — a **new folder** `data/tmp/dropped/<uuid>/<name>`: `Cover.png`, `1.png…N.png`. The user's
   originals are never renamed: dropped copies are moved, other files get a hard link (same drive, no
   extra space) or a copy.
8. A note for the card: "pages 2–25 → 1–24; cover — design.png".

Next comes the Order Creator's check (`validate()`): for Printify, exact sizes, so un-upscaled pages
show up as an error right away. For Gelato, the check works out the book's length from the highest file
number itself (`_gelato_page_count()`: `29.png` or `30.png` present → 30, otherwise 28).

## Importing into the library (`scan_folder()`)

One set of rules for the "Import from folder" button, a dropped folder, a ZIP, and several files (since
2026-09-23; before that, dropping had its own copy of the rules in the page).

| Name (no extension) | Where |
|---|---|
| contains `cover` / `cober` / `обкладин` | the cover (PNG takes priority) |
| contains `thumb` / `заставк` / `preview` / `gallery` | the thumbnail |
| `1` | the dedication |
| `30` | the afterword |
| `2-3`, `2–3`, `2_3` (a spread pair) | a whole spread |
| `2`, `3` (separate) | the left / right page of a spread |
| `book-text.json`, `text.json`, `book.json` (or any `.json`) | the book's text |
| anything else | skipped (shown in a list) |

- A folder may contain `generated/` or `pages/` subfolders — their files take priority.
- Allowed formats: PNG, JPG, WEBP.
- A partial set is normal.
- The rules for a person or agent preparing files live in the "agent guide" (`agent_guide()`), built
  from these same rules.

## A replaced page

When the owner replaces a single page from the viewer (`replace_page()`), the old one lands next to it
in a **hidden** `.replaced` subfolder, named `7.png.20260920-142530`. Checks, page counting, and the
archive only look at the files in the folder itself (`_files_by_lower()`, `_signature()` use
`is_file()`), so this subfolder doesn't get in their way; "Undo" (`restore_page()`) takes the newest
copy from there.

## Dropped files (`_drop_rel()`)

Only pictures (and `.json` for the library) are accepted, up to 6 levels deep; `..`, `:`, `__MACOSX`,
`._*` are all rejected; forbidden characters in names are replaced with `_`. More detail —
[flows/dropped-files.md](../flows/dropped-files.md).

## Where in the code

- [app/studio/drops.py](../../app/studio/drops.py) — `export_files()`, `page_number()`, `_LAST_NUMBER`, `UPSCAYL_TAIL`, `COVER_NAME` (one set for the print folder, the library and the mockups), `_drop_rel()`, `DROPS`
- [app/studio/orders.py](../../app/studio/orders.py) — `arrange_pages()`, `page_options()`, `pages_word()`, `ranges()`
- [app/studio/library.py](../../app/studio/library.py) — `scan_folder()`, `_NUM_RE`, `agent_guide()`
- [app/studio/creator/printfolder.py](../../app/studio/creator/printfolder.py) — `validate()`, `expected_files()`, `_gelato_page_count()`, `replace_page()`, `restore_page()`, `REPLACED`
- [app/studio/mockups.py](../../app/studio/mockups.py) — `read_book()` (a demo book: any page count)
- Tests: [app/tests/test_orders.py](../../app/tests/test_orders.py) (`ArrangePages`, `GelatoLength`, `PreparationGuide`, `PartialBookImport`), [app/tests/test_library_creator.py](../../app/tests/test_library_creator.py) (`FolderScan`, `GelatoValidation`)

## Related

- [Book structure](book-structure.md) · [The order-to-print path](../flows/order-to-print.md) · [Filling the library](../flows/book-import.md)
