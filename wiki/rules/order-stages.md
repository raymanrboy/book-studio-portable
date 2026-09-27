---
title: Order stages — new, in progress, shipped by the printer, sent
type: rule
updated: 2026-09-27
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
| Etsy: shipped (`is_shipped`) | `shipped` (+ the printer, if any) | Sent (a box) |
| No live print order | `new` (or `work`, if manually marked "no cost") | New |
| The printer shipped it: a tracking number **or** a status from `SENT_STATUSES` | `sent` (+ the printer) | the truck |
| Otherwise | `work` (+ the printer) | In progress (a clock) |

`SENT_STATUSES`: Printify — `fulfilled`, `partially-fulfilled`; Gelato — `shipped`, `in_transit`,
`delivered`, `returned` (`printorders.GELATO_SHIPPED`).

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

A known gap: a book created in Printify **without** an order doesn't move the receipt. The idea of a
"product already created" mark is in the [plans](../plans/roadmap.md).

## A reprint doesn't change the stage (since 2026-09-18)

A reprint from the [order archive](../features/archive.md) is recorded as a replacement
(`mark_reprint()`), and replacement orders take no part in automatic matching (`reserved_orders()`). So
the receipt stays at its own stage (usually "Sent" — the book was already with the buyer), and the second
print order doesn't take the first one's place. The exception is when the first order was cancelled at
the printer: then the reprint isn't marked as a replacement, gets matched normally, and the receipt moves
from "New" to "In progress".

## Status and tracking number for the queue

`picker_orders()` returns, for every order with a live print order (and for "New" ones — for a draft or
an unpaid order waiting for confirmation at the printer):
- `printStatus` — the status **exactly as Printify or Gelato writes it**, in English, untranslated (the
  owner's wish); there's no separate label for drafts (Gelato's `draft`, Printify's `on-hold` — shown
  as-is);
- `tracking` — `[{carrier, number, url}]`; Printify's carrier comes as a code (`usps`) and gets turned
  into a name (`carrier_label()`: USPS, FedEx, Royal Mail…); in Gelato it's already the shipping
  method's name ("UPS Surepost"). Where this comes from —
  [Printify](../integrations/printify.md), [Gelato](../integrations/gelato.md).

## Where in the code

- [app/studio/stages.py](../../app/studio/stages.py) — `order_stage()`, `print_order()`, `waiting_order()`, `_matched_order()`, `picker_orders()`, `HOUR_MS`, `mark_reprint()`
- [app/studio/printorders.py](../../app/studio/printorders.py) — `is_placed()`, `PRINTIFY_NOT_PLACED`, `GELATO_NOT_PAID`, `all_facts()`, `carrier_label()`, `SENT_STATUSES`, `GELATO_SHIPPED`, `CARRIERS`
- [app/studio/outcomes.py](../../app/studio/outcomes.py) — `reserved_orders()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `STAGES`, `STAGE_EMPTY`, `STAGE_LABEL`
- [app/studio/creator.py](../../app/studio/creator.py) — `printify_order_payload()`, `create_gelato_draft()`
- Tests: [app/tests/test_states.py](../../app/tests/test_states.py) (`PickerStages` — drafts, "on hold", unpaid, `SentStage`)

## Related

- [Orders](../features/orders.md) · [Matching](reconciliation.md) · [Sync](sync-policy.md)
