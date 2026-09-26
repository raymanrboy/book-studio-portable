---
title: The book console — the book pipeline and the Workshop as one place (plan)
type: plan
updated: 2026-09-26
code: []
---
# The book console (Пульт книги) — plan

> **Agreed as a plan on 2026-09-25; a prototype apart from Book Studio built and tried on a real book on
> 2026-09-26; moved into Book Studio the same day** (branch `book-console`) — how it works now:
> [the Workshop](../features/workshop.md). The owner: "I'd put it in the roadmap for sure and build it in a separate
> branch — but for now we only plan, and start with a **prototype apart from Book Studio**; we'll see how it works."
> The same path the [Mockups](listing-mockups.md) took. This page keeps the agreements and the history.

## The idea

The owner's `Etsy-Book-Pipeline` (agents 0–6 that write a book's text and prompts) and the
[Workshop](../features/workshop.md) become **one place for a book**: the agents keep working in the chat as
now, and the console **sees what they write** and catches the pictures he downloads. No new program for the
agents, no image API ([decisions](../decisions.md), 2026-09-25).

## How the owner works today (2026-09-25)

- The agents run in **Antigravity** (its rules file — `GEMINI.md`; Antigravity has a CLI `agy`, not installed
  here — he works in the Antigravity app). "I'll figure out any variant."
- **Spreads** — generated in **Gemini**'s website chat, downloaded as **PNG** to Downloads.
- **Listing lifestyle photos** — **ChatGPT**, downloaded as **JPEG**; prompts in the pipeline's `Listing prompts`.
- **The cover** — a Photoshop cover mockup put into the chat as context, plus one of his existing listings as a
  reference, asking to replace the picture.
- **Tier H heroes** — per-book folders `G1_blonde`, `G2_brunette`… with `manual-replacement-prompts/<spread>.json`;
  the hero is swapped per order for now.

## The three parts

1. **The book's path strip** (at the top of a book's page): Formula → Hero (`canonical.png`, its thumbnail) →
   Story → Text → Prompts · GO → Pictures `n/16` (the cover is its own step, 2026-09-26) → Cover → Canva → Mockups → Library. Ticked **by the files that
   exist** in the book's folder; a click shows the step's file. The same progress on the gallery card. An
   **"Open the agent"** button opens Antigravity in that book's folder.
2. **The generation mode** (the main win): "Generate" on a row (or on the whole book) → the row's prompt goes to
   the clipboard, the row shows "waiting for a picture" → the owner pastes into Gemini and downloads → the new
   file in **Downloads** goes into that row, cut and flipped → **the next row's prompt is already in the
   clipboard**. A redo replaces the picture. A "copy the hero" button puts `canonical.png` in the clipboard for a
   new chat. The cover row puts in the clipboard, one after another, the cover mockup, a reference listing, the
   prompt. Listing photos — the same, catching JPEG.
3. **Hero variants** — tabs "Base · G1 · G2 …" on the book's page; the generation mode gives each spread's
   swap prompt; "G2 14/14".

## Related ideas from the same talk (2026-09-25)

Kept in the [roadmap](roadmap.md); they belong to the same road and the console should leave room for them:
- **Upscaling right after a drop** — a spread goes in cut, flipped **and upscaled** ("a top feature"); in the
  generation mode that's the same step: the caught picture comes out print-ready.
- **Tier H orders** — the order card shows the buyer's chosen look and copies a ready hero-swap prompt; **later**,
  with one look per hero, every variant is made once here and an order takes the right set (the owner: making
  every look now is too costly — look, clothing colour, eye colour multiply).
- **Listing photos** — the pipeline's `Listing prompts` (flat lay, shelf, a mother reading) with the book's cover,
  to copy into ChatGPT; caught as JPEG.
- **The listing's texts by the local Gemma — maybe**, after a test on 2–3 existing books.
- **Not wanted:** an image API (money), a demo book without Canva, a character-consistency check
  ([decisions](../decisions.md), 2026-09-25).

## The pipeline moves in, cleaned (the owner's idea)

