---
title: Printify
type: integration
updated: 2026-09-29
code:
  - app/studio/printify.py
---
# Printify

> **From 1 October 2026 only read** (the owner, 29.09.2026: "from 1 October I move only to Gelato"): every new
> book goes to Gelato. Until then it printed **hardcovers for the US** (24 pages). Shop CozyCovenant, template
> "Hardcover 8x8 Template" (the Master). API `https://api.printify.com/v1`, token — a Personal Access Token.

## Read only from 1 October 2026

- `retired()` — from `READ_ONLY_FROM` (1 October 2026, this computer's calendar). Then `_check()` blocks **every**
  request that isn't a `GET` — image uploads, products, orders on hold — with "З 1 жовтня Printify лише для читання —
  нові книги друкує Gelato." (`RETIRED_TEXT`); the Order Creator's Printify routes refuse before a job starts.
- **Reading stays**: the sync still reads its orders, so the earlier ones keep their stage, tracking, archive days
  and cost. The token stays in Settings (the card says «лише читання старих замовлень», no Master picker).
- **Where it shows**: the printer rule gives every book to Gelato ([printer-rule](../rules/printer-rule.md)); the
  Order Creator has no Printify/Gelato switch; an archived Printify book has no «Передрук» — its 24 pages don't fit
  Gelato, so a reprint starts from the order's card with the book downloaded anew (28 or 30 pages).

## What's allowed (until 1 October 2026)

| Action | API path | When |
|---|---|---|
| Read shops, products, orders, uploads, the catalog | `GET shops.json`, `shops/{id}/products…`, `shops/{id}/orders.json`, `uploads/{id}.json`, `catalog/…` | always |
| Upload an image (base64) | `POST uploads/images.json` | creating a book |
| Create an unpublished product | `POST shops/{id}/products.json` | creating a book |
| Create an "On hold" order | `POST shops/{id}/orders.json` | only via `create_order_on_hold()`, after Manual approval is confirmed |

Everything else is blocked in `_check()` ([security](../security.md)).

## How an order created via the API works

- An order created through the API is kept **"On hold"** by Printify. Whether (and when) it goes into
  production and gets charged depends on the shop's *Order submission / Order approval* setting:
  **Manual** — only after "Submit order" in Printify; the automatic options go on their own after a set
  time. The owner's shop is set to **Manual** (a screenshot from 2026-09-15), and the program asks once
  to confirm this.
- Fields: `external_id` (`<receipt>-<8 characters>`), `label` (the book's title), `line_items`
  (`product_id` + the matte variant's `variant_id` + `quantity` 1) — **one line item per book of the
  receipt**: an order for two books goes as one order to one address (since 2026-09-20),
  `shipping_method: 1` (standard), `is_printify_express: false`, `send_shipping_notification: false`,
  `address_to` (`first_name`, `last_name`, `address1`, `address2`, `city`, `region`, `zip`, `country`,
  `phone`).
- A book's finish is **always matte**.
- The first real On-hold order hasn't been observed yet — see [open questions](../plans/open-questions.md).

## The Master

- Settings `printify.master`: `productId`, `blueprintId` 2737, `printProviderId` 28, variants (8x8
  Glossy/Matte enabled, 11x8.5 disabled), `placements` (x/y/scale/angle for `cover` and
  `page_1…page_24`).
- Artwork sizes: the cover 4672×2464, a page 4000×4000 (`coverSize`, `pageSize`).
- A new book = a copy of the Master's configuration with new images (`build_printify_payload()`).
- Before every creation — a snapshot of the Master; after — a check that it hasn't changed.

## Upload cache

`data/creator/upload-cache.json`: a file's SHA-256 → its image ID (the last 5000, `UPLOADS_KEPT`).
Before reusing one, it's checked to still exist in Printify (`upload_exists()`). An upload is only
retried when it certainly didn't arrive (the connection was refused, 429, 503); never after a timeout,
so duplicates never pile up in Printify's media library (since 2026-09-23). The upload's JSON is built straight in
bytes (`upload_image()`): a 30 MB page was held about five times over, three uploads at once (since 2026-09-26).

## Sync

`all_orders()` reads every order in the shop (50 at a time, up to 4 pages in parallel, no more than
`MAX_ORDER_PAGES` = 400 pages — a larger shop is marked incomplete, `httpc.Listing`); `slim_order()`
keeps only the fields needed for matching, the status, and (since 2026-09-17) `shipments` — tracking
numbers once shipped (`carrier` as a code, e.g. `usps`, `number`, `url`, and since 2026-09-28 `delivered_at` —
when the carrier delivered it; not stored without a number). The chip shows `fulfilled` as In transit /
Delivered by it ([rules/order-stages.md](../rules/order-stages.md)).
They're already in the order list, so no separate requests are needed. A `fulfilled`/`partially-fulfilled`
status or a tracking number moves the receipt to the truck tab
([rules/order-stages.md](../rules/order-stages.md)). An order with the receipt number in a product's
title, or in `shop_order_id`, gets matched to the Etsy receipt
([rules/reconciliation.md](../rules/reconciliation.md)).

## Errors

`_human()` → `httpc.human()`, shared with Gelato: 401/403 — the token (`code: printify_token`), 404,
429, 4xx, 5xx; `extra` carries `upstream` and `ambiguous` ("result unknown, don't retry").
`MANUAL_APPROVAL_NEEDED` — one shared text, "please confirm manual approval first", for the client and
for sends.

## Links

- A product: `https://printify.com/app/product-details/<id>?fromProductsPage=1`
- Orders: `https://printify.com/app/orders` (the address hasn't been checked against a real order).

## Where in the code

- [app/studio/printify.py](../../app/studio/printify.py) — `READ_ONLY_FROM`, `RETIRED_TEXT`, `retired()`, `_READ`, `_WRITE`, `_check()`, `_human()`, `call()`, `token()`, `MAX_ORDER_PAGES`, `MANUAL_APPROVAL_NEEDED`, `shops()`, `product()`, `upload_exists()`, `all_orders()`, `slim_order()`, `upload_image()`, `create_product()`, `create_order_on_hold()`, `manual_approval_confirmed()`, `analyze_master()`, `_manual_approval()`
- [app/studio/creator/printify_send.py](../../app/studio/creator/printify_send.py) — `create_printify_draft()`, `build_printify_payload()`, `printify_order_payload()`, `matte_variant()`, `_master_fingerprint()`, `_remember_upload()`, `UPLOADS_KEPT`, `_printify_setup()`
- [app/studio/core.py](../../app/studio/core.py) — `DEFAULT_SETTINGS`
- [app/studio/printorders.py](../../app/studio/printorders.py) — `carrier_label()`, `CARRIERS`
- Tests: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`FakePrintify`, `PrintifyDraftFlow`), [app/tests/test_states.py](../../app/tests/test_states.py) (`SentStage`)

## Related

- [Order Creator](../features/order-creator.md) · [Security](../security.md) · [Printer rule](../rules/printer-rule.md)
