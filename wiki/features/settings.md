---
title: Settings
type: feature
updated: 2026-09-23
code:
  - app/studio/settings_api.py
  - app/web/js/pages/settings.js
---
# Settings

> A minimal page: service keys, the Etsy connection, the Printify template, the text check, the data
> folder. Every block is collapsed to one line with its status; a block that needs something opens on
> its own.
> The theme isn't here — it's in the menu at the bottom of the sidebar.

## Blocks (`#/settings[/<block>]`)

- **Keys found from earlier programs** (only if there's something to move) — "Move over": keys from
  Order Creator Printify (`.local/*.dpapi`) and Etsy Profit Calculator (`.env.local`/`.env`), the
  Printify upload cache. Looked for on the desktop, next to the Book Studio folder.
- **Etsy**: a key missing → Keystring / Shared Secret fields. Not connected → an "access link" from
  Profit Calculator (`…/?sync=…`), or "Sign in to Etsy (Kyiv PC only)" — see
  [integrations/etsy.md](../integrations/etsy.md). Connected → the shop name and "Disconnect".
  "Details": the saved keys, the return address (Callback URL), copying the session key for another PC.
- **Printify**: the token; the template (Master) and "24 pages"; the template-picker button — only when
  there isn't one yet; a connection check.
- **Gelato**: the key; three formats and "28 or 30 pages"; a connection check.
- **Text check** (since 2026-09-19): a "Check page text in the order card" switch, a "First take a quick
  look at which pages even have text" switch (since 2026-09-20 — the program decides on its own which
  pages to show the model; can be turned off if something seems to be getting skipped), the model (a
  picker icon — when Ollama has more than one that can see pictures), "on the GPU", "Check connection";
  Ollama not running → "Start" (the program can also start it itself before a check). The block is drawn
  right away, from the settings ("checking status…") — with both switches shown as saved (`prescan`
  comes in `GET /api/settings`; before 2026-09-23 the "quick scan" switch was drawn off at first),
  Ollama's status is fetched by a separate request — Settings doesn't wait for it (on Windows, a
  disabled Ollama only answers "no" after 2 s).
  In detail — [text-check.md](text-check.md).
- **Program data**: the path to `app/data` and an "Open" button.

Technical values (Master positions, artwork sizes, the product UID, the EUR→USD rate, how long a link
lives) are deliberately not shown or editable from the interface — the owner's decision. The
`/api/settings/gelato` and `/api/settings/printify` routes, which the interface never called, were
removed on 2026-09-23.

- The theme and "reduce motion" are both saved in the program's settings, and both come from there on
  launch (the browser only remembers the theme for the first frame); a failed save shows a message.
- Looking for keys in the old programs (`legacy_sources()`) only decrypts their files when those files
  have changed, not every time Settings is opened (`_legacy_names()`).
- **The preview server** (`app/tools/dev_server.py`, `core.SAMPLE`) doesn't show keys from the old
  programs, and doesn't save any key: "This is a preview server on made-up data — keys aren't stored
  here" (since 2026-09-23; before that its Settings used to offer to import the owner's real keys from
  the desktop).

## Keys

A password field → `POST /api/secrets` → `Vault` (DPAPI). Only "saved" and the last 4 characters come
back. Names: `etsy_keystring`, `etsy_shared_secret`, `printify_token`, `gelato_api_key`.

## Picking the Master (Printify)

`pickMaster()`: shop → a list of products, or an ID/link → an analysis (`analyze_master()`: the cover
and page_1…page_N positions, variants, sizes) → "Make it the Master" (confirmation). The Master is only
ever read.

## Where in the code

- [app/web/js/pages/settings.js](../../app/web/js/pages/settings.js) — `mount()`, `card()`, `details()`, `secretField()`, `legacyCard()`, `etsyCard()`, `printifyCard()`, `gelatoCard()`, `dataCard()`, `textcheckCard()`, `loadTextcheck()`, `saveTextcheck()`, `oauthFlow()`, `pickMaster()`, `SECRET_LABELS`
- [app/studio/settings_api.py](../../app/studio/settings_api.py) — `integrations()`, `_settings()`, `_secret()`, `_open_url()`, `_legacy_values()`, `_legacy_names()`, `legacy_sources()`, `_legacy_import()`, `EDITABLE_SECRETS`, `DESKTOP`
- [app/studio/printify.py](../../app/studio/printify.py) — `analyze_master()`, `_save_master()`
- [app/studio/etsy.py](../../app/studio/etsy.py) — `status()`, `import_session()`
- [app/studio/textcheck.py](../../app/studio/textcheck.py) — `status()`, `start_ollama()`, `_save_settings()`, `_start()`

## Related

- [Security](../security.md) · [Etsy](../integrations/etsy.md) · [Printify](../integrations/printify.md) · [Gelato](../integrations/gelato.md)
