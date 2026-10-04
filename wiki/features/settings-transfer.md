---
title: Moving the settings and keys
type: feature
updated: 2026-10-04
code:
  - app/studio/transfer.py
  - app/tests/test_transfer.py
---
# Moving the settings and keys

> One small file with the settings and the keys, to carry to another computer or between the ordinary and the portable Book
> Studio. Settings → «Перенесення налаштувань»: «Експорт у файл» and «Імпорт із файлу». Built 2026-10-03
> ([decision](../decisions.md)).

## What goes in

- `Налаштування.json` — `settings.json` without what belongs to one computer: the `backup` section (its state), `workshop`
  (the path to Upscayl), `browser.exe`.
- `Ключі (відкрито).json` — every key of the vault, decrypted (Windows locks `vault.json` to one user), except the backup
  password. From memory, never onto the disk readable.
- The slides' `design`, `saved-colours`, `schemes` folders (under `app/data/slides`).
- **Not** in: books, orders, pictures, the slides' per-book `sets`, the mockups' places (they are paths of one PC). The whole
  folder is what the [backup](backup.md) is for.

## The file

A 7-Zip under the **backup password** (the same `7za.exe`, AES-256, names hidden; `backup._seven_zip`), named
`Налаштування Book Studio ГГГГ-ММ-ДД.7z`; written as `.part`, renamed when done. The owner picks where in the usual save dialog
(`desktop.save_file`). Export needs the backup password set (the button is off until then).

## Import

The file is opened with the vault's backup password, or the one typed in the field next to the button (the field shows when this
PC has no backup password yet, or after a wrong one). On success: the settings are merged in (`core.settings.update`),
the keys go into the vault (Windows encrypts them for this user), the three slides folders are replaced, and if this PC had no
backup password the typed one becomes it. **Before** anything is replaced, the current `settings.json`, `vault.json` (still
encrypted) and the slides folders are copied to `app/data/import-backup/<time>/`. A wrong password or a foreign file changes
nothing. Never in the preview or the tests' sandbox (the routes refuse); the tests call `export_to` / `import_from` directly.

## Where in the code

- [transfer.py](../../app/studio/transfer.py): `export_to()`, `import_from()`, `_portable_settings()`, `_save_current()`, the two routes.
- `desktop.pick_7z()` — the open dialog for the file; the settings page — `transferCard()` in `web/js/pages/settings.js`.
- Tests: [test_transfer.py](../../app/tests/test_transfer.py).

## What never travels (2026-10-04)

The owner's safety switches — `security.*` (Etsy only from Kyiv) and `printify.readOnlyFrom` / `manualApprovalConfirmedAt` — are left out on export **and ignored on import** (`transfer._computer_bound()`): a file made on a colleague's copy, where they are off, must not switch them off on the owner's PC. Only the known key names are written back to the vault. The opened keys file is deleted from `tmp/import-*` as soon as it is read, and `transfer.sweep()` clears leftovers at the start. A password with `"` is refused.
