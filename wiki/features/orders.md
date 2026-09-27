---
title: Orders — the queue and the order card
type: feature
updated: 2026-09-27
code:
  - app/studio/orders.py
  - app/web/js/pages/orders.js
  - app/web/js/order-bits.js
  - app/web/js/handoff.js
  - app/web/js/keep.js
---
# Orders

> The start screen. The queue of Etsy orders by stage, and a card that carries one order through
> *book and Canva → files → proofing → print*. Saves nothing to disk: everything is drawn from the sync
> snapshot and the library (unfinished work on a new order lives only in memory). Step by step —
> [flows/order-to-print.md](../flows/order-to-print.md).

## Queue (`#/orders`)

- Toolbar: search (buyer name or receipt number; Enter opens the first one), a stage switch with
  counters **New (a spark) / In progress (a clock) / the truck / Sent (a box)**, an "Update orders"
  button. The truck — the printer has already shipped it, but Etsy hasn't marked it yet: this is how the
  owner knows it can be marked shipped on Etsy
  ([rules/order-stages.md](../rules/order-stages.md)).
- **"In progress" only means a confirmed and paid** order at the printer (since 2026-09-18): a Gelato
  draft or Printify "On hold" leaves the order in "New" with a printer-status chip (`Draft`, `On hold`),
  until the owner confirms and pays for it and clicks "Refresh". A cancelled one goes back to "New" with
  no chip.
- A row (since 2026-09-17 — per the owner's wishes):
  - top row: the buyer's name, `#receipt number` (**a click copies the number without "#"**,
    `receiptCopy()`), the number of books (if > 1), the printer chip (for "New" — from the rule, with an
    explanation in the tooltip; for a hardcover, for now, only the suggestion — the files decide; after that — where it was actually ordered; "printer?" — if the cover
    type couldn't be read), the **tracking chip** (`trackChips()`): a truck icon, carrier | number,
    separated by a thin line; **a click on the carrier copies the carrier, on the number (or the truck)
    — the number** (the owner, 2026-09-25: two separate fields in Etsy; the part under the cursor is
    underlined); on a narrow window the chip wraps to its
    own line. Copying (`copyChip()`, `data-act="copy-text"`) doesn't open the card;
  - the printer name, carrier and number are all **one soft shade** of the printer's color (80% of the
    color, medium weight): the owner asked for equal contrast and picked the softest option
    (2026-09-17);
  - the gray row: the time · **the child's name, bold** · the book's title or "book not in the library" ·
    city, country;
  - on the right — the **printer status** (`statusChip()`): the Printify/Gelato word in English, but in
    plain language (`statusText()`: `in_transit` → "In transit", `has-issues` → "Has issues") with a
    dot colored by meaning (`statusTone()`: a problem — yellow, shipped/delivered — green, draft/on
    hold/pending — gray, everything else — light blue). "New" orders don't have a status yet.
  - Every text in the top row sits on one baseline (not aligned to the top edge of the chips) — the
    owner's requirement.
- **The queue remembers where the owner was** (since 2026-09-19, his request): the tab, the search, and
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

**An "× Finish work on this order"** next to the "back" arrow appears once a draft has been created for
the order (`sentOf()`, `renderFinish()`). Clicking it — the card and the Order Creator forget this order
(`keep.finish()`), and the queue opens. The owner's wish, 2026-09-20: "sent it — and closed it."

