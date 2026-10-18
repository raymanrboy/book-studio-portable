---
title: Order stages — new, in progress, shipped by the printer, sent
type: rule
updated: 2026-10-18
code:
  - app/studio/stages.py
  - app/studio/printorders.py
---
# Order stages

> The Etsy API doesn't return the seller's own tabs (the owner calls this "In Production"), so a stage
> is worked out from the facts: **"new" — the receipt has no confirmed, paid order in Printify or
> Gelato yet.** A draft, "on hold", unpaid, or cancelled order **doesn't count** (the owner's decision,
> 2026-09-18).
> Path: **New → In progress (a clock) → the truck → Sent (a box)**.

## The rule (`order_stage()`)

First, `print_order()` finds a "live" print order for the receipt: matched, **confirmed**
(`is_placed()`: Printify — not `on-hold`, not `pending`, not `payment-not-received`, not cancelled;
Gelato — `orderType: order`, not a draft, `financialStatus` isn't `draft` / `pending` / `canceled` /
`refused`), and not an old order from a returning buyer (matched **by name** and created more than an
hour before the receipt). Then:

| Condition (in order) | Stage | In the queue |
|---|---|---|
| The accounting state is "cancelled" or "full refund" | `closed` | not shown |
| A replacement reprint is placed and not shipped by its printer yet (`live_reprint()`, since 2026-10-18) | `work` (+ the reprint's printer) | In progress, with a «передрук» chip |
| Etsy: shipped (`is_shipped`) | `shipped` (+ the printer, if any) | Sent (a box) |
| No live print order | `new` (or `work`, if manually marked "no cost") | New |
| The printer shipped it: a tracking number **or** a status from `SENT_STATUSES` | `sent` (+ the printer) | the truck |
| Otherwise | `work` (+ the printer) | In progress (a clock) |

`SENT_STATUSES`: Printify — `fulfilled`, `partially-fulfilled`; Gelato — `shipped`, `in_transit`,
`delivered`, `returned` (`printorders.GELATO_SHIPPED`).

**The status chip** (the queue, the order card, the archive) shows the printer's word — except Printify's
`fulfilled`, which only means "shipped": it reads **In transit**, and **Delivered** once every parcel has
`delivered_at` from the carrier (`printorders.shown_status()`, the `shown` fact; since 2026-09-28, the owner:
"Fulfilled" beside Gelato's "Delivered" looked inconsistent). Stages still go by the real `status`.

## The truck (`sent`) — since 2026-09-17

Why it exists: to see which orders **can already be marked shipped on Etsy** (the owner's decision). The
owner marks them on Etsy by hand (on the Kyiv PC) → after the next refresh, Etsy returns `is_shipped` →
the order moves to the box. A `delivered` status at the printer does **not** move it off the truck tab —
only the mark on Etsy does.

## How an order becomes "in progress"

- Gelato: the draft's `orderReferenceId` contains the receipt number. Printify: the receipt number is in
  the book's title (`receipt number - name`) and in the order's `external_id`.
- A created draft (Gelato) or "On hold" order (Printify) **doesn't move** the receipt yet: it stays in
  "New" with a printer-status chip (`Draft`, `On hold`, `Created`…) — showing that the book has already
  been sent and needs confirming (`waiting_order()`). One cancelled at the printer has no chip.
- The owner confirms and pays in Printify ("Submit order") or Gelato → "Refresh"
  ([sync-policy.md](sync-policy.md)) → matching ([reconciliation.md](reconciliation.md)) finds the
  confirmed order — and the receipt moves to "In progress".

**An order of several books** (since 2026-10-14; open since 22.09): each send this program makes notes how many of the
receipt's books it holds (`records.remember_print_order(…, books=)`, one per Etsy item — the Order Creator's books). While the
placed print orders hold fewer books than the receipt has items (`books_in_print()`), the receipt is **`partial`**: its stage
stays what the ordered book makes it (the card keeps what went to print — a stage turned back to "new" hid it and invited a
second print of the same book, the code review of 14.10), and the queue lists it **under «Нові» too** (`inTab()`), the books
chip reading «1/2» in amber. Not for a partial refund (one book dropped). A send made before 14.10, or an order made at the
printer by hand, has no count and is taken to hold every book (as before). The receipt's other sends waiting at the printer
(`pending`: a second book's draft or refused payment) show their status chips in the row too.

A known gap: a book created in Printify **without** an order doesn't move the receipt (the queue's chip `On hold` /
`Draft` already says a book was sent and waits for confirmation).

## A reprint is "in progress" while it is made (since 2026-10-18)

A reprint — from the [order archive](../features/archive.md), or with new files from the Order Creator's «Передрук» tick
([order-creator](../features/order-creator.md)) — is recorded as a replacement (`mark_reprint()`), and replacement orders take
no part in automatic matching (`reserved_orders()`): the first print order stays the receipt's own. **While the reprint is
placed and its printer has not shipped it, the order is «Друкується» again** (`live_reprint()`), whatever Etsy says, with a
«передрук» chip in the row (no ship-by chip: Etsy's order shipped long ago); the queue's status and tracking are the reprint's.
Once its printer ships it, the order goes back to its own stage (usually "Sent" — Etsy's mark stays). Until 2026-10-18 the
stage did not change at all (decision of 2026-09-18) — the owner: a reprint sat among the shipped orders and could not be followed.
The exception stays: when the first order was cancelled at the printer, the reprint isn't marked as a replacement, gets matched
normally, and the receipt moves from "New" to "In progress".

`alreadyPrinted` (the stage is work / sent / shipped and not `partial`) tells the Order Creator to tick «Передрук» for a send
of this order; `reprint` — the print shown is a reprint being made.

## Status and tracking number for the queue

`picker_orders()` returns, for every order with a live print order (and for "New" ones — for a draft or
an unpaid order waiting for confirmation at the printer):
- `printStatus` — the status **exactly as Printify or Gelato writes it**, in English, untranslated (the
  owner's wish); there's no separate label for drafts (Gelato's `draft`, Printify's `on-hold` — shown
  as-is);
- `payment` — Gelato's `financialStatus`: `refused` (it could not take the money — the Payoneer limit of 13.10.2026)
  shows as a red «Payment refused» instead of the order's own word; a draft older than 12 hours is amber with its age;
- `shipBy` — Etsy's date to ship by (the earliest of the items' `expected_ship_date`, kept by `sync.normalize_receipt()`
  since 2026-10-14; an open receipt kept before without it makes the next sync read Etsy whole once): the row's clock chip,
  amber on its last day, red once past, until Etsy marks the order shipped;
- `booksInPrint` — see above;
- `tracking` — `[{carrier, number, url}]`; Printify's carrier comes as a code (`usps`) and gets turned
  into a name (`carrier_label()`: USPS, FedEx, Royal Mail…); in Gelato it's already the shipping
  method's name ("UPS Surepost"). Where this comes from —
  [Printify](../integrations/printify.md), [Gelato](../integrations/gelato.md).

## Where in the code

- [app/studio/stages.py](../../app/studio/stages.py) — `books_in_print()`; [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `statusChip()`, `shipByChip()`, `booksChip()`

- [app/studio/stages.py](../../app/studio/stages.py) — `order_stage()`, `print_order()`, `waiting_order()`, `_matched_order()`, `picker_orders()`, `HOUR_MS`, `mark_reprint()`, `live_reprint()`, `prints()`
- [app/studio/printorders.py](../../app/studio/printorders.py) — `is_placed()`, `PRINTIFY_NOT_PLACED`, `GELATO_NOT_PAID`, `all_facts()`, `carrier_label()`, `SENT_STATUSES`, `GELATO_SHIPPED`, `CARRIERS`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `reserved_orders()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `STAGES`, `STAGE_EMPTY`, `STAGE_LABEL`
- [app/studio/creator/printify_send.py](../../app/studio/creator/printify_send.py) — `printify_order_payload()`
- [app/studio/creator/gelato_send.py](../../app/studio/creator/gelato_send.py) — `create_gelato_draft()`
- Tests: [app/tests/test_states.py](../../app/tests/test_states.py) (`PickerStages` — drafts, "on hold", unpaid, `SentStage`, `ReprintWithNewFiles`)

## Related

- [Orders](../features/orders.md) · [Matching](reconciliation.md) · [Sync](sync-policy.md)
