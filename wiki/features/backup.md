---
title: Backup to Google Drive
type: feature
updated: 2026-11-12
code:
  - app/studio/backup.py
  - app/tools/restore_keys.py
---
# Backup to Google Drive

> Every 3 days the program packs **the whole Book Studio folder** and the **mockup templates** into one 7-Zip archive under the owner's password and puts it in Google Drive, whose desktop app uploads it. The keys are inside, readable, so a restore on another computer works at once. Settings → «Резервна копія» ([Settings](settings.md)).

## What goes in (`sources()`)
- The templates folder, in place (`mockups.places()["templates"]`; in the portable layout `runtime/Templates`, outside `Book Studio`). It is added only when outside the program folder, and backed up where it is: a second copy would drift.
- `Ключі (відкрито).json`: every vault key decrypted (`Vault.readable()`), except the backup password. The vault is DPAPI, so on another PC or Windows user `vault.json` does not open. It goes in from memory over 7-Zip's stdin, never readable on disk. `Як відновити.txt` (`README_FILE`) holds the restore steps.
- The whole `Book Studio` folder (`PROGRAM_DIR`, the parent of `core.ROOT`): code, `app/data` (archive, library, profit, logs, settings, vault), `pipeline/books`, `.secrets.txt`. Left out (`SKIP`): `app/data/window-profile`, `app/data/work-browser`, `app/data/tmp`, `.tmp`, the spare `Трафарети мастхев (копія)`, and `__pycache__`. It is added **last**: every later addition rewrites what the archive already holds.
- Stored, not compressed (`-mx0`): pictures do not shrink.

## Where and how
- **Destination:** the disk labelled "Google Drive" → `My Drive\Book Studio — резервні копії\Book Studio YYYY-MM-DD HH-MM.7z` (`drive_root()`, `target()`).
- **7-Zip:** `app/bin/7za.exe` (not in git), AES-256 with names hidden (`-mhe=on`), below normal priority. Written as `.7z.part` and renamed when finished; a leftover `.part` goes on the next run.
- **Password:** set in Settings (at least 12 characters, no quotes), kept in the vault as `backup_password`. It cannot be recovered; changing it does not touch earlier copies.
- **Retention** (`to_remove()`): the last 7 (`KEEP_LAST`) plus the newest of each of the last 12 months (`KEEP_MONTHS`); the rest are deleted from the Drive folder, which keeps them in its trash for 30 days.
- **When** (`start_if_due()`): at launch after `START_DELAY` (120 s), then every `CHECK_EVERY` (6 h) while the program runs, when the last copy is `EVERY_DAYS` (3) old (`due()` allows an hour's slack) and password, 7-Zip and Drive are all there. «Зробити копію зараз» makes one any time. It is a background job: closing the window waits for it. Never in the preview or tests (`core.SANDBOX`).
- Files another program holds open are skipped with a warning (7-Zip exit code 1); their count shows in Settings.
- The result (`last`: time, file, size, seconds, skipped) or the error goes to `settings.json` → `backup`.

## Restoring
1. Unpack with 7-Zip and the password.
2. Same PC and Windows user: the vault opens as is. Another one: `python app/tools/restore_keys.py "…\Ключі (відкрито).json"` puts the keys back (prints only names); then delete that file.
3. `python app/tools/make_shortcut.py` makes the shortcut. Python and packages: [Portable copy](../dev/portable.md).

## Why
- The whole folder, secrets included: a restore must need nothing else.
- Keys travel readable because the vault is tied to one Windows user.
- Templates are backed up in place and stored uncompressed to keep one copy and a fast run.
- Drive's cache stays off drive C.

## Where in the code
- [app/studio/backup.py](../../app/studio/backup.py) — `sources()`, `to_remove()`, `due()`, `start_if_due()`, `SKIP`
- [app/studio/vault.py](../../app/studio/vault.py) — `readable()`
- [app/web/js/pages/settings.js](../../app/web/js/pages/settings.js) — `backupCard()`, `watchBackup()`
- [app/tools/restore_keys.py](../../app/tools/restore_keys.py) — `main()`
- [app/tests/test_backup.py](../../app/tests/test_backup.py) — the rules and a real 7-Zip run on a made-up folder

## Related
- [Settings](settings.md) · [Data safety](../architecture/data-safety.md) · [Data](../architecture/data.md) · [Security](../security.md) · [Runtime](../architecture/runtime.md)
