---
title: Order to print
type: flow
updated: 2026-11-12
code:
  - app/web/js/pages/orders.js
  - app/studio/orders.py
  - app/web/js/pages/order-card.js
  - app/web/js/pages/creator.js
  - app/studio/creator/
  - app/studio/archive.py
  - canva-extension/
---
# Order to print

> One path for every order: *Etsy order → Canva → files → proofing → Gelato draft → print*. The buyer's data stays beside the work to be copied, not retyped. Every book is printed by Gelato ([Gelato](../integrations/gelato.md)).

## Canva
The program has no Canva API. A book's passport keeps the template link (`canvaUrl`); the order card opens it. The rest is the Chrome extension ([Canva extension](../features/canva-extension.md)) and the owner's hands.
1. Every book has one template: cover + 30 pages, with `{Name}` throughout. The owner adds "from whom" at the end of the dedication by hand and removes a duplicated "With love, …".
2. «Відкрити шаблон у Canva» opens the link with the order encoded in its `#bs=` part (`canvaLink()`, read by the extension's `early.js`, never sent to Canva). The extension makes the copy, names it `<receipt> - <child>` and deletes its first page.
3. The owner replaces the name with find-and-replace (Ctrl+F); if the dedication was replaced, everything else almost certainly was. A buyer's own dedication is typed in; with `DEFAULT` in the field the standard one stays.
4. The owner downloads PNG (a ZIP): all 30 pages, or 28 without one spread. Some pages are run through Upscayl after Canva; the program ignores the `_upscayl…` tail in names.
5. The card catches that book's ZIP from Downloads by itself (`awaitZip()`, `/api/orders/<id>/canva-zip`) — the same as dropping it. Without a child's name in the order the template opens plain and the ZIP is dropped by hand.

## Steps
| # | Owner | Program | Code |
|---|---|---|---|
| 0 | Starts the program | One sync of Etsy + Gelato; old Printify orders are only read | `startup_sync()` |
| 1 | Orders → New | Receipts with no placed print order, with book and format | `mountQueue()` |
| 2 | Opens an order | Card: the library book by listing, the format by rule ([Gelato](../integrations/gelato.md)), the buyer's fields | `enrich()` |
| 3–4 | Canva (above) | Buttons copy the buyer's values | `canvaLink()` |
| 5 | Drops the ZIP or folder into «Файли з Canva» (or it is caught) | Copied in, laid out as `Cover.png` + `1…N.png`, full check ([Intake](intake.md), [Book files](../rules/book-files.md)) | `takeDrop()`, `arrange_pages()` |
| 6 | Proofs; watches the text-check badge | Cover, first spread with a note, filmstrip of every spread, viewer; the local model checks pages against the passport ([Text check](../features/text-check.md)) | `proofCard()` |
| 6a | Fixes a page in Canva, downloads just that page | «Replace N» in the viewer swaps it, files and text are re-checked, "Undo" next to it | `openFolderViewer()`, `replace_page()` |
| 7 | «Send to print» | The Order Creator opens as the print step (back to the card), prefilled: folder, title `receipt - name`, address, format | `print()`, `take()` |
| 8 | «Create draft» | Gelato: PDF + draft; the sent files are copied into the [archive](../features/archive.md) | `create()`, `create_gelato_draft()` |
| 9 | Opens the draft in Gelato, confirms and pays | Until then the order stays New with a "Draft" chip | [Order stages](../rules/order-stages.md) |
| 10 | Refresh | A placed, paid order moves to In progress; printer status shows; the book appears in the archive | `order_stage()` |
| 11 | When the printer ships: «Позначити в Etsy» tab, copies the tracking number | Tracking or a shipped status puts it on the truck tab | `trackChips()` |
| 12 | Marks shipped on Etsy (Kyiv PC), Refresh | Moves to Sent; its 14-day archive countdown starts | `refresh()` |
| 13 | If a book went wrong: card → «Що пішло в друк · передрук» (or Tools → «Архів друку») → Reprint | A new Gelato draft from the same files, the receipt marked as a replacement. With new files (a fixed cover): «Покласти інші файли й надіслати ще раз» ticks «Передрук» in the Order Creator | `reprint()`, `create_gelato_draft()` |

Steps 9–12 and the stages behind them: [Order stages](../rules/order-stages.md). While an order is New, the card and the Order Creator remember where the owner left off; switching tabs and coming back returns to the same step ([Orders](../features/orders.md)).

**Several books in one order**: steps 3–6 are done per book ("Book 1 / Book 2" switch, each with its own folder, proofing and text check). Step 7 takes every ready book together; step 8 creates one draft with several items to one address. Queue, accounting and archive then see one order with several books.

A separate Order Creator stays for manual cases (a reprint when the files are no longer in the archive, a replacement).

## Left manual
- A custom dedication or afterword from the buyer is not parsed; those cases are rare and are sorted out with the buyer.
- Choosing the spread to drop for a 28-page book is done in Canva ([Book files](../rules/book-files.md)).
- Marking shipped on Etsy: the program never writes to Etsy.

## Why
- One order is one screen: no locks, revisions or file generations; the state comes from Etsy and Gelato facts, not saved states.
- Temp copies are wiped on launch; the only kept files are the archive's, for 14 days after Etsy shows shipped.
- Canva's name step is the riskiest manual one, hence the card keeps all the buyer's data close to copy.

## Where in the code
- [app/web/js/pages/order-card.js](../../app/web/js/pages/order-card.js) — `canvaLink()`, `awaitZip()`, `takeDrop()`, `proofCard()`, `print()`
- [app/web/js/pages/orders.js](../../app/web/js/pages/orders.js) — `mountQueue()`
- [app/studio/orders.py](../../app/studio/orders.py) — `enrich()`, `arrange_pages()`
- [app/studio/creator/gelato_send.py](../../app/studio/creator/gelato_send.py) — `create_gelato_draft()`
- [app/web/js/pages/archive.js](../../app/web/js/pages/archive.js) — `reprint()`
- [canva-extension/order.js](../../canva-extension/order.js) — the order driver (copy, name, delete first page)

## Related
- [Orders](../features/orders.md) · [Order Creator](../features/order-creator.md) · [Intake](intake.md) · [Book files](../rules/book-files.md) · [Order stages](../rules/order-stages.md) · [Known limits](../dev/limits.md)
