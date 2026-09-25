---
title: Gelato and the temporary link
type: integration
updated: 2026-09-25
code:
  - app/studio/gelato.py
  - app/studio/tunnel.py
---
# Gelato

> Prints **everything except US hardcovers**: hardcovers to other countries, and softcovers anywhere
> (28 or 30 pages). The program only creates **drafts** of orders. API: `order.gelatoapis.com/v4`,
> `product.gelatoapis.com/v3`, the key in the `X-API-KEY` header. The rules below were checked on
> 2026-09-17 against two of the owner's real orders (a manual 28-page one, and a 30-page one created
> through the API and already printed) and two test drafts with numbered pages.

## Formats (`settings.gelato.formats`)

| Key | Name | Gelato product | Page, with bleed | Cover (28 / 30 pages) |
|---|---|---|---|---|
| `hardcover_8x8` | Hardcover 8×8 | `photobooks-hardcover_pf_200x200-mm-8x8-inch_…` (20×20 cm) | 206×206 mm | 458×246 mm (with the wrap) |
| `softcover_8x8` | Softcover 8×8 | `photobooks-softcover_pf_200x200-mm-8x8-inch_…` (20×20 cm) | 206×206 mm | 408.72 / 408.88 × 206 mm |
| `softcover_5x5` | Softcover 5.5×5.5 | `photobooks-softcover_pf_140x140-mm-5_5x5_5-inch_…` (14×14 cm) | 146×146 mm | 288.72 / 288.88 × 146 mm |

- All of them — matte lamination, 170 gsm paper; when each format applies — the
  [printer rule](../rules/printer-rule.md).
- **The metric products** are the same ones the owner picks in Gelato by hand. Before 2026-09-17 the
  program used the "inch" ones (`pf_8x8-inch-200x200-mm`, `pf_5_5x5_5-inch-140x140-mm`: 203.2 and
  139.7 mm) — those are **different products**, with different sizes. Saved old names get swapped on
  launch (`core._upgrade()`).
- The program never stores sizes; it fetches them from the catalog every time
  (`photobook_geometry()`).

## How many pages

- A book is as long as the Canva export: **30 pages** or **28** (the owner dropped one spread). There's
  no switch — the number comes from the files (`settings.gelato.pageCounts` = `[28, 30]`).
- `pageCount` in an order counts **only the inner pages** (28 / 30), the same as in the owner's manual
  orders. The cover catalog counts them together with the cover's own sides (`pagesCount` 32 / 34).
- What Gelato actually prints is decided by **its catalog**: a product's `validPageCounts` (read-only,
  cached for `CATALOG_HOURS` = 6 hours, or until the Gelato key changes, `_fresh_catalog()` — it used to
  be cached until the next restart). On 2026-09-17 all three formats — **28–200**. Gelato's public docs
  say "from 30" — that's stale; the program trusts the catalog regardless.
- The program asks the catalog in three places: the order card (right after laying out files), the
  Order Creator (format buttons: a "28–200 pages" tooltip, a yellow mark and a sentence if the format
  doesn't fit; the "Create" button is blocked), and right before creating the draft (nothing gets
  created if it fails). No key or no internet → the first two checks stay silent, the last one still
  fires.

## The book file

**One PDF**, type `default`: **cover** (back + spine + front) · **blank endpaper** · **pages 1…N** ·
**blank endpaper** (31 PDF pages for 28, 33 for 30). The blank pages are **required**.