Header: the buyer's name and, centered next to it, a printer-status chip (`.ord-title`, the owner's
request, 2026-09-17); below them, in gray, the receipt number (a click copies it), the time, the stage
(`STAGE_LABEL`), the tracking chip (the same one as in the queue, a click copies it); on the right, a
chip "Printify · 24 pages" (the same soft shade) / "Gelato · 28 or 30 pages" (once the files are laid
out — the exact number, e.g. "Gelato · 28 pages"; the whole chip's text is one font, so the digits don't
"jump" — the owner's note, 2026-09-17). **A hardcover, for now (since 2026-09-25):** "Printify · 24
pages" / "Gelato · 28 or 30 pages" — the rule's suggestion (no question mark, the owner's wish) — until the files are
in; then the printer the files decided (24 pages → Printify, 28/30 → Gelato;
[rules/printer-rule.md](../rules/printer-rule.md)). If the cover type is unknown — a printer switch (page options
from the order's `pageOptions`). For "In progress" / the truck / "Sent" — a warning "only print again for
a reprint" (for the truck — also "mark it shipped on Etsy"). Esc — back to the queue.

**The card remembers where the owner left off** (since 2026-09-18, his request): while the order is in
"New", the card isn't destroyed when switching to another tab, it's hidden — and comes back exactly as
it was (files, proofing, the filmstrip's and page's scroll position), whether from the queue or the
"Orders" icon (which, from another tab, leads to the last opened card). After "Print" and creating a
draft in the Order Creator, the "Print" step shows "Draft … created" and a "Result in Order Creator"
button (the same saved Order Creator, with its result); "Send again" is a small button next to it. Cards
with no work (no files, no draft) are only kept for the last three (since 2026-09-19, a code review).
All of this is released as soon as the order leaves "New" (the next refresh finds it at the printer), or
after the program restarts. How this is built —
[architecture/frontend.md](../architecture/frontend.md) (`keep.js`).

**Layout** (since 2026-09-16, per the owner's request): work on the left, data on the right; the right
column is "sticky" (stays on screen while scrolling through proofing). On a narrow window (< 1100 px) —
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
  text; the name "Leo." is Leo (the 2026-09-22 audit: the card and the check used to decide differently).
  Several books in an order → a "Book 1 / Book 2" switch (the same one sits above the "Files from
  Canva" step), each going through its own path — see below.
- **Buyer's message**, if any.
- **Shipping**: the address from Etsy.

### Left — work (`#oc-flow`, `renderRight()`)
1. **Files from Canva** (`filesCard()`): drag a ZIP/folder, or pick a folder. Dropping one or two loose
   pictures onto an already-prepared book **destroys nothing** — the program suggests replacing one page
   in the viewer instead (before 2026-09-20, such a drop used to wipe out all the work on the book). The
   server lays out the pages (`arrange_pages()`: cover + 24 pages for Printify, 28 or 30 for Gelato —
   however many were downloaded, see [rules/file-naming.md](../rules/file-naming.md); a hardcover, for
   now, takes any of 24/28/30 and the length picks the printer — `w.decided`), shows what it
   renamed ("pages 2–25 → 1–24"), then runs a full check, just like in the Order Creator. For Gelato the
   server immediately asks the catalog whether it prints that many pages in the order's format; if not —
   an error in the same block ([integrations/gelato.md](../integrations/gelato.md)).
   If this order was sent before but **never became a print-shop order** (cancelled, a draft was
   deleted), a **"Take files from an earlier send · … ago"** button appears under the field (`earlier()`,
   `takeEarlier()`): files from the [archive](archive.md) get substituted in, and everything else
   follows as normal — this is a new, ordinary order, not a reprint.
2. **Proofing** (`proofCard()`, appears after a successful check; the page scrolls to it on its own):
   - the cover, full width;
   - below it, the first spread, full width: the left half (blank in print) is the **note**: the child's
     name in large type (`.proof-name`) and the buyer's fields in bold, scaling with the spread (`cqw`
     units); the cover format and the name field aren't in the note; long text (a dedication) isn't
     truncated — the note scrolls internally (since 2026-09-18); the right half is the real page 1;
   - a **filmstrip** of every spread (`#oc-strip`): the mouse wheel scrolls it smoothly
     (`smoothWheel()`, no "snapping"), all the way to the last spread; the server prepares 360 px
     thumbnails ahead of time (`STRIP_THUMB` = `STRIP_PREVIEW`) — after the check the page asked for; a
     send's own check doesn't (since 2026-09-25: the PDF or the uploads read every file anyway);
   - clicking anything opens the viewer, by spreads (`folderViewerItems()`; the T key shows what the
     text check read versus what should have been there, `viewerItems()`);
   - **replacing a single page right from the viewer** (since 2026-09-20): buttons at the top, one per
     page of a spread ("Replace 6", "Replace 7"; the cover and outer spreads have one). A click opens
     the regular Windows dialog, and the owner picks the page they just fixed in Canva and downloaded.
     Then the program handles the rest itself: a new picture in the viewer (the address gets a new
     version number `v`, so the browser doesn't show the old one), **a fresh file check**, and
     **restarting the text check** (the model re-checks just this page), and any "not an error" marks
     on this page are forgotten. "Undo" appears next to it — the previous page waits in a hidden
     `.replaced` subfolder. If a draft has already been created — a question first, since the old page
     is sitting at the printer; the card knows this even after the program restarts (`atPrinter` from
     the archive). The question, and any replacement error, appear **above the viewer** (since
     2026-09-23; they used to be hidden underneath it, with keystrokes going to the invisible window).
     For Printify the page has to be 4000×4000: an un-upscaled size will be caught by the file check
     ("run it through Upscayl").
     **"Undo" survives leaving the card and restarting the program** (since 2026-09-22): whether there's
     anything to undo is decided by the file check (a `replaced` flag on each page), not by the open
     page's memory — before this, a copy sat on disk but the button disappeared (found by the audit).
     Replace a page twice — "Undo" rolls it back one step at a time. **While the book is being sent to
     the printer, replacing and undoing are refused** ("wait for the send to finish"): otherwise the
     printer would get files the check never saw;
   - **the text check** (since 2026-09-19): starts on its own as soon as the files are checked
     (`startCheck()`); a badge to the right of the "Proofing" heading (a percentage → "Text matches" /
     "N errors" / "N questions", ↻), a list of problems under the heading (a click opens the viewer on
     that page, ✓ "Not an error"), red and yellow outlines on pages (`markPages()`), "Update passport"
     for differences from the book's passport. Closing the card, dropping other files, or picking
     another book stops the check (`dropCheck()`); clearing a "Not an error" mark doesn't make the rest
     of the rows "slide in" again. **Another book's pages** (since 2026-09-25) — a big red banner
     "Це не та книга!" above the list, with the ordered book's and the look-alike book's covers
     (`wrongBook()`); "Not an error" is also written into the check's journal (`keepMark()`).
     In detail — [text-check.md](text-check.md).
3. **Print** (`printCard()`, `#oc-print`): "Send to print in Printify/Gelato" → the Order Creator,
   filled in with the receipt number, the title `receipt number - name`, the address, the format, and
   the files (`print()` → `give('creator', …)`). The Printify card uses the lime-green accent. If the
   text check is still running, or found something red — a question first ("Send without waiting?" /
   "Print anyway?"; for another book's pages — "Це не та книга!", since 2026-09-25), printing is never
   blocked.

## Orders with several books (since 2026-09-20)

> One receipt — several books (10% of the owner's orders: 2–5 books, usually the same book for
> different children). They go as one **shared draft to one address**, not as separate orders.

- **Every book has its own work record** (`work[]`, one per line item of the order): its own folder, its
  own file check, its own proofing, and its own text check. The "Book 1 / Book 2" switch (above "Files
  from Canva" and in "Personalization") just shows a different one — **nothing is lost**, and a hidden
  book's text check keeps finishing on its own (before 2026-09-22 the code didn't keep this promise:
  the second book used to cut off the first one — found by the audit, see [the text check](text-check.md)).
- **The "Print" step** for such an order shows a list: which book is ready and which isn't ("no files",
  "checking files", "files failed the check", "printing in Gelato" — if the cover type differs). The
  button reads "Send to print in … · N books".
- **"Print" takes every ready book of the same printer** (`readyBooks()`) and hands them to the Order
  Creator as a list. If not all are ready, it asks: "Send just these? The rest can be sent later — that
  will be a separate order at the printer." The text-check question counts the errors of every book
  being sent.
- **Titles** — `receipt number - child's name`; a number tells apart two children with the same name:
  `… - Emma (2)`.
- **"+N more in print"** (since 2026-09-22) — a gray chip next to the printer status in a queue row and
  in the card's header: this receipt has N more print orders besides the one whose status is shown. The
  tooltip says which printers. Where the program learns this, and how it counts the money — see
  [Profit](profit.md).
- Next — the [Order Creator](order-creator.md): Printify makes a product for every book and **one**
  order with several line items; Gelato — one draft with several items.

## What the server returns

- `GET /api/orders` → `{orders, syncedAt}`; every order from `picker_orders()` (`stage`: `new` /
  `work` / `sent` / `shipped`, `provider`, `printStatus`, `tracking`), extended by
  `enrich()`: for every book — `book` (from the library, by listing number), `plan` (the printer rule;
  `plan.pages` — the list of allowed lengths: `[24]` or `[28, 30]`; a hardcover for now — `[24, 28, 30]`
  and `plan.choice`), `childName`; for the order —
  `pageOptions` (the lengths for each printer, when it's picked by hand).
- `GET /api/orders/<receipt>` → the same, for one order, plus `buyerMessage` and `earlierSends` (sends
  that never became a print-shop order, whose files are still in the archive — `archive.earlier_sends()`).
- `POST /api/orders/<receipt>/files` `{folder, provider, format}` → `{path, note, renumbered, pageCount, provider}`;
  `provider: "files"` — a hardcover whose printer the length decides (the answer's `provider`).
- `POST /api/orders/<receipt>/textcheck` `{folder, pages, pick}` → `{jobId}` (or `{off: true}`, when the
  check is turned off); the job's result — `{mode, issues, pages, skipped, …}` ([text-check.md](text-check.md)).

## Where in the code

- [app/web/js/pages/orders.js](../../app/web/js/pages/orders.js) — `openViewer()`, `pageActions()`, `replacePage()`, `restorePage()`, `pageChanged()`, `revalidate()`, `mountQueue()`, `mountCard()`, `renderPlan()`, `renderLeft()`, `renderRight()`, `filesCard()`, `proofCard()`, `printCard()`, `arrange()`, `takeDrop()`, `takeFolder()`, `earlier()`, `takeEarlier()`, `print()`, `readyBooks()`, `titleOf()`, `providerOf()`, `blank()`, `showing()`, `queueState`, `startCheck()`, `warmModel()`, `checkBadge()`, `checkBody()`, `issueRow()`, `markPages()`, `viewerItems()`, `learnPassport()`, `STRIP_THUMB`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — shared with the [order archive](archive.md): `trackChips()`, `statusChip()`, `statusText()`, `statusTone()`, `STATUS_TONE`, `receiptCopy()`, `copyChip()`, `isFormatField()`, `isCustomText()`, `isNameField()`, `alsoSentChip()`, `restorable()`
- [app/studio/orders.py](../../app/studio/orders.py) — `plan_for()`, `books_by_listing()`, `book_brief()`, `enrich()`, `arrange_pages()`, `page_options()`, `pages_word()`, `_list()`, `_one()`, `_files()`
- [app/studio/stages.py](../../app/studio/stages.py) — `picker_orders()`, `order_stage()`, `print_order()`, `waiting_order()`
- [app/studio/printorders.py](../../app/studio/printorders.py) — `is_placed()`, `all_facts()`, `carrier_label()`
- [app/studio/archive.py](../../app/studio/archive.py) — `card_facts()`, `_reuse()`
- [app/studio/wording.py](../../app/studio/wording.py) — `custom_text()`, `clean_name()` ("custom text" fields, and the child's name)
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `STAGES`, `STAGE_EMPTY`, `STAGE_LABEL`, `planText()`, `pagesText()`, `addressFromEtsy()`, `orderSync()`, `holdClicks()`, `syncOrders()`, `runningSync()`, `watchSync()`, `spreadsOf()`, `folderViewerItems()`, `receiveDrop()`, `wireFolderDrop()`, `smoothWheel()`
- [app/web/js/handoff.js](../../app/web/js/handoff.js) — `give()`
- [app/web/js/keep.js](../../app/web/js/keep.js) — `settle()`, `sentOf()`, `keptOrder()`, `finish()`
- [app/studio/creator.py](../../app/studio/creator.py) — `STRIP_PREVIEW`, `_warm_previews()`, `_warm_in_background()`, `guess_child_name()`, `gelato_pages_problem()`
- [app/web/js/icons.js](../../app/web/js/icons.js) — `truck`
- [app/web/css/app.css](../../app/web/css/app.css) — `.ord-chips`, `.ord-child`, `.ord-copy`, `.ord-title`, `.ord-track`, `.ord-track-text`, `.ord-carrier`, `.ord-track-sep`, `.ord-track-no`, `.ord-sub`, `.ord-grid`, `.ord-side`, `.proof`, `.proof-note`, `.strip`
- Tests: [app/tests/test_orders.py](../../app/tests/test_orders.py) (including `GelatoLength`), [app/tests/test_states.py](../../app/tests/test_states.py) (`PickerStages`, `SentStage`)

## Related

- [The order-to-print path](../flows/order-to-print.md) · [Printer rule](../rules/printer-rule.md) · [Stages](../rules/order-stages.md)
- [Order Creator](order-creator.md) · [Text check](text-check.md) · [Canva](../integrations/canva.md) · [Open questions](../plans/open-questions.md)