A fresh copy, "only the needed things, started from zero"; the old `Etsy-Book-Pipeline` stays as it is, an
archive (read-only, as now).
- **Taken:** `playbook` (agents 0–6, master prompt, visual world bible, knowledge, archetypes — ~200 KB),
  `notes/discoveries.md`, the `Listing prompts` JSON. **Not** the `seo-intelligence` guide (the owner,
  2026-09-26: "it goes separately"). In git (the repo is private — checked 2026-09-25) — the playbook gets a
  change history for the first time, **only once it moves into Book Studio** (no git in the prototype, the
  owner, 2026-09-26). Copied into the prototype on 2026-09-26; into Book Studio's `pipeline/` (in git) the same
  day.
- **Not taken:** most of `tools/` — cutting and flipping are already in the Workshop, `build_workshop_json` is no
  longer needed, `validate-book` becomes the console's own check (shown on the strip), `split_cover` belongs to
  the Mockups. `BOOKS_NEW` (13 GB) stays where it is.
- **One book — one folder:** the agents write only into the book's `agent/` subfolder (text, prompts,
  `canonical.png`); the console carries them into the rows. **Agents never touch `book.json`** — so they can't
  break a book, and the owner's edits in the Workshop aren't lost.

## Catches (settled on the move, 2026-09-26)

