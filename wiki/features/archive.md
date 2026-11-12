---
title: Print archive
type: feature
updated: 2026-11-12
code:
  - app/studio/archive.py
  - app/web/js/pages/archive.js
  - app/tools/archive_dedupe.py
---
# Print archive

> **«Архів друку»** (`#/archive`, `#/archive/<id>`; a tool under «Інструменти» → «Для замовлень»). Every book sent to print from Book Studio whose print order is **confirmed and paid** sits here with exactly the files that went to print, so the owner can see what was printed and reprint it. A printed order's card shows the same and leads to its entry. Files delete themselves **14 days after the order is shipped or closed on Etsy** (a reprint: after its own print order ships).

## What is stored
- **Every successful send** from the Order Creator (and from the order card through it), at send time (`sending._to_archive()`). Failed attempts are only in the send journal ([Order Creator](order-creator.md)). Books made by hand at the printer are not picked up.
- **Exactly the files sent:** `Cover.png` + `1…N.png`, a copy, not a link, so later edits in the owner's folder change nothing. Folder `app/data/archive/<id>/` (`YYYYMMDD-HHMMSS-xxxxxx`) with `entry.json`; never in git (a book is hundreds of MB).
- **The same page is kept once.** Pages are shared between children's books and Canva signs each export with its own text, so a page is known by its picture (`page_key()`: the PNG's chunks without the text ones) and a send whose page the archive holds keeps a hard link to that file (`_index()`, `dedupe()`, `archive/pages.json`, refreshed at launch and after each sync). Removing one book leaves the others whole. Library pictures are not hard-linked and PNG pages are not recompressed; the backup packs every name in full. `app/tools/archive_dedupe.py --apply` re-links entries stored without it.
- **`entry.json`:** printer, title (`<receipt> - <name>`), receipt number, time, pages, Gelato format, Product/Order ID, shipping address, the send journal's record name, whether it is a reprint and of which book, `keep`, when the order became Sent.
- **Shown only if the print order is placed** (`standing()` returns counted / waiting / dropped; `printorders.is_placed()`, [Order stages](../rules/order-stages.md)): a draft, unpaid or cancelled order does not count, and there is no reprint from it. "Keep" overrides (`shown()`).

## When files are deleted
Checked at launch and after every sync (`refresh_quietly()`); rules in `clock()` (constants `KEEP_DAYS` 14, `LOST_DAYS` 30, `DROP_DAYS` 3, `VANISH_DAYS` 2):

