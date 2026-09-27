---
title: Order archive — what went to print, and reprints
type: feature
updated: 2026-09-27
code:
  - app/studio/archive.py
  - app/web/js/pages/archive.js
---
# Order archive

> A separate menu on the left. Every book sent to print **from Book Studio**, whose print-shop order is
> **confirmed and paid**, sits here with exactly the files that went to print — so you can see what was
> really printed, and **reprint it in two clicks**.
> Files delete themselves **14 days after the order became "Sent"**.
> Designed and built on 2026-09-18 ([decision](../decisions.md)).

## What goes into the archive

- **Every successful send** from the Order Creator (and from the order card through it): a book in
  Printify (with or without an "On hold" order), a draft in Gelato, a reprint. Failed attempts don't —
  they're visible in the [send journal](send-journal.md).
- **Exactly the files that were sent**: `Cover.png` + `1…N.png` (24 for Printify, 28 or 30 for Gelato) —
  a **copy**, not a link: if the files in your own folder change afterward, the archive stays as it went
  to print. A reprint from the archive takes the same files via a hard link (uses no extra space).
- **Description** (`entry.json`): the printer, the title (`receipt number - name`), the receipt number,
  when, how many pages, the Gelato format, Product ID / Order ID, the shipping address, the send
  journal's record name, whether it's a reprint and of which book, "Keep", when the order became "Sent".
