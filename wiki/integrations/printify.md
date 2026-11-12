---
title: Printify (read-only)
type: integration
updated: 2026-11-12
code:
  - app/studio/printify.py
---
# Printify

> Every new book goes to Gelato. Printify is read-only from 2026-10-01 on the owner's copy (`printify.readOnlyFrom`); its earlier orders are still read for stage, tracking, cost and archive days. A copy with the date unset (the colleague's) can still send to Printify.

## Still read
- `all_orders()` reads the whole shop (`MAX_ORDER_PAGES`); `slim_order()` keeps status and tracking. Stage, matching and cost: [Order stages](../rules/order-stages.md), [Reconciliation](../rules/reconciliation.md).
- A missing token is normal: no warning. An archived Printify book has no «Передрук» (24 pages do not fit Gelato).

## The gate
- `read_only_from()` = `READ_ONLY_FROM` (2026-10-01) unless the setting says otherwise (ISO date; null = never); `retired()` follows it.
- Retired: `_check()` refuses every non-GET with `RETIRED_TEXT` (403), the Order Creator's Printify routes refuse, `orders.printing()` sets `gelatoOnly` ([Gelato](gelato.md)).
- Settings transfer drops `readOnlyFrom`, so a colleague's file cannot switch the owner's gate off.

## Date unset
- `retired()` is false: a US 8×8 hardcover goes to Printify with 24 pages (`plan_for()`), and the Order Creator makes an "On hold" order (`create_printify_draft()`). Not exercised on the owner's copy.

## Where in the code
- [app/studio/printify.py](../../app/studio/printify.py) — `READ_ONLY_FROM`, `RETIRED_TEXT`, `read_only_from()`, `retired()`, `_check()`
- [app/studio/creator/printify_send.py](../../app/studio/creator/printify_send.py) — `create_printify_draft()`

## Related
- [Gelato](gelato.md) · [Security](../security.md)
