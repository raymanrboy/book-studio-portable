---
title: Settings
type: feature
updated: 2026-10-28
code:
  - app/studio/settings_api.py
  - app/studio/gelato_accounts.py
  - app/web/js/pages/settings.js
  - app/web/js/pages/settings-dialogs.js
---
# Settings

> A minimal page: service keys, the Etsy connection, the Printify template, the optional modules, the backup, the settings transfer,
> the data folder. Every block is collapsed to one line with its status; a block that needs something opens on its own.
> The theme isn't here — it's in the menu at the bottom of the rail, under Settings' own icon (Settings sit at the bottom of the rail,
> apart from the places). A key's ✓ lights up in the ink only once something is pasted; an empty save says so and lights the field up.

## Blocks (`#/settings[/<block>]`)

In order on the page:

- **Keys found from earlier programs** (only if there's something to move) — "Move over": keys from
  Order Creator Printify (`.local/*.dpapi`) and Etsy Profit Calculator (`.env.local`/`.env`), the
  Printify upload cache. Looked for on the desktop, next to the Book Studio folder.
- **Etsy**: a key missing → Keystring / Shared Secret fields. Not connected → an "access link" from
  Profit Calculator (`…/?sync=…`), or "Sign in to Etsy (Kyiv PC only)" — see
  [integrations/etsy.md](../integrations/etsy.md). Connected → the shop name and "Disconnect".
  "Details": the saved keys, the return address (Callback URL), copying the session key for another PC.
- **Printify** (optional — no token means «Не обов’язково», no warning mark, the card stays closed): the token; the template (Master) and
  "24 pages"; the template-picker button — only when there isn't one yet; a connection check. Printify is read-only (`readOnly`):
  «лише читання старих замовлень», «Нові книги друкує Gelato», no template picker ([printify](../integrations/printify.md)).
- **Gelato**: the key; three formats and "28 or 30 pages"; a connection check. A saved key has **«Перейти на новий акаунт Gelato»** in
  place of «Замінити ключ» — the switch to the owner's own account, described on
  [gelato](../integrations/gelato.md#his-own-account--two-keys-during-the-move) (the old account stays as «Старий акаунт · лише читання»
  with its own check and a bin; while it is kept, the new key has the usual «Замінити ключ»).
- **Модулі**: the optional heavy parts (text check, upscaling) — install from the internet or from a file, remove; under the installed text
  check its own switches, model and Ollama's status. Everything about it — [optional modules](modules.md); what the text check does —
  [text-check.md](text-check.md). The block is drawn right away from the settings; Ollama's status is fetched by a separate request, so
  Settings doesn't wait for it.
- **Резервна копія**: the archive's password (set / change — the owner writes it down), the Google Drive folder with an "Open" button,
  «Зробити копію зараз» with its progress, the last copy or the last error. Opens on its own while there is no password or the last try
  failed; a copy started on launch is followed when the page opens. Everything about it — [backup.md](backup.md).
- **Перенесення налаштувань**: «Експорт у файл» / «Імпорт із файлу» — the settings, keys and slide schemes in one file under the backup
  password. Everything about it — [settings-transfer.md](settings-transfer.md).
- **Program data**: the path to `app/data` and an "Open" button.

Technical values (Master positions, artwork sizes, the product UID, the EUR→USD rate, how long a link
lives) are deliberately not shown or editable from the interface — the owner's decision.

- **The browser profile for chosen sites**: the settings' `browser` section: `exe` (Cent Browser's
  `Chrome.exe`), `profile` (`Profile 6` = «Work»), `hosts` (`gelato.com`, `canva.com`). With it, `_open_url()` opens
  those sites in that profile (`_open_in_profile()`), and every other link opens in the default browser. It isn't in
  the interface; it is written straight into `settings.json` ([decisions](../decisions.md)).
- The theme and "reduce motion" are both saved in the program's settings, and both come from there on
  launch (the browser only remembers the theme for the first frame); a failed save shows a message.
- Looking for keys in the old programs (`legacy_sources()`) only decrypts their files when those files
  have changed, not every time Settings is opened (`_legacy_names()`).
- **The preview server** (`app/tools/dev_server.py`, `core.SAMPLE`) doesn't show keys from the old
  programs, and doesn't save any key: "This is a preview server on made-up data — keys aren't stored here".

## Keys

A password field → `POST /api/secrets` → `Vault` (DPAPI). Only "saved" and the last 4 characters come
back. Names: `etsy_keystring`, `etsy_shared_secret`, `printify_token`, `gelato_api_key`; `gelato_old_api_key` is
written only by the switch (`POST /api/gelato/switch`), never typed in.

## Picking the Master (Printify)

`pickMaster()`: shop → a list of products, or an ID/link → an analysis (`analyze_master()`: the cover
and page_1…page_N positions, variants, sizes) → "Make it the Master" (confirmation). The Master is only
ever read.

## Where in the code

- [app/web/js/pages/settings.js](../../app/web/js/pages/settings.js) — `mount()`, `card()`, `details()`, `secretField()`, `legacyCard()`, `etsyCard()`, `printifyCard()`, `gelatoCard()`, `oldAccountField()`, `switchGelato()`, `forgetOldGelato()`, `dataCard()`, `modulesCard()`, `transferCard()`, `textcheckSettings()`, `loadTextcheck()`, `saveTextcheck()`, `SECRET_LABELS`
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
