---
title: Launch and shutdown
type: architecture
updated: 2026-10-03
code:
  - app/Book Studio.pyw
  - app/Запуск з консоллю.bat
  - app/studio/main.py
  - app/studio/desktop.py
  - app/tools/make_shortcut.py
---
# Launch and shutdown

> Desktop shortcut → `app/Book Studio.pyw` → a server on `127.0.0.1:47821` → a separate Edge window.
> When the window is closed, the program waits for background work and shuts itself down.

## Launch sequence

1. **`Book Studio.pyw`** (no console, `pythonw.exe`): checks the Pillow, img2pdf, pikepdf, cryptography packages.
   Missing one — shows a window with the `pip install` command. A crash during startup is written to
   `app/data/logs/startup-error.txt` and shown in a window.
2. **`main()`**: creates the data folders, turns on logging (`data/logs/app.log`).
3. If the program is already running (answers `/api/ping`) — it just opens another window and exits.
   Otherwise it takes its own temp folder on drive D (`core.own_temp()`, [below](#temporary-files-and-drive-c)).
4. Imports every module with routes (`archive`, `creator`, `drops`, `etsy`, `gelato`, `images`, `library`,
   `mockups`, `orders`, `printify`, `profit`, `sendlog`, `settings_api`, `textcheck`, `tunnel`, `workshop`) —
   the import itself registers the routes. (`workshop` is a package, its routes in `workshop/routes.py`; its generation
   mode starts its Downloads watcher and the F8 thread the first time it's asked for.)
5. Cleanup: old Gelato temp folders (`cleanup_stale()`), dropped files from the previous session
   (`drops.clear_drops()`), the mockups' unpacked demo book (`mockups.clear_books()`). (The one-time cleanings —
   the old Order Creator form, what the separate «Мокапи» left in `data/mockups` — did their work on the owner's PC
   and were removed on 2026-09-27.)
6. **Server** on port 47821 (`DEFAULT_PORT`). Port taken → a random free port and a warning in Etsy
   Settings (the OAuth return address contains the port).
7. **One automatic order sync** — `startup_sync()` (after that, only by button, see the
   [rule](../rules/sync-policy.md)). In parallel, in the background — an
   [order archive](../features/archive.md) check (`archive.refresh_quietly()`: books whose 14 days are
   up get deleted); it also runs again after every sync. Also in the background — preview cache cleanup
   (`images.prune_cache_quietly()`: unneeded after 21 days) and the mockup runs Photoshop no longer needs
   (`mockups.clean_runs()`). Two minutes later — a [backup](../features/backup.md) to Google Drive when the last
   one is 3 days old (`backup.schedule()`).
8. **Window**: Edge or Chrome with `--app=<address>`, its own profile `data/window-profile`, sized
   1480×940. Neither Edge nor Chrome present — opens the regular browser.

## How the program knows the window is closed

- The page sends `/api/app/heartbeat` every 20 s, and `sendBeacon` to `/api/app/bye` when it closes.
- The loop in `main()` considers the window closed when:
  - there was a "bye" and no new heartbeat arrived within 6 s (a page reload isn't a close);
  - the window process ended and there was no heartbeat for 12 s;
  - the fallback browser with no process stays silent for 10 minutes.
- The loop itself is `run_until_closed(proc, busy)`; `busy()` says what must finish first.
- Before exiting, it waits for background jobs to finish (`jobs.any_running()` — a mockup run still copying or
  watching Photoshop too, a backup being packed; not the text check — it only reads) and for Gelato's temporary links
  (`tunnel.registry.active()`), then closes the links and the server, lets the mockups' demo book and the runs
  Photoshop can no longer have open go (`mockups.clear_books()`, `mockups.clean_runs()`) and empties its temp
  folder (`core.clear_own_temp()`). If the program is killed or crashes, `cloudflared.exe` disappears along with it too (a
  Windows job object, `tunnel._ends_with_us()`).
- The Windows "Choose a folder" / "Choose a page" dialogs run as a separate Python process with Tk (one
  shared script for both, `_dialog()`), because Tk wants its own main thread.

## «Мокапи» — a page of Book Studio

The [mockups](../features/mockups.md) are a page of Book Studio, not a program of their own; their data lives in
`app/data/mockups` (places, runs).

## Temporary files and drive C

The owner keeps drive C clean (2026-09-23: "any temporary file must go when the work is done"). Windows'
own temp folder is on C, and the programs Book Studio starts write there — the Edge window left its logs
and empty folders in `%TEMP%`. So after the single-instance check each program sets `TEMP`/`TMP` (and
Python's `tempfile`) to **`<data folder>\tmp\system`** on D (`core.own_temp()`): everything it starts
from then on — the Edge window, the Windows dialogs (their Python runs with `-B`, no `.pyc`), cloudflared —
inherits it. The folder is emptied on launch and when the program closes (`core.clear_own_temp()`; a file
still held stays till the next launch). A Photoshop started by the Mockups gets `data\tmp\photoshop`,
emptied only once Photoshop is closed. The tests and the preview servers write to `.tmp\` in the
repository ([testing](../dev/testing.md), [preview](../dev/preview.md)). What «Мокапи» leaves and when it
goes — [features/mockups.md](../features/mockups.md#temporary-files).

## Windowless mode (development)

`main(["--no-window", "--port", "47890"])` — server only; this is how
[app/tools/dev_server.py](../../app/tools/dev_server.py) runs ([dev/preview.md](../dev/preview.md)).

## Shortcuts

[make_shortcut.py](../../app/tools/make_shortcut.py) creates `Book Studio.lnk` on the real desktop (it asks
Windows for the path): `pythonw.exe "…\app\Book Studio.pyw"`, working folder `app`, the icon
`app/web/img/icon.ico` (`SHORTCUTS`; «Мокапи.lnk» until 2026-09-24). After moving the program, the shortcut
has to be recreated. Windows' shortcut maker (WScript) keeps only the ANSI code page — Cyrillic in a path or
tooltip turns into "?????" (checked 2026-09-23): so the scripts have Latin names, the tooltips are Latin, and a
Cyrillic shortcut name is saved under a Latin one and then renamed.

## Where in the code

- [app/Book Studio.pyw](<../../app/Book Studio.pyw>) — `_message()`
- [app/studio/main.py](../../app/studio/main.py) — `main()`, `_running_instance()`, `run_until_closed()`
- [app/studio/core.py](../../app/studio/core.py) — `own_temp()`, `clear_own_temp()`
- [app/studio/mockups.py](../../app/studio/mockups.py) — `clear_books()`, `clean_runs()`
- [app/studio/desktop.py](../../app/studio/desktop.py) — `open_app_window()`, `find_browser()`, `pick_folder()`, `pick_file()`, `_dialog()`
- [app/studio/server.py](../../app/studio/server.py) — `start()`, `_heartbeat()`, `_bye()`, `_State`
- [app/studio/tunnel.py](../../app/studio/tunnel.py) — `cleanup_stale()`, `_ends_with_us()`
- [app/studio/drops.py](../../app/studio/drops.py) — `clear_drops()`
- [app/studio/sync.py](../../app/studio/sync.py) — `startup_sync()`
- [app/studio/archive.py](../../app/studio/archive.py) — `refresh_quietly()`
- [app/studio/backup.py](../../app/studio/backup.py) — `schedule()`, `start_if_due()`
- [app/studio/images.py](../../app/studio/images.py) — `prune_cache_quietly()`, `prune_cache()`
- [app/web/js/app.js](../../app/web/js/app.js) — `heartbeat()`, `boot()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `markOffline()`
- [app/tools/make_shortcut.py](../../app/tools/make_shortcut.py) — `main()`, `SHORTCUTS`

## Related

- [Server](server.md) · [Interface](frontend.md) · [Setup](../dev/setup.md)
