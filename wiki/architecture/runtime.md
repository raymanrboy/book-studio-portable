---
title: Launch and shutdown
type: architecture
updated: 2026-09-23
code:
  - app/Book Studio.pyw
  - app/Запуск з консоллю.bat
  - app/studio/main.py
  - app/studio/desktop.py
  - app/tools/make_shortcut.py
  - app/studio/mockups_app.py
  - app/Mockups.pyw
---
# Launch and shutdown

> Desktop shortcut → `app/Book Studio.pyw` → a server on `127.0.0.1:47821` → a separate Edge window.
> When the window is closed, the program waits for background work and shuts itself down.

## Launch sequence

1. **`Book Studio.pyw`** (no console, `pythonw.exe`): checks the Pillow, img2pdf, cryptography packages.
   Missing one — shows a window with the `pip install` command. A crash during startup is written to
   `app/data/logs/startup-error.txt` and shown in a window.
2. **`main()`**: creates the data folders, turns on logging (`data/logs/app.log`).
3. If the program is already running (answers `/api/ping`) — it just opens another window and exits.
   Otherwise it takes its own temp folder on drive D (`core.own_temp()`, [below](#temporary-files-and-drive-c)).
4. Imports every module with routes (`archive`, `creator`, `drops`, `etsy`, `gelato`, `library`, `orders`,
   `printify`, `profit`, `sendlog`, `settings_api`, `textcheck`, `tunnel`) — the import itself registers
   the routes. (`mockups` is not among them: it belongs to the second program, below.)
5. Cleanup: old Gelato temp folders (`cleanup_stale()`), leftovers from the old Order Creator form
   (`forget_old_form()`), dropped files from the previous session (`drops.clear_drops()`).
6. **Server** on port 47821 (`DEFAULT_PORT`). Port taken → a random free port and a warning in Etsy
   Settings (the OAuth return address contains the port).
7. **One automatic order sync** — `startup_sync()` (after that, only by button, see the
   [rule](../rules/sync-policy.md)). In parallel, in the background — an
   [order archive](../features/archive.md) check (`archive.refresh_quietly()`: books whose 14 days are
   up get deleted); it also runs again after every sync. Also in the background — preview cache cleanup
   (`images.prune_cache_quietly()`: unneeded after 21 days).
8. **Window**: Edge or Chrome with `--app=<address>`, its own profile `data/window-profile`, sized
   1480×940. Neither Edge nor Chrome present — opens the regular browser.

## How the program knows the window is closed

- The page sends `/api/app/heartbeat` every 20 s, and `sendBeacon` to `/api/app/bye` when it closes.
- The loop in `main()` considers the window closed when:
  - there was a "bye" and no new heartbeat arrived within 6 s (a page reload isn't a close);
  - the window process ended and there was no heartbeat for 12 s;
  - the fallback browser with no process stays silent for 10 minutes.
- The loop itself is `run_until_closed(proc, busy)` — shared with the mockups utility (below); `busy()`
  says what must finish first.
- Before exiting, it waits for background jobs to finish (`jobs.any_running()`; not the text check — it
  only reads) and for Gelato's temporary links (`tunnel.registry.active()`), then closes the links and
  the server and empties its temp folder (`core.clear_own_temp()`). If the program is killed or crashes, `cloudflared.exe` disappears along with it too (a
  Windows job object, `tunnel._ends_with_us()`).
- The Windows "Choose a folder" / "Choose a page" dialogs run as a separate Python process with Tk (one
  shared script for both, `_dialog()`), because Tk wants its own main thread.

## The second program: «Мокапи» (since 2026-09-23)

The [listing-mockups utility](../features/mockups.md) starts the same way, but on its own:
`app/Mockups.pyw` sets the data folder `app/data/mockups` **before anything loads**, then
`mockups_app.main()` — port **47831**, its own window (`mockups.html`), only the mockups, the dropped
files and the lifecycle routes (no keys, orders, library, sync, archive). `/api/ping` answers
"Book Studio · Мокапи", so a second double-click only opens another window. Started with Book Studio's
own data folder, it refuses to run (it would wipe Book Studio's dropped files). It waits for a run that
is still copying or watching Photoshop before it exits; then the unpacked demo book goes, and so do the
runs Photoshop can no longer have open (`clean_runs()`). Both programs can run side by side.

## Temporary files and drive C

The owner keeps drive C clean (2026-09-23: "any temporary file must go when the work is done"). Windows'
own temp folder is on C, and the programs Book Studio starts write there — the Edge window left its logs
and empty folders in `%TEMP%`. So after the single-instance check each program sets `TEMP`/`TMP` (and
Python's `tempfile`) to **`<data folder>\tmp\system`** on D (`core.own_temp()`): everything it starts
from then on — the Edge window, the Windows dialogs (their Python runs with `-B`, no `.pyc`), cloudflared —
inherits it. The folder is emptied on launch and when the program closes (`core.clear_own_temp()`; a file
still held stays till the next launch). A Photoshop started by «Мокапи» gets `data\mockups\tmp\photoshop`,
emptied only once Photoshop is closed. The tests and the preview servers write to `.tmp\` in the
repository ([testing](../dev/testing.md), [preview](../dev/preview.md)). What «Мокапи» leaves and when it
goes — [features/mockups.md](../features/mockups.md#temporary-files--what-is-left-and-when-it-goes).

## Windowless mode (development)

`main(["--no-window", "--port", "47890"])` — server only; this is how
[app/tools/dev_server.py](../../app/tools/dev_server.py) runs ([dev/preview.md](../dev/preview.md)); the
mockups utility the same way on port 47891 (`dev_server.py --mockups`).

## Shortcuts

[make_shortcut.py](../../app/tools/make_shortcut.py) creates `Book Studio.lnk` and `Мокапи.lnk` on the real
desktop (it asks Windows for the path): `pythonw.exe "…\app\Book Studio.pyw"` / `"…\app\Mockups.pyw"`,
working folder `app`, icons `app/web/img/icon.ico` / `mockups.ico` (`SHORTCUTS`). After moving the
program, the shortcuts have to be recreated. Windows' shortcut maker (WScript) keeps only the ANSI code
page — Cyrillic in a path or tooltip turns into "?????" (checked 2026-09-23): so the scripts have Latin
names, the tooltips are Latin, and «Мокапи.lnk» is saved under a Latin name and then renamed.

## Where in the code

- [app/Book Studio.pyw](<../../app/Book Studio.pyw>) — `_message()`
- [app/studio/main.py](../../app/studio/main.py) — `main()`, `_running_instance()`, `run_until_closed()`
- [app/studio/core.py](../../app/studio/core.py) — `own_temp()`, `clear_own_temp()`
- [app/studio/mockups_app.py](../../app/studio/mockups_app.py) — `main()`, `APP`, `PORT`
- [app/Mockups.pyw](<../../app/Mockups.pyw>) — the data folder `app/data/mockups`, `_message()`
- [app/studio/desktop.py](../../app/studio/desktop.py) — `open_app_window()`, `find_browser()`, `pick_folder()`, `pick_file()`, `_dialog()`
- [app/studio/server.py](../../app/studio/server.py) — `start()`, `_heartbeat()`, `_bye()`, `_State`
- [app/studio/tunnel.py](../../app/studio/tunnel.py) — `cleanup_stale()`, `_ends_with_us()`
- [app/studio/creator.py](../../app/studio/creator.py) — `forget_old_form()`
- [app/studio/drops.py](../../app/studio/drops.py) — `clear_drops()`
- [app/studio/profit.py](../../app/studio/profit.py) — `startup_sync()`
- [app/studio/archive.py](../../app/studio/archive.py) — `refresh_quietly()`
- [app/studio/images.py](../../app/studio/images.py) — `prune_cache_quietly()`, `prune_cache()`
- [app/web/js/app.js](../../app/web/js/app.js) — `heartbeat()`, `boot()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `markOffline()`
- [app/tools/make_shortcut.py](../../app/tools/make_shortcut.py) — `main()`, `SHORTCUTS`

## Related

- [Server](server.md) · [Interface](frontend.md) · [Setup](../dev/setup.md)
