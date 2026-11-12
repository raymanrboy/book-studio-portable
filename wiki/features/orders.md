---
title: Orders
type: feature
updated: 2026-11-12
code:
  - app/web/js/pages/orders.js
  - app/web/js/pages/order-card.js
  - app/web/js/order-bits.js
  - app/web/js/keep.js
  - app/studio/orders.py
  - app/web/js/order-history.js
---
# Orders

> The start screen (`#/orders`, rail «Замовлення», Alt+1): the queue of Etsy orders by stage, and a card (`#/orders/<receipt>`) that carries one order through *book and Canva → files → proofing → print*. Nothing is saved to disk: it is drawn from the sync snapshot and the library; unfinished work lives in memory. Step by step: [Order to print](../flows/order-to-print.md).

Every new book goes to Gelato. Printify is read-only from 2026-10-01 on the owner's copy (`printify.readOnlyFrom`); its earlier orders are still read for stage, tracking, cost and archive days. A copy with the date unset (the colleague's) can still send to Printify — see [Printify](../integrations/printify.md). A Printify order keeps its Printify chip and has no history card.

## Queue

- **Tabs** (icons with counters; the chosen one shows its word): new (spark) · printing (hourglass) · truck · sent (box) (`STAGES`, `countStages()`, `inTab()` in `order-bits.js`). The truck holds orders the printer has shipped but Etsy is not told; while it holds any, its count takes the ink. Rules: [Order stages](../rules/order-stages.md).
- "In progress" means a confirmed, paid order at the printer. A Gelato draft stays in New with a status chip; a cancelled order goes back to New with no chip.
- Toolbar: search (buyer or receipt; Enter opens the first match) and the refresh icon.
- **A row**:
  - top line: buyer, `#receipt` (a click copies the number without "#", `receiptCopy()`), number of books if more than one, the printer chip (for New the printer the rule gives; otherwise where it went), the tracking chip (`trackChips()`: a click on the carrier copies the carrier, on the number or truck the number, as they are two Etsy fields; copying never opens the card);
  - grey line: time, the child's name in bold, the book title or "book not in the library", city and country;
  - right: the printer status (`statusChip()`, the printer's own word, a dot coloured by meaning) and chips: ship-by (`shipByChip()`: plain, amber on the last day, red once past), red «Payment refused», amber draft older than 12 h, amber «1/2» when only some books are ordered (`booksChip()`; also listed under New), other sends still at the printer (`pendingChips()`), «+N more in print» (N more print orders for the receipt), «передрук» while a reprint is made (no ship-by chip then).
- **Refresh.** The page never syncs by itself (it waits for a running one); the refresh icon starts one (`orderSync()`, shared with the Order Creator). A list left open follows the hourly sync: `watchSyncs()` asks `GET /api/profit/sync` every 60 s while the window is shown and reloads when a newer sync has ended ([Sync](../rules/sync-policy.md)). Rows ignore clicks for 0.45 s after they move (`holdClicks()`).
- **The queue remembers** its tab, search and scroll (`queueState`, in memory only); Back, Esc in the card and the «Замовлення» icon return there.

## Card

- **Layout:** work left (`#oc-flow`), data right (`#oc-data`, sticky, never its own scroller; `stickyFit()` in `lib.js`); one column below 1100 px.
- **Header:** buyer's name with the printer-status chip beside it; in grey the receipt (click copies), time, stage (`STAGE_LABEL`), tracking chip; right, a chip «Gelato · 28 or 30 pages» (exact count once files are laid out). After sending, the chip names the printer the order really went to (`o.provider`). In-progress, truck and sent orders warn to print again only for a reprint (the truck adds: mark it shipped on Etsy).
- **Path strip** (`renderPath()`, `path.js` shared with the Workshop): icons for the shown book (Canva, files, text check, printer, truck): filled = done, ringed = next, red = problem; the tooltip has word and count; a click does the step or scrolls to its card.
- **Finish:** a check-circle icon, tooltip «Завершити роботу над замовленням», appears once a draft exists (`sentOf()`, `renderFinish()`); `keep.finish()` makes the card and the Order Creator forget the order and opens the queue.
- **Canva button** «Відкрити шаблон у Canva» hands the order to the [Canva extension](canva-extension.md): the template link carries `#bs=…` (receipt, child, copy name, book). Then each book waits for its ZIP: `awaitZip()` polls `…/canva-zip?title=` every 2.5 s for 3 hours (`orders.find_canva_zip()`) and takes it like a dropped one. Files put in by hand end the wait; with no child's name the template opens plain.
- **State is kept while the order is New** (`keep.js`: `settle()`, `sentOf()`, `keptOrder()`, `finish()`): switching tabs hides the card and it returns as it was (files, proofing, scroll). Cards with no work are kept only for the last `IDLE_KEPT`. Released when the order leaves New or the program restarts ([Interface](../architecture/frontend.md)).
- **Printed order** (`printedHtml()`): a strip with date, pages, format, an icon to its [archive](archive.md) entry and «other files» (the files flow, folded).
- **Several prints, a tab each** (`printsTabs()`; `stages.prints()` gives `first` / `more` / `reprint`, oldest first, the newest open): a tab switches the status chip, tracking, strip (date, pages, format, cost, archive entry) and history (`/history?order=`); labels are "Print · date", "Reprint · date".
- **Temporary link:** a Gelato draft's green result card (`gelatoResultHtml()`: countdown, order ID, journal, «Надіслати ще раз») stays in the print step while the link lives, also after finishing. The server reports open links (`card_facts()` → `links`), so a green strip «Тимчасове посилання … ще працює — mm:ss» with «Файли забрано — закрити посилання» shows on any step; links end with the program ([Gelato](../integrations/gelato.md)).

### Data column (`renderLeft()`)
- **Book:** cover and title from the library (link to the passport), the Canva button (no link → "add a link"; no book → "go to library").
- **Personalization:** every field as Etsy gives it, with a copy button; the child's name larger; the cover-format field has no copy (it only picks the format); a non-default dedication gets a "custom text" tag. The server decides name and custom text (`orders.enrich()`, `wording.py`, the same rules the text check uses).
- **Buyer's message** and **shipping address** from Etsy.
- **History** (`order-history.js`, `mountHistory()`): for a placed Gelato order only, a card beside the data: Gelato's events as a timeline (newest first), «Очікується до …» when Gelato gives a date, icons for the carrier's page and refresh. It is asked for when the card opens, for that one order, never at launch or for the queue; a failure shows in the card. The server caches a read for `HISTORY_FRESH` seconds, a finished order's until the program closes (`GET /api/orders/<receipt>/history?fresh=1&order=`; `{available: false}` for a new, Printify or unknown order).

### Work column (`renderRight()`)
1. **Files from Canva** (`filesCard()`): drop a ZIP or folder, or pick a folder. The server lays pages out as the cover plus 28 or 30 pages (`arrange_pages()`, [Book files](../rules/book-files.md)), reports what it renamed, runs the full check, and asks Gelato's catalog whether that length prints in the order's format (`gelato_pages_problem()`; an error shows in the block). Loose pictures dropped on a prepared book destroy nothing: the card suggests replacing one page in the viewer. If an earlier send never became a print order, «Взяти файли минулої відправки · <ago>» takes its files from the [archive](archive.md) as an ordinary new order (`earlier()`, `takeEarlier()`).
2. **Proofing** (`proofCard()`, after a successful check): the cover full width; the first spread whose left half (blank in print) is the **note** (child's name large, the buyer's fields; a long dedication scrolls inside); a filmstrip of every spread; a viewer by spreads on any click (key T shows what the text check read against the passport).
   - **Replace one page from the viewer:** one button per page of the spread, the file picked in the Windows dialog; the file check and text check re-run for that page and its "not an error" marks clear. «Undo» (the previous page waits in a hidden `.replaced` folder) rolls back step by step and survives restarts (the check's `replaced` flag). If a draft exists the card asks first (`atPrinter`). During a send both are refused.
   - **Text check:** starts after the file check (`startCheck()`): a badge by the «Вичитка» heading, a problem list (click opens the page; ✓ «not an error»), outlines on pages; closing the card, other files or another book stop it. Rules and the «Це не та книга!» banner: [Text check](text-check.md).
3. **Print** (`printCard()`, `#oc-print`): «До друку в Gelato» (with « · N книг» for several) opens the [Order Creator](order-creator.md) as this order's print step, filled with receipt, buyer, title `<receipt> - <name>`, address, format and files (`print()` → `give('creator', …)`; the rail stays on «Замовлення»). **One review before the send** lists what was noticed, most serious first: not every book ready, text still checking, mistakes, another book's pages. Buttons: «Все одно до друку» (red for mistakes or a wrong book), «Відправити готові», «До друку». Nothing noticed, no question.

### Several books
One receipt with several line items (usually one book for different children) goes as one draft to one address.
- Each book has its own work record (`work[]`): its folder, file check, proofing and text check; the «Book 1 / Book 2» switch (above the files step and in the data column) shows one; a hidden book's text check keeps running.
- The print step lists which books are ready. «До друку» takes every ready book (`readyBooks()`); if not all are ready it asks to send just these, the rest becoming a separate order. Titles: `<receipt> - Emma`, `Emma (2)` for two children of one name.

## Endpoints
`GET /api/orders` → `{orders, syncedAt}` (`picker_orders()` + `enrich()`: per book `book`, `plan`, `childName`; per order `pageOptions`); `GET /api/orders/<receipt>` adds `buyerMessage`, `earlierSends`, `atPrinter`, `printed`, `prints`, `links`; `POST …/files`, `POST …/textcheck`, `GET …/canva-zip`, `GET …/history`.

## Why
- Shown, not told: icons with counters; everything needed to mark an order in Etsy is a copyable chip.
- History is asked per card, never scanned at launch.
- Replace and undo are refused during a send (the printer would get unchecked files); the review dialog only asks, printing is never blocked.
- The right column is never its own scroller: it would trap the wheel at its end.

## Where in the code
- [app/web/js/pages/orders.js](../../app/web/js/pages/orders.js) — `mountQueue()`, `queueState`
- [app/web/js/pages/order-card.js](../../app/web/js/pages/order-card.js) — `mountCard()`, `proofCard()`, `printCard()`, `awaitZip()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `STAGES`, `inTab()`, `statusChip()`, `watchSyncs()`
- [app/web/js/order-history.js](../../app/web/js/order-history.js) — `mountHistory()`
- [app/web/js/keep.js](../../app/web/js/keep.js) — `settle()`, `finish()`, `IDLE_KEPT`
- [app/studio/orders.py](../../app/studio/orders.py) — `plan_for()`, `enrich()`, `arrange_pages()`, `find_canva_zip()`
- [app/studio/stages.py](../../app/studio/stages.py) — `picker_orders()`, `prints()`
- [app/studio/archive.py](../../app/studio/archive.py) — `card_facts()`

## Related
- [Order to print](../flows/order-to-print.md) · [Order stages](../rules/order-stages.md) · [Order Creator](order-creator.md) · [Archive](archive.md) · [Text check](text-check.md)
