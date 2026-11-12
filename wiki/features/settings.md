---
title: Settings
type: feature
updated: 2026-11-12
code:
  - app/web/js/pages/settings.js
  - app/web/js/pages/settings-dialogs.js
  - app/studio/settings_api.py
  - app/studio/transfer.py
---
# Settings

> `#/settings[/<block>]`, the icon at the bottom of the rail (it carries a dot when a service lacks a key or a sign-in). A minimal page: service keys, the Etsy connection, the optional modules, the backup, the settings transfer, the data folder. Every block is collapsed to one line with its status; a block that needs something opens itself.

## Blocks, in order
- **Keys from earlier programs** (only when found and not already set): a one-time import of keys from the programs Book Studio replaced; «Перенести» (`legacy_sources()`). The preview server offers none.
- **Etsy:** key fields; not connected → an access link from the Profit Calculator (`…/?sync=…`) or, when `security.etsyKyivOnly` is set, «Увійти в Etsy (лише з київського ПК)», else «Увійти в Etsy». Connected → shop name, «Disconnect», copy the session key for another PC. Details: [Etsy](../integrations/etsy.md).
- **Printify** (optional: «Не обов'язково · не підключено», no warning mark, closed): token and a connection check. Printify is read-only (`printify.retired()`): «… · лише читання старих замовлень», «Нові книги друкує Gelato», no template picker; the Master picker (`pickMaster()` in `settings-dialogs.js`) is offered only on a copy that is not read-only ([Printify](../integrations/printify.md)).
- **Gelato:** key, formats, «28 or 30 pages», connection check, and the switch to a second account (button «Перейти на новий акаунт Gelato», then «Старий акаунт · лише читання»). How it works: [Gelato](../integrations/gelato.md).
- **«Модулі»:** install or remove the text check and upscaling, plus the text check's own switches: [Optional modules](modules.md).
- **«Резервна копія»:** password, Drive folder with Open, «Зробити копію зараз», last copy or error; opens itself when there is no password or the last try failed: [Backup](backup.md).
- **«Перенесення налаштувань»:** export and import, below.
- **Program data:** the path to `app/data` and an Open button.

Technical values (Master positions, artwork sizes, product UID, the EUR→USD rate, link lifetime) are not shown or editable in the interface, only in `settings.json`.

## Keys
A password field → `POST /api/secrets` → the vault (DPAPI, one Windows user). Only «saved» and the last 4 characters come back. Typed names are `EDITABLE_SECRETS` (`etsy_keystring`, `etsy_shared_secret`, `printify_token`, `gelato_api_key`); `gelato_old_api_key` is written only by the account switch. The preview server (`core.SAMPLE`) stores no keys and says so.

## Other settings
- Rail bottom menu: the «Анімації» button holds one item, «Мінімум анімацій», saved as `ui.reduceMotion` through `POST /api/settings/ui`; the browser remembers it only for the first frame, a failed save shows a message.
- `browser` section (not in the UI): `hosts` (`gelato.com`, `canva.com`) and optionally `exe` and `profile`. With an `exe`, `_open_url()` opens those hosts in that browser profile (`_open_in_profile()`) and every other link in the default browser. The portable copy uses its own Edge profile.
- Looking for earlier programs' keys decrypts their files only when those changed (`_legacy_names()`).

## Settings transfer
One small 7-Zip file with the settings and keys, to carry to another computer or copy of Book Studio. Settings → «Перенесення налаштувань»: «Експорт у файл» and «Імпорт із файлу» (`transferCard()`, `transfer.py`).
- **In:** `Налаштування.json` (`settings.json` without what belongs to one computer), `Ключі (відкрито).json` (every vault key decrypted, except the backup password; it is built in memory and never lies readable on disk), and the slides' `design`, `saved-colours`, `schemes` under `app/data/slides`. **Not in:** books, orders, pictures, per-book slide `sets`, mockup paths. The whole folder is what the [backup](backup.md) is for.
- **The file:** named `Налаштування Book Studio {stamp}.7z` (`NAME`), under the **backup password** (the same `7za.exe`, AES-256, names hidden), written as `.part` and renamed. The save dialog picks the place. Export needs the backup password set; the button is off until then.
- **Import:** `desktop.pick_7z()` chooses the file; it opens with the vault's backup password or one typed in the field (shown when none is set, or after a wrong one; a password containing `"` is refused). Settings are merged, keys go into the vault (Windows encrypts them for this user), the three slides folders are replaced, and a typed password becomes the backup password when none existed. **Before** anything changes, the current `settings.json`, `vault.json` (still encrypted) and slides folders are copied to `app/data/import-backup/<time>[-n]/` (`_save_current()`). A wrong password or foreign file changes nothing. The opened keys file is deleted from `tmp/import-*` as soon as it is read, and `sweep()` clears leftovers at launch. The routes refuse in the preview and in tests.
- **Never travels:** `_computer_bound()` removes the `backup`, `workshop` and `security` sections, `browser.exe`, `printify.readOnlyFrom` and `manualApprovalConfirmedAt`, on export **and on import**. Only known key names go back to the vault. New safety switches belong in `_computer_bound()`.

## Why
- Printify is optional with no warning mark: every order goes through Gelato.
- Technical values are hidden so they cannot be broken from the UI.
- Transfer never carries the safety switches (Etsy only from Kyiv, the Printify read-only date, the manual-approval stamp), so a colleague's file cannot switch the owner's rules off, nor the reverse.
- The preview and sandbox never show or store real keys.

## Where in the code
- [app/web/js/pages/settings.js](../../app/web/js/pages/settings.js) — `mount()`, `etsyCard()`, `gelatoCard()`, `transferCard()`, `modulesCard()`
- [app/web/js/pages/settings-dialogs.js](../../app/web/js/pages/settings-dialogs.js) — `oauthFlow()`, `pickMaster()`
- [app/studio/settings_api.py](../../app/studio/settings_api.py) — `EDITABLE_SECRETS`, `legacy_sources()`, `_open_url()`, `_open_in_profile()`
- [app/studio/transfer.py](../../app/studio/transfer.py) — `export_to()`, `import_from()`, `_computer_bound()`, `_save_current()`, `sweep()`
- [app/tests/test_transfer.py](../../app/tests/test_transfer.py) — the tests call `export_to` and `import_from` directly

## Related
- [Security](../security.md) · [Etsy](../integrations/etsy.md) · [Gelato](../integrations/gelato.md) · [Printify](../integrations/printify.md) · [Backup](backup.md) · [Optional modules](modules.md) · [Rail](rail.md)
