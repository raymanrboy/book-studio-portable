---
title: The Canva extension — a Workshop book into its Canva template
type: feature
updated: 2026-10-18
code:
  - canva-extension/
  - app/tests/test_canva_extension.py
---
# The Canva extension

> A Chrome extension (`canva-extension/`, not part of the program's server): a panel inside the Canva editor that takes a Workshop
> book's folder and lays it into the book's Canva template — every picture into its page's frame, and on the text pages the
> «Yellow gradient sphere» with the page's text on top (Schoolbell; 110 on the afterword, 100 on the spreads; line spacing
> 2.04). The owner then only aligns. Born 2026-10-07/08: Canva has
> no API for this on the owner's plan, so the extension does what a person would do, in the Ukrainian interface.

## What it does

1. **«Папка книги»** — the owner picks the book's folder (`pipeline/books/33.guardian-angel`). The extension reads
   `pictures/1.png … 30.png` + `Cover.png`, `agent/book-text.md` and `book.json` — nothing is written anywhere.
2. **The shelf** shows the book as it is printed: the cover, then `[endpaper | 1]`, `[2 | 3]` … `[30 | endpaper]`; a page with text has a
   «T» chip (red — the text is missing in `book-text.md`), a page without a picture is hatched red. A click on a page shows its text
   below in the book's font, `{Name}`/`{Gifter}` lit.
3. **The pages field** (`1-31`, `5-10`, `3,7,12`) — which pages go; the others are greyed.
4. **«Розкласти»** — in three steps (the owner's speed-up, 2026-10-08): (1) every picture of the chosen pages goes into
   «Передані» at once (Canva uploads them side by side; the names carry the run's mark `<book>-p02-MMDD-HHMM.png`, so an older
   upload is never taken); (2) the text pages are made while they upload; (3) each picture into its frame from its uploaded
   tile (the Replace panel's list, scrolled when the tile is further down). What a page gets: the picture into the page's empty frame; on a text page — the sphere, then a new text box with
   the text, then Schoolbell, the size (110 on the afterword, 100 on the spreads) and the line spacing 2.04 (not on page 30 — it keeps
   Canva's own, the owner) on
   the whole box. The reader shows the look each text page will get. Each page lights up (orange — now, green ✓ — done, red ! — what went wrong, in
   the reader below); the bar fills by pages. «Зупинити» stops after the current step.
5. **A second run skips what is done** (the owner's choice): a frame that already has a picture is left alone; a text whose first
   line is already on the page is not added again — only its font, size and line spacing are made right; a sphere the extension
   already put (one not inside a group) is not put twice.
6. **The button and the panel are dragged** (the button, or the panel by its head); they share one remembered place — the panel
   opens where the button stood (2026-10-08, the owner).

### What goes where

| Canva page | Picture | Text (`book-text.md`, without the `##` heading) |
|---|---|---|
| 1 | `1.png` | none — only the picture (the owner, 2026-10-08) |
| 2–29 | `2.png … 29.png` | `## Spread NN` on the spread's text page |
| 30 | `30.png` | `## Afterword` |
| 31 (the template's «Cover») | `Cover.png` | none — the owner sets the title |

A spread's text page: its right page; the mirrored spreads (`rows.MIRRORED`, or the row's `mirrored` mark in `book.json` after ⇄)
have it on the left — 3, 4, 7, 8, 11, 12 … The text is read exactly as the Workshop reads it (`rows.text_sections()`): `{Name}` and
`{Gifter}` stay as they are — the owner fills them per order.

## How it drives Canva (all tried by hand first, 2026-10-07/08)

- **Pages** — the page strip's thumbnails «Сторінка: N» (the strip draws only what is in view, so it is scrolled). Clicking the
  current page's thumbnail is also how a selection is dropped: a script's Escape does nothing in Canva.
- **What is on a page** — Canva's accessibility layer («Елемент рамки | Заповнювач» = an empty frame, «Зображення» once filled,
  «Елемент тексту | …» with the text) matched in order to the drawn elements (16-letter ids). The drawn page is the `[data-page-id]` around the layer «Сторінка N» — its `data-page-id` is Canva's own id, not the number (0 for page 1 in the owner's Chrome).
- **What is selected** — read from the toolbar: a page shows its duration («5.0с»), a frame «Замінити», a text the font button.
- **A picture**: pointer events straight at the frame's element (so the cover's print guides lying on top are skipped) → «Замінити»
  → «Передати файли» → Canva's file chooser is answered from the page (the extension runs in the page's world) → the uploaded tile
  (its local preview turns into Canva's picture when the upload ends) is clicked → the frame is filled, cropped by Canva.
  The upload is named `<book>-p02-MMDD-HHMM.png` / `<book>-cover-…` and stays in the owner's «Передані» (uploaded at the start,
  all at once — the «Передані» panel's «Передати файли» puts nothing on the page, tried live).
  Not used: dropping a file onto the frame — Canva puts it *on top of* the frame.
- **The sphere** — the tile «Додати на полотно Yellow gradient sphere» of «Елементи» → «Нещодавно використані»; if it ever drops
  out of that list, the page says so (add it once by hand). It is made **white** (the owner: «в самий білий»): the sphere selected →
  «поточний колір» → the swatch `#ffffff` of the panel «Колір»; checked by the picture's middle pixel (Canva's white reads 248; while
  recolouring the picture is briefly gone). A re-run whitens a yellow sphere it finds. Canva takes **~5 s** to redraw the
  recoloured sphere (measured), so a run doesn't wait: it clicks white and goes on to the text; step 3, opening the page for its
  picture anyway, reads the sphere once and recolours one that stayed yellow (page 24 in the owner's run). The text box is
  added with **nothing selected** — with the sphere selected Canva put it under the sphere (page 23). A new text box is made one line high
  in the page's centre and grows **downwards** as the text and its size go in, so after its look is set it is put back in the
  middle: «Розташування» → «По центру» (vertical) and «У центрі» (horizontal) — tried live. A text already on the page (a re-run)
  keeps the place the owner gave it. A side-panel click Canva swallows while busy is made again after 2 s (it was 8 s). Each text page's
  note carries its parts' seconds («сфера 1.1 с, білий 0.6 с, текст 4.2 с»), so a slow part shows itself. A press on a picture that is already selected
  unselects it (tried live) — a sphere just put is already selected, so it isn't pressed again.
- **A text** — «Текст» → «Додати текстове поле» → the text typed in (a line break = a new line) → the box left → selected whole →
  the font button opens the panel «Шрифт»: the font's own button (`aria-label` = its name, there when used lately), else that
  panel's search → the size typed into «Розмір шрифту» after a pointer click into it (a number field that a script can't select;
  Canva selects it on a click) → «Розширені параметри» → the **sliders** of «Трекінг» (50) and «Відстань між рядками» (2.04) set
  (each field and slider found by position — the number nearest under its words, the slider in its row; the number beside it
  shows a typed value but Canva ignores it; the slider's value + its input event is what Canva hears) → the box selected again
  from scratch to check all three stuck. Typing the size while still inside the text sets only the caret's paragraph (a box of
  mixed sizes shows an empty size field).
