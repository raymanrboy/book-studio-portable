---
title: Etsy
type: integration
updated: 2026-11-12
code:
  - app/studio/etsy.py
---
# Etsy

> Etsy Open API v3, read-only (`SCOPES` = `shops_r transactions_r`): the shop's receipts, listings and payment ledger. Signing in to Etsy happens only on the Kyiv computer; the program itself runs on the other one.

## Keys and sign-in

- **App keys** (Keystring and Shared Secret, Etsy Developers → Your apps) go in the `x-api-key` header (`api_key_header()`). The keys alone are enough to read a listing; receipts need the sign-in.
- **Sign-in** is OAuth 2.0 with PKCE (`start_oauth()`, `complete_oauth()`), started from Settings after the owner confirms "I'm on the Kyiv PC" (`oauthFlow()`). The program is not on the Kyiv PC, so the usual path is: the link is copied and opened there, the browser ends on a `localhost…/etsy/callback` page that does not load (expected), and the full address is pasted back. The return address must be listed under Etsy Developers → Callback URLs; the link is valid for an hour. When the program itself runs on the Kyiv PC, the callback route catches the redirect (`_oauth_callback()`).
- **Access link**: a `?sync=…` link or key from the Etsy Profit Calculator is accepted as a ready session (`import_session()`, `decode_session_key()`); "Copy session key" exports one for another PC.
- **Tokens** are kept in the vault (`etsy_tokens`) and refresh themselves 5 minutes before expiry (`refresh_tokens()`); a 401 forces one refresh and a retry. Etsy refresh tokens are single use: if another program refreshes the same session, this one must reconnect.
- **Kyiv-only rule**: while `security.etsyKyivOnly` is on (default; off in a copy for someone else), the server's URL opener refuses every etsy.com / etsy.me address except the sign-in page, so a foreign sign-in cannot block the shop ([Security](../security.md)).

## Data

- `fetch_all_receipts()` returns every paid receipt (cancelled and refunded included), newest first, 100 per request with a short pause; with `min_last_modified` only changed ones (incremental sync, see [Sync](../rules/sync-policy.md)). Past `MAX_RECEIPTS` the list is marked incomplete (`httpc.Listing`) and the sync warns.
- `normalize_receipt()` and `plain()` ([sync.py](../../app/studio/sync.py)) turn a receipt into the program's row: fees, items with variations, address, refunds; Etsy's HTML-escaped text is un-escaped. `ship_by` is the earliest item `expected_ship_date`; an open receipt stored without it forces one whole Etsy read.
- `fetch_listing()` gives title, status, shop and main photo (used when adding a book).
- The payment ledger is read in the same sync ([Reconciliation](../rules/reconciliation.md)).
- The API has no seller tabs ("In Production"), so the stage is computed from print orders ([Order stages](../rules/order-stages.md)).
- Nothing is written to Etsy: no marking shipped, no listings. The owner marks orders shipped by hand.

## Errors

`_human()` maps responses to readable messages; `code: etsy_auth` means the connection must be redone. The token refresh is a POST that only reads, so it is retried after a dropped connection (`idempotent=True`). If the wanted port is busy, `port_warning()` tells the owner the registered callback may not match.

## Why
- Agents browse Etsy signed out only; no sign-in, no changes, never around a CAPTCHA — nothing may put the shop at risk.

## Where in the code
- [app/studio/etsy.py](../../app/studio/etsy.py) — `SCOPES`, `start_oauth()`, `complete_oauth()`, `refresh_tokens()`, `fetch_all_receipts()`, `MAX_RECEIPTS`
- [app/studio/sync.py](../../app/studio/sync.py) — `normalize_receipt()`, `plain()`
- [app/studio/settings_api.py](../../app/studio/settings_api.py) — `_open_url()`
- [app/web/js/pages/settings-dialogs.js](../../app/web/js/pages/settings-dialogs.js) — `oauthFlow()`

## Related
- [Security](../security.md) · [Sync](../rules/sync-policy.md) · [Settings](../features/settings.md)
