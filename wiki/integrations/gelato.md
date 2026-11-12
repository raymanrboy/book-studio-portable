---
title: Gelato
type: integration
updated: 2026-11-12
code:
  - app/studio/gelato.py
  - app/studio/gelato_accounts.py
  - app/studio/tunnel.py
---
# Gelato

> Every new book goes to Gelato (28 or 30 pages). The program creates only **drafts**; the owner confirms and pays in Gelato. API `order.gelatoapis.com/v4` and `product.gelatoapis.com/v3`, key in the vault, header `X-API-KEY`. Printify is read-only ([Printify](printify.md)).

## Which format a book gets
`orders.plan_for()` reads the buyer's choice and gives each book a Gelato format; the card and queue show it (`planText()`).

| Etsy item says | Format | Page counts |
|---|---|---|
| Hardcover | `hardcover_8x8` | 28 / 30 |
| Hardcover whose chosen format says 11x11, 11" × 11", 28 × 28 cm | `hardcover_11x11` | 28 / 30 |
| Softcover with 5.5, 5x5, 14 × 14 in the item | `softcover_5x5` | 28 / 30 |
| Other softcover | `softcover_8x8` | 28 / 30 |
| Cover type unreadable | Gelato, `format: None`, picked in the Order Creator | 28 / 30 |

- Cover type: `binding_of()` → `reconcile.item_format()` reads variations, then SKU, then title; mixed or unknown gives `None`.
- The 11×11 test (`reconcile.is_large()`) looks only at format-like variation fields (`chosen_format_text()`), never the title or the buyer's own words.
- Etsy's "5x5" softcover is Gelato's 5.5×5.5 product (`softcover_5x5`); otherwise the name mismatch offered an 8×8.
- `settings.gelato.defaultFormat` is `hardcover_8x8`. The Order Creator lets the owner change a format.

## Formats (`settings.gelato.formats`)
| Key | Gelato product (metric) | Page with bleed | Cover, with wrap |
|---|---|---|---|
| `hardcover_8x8` | `photobooks-hardcover_pf_200x200-mm-8x8-inch_…` | 206×206 mm | 458×246 mm |
| `hardcover_11x11` | `photobooks-hardcover_pf_280x280-mm-11x11-inch_…` | 286×286 mm | 618×326 mm |
| `softcover_8x8` | `photobooks-softcover_pf_200x200-mm-8x8-inch_…` | 206×206 mm | about 408.8×206 mm |
| `softcover_5x5` (label «Softcover 5.5×5.5») | `photobooks-softcover_pf_140x140-mm-5_5x5_5-inch_…` | 146×146 mm | about 288.8×146 mm |

- All matte lamination, 170 gsm paper. The same Canva files serve all four; the 11×11 cover has the Canva cover's own proportions (4672×2464).
- Sizes are never stored: `photobook_geometry()` reads them from the catalog each time.

## How many pages
- A book is as long as the Canva export: `settings.gelato.pageCounts` = `[28, 30]`; the files decide ([Book files](../rules/book-files.md)). `pageCount` in an order counts inner pages only.
- What Gelato prints is decided by its catalog: `page_counts()` reads `validPageCounts` (28–200), cached for `CATALOG_HOURS`. It is checked on the order card, in the Order Creator (format tooltip, yellow mark, blocked "Create") and right before the draft is made (`gelato_pages_problem()`). No key or internet silences the first two; the last still fires.

## The book file
One PDF of type `default`: cover (back, spine, front) · blank endpaper · pages 1…N · blank endpaper (`build_photobook_pdf()`).
- A Gelato draft shows Cover, Page 0 (the blank endpaper), Page 1…N. Page 0 is the price of an automatic send; the book prints correctly.
- The blank pages are required: without them the book shifts by one page.
- Blanks are white pictures at `BLANK_DPI` = 300; tiny ones made Gelato rate the whole book as low quality.
- A Canva cover fits as is (Gelato trims 3–5 mm); the PDF warns only above `COVER_TRIM_WARN_MM` (10 mm). Pictures are not recompressed.
- A `default` cover with `inside` pages does not work: Gelato puts the cover on every page.

## Temporary link
Gelato fetches the PDF by URL shortly after the draft exists, so the `readback` journal step may still say `fileFetched: false`. `FileTunnel` (`tunnel.py`):
1. serves exactly the book files from a local server, no listing;
2. starts `app/bin/cloudflared.exe` (a Cloudflare quick tunnel, no account) and waits for an `https://*.trycloudflare.com` address (`_URL_RE` skips `api.`); from the third check it also asks Cloudflare's public DNS (`_head_ok_public_dns()`), since the home router lags;
3. `TunnelRegistry.keep()` holds the link `tunnelKeepAliveSeconds` (900) and then wipes `data/tmp/gelato/<session>`.
- `cloudflared.exe` is put into `app/bin` by hand; without it the Order Creator warns.
- If Cloudflare refuses a tunnel there is no address and no draft is created ("wait a minute or two and send again").
- The program does not exit while a link is active.

