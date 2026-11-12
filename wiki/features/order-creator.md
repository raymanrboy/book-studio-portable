---
title: Order Creator
type: feature
updated: 2026-11-12
code:
  - app/web/js/pages/creator.js
  - app/web/js/pages/creator-picker.js
  - app/web/js/pages/gelato-result.js
  - app/studio/creator/
  - app/studio/sendlog.py
---
# Order Creator

> A tool (`#/creator`, «Інструменти» → «Для замовлень») that turns a folder of PNGs (`Cover.png` + pages) into a **Gelato draft** with a PDF. An order of several books goes as one draft to one address. Nothing goes into production: the owner confirms and pays in Gelato. Opened by hand it starts empty; from an order card it is that order's print step.

Every new book goes to Gelato. Printify is read-only from 2026-10-01 on the owner's copy (`printify.readOnlyFrom`); its earlier orders are still read for stage, tracking, cost and archive days. A copy with the date unset (the colleague's) can still send to Printify — see [Printify](../integrations/printify.md). The Printify create and reprint routes exist and answer 403 while `printify.retired()`; the page shows only Gelato (`gelatoOnly` in `creator.js`).

## Screen
- **Two ways in:** from «Інструменти» (header «Order Creator · Друк у Gelato з папки файлів»), or from an order card: then the header shows the buyer, receipt, «back» to the card and the order's path icons, and the rail stays on «Замовлення» (`navFor()`).
- **Header icons:** the send journal (below), and «Завершити роботу над замовленням» after a successful send (`keep.finish()`: page and card forget the order, the queue opens). A line under the header appears only when something is missing (key, template, `cloudflared.exe`), linking to Settings, plus active temporary links.
- **Steps (left):** 1 Format (Hardcover 8×8, Hardcover 11×11, Softcover 8×8, Softcover 5.5×5.5; [Gelato](../integrations/gelato.md)) → 2 Folder → 3 Title → 4 Address → 5 Draft.
  - **Several books** (from the card, or the "Another book" button): a block per book in Folder, Title and Format; one address. A click on a book's name shows its structure; × removes it.
  - A format button's tooltip gives the pages Gelato prints for it (from the catalog, `loadPageCounts()`, only with a key). A folder whose length the format does not accept turns the button yellow, adds one sentence and blocks «Створити» (`formatProblem()`).
