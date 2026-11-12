---
title: Interface preview
type: dev
updated: 2026-11-12
code:
  - app/tools/dev_server.py
  - app/tools/sample_data.py
  - app/tools/sample_mockups.py
  - app/tools/sample_books.py
---
# Interface preview

> Check interface changes on a separate server with made-up data (port 47890), never on the owner's real program. `core.SANDBOX` (`BOOK_STUDIO_SAMPLE` or `BOOK_STUDIO_SANDBOX`) makes the Workshop, the clipboard, Downloads and the Recycle Bin fake; the real Photoshop is never started.

## Launch
- Claude Code: `preview_start("book-studio-dev")` (`.claude/launch.json`; it runs `python -B app/tools/dev_server.py --sample` with the copy's own `../runtime/python/python.exe`). By hand: `python app/tools/dev_server.py --sample` → `http://127.0.0.1:47890/`; another port with `BOOK_STUDIO_DEV_PORT` (the robot in [testing](testing.md) uses it).
- Open the session **in this folder**: a session opened in the ordinary Book Studio folder starts that program's preview, whose pages differ. `/api/ping` answers a `data` id; this copy's preview is the one whose id matches `core.data_id()`.
- `--sample` writes made-up data into `.tmp\bsdev` in the repository (drive D): orders for every queue tab, a receipt for two books, a receipt with two print orders, an order archive with a book that never became an order, library and Workshop books (three, in the sandbox), the Mockups' made-up templates, a made-up Canva export and photo-mockup templates. What each seed holds is in the docstrings of `sample_data.py` (`seed()`, `_seed_archive()`), `sample_books.py` (`make_books()`, `seed_workshop()`) and `sample_mockups.py` (`seed_mockups()`). Print orders are written straight into the snapshot: no service is ever called.
- To redraw a seed after changing the tool, delete `.tmp\bsdev` (or just `workshop-books`).

## What stays fake
- **Only its own folder is written** (`claim()`; [data safety](../architecture/data-safety.md)): the default `.tmp\bsdev`, an empty folder, or a folder already marked `.book-studio-sample` (`MARK`). It refuses the real `app/data`, any folder with `vault.json`, and a non-empty folder that is not its own, because `BOOK_STUDIO_DATA` can point at a copy or a backup and `--sample` overwrites the order snapshot.
- **No keys:** the server sets `BOOK_STUDIO_SAMPLE=1`; the program shows and saves no keys, the startup sync never starts, and a `vault.json` in the folder stops the server.
- **No Ollama:** fake data never starts it (a UI test once did); the text check on a sample order talks to an Ollama already running on the PC, otherwise a yellow banner shows.
- **The Workshop** in the sandbox: a picture put into `.tmp\bsdev\downloads` is caught by a waiting row as a download would be; the clipboard lands in `.tmp\bsdev\clipboard\`; no window opens («Зберегти як» → `saved\`); a deleted book goes to `recycle-bin\`.
- **Mockups and slides:** a pretend Photoshop (`pretend_photoshop()`: reports progress into the status file like the real script) and drawn runs (`pretend_render()`); no Windows dialog, flash or sound. The slides bake with the real headless Edge into `sample-mockups\out`. The real Photoshop is checked only by hand, on copies, with a made-up book ([mockups-engine](../features/mockups-engine.md#photoshop-fallback)).

## Never wrap the sample server
`studio.core` fixes the data folder the first time anything imports it. A script that imports `studio` before `BOOK_STUDIO_DATA` is set (a wrapper around `dev_server.py`, a patch for a look) makes the seed write into the **real** data; this once overwrote the profit files. Start `tools/dev_server.py` directly. To look at a pretend state, set `BOOK_STUDIO_DATA` (a made-up folder) and `BOOK_STUDIO_SAMPLE=1` first, import `studio` after, then patch. `sample_data.seed()` refuses when core points elsewhere.

## Pitfalls of the built-in browser
- A hidden pane does not fire `requestAnimationFrame`, skips View Transitions and lags screenshots: check the DOM (sizes, classes, `scrollLeft`), and swap `requestAnimationFrame = (cb) => setTimeout(() => cb(performance.now()), 16)` and `document.startViewTransition = undefined` when needed. For clean screenshots set `document.documentElement.dataset.motion = 'reduce'`.
- Check layout with `resize_window` 1440×900 and the narrower widths, and set the preset back to `desktop` afterwards. Test files for a drop can be drawn on a `canvas` and dispatched as a `drop` on `.ws-ph` (a Workshop frame) or `.mk` (the demo book).
- Finish with `preview_stop`. Say honestly what was checked on faked frames: only the owner sees the real smoothness.

## After changes
`app/studio/*.py` take effect in the owner's program only after it restarts: tell him. `app/web/*` is picked up by reloading the window (Ctrl+R).

## Where in the code
- [app/tools/dev_server.py](../../app/tools/dev_server.py) — `main()`, `claim()`, `MARK`, `PORT`
- [app/tools/sample_data.py](../../app/tools/sample_data.py) — `seed()`, `_seed_archive()`
- [app/tools/sample_mockups.py](../../app/tools/sample_mockups.py) — `seed_mockups()`, `pretend_photoshop()`, `pretend_render()`
- [app/tools/sample_books.py](../../app/tools/sample_books.py) — `make_books()`, `make_photo_templates()`, `seed_workshop()`
- [app/studio/core.py](../../app/studio/core.py) — `SANDBOX`, `SAMPLE`, `data_id()`

## Related
- [Tests](testing.md) · [Security](../security.md) · [Portable copy](portable.md)
