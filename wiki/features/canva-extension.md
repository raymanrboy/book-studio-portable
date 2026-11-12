---
title: Canva extension
type: feature
updated: 2026-11-12
code:
  - canva-extension/
  - app/tests/test_canva_extension.py
---
# The Canva extension

> A Chrome extension (`canva-extension/`, outside the server) with a panel inside the Canva editor. **Book mode** takes a Workshop book's folder and lays it into the book's Canva template: every picture into its page's frame, and on text pages the «Yellow gradient sphere» with the page's text on top. **Order mode** prepares one order's copy of the template. Canva has no API on the owner's plan, so the extension imitates a person in Canva's Ukrainian interface. Install and usage steps (Ukrainian): [canva-extension/README.md](../../canva-extension/README.md).

## Book mode
1. **«Папка книги»**: the owner picks `pipeline/books/<n>.<slug>`. The extension reads `pictures/` (`1.png … 30.png`, `Cover.png`), `agent/book-text.md` and `book.json`; it writes nothing.
2. **The shelf** shows the book as printed: cover, then `[endpaper | 1]`, `[2 | 3]` … `[30 | endpaper]`. A text page has a «T» chip (red when its text is missing); a page without a picture is hatched red. A click shows the page's text in the book's font.
3. **The pages field** (`1-31`, `5-10`, `3,7,12`) chooses which pages go.
4. **«Розкласти»**: (1) all pictures of the chosen pages are uploaded at once to «Передані», named `<book>-p02-MMDD-HHMM.png` (the run's mark, so an older upload is never taken); (2) text pages are made while they upload; (3) each picture goes into its frame from its uploaded tile. A text page gets the sphere, then a new text box with the text in Schoolbell, then the size and line spacing. Pages light up (orange now, green done, red problem); «Зупинити» stops after the current step.
5. A second run skips what is done: a filled frame is left alone; a text whose first line is on the page is not added again (only its look is made right); a sphere the extension put is not put twice.
6. The button and the panel are draggable and share one remembered place.

`STYLE` in `canva.js`: Schoolbell, size 100 (110 on the end pages 1 and 30), line spacing 2.04 (page 30 keeps Canva's own), tracking 50, sphere colour white.

| Canva page | Picture | Text from `book-text.md` |
|---|---|---|
| 1 | `1.png` | none |
| 2–29 | `2.png … 29.png` | `## Spread NN`, on the spread's text page |
| 30 | `30.png` | `## Afterword` |
| 31 (the template's «Cover») | `Cover.png` | none |

A spread's text page is its right page; a mirrored spread (`rows.MIRRORED`, or the row's `mirrored` mark in `book.json`) has it on the left. Text is read as the Workshop reads it (`rows.text_sections()`); `{Name}` and `{Gifter}` stay as they are.

## Order mode
Three steps for one order; the owner does the rest by hand (name replace, dedication, download press). The full path from order to print: [order to print](../flows/order-to-print.md).
1. **Copy**: the order card's «Відкрити шаблон у Canva» opens the template with `#bs=…` (receipt, child, title `<receipt> - <child>`, book). `early.js` keeps it in `localStorage["bs-canva:orders"]` (12 h) and removes the hash from the address. `BSOrder.makeCopy` does «Файл → Копіювати»; the new tab takes the order only if it is Canva's own fresh copy of that template (`isFreshCopy`), and `rename` names it.
2. **First page deleted**: `deleteFirstPage` on a design that carries the order's name, once per copy, by itself.
3. **ZIP**: the owner presses «Завантажити PNG»; the order card catches that book's ZIP from Downloads (`GET /api/orders/<id>/canva-zip?title=`).

The panel watches the copy's tab every second (`watchOrder()` in `panel.js`). The buyer's name stays in the browser profile; it is never sent anywhere.

## Constraints that keep it from breaking
- All words it looks for are in `UI` at the top of `canva.js`; if Canva renames a button, change that line.
- The text box is added with **nothing selected** (otherwise Canva puts it under the sphere); a selection is dropped by clicking the page's thumbnail, because a script's Escape does nothing in Canva.
- A picture goes in by pointer events on the frame's element, then «Замінити» → uploaded tile; dropping a file onto the frame is not used.
- The font size is typed after a pointer click into the field; tracking and line spacing are set by their sliders.
- «Розкласти» counts 3-2-1, then a clear layer covers Canva and swallows the real mouse for the run (a moving hand made Canva drag a frame); the script's own presses go straight to elements.
- A run is tied to its design (another design in the tab stops it); before a tile is clicked the frame must still be selected and empty; a number is typed only into the focused field.
- If the sphere tile drops out of «Нещодавно використані», the panel says so (add it once by hand).

## Why
- A second run skips done work: reruns after a failure are cheap.
- The sphere is white and the first page is deleted only on a design carrying the order's name, so a wrong design is never changed.
- The extension does only what a person would: copy, delete first page, catch the download.
- The icon is symmetric (the owner's choice).

## Where in the code
- [canva-extension/canva.js](../../canva-extension/canva.js) — `UI`, `STYLE`, `NS.run()`
- [canva-extension/book.js](../../canva-extension/book.js) — `textSections()`, `buildPlan()`, `parsePages()`
- [canva-extension/order.js](../../canva-extension/order.js) — `BSOrder`, `makeCopy()`, `isFreshCopy()`, `deleteFirstPage()`
- [canva-extension/panel.js](../../canva-extension/panel.js) — `readFolder()`, `drawShelf()`, `watchOrder()`
- [canva-extension/early.js](../../canva-extension/early.js) — reads `#bs=` at document start
- [app/tests/test_canva_extension.py](../../app/tests/test_canva_extension.py) — `book.js` against `rows.text_sections()`

## Related
- [Order to print](../flows/order-to-print.md) · [Workshop](workshop.md) · [Orders](orders.md) · [Book files](../rules/book-files.md)
