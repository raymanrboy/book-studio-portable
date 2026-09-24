---
title: Interface preview during development
type: dev
updated: 2026-09-24
code:
  - app/tools/dev_server.py
---
# Interface preview

> Check interface changes on a separate server with temporary data (port 47890), never on the owner's
> real program.

## Launch

- **Claude Code (built-in browser)**: the `book-studio-dev` configuration in `.claude/launch.json` →
  `preview_start("book-studio-dev")`. It runs `python -B app/tools/dev_server.py --sample`.
- By hand: `python app/tools/dev_server.py --sample` → http://127.0.0.1:47890/
- `--sample` puts made-up orders, one library book (listing `4100000900`, no illustrations), one
  [Workshop](../features/workshop.md) book and the mockups' made-up templates (below) into
  `.tmp\bsdev` in the repository — on drive D (until 2026-09-23 `%TEMP%\bsdev` on drive C, which the owner
  keeps clean; the program started there also keeps its temp files inside that folder). The orders cover every queue tab: new (US Hardcover), in progress (Printify
  `in-production` and `has-issues`, a Gelato draft), the "printer shipped" tab (Printify `fulfilled`
  with USPS, Gelato `in_transit` with a tracking number), shipped on Etsy (with a tracking number).
  Order `4100000108` (Robin Sample) is **for two books** (Sofia and Jack, US Softcover → Gelato): for
  checking per-book work in the card and a shared draft (`_receipt(..., also=("Jack",))`). The print
  orders are made up (`_printify()`, `_gelato()`) and written straight into the snapshot — no service is
  ever called.
