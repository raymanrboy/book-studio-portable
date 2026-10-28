---
title: Orders — the queue and the order card
type: feature
updated: 2026-10-28
code:
  - app/web/js/path.js
  - app/studio/orders.py
  - app/web/js/pages/orders.js
  - app/web/js/pages/order-card.js
  - app/web/js/order-bits.js
  - app/web/js/order-history.js
  - app/web/js/folder-viewer.js
  - app/web/js/handoff.js
  - app/web/js/keep.js
---
# Orders

> The start screen. The queue of Etsy orders by stage, and a card that carries one order through
> *book and Canva → files → proofing → print*. Saves nothing to disk: everything is drawn from the sync
> snapshot and the library (unfinished work on a new order lives only in memory). Step by step —
> [flows/order-to-print.md](../flows/order-to-print.md).

## Queue (`#/orders`)

- **The tabs** on their own row under the title: icons with counters — **new (a spark) · printing (an hourglass) · the
  truck · sent (a box)** — and the chosen one shows its word (`compact`); a tooltip names the others. The truck is the
  owner's to-do: the printer has already shipped it, but Etsy hasn't marked it yet — **its count takes the ink while it
  holds something** ([rules/order-stages.md](../rules/order-stages.md)). The owner: shown, not told — no words on every tab, no next-step sentence on a row;
  everything for marking it in Etsy is in the row's copyable chips.
- Toolbar: search (buyer name or receipt number; Enter opens the first one; it only hides rows of the tab, drawn once —
  no thumbnail reloads as you type) and the refresh **icon**.
- **"In progress" only means a confirmed and paid** order at the printer ): a Gelato
  draft or Printify "On hold" leaves the order in "New" with a printer-status chip (`Draft`, `On hold`),
  until the owner confirms and pays for it and clicks "Refresh". A cancelled one goes back to "New" with
  no chip.
- A row:
  - top row: the buyer's name, `#receipt number` (**a click copies the number without "#"**,
    `receiptCopy()`), the number of books (if > 1), the printer chip (for "New" — from the rule, with an
    explanation in the tooltip — Gelato; after that — where it was actually ordered, so an order printed earlier in
    Printify keeps its chip), the **tracking chip** (`trackChips()`): a truck icon, carrier | number,
    separated by a thin line; **a click on the carrier copies the carrier, on the number (or the truck)
    — the number** (two separate fields in Etsy; the part under the cursor is
    underlined); on a narrow window the chip wraps to its
    own line. Copying (`copyChip()`, `data-act="copy-text"`) doesn't open the card;
  - the printer name, carrier and number are all **one soft shade** of the printer's color (80% of the
    color, medium weight): the owner asked for equal contrast and picked the softest option;
  - the gray row: the time · **the child's name, bold** · the book's title or "book not in the library" ·
    city, country;
  - on the right — the **printer status** (`statusChip()`), then the next step: the Printify/Gelato word in English, but in
    plain language (`statusText()`: `in_transit` → "In transit", `has-issues` → "Has issues") with a
    dot colored by meaning (`statusTone()`: a problem — yellow, shipped/delivered — green, draft/on
    hold/pending — gray, everything else — light blue). "New" orders don't have a status yet.
  - A **clock chip** with Etsy's ship-by date (`shipByChip()`: plain,
    amber on its last day, red once past — late marking counts against the shop), a red **«Payment refused»** when Gelato
    could not take the money, an amber draft older than 12 hours (`statusChip()`), and **«1/2»** in amber on an order of
    several books only some of which are ordered (`booksChip()`; listed under «Нові» too — `inTab()`), the status chips of
    its other sends still waiting at the printer (`pendingChips()`). **A list left open follows the hourly sync**
    (`watchSyncs()`: once a minute, while the window is shown, it asks `GET /api/profit/sync` — now with `syncedAt` — and
    fetches the orders again when a newer sync ended) — [rules/order-stages.md](../rules/order-stages.md).
  - Every text in the top row sits on one baseline (not aligned to the top edge of the chips) — the
    owner's requirement.