| Book | Counted from | Deleted |
|---|---|---|
| "Keep" | | never, until the mark is removed |
| Normal | Etsy shipped or closed (cancelled, fully refunded) | after 14 days |
| Reprint | its own print order has tracking or a shipped status | after 14 days |
| No receipt number, or receipt not among synced orders | the send | after 30 days |
| Never became an order (missing from **its own** printer's list, loaded whole at least 2 days after the send); not shown | the moment noticed (`droppedAt`) | after 3 days; until then the files can be taken from the order card |
| Draft, on hold or unpaid, never confirmed; not shown | the send | after 30 days |
| Order not yet Sent | not started | |

- No sync data (Etsy not connected) or unreadable: **nothing is deleted**.
- **Only a fresh printer list proves anything.** The sync records per service when its list last loaded whole (`loaded`, `_loaded()`). A list that failed or hit its cap proves nothing; "never became an order" and "never confirmed" delete only when that printer's list loaded after the deadline.
- A reprint that never became an order clears its "replacement" mark (`records.unmark_reprint()`).
- Pictures go first, the description last (`_remove()`); a file held open elsewhere keeps the entry for the next check. `.tmp-*` leftovers are cleared after an hour.

## Screen
- **List:** search (name, receipt, title; Enter opens the first; it only hides rows), a thumbnail (front half of the cover), buyer, `#receipt` (click copies), printer chip, "reprint", tracking; grey: "printed … ago", child, pages, format; right: "N days left" (yellow at 3 or less) or "keep", nothing before the countdown starts. Previews are made before the page opens (`images.copy_previews()` reuses the card's).
- **Book:** opened from its order's card, Back and Esc return to the card and the rail stays on «Замовлення» (`navFor()`); from the list, to the list. Header: name, the status of **this** print order, receipt, "printed …", stage, tracking; icons «Keep» (pin), files folder, send journal. Left: "What went to print" (cover, first spread with its note, filmstrip, viewer) and the reprint card (`reprintCard()`). Right: "The send" (printer, time, title, Product/Order ID, link to the first send for a reprint, when files go, the Gelato orders list), Etsy personalization if still synced, the shipping address.
- An archived Printify book has no reprint button, only a note that Printify no longer prints; its reprint starts from the order's card with a Gelato-sized book ([Printify](../integrations/printify.md)).

## Reprint
«Передрук у Gelato» opens the [Order Creator](order-creator.md) filled in: files from the archive, title, the address it went to (editable), format. The server (`POST /api/creator/gelato/create` with `reprintOf`) takes exactly those files and refuses if the entry's printer is not Gelato.
- **Only from a book that went to print** (`reprintable()`, 409 otherwise); a send that never became an order is simply sent again from its card.
- **A reprint is a replacement, not a second sale.** `_mark_reprint()` → `stages.mark_reprint()` records it for the receipt, so matching keeps the first print order and the stage does not jump; a receipt with another manual state (cancelled, refunded) is untouched. If the first order was **cancelled at the printer** (or missing), the reprint is not marked: it is the only live print order and moves the receipt from New to In progress. While the reprint is placed and unshipped the order shows «Друкується» with a «передрук» chip ([Order stages](../rules/order-stages.md)).
- **A reprint with new files** (a cover fixed after a complaint) goes from the order card via the Order Creator's «Передрук» tick: the new files are sent, the record has `reprint: true` and `reprintOf` (the first print's book while archived, `printed_before()`). `is_reprint()` treats both kinds alike: 14 days start from its own shipment, replacement mark, chip.
- A reprint is a new archive entry (`reprintOf`) and a send-journal record.

## Files from an earlier send
If a send never became an order and its files are still here, the order card's files step offers «Взяти файли минулої відправки · <ago>» (only for the chosen printer). `POST /api/archive/<id>/reuse` makes a hard-link working copy in the drops folder (`drops.DROPS`) and the order goes on as an ordinary new one. For several books only the send with that book's own name is offered (`child_of()`). The listing is `earlierSends` in `GET /api/orders/<receipt>`; the opposite fact, a send already at the printer, is `atPrinter` (a page replacement then asks first). Both come from `card_facts()`, with `printed` and `links`.

## Endpoints
`GET /api/archive` → `{entries, keepDays, lostDays}` (each entry: `entry.json` + `folder`, `buyer`, `stage`, `printStatus` and `tracking` of its own print order, `clock`, `deleteAt`, `daysLeft`); `GET /api/archive/<id>` (404 if it never went to print); `POST /api/archive/<id>/keep` `{keep}`; `POST /api/archive/<id>/reuse` → `{path}`.

## Why
- Auto-deletion is a deliberate exception to "never delete owner data": the files are huge, and buyers notice mistakes up to about 20 days after delivery.
- Only placed and paid books are listed and a stale printer list proves nothing, because an outage or a cut-off list must never read as "the book never became an order".
- A reprint is a replacement so the receipt's stage does not jump and the sale is not counted twice.
- The archive holds copies of what was printed, not links to the owner's working folder.

## Where in the code
- [app/studio/archive.py](../../app/studio/archive.py) — `clock()`, `standing()`, `refresh_quietly()`, `reprintable()`, `card_facts()`
- [app/web/js/pages/archive.js](../../app/web/js/pages/archive.js) — `mountList()`, `mountBook()`, `reprintCard()`
- [app/studio/creator/sending.py](../../app/studio/creator/sending.py) — `_to_archive()`, `_mark_reprint()`
- [app/studio/stages.py](../../app/studio/stages.py) — `mark_reprint()`
- [app/studio/printorders.py](../../app/studio/printorders.py) — `is_placed()`
- [app/tools/archive_dedupe.py](../../app/tools/archive_dedupe.py) — `main()`

## Related
- [Order Creator](order-creator.md) · [Orders](orders.md) · [Order stages](../rules/order-stages.md) · [Gelato](../integrations/gelato.md) · [Sync](../rules/sync-policy.md)
