---
title: The order-to-print path, from Etsy
type: flow
updated: 2026-09-27
code:
  - app/web/js/pages/orders.js
  - app/studio/orders.py
  - app/web/js/pages/creator.js
  - app/studio/creator.py
  - app/studio/archive.py
---
# The order-to-print path, from Etsy

> Every order follows one path: *order → Canva → files → proofing → print*, with everything needed kept
> in view the whole time. Designed and built on 2026-09-15 (the first version, that same day); the
> card's layout changed on 2026-09-16. The goal is to remove mistakes from manual work in Canva: the
> buyer's data sits right there, to be copied, not retyped.

## Steps

| # | What the owner does | What the program does | Where in the code |
|---|---|---|---|
| 0 | Starts the program | One sync of Etsy + Printify + Gelato | [sync.py](../../app/studio/sync.py) `startup_sync()` |
| 1 | Opens "Orders" → "New" | A list of receipts with no print order, with book and printer | [orders.js](../../app/web/js/pages/orders.js) `mountQueue()` |
| 2 | Opens an order | The card: the book from the library by listing, the printer by rule, the buyer's fields | [orders.py](../../app/studio/orders.py) `enrich()` |
| 3 | "Open template in Canva" | Opens the link from the book's passport in a browser | [orders.js](../../app/web/js/pages/orders.js) `renderLeft()` |
| 4 | In Canva: a copy of the template, `{Name}` → the name, the dedication, download PNGs (for Printify — 24 pages; for Gelato — 30, or 28 without one spread). A hardcover, for now (since 2026-09-25): the owner picks the printer by what he downloads — 24 → Printify, 28/30 → Gelato ([printer rule](../rules/printer-rule.md)) | — (copying values with buttons in the card) | [integrations/canva.md](../integrations/canva.md) |
| 5 | Drags the ZIP/folder into "Files from Canva" | Copies it into the program, lays out `Cover.png` + `1…N.png`, a full check | [orders.js](../../app/web/js/pages/orders.js) `takeDrop()`; [orders.py](../../app/studio/orders.py) `arrange_pages()` |
| 6 | Proofs it; watches the text-check badge | The cover, the first spread with its note (name, fields), a filmstrip of every spread, the viewer; meanwhile the local model reads the pages and checks them against the book passport (~20–50 s), problems as a list and outlines on the pages ([text check](../features/text-check.md)) | [orders.js](../../app/web/js/pages/orders.js) `proofCard()` |
| 6a | Found a mistake — fixes the page in Canva, downloads **just that page** | A "Replace N" button in the viewer: the page takes the old one's place, files and text are checked again, "Undo" sits next to it | [orders.js](../../app/web/js/pages/orders.js) `replacePage()`; [creator.py](../../app/studio/creator.py) `replace_page()` |
| 7 | "Send to print in …" | The Order Creator is filled in: mode, folder, title `receipt - name`, address, format | [orders.js](../../app/web/js/pages/orders.js) `print()`; [handoff.js](../../app/web/js/handoff.js) `take()` |
| 8 | "Create draft (order)" | Printify: a book + an On-hold order; Gelato: a PDF + a draft. A copy of the files that went to print goes into the [order archive](../features/archive.md) | [creator.js](../../app/web/js/pages/creator.js) `create()`; [creator.py](../../app/studio/creator.py) `create_printify_draft()`, `create_gelato_draft()` |
| 9 | In Printify — "Submit order"; in Gelato — open the draft in the Dashboard (while the link is alive), confirm and pay | Until then the order stays in "New" with a "Draft" / "On hold" chip: a draft doesn't count | [integrations/printify.md](../integrations/printify.md), [integrations/gelato.md](../integrations/gelato.md) |
| 10 | Clicks "Refresh" | A confirmed and paid order moves to "In progress" (the receipt number is in the reference / title); the printer status shows on the right; the book appears in the order archive | [stages.py](../../app/studio/stages.py) `order_stage()`; [printorders.py](../../app/studio/printorders.py) `is_placed()` |
| 11 | Once the printer ships it — opens the truck tab, clicks to copy the tracking number | An order with a tracking number or "shipped" status is on the truck tab, with a carrier and a number | [stages.py](../../app/studio/stages.py) `order_stage()`; [orders.js](../../app/web/js/pages/orders.js) `trackChips()` |
| 12 | Marks the order shipped on Etsy (on the Kyiv PC), then clicks "Refresh" | The order moves to "Sent" (a box); its 14-day countdown starts in the order archive | [rules/order-stages.md](../rules/order-stages.md); [archive.py](../../app/studio/archive.py) `refresh()` |
| 13 | If something happened to the book — "Order archive" → the book → "Reprint" | Printify: a new On-hold order for the same book; Gelato: a new draft from the same files; the receipt is marked as a replacement | [archive.js](../../app/web/js/pages/archive.js) `reprint()`; [creator.py](../../app/studio/creator.py) `create_printify_reprint()` |

While the order is in "New", the card and the Order Creator remember with it where the owner left off:
he can switch to another tab and come back to the same step, even a page showing a successful creation
([features/orders.md](../features/orders.md)).

**Several books in one order** (since 2026-09-20): the owner goes through steps 4–6 for each book
separately — a "Book 1 / Book 2" switch in the card, each with its own folder, its own proofing and its
own text check. Step 7 takes **every ready book** together, step 8 creates **one** draft to one address
(Printify — a product per book and one order with several line items; Gelato — one draft with several
items). After that, the path is the same: in the queue, in the accounting and in the archive, it's one
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
- Upscaling with Upscayl — manual for now.
- Picking the three spreads that don't fit the 24-page version — still manual, in Canva. The same goes
  for the spread that doesn't fit a 28-page Gelato book ([decision](../decisions.md)).

## Known limits

- Orders with several books: a "Book 1 / Book 2" switch, each book going through the path separately;
  full support (each copy's own personalization) is in the [plans](../plans/roadmap.md).
- A book created in Printify with no order doesn't move the receipt to "In progress".

## Related

- [Orders](../features/orders.md) · [Order Creator](../features/order-creator.md) · [Printer rule](../rules/printer-rule.md)
- [File naming](../rules/file-naming.md) · [Stages](../rules/order-stages.md) · [Plans](../plans/roadmap.md)