- How it looks in a Gelato draft: Cover, **Page 0** — blank (this is the endpaper, and that's correct),
  Page 1…Page N — the book; the back endpaper doesn't show in the list. Page 0 stays even after the
  order is confirmed (checked 2026-09-18); without it, Gelato only shows books made in its own editor
  (below).
- Evidence (2026-09-17): the print PDFs of both of the owner's real orders have exactly this structure.
  A test draft **without** the blank pages came out shifted: page "1" became Page 0, and Page 28 stayed
  blank. A test draft **with** the blank pages (hardcover 20×20, 28 pages) had no shift: Page 0 blank,
  Page 1…28 = "1"…"28" (confirmed by the owner). **Don't remove the blank pages** — it will break both
  28- and 30-page books.
- **Why the "correct" order 5d72fd05 (2026-09-15) shows without Page 0** (worked out on 2026-09-18 by
  reading orders from the API and the old Order Creator's journal): it was created by the old Order
  Creator (a `default` cover + `inside` pages), but the book then went through **Gelato's own editor**.
  6 minutes after the draft, the item was recreated (`order-item-<time>`), a `designId` appeared, and
  Gelato built a new PDF itself (22 MB, 300 dpi). For books made in Gelato's editor, only Page 1…N show.
  The PDF that actually went to print has the same structure as ours: cover · blank · pages · blank
  (checked 2026-09-17). So Page 0 is the inside of the cover, white in both books. Page 1 (the
  dedication) is on Page 1 in both.
- **The blank pages are white pictures at 300 dpi** (`BLANK_DPI`; 1725 px for 14 cm, 2434 px for 20 cm —
  matching Gelato's own PDFs). Before 2026-09-18 they were 16×16 px, and Gelato rated the whole book's
  quality at **3 dpi** (the order item's `dpi` field), even though the pages themselves are ~700 dpi.
- The PDF's page sizes come from the catalog: the page with bleed (206 mm for 20×20), the cover across
  the whole sheet. Pictures aren't recompressed, and are fitted with an even trim of the edges.
- **A Canva cover** (4672×2464, the same as for Printify) fits: Gelato takes it as-is, trimming ~3–5 mm
  off the edges. A warning only appears if the trim is more than 10 mm (`COVER_TRIM_WARN_MM`, meaning
  it's clearly not the cover); how much got trimmed shows in the [send journal](../features/send-journal.md).
- A `default` cover + `inside` pages (what the old Order Creator used to do) **doesn't work**: Gelato
  puts the cover on every page. That's what happened in Book Studio before 2026-09-15, and again in a
  test draft from the old Order Creator on 2026-09-18 (a real book, 30 pages; the owner deleted it). So
  the successful order 5d72fd05 was fixed in Gelato's editor (above). **Page 0 is the price of an
  automatic send; the book prints correctly.**

## Temporary link

Gelato only fetches a file **by URL**, and (confirmed 2026-09-17) does so itself, **within roughly a
minute of the draft being created**, without waiting for anyone to open it. So the `readback` step in
the journal, taken right after creation, may still show `fileFetched: false`.
`FileTunnel`:
1. starts a local server that serves exactly `book.pdf` (no file listing);
2. runs `app/bin/cloudflared.exe tunnel --url …` (a Cloudflare quick tunnel, no account needed) and
   waits for a `https://*.trycloudflare.com` address, then checks that the file is really served
   (`reachable`). The home router often doesn't know the new address yet, so from the third try the
   address is also asked of Cloudflare's public DNS (`1.1.1.1`, `_head_ok_public_dns()`) — otherwise the
   warning would be false. **When Cloudflare refuses a quick tunnel** (it happens — 2026-09-25, a real
   order), cloudflared prints an error that names `https://api.trycloudflare.com`; that line was
   taken for the address, and Gelato got a draft whose file never loads ("loading forever"). Now
   `_URL_RE` skips `api.`, cloudflared's last lines go to `app.log`, and the send stops with "Cloudflare
   gave no address — no draft was created, wait a minute or two and send again";
3. `TunnelRegistry.keep()` keeps the link up for 15 min (`tunnelKeepAliveSeconds`), then closes it and
   wipes `data/tmp/gelato/<session>`. A "Files fetched" button closes it earlier.
The program won't exit while the link is active. No `cloudflared.exe` → the Order Creator warns.

## The draft

`orderType: draft` (forced), `orderReferenceId` = **the book's title** `receipt number - name` (since
2026-09-18, the way the owner names his own manual orders too; Gelato doesn't require uniqueness) — the
sync finds the receipt by the number in it, and once confirmed and paid the order moves to "In
progress". **Phone:** Etsy doesn't provide one, and without it Gelato won't let a draft be confirmed —
an empty one gets the made-up `+1 555 555 0100` (`GELATO_PLACEHOLDER_PHONE`; the owner's usual practice).
Email isn't needed (his manual orders don't have one either). Drafts don't count as a cost in the
accounting. Every attempt (successful or not) is its own record in the
[send journal](../features/send-journal.md).
**Several books of one receipt** (since 2026-09-20) — one draft with several `items`: each with its own
`productUid`, its own `pageCount`, and its own PDF (`book-1.pdf`, `book-2.pdf`… on one temporary link),
`orderReferenceId` — `receipt number - Emma, Liam`.

## Sync

`all_orders()` — searching orders (`orders:search`, explicitly with `orderTypes: order, draft`; Gelato
returns drafts even without this) 100 at a time, up to 5000; `slim_order()`. A list that stopped at 5000
is marked incomplete (`httpc.Listing.complete`): the sync warns, and the archive doesn't treat such a
list as fresh. The search is a POST that only reads, so it can be retried after a drop
(`idempotent=True`). The cost in EUR is converted using the `eurUsdRate` (1.085).

**Tracking numbers** (since 2026-09-17, for the truck tab — see [stages](../rules/order-stages.md)): the
search doesn't return them. For orders with a status from `SHIPPED` (`shipped`, `in_transit`,
`delivered`, `returned`), `attach_shipments()` reads the full order (`GET /v4/orders/{id}`, read-only)
and takes `shipment.shipmentMethodName` + `shipment.packages[].trackingCode/trackingUrl`, or, if there
are no packages, `items[].fulfillments[]` (`shipments_of()`). In the snapshot this is the `shipments`
field (`carrier`, `number`, `url`) and `shipmentsFor` — the status it was read at. Each order is read
once; read again only while it has no tracking number and its status has changed; up to 60 per refresh
(`TRACKING_READS`), 4 in parallel.
Documentation: [Get order](https://dashboard.gelato.com/docs/orders/v4/get/),
[statuses](https://dashboard.gelato.com/docs/orders/order_details/).

## Errors

Gelato's responses are read by a function shared with Printify, `httpc.human()` (`_human()`): 401/403 —
the key, 404, 429, 4xx — "Gelato rejected the data", 5xx and a drop — with `ambiguous`. For creating a
draft, this tells apart a refusal from an **unknown result**
([order-creator.md](../features/order-creator.md), step 7).

## Where in the code

- [app/studio/gelato.py](../../app/studio/gelato.py) — `ORDER_API`, `PRODUCT_API`, `_FORBIDDEN`, `_allowed()`, `_human()`, `call()`, `search_orders()`, `all_orders()`, `slim_order()`, `product()`, `page_counts()`, `_fresh_catalog()`, `CATALOG_HOURS`, `photobook_geometry()`, `create_draft_order()`, `get_order()`, `SHIPPED`, `TRACKING_READS`, `shipments_of()`, `attach_shipments()`
- [app/studio/tunnel.py](../../app/studio/tunnel.py) — `CLOUDFLARED`, `_URL_RE`, `FileTunnel`, `_head_ok()`, `_head_ok_public_dns()`, `TunnelRegistry`, `cleanup_stale()`, `_ends_with_us()`
- [app/studio/creator.py](../../app/studio/creator.py) — `gelato_page_options()`, `_gelato_page_count()`, `gelato_page_counts()`, `gelato_pages_problem()`, `_pages_problem()`, `create_gelato_draft()`, `_gelato_draft()`, `_unknown_outcome()`, `_journal_readback()`, `build_photobook_pdf()`, `COVER_TRIM_WARN_MM`, `BLANK_DPI`, `GELATO_PLACEHOLDER_PHONE`, `_one_idat()`
- [app/studio/core.py](../../app/studio/core.py) — `DEFAULT_SETTINGS`, `_OLD_GELATO_SIZES`, `_upgrade()`
- [app/studio/orders.py](../../app/studio/orders.py) — `page_options()`, `_files()`
- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — `renderTunnels()`, `startCountdown()`, `loadPageCounts()`, `formatProblem()`, `formatCard()`
- Tests: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`GelatoDraftFlow`), [app/tests/test_library_creator.py](../../app/tests/test_library_creator.py) (`SafetyRails`, `GelatoValidation`), [app/tests/test_orders.py](../../app/tests/test_orders.py) (`GelatoLength`), [app/tests/test_states.py](../../app/tests/test_states.py) (`GelatoTracking`)

## Related

- [Order Creator](../features/order-creator.md) · [Send journal](../features/send-journal.md) · [Security](../security.md) · [Printer rule](../rules/printer-rule.md)
