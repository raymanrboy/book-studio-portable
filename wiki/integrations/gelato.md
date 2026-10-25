---
title: Gelato and the temporary link
type: integration
updated: 2026-10-14
code:
  - app/studio/gelato.py
  - app/studio/gelato_accounts.py
  - app/studio/tunnel.py
---
# Gelato

> Since 1 October 2026 prints **every book** (28 or 30 pages), US hardcovers too — Printify only reads
> ([printer rule](../rules/printer-rule.md)); before that, everything except US hardcovers. The program only
> creates **drafts** of orders. API: `order.gelatoapis.com/v4`,
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
  139.7 mm) — those are **different products**, with different sizes. The saved old names were swapped on
  launch until 2026-09-27; the owner's settings had none left, so the swap is gone.
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
**History** (since 2026-10-04, for the order card — [orders](../features/orders.md)): the same full order
(`GET /v4/orders/{id}`, read-only) read **when the card is opened**, one order, never in bulk: `cached_history()` →
`history()` — the items' `eventLog`, the order's own dates, `shipment.minDeliveryDate` / `maxDeliveryDate`, the tracking.
`slot_of()` picks the key (the old account's orders are read with the old key). Gelato's docs weren't readable from here
(403); the `eventLog` was `[]` in every draft ever read, so its entries' field names are guessed and their shape is logged
(names only) to `gelato.log`. Gelato also offers webhooks (`order_status_updated`), but they need a public address, which a
local program doesn't have.
Documentation: [Get order](https://dashboard.gelato.com/docs/orders/v4/get/),
[statuses](https://dashboard.gelato.com/docs/orders/order_details/).

## His own account — two keys during the move

The owner moved to his own Gelato account (switched on 2026-09-30; the old one holds other people's orders too; agreed
2026-09-27, "the smooth switch").

- **Settings → Gelato → «Перейти на новий акаунт Gelato»** (the swap icon in place of «Замінити ключ»): the owner
  pastes the new key; the program reads **one** order with it (`check_key()` — a mistyped key is told before anything
  changes), then keeps the current key as `gelato_old_api_key` («Старий акаунт · лише читання») and the new one as
  `gelato_api_key`, inside the vault — no key goes through the chat or the screen. A sync starts at once. Refused on
  the preview server, during a sync, with the same key, and while an old key is still kept (one move at a time).
- **Each order knows its account**: `slim_order(g, account)` puts `account` — `account_id()`, the first 12 hex of the
  key's SHA-256 (which account, never the key) — on every order. Orders kept from before carry none: they are the
  account read before the first switch (`settings.gelato.firstAccount`, `untagged_account()`).
- **Every sync reads each account the program has a key for** (`accounts()`, `sync._gelato_part()`); a shipped
  order's tracking is read with its own account's key (`attach_shipments(…, account)`).
- **The safety net, always on**: an order is dropped only when its **own** account's list, loaded whole, lacks it (a
  deleted draft). An account not read whole — it failed, its list was cut at 5000, its key was removed — keeps its
  orders as last seen (status, tracking, cost). So the queue, the [archive](../features/archive.md) and Profit never
  lose an order to the switch. `loaded.gelato` (what the archive trusts) is written only when every account was
  loaded whole.
- **The old key only reads**: `_allowed(…, account="old")` lets through the order search and `GET` only —
  `POST /v4/orders` needs the main key. Drafts and reprints go to the new account only (reprints of an old-account
  book too).
- **When the old key can go**: Settings shows «Ще N замовлень в роботі» while any of the owner's Etsy orders follows
  an old-account order that is a draft, in print, or shipped by Gelato but not marked on Etsy
  (`gelato_accounts.open_orders()`, stages `new`/`work`/`sent`); then «Його замовлення завершено». The owner removes
  it with the bin (a warning if some are still open); its orders stay as they were.
- The legacy import (keys from the old Order Creator) doesn't offer the Gelato key while one is saved — it is the
  old account's key.

## Errors

Gelato's responses are read by a function shared with Printify, `httpc.human()` (`_human()`): 401/403 —
the key, 404, 429, 4xx — "Gelato rejected the data", 5xx and a drop — with `ambiguous`. For creating a
draft, this tells apart a refusal from an **unknown result**
([order-creator.md](../features/order-creator.md), step 7).

## Paying Gelato (outside the program)

The program only creates drafts; the owner pays the orders in Gelato himself. **The main way: the direct Payoneer integration**
(Gelato → Billing → Payment → Methods → Payoneer — Gelato takes the money from the Payoneer USD balance, no fee). **A Payoneer
card** is linked as the spare: it works, but Payoneer may take up to 1.8% a purchase (Gelato is not in the card's country) and the
card costs 29.95 USD a year (Payoneer's price page, 13.10.2026).

What a hardcover costs now (order #4202433342, 13.10.2026): print $13.17 − Gelato+ discount $3.29 + USPS Ground Advantage $6.99 +
**9% US sales tax $1.52** (Louisiana) = $18.39. The buyer already paid sales tax on Etsy, so the owner asked Gelato about a resale
certificate (2026-10-14). Gelato: no registered business is needed, a personal Ukrainian taxpayer number will do, as long as the
name, address and email match the Gelato account (Billing → Tax center → Resale certificate → Avalara's form, state by state).
**Submitted on 2026-10-14, all «under review»:** the Streamlined Sales Tax states among his buyers (North Carolina, Iowa, Ohio,
Wisconsin, Michigan, Tennessee, Minnesota, New Jersey, Nevada, Washington, Kansas, Oklahoma, North and South Dakota) with the
Ukrainian number, and Pennsylvania with a written reason (no PA licence: a non-US seller selling only through Etsy, a marketplace
facilitator). **Skipped** — they want a registration in the state, which he has not: California (a seller's permit), New York,
Florida (its own Annual Resale Certificate), Illinois (the out-of-state option says «delivered outside Illinois» — untrue),
Missouri (did not let through), Texas (its permit, another US state's or a Mexican RFC). About a quarter of his US orders; once
approved, their tax line should be gone — the Profit page sees it by itself (it takes Gelato's own totals).

**Done again on 2026-10-24 — the 14.10 ones were not there.** Gelato's Resale Certificates list and Avalara CertExpress
(roman.boichenko.work@gmail.com, opened from Gelato → Tax center → Resale certificate → «Get resale certificate») both showed
none. So the certificates were made again, all for Gelato ASA, **16, all «PENDING»**: the SST states North Carolina (21783), South
Dakota (21784), Ohio (21785), Iowa (21786), Minnesota (21787), Michigan (21788), Wisconsin (21789), Tennessee (21790), New Jersey
(21791), Nevada (21792), Washington (21793), Kansas (21794), Georgia (21795), Oklahoma (21796), North Dakota (21797), and Pennsylvania
(21798, REV-1220: resale, no PA licence, the written reason, no EIN). The answers: Blanket, Retail trade, Resale (G), ID from
Ukraine; the company: Roman Boichenko, 3 Petra Zaporozhtsia St, Kyiv 02125, Ukraine (the phone has to be xxx-xxx-xxxx). Avalara
fills the ID in later SST forms by itself after the first ones; the owner pastes it where it doesn't (an agent never types it).
**Not filed — the state's own registration is needed:** California, New York, Florida, Illinois, Missouri, Texas (as before),
Louisiana and New Mexico (only a request for the state's own form), Maryland (MD registration), Massachusetts (MA account or US
EIN), Alabama and Maine (the MTC form: registered states), Colorado (state licence), Connecticut («registered» retailer), Hawaii
(GE number), Virginia (a state tax ID; a foreign number is doubtful, 1 order). Delaware and New Hampshire have no sales tax.
US orders by state up to 2026-10-24 (115): the filed states hold ~40, the skipped ones ~66.

### Incident 2026-10-13 — Payoneer refused every payment to Gelato

- **What happened:** order #4202433342 (Margot, 21:52) and then a top-up of the Gelato USD wallet ($50) failed: «Top-up transaction
  failed. The program has exceeded the allowed limit. Please contact Payoneer support to request an increase in the limit.» The first
  refusal of the direct integration; the failed tries never show in Payoneer's history (and Gelato's payments reach it late).
- **Payoneer support (chat, ticket 261013-020209):** first said there is no limit on their side ($50,000 a month on payments
  *received* from Gelato — they mixed up the direction) and sent the owner to Gelato; after the wallet top-up failed too, they
  escalated it and promised to change the limits on his account **within 24 hours**. On 14.10 they explained by email: payments
  of this integration are capped at **10 a day and 30 a month** (he makes 65–90 a month); they asked for the wanted values — he
  asked for 40 a day, 600 a month, 1,000 USD a day, 10,000 USD a month, with the Christmas season as the reason.
- **Meanwhile:** the Payoneer card is linked in Gelato and goes through — the waiting orders can be paid with it (on the order:
  Edit, after the refusal).
- **To check on 2026-10-14:** a small wallet top-up ($20) through Payoneer. It passes → the direct integration is the main method
  again, the card the spare. It fails → write to Payoneer with the ticket number.
- If it comes back before Christmas: the limit on outgoing payments to Gelato grows with the shop — ask Payoneer for a margin.

## Where in the code

- [app/studio/gelato.py](../../app/studio/gelato.py) — `KEYS`, `OLD_NAME`, `api_key()`, `account_id()`, `accounts()`, `untagged_account()`, `check_key()`, `ORDER_API`, `PRODUCT_API`, `_FORBIDDEN`, `_allowed()`, `_human()`, `call()`, `search_orders()`, `all_orders()`, `slim_order()`, `product()`, `page_counts()`, `_fresh_catalog()`, `CATALOG_HOURS`, `photobook_geometry()`, `create_draft_order()`, `get_order()`, `TRACKING_READS`, `shipments_of()`, `attach_shipments()`, `slot_of()`, `history()`, `cached_history()`, `HISTORY_FRESH`, `HISTORY_DONE`
- [app/studio/gelato_accounts.py](../../app/studio/gelato_accounts.py) — `_switch()`, `_forget()`, `status()`, `open_orders()`, `old_id()`, `OPEN_STAGES`, `_resync()`
- [app/studio/sync.py](../../app/studio/sync.py) — `_gelato_part()`
- [app/web/js/pages/settings.js](../../app/web/js/pages/settings.js) — `gelatoCard()`, `oldAccountField()`, `switchGelato()`, `forgetOldGelato()`
- [app/studio/printorders.py](../../app/studio/printorders.py) — `GELATO_SHIPPED`
- [app/studio/tunnel.py](../../app/studio/tunnel.py) — `CLOUDFLARED`, `_URL_RE`, `FileTunnel`, `_head_ok()`, `_head_ok_public_dns()`, `TunnelRegistry`, `cleanup_stale()`, `_ends_with_us()`
- [app/studio/creator/printfolder.py](../../app/studio/creator/printfolder.py) — `gelato_page_options()`, `_gelato_page_count()`
- [app/studio/creator/gelato_send.py](../../app/studio/creator/gelato_send.py) — `gelato_page_counts()`, `gelato_pages_problem()`, `_pages_problem()`, `create_gelato_draft()`, `_gelato_draft()`, `_journal_readback()`, `GELATO_PLACEHOLDER_PHONE`
- [app/studio/creator/sending.py](../../app/studio/creator/sending.py) — `_unknown_outcome()`
- [app/studio/creator/photobook.py](../../app/studio/creator/photobook.py) — `build_photobook_pdf()`, `COVER_TRIM_WARN_MM`, `BLANK_DPI`, `_one_idat()`
- [app/studio/core.py](../../app/studio/core.py) — `DEFAULT_SETTINGS`
- [app/studio/orders.py](../../app/studio/orders.py) — `page_options()`, `_files()`
- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — `renderTunnels()`, `startCountdown()`, `loadPageCounts()`, `formatProblem()`, `formatCard()`
- Tests: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`GelatoDraftFlow`), [app/tests/test_library_creator.py](../../app/tests/test_library_creator.py) (`SafetyRails`, `GelatoValidation`), [app/tests/test_orders.py](../../app/tests/test_orders.py) (`GelatoLength`), [app/tests/test_states.py](../../app/tests/test_states.py) (`GelatoTracking`), [app/tests/test_gelato_accounts.py](../../app/tests/test_gelato_accounts.py), [app/tests/test_gelato_history.py](../../app/tests/test_gelato_history.py)

## Related

- [Order Creator](../features/order-creator.md) · [Send journal](../features/send-journal.md) · [Security](../security.md) · [Printer rule](../rules/printer-rule.md)
