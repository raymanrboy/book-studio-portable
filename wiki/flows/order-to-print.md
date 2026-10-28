---
title: The order-to-print path, from Etsy
type: flow
updated: 2026-10-28
code:
  - app/web/js/pages/orders.js
  - app/studio/orders.py
  - app/web/js/pages/creator.js
  - app/studio/creator/
  - app/studio/archive.py
---
# The order-to-print path, from Etsy

> Every order follows one path: *order → Canva → files → proofing → print*, with everything needed kept
> in view the whole time. The goal is to remove mistakes from manual work in Canva: the buyer's data sits right
> there, to be copied, not retyped. Every book is printed by Gelato.

## Steps

| # | What the owner does | What the program does | Where in the code |
|---|---|---|---|
| 0 | Starts the program | One sync of Etsy + Gelato (Printify's old orders are only read) | [sync.py](../../app/studio/sync.py) `startup_sync()` |
| 1 | Opens "Orders" → "New" | A list of receipts with no print order, with book and printer | [orders.js](../../app/web/js/pages/orders.js) `mountQueue()` |
| 2 | Opens an order | The card: the book from the library by listing, the printer by rule, the buyer's fields | [orders.py](../../app/studio/orders.py) `enrich()` |
| 3 | "Open template in Canva" | Opens the link from the book's passport in a browser | [order-card.js](../../app/web/js/pages/order-card.js) `renderLeft()` |
| 4 | In Canva: a copy of the template, `{Name}` → the name, the dedication, download PNGs (30 pages, or 28 without one spread — [printer rule](../rules/printer-rule.md)) | — (copying values with buttons in the card) | [integrations/canva.md](../integrations/canva.md) |
| 5 | Drags the ZIP/folder into "Files from Canva" | Copies it into the program, lays out `Cover.png` + `1…N.png`, a full check | [order-card.js](../../app/web/js/pages/order-card.js) `takeDrop()`; [orders.py](../../app/studio/orders.py) `arrange_pages()` |
| 6 | Proofs it; watches the text-check badge | The cover, the first spread with its note (name, fields), a filmstrip of every spread, the viewer; meanwhile the local model reads the pages and checks them against the book passport, problems as a list and outlines on the pages ([text check](../features/text-check.md)) | [order-card.js](../../app/web/js/pages/order-card.js) `proofCard()` |
| 6a | Found a mistake — fixes the page in Canva, downloads **just that page** | A "Replace N" button in the viewer: the page takes the old one's place, files and text are checked again, "Undo" sits next to it | [folder-viewer.js](../../app/web/js/folder-viewer.js) `openFolderViewer()`; [creator/printfolder.py](../../app/studio/creator/printfolder.py) `replace_page()` |
| 7 | "Send to print in …" | The Order Creator opens as the order's print step (its path, back to the card) and is filled in: mode, folder, title `receipt - name`, address, format | [order-card.js](../../app/web/js/pages/order-card.js) `print()`; [handoff.js](../../app/web/js/handoff.js) `take()` |
| 8 | "Create draft" | Gelato: a PDF + a draft. A copy of the files that went to print goes into the [order archive](../features/archive.md) | [creator.js](../../app/web/js/pages/creator.js) `create()`; [creator/gelato_send.py](../../app/studio/creator/gelato_send.py) `create_gelato_draft()` |
| 9 | In Gelato — open the draft from the orders list («Замовлення в Gelato»), confirm and pay | Until then the order stays in "New" with a "Draft" chip: a draft doesn't count | [integrations/gelato.md](../integrations/gelato.md) |
| 10 | Clicks "Refresh" | A confirmed and paid order moves to "In progress" (the receipt number is in the reference / title); the printer status shows on the right; the book appears in the order archive | [stages.py](../../app/studio/stages.py) `order_stage()`; [printorders.py](../../app/studio/printorders.py) `is_placed()` |
| 11 | Once the printer ships it — opens the «Позначити в Etsy» tab, clicks to copy the tracking number | An order with a tracking number or "shipped" status is on the truck tab, with a carrier and a number | [stages.py](../../app/studio/stages.py) `order_stage()`; [order-bits.js](../../app/web/js/order-bits.js) `trackChips()` |
| 12 | Marks the order shipped on Etsy (on the Kyiv PC), then clicks "Refresh" | The order moves to "Sent" (a box); its 14-day countdown starts in the order archive | [rules/order-stages.md](../rules/order-stages.md); [archive.py](../../app/studio/archive.py) `refresh()` |
| 13 | If something happened to the book — the order's card → «Що пішло в друк · передрук» (or «Інструменти» → «Архів друку») → "Reprint" | Gelato: a new draft from the same files; a Printify-era book is downloaded again and sent from the order's card; the receipt is marked as a replacement. **With new files** (a cover fixed after a complaint): the card's «Покласти інші файли й надіслати ще раз» → the Order Creator ticks «Передрук» itself | [archive.js](../../app/web/js/pages/archive.js) `reprint()`; [creator/gelato_send.py](../../app/studio/creator/gelato_send.py) `create_gelato_draft()` (`reprint_of`, `again`) |

While the order is in "New", the card and the Order Creator remember with it where the owner left off:
he can switch to another tab and come back to the same step, even a page showing a successful creation
([features/orders.md](../features/orders.md)).

**Several books in one order**: the owner goes through steps 4–6 for each book
separately — a "Book 1 / Book 2" switch in the card, each with its own folder, its own proofing and its
own text check. Step 7 takes **every ready book** together, step 8 creates **one** draft to one address
(one Gelato draft with several items). After that, the path is the same: in the queue, in the accounting and in the archive, it's one
order with several books.

A separate Order Creator remains for manual cases (a reprint when the files are no longer in the
archive, a replacement).

## Principles (why it's not like Etsy OS)

- One order — one screen, no locks, revisions, "file generations", or blockers.
- An order's state comes from the facts (Etsy + Printify/Gelato), not from hidden saved states.
- Nothing is stored "just in case"; temporary file copies are wiped on launch. The one exception is the
  order archive: books that went to print live for 14 days after "Sent".
- Built in small steps, each one working and checked by the owner right away.

## Left manual (the owner's decision)

- "With love, …" at the start of the "from whom" field isn't removed automatically — a duplicate is
  visible right away.
- The program doesn't parse a custom dedication or afterword: the cases are rare and get sorted out with
  the buyer.
- Upscaling isn't a step of an order: the pages in the owner's Canva books are already upscaled (the Workshop
  upscales new books' pictures itself).
- Picking the spread that doesn't fit a 28-page Gelato book — by hand, in Canva ([decision](../decisions.md)).

More — [known limits](../dev/limits.md).

## Related

- [Orders](../features/orders.md) · [Order Creator](../features/order-creator.md) · [Printer rule](../rules/printer-rule.md)
- [File naming](../rules/file-naming.md) · [Stages](../rules/order-stages.md) · [Known limits](../dev/limits.md)