- **Which page is open** — the counter in the bottom bar («7 з 32») must read the page; a lost click on a thumbnail is tried once more.
- **The lock** — «Розкласти» counts 3-2-1 («Відпустіть мишку»), then a clear layer covers Canva for the run and swallows the real
  mouse (the panel stays above it): a hand moving the mouse while the script pressed a frame made Canva drag it (the owner,
  2026-10-08). The script's own presses go straight to their elements, so the layer doesn't stop them (tried live); a press is
  down-and-up at once, with no gap.
- **Safety** — a run is tied to the design it started on (another design opened in the tab stops it); before the uploaded tile is
  clicked the frame must still be selected and empty (else the picture would land loose); a number is typed only into the focused
  field; «Зупинити» closes the side panel and leaves the page unselected.

All the words it looks for are in one place — `UI` at the top of `canva.js`; if Canva renames a button, that is the line to change.

## The order mode, reduced (2026-10-18)

The order mode of 2026-10-15 was removed whole on 18.10 («тільки для створення книг»), and the same day the owner took back
three things he liked: **the template's copy made and named by itself, the copy's first page deleted, the downloaded ZIP caught by
the card**. Nothing else came back — no `{Name}` replace, no dedication fields, no download press (the owner downloads himself).
The first version's `order.js` was lost (it was never committed), so `order.js` is **new, written from what the owner's Canva shows**.
- **The hand-over**: the order card's «Відкрити шаблон у Canva» opens the book's template with `#bs=<base64url JSON>` —
  `receipt`, `child`, `title` («<receipt> - <child>», «#2» for a second child of one name), `book`. `early.js` (document_start) keeps it in
  `localStorage["bs-canva:orders"]` (one entry per book, 12 hours, the template's design id) and takes the hash off the address.
  The buyer's name stays local in the browser profile's history and is never sent anywhere.
- **The steps** (the panel shows them instead of the shelf; «Розкласти книгу з Майстерні» goes back to the book mode, a chip back to
  the order): ① **Копія шаблону** — «Файл → Копіювати» (`BSOrder.makeCopy`; Canva opens the copy in a new tab); the new tab takes the order
  on only if the design is Canva's own copy of that template (`isFreshCopy`: name «<template>, копія», opened within 5 minutes — never a
  master or another design) and renames it, in the field «Назва дизайну» that lives **inside the «Файл» menu** (the name is read from the tab
  title «<name> – Multi-design»); ② **Перша сторінка** — page 1 opened, the trash «Видалити сторінку» pressed (no confirm; checked by the
  counter «N з M» dropping by one) — **only on a design that carries the order's name**, once (`firstDeleted`); ③ «Завантажити PNG» is the
  owner's own press. Each step has a button to repeat it by hand. A step runs under the lock.
- **The ZIP**: Canva names it after the design; the order card asks `/api/orders/<id>/canva-zip?title=<the copy's name>` every 2.5 s
  after the press (each book its own wait, 3 hours; a drop by hand ends it) and takes **that book's** ZIP only — like a dropped ZIP
  ([orders](orders.md)). A ZIP that cannot be unpacked is said once.
- **Tried live (18.10, the owner's «BS 4k Трафарет», signed in in the browser pane, the template put back after each try):** the «Файл» menu's
  items and the «Назва дизайну» field; the rename (and back, trailing space and all); page 1's delete (32 → 31 pages, no dialog) and **Ctrl+Z**
  puts it back; the menu closes by the «Файл» button again (a script's Escape does not close it). **Not tried:** «Файл → Копіювати» itself
  (it opens a new tab, which the pane blocks; it would also leave a stray copy), so the whole run from the card's button, the copy's
  new tab, the rename there and the first page's delete — all in the owner's Chrome — is the first real test.

## The look (2026-10-14, the owner: «перемалювати значок… зробити інтерфейс гарнішим»)

- **The icon** (`icons/`, drawn by a script — Pillow, 1024 px brought down): Book Studio's orange squircle and its open book,
  centred and symmetric (15.10, the owner: «не симетричне» — the cyan sparkle badge of 14.10 pushed the book aside and crowded
  the 48 px button; gone). The same drawing in the panel (`logo()`); the icons' line style no longer outlines it in black
  (`svg.logo { stroke: none }` — the dark rim the owner called «жахливо»).
- **The panel**: the head names «Book Studio · Книга → Canva»; the book button and the pages field as one pair (38 px, a
  focus ring in the accent); page thumbnails lift on hover, the chosen one outlined in the accent; a fuller bar with a moving
  sheen while it works; the panel rises in and sinks away when folded (the button pops back), still under reduced motion.

## Install (the owner)

`chrome://extensions` → «Режим розробника» on → «Завантажити розпаковане розширення» → the folder `Book Studio\canva-extension`.
After a change in the folder — the ↻ on the extension's card, then reload the Canva tab. The steps in Ukrainian —
[canva-extension/README.md](../../canva-extension/README.md).

## Where in the code

- [canva-extension/early.js](../../canva-extension/early.js) — the order from the link's `#bs=`, kept and taken off the address (document_start).
- [canva-extension/order.js](../../canva-extension/order.js) — the order mode's Canva driver: `UI`, current, save, clear, title, isCopyFor,
  isTemplateFor, isFreshCopy, makeCopy, rename, pageCount, deleteFirstPage.
- [canva-extension/manifest.json](../../canva-extension/manifest.json) — Manifest V3; content scripts on `https://www.canva.com/*` in the
  page's world (`"world": "MAIN"`); the panel shows only under `/design/`.
- [canva-extension/book.js](../../canva-extension/book.js) — pure logic, run in node by the test: textSections (the same as
  `rows.text_sections()`), textPageOf, buildPlan, parsePages, pictureKey, uploadName.
- [canva-extension/canva.js](../../canva-extension/canva.js) — the Canva driver: `UI` (the words looked for), `STYLE` (Schoolbell,
  100 / 110 on page 30 (and 1, should it ever get a text), line spacing 2.04), sizeOf, openPage, currentPage, selection, pageModel, emptyFrame, textBox, putPicture,
  addSphere, addText, styleText, setFont, typeNumber, setLineSpacing, run.
- [canva-extension/panel.js](../../canva-extension/panel.js) — the panel in a shadow root, Book Studio's light look: readFolder (and
  readFolderInput without the folder picker), drawShelf, focus (the reader), layout and draggable (the shared place), the run with its
  progress.
- [app/tests/test_canva_extension.py](../../app/tests/test_canva_extension.py) — book.js against the Workshop's own reading (skipped
  without node), the manifest's files.

## Related

- [Canva](../integrations/canva.md) · [Workshop](workshop.md) · [Book structure](../rules/book-structure.md)
