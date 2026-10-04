---
title: Interface preview during development
type: dev
updated: 2026-10-04
code:
  - app/tools/dev_server.py
  - app/tools/sample_data.py
  - app/tools/sample_mockups.py
  - app/tools/sample_books.py
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

## The Workshop and the Mockups

- The same `--sample` server has them (the separate `--mockups` server on port 47891 went with the utility).
- **The Workshop** (since 2026-09-26 — the book console moved in): the preview is its **sandbox** (`core.SANDBOX`):
  three made-up books in `.tmp\bsdev\workshop-books` (`seed_workshop()` → [tools/sample_books.py](../../app/tools/sample_books.py)
  `make_books()`, only when there are none): **40** — Tier H, the hero, story, text, no prompts yet, a hero variant
  G2_brunette, four looks with a made-up `hero.png` (G3_blond, G4_east_asian, G5_redhead, G6_afro — the listing
  slide 7's frames), and made-up photo-mockup references in its `mockups\` (Cover 1, Cover & Open 1, the Canva cover); **41** —
  Tier S, every prompt (the book check says 14 errors), 5 rows of pictures, Canva ticked, no references (the photo
  step's missing states); **42** — just started. The [photo mockups](../features/photo-mockups.md)' made-up templates —
  a coloured scene with a white book, per category — in `.tmp\bsdev\photo-mockups` (`make_photo_templates()`, only
  when empty). **A picture put into `.tmp\bsdev\downloads`** is caught by a waiting row, as a download would be; what
  would go into the clipboard lands in `.tmp\bsdev\clipboard\`; F8 isn't taken; no window opens (Antigravity,
  Explorer, «Зберегти як» → `saved\`); a deleted book goes to `recycle-bin\`. To have the books back as they were,
  delete `.tmp\bsdev\workshop-books`.
- **The Mockups** (`seed_mockups()`, in `.tmp\bsdev\sample-mockups`): made-up templates (small pictures of a
  table with an open book, saved under the owner's `.psd` names — Pillow reads them by content, so the template
  previews show), a made-up Canva export `Goose demo.zip` (a wide cover, 24 numbered pages), a **pretend
  Photoshop** (`pretend_photoshop()`: after 2.5 s "the owner said Yes", then it reports progress into the status
  file like the real script and saves each picture as the template's scene with the pages laid on it; for
  «Зберегти відкриті» (`finish.jsx`) it "saves and closes" the templates it was given), and **no Windows dialog,
  flash or sound for the mockups** — the book field's button answers with `Goose demo.zip`, "where to save" with
  `sample-mockups\out`, `attention()` does nothing (only the mockups' own `desktop` is swapped: the rest of the
  program keeps its dialogs).
- **The listing slides** (since 2026-09-29): the slides' cut-out gets a pretend template (`pretend_template()` — the
  book is where the pretend Photoshop lays the pages, a soft shadow down-right), so a run fills «Без фону», and
  «Зробити слайди» bakes the six with the real headless Edge into `sample-mockups\out`. The editor's live pick-up of an
  agent's change waits while the page is hidden — the hidden pane says `document.visibilityState === 'hidden'`: set it
  to `visible` with `Object.defineProperty` to see it.
- Files for a Workshop frame or the demo book: draw PNGs with `canvas` in `javascript_tool` and dispatch
  `DragEvent('dragover')` + `DragEvent('drop')` with one `DataTransfer` on `.ws-ph` (a frame) or `.mk` (the
  demo book). Then click `.mk-spread` tiles and `[data-act="make"]`, then `[data-act="finish"]`.
- A mode switch or a dialog opening is caught mid-animation by a screenshot of the hidden pane: for clean
  pictures set `document.documentElement.dataset.motion = 'reduce'` (and `.theme` for the other theme) — only
  in the preview window.
- The real Photoshop is checked only by hand, on copies, with a made-up book — see
  [features/mockups.md](../features/mockups.md#where-things-are) (what is not checked live).

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

- [app/tools/dev_server.py](../../app/tools/dev_server.py) — `main()` (`BOOK_STUDIO_SAMPLE`), `claim()`, `MARK`, `PORT` (split by job on 2026-09-27: the made-up data is in the two files below)
- [app/tools/sample_data.py](../../app/tools/sample_data.py) — `seed()`, `_receipt()`, `_book_bought()`, `_printify()`, `_gelato()`, `_seed_archive()`, `_sample_book()`, `_printed()`, `SAMPLE_TEXTS`, `SLIPS`
- [app/tools/sample_mockups.py](../../app/tools/sample_mockups.py) — `seed_mockups()`, `pretend_photoshop()`
- [app/tools/sample_books.py](../../app/tools/sample_books.py) — `make_books()`, `hero_png()`, `make_photo_templates()`, `book_shot()`, `seed_workshop()`
- [app/studio/main.py](../../app/studio/main.py) — `main()` (`--no-window` mode)

## Related

- [Tests](testing.md) · [Security](../security.md) · [Setup](setup.md)

## In the portable copy (2026-10-04)

`.claude/launch.json` here starts the portable copy's own Python (`../runtime/python/python.exe`). Open the session **in this folder**: a session opened in the ordinary Book Studio folder starts *that* program's preview — its pages differ and nothing here is proven by them (found the hard way). `/api/ping` answers a `data` id: the preview of this copy is the one whose id matches `core.data_id()`.