- **Structure (right):** cover and every spread with thumbnails, file names green or red by the check; a click opens the viewer with a replace button per page and «Undo» (as in the [order card](orders.md), without the text-check restart). «Undo» is read from disk (the check's `replaced` flag). While a draft is being created, replace and undo are refused. 
- **Folder:** pick, paste a path, or drag a folder or ZIP onto the block ([Intake](../flows/intake.md)); the field shows the folder's name and the copy lives inside the program. The check starts by itself; a new check of the same folder stops the previous one.
- **Title:** `<receipt> - <child's name>`; the receipt button fills title and address from an Etsy order; several books each get their own name.
- **Receipt number** is its own field on a book (`receiptId`), given by the card or the order picker. The server uses it, not the title, for the archive and for "which print orders belong to which receipt". A title that starts with a different number is refused before any upload (`receipt_for()`); a book typed by hand takes its number from the start of the title.
- **Address:** every field has its label above it, required ones are marked, «Створити» with a gap names it and lights it up (`markMissing()`), an eraser clears. State is required for US, CA, AU. An empty phone becomes a placeholder (`GELATO_PLACEHOLDER_PHONE`) because Gelato will not confirm an order without one.
- **Result card** (`gelato-result.js`, one markup shared with the order card): order ID, checks, warnings, the PDF build, a yellow notice with the temporary link's countdown and a close-the-link icon, and the orange «Замовлення в Gelato» button (the Gelato orders list). The journal icon opens that send's record; on an error card, the journal folder.

**Picking an Etsy order** (`pickEtsyOrder()`, `creator-picker.js`): search, stages New / In progress / Sent, personalization collapsed; it lists the queue's own orders with the same counts. Opening it only waits for a running sync; its refresh button starts one. Picking fills title and address (`fillFromOrder()`, `addressFromEtsy()`).

**Hand-over and kept work.** `take('creator')` takes the card's data once (receipt, folder, title, format, address) and the check starts. A form filled from the card or an Etsy order remembers its order (`st.receiptId`) while that order is New: switching tabs returns to the same form or result (the countdown keeps running). On success the card shows "Draft … created" (`markSent()`). A new hand-over replaces the saved one; a reprint from the archive is not saved. How: [Interface](../architecture/frontend.md).

## «Передрук» (sent again)
An order already at the printer and sent again, from its card («Покласти інші файли й надіслати ще раз») or picked in «Заповнити із замовлення Etsy», arrives with `reprintOffered` (every book placed at the printer, `stages._all_placed()`) and `alreadyPrinted` (the book has left the printer, or a reprint is being made). The Draft step then shows a **«Передрук» tick**, set by itself once the book has left the printer; while the first print is paid but still being made it is offered unticked, because a new send may be a correction with the first cancelled. The owner unticks it when it is not a reprint. Ticked, the draft goes with `reprint: true`, button «Створити чернетку-передрук»: the page's own new files, recorded as a replacement of the receipt, not a second sale ([Archive](archive.md)). If the server cannot record it as a replacement (first print cancelled, a state set by hand) the result says so.
**Reprinting from the archive** passes `reprint: {archiveId, …}`: a line "Reprint from the archive: …" in the folder block, button «Create reprint draft»; another folder drops reprint mode. Details: [Archive](archive.md).

## What a Gelato send does (`create_gelato_draft()`)
`books` is a list of `{folder, title, format}`; what every send does the same way is in `sending.py`.
1. Address check, then per book (`_gelato_book()`) a light file check: `Cover.png` + `1…28` or `1…30`, no size demands. The book's folder decides its length (`_gelato_page_count()`): the shortest allowed length that fits the highest page, so `1…27` needs 28 and `1…29` needs 30; two books of one order may differ.
2. Does Gelato print that length in this format (`gelato_pages_problem()`) and the book's dimensions (`photobook_geometry()`). If not, an error and nothing is created. The page gets the same text ready-made (`problems` in `GET /api/creator/gelato/page-counts`), so card, creator and send say the same.
3. A PDF per book (`build_photobook_pdf()`: cover, blank endpaper, pages, blank endpaper; images are not recompressed, a Canva PNG is glued into one IDAT chunk, `_one_idat()`; the cover warns only above 10 mm trim; blanks are white at `BLANK_DPI`, why: [Gelato](../integrations/gelato.md)). pikepdf is pinned in `requirements.txt` so another computer cannot write a different PDF.
4. One Cloudflare temporary link for all PDFs (`tunnelKeepAliveSeconds`, default 900), reachability checked.
5. `create_draft_order()`: `orderReferenceId` = the shared title (`<receipt> - Emma, Liam` for several books, so a paid, synced order moves to In progress), one item per book with its own `pageCount` and file. Once Gelato answers, the link goes to the registry (the draft still has to fetch its PDFs); then the draft is read back for the journal (`_journal_readback()`, a failed read-back is only a note).
6. **Result unknown** (no answer in 120 s, dropped connection, 500/502/504): the draft may exist. The link stays up for the same time, the journal gets `outcome: unknown`, and the message says not to resend before checking Gelato → Orders → Drafts. A POST is never retried. A real refusal (4xx) says "Gelato rejected…" and closes the link.

After a successful send the files go into the [archive](archive.md) (`_to_archive()`); a failed archive write never undoes the send, a warning appears on the card. The archive lists the book once its print order is confirmed and paid.

## Send journal
Every send attempt, failed ones too, is one JSON file: what went out, which files and PDF, what Gelato answered, where it broke. Keys never enter it; buyer addresses do, so it lives only in `app/data` (not in git).
- **Where:** `app/data/logs/sends/YYYY-MM-DD_HHMMSS_<provider>_<title>.json`, the last `KEEP` (400) kept (`sendlog.py`). The icon «Журнал відправок» is always in the creator's header (Explorer highlights the newest record, `latest()`), and result cards have «Журнал відправки» for exactly that send (`POST /api/sends/open` `{file}`).
- **Record:** `provider`, `kind`, `title`, `at`, `seconds`; `ok`, `error`, `errorType`; `folder`, `format`, `books`; `steps`; `request` and `response` (full, with the address); `result` (what the owner saw). A Printify-enabled copy also writes `printify` records.
- **Steps:** `files` (every PNG: pixels, bytes, errors) → `catalog` (product, pages, sizes) → `pdf` (pages, bytes, cover size, mm trimmed) → `link` (each PDF's address, `reachable`) → `readback` (what Gelato recorded: item, pages, file, `fileFetched`), plus the program's own `archive`, `printOrderRemembered`, `reprintMarked`.
- Several books: one record, per-book steps carry `book`. A send stopped at the file check also leaves a record (no `request`). `write()` never breaks a send; on failure it logs "Send journal not written".
- **Why:** a book that looks wrong at the printer must be traceable; the icon is always in the header, not only on result cards.

## Why
- One draft per order and one address; nothing but a draft is ever created.
- After an unknown outcome nothing is resent; duplicates cost money.
- The receipt number is its own field so a wrong title cannot attach a send to another order.
- «Передрук» ticks itself and the owner unticks it; a replacement must not count as a second sale, or the order stays among the shipped and the replacement picker cannot offer it.

## Where in the code
- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — `mount()`, `formatProblem()`, `fillFromOrder()`, `sendLogButton()`
- [app/web/js/pages/creator-picker.js](../../app/web/js/pages/creator-picker.js) — `pickEtsyOrder()`
- [app/web/js/pages/gelato-result.js](../../app/web/js/pages/gelato-result.js) — `gelatoResultHtml()`
- [app/studio/creator/gelato_send.py](../../app/studio/creator/gelato_send.py) — `create_gelato_draft()`, `gelato_pages_problem()`, `GELATO_PLACEHOLDER_PHONE`
- [app/studio/creator/sending.py](../../app/studio/creator/sending.py) — `journaled_send()`, `record_order()`, `receipt_for()`, `_to_archive()`, `_mark_reprint()`
- [app/studio/creator/printfolder.py](../../app/studio/creator/printfolder.py) — `validate()`, `_gelato_page_count()`, `replace_page()`
- [app/studio/creator/photobook.py](../../app/studio/creator/photobook.py) — `build_photobook_pdf()`, `BLANK_DPI`
- [app/studio/sendlog.py](../../app/studio/sendlog.py) — `SENDS`, `KEEP`, `write()`, `attempt()`, `latest()`

## Related
- [Gelato](../integrations/gelato.md) · [Printify](../integrations/printify.md) · [Orders](orders.md) · [Archive](archive.md) · [Order to print](../flows/order-to-print.md) · [Intake](../flows/intake.md) · [Security](../security.md)
