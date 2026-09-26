---
title: Order Creator — a book in Printify, a draft in Gelato
type: feature
updated: 2026-09-26
code:
  - app/studio/creator.py
  - app/web/js/pages/creator.js
---
# Order Creator

> The last link in the chain: from a folder of PNGs (`Cover.png` + pages) it creates an unpublished book
> in **Printify** (and, if the address is filled in, an "On hold" order), and a draft order with a PDF
> in **Gelato**. An order with several books goes as **one draft to one address** (since 2026-09-20).
> Nothing is published and nothing goes into production. Opens empty — except for work on a new order,
> which is kept while the order is in "New" (see below).

## Screen (`#/creator`)

- Header: the service name, the **"Send journal"** icon ([send-journal.md](send-journal.md)), and the
  **Printify / Gelato** switch (Printify mode uses a lime-green accent, Gelato — blue, `.creator.mode-gelato`; since 2026-09-25 set
  explicitly, because the Orders mode's own accent is orange). Below it, a line
  appears only when something is missing (a key, the template, `cloudflared.exe`), with a link to
  Settings. For Gelato — active temporary links, if any.
- Left column — the steps:
  - **Printify**: 1 Folder of files → 2 Title → 3 Recipient address → 4 Draft.
  - **Gelato**: 1 Format (Hardcover 8×8, Softcover 8×8, Softcover 5.5×5.5) → 2 Folder → 3 Title →
    4 Address → 5 Draft.
  - **Several books** (came from the card, or added with the "Another book" button): in the "Folders of
    files", "Book titles" and "Book formats" steps — a block per book; one address for all. Clicking a
    book's title ("Book 2") shows its structure on the right; an × removes the book from the list.
    Format buttons show a tooltip with how many pages Gelato prints ("28–200 pages", from the catalog —
    `loadPageCounts()`, only when there's a key); if a folder has 28 pages and the format doesn't accept
    that — the button turns yellow, one sentence appears under it, and "Create" is blocked
    (`formatProblem()`).
- Right column — the **structure**: the cover and every spread with thumbnails; green/red file names
  based on the check result; a click opens the viewer. In the viewer — **page-replacement buttons** (one
  per page of a spread, since 2026-09-20): pick a file on the computer, and the page takes the old one's
  place; "Undo" sits next to it. The folder is re-checked after a replacement. The same exists in the
  [order card](orders.md), except there the text check also restarts. "Undo" is read from disk (the
  `replaced` flag from the file check), so it doesn't disappear after leaving the page or restarting the
  program; **while a draft is being created, replacing and undoing are refused**, because the server is
  reading exactly those files at that moment (since 2026-09-22). For Gelato, before a folder is chosen —
  "28 or 30 pages"; after the check — the exact number from the folder (`pageCount` in the check's
  response).
- **Folder**: pick it, paste a path, or **drag a folder or ZIP** onto the block (the field lights up; it
  shows the folder's own name, and the path is a copy inside the program). The check starts on its own;
  a new check of the same folder (new files, a replaced page) stops the previous one, and a page that
  was closed stops polling it.
- **Title**: `receipt number - child's name` (the receipt button fills in the title and address from an
  Etsy order; in an order with several books, each gets its own child's name).
- **The receipt number is its own field on a book** (`receiptId`, since 2026-09-23): given by the order
  card, or by picking an Etsy order, and the server uses exactly this — not the title — to keep the
  archive, the record of "which print orders belong to which receipt", and Printify's `external_id`. The
  title stays what the owner and the printer see. A title that starts with a **different** number than
  the order's is refused before any upload (`receipt_for()`); a book entered by hand with no order takes
  its number from the start of the title, as before.
- **Address**: an eraser icon clears it. State is required for US, CA, AU. For Gelato, an empty phone →
  the made-up `+1 555 555 0100` (Gelato won't let an order through with no phone).
- **The button**'s label changes: Gelato — "Create draft"; Printify with an address — "Create draft
  order", without one — "Create book without an order".
- **Result**: a card with the ID, checks, warnings; Printify — "Order in Printify" or "Open in Printify";
  Gelato — the PDF's build, a temporary-link timer, and "Gelato Dashboard". Both have a "Send journal"
  icon (`sendLogButton()`); on an error card, it opens the journal folder
  ([send-journal.md](send-journal.md)).

## Picking an Etsy order

The `fromEtsy()` dialog: search, stages "New / In progress / Sent", personalization is collapsed (an
arrow expands the "field: value" list). Opening the dialog doesn't start a sync, only waits for one
already running; the refresh button starts one. Picking an order fills in the title and address
(`addressFromEtsy()`).

## Handoff from the order card

`take('creator')` grabs the card's data once (receipt number, mode, folder, title, format, address) —
and the check starts right away. Visiting the page directly, with no such handoff, leaves it empty.

**Work on an order is saved** (since 2026-09-18, the owner's request): an Order Creator filled from the
card, or by picking a new Etsy order, remembers its order (`st.receiptId`). Switching to another tab, the
owner comes back to the same form, or to the result page (with the Gelato link's countdown still
running), as long as the order is in "New"; after that — an empty page. On success, the order card shows
"Draft … created" (`markSent()`, `sentText()`). **After a successful send, an "× Finish work on this
order" appears in the header** (next to the journal): the page and the card forget the order
(`keep.finish()`), and the queue opens (since 2026-09-20). A new handoff from the card or the archive
replaces the saved one. A reprint from the archive isn't saved (the order is no longer new). How this is
built — [architecture/frontend.md](../architecture/frontend.md).

## Reprinting from the order archive (since 2026-09-18)

The "Reprint" button in the [order archive](archive.md) also passes `reprint: {archiveId, productId}`:
- in the folder block — a line "Reprint from the archive: …", the button — "Create reprint order"
  (Printify, address required — `withOrder()`) or "Create reprint draft" (Gelato);
- Printify goes to `POST /api/creator/printify/reprint`: **a new "On hold" order for the same book**, no
  files are sent, so the file check doesn't block the button; Gelato — the usual creation, with
  `reprintOf` (the server fetches the files from the archive itself);
- a different folder (picked, dragged, or a typed path) drops reprint mode;
- the result card: "Reprint: order created in Printify!" (for the same book — "nothing was uploaded") /
  "Reprint: draft created in Gelato!".

## Printify: what happens on the server

`create_printify_draft(books, job, address)` — `books` is a list of `{folder, title}` (one book, or
every book of a receipt; `books_of()` checks them, `joint_title()` gives a shared title
`4100000001 - Emma, Liam`):
1. If there's an address — it **first** checks everything about the order: the address
   (`validate_address()`), the manual-approval confirmation, whether the Master has a matte variant
   (`matte_variant()`). These checks are one function shared by a normal book and a reprint
   (`_printify_setup()`).
2. A full file check for **every book** (`_printify_files()` → `validate("printify")`): exactly
   `Cover.png` at 4672×2464 and `1…24.png` at 4000×4000, real PNGs, fully decoded, no animation;
   duplicates — a warning. No book is created while another one's files are wrong.
3. Reads the Master, checks the blueprint/provider, saves a snapshot.
4. Every book's images go up first, 3 at a time (`_printify_images()`); already uploaded ones (SHA-256
   cache, checked to still exist in Printify) aren't duplicated. A failure → **no book is made at all**, and
   a retry continues from where it stopped (the 2026-09-26 audit: the books went one after another, so a
   failed upload of book 2 left book 1 made, and the retry made it a second time).
5. Then each book (`_printify_product()`) is made from the Master's configuration
   (`build_printify_payload()`), no auto-retry.
6. Re-reads the book (image positions); the Master — once, after every book (unchanged). The books exist by
   then: a failed read-back is a warning in the result, never a failed send (a retry would make them twice).
7. With an address — **one** order for every book (`_printify_order()` → `create_order_on_hold()`):
   `external_id` = `<receipt>-<8 characters>`, `label` = the shared title, **one line item per book**,
   matte variant, standard shipping, no Express or notifications. An error here doesn't undo the books:
   `orderError` explains what to do.
8. "Result unknown" (the connection dropped after the request was sent, a reply cut short while it was
   read, or the printer answered with 500/502/504) is told apart from a refusal the same way for every send
   (`_unknown_outcome()`): the message says **not to resend**, and to check Printify / Gelato first.

Before the first such order, the interface shows a "Manual order approval in Printify" dialog
(`confirmManualApproval()`), and the server remembers `manualApprovalConfirmedAt`.

## Gelato: what happens on the server

`create_gelato_draft(books, address, job)` — `books` is a list of `{folder, title, format}`:
1. The address, then for every book (`_gelato_book()`) — a light file check (`Cover.png` +
   `1…30.png` or `1…28.png`, no size requirements). The book's own folder decides its length
   (`_gelato_page_count()`): the shortest allowed length that fits the highest page number — `1…27` →
   needs `28`; `1…29` → needs `30`. Two books of one order can be different lengths.
2. Whether Gelato prints that many pages in this format (`gelato_pages_problem()`, the catalog), and the
   book's dimensions (`photobook_geometry()` at the same count). It doesn't print that length → an
   error, nothing is created. The Order Creator page gets the same text ready-made (`problems` in
   `GET /api/creator/gelato/page-counts`, `_pages_problem()`), so the card, the Order Creator, and the
   send itself all say the same thing.
3. A PDF for every book (`build_photobook_pdf()`, `book.pdf` or `book-1.pdf`, `book-2.pdf`…): cover,
   blank endpaper, 28 or 30 pages, blank endpaper — the blank ones are required
   ([integrations/gelato.md](../integrations/gelato.md)); no recompression of images (a Canva PNG gets
   glued into one IDAT chunk — `_one_idat()`), fitted with edges trimmed; a warning only when the cover
   is trimmed by more than 10 mm.
4. One Cloudflare temporary link for all these PDFs (reachability checked, including via public DNS).
5. `create_draft_order()`: `orderReferenceId` = the shared title `<receipt> - <name>` (for several
   books — `<receipt> - Emma, Liam`; so that once confirmed, paid in Gelato and synced, the order moves
   to "In progress"), **one item per book** with its own `pageCount` and its own
   `files: [{type: "default", url}]`, metadata. As soon as Gelato answers, the link goes to the registry —
   the draft exists and still has to fetch its PDFs, so nothing that fails after this point can take them
   away (the 2026-09-26 audit); then the draft is read back for the journal (`_journal_readback()` — one
   record per item; a failed read-back is only a journal note). A reply without the draft's number is a
   "result unknown": don't resend, check Drafts.
6. The link lives for 15 min (`tunnelKeepAliveSeconds`); Gelato fetches the file itself, in about a
   minute.
7. **Result unknown** (Gelato didn't answer within 120 s, the connection dropped, 500/502/504): the draft
   may have been created anyway. Then the PDF link **stays up** for the same 15 min (Gelato can still
   fetch the file), the journal gets `outcome: unknown`, and the message says not to resend until the
   owner has checked Gelato → Orders → Drafts. A real refusal (4xx) — "Gelato rejected…", the link closes
   (the 2026-09-22 audit: before, any error was "rejected", and the link closed right away).

Both kinds of send (Printify and Gelato) write to the [send journal](send-journal.md): the wrappers
`create_printify_draft()` / `create_gelato_draft()` call `_printify_draft()` / `_gelato_draft()` inside
`sendlog.attempt()`; `_journaled()` adds the journal record's name to the result and to the archive.

After a **successful** send, the files go into the [order archive](archive.md) (`_to_archive()`):
Printify — as soon as the book is created (with or without an order), Gelato — as soon as the draft is
created; the book appears in the archive's list once the print-shop order is confirmed and paid. A
reprint — only from a book that really went to print (`archive.reprintable()`). A failed archive write
never undoes the send — a warning appears on the result card instead. A reprint is marked as a
replacement for the receipt (`_mark_reprint()` → `profit.mark_reprint()`), except when the first order
was cancelled at the printer.

The Gelato PDF: cover · blank · pages · blank; the blank pages are white at 300 dpi (`BLANK_DPI`) — why
exactly that — [Gelato](../integrations/gelato.md).

## Where in the code

- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — `structureItems()`, `replacePage()`, `restorePage()`, `pageChanged()`, `mount()`, `renderStatus()`, `folderCard()`, `folderBlock()`, `titleCard()`, `formatCard()`, `addressCard()`, `createCard()`, `resultHtml()`, `renderRight()`, `validate()`, `create()`, `confirmManualApproval()`, `startCountdown()`, `fromEtsy()`, `dropFolder()`, `createLabel()`, `withOrder()`, `pageTotal()`, `loadPageCounts()`, `formatProblem()`, `sendLogButton()`, `sentText()`, `newBook()`, `bk()`, `many()`, `bookName()`
- [app/studio/creator.py](../../app/studio/creator.py) — `replace_page()`, `restore_page()`, `_print_page()`, `_backups()`, `_while_sending()`, `_not_while_sending()`, `REPLACED`, `books_of()`, `receipt_for()`, `joint_title()`, `expected_files()`, `validate()`, `_forget_validation()`, `_validating`, `gelato_page_options()`, `_gelato_page_count()`, `gelato_page_counts()`, `gelato_pages_problem()`, `_pages_problem()`, `create_printify_draft()`, `_printify_setup()`, `_unknown_outcome()`, `_variant_title()`, `_printify_draft()`, `_printify_files()`, `_printify_images()`, `_printify_product()`, `_printify_order()`, `create_printify_reprint()`, `_printify_reprint()`, `_to_archive()`, `_mark_reprint()`, `_remember_sent()`, `_journaled()`, `build_printify_payload()`, `matte_variant()`, `printify_order_payload()`, `validate_address()`, `create_gelato_draft()`, `_gelato_draft()`, `_gelato_book()`, `_journal_readback()`, `build_photobook_pdf()`, `_one_idat()`, `_status()`, `_gelato_page_counts()`, `_etsy_orders()`, `_folder_media()`, `_folder_spread()`
- [app/studio/printify.py](../../app/studio/printify.py) — `create_order_on_hold()`, `upload_exists()`
- [app/studio/gelato.py](../../app/studio/gelato.py) — `page_counts()`, `photobook_geometry()`, `create_draft_order()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `pagesText()`
- [app/studio/sendlog.py](../../app/studio/sendlog.py) — `attempt()`, `step()`
- [app/studio/archive.py](../../app/studio/archive.py) — `store()`, `update()`, `get()`
- [app/web/css/app.css](../../app/web/css/app.css) — `.fmt-pill.bad`, `.cr-reprint`, `.cr-book`, `.cr-book-name`
- [app/web/js/handoff.js](../../app/web/js/handoff.js) — `take()`
- [app/studio/desktop.py](../../app/studio/desktop.py) — `pick_folder()`, `pick_file()`
- Tests: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`PrintifyDraftFlow`, `GelatoDraftFlow`, `CreatorStartsEmpty`, `DroppedFolders`), [app/tests/test_library_creator.py](../../app/tests/test_library_creator.py) (`PrintifyValidation`, `GelatoValidation`), [app/tests/test_archive.py](../../app/tests/test_archive.py) (`PrintifyReprint`, `GelatoReprint`)

## Related

- [Printify](../integrations/printify.md) · [Gelato](../integrations/gelato.md) · [Security](../security.md) · [Dragging files](../flows/dropped-files.md) · [Orders](orders.md)