- **The queue remembers where the owner was** (the owner's request): the tab, the search, and
  the scroll position. The "back" arrow and Esc in the card, and the "Orders" icon from another page, all
  go back to the same place, not to "New"; rows don't "slide in" again on return (`queueState`). Memory
  only — the program starts on "New".
- Refresh: the page itself **never** syncs on its own. Opening it while a sync is running (after launch)
  just waits for it; the button starts a new one. This is one shared function with picking an order in
  the Order Creator (`orderSync()`), not two separate copies.
- After a refresh, rows that moved don't respond to clicks for 0.45 s (`holdClicks()`) — so a click
  doesn't land on a different buyer.
- Stages, status, and tracking numbers are computed by the server —
  [rules/order-stages.md](../rules/order-stages.md).

## Card (`#/orders/<receipt number>`)

**«Відкрити шаблон у Canva» hands the order to the Canva extension** (`canvaLink()`, `openCanva()`): the template's
link carries `#bs=…` (the receipt, the child, the copy's name `titleOf()`, the book) — the extension makes the copy, names it and deletes
its first page ([canva-extension](canva-extension.md)). Then each book waits for its own ZIP
(`awaitZip()`, `w.zipTimer`: `GET /api/orders/<id>/canva-zip?title=…` every 2.5 s for 3 hours, one look at a time — the newest ZIP in
Downloads named after the book's copy (`canvaTitle()`, «#2» for a second child of one name), saved after the press, its size
still; `orders.find_canva_zip()`, `_is_book_zip()`), and takes it like a dropped one: unpacked, laid out, checked. Files put in by
hand end the wait; no child's name in the order — the template opens without the hand-over and the ZIP is dropped as before. The
download stays in Downloads.

**A "✓ Finish work on this order"** (not an ×: that glyph means «remove» elsewhere) next to the "back"
arrow appears once a draft has been created for the order (`sentOf()`, `renderFinish()`). Clicking it — the card and the
Order Creator forget this order (`keep.finish()`), a toast says it is done, and the queue opens. The owner: "sent it — and closed it."

**A Gelato draft's green card stays in the card while its link lives** (the owner: "щоб він лишався поки
живе посилання"). The print step shows the Order Creator's whole result card (`gelatoResultHtml()`, `markSent()` carries
the result), with the countdown, «Замовлення в Gelato», copying the Order ID and the send journal, and a «Надіслати ще раз»
icon under it. When the link closes, by its timer or the close icon, the step goes back to the short «created» line
(`linkTimer()`, `redrawPrint()`).

**The order's path** (`pathSteps()`, `renderPath()` — the Workshop's strip, [path.js](../architecture/frontend.md)):
five **icons** under the header — Canva · files · text check · printer · truck, for the book shown: filled = done, ringed
and breathing = next, red = a problem; the word and the count («28 стор.», «2 помилки», «підтвердіть») are in the tooltip.
A click does the step: Canva opens the template, the others scroll to their card. The work cards carry the same numbers
(2 Файли з Canva · 3 Вичитка · 4 Друк).

**A printed order** (in «Друкуються» and later; `printedHtml()`): a slim strip with what went to
print (date, pages, format) and two icons — the [archive](archive.md) entry (files, reprint; it goes back to this card) and
«other files» (the files flow, folded until asked, for a send by hand). **The header chip names the printer it really went
to** (`o.provider`); the printer rule's chip appears only while the order is new. The server gives the card `printed` (`archive.card_facts()`).

**Several prints — a tab each** (the owner chose tabs over a list): an order printed more than once
(a reprint, a book sent in another go) has tabs above the strip — «Друк · 08.10», «Передрук · 18.10» (`printsTabs()`), the
newest open. A tab switches the header's status chip and tracking, the strip (date, pages, format, the print's cost, its
archive entry — matched by `orderId`) and the history (`mountHistory(…, printId)` → `/history?order=`; a Printify print has
none, the panel hides). The server gives `prints` (`stages.prints()`: `first` / `more` / `reprint`, oldest first). The queue
row of a reprint being made has a «передрук» chip and no ship-by chip.

