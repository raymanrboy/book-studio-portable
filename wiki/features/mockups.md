---
title: Mockups
type: feature
updated: 2026-11-12
code:
  - app/studio/mockups.py
  - app/studio/mockup_render.py
  - app/studio/mockup_colours.py
  - app/web/js/pages/mockups.js
  - app/web/js/pages/mockups-run.js
  - app/web/js/pages/mockups-edit.js
  - app/web/js/pages/mockups-slides.js
---
# Mockups (Мокапи)

> A tool at `#/mockups` (in «Інструменти») and a Workshop book's «Мокапи» step. The owner drops the demo book's Canva ZIP, clicks the spreads that look good, and **Book Studio draws the six mockup templates itself** — no Photoshop, a run takes seconds. Every picture is also cut out without its background, and step 4 makes the [listing slides](slides.md). Templates, layers, baking and size rules: [mockups-engine.md](mockups-engine.md).

Opened from a Workshop book the page says «Для книги №…», goes back to the book and keeps the rail on «Книги» (`arrived()`, `navFor()`); opened from «Інструменти» it starts clean every time. The page keeps its state when the owner steps away (book, picks, a running job) but only for a way back that is not the tools list.

## Layout

Numbered steps on the left, the demo book's structure on the right; a finished step's number turns into a check mark. A run in progress puts a cyan dot on «Інструменти» and a notice says when it ends ([rail](rail.md)).

### The demo book

A dashed veil «Перетягніть сюди ZIP із Canva»: drop the ZIP (anywhere on the window), the unpacked folder or loose pictures, or click for the Windows dialog (it starts in Downloads, then where the last ZIP was — `lastZip` in `places.json`). The pages are read by the print folder's rules ([book files](../rules/book-files.md)): the cover is `cover…` or the one wide picture, page 1 is the dedication, spreads are `2–3`, `4–5`…, page 30 is not offered. A dropped ZIP is moved out of the orders' dropped files at once (`_take_dropped()`), so a new demo book never clears an order's files and the orders' cleaning never takes the demo book ([intake](../flows/intake.md)).

### Steps

1. **Розвороти в шаблонах.** One row per template with its own preview and slots: Open 1 ×4, Open 2 ×2, Cover & Open 1 ×1, All & Open 1 ×1. Dedication (page 1) and Cover 1 fill themselves.
   - Click a spread: it goes into the highlighted slot and the next lights up. Drag a spread onto a slot (or a slot onto another: they swap); × / Delete empties a slot, the eraser empties all, the magnifier opens a spread large.
   - A book dropped in again gets its picks back (`localStorage`).
   - **Every template row has a tick**, all ticked by default. «Зробити мокапи» makes only the ticked ones, spreads are asked for only there (`selected()`, the `only` list sent to `/api/mockups/make`). A partial run does not tick the Workshop book's step (`_ticked(whole=False)`).
2. **Книга** — only when the page is a book's step. The Workshop's books, newest first; the chosen book's `mockups\` takes the pictures and their cut-outs with **no dialog**. «Інша папка…» gives a folder field and the Windows dialog instead. Opened from «Інструменти» without a book, the run asks for a folder and never fills a Workshop book's folder by itself.
   - A Workshop book's folder is read as it is (`GET /api/mockups/existing`, `existing()`): step 3 shows «У папці книги · N картинок» and step 4 is available with **no demo book and no run needed**. It is re-read on opening, on choosing another book, after every run and after «Завершити».
   - For a Workshop book a run also keeps the Canva cover as `mockups\canva-cover.*` (`_keep_canva_cover()`) and copies Cover & Open 1 and All & Open 1 into the book's `etsy\` (`_to_etsy()`) — [photo mockups](photo-mockups.md) own that folder's numbering.
3. **Картинки** — one line says what will happen, then «Зробити мокапи». The button always answers: no book → the veil blinks; empty slots → they blink and a toast names them. While it runs: a row per template, a bar, × stops. Done: «Готово · N картинок» with the pictures (a click opens large). With the window behind, the taskbar button flashes, Windows chimes and the title says so (`bs:busy`).
4. **Слайди для лістингу** — [slides](slides.md).
5. **«Завершити»** — the page starts clean for the next book and the unpacked demo book is deleted (`close()`).

The sliders button in the header (`openPlaces()`) shows where the templates (and Photoshop for the fallback) are; a missing folder is a yellow line above the steps.

## Where the output goes

