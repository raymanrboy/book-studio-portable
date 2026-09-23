---
title: Send journal for Printify and Gelato
type: feature
updated: 2026-09-20
code:
  - app/studio/sendlog.py
---
# Send journal

> Every attempt to send something to a printer — a book/order in Printify, a draft in Gelato — is
> recorded as its own file: what went out, which files and PDF, what the service answered, where it
> broke. The owner asked for this on 2026-09-17, to "make the mechanism ideal". There are no keys in the
> journal.

## Where

`app/data/logs/sends/YYYY-MM-DD_HHMMSS_<printify|gelato>_<title>.json`, the last 400 files (`KEEP`). To
open it — the dotted-list icon in the Order Creator:
- **always** — in the header, left of the Printify/Gelato switch ("Send journal"): Explorer highlights
  the newest record (`latest()`; the owner couldn't find the button when it only lived on result cards);
- on the result card — highlights the record for exactly that send; on an error card — the newest one.

## What's in a record

| Field | What it is |
|---|---|
| `provider`, `kind`, `title`, `at`, `seconds` | where (`printify` / `gelato`), what (`book`, `book+order`, `draft`), title, time, duration |
| `ok`, `error`, `errorType` | whether it worked; the error text the owner saw |
| `folder`, `format`, `books` | the folder of files and the Gelato format (of the first book); `books` — every book of the send (title, folder, format) |
| `steps` | the steps, in order (below) |
| `request`, `response` | the full request body for the creation, and the service's full response (with the address) |
| `orderRequest`, `orderResponse`, `orderError` | Printify: the On-hold order |
| `result` | what the owner saw on the result card |

Steps: **Gelato** — `files` (every PNG: size in px, bytes, errors) → `catalog` (the product, page count,
sizes from the catalog) → `pdf` (pages in the PDF, bytes, the cover's size in px, how many mm it will be
trimmed) → `link` (every PDF's address, `reachable`) → `readback` (what Gelato recorded in the draft: the
item, pages, the file, and whether it's already been fetched — `fileFetched`). **Printify** — `files`
(with SHA-256) → `master` → `uploads` (reused / new, image IDs by position) → `product` (the creation
request and response) → `verify` (positions) → `masterSafe` (the Master hasn't changed).

**An order with several books** (since 2026-09-20) — one record for the whole send: the per-book steps
repeat, each carrying a `book` field with the book's title (`files`, `uploads`, `product`, `verify`,
`catalog`, `pdf`, `archive`); `orderRequest` is a single one — the order is shared.

A record is also made when the send stopped at the file check — then there are fewer steps and no
`request` (nothing went out). If the journal fails to write, the send still happens anyway.

## Security

- Keys and tokens never make it into the journal: they only exist in request headers (tests check this).
- Buyer addresses do, so the journal lives only in `app/data` (not in git, [security.md](../security.md)).

## Where in the code

- [app/studio/sendlog.py](../../app/studio/sendlog.py) — `SENDS`, `KEEP`, `write()`, `attempt()`, `step()`, `latest()`, `_open()`
- [app/studio/creator.py](../../app/studio/creator.py) — `create_gelato_draft()`, `_gelato_draft()`, `_gelato_book()`, `_journal_readback()`, `create_printify_draft()`, `_printify_draft()`, `_printify_files()`, `_printify_images()`, `_printify_product()`, `_printify_order()`
- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — `renderSwitch()` (the icon in the header), `sendLogButton()`
- [app/web/css/app.css](../../app/web/css/app.css) — `.cr-tools`, `.mode-switch`
- [app/web/js/icons.js](../../app/web/js/icons.js) — the `sendLog` icon
- Tests: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`PrintifyDraftFlow`, `GelatoDraftFlow` — including `test_journal_button_shows_the_newest_record`)

## Related

- [Order Creator](order-creator.md) · [Gelato](../integrations/gelato.md) · [Printify](../integrations/printify.md) · [Data](../architecture/data.md)
