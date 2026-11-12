---
title: Order stages
type: rule
updated: 2026-11-12
code:
  - app/studio/stages.py
  - app/studio/printorders.py
---
# Order stages

> The Etsy API does not return the seller's own tabs, so an order's stage is computed from facts: **"new" means the receipt has no confirmed, paid print order.** A draft, on-hold, unpaid or cancelled order does not count. Path: New → In progress (clock) → the truck → Sent (box).

## The rule (`order_stage()`)
`print_order()` first finds the receipt's live print order: matched ([Reconciliation](reconciliation.md)), placed (`is_placed()`), and not an earlier order of a returning buyer (matched by name and created more than an hour before the receipt, `_matched_order()`). Then, in this order:

| Condition | Stage | Queue |
|---|---|---|
| Accounting state cancelled or full refund | `closed` | not shown |
| A replacement reprint is placed and not shipped by its printer (`live_reprint()`) | `work` + the reprint's printer | In progress, «передрук» chip |
| Etsy says shipped | `shipped` | Sent (box) |
| No live print order | `new` (`work` if manually marked "no cost") | New |
| Printer shipped it: tracking number or a status in `SENT_STATUSES` | `sent` | the truck |
| Otherwise | `work` | In progress (clock) |

- **Placed** (`is_placed()`): Printify status not in `PRINTIFY_NOT_PLACED` (on-hold, pending, payment-not-received, cancelled); Gelato `orderType: order`, not a draft, `financialStatus` not in `GELATO_NOT_PAID` (draft, pending, refused, cancelled).
- `SENT_STATUSES`: Printify `fulfilled`, `partially-fulfilled`; Gelato `GELATO_SHIPPED` (shipped, in_transit, delivered, returned).
- **Status chip** (queue, card, archive) shows the printer's word as is, in English, except Printify `fulfilled`: it reads In transit, and Delivered once every parcel has `delivered_at` (`shown_status()`). Stages use the real status.
- **The truck** lists orders that can already be marked shipped on Etsy. The owner marks them on Etsy by hand (Kyiv PC); after the next refresh Etsy returns `is_shipped` and the order moves to the box. A `delivered` status at the printer does not move it off the truck.

## Becoming "in progress"
- A created draft does not move the receipt: it stays New with a printer-status chip (Draft, On hold, Created…) — the book is sent and needs confirming (`waiting_order()`); one cancelled at the printer has no chip.
- The owner confirms and pays in Gelato, then Refresh ([Sync](sync-policy.md)); matching finds the confirmed order and the receipt moves.

**Several books in one receipt.** Each send records how many books it holds (`records.remember_print_order(…, books=)`). While placed orders hold fewer books than the receipt has items (`books_in_print()`) the receipt is `partial`: its stage stays what the ordered book makes it, and the queue lists it under New too (`inTab()`) with an amber «1/2» chip. Not for a partial refund. A send with no count, or an order made at the printer by hand, counts as every book. Other sends of the receipt still waiting at the printer show their status chips in the row.

## Reprints
A reprint (from the [archive](../features/archive.md), or with new files via the Order Creator's «Передрук» tick) is recorded as a replacement (`mark_reprint()`) and replacement orders are excluded from automatic matching (`reserved_orders()`): the first print order stays the receipt's own. While the reprint is placed and unshipped the order shows «Друкується» with a «передрук» chip (no ship-by chip), and the queue's status and tracking are the reprint's. When its printer ships it, the order returns to its own stage. If the first order was cancelled at the printer, the reprint is not marked as a replacement and matches normally.
`alreadyPrinted` (stage work/sent/shipped and not `partial`) makes the Order Creator tick «Передрук»; `reprint` says the shown print is a reprint.

## What the queue gets (`picker_orders()`)
For every order with a live print order, and for New ones waiting at a printer:
- `printStatus` — the printer's word untranslated; Gelato's `financialStatus` `refused` shows a red «Payment refused»; a draft older than 12 hours is amber with its age.
- `shipBy` — the earliest item `expected_ship_date`: a clock chip, amber on the last day, red once past, until Etsy marks shipped.
- `booksInPrint`, `partial`, `alreadyPrinted`, and `tracking` = `[{carrier, number, url}]` (Printify carrier codes become names, `carrier_label()`; Gelato gives the method name).

## Why
- Only a placed and paid order counts, because cancelled orders once looked printed.
- A multi-book receipt keeps its stage instead of turning back to New: turning it back hid the print and invited a duplicate.

## Where in the code
- [app/studio/stages.py](../../app/studio/stages.py) — `order_stage()`, `print_order()`, `waiting_order()`, `books_in_print()`, `live_reprint()`, `picker_orders()`, `mark_reprint()`
- [app/studio/printorders.py](../../app/studio/printorders.py) — `is_placed()`, `shown_status()`, `SENT_STATUSES`, `GELATO_SHIPPED`, `carrier_label()`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `reserved_orders()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `STAGES`, `inTab()`, `statusChip()`, `shipByChip()`, `booksChip()`
- Tests: [app/tests/test_states.py](../../app/tests/test_states.py) — `PickerStages`, `SentStage`, `ReprintWithNewFiles`

## Related
- [Orders](../features/orders.md) · [Reconciliation](reconciliation.md) · [Sync](sync-policy.md) · [Gelato](../integrations/gelato.md)