- **Two sets of agent rules in one project**: Book Studio's `AGENTS.md`/`CLAUDE.md` are for coding agents. Settled:
  Antigravity is opened on `pipeline/` — it reads the rules from the opened folder up to that folder only
  (Antigravity's docs, 2026-09-26), so a book agent never sees the root files; the root `AGENTS.md` still has a fork
  at the top ("making a book → `pipeline/GEMINI.md`"), and `pipeline/CLAUDE.md` sends a coding agent back up.
- **Antigravity hides git-ignored files** from its agents (its setting *Agent Gitignore Access*, off by default —
  found in the program on 2026-09-26) and everything outside the opened folder. The books (`pipeline/books/`) are
  kept out of git — so the owner turns that setting on once; the agents' rules say so.
- **Watching Downloads**: only files that appear after "Generate" was pressed, only pictures (PNG/JPEG/WEBP),
  never touching other files there.
- The pipeline's folder is read-only by today's rule ([glossary](../glossary.md)) — the prototype works on its
  own copy.

## Steps (each checked by the owner)

1. ✓ **The prototype, apart from Book Studio** (2026-09-26) — [below](#the-prototype-2026-09-26).
2. ✓ **A separate branch** of Book Studio (`book-console`, 2026-09-26): the pipeline into the project, the strip and
   `agent/` — [below](#into-book-studio--the-integration-plan-2026-09-26).
3. ✓ The generation mode in the Workshop and the hero variants (the same day). The listing photos were dropped by
   the owner after the first real book ("redundant").

## The prototype (2026-09-26)

A separate program in `D:\Roman\Desktop\Book Console` (its own window «Пульт книги», port 47850) — the steps were
built one by one, each tried on made-up books first; the owner then made his **first real book** in it
(`40.first-halloween`: 29 pictures caught, Gemini's JPEGs 5824×2880 and 4096×4096) — "it all works really great,
really convenient" — and deleted that book afterwards (it didn't please him). What it taught, now in the Workshop:

- **A download moves into the book** ("it should live in the program") — `originals/`, named by its row; the cut,
  named pages in `pictures/` are the set for Canva; every picture can be saved anywhere («Зберегти як…»).
- **The listing photos, the cover's mockup and reference went** ("redundant", "they only confuse me").
- **The cover is the last card, in two stages** — the picture, then its margins outpainted to **the printer's
  template** (the owner's 8×8 hardcover, "just make it the default"): 5370×2850 px, 300 dpi, the template's lines.
- **A deleted book goes to the Windows Recycle Bin**, never away for good.
- The flow polished: the page redraws without blinking, the generation bar shows the queue, the page follows the
  waiting row, a finished queue says so, buttons wait (no double press).
- *Not checked on the owner's PC in the prototype*: whether Gemini's download is caught every time (a picture saved
  twice), pasting the program's clipboard picture into Gemini, F8 vs «Далі», Antigravity opened on a folder. The
  first real book answered most of them in practice.

The prototype's folder is left as it was; with the move it is no longer needed (the owner removes it and its
desktop shortcut himself).

## Into Book Studio — the integration plan (2026-09-26)

> The owner: "create a new branch on GitHub and integrate the console into the Workshop — a detailed plan, then
> the integration; think the UX through, change the interface where needed, but above all a seamless, smooth
> integration and the cleanest code". Branch **`book-console`** (pushed to GitHub the same day).

### What changes for the owner

1. **One program.** The Workshop (Listings → Майстерня) *is* the console: its book list is the Workshop's
   gallery, a book's page is the console's page, in Book Studio's own parts and cyan. The separate window «Пульт
   книги» is no longer needed; its folder `D:\Roman\Desktop\Book Console` is left as it is (the owner removes it
   and its shortcut when he wants).
2. **The pipeline moves into the project**: `Book Studio/pipeline/` — the agents' rules, the playbook, the notes,
   the listing prompts, in git (the playbook's history starts). The books live in `pipeline/books/` — **not in
   git** (pictures, gigabytes). Antigravity is opened on `pipeline/` («Відкрити агента», «Нова книга»).
   **Once, by the owner:** Antigravity → Settings → Agent → *Agent Gitignore Access* on — Antigravity hides
   git-ignored files from its agents by default (checked 2026-09-26 in the program itself:
   `AllowAgentAccessGitignoreFiles`, `BLOCK_REASON_GITIGNORED`); the agents' rules say so too, so an agent that
   can't see `books/` tells him.
3. **The gallery**: the console's cards (the picture, №, the cover's title, the 10-step bar, «Далі: …»,
   «Картинки n/16», GO, «чекаю картинку»), search, sort (by number — default, recently changed, least ready),
   «У роботі · У бібліотеці». «+» (N) = a new book in Antigravity (the clipboard holds «нова книга»); the books
   folder button.
4. **A book's page**: the header (№ and title, the cover's title, Tier; «Відкрити агента», «Сторінки», the
   originals, «Ще» → the folder, delete to the Recycle Bin; «Передати в бібліотеку»), the generation bar, the
   path strip and its panel, the rows (prompt · 2:1 frame · text), the cover's two stages, hero variants — all
   the prototype's behaviour. New from Book Studio: the upload progress on a frame, the viewer (a click on a page —
   every page in order, T for the text), the dark picture tools of the library.
5. **The old Workshop's own ways go**: typing prompts and texts in the page, the JSON `{ }` menu and its agent
   instruction, a new book by title — **the agents' files are the one source** (read, never written by the page;
   a file opens in Windows from the step's panel). No real book used them (0 on 2026-09-26).
6. **«Бібліотека» becomes real**: «Передати в бібліотеку» (the same dialog: the Etsy listing, checked read-only)
   makes a library book from the book's pages (`pictures/1…30.png`, `Cover.png`), its texts (`book-text.md`) and
   the listing, with a progress bar; the strip's last step ticks by itself; the book stays in the Workshop (tab «У
   бібліотеці») with its folder — originals, variants — untouched. «Мокапи» and «Canva» stay ticked by hand
   («Мокапи» opens the Mockups page).
7. **The generation mode reaches the whole program**: while a picture is awaited and the owner is elsewhere in
   Book Studio — a dot on the rail (the brand icon in Orders, «Майстерня» in Listings), the window's title
   «● Розворот 10–11 · 6 з 16», a notice per caught picture; when the queue is done the taskbar button flashes
   with Windows' sound.

### Where things go (code)

- `pipeline/` — `GEMINI.md` = `AGENTS.md` (paths: `python check_book.py "books/<book>"`, "Book Studio's
  Workshop"), `CLAUDE.md` (the fork), `playbook/`, `notes/`, `Listing prompts/`, `check_book.py` (a thin start for
  the agents → the Workshop's check), `books/` (git-ignored). The root `AGENTS.md` gets a fork at the top.
- `app/studio/workshop/` — a package replacing `workshop.py`: `books.py` (a book = a folder: the list, the strip,
  marks, versions, delete, passing to the library), `rows.py` (the agents' files → rows, the cover's template,
  variants), `pictures.py` (a picture into its row), `generate.py` (the generation mode), `check.py` (the old
  validator's rules), `routes.py`. `app/studio/clipboard.py` — the Windows clipboard and F8. `desktop.py` — the
  «Зберегти як» dialog, the Recycle Bin. `core.py` — `PIPELINE`, `WORKSHOP_BOOKS`, `SANDBOX` (the preview and the
  tests: no clipboard, no F8, no windows, their own Downloads and books).
- `library.py` — the old Workshop's `stage`/`prompts` go; `create_book()` and `import_pictures()` are shared by
  «Нова книга», the folder import and the passing.
- The page: `pages/workshop.js` (the gallery), `pages/workshop-book.js` (a book), `workshop-live.js` (the live link:
  what changed, the generation's state and bar, the rail's dot and the title, the notices), `lib.js` `patch()` (a
  keyed redraw in place that carries loaded pictures over), `app.js` (routes by the folder's name), `app.css`.
- Tests: `test_workshop.py` from the prototype's 43 + the passing + the sandbox; `tools/sample_books.py` — made-up
  books for the tests and the preview.

### Smoothness

- The page asks `/api/workshop/sig` every 1.5 s while it's visible; on a change it fetches the book and **redraws
  only what changed** (keyed parts); a picture that stays is carried over into the new markup, never reloaded —
  the scroll, the hover, an opened prompt stay.
- Every picture's address carries its version (`?v=`): cached for good, a replaced picture gets a new address.
- Only transform and opacity animate; the cover's stages slide, a step that has just become done pops.

### Build order

1. The pipeline into the project, the forks. 2. The server package and its routes. 3. The library: the passing,
the old model out. 4. The page: the live link, `patch()`, the gallery, the book, CSS, the shell. 5. Tests, the
preview server, the sandbox. 6. The wiki: the Workshop's page rewritten, glossary, decisions, code map, routes,
data, runtime, preview, log; the steps page folded in here and removed. 7. Checked in the preview on made-up books
(both themes); commit and push to `book-console`.

*Not now* (the roadmap as before): upscaling right after a catch, Tier H orders, the listing's texts by Gemma.

**Built as planned on 2026-09-26** (checked in the preview on made-up books: the gallery, a book's page, a caught
download row after row, the cover's two stages, hero variants, passing to the library, the rail's dot and the title
while in another mode, both themes; 52 tests of the Workshop). *Not checked by the agent:* Antigravity's window and
its setting on the owner's PC, a real Gemini download and paste, F8 on the real Windows inside Book Studio.

## Open questions

- ~~Where the prototype lives~~ — **its own folder on D**, like «Мокапи» at first (the owner, 2026-09-25).
  What it looks like — **proposed 2026-09-26**: the Workshop's book page on its own small server, in its own
  Edge window, in Book Studio's style; the folder `D:\Roman\Desktop\Book Console` (confirmed by the owner,
  2026-09-26) — [the prototype](#the-prototype-2026-09-26).
- ~~Which book to try it on~~ — **a real new book**: the console is for making a book, so the prototype is
  tried by making one from scratch; the owner will think of which (2026-09-25).
- **Opening Antigravity** — the app is `%LOCALAPPDATA%\Programs\antigravity\Antigravity.exe` (the `agy` CLI
  isn't installed); «Відкрити агента» ran `Antigravity.exe <pipeline folder>` (VS Code's way of opening a folder).
  **Wrong for Antigravity 2** (found 2026-09-26, the owner: "the agent saves books into the old folder"): it takes
  only `antigravity://` links, never a folder; a new chat runs in the project last picked — it was the prototype's
  `Book Console`. Now Antigravity is only started, the clipboard's words carry the pipeline's full paths, and the
  owner picks a project on `Book Studio\pipeline` once — [Workshop](../features/workshop.md#where-a-book-lives).

## Related

- [Plans](roadmap.md) · [Workshop](../features/workshop.md) · [Mockups](../features/mockups.md) ·
  [Decisions](../decisions.md)
