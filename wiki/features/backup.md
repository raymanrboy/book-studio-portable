---
title: Backup to Google Drive
type: feature
updated: 2026-09-29
code:
  - app/studio/backup.py
  - app/tools/restore_keys.py
---
# Backup to Google Drive

> Every 3 days, 2 minutes after launch, the program packs **the whole Book Studio folder** and the **mockup
> templates** into one 7-Zip archive under the owner's password and puts it in Google Drive (the "Google Drive for
> desktop" app uploads it on its own). The keys are inside, readable, so a restore on another computer works at once.
> Built on 2026-09-27 ([decision](../decisions.md)).

## What goes in

- The whole `Book Studio` folder: the code, `app/data` (orders archive, library, profit, logs, settings, the vault),
  the Workshop's books `pipeline/books`, `.secrets.txt` too — the owner: "just the whole folder, everything".
  Left out only: `app/data/window-profile` (Edge holds it open), `app/data/tmp`, `.tmp`, `__pycache__`, and the spare
  copy `Трафарети мастхев (копія)` in the Book Studio folder (the templates themselves go in every copy; since
  2026-09-29) (`SKIP`).
- The mockup templates folder, from where it is (`mockups.places()["templates"]`, usually
  `D:\Roman\Desktop\Трафарети мастхев`) — backed up in place, not copied into the program (two copies would drift).
- `Ключі (відкрито).json` — every key from the vault, decrypted (`Vault.readable()`), except the backup password
  itself. The vault is DPAPI: on another computer or another Windows user `vault.json` from the copy won't open.
  Goes in straight from memory (7-Zip's `-si`), never onto the disk readable.
- `Як відновити.txt` — the restore steps (`README`).
- ~8.7 GB + 1.5 GB of templates on 2026-09-27; stored, not compressed (`-mx0`: pictures don't shrink).

## Where and how

- **Google Drive for desktop** (installed 2026-09-27; its cache on `D:\Google Drive Cache` — registry
  `HKCU\Software\Google\DriveFS\ContentCachePath`, the owner keeps drive C clean). Its disk is labelled "Google
  Drive" (G:); the program finds "My Drive" there by itself (`drive_root()`) and writes to
  `My Drive\Book Studio — резервні копії\Book Studio YYYY-MM-DD HH-MM.7z`.
- **7-Zip** `app/bin/7za.exe` (26.03, from the official GitHub release `ip7z/7zip`, hash checked; not in git like
  the rest of `app/bin`). AES-256 with the file names hidden (`-mhe=on`). The archive is written as `.7z.part` and
  renamed when finished; a `.part` left by a cut-off copy goes on the next run.
- **Password**: set by the owner in Settings → «Резервна копія» (at least 8 characters, no quotes), kept in the vault
  as `backup_password`. Can't be recovered — he writes it down. Changing it doesn't touch old copies (they keep the
  old one).
- **Which copies stay** (`to_remove()`): the last 7, plus the newest of each of the last 12 months. The rest are
  deleted from the Drive folder — Drive keeps them in its trash for 30 days.
- **When** (`start_if_due()`): on launch, after `START_DELAY` (120 s), if the last copy is 3 days old (`EVERY_DAYS`,
  an hour's slack) and the password, 7-Zip and Drive are all there. Never in the preview or the tests (`SANDBOX`).
  The button «Зробити копію зараз» makes one any time. It's a background job: closing the window waits for it.
- Files another program holds open are skipped with a warning (7-Zip's exit code 1) — their count shows in Settings.
- The result (`last`: time, file, size, seconds, skipped) or the error goes to `settings.json` → `backup`.

## Restoring

1. Unpack the archive with 7-Zip and the password.
2. The same PC and Windows user — the vault opens as is. Another one — `python app/tools/restore_keys.py
   "…\Ключі (відкрито).json"` puts the keys back into the vault (prints only the names), then delete that file.
3. `python app/tools/make_shortcut.py` for the shortcut. Python and its packages — [setup](../dev/setup.md).

A test restore of the first real copy is to be done with the owner.

## Where in the code

- [app/studio/backup.py](../../app/studio/backup.py) — `drive_root()`, `target()`, `sources()`, `copies()`, `to_remove()`, `due()`, `make()`, `start_if_due()`, `schedule()`, `status()`, `SEVEN_ZIP`, `SKIP`, `EVERY_DAYS`, `KEEP_LAST`, `KEEP_MONTHS`, `START_DELAY`
- [app/studio/vault.py](../../app/studio/vault.py) — `readable()`
- [app/web/js/pages/settings.js](../../app/web/js/pages/settings.js) — `backupCard()`, `watchBackup()`
- [app/tools/restore_keys.py](../../app/tools/restore_keys.py) — `main()`
- [app/tests/test_backup.py](../../app/tests/test_backup.py) — the rules and a real 7-Zip run on a made-up folder

## Related

- [Settings](settings.md) · [Data](../architecture/data.md) · [Security](../security.md) · [Launch](../architecture/runtime.md)
