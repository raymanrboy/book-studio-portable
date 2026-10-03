---
title: Book structure — pages, spreads, slots
type: rule
updated: 2026-10-03
code:
  - app/studio/library.py
  - app/web/js/order-bits.js
---
# Book structure

> A book is a cover and 30 pages. Page 1 is the dedication (right side, an endpaper on the left),
> spreads 2–15 are pages 2–29, page 30 is the afterword (left side, an endpaper on the right).
> **Spread N = pages 2N−2 and 2N−1.**

## The library (the reference, 30 pages)

| Slot (`SLOT_KEYS`) | Pages | What |
|---|---|---|
| `cover` (separate from the slots) | — | the full cover spread (back + front) |
| `thumbnail` (separate) | — | the gallery thumbnail |
| `page1` | 1 | the dedication, one image |
| `spread2` … `spread15` | 2–3 … 28–29 | a whole spread (`image`) **or** `left` + `right` |
| `page30` | 30 | the afterword, one image |

Texts (`TEXT_KEYS`): `cover`, `page1`, `spread2…spread15`, `page30` — 16 slots + the cover.
A book is "complete" once it has the cover, all 16 illustrations, and all 17 texts (`completeness()`).

Every spread has one page with text and one that's just a picture.

**The Workshop** (since 2026-09-24) has the same 17 rows — the cover, page 1, spreads 2–15, page 30 — each with
a prompt (`PROMPT_KEYS`, the same keys as the texts) beside its text; a spread is dropped as one 2:1 picture and
becomes its `left` + `right` square pages at once (mirrored first for 4–5, 8–9 … 28–29), the cover is one wide
picture, pages 1 and 30 a square beside the empty endpaper ([workshop](../features/workshop.md)).

## Print (the Order Creator's folder)

- Files: `Cover.png` + `1.png … N.png`, where N = 24 (Printify) or 28 or 30 (Gelato — however many were
  downloaded).
- Spreads in the viewer (`spreadsOf()`): `[endpaper | 1]`, `[2 | 3]`, `[4 | 5]`, …; the last one —
  `[N | endpaper]` (24, 28, or 30).
- For Printify, **exactly 3 spreads** (6 pages) are dropped from the 30-page template; for a 28-page
  Gelato book — **one** spread; which ones exactly is decided by the owner in Canva, for each book. That
  leaves the Canva file numbers "with gaps" — the program renumbers them in order
  ([file-naming.md](file-naming.md)). A whole spread has to be dropped (pages 2N−2 and 2N−1), or the
  spreads shift — the program doesn't check this ([decision](../decisions.md)).
- In the Gelato PDF: cover, blank endpaper, 28 or 30 pages, blank endpaper (31 or 33 PDF pages). Without
  the blank ones, Gelato shifts the book by a page; in the draft the endpaper shows as a blank "Page 0";
  the blank pages are white pictures at 300 dpi
  ([integrations/gelato.md](../integrations/gelato.md)).

## Where in the code

- [app/studio/library.py](../../app/studio/library.py) — `SLOT_KEYS`, `TEXT_KEYS`, `SPREAD_NUMBERS`, `spread_pages()`, `slot_label()`, `_empty_slots()`, `completeness()`
- [app/web/js/pages/book-dialogs.js](../../app/web/js/pages/book-dialogs.js) — `SPREADS`, `SLOT_KEYS`, `pagesOf()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `spreadsOf()`, `folderViewerItems()`
- [app/studio/creator/printfolder.py](../../app/studio/creator/printfolder.py) — `expected_files()`
- [app/studio/creator/photobook.py](../../app/studio/creator/photobook.py) — `build_photobook_pdf()`

## Related

- [Library](../features/library.md) · [File naming](file-naming.md) · [Canva](../integrations/canva.md)
