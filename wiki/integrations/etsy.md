---
title: Etsy — read-only
type: integration
updated: 2026-09-27
code:
  - app/studio/etsy.py
---
# Etsy

> Etsy Open API v3, **read-only** (`shops_r transactions_r`): the shop's receipts and listings.
> Signing in to Etsy is done only on the Kyiv computer ([security](../security.md)).

## Keys and sign-in

- **App keys**: Keystring and Shared Secret (Etsy Developers → Your apps). Header
  `x-api-key: <keystring>:<secret>`. Just the keys are already enough to check listings (no sign-in
  needed).
- **Sign-in (OAuth 2.0 + PKCE)**, two paths in Settings, after confirming "I'm on the Kyiv PC":
  1. the program is running on the Kyiv PC — the sign-in page opens there, and Etsy redirects to
     `http://localhost:47821/etsy/callback` (the owner doesn't do this — there's no program on the Kyiv
     PC);
  2. **the main path:** the program is here — the link is copied and opened on the Kyiv PC; the browser
     there will navigate to `localhost…` (the page won't load — that's expected), and the full address
     gets pasted back.
  The return address has to be added under Etsy Developers → Callback URLs. The link is valid for an
  hour.
- **The access link** (`…?sync=<iv:tag:cipher>`) from Etsy Profit Calculator: a session, encrypted with
  AES-GCM using a key derived from the Shared Secret (a fallback secret, as in Profit Calculator). The
  simplest way to connect. Works the other way too: "Copy session key" for another PC.
- **Tokens** are kept in the vault (`etsy_tokens`), and refresh themselves 5 minutes before they expire.
  Etsy issues **one-time-use** refresh tokens: if another program (Profit Calculator) refreshed the same
  session, this one stops working → "reconnect the session".

## Data

- `fetch_all_receipts()` — every paid receipt (including cancelled/refunded ones), newest first, 100 at
  a time, a 0.12 s pause; with `min_last_modified` — only changed ones (an incremental sync). No more
  than `MAX_RECEIPTS` = 20,000; beyond that, the list is marked incomplete (`httpc.Listing`) and the sync
  warns.
- `normalize_receipt()` ([profit.py](../../app/studio/profit.py)) transforms a receipt: fees, items with
  variations (personalization), address, refunds. Etsy's text arrives HTML-escaped (`&quot;`, `&amp;`) —
  `plain()` un-escapes it.
- **Not in the API**: the seller's own tabs (e.g. "In Production"). So an order's stage is worked out
  from whether it has a print order ([rules/order-stages.md](../rules/order-stages.md)).
- `fetch_listing()` — title, status, shop, main photo (one request, `includes=Images`).

## Errors

`_human()` turns Etsy's responses into understandable messages, with `code: etsy_auth` when the
connection needs to be re-made. A 401 on a request → one forced token refresh and a retry. The token
refresh is a POST that only reads, so it can be retried after a dropped connection
(`idempotent=True`).

## Where in the code

- [app/studio/etsy.py](../../app/studio/etsy.py) — `SCOPES`, `keys()`, `api_key_header()`, `start_oauth()`, `complete_oauth()`, `refresh_tokens()`, `get()`, `ensure_shop()`, `decode_session_key()`, `encode_session_key()`, `import_session()`, `fetch_listing()`, `fetch_all_receipts()`, `MAX_RECEIPTS`, `parse_listing_ref()`, `_oauth_callback()`, `port_warning()`, `_human()`
- [app/studio/sync.py](../../app/studio/sync.py) — `normalize_receipt()`, `plain()`
- [app/web/js/pages/settings.js](../../app/web/js/pages/settings.js) — `oauthFlow()`, `etsyCard()`
- Tests: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`EtsyOAuth`, `OpenUrlGuard`)

## Related

- [Security](../security.md) · [Sync](../rules/sync-policy.md) · [Settings](../features/settings.md)