| Case | Pictures | Cut-outs |
|---|---|---|
| Workshop book | `pipeline/books/<n>.<slug>/mockups/` | its `mockups/no-background/` |
| Other folder | the chosen folder | its `no-background/` |

- **Kept only without the background:** Open 1, Open 2 and Dedication (`CUT_ONLY`) are cut straight from the drawing (`slide_cutout.cut_drawn()`) and saved only in `no-background\`. `mockups\` keeps Cover 1 (the photo mockups use it with its background as the reference) and the two scene mockups (`SCENES`). A background-free file carries a note of where it lay in the template, so the slides tell book and shadow apart again (`cutout._split()`); the slides, the card «У папці книги» and the Workshop counts count such files as mockups (`cutout.alone()`).
- Names are `<template> (<pages>).png`, never over an existing file (` (2)`, `_free_name()`).
- Temporary files and the demo book's folder: [mockups-engine.md](mockups-engine.md#temporary-files) and [runtime](../architecture/runtime.md).
- A job's trace is in `app/data/logs/app.log`, lines `Mockups: …`.

## The crop window

`mockups-edit.js` (`openEditor()`). On a drawn result **Cover 1, Cover & Open 1 and All & Open 1** (`EDITABLE`) carry the crop button «Поправити обкладинку». The program puts the right half of the 2:1 cover in; the owner only nudges it.

- **Left: the whole cover** with the front's frame and the spine's middle dashed. The frame goes anywhere on the cover: drag inside to move, press beside to bring it there. Its four corners resize it like Ctrl+T — the opposite corner stays, the board's proportions never change. It cannot leave the picture, be taller than the cover (`min_zoom()`) or closer than ×3 (`MAX_ZOOM`). ↶ restores the program's choice.
- **The crop is per template** (a hardcover board and a softcover square differ). The server cuts the picture to the window before resizing, so nothing beyond it bleeds in (`cover_pictures()`, `_crop_values()`). A run without a crop keeps the right half.
- **All & Open 1 also crops the back** (a scene of its own): a second frame over the left half, tagged «Задня» / «Лицьова», each moved by itself. ↶ puts both back; «Зберегти» keeps both (the back is sent only when moved).
- **Right: the mockup as it will be**, drawn by the server a moment after each change, nothing saved. The window fits 1024×640 and up without scrolling.
- **In the two scene templates, also «Фон» and «Краї розкритої книги».** «Фон»: pastel shades of the cover's own leading hues (`mockup_colours.pastels()`; the first is what a run uses), a warm off-white, or any colour. The two scenes share one background — saving redraws the other too. «Краї»: each half's colour from the cover's outer edges (`edges()`); a click on the chip, then on the cover, takes another.
- «Зберегти» draws the picture over the file the run saved, makes its «Без фону» again and refreshes the book's `etsy/` copy. It needs the demo book still open on the page.
- Dedication needs no colours: its desk colour is the template's own, its floor is cut away.

## Why

- The templates folder is read-only; the program only opens copies ([security](../security.md)).
- "If it isn't needed, don't save it": Open 1, Open 2 and Dedication exist only without background.
- A tick per template so one changed template is redone without the rest.
- No question about where to save for a Workshop book.
- The crop window is a mini editor on purpose: the owner touches nothing when the program's half is right.

## Where in the code

- [app/studio/mockups.py](../../app/studio/mockups.py) — `draw()`, `drawn()`, `make()`, `existing()`, `_keep_canva_cover()`, `_edit_save()`
- [app/studio/mockup_render.py](../../app/studio/mockup_render.py) — `render()`, `ready()`
- [app/studio/mockup_colours.py](../../app/studio/mockup_colours.py) — `pastels()`, `edges()`
- [app/web/js/pages/mockups.js](../../app/web/js/pages/mockups.js) — `arrived()`, `openPlaces()`; [mockups-run.js](../../app/web/js/pages/mockups-run.js) — `runView()`, `existingCard()`; [mockups-edit.js](../../app/web/js/pages/mockups-edit.js) — `openEditor()`
- [app/studio/slides/cutout.py](../../app/studio/slides/cutout.py) — `cut_drawn()`, `alone()`

## Related

- [Mockups engine](mockups-engine.md) · [Slides](slides.md) · [Photo mockups](photo-mockups.md) · [Workshop](workshop.md) · [Rail](rail.md) · [Security](../security.md) · [Runtime](../architecture/runtime.md)
