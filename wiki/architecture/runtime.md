---
title: Launch and shutdown
type: architecture
updated: 2026-11-12
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

1. `Book Studio.pyw` (`pythonw.exe`, no console) checks that Pillow, img2pdf, pikepdf and cryptography are installed (found, not imported). A missing one shows a window with the `pip install` command; a crash during startup goes to `data/logs/startup-error.txt` and is shown in a window.
2. `main()` creates the data folders and turns on logging.
3. One copy per data folder: a named mutex `Local\BookStudio-<data id>` is asked first (`_another_copy_starting()`); `/api/ping` only when the lock is held. If a copy runs on the same data, the new start only opens another window and exits. A copy that waits releases the lock (`_release_lock()`) and waits up to 30 s for the other one's ping; if nobody answers and the lock is free, it starts itself. Otherwise it sets its own temp folder ([below](#temp-folder)).
4. Every module with routes is imported in `main()`; the import registers the routes.
5. Cleanup: stale Gelato temp folders (`tunnel.cleanup_stale()`), dropped files (`drops.clear_drops()`), the Mockups' unpacked demo book (`mockups.clear_books()`), the slides' cut-out cache and bake browser files (`slides.store.clean_temporary()`); what still waited on the «Скасувати» shelf goes to the Recycle Bin (`aside.flush(0)`).
6. Server on `DEFAULT_PORT` 47821; if taken, a random free port and a warning in Etsy settings (the OAuth return address contains the port).
7. Background work started here:
   - `sync.startup_sync()` — the one automatic order sync at launch (then hourly, see [sync policy](../rules/sync-policy.md));
   - `archive.refresh_quietly()` — [archive](../features/archive.md) clean-up (also after every sync);
   - `images.prune_cache_quietly()` and `mockups.clean_runs()` — cache and Photoshop-run clean-up;
   - `textcheck.run.start_quietly()` — hidden Ollama without a model, never on made-up data ([text check](../features/text-check.md));
   - `backup.schedule()` — a [backup](../features/backup.md) when the last one is 3 days old, checked on launch and every 6 hours.
8. Window: Edge (else Chrome) `--app=<address>`, profile `data/window-profile`, size 1480×940, started with component updates and background networking off (`desktop.QUIET_EDGE`) and with the occlusion/timer throttles off so a covered window keeps sending its heartbeat. Edge's own cache inside the profiles is trimmed while no window holds the profile (`desktop.trim_profile()`; same for `work-browser`). With neither browser present the regular browser opens.

## Closing

- The page sends `/api/app/heartbeat` every 20 s and `sendBeacon` to `/api/app/bye` on close.
- `run_until_closed(proc, busy)` treats the window as closed when:
  - a "bye" arrived, no heartbeat followed within 6 s and Edge has no window of ours (a reload or a frozen page is not a close);
  - Edge has no window of ours (our process ended and `window-profile/lockfile` is free, `_profile_open()`) and there was no heartbeat for `GRACE` (12 s; `SILENCE` 90 s if no window was ever seen);
  - Edge holds the profile but nothing pinged for `LOST` (30 min);
  - the fallback browser (no process to watch) is silent for 10 minutes.
- Before exiting it waits for `jobs.any_running()` (mockup runs, a backup being packed; not the text check, which only reads) and for Gelato's temporary links (`tunnel.registry.active()`), then closes the links and the server, clears the demo book, Photoshop runs and the slides' temporary files, and empties its temp folder. If the program is killed, `cloudflared.exe` ends with it (a Windows job object, `tunnel._ends_with_us()`).
- The Windows "choose folder / file" dialogs run as a separate Python process with Tk (`desktop._dialog()`), because Tk needs its own main thread.
- The log says why the window counted as closed (`Window closed: …`), notes ping gaps over a minute (`Window: no ping for …`) and page errors (`Page error: …`, `/api/app/log`). The server logs requests slower than 1 s as «Slow request».

## Temp folder

Drive C stays clean: after the single-instance check the program sets `TEMP`/`TMP` (and Python's `tempfile`) to `<data folder>\tmp\system` (`core.own_temp()`), so everything it starts — the Edge window, the dialogs (Python with `-B`), cloudflared — writes there. The folder is emptied on launch and on close (`core.clear_own_temp()`); a file still held stays until the next launch. Photoshop started by the Mockups gets `data/tmp/photoshop`, emptied once Photoshop is closed ([Mockups temp files](../features/mockups-engine.md#temporary-files)). Tests and preview servers write to `.tmp\` in the repository ([testing](../dev/testing.md), [preview](../dev/preview.md)).

## Logs

`data/logs/app.log`, `printify.log`, `gelato.log` — one file a day, the last 7 kept (`core.log_file()`, `LOG_DAYS`); older leftovers go at start (`core.prune_logs()`). `setup_logging()` only makes the `logs` folder. The send and text-check journals (`logs/sends`, `logs/checks`) are records, not logs, and are never cleaned this way ([data](data.md)).

## Windowless mode

`main(["--no-window", "--port", "47890"])` runs the server only; this is how [app/tools/dev_server.py](../../app/tools/dev_server.py) works ([preview](../dev/preview.md)).

## Shortcuts

[make_shortcut.py](../../app/tools/make_shortcut.py) creates `Book Studio.lnk` on the real desktop: `pythonw.exe "…\app\Book Studio.pyw"`, working folder `app`, icon `app/web/img/icon.ico` (`SHORTCUTS`). After moving the program the shortcut is recreated.

## Why
- Edge stays the window (same engine as Chrome; no WebView2/Qt/Electron gain).
- A waiting second copy must release the one-copy lock, else every later start waits.
- Window-closed detection uses the Edge profile lockfile plus a 30-minute silence, not pings alone: pings are unreliable when the window is covered.
- Windows' shortcut maker keeps only the ANSI code page: scripts and tooltips have Latin names, a Cyrillic shortcut name is set by renaming afterwards.
- Frame-rate flags are deliberately not passed to Edge.

## Where in the code
- [app/Book Studio.pyw](<../../app/Book Studio.pyw>) — `_message()`
- [app/studio/main.py](../../app/studio/main.py) — `main()`, `_another_copy_starting()`, `_release_lock()`, `run_until_closed()`, `SILENCE`, `GRACE`, `LOST`
- [app/studio/core.py](../../app/studio/core.py) — `own_temp()`, `clear_own_temp()`, `log_file()`, `prune_logs()`, `LOG_DAYS`, `DEFAULT_PORT`
- [app/studio/desktop.py](../../app/studio/desktop.py) — `open_app_window()`, `find_browser()`, `trim_profile()`, `QUIET_EDGE`, `_dialog()`
- [app/studio/tunnel.py](../../app/studio/tunnel.py) — `cleanup_stale()`, `_ends_with_us()`
- [app/web/js/app.js](../../app/web/js/app.js) — `heartbeat()`, `boot()`

## Related
- [Server](server.md) · [Data](data.md) · [Frontend](frontend.md) · [Portable copy](../dev/portable.md)