## The draft
- `orderType: draft` is forced (`create_draft_order()`); `orderReferenceId` = `receipt - name` (the sync finds the receipt by that number); several books of one receipt are one draft with several `items`, each with its own PDF, `productUid` and `pageCount`.
- Etsy gives no phone and Gelato will not confirm without one, so an empty phone becomes `GELATO_PLACEHOLDER_PHONE`. No email is needed.
- Drafts are not a cost in Profit. Every attempt is a record in the send journal ([Order Creator](../features/order-creator.md)).
- A send whose result is unknown is not a failure and is never retried: the owner checks Gelato → Drafts first.

## Sync
- `all_orders()` runs `orders:search` (orders and drafts, 100 per call, cap 5000; a capped list is incomplete, so the sync warns and the archive does not trust it). The search is a POST that only reads, so it is retried after a drop.
- Costs are converted with `eurUsdRate` etc. ([Reconciliation](../rules/reconciliation.md)).
- Tracking is not in the search: for statuses in `GELATO_SHIPPED`, `attach_shipments()` reads the full order (read-only GET) one at a time, at most `TRACKING_READS` (60) per sync; an order is re-read only while it has no number and its status changed.
- The order card's history is read when the card opens (`cached_history()`, kept `HISTORY_FRESH` seconds; finished states `HISTORY_DONE` until the program closes). Gelato webhooks are not used (no public address).
- The account list can hold other people's orders; only those matched to an Etsy receipt count.

## Second account (read-only)
A second key can be saved (vault `gelato_old_api_key`) next to the main one; Settings shows it as «Старий акаунт · лише читання».
- `gelato_accounts.py`: `_switch()` (Settings → «Перейти на новий акаунт Gelato»; checks the new key with `check_key()` first), `_forget()`, `status()`, `open_orders()` (how many Etsy orders still follow an old-account order).
- Every order carries its account (`account_id()`); each sync reads every account that has a key (`_gelato_part()`). An order is dropped only when its own account's list, loaded whole, lacks it, so the queue, archive and Profit never lose one. `loaded.gelato` is written only when all accounts loaded whole.
- The second key only reads: `_allowed()` lets it do order search and `GET`; drafts go through the main key.

## Errors
`_human()` (shared `httpc.human()`): 401/403 key, 404, 429, other 4xx "Gelato rejected the data", 5xx or a drop marked `ambiguous` (unknown result).

## Why
- Metric products only: the "inch" products (`pf_8x8-inch-200x200-mm`, 203.2 mm) are different products with different sizes.
- Gelato's public docs say "from 30 pages"; that is stale, the catalog is trusted.
- `hardcover_11x11` only on the buyer's chosen format: a wrong size costs more, and «11.11» dedications must not trigger it.

## Where in the code
- [app/studio/gelato.py](../../app/studio/gelato.py) — `_allowed()`, `all_orders()`, `page_counts()`, `photobook_geometry()`, `attach_shipments()`
- [app/studio/gelato_accounts.py](../../app/studio/gelato_accounts.py) — `_switch()`, `_forget()`, `status()`, `open_orders()`
- [app/studio/tunnel.py](../../app/studio/tunnel.py) — `FileTunnel`, `TunnelRegistry`, `_URL_RE`, `_head_ok_public_dns()`
- [app/studio/orders.py](../../app/studio/orders.py) — `plan_for()`, `printing()`, `binding_of()`, `page_options()`
- [app/studio/reconcile.py](../../app/studio/reconcile.py) — `item_format()`, `is_large()`, `chosen_format_text()`
- [app/studio/creator/gelato_send.py](../../app/studio/creator/gelato_send.py) — `create_gelato_draft()`, `gelato_pages_problem()`, `GELATO_PLACEHOLDER_PHONE`
- [app/studio/creator/photobook.py](../../app/studio/creator/photobook.py) — `build_photobook_pdf()`, `BLANK_DPI`, `COVER_TRIM_WARN_MM`

## Related
- [Order Creator](../features/order-creator.md) · [Order to print](../flows/order-to-print.md) · [Book files](../rules/book-files.md) · [Printify](printify.md) · [Security](../security.md)