- **Only what really went to print is shown** (the owner's decision, 2026-09-18, `standing()`): files
  are stored at the moment they're sent, but a book appears in the list **once its print-shop order is
  confirmed and paid** (after "Refresh"): Printify — not "on-hold", not "pending", not
  "payment-not-received", not cancelled; Gelato — the draft confirmed as an order, paid, not cancelled
  (`profit.is_placed()`). A draft, unpaid, or cancelled order **doesn't count**: the book isn't in the
  archive, and there's no reprint from it. The exception is "Keep".
- **New ones only**: books sent before 2026-09-18, or created by hand in Gelato, aren't picked up.
- Lives in `app/data/archive/<id>/` (id — `YYYYMMDD-HHMMSS-xxxxxx`); never goes into git. One book is
  ~200–500 MB of real files.

## When files get deleted (`archive.refresh()`)

Checked on program launch and after every order refresh. Rules (`clock()`):

| Book | Counted from | Deleted |
|---|---|---|
| "Keep" | — | never, until the mark is removed |
| Normal | the moment the program **first saw the order as "Sent"** (a box icon) or closed (cancelled, fully refunded) | after **14 days** (`KEEP_DAYS`) |
| Reprint | the moment **the printer shipped the reprint itself** (tracking number or "shipped" status) | after 14 days |
| The program can't track the order: the book isn't from an Etsy order (no receipt number), or the receipt wasn't found among the synced ones | from the send to print | after **30 days** (`LOST_DAYS`) |
| The order isn't "Sent" yet | hasn't started yet | — |
| **Never became an order:** cancelled at the printer, or a draft was deleted (missing from **its own** printer's list, loaded in full at least 2 days after sending, `VANISH_DAYS`) — not shown in the list | the moment the program noticed (`droppedAt`) | after **3 days** (`DROP_DAYS`); until then the files can be taken from the order card |
| A draft, "on hold", or unpaid — not shown in the list | from the send | after 30 days, if it never got confirmed |

- No sync data (Etsy not connected), or it couldn't be read → **nothing gets deleted**, and the list
  shows everything as before.
- **Only a fresh printer list** (the 2026-09-22 audit): the sync records, separately for Etsy, Printify
  and Gelato, when their order list **last loaded in full** (`loaded` in the snapshot, `_loaded()`). A
  printer whose list failed to load (an expired key, a glitch) or was cut off at its cap proves nothing:
  an order missing from a stale list doesn't make a book a "deleted draft". Both "never became an order"
  (3 days) and "never got confirmed" (30 days) only delete files when that printer's list loaded
  **after** the deadline arrived. Before, a fresh list from any printer was enough — and a book that
  went to print in Gelato could lose its files after 5 days of Gelato failing to sync.
- A reprint that never became an order clears its "replacement" mark from the receipt
  (`profit.unmark_reprint()`).
- Pictures are deleted first, the description last: if some file is open in another program, the book
  stays in the list and gets deleted on the next check (`_remove()`).
- Half-copied `.tmp-*` folders (a power cut) are cleared out after an hour.
- Auto-deletion is a **deliberate exception** to the "never delete the owner's data" rule (decision,
  2026-09-18).

## Screen

**The list** (`#/archive`): search (name, receipt number, title; Enter opens the first one), rows like
in the order queue: a thumbnail (the front half of the cover), the buyer's name, `#receipt number` (a
click copies it), the printer chip, "reprint", a tracking number; in gray — "printed … ago" · the
child's name · pages · format; on the right — "N days left" (yellow when ≤ 3) or "keep". Before the
countdown starts — nothing.

**A book** (`#/archive/<id>`):
- header — name, the status of **this** print order, receipt number, "printed …", stage, tracking
  number; on the right, icons for **"Keep"** (a pin), **the files folder**, **the send journal**, and a
  chip "Printify · 24 pages";
- on the left — "What went to print": the cover, the first spread with its note, a filmstrip of every
  spread, the viewer (click); below it, the **"Reprint in Printify/Gelato"** button;
- on the right — "The send" (printer, when, title, Product/Order ID with copying, a link to the first
  send for a reprint, when the files will be deleted, "Open in Printify" / "Gelato Dashboard"),
  personalization from Etsy (if the order is still in the sync), **the shipping address**.
- Esc — back to the list.

## Reprint

"Reprint" opens the [Order Creator](order-creator.md) already filled in: printer, files from the
archive, title, the address it was sent to (can be changed), the Gelato format. A line "Reprint from the
archive…", the button — "Create a reprint order" / "Create a reprint draft". A different folder →
reprint mode is dropped.

- **Printify** (`create_printify_reprint()`): a new "On hold" order for **the same book** already in
  Printify — nothing is uploaded, no product is created (seconds). The same safeguards: address
  required, manual approval, matte variant, no Express. The book no longer exists in Printify → it's
  created again from the archived files (pictures already in Printify aren't duplicated), and a warning
  is shown.
- **Gelato**: a new draft from the archived files (the server takes exactly those, `reprintOf`); the
  archived book has to be from Gelato.
- A reprint is recorded in the accounting as a **replacement** for this receipt
  (`profit.mark_reprint()`): matching keeps the first print order attached to the receipt, so its stage
  in the queue doesn't jump. A receipt with another manual mark (cancelled, refunded) isn't touched.
  Accounting is frozen — nothing deeper is tied to the finances.
- If the first order was **cancelled at the printer** (or doesn't exist), the reprint isn't marked as a
  replacement: it becomes the only live print order, gets matched like a normal one, and the receipt
  moves from "New" to "In progress".
- A reprint is a new record in the archive (`reprintOf`) and in the send journal (`kind: reprint`).
- **Only from a book that really went to print** (`reprintable()`): the server won't make a reprint from
  a send that never became an order (409) — that order is simply sent again from its card.

## Files from an earlier send (the order card)

If a send **never became an order** (cancelled at the printer, a draft was deleted or never confirmed)
and its files are still in the archive, this order's card shows a **"Take files from an earlier send · …
ago"** button in the "Files from Canva" step (only for the chosen printer). The button makes a working
copy in `tmp/dropped` (hard links, `POST /api/archive/<id>/reuse`), and everything else goes as usual:
laying out pages, proofing, "Print" — this is a **normal order, not a reprint**. The list of such sends
is `earlierSends` in `GET /api/orders/<receipt>` (`earlier_sends()`).

The same card also knows the opposite — that a send for this order **is already at the printer** (a
book, draft, or order, not cancelled or deleted): `atPrinter` (`at_printer()`). Then a page replacement
first asks "A draft already exists…", even after the program has been restarted (previously only the
page itself remembered this).

## What the server returns

- `GET /api/archive` → `{entries, keepDays, lostDays}`; each record — `entry.json` + `folder`, `buyer`,
  `stage`, `printStatus` and `tracking` from **its own** print order, `clock`, `deleteAt`, `daysLeft`.
- `GET /api/archive/<id>` → one record the same way (a book that never went to print — 404).
- `POST /api/archive/<id>/keep` `{keep}` → the record.
- `POST /api/archive/<id>/reuse` → `{path}` of a working copy of the files, for the order card.
- `POST /api/creator/printify/reprint` `{archiveId, title, address}` → a background job.
- `POST /api/creator/gelato/create` with `reprintOf` — a reprint draft.

## Where in the code

- [app/studio/archive.py](../../app/studio/archive.py) — `ROOT`, `KEEP_DAYS`, `LOST_DAYS`, `store()`, `update()`, `entries()`, `get()`, `folder()`, `receipt_of()`, `child_of()`, `_facts()`, `_loaded()`, `_reached_buyer()`, `_unknown()`, `standing()`, `shown()`, `clock()`, `refresh()`, `_note()`, `_reprint_mark()`, `refresh_quietly()`, `_remove()`, `summary()`, `_warm_previews()`, `_list()`, `_one()`, `_keep()`, `reprintable()`, `card_facts()`, `_reuse()`, `DROP_DAYS`, `VANISH_DAYS`
- [app/studio/creator.py](../../app/studio/creator.py) — `_to_archive()`, `_mark_reprint()`, `_journaled()`, `create_printify_reprint()`, `_printify_reprint()`, `_reprint_printify()`, `_create_gelato()`
- [app/studio/printorders.py](../../app/studio/printorders.py) — `is_placed()`
- [app/studio/stages.py](../../app/studio/stages.py) — `facts()`, `mark_reprint()`
- [app/studio/records.py](../../app/studio/records.py) — `unmark_reprint()`
- [app/studio/sync.py](../../app/studio/sync.py) — `_sync()` (`loaded` for each list; after a sync — `archive.refresh_quietly()`)
- [app/studio/orders.py](../../app/studio/orders.py) — `_one()` (`earlierSends`, `atPrinter`); [app/web/js/pages/orders.js](../../app/web/js/pages/orders.js) — `earlier()`, `takeEarlier()`
- [app/studio/main.py](../../app/studio/main.py) — `main()` (checking the archive on launch)
- [app/web/js/pages/archive.js](../../app/web/js/pages/archive.js) — `mountList()`, `mountBook()`, `clockChip()`, `clockText()`, `proofCard()`, `reprintCard()`, `sendCard()`, `fieldsCard()`, `addressCard()`, `toggleKeep()`, `reprint()`
- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — reprint mode: `withOrder()`, `createLabel()`, `folderCard()`, `create()`
- [app/web/js/app.js](../../app/web/js/app.js) — `MODES`, `ROUTES`; [app/web/js/icons.js](../../app/web/js/icons.js) — `orderArchive`, `pin`
- [app/web/css/app.css](../../app/web/css/app.css) — `.arc-thumb`, `.arc-id`, `.arc-clock`, `.cr-reprint`
- [app/tools/dev_server.py](../../app/tools/dev_server.py) — `_seed_archive()`, `_sample_book()` (4 made-up books for the preview, and Olivia's draft that never became an order)
- Tests: [app/tests/test_archive.py](../../app/tests/test_archive.py) (`Storing`, `Removing`, `OnlyWhatWentToPrint`, `ReprintMark`, `PrintifyReprint`, `GelatoReprint`), [app/tests/test_flows.py](../../app/tests/test_flows.py) (the archive after a send)

## Related

- [Order Creator](order-creator.md) · [Send journal](send-journal.md) · [Orders](orders.md) · [Stages](../rules/order-stages.md) · [Data](../architecture/data.md)