- [Order archive](../features/archive.md) (`_seed_archive()`, only when the archive is empty): four
  books with drawn, numbered pages (`_sample_book()`) — Liam (Printify, shipped 3 days ago → "11 days
  left"), Noah (Gelato, 28 pages, waiting for the mark on Etsy), Ava ("Keep"), and a reprint of Liam. The
  fifth is Olivia: a Gelato draft that never became an order — it's not in the archive, and in "New"
  Olivia has a "Draft" chip and a "Take files from an earlier send" button in the card. Olivia's book
  has verse (`SAMPLE_TEXTS`, `_printed()`): text on one page of every spread, like real books, with two
  planted mistakes (`SLIPS`: "Olivai", a forgotten `{NAME}`); the made-up book's passport has the same
  texts — so the **text check** on Olivia's card finds exactly 2 errors. It talks to the real Ollama on
  this PC (locally, on made-up pages); without Ollama — a yellow banner. To have the archive redrawn
  after changes to `dev_server.py`, delete `.tmp\bsdev`.
- **The server only writes made-up data to its own folder** (`claim()`, since 2026-09-22). It accepts
  its default `.tmp\bsdev`, an empty folder, and any folder already marked `.book-studio-sample`. It refuses: the
  real `app/data`, any folder with `vault.json` (keys live there), and a non-empty folder that isn't its
  own — because `BOOK_STUDIO_DATA` could point at a copy, a backup, or a moved data folder, and
  `--sample` overwrites the order snapshot. Before 2026-09-22 it only checked one exact path (found by
  the audit). There are no keys in the temp folder, so the startup sync never starts and no service is
  ever called.
- **No keys will ever be here either** (since 2026-09-23): the server sets `BOOK_STUDIO_SAMPLE=1`, and
  the program doesn't show keys from the old programs on the desktop and won't save any ("This is a
  preview server on made-up data — keys aren't stored here"). If the folder somehow has a `vault.json`
  anyway, the server refuses to start and asks to delete the folder by hand.
- Among the made-up orders is **receipt `4100000107` with two print orders** (Printify + Gelato): this
  shows the "+N more in print" chip, and how the cost of a receipt split between printers is calculated
  ([reconciliation.md](../rules/reconciliation.md)).

## The Listings mode: the Workshop and the Mockups (since 2026-09-24)

- The same `--sample` server has them (the separate `--mockups` server on port 47891 went with the utility).
- **The Workshop**: one made-up book, «Silly Goose (Workshop sample)» (`seed_workshop()`, `WORKSHOP_BOOK`, only
  when it isn't there yet): every prompt and text but one of each (spread 9's prompt, page 30's text), pictures
  in four frames — the cover and spreads 2–3, 4–5 at 2:1, and spread 8–9 at 1792×1024 to show the amber «не
  2:1» mark. Passed to the library in a check, it stays there: delete `.tmp\bsdev` to have it back.
- **The Mockups** (`seed_mockups()`, in `.tmp\bsdev\sample-mockups`): made-up templates (small pictures of a
  table with an open book, saved under the owner's `.psd` names — Pillow reads them by content, so the template
  previews show), a made-up Canva export `Goose demo.zip` (a wide cover, 24 numbered pages), a **pretend
  Photoshop** (`pretend_photoshop()`: after 2.5 s "the owner said Yes", then it reports progress into the status
  file like the real script and saves each picture as the template's scene with the pages laid on it; for
  «Зберегти відкриті» (`finish.jsx`) it "saves and closes" the templates it was given), and **no Windows dialog,
  flash or sound for the mockups** — the book field's button answers with `Goose demo.zip`, "where to save" with
  `sample-mockups\out`, `attention()` does nothing (only the mockups' own `desktop` is swapped: the rest of the
  program keeps its dialogs).
- Files for a Workshop frame or the demo book: draw PNGs with `canvas` in `javascript_tool` and dispatch
  `DragEvent('dragover')` + `DragEvent('drop')` with one `DataTransfer` on `.ws-ph` (a frame) or `.mk` (the
  demo book). Then click `.mk-spread` tiles and `[data-act="make"]`, then `[data-act="finish"]`.
- A mode switch or a dialog opening is caught mid-animation by a screenshot of the hidden pane: for clean
  pictures set `document.documentElement.dataset.motion = 'reduce'` (and `.theme` for the other theme) — only
  in the preview window.
- The real Photoshop is checked only by hand, on copies, with a made-up book — see
  [features/mockups.md](../features/mockups.md#what-was-checked).

## Pitfalls of the built-in browser

- The browser pane is often **hidden** — then `requestAnimationFrame` doesn't fire, View Transitions
  are skipped, and screenshots lag. For checks through `javascript_tool`, swap it out:
  `requestAnimationFrame = (cb) => setTimeout(() => cb(performance.now()), 16)` — and check the DOM
  (sizes, classes, `scrollLeft`), not the picture.
- Sometimes a hidden pane **counts as visible** (`document.hidden === false`, e.g. after
  `resize_window`) but never draws a frame: then a page transition (View Transition) waits for a frame,
  and the page "lags one behind" — showing the previous address until the next transition starts. This
  is only the pane, not the program; for checks, open the page with a direct navigation, or turn off
  transitions: `document.startViewTransition = undefined`.
- For checking layout — `resize_window` 1440×900; after checking, **always** set it back to
  `preset: "desktop"`.
- Files for the order card can be generated on the page via `canvas` and passed in as a drop, or a PNG
  can be placed in a temp folder and its path picked.
- When done — `preview_stop`; the folders in `.tmp\` (drive D, not in git) can be left or deleted.
- Tell the owner honestly what was checked with faked frames and what wasn't (only he sees the real
  smoothness).

## After server-side changes

Changed `app/studio/*.py` files only take effect in the owner's program after it's restarted — tell him
so. Changes to `app/web/*` are picked up by reloading the window (Ctrl+R).

## Where in the code

- [app/tools/dev_server.py](../../app/tools/dev_server.py) — `main()` (`BOOK_STUDIO_SAMPLE`), `claim()`, `MARK`, `seed_workshop()`, `WORKSHOP_BOOK`, `WORKSHOP_PROMPTS`, `seed_mockups()`, `pretend_photoshop()`, `seed()`, `_receipt()`, `_book_bought()`, `_printify()`, `_gelato()`, `_seed_archive()`, `_sample_book()`, `_printed()`, `SAMPLE_TEXTS`, `SLIPS`, `PORT`
- [app/studio/main.py](../../app/studio/main.py) — `main()` (`--no-window` mode)

## Related

- [Tests](testing.md) · [Security](../security.md) · [Setup](setup.md)
