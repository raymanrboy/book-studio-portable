---
title: Settings
type: feature
updated: 2026-10-03
code:
  - app/studio/settings_api.py
  - app/studio/gelato_accounts.py
  - app/web/js/pages/settings.js
  - app/web/js/pages/settings-dialogs.js
---
# Settings

> A minimal page: service keys, the Etsy connection, the Printify template, the text check, the backup,
> the data folder. Every block is collapsed to one line with its status; a block that needs something opens on
> its own.
> The theme isn't here — it's in the menu at the bottom of the rail, under Settings' own icon (since 2026-09-30 Settings
> sit at the bottom of the rail, apart from the places). A key's ✓ lights up in the ink only once something is pasted;
> an empty save says so and lights the field up.

## Blocks (`#/settings[/<block>]`)

- **Keys found from earlier programs** (only if there's something to move) — "Move over": keys from
  Order Creator Printify (`.local/*.dpapi`) and Etsy Profit Calculator (`.env.local`/`.env`), the
  Printify upload cache. Looked for on the desktop, next to the Book Studio folder.
- **Etsy**: a key missing → Keystring / Shared Secret fields. Not connected → an "access link" from
  Profit Calculator (`…/?sync=…`), or "Sign in to Etsy (Kyiv PC only)" — see
  [integrations/etsy.md](../integrations/etsy.md). Connected → the shop name and "Disconnect".
  "Details": the saved keys, the return address (Callback URL), copying the session key for another PC.
- **Printify**: the token; the template (Master) and "24 pages"; the template-picker button — only when
  there isn't one yet; a connection check. From 1 October 2026 (`readOnly`): «лише читання старих замовлень»,
  «Нові книги друкує Gelato», no template picker ([printify](../integrations/printify.md)).
- **Gelato**: the key; three formats and "28 or 30 pages"; a connection check. A saved key has **«Перейти на новий
  акаунт Gelato»** (the swap icon) in place of «Замінити ключ» — a dialog for the new account's key; the current one
  becomes «Старий акаунт · лише читання» with its hint, «Ще N замовлень в роботі» / «Його замовлення завершено», its
  own connection check and a bin to remove it (since 2026-09-29, [gelato](../integrations/gelato.md#his-own-account--two-keys-during-the-move)).
  While the old one is kept, the new key has the usual «Замінити ключ» (to fix a mistyped one).
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
- **Резервна копія** (since 2026-09-27): the archive's password (set / change — the owner writes it down),
  the Google Drive folder with an "Open" button, «Зробити копію зараз» with its progress, the last copy (when,
  size, files skipped) or the last error. Opens on its own while there is no password or the last try failed; a
  copy started on launch is followed when the page opens. In detail — [backup.md](backup.md).
- **Program data**: the path to `app/data` and an "Open" button.

Technical values (Master positions, artwork sizes, the product UID, the EUR→USD rate, how long a link
lives) are deliberately not shown or editable from the interface — the owner's decision. The
`/api/settings/gelato` and `/api/settings/printify` routes, which the interface never called, were
removed on 2026-09-23.

- **The browser profile for chosen sites** (since 2026-10-01): the settings' `browser` section: `exe` (Cent Browser's
  `Chrome.exe`), `profile` (`Profile 6` = «Work»), `hosts` (`gelato.com`, `canva.com`). With it, `_open_url()` opens
  those sites in that profile (`_open_in_profile()`), and every other link opens in the default browser. It isn't in
  the interface; it is written straight into `settings.json` ([decisions](../decisions.md)).

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
back. Names: `etsy_keystring`, `etsy_shared_secret`, `printify_token`, `gelato_api_key`; `gelato_old_api_key` is
written only by the switch (`POST /api/gelato/switch`), never typed in.

## Picking the Master (Printify)

`pickMaster()`: shop → a list of products, or an ID/link → an analysis (`analyze_master()`: the cover
and page_1…page_N positions, variants, sizes) → "Make it the Master" (confirmation). The Master is only
ever read.

## Where in the code

- [app/web/js/pages/settings.js](../../app/web/js/pages/settings.js) — `mount()`, `card()`, `details()`, `secretField()`, `legacyCard()`, `etsyCard()`, `printifyCard()`, `gelatoCard()`, `oldAccountField()`, `switchGelato()`, `forgetOldGelato()`, `dataCard()`, `textcheckCard()`, `loadTextcheck()`, `saveTextcheck()`, `SECRET_LABELS`
- [app/web/js/pages/settings.js](../../app/web/js/pages/settings.js) — `backupCard()`, `watchBackup()`, `redrawBackup()`
- [app/web/js/pages/settings-dialogs.js](../../app/web/js/pages/settings-dialogs.js) — `oauthFlow()`, `pickMaster()`
- [app/studio/settings_api.py](../../app/studio/settings_api.py) — `integrations()`, `_settings()`, `_secret()`, `_open_url()`, `_open_in_profile()`, `_legacy_values()`, `_legacy_names()`, `legacy_sources()`, `_legacy_import()`, `EDITABLE_SECRETS`, `DESKTOP`
- [app/studio/gelato_accounts.py](../../app/studio/gelato_accounts.py) — `status()`, `_switch()`, `_forget()`
- [app/studio/printify.py](../../app/studio/printify.py) — `analyze_master()`, `_save_master()`
- [app/studio/etsy.py](../../app/studio/etsy.py) — `status()`, `import_session()`
- [app/studio/textcheck/ollama.py](../../app/studio/textcheck/ollama.py) — `status()`, `start_ollama()`
- [app/studio/textcheck/routes.py](../../app/studio/textcheck/routes.py) — `_save_settings()`, `_start()`

## Related

- [Security](../security.md) · [Etsy](../integrations/etsy.md) · [Printify](../integrations/printify.md) · [Gelato](../integrations/gelato.md)
