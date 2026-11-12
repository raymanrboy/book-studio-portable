---
title: Book files — structure and naming
type: rule
updated: 2026-11-12
code:
  - app/studio/drops.py
  - app/studio/orders.py
  - app/studio/library.py
  - app/studio/library_files.py
  - app/studio/creator/printfolder.py
---
# Book files — structure and naming

> A book is a cover and 30 pages. Two file sets follow different rules: the **print folder** (`Cover.png` + `1…N.png`, N = 28 or 30) and the **library** (page numbers, or spread pairs like `12-13`). The Upscayl tail (`_upscayl…`) is ignored in both.

## Structure
- Page 1 is the dedication (right side, an endpaper on the left); spreads 2–15 are pages 2–29; page 30 is the afterword (left side, an endpaper on the right). **Spread N = pages 2N−2 and 2N−1.** Every spread has one page with text and one with a picture only.
- **Library slots** (`SLOT_KEYS`): `cover` and `thumbnail` (kept apart), `page1`, `spread2` … `spread15` (one `image`, or `left` + `right`), `page30`. Texts (`TEXT_KEYS`): the cover plus those 16 slots. A book is complete with the cover, all 16 illustrations and all 17 texts (`completeness()`).
- The Workshop has the same 17 rows; a spread is dropped as one 2:1 picture and becomes `left` + `right` at once ([Workshop](../features/workshop.md)).
- **Print folder viewer** pairs pages as `[endpaper | 1]`, `[2 | 3]`, … and last `[N | endpaper]` (`spreadsOf()`).
- A 28-page book is the 30-page template minus one whole spread (pages 2N−2 and 2N−1); the owner picks which in Canva, per book, and the program does not check it. The gap in Canva's numbers is closed by renumbering below.
- The Gelato PDF adds blank endpapers around the pages ([Gelato](../integrations/gelato.md)).

## Canva export → print folder (`arrange_pages()`)
Steps 1–4 are `drops.export_files()`, shared with the [mockups tool](../features/mockups.md) (it also takes JPG/WEBP and any page count).
1. PNGs in the folder are collected (hidden ones excluded).
2. **Cover**: a file whose name has `cover`, `cober` or `обкладин` (`COVER_NAME`), else the one wide picture (width ≥ 1.4 × height). Several covers or none: error "name it Cover.png". Canva's own ZIP needs no renaming: its `1.png` is the wide cover, `2.png…31.png` become pages 1–30.
3. The rest by the **last number in the name** (`page_number()`: "12", "Madelynn - 12", "12_upscayl_4x_ultrasharp" → 12). No number: error naming the file.
4. Sorted by number; equal numbers: "Page N appears twice".
5. The count must be an allowed Gelato count (`page_options()`: 28 or 30), else "28 or 30 pages needed, found 29"; the response carries `pageCount`.
6. A folder already named correctly with no extra files is used as is.
7. Otherwise a new folder `data/tmp/dropped/<uuid>/<name>` gets `Cover.png`, `1.png…N.png`. Originals are never renamed: dropped copies are moved, other files are hard-linked (same drive) or copied.
8. The card shows a note such as "pages 2–25 → 1–24; cover — design.png".

The Order Creator then runs the full check (`validate()`). For Gelato the book length is the smallest allowed count that holds the highest numbered file (`_gelato_page_count()`).

## Importing into the library (`scan_folder()`)
One rule set for «Import from folder», a dropped folder, a ZIP and several files. A folder's `generated/` or `pages/` subfolders win over the top level. PNG, JPG, WEBP; a partial set is normal.

| Name (no extension) | Slot |
|---|---|
| contains `cover` / `cober` / `обкладин` | cover (PNG wins) |
| contains `thumb` / `заставк` / `preview` / `gallery` | thumbnail |
| `1` | dedication |
| `30` | afterword |
| `2-3`, `2–3`, `2_3` | a whole spread |
| `2`, `3` separately | left / right page of a spread |
| `book-text.json`, `text.json`, `book.json`, or any `.json` | the book's text |
| anything else | skipped, shown in a list |

The "agent guide" for whoever prepares files (`agent_guide()`) is built from these rules.

## Replaced pages
Replacing one page from the viewer (`replace_page()`) puts the old file in a hidden `.replaced` subfolder (`REPLACED`) named like `7.png.20260920-142530`. Checks, page counting and the archive look only at files in the folder itself, so it never interferes; Undo (`restore_page()`) takes the newest copy back.

## Dropped paths
Only pictures (and `.json` for the library), up to 6 levels deep; `..`, `:`, `__MACOSX`, `._*` are rejected; forbidden characters become `_` (`_drop_rel()`; [Intake](../flows/intake.md)).

## Why
- Originals are copied or linked and never renamed or deleted: the owner's Canva downloads stay as they are.
- The length is the smallest allowed count that holds the top file (not "30 if 29 or 30 is present"), so a 28-page book needs no extra file.

## Where in the code
- [app/studio/drops.py](../../app/studio/drops.py) — `export_files()`, `page_number()`, `UPSCAYL_TAIL`, `COVER_NAME`, `_drop_rel()`
- [app/studio/orders.py](../../app/studio/orders.py) — `arrange_pages()`, `page_options()`
- [app/studio/library.py](../../app/studio/library.py) — `SLOT_KEYS`, `TEXT_KEYS`, `spread_pages()`, `completeness()`
- [app/studio/library_files.py](../../app/studio/library_files.py) — `scan_folder()`, `agent_guide()`
- [app/studio/creator/printfolder.py](../../app/studio/creator/printfolder.py) — `validate()`, `_gelato_page_count()`, `replace_page()`, `restore_page()`, `REPLACED`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `spreadsOf()`
- Tests: [app/tests/test_orders.py](../../app/tests/test_orders.py) — `ArrangePages`, `GelatoLength`; [app/tests/test_library_creator.py](../../app/tests/test_library_creator.py) — `FolderScan`

## Related
- [Intake](../flows/intake.md) · [Order to print](../flows/order-to-print.md) · [Library](../features/library.md) · [Gelato](../integrations/gelato.md)