Header: the buyer's name and, centered next to it, a printer-status chip (`.ord-title`, the owner's
request); below them, in gray, the receipt number (a click copies it), the time, the stage
(`STAGE_LABEL`), the tracking chip (the same one as in the queue, a click copies it); on the right, a
chip "Gelato · 28 or 30 pages" (the same soft shade; once the files are laid out — the exact number, e.g. "Gelato · 28
pages"; the whole chip's text is one font, so the digits don't "jump" — the owner's note). Every card says
so, a US hardcover too ([printer rule](../rules/printer-rule.md)); an unknown cover type has no switch, it goes to Gelato
and its format is picked in the Order Creator (`planText()`). For "In progress" / the truck / "Sent" — a warning "only print again for
a reprint" (for the truck — also "mark it shipped on Etsy"). Esc — back to the queue.

**The card remembers where the owner left off** (the owner's request): while the order is in
"New", the card isn't destroyed when switching to another tab, it's hidden — and comes back exactly as
it was (files, proofing, the filmstrip's and page's scroll position), whether from the queue or the
"Orders" icon (which, from another tab, leads to the last opened card). After "Print" and creating a
draft in the Order Creator, the "Print" step shows "Draft … created" and a "Result in Order Creator"
button (the same saved Order Creator, with its result); "Send again" is a small button next to it. Cards
with no work (no files, no draft) are only kept for the last three.
All of this is released as soon as the order leaves "New" (the next refresh finds it at the printer), or
after the program restarts. How this is built —
[architecture/frontend.md](../architecture/frontend.md) (`keep.js`).

**Layout** (the owner's request): work on the left, data on the right; the right
column is "sticky" (stays on screen while scrolling through proofing) — **never a scroller of its own** (the owner: the wheel over its cards scrolled it and then stopped at its end, trapping the page); one taller than the window sticks by its
bottom (`stickyFit()` in `lib.js`). On a narrow window (< 1100 px) —
one column.

### Right — data (`#oc-data`, `renderLeft()`)
- **Book**: the cover and title from the library (a link to the passport), an "Open template in Canva"
  button. No Canva link → "Add a Canva link" (into the passport); no book → "Go to library".
- **Personalization**: every field exactly as Etsy returns it (`dl.ord-fields`), values in bold, a copy
  button next to each. The field with the child's name — larger (`.is-name`). The cover-format field
  (`isFormatField()`) — no copy button: it only picks the printer. A dedication that isn't `DEFAULT` →
  a "custom text" tag (`isCustomText()`). Which fields are "custom text", and which one is the child's
  name, is decided by the server (`custom`, `isName` in `orders.enrich()`, rules from `wording.py`) —
  the same rules the text check uses: "“DEFAULT “" or "Dedication and Closing Default" is not custom
  text; the name "Leo." is Leo.
  Several books in an order → a "Book 1 / Book 2" switch (the same one sits above the "Files from
  Canva" step), each going through its own path — see below.
- **Buyer's message**, if any.
- **Shipping**: the address from Etsy.

### Beside the data — the printer's history (`#oc-history`, `order-history.js`)
- **A placed Gelato order's card** (the stage isn't new, `o.provider` is Gelato; Printify's and new orders have none)
  gets a card **Історія** beside the data, as tall as the data column, its list scrolling inside: Gelato's status
  and events as a timeline, newest first, the current one filled (an icon per status, the word in English as in the
  chip, Gelato's own note in grey, the time on the right), and on top «Очікується до …» while Gelato gives a delivery
  date. Two icons: **track** (the carrier's page — the carrier's own scans are there, Gelato's API doesn't give them) and
  **refresh** (asks Gelato again). Under the data when the work flow is open too, and under everything on a narrow window.
- **Asked for when the card opens, one order only** (the owner: "не скануй усе при запуску — я можу почекати
  пару секунд"): a skeleton for a second or two, then the list; never at launch, never for the queue. A failure says so
  inside the card, the refresh icon retries, the rest of the card works. The server keeps a read for a minute
  (`HISTORY_FRESH`), a delivered / cancelled / returned order's until the program closes.
- **What it shows** (`gelato.history()`): the items' `eventLog` (the field names are guessed — time / status / text; the
  shape found is written to `gelato.log` as names only, to read the real ones next time), plus the order's own
  `createdAt` / `orderedAt` / `shippedAt` for what the log lacks, so an order whose log is empty still has a few rows.

### Left — work (`#oc-flow`, `renderRight()`)
1. **Files from Canva** (`filesCard()`): drag a ZIP/folder, or pick a folder. Dropping one or two loose
   pictures onto an already-prepared book **destroys nothing** — the program suggests replacing one page
   in the viewer instead. The
   server lays out the pages (`arrange_pages()`: cover + 28 or 30 pages for Gelato —
   however many were downloaded, see [rules/file-naming.md](../rules/file-naming.md)), shows what it
   renamed ("pages 2–25 → 1–24"), then runs a full check, just like in the Order Creator. For Gelato the
   server immediately asks the catalog whether it prints that many pages in the order's format; if not —
   an error in the same block ([integrations/gelato.md](../integrations/gelato.md)).
   If this order was sent before but **never became a print-shop order** (cancelled, a draft was
   deleted), a **"Take files from an earlier send · … ago"** button appears under the field (`earlier()`,
   `takeEarlier()`): files from the [archive](archive.md) get substituted in, and everything else
   follows as normal — this is a new, ordinary order, not a reprint.
   The text check's model is asked for as soon as a new, unsent order's card opens (`warmModel()`) and again when the
   files come — nothing is shown for it ([text-check](text-check.md)).
2. **Proofing** (`proofCard()`, appears after a successful check; the page scrolls to it on its own):
   - the cover, full width;
   - below it, the first spread, full width: the left half (blank in print) is the **note**: the child's
     name in large type (`.proof-name`) and the buyer's fields in bold, scaling with the spread (`cqw`
     units); the cover format and the name field aren't in the note; long text (a dedication) isn't
     truncated — the note scrolls internally ; the right half is the real page 1;
   - after a page is replaced only that page's pictures load (each page has its own version — `pageVersion()`), the
     flow is redrawn in place and the strip stays where it was; a text-check finding slides in once — the ones shown while the check
     ran stay when it ends (`markSeen()`);
   - a **filmstrip** of every spread (`#oc-strip`): the mouse wheel scrolls it smoothly
     (`smoothWheel()`, no "snapping"), all the way to the last spread; the file check the page asks for makes
     the 1400 px and the 360 px previews (`STRIP_THUMB` = `images.VIEW_SIDES`) from the same decode of each page,
     so they are ready when it ends; a
     send's own check makes none (the PDF or the uploads read every file anyway);
   - clicking anything opens the viewer, by spreads (`folderViewerItems()`; the T key shows what the
     text check read versus what should have been there, `viewerItems()`);
   - **replacing a single page right from the viewer**: buttons at the top, one per
     page of a spread ("Replace 6", "Replace 7"; the cover and outer spreads have one). A click opens
     the regular Windows dialog, and the owner picks the page they just fixed in Canva and downloaded.
     Then the program handles the rest itself: a new picture in the viewer (the address gets a new
     version number `v`, so the browser doesn't show the old one), **a fresh file check**, and
     **restarting the text check** (the model re-checks just this page), and any "not an error" marks
     on this page are forgotten. "Undo" appears next to it — the previous page waits in a hidden
     `.replaced` subfolder. If a draft has already been created — a question first, since the old page
     is sitting at the printer; the card knows this even after the program restarts (`atPrinter` from
     the archive). The question, and any replacement error, appear **above the viewer**.
     **"Undo" survives leaving the card and restarting the program**: whether there's
     anything to undo is decided by the file check (a `replaced` flag on each page), not by the open
     page's memory.
     Replace a page twice — "Undo" rolls it back one step at a time. **While the book is being sent to
     the printer, replacing and undoing are refused** ("wait for the send to finish"): otherwise the
     printer would get files the check never saw;
   - **the text check**: starts on its own as soon as the files are checked
     (`startCheck()`); a badge to the right of the «Вичитка» heading (a percentage → "Text matches" /
     "N errors" / "N questions", ↻), a list of problems under the heading (a click opens the viewer on
     that page, ✓ "Not an error"), red and yellow outlines on pages (`markPages()`), "Update passport"
     for differences from the book's passport. Closing the card, dropping other files, or picking
     another book stops the check (`dropCheck()`); clearing a "Not an error" mark doesn't make the rest
     of the rows "slide in" again. **Another book's pages** — a big red banner
     "Це не та книга!" above the list, with the ordered book's and the look-alike book's covers
     (`wrongBook()`); "Not an error" is also written into the check's journal (`keepMark()`).
     In detail — [text-check.md](text-check.md).
3. **Print** (`printCard()`, `#oc-print`): "Send to print in Gelato" → the Order Creator **as this order's
   print step** (its buyer and path on top, «back» to the card, the rail on «Замовлення»),
   filled in with the receipt number, the buyer, the title `receipt number - name`, the address, the format, and
   the files (`print()` → `give('creator', …)`). **One review before
   the send**: if something was noticed — not every
   book ready, the text still checking, mistakes found, or another book's pages («Це не та книга!») —
   one dialog lists it all, most serious first, with «Все одно до друку» (red when it is the wrong book or mistakes) or
   «Відправити готові» / «До друку». Nothing noticed — no question. Printing is never blocked.

## Orders with several books

> One receipt — several books (2–5 books, usually the same book for
> different children). They go as one **shared draft to one address**, not as separate orders.

- **Every book has its own work record** (`work[]`, one per line item of the order): its own folder, its
  own file check, its own proofing, and its own text check. The "Book 1 / Book 2" switch (above "Files
  from Canva" and in "Personalization") just shows a different one — **nothing is lost**, and a hidden
  book's text check keeps finishing on its own ([the text check](text-check.md)).
- **The "Print" step** for such an order shows a list: which book is ready and which isn't ("no files",
  "checking files", "files failed the check", "printing in Gelato" — if the cover type differs). The
  button reads "Send to print in … · N books".
- **"Print" takes every ready book of the same printer** (`readyBooks()`) and hands them to the Order
  Creator as a list. If not all are ready, it asks: "Send just these? The rest can be sent later — that
  will be a separate order at the printer." The text-check question counts the errors of every book
  being sent.
- **Titles** — `receipt number - child's name`; a number tells apart two children with the same name:
  `… - Emma (2)`.
- **"+N more in print"** — a gray chip next to the printer status in a queue row and
  in the card's header: this receipt has N more print orders besides the one whose status is shown. The
  tooltip says which printers. Where the program learns this, and how it counts the money — see
  [Profit](profit.md).
- Next — the [Order Creator](order-creator.md): one Gelato draft with several items.

## What the server returns

- `GET /api/orders` → `{orders, syncedAt}`; every order from `picker_orders()` (`stage`: `new` /
  `work` / `sent` / `shipped`, `provider`, `printStatus`, `tracking`), extended by
  `enrich()`: for every book — `book` (from the library, by listing number), `plan` (the printer rule;
  `plan.pages` — the list of allowed lengths, `[28, 30]`), `childName`; for the order —
  `pageOptions` (the lengths for each printer, when it's picked by hand).
- `GET /api/orders/<receipt>` → the same, for one order, plus `buyerMessage`, `earlierSends` (sends
  that never became a print-shop order, whose files are still in the archive), `atPrinter` and `printed` (the sends
  that went to print, newest first; each with its `orderId`) — all from `archive.card_facts()`; and
  `prints` — every placed print order of it (`stages.prints()`).
- `GET /api/orders/<receipt>/history` → `{available, status, events, shipments, due}` — Gelato's history of the placed order
  (`?fresh=1` skips the minute's memory; `?order=<id>` — one of the receipt's own prints, a tab); `{available: false}` for a
  new, Printify or unknown one.
- `POST /api/orders/<receipt>/files` `{folder, provider, format}` → `{path, note, renumbered, pageCount, provider}`.
- `POST /api/orders/<receipt>/textcheck` `{folder, pages, pick}` → `{jobId}` (or `{off: true}`, when the
  check is turned off); the job's result — `{mode, issues, pages, skipped, …}` ([text-check.md](text-check.md)).

## Where in the code

- [app/web/js/order-history.js](../../app/web/js/order-history.js) — `mountHistory()`, `rows()`, `iconOf()`
- [app/studio/orders.py](../../app/studio/orders.py) — `_history()`
- [app/web/js/pages/orders.js](../../app/web/js/pages/orders.js) — `mountQueue()`, `queueState`
- [app/web/js/pages/order-card.js](../../app/web/js/pages/order-card.js) — `mountCard()`, `readyBooks()`
- [app/web/js/pages/order-card.js](../../app/web/js/pages/order-card.js) — `pathSteps()`, `renderPath()`, `goStep()`, `printedHtml()`, `openViewer()`, `readings()`, `pageChanged()`, `revalidate()`, `mountCard()`, `renderPlan()`, `renderLeft()`, `renderRight()`, `filesCard()`, `proofCard()`, `printCard()`, `linkTimer()`, `redrawPrint()`, `arrange()`, `takeDrop()`, `takeFolder()`, `earlier()`, `takeEarlier()`, `print()`, `titleOf()`, `providerOf()`, `blank()`, `showing()`, `printsTabs()`, `showPrint()`, `asShown()`, `startCheck()`, `warmModel()`, `checkBadge()`, `checkBody()`, `issueRow()`, `markPages()`, `learnPassport()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — shared with the [order archive](archive.md): `proofHtml()`, `STRIP_THUMB`, `fieldsHtml()`, `addressHtml()`, `etsyAddressLines()`, `svcChip()`, `trackChips()`, `statusChip()`, `statusText()`, `statusTone()`, `STATUS_TONE`, `receiptCopy()`, `copyChip()`, `isFormatField()`, `isCustomText()`, `isNameField()`, `alsoSentChip()`, `restorable()`
- [app/studio/orders.py](../../app/studio/orders.py) — `plan_for()`, `books_by_listing()`, `book_brief()`, `enrich()`, `arrange_pages()`, `page_options()`, `pages_word()`, `_list()`, `_one()`, `_files()`
- [app/studio/stages.py](../../app/studio/stages.py) — `picker_orders()`, `order_stage()`, `print_order()`, `waiting_order()`
- [app/studio/printorders.py](../../app/studio/printorders.py) — `is_placed()`, `all_facts()`, `carrier_label()`
- [app/studio/archive.py](../../app/studio/archive.py) — `card_facts()`, `_reuse()`
- [app/studio/wording.py](../../app/studio/wording.py) — `custom_text()`, `clean_name()`, `guess_child_name()` ("custom text" fields, and the child's name)
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `STAGES`, `STAGE_EMPTY`, `STAGE_LABEL`, `planText()`, `pagesText()`, `addressFromEtsy()`, `orderSync()`, `holdClicks()`, `countStages()`, `emptyOrders()`, `filesBadge()`, `checkNotices()`, `syncOrders()`, `runningSync()`, `watchSync()`, `spreadsOf()`, `folderViewerItems()`, `smoothWheel()`
- [app/web/js/drop.js](../../app/web/js/drop.js) — `receiveDrop()`, `wireFolderDrop()`
- [app/web/js/folder-viewer.js](../../app/web/js/folder-viewer.js) — `openFolderViewer()`, `pageNo()`, `pageWord()` (the viewer with a page replaced and put back — shared with the Order Creator)
- [app/web/js/lib.js](../../app/web/js/lib.js) — `escBack()`, `notFound()` (Esc to the queue; the card that could not open)
- [app/web/js/handoff.js](../../app/web/js/handoff.js) — `give()`
- [app/web/js/keep.js](../../app/web/js/keep.js) — `settle()`, `sentOf()`, `keptOrder()`, `finish()`
- [app/studio/creator/printfolder.py](../../app/studio/creator/printfolder.py) — `validate()`
- [app/studio/creator/gelato_send.py](../../app/studio/creator/gelato_send.py) — `gelato_pages_problem()`
- [app/studio/images.py](../../app/studio/images.py) — `check_png()`, `VIEW_SIDES`
- [app/web/js/icons.js](../../app/web/js/icons.js) — `truck`
- [app/web/css/orders.css](../../app/web/css/orders.css) — `.ord-chips`, `.ord-child`, `.ord-copy`, `.ord-title`, `.ord-track`, `.ord-track-text`, `.ord-carrier`, `.ord-track-sep`, `.ord-track-no`, `.ord-sub`, `.ord-grid`, `.ord-side`, `.proof`, `.proof-note`, `.strip`
- Tests: [app/tests/test_orders.py](../../app/tests/test_orders.py) (including `GelatoLength`), [app/tests/test_states.py](../../app/tests/test_states.py) (`PickerStages`, `SentStage`)

## Related

- [The order-to-print path](../flows/order-to-print.md) · [Printer rule](../rules/printer-rule.md) · [Stages](../rules/order-stages.md)
- [Order Creator](order-creator.md) · [Text check](text-check.md) · [Canva](../integrations/canva.md) · [Known limits](../dev/limits.md)

## The link stays after «Завершити»

A Gelato draft's temporary link to the print files is shown in the order's card (the green card with the countdown) for as long as it lives, also after «Завершити роботу над замовленням»: `keep.finish()` moves the result to `linkOf(rid)`; `order-card.js` `printCard()` / `linkTimer()` read `sentOf(...)?.result || linkOf(...)`. It goes when the link closes or the order is no longer new.

The **server** says it too, so it shows whatever step is on screen: `archive.card_facts()` has `links` (`archive._open_links()`: the open Cloudflare tunnels of `tunnel.registry` matched to this receipt's Gelato sends by order id), and `GET /api/orders/<receipt>` carries it. The card shows a green strip under the path — «Тимчасове посилання на файли для Gelato ще працює — mm:ss» with «Файли забрано — закрити посилання» (`order-card.js` `renderLink()`; the strip hides itself when the print step's own green card is showing). It does not survive closing the program: the tunnels close with it. The link itself — [integrations/gelato.md](../integrations/gelato.md).
