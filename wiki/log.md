# Wiki change log

Newest entries at the top. Heading format: `## [YYYY-MM-DD] kind | what happened`
(kind: `setup`, `ingest`, `update`, `query`, `lint`, `decision`). Rules — [dev/wiki-rules.md](dev/wiki-rules.md).

## [2026-09-25] update | The text check calibrated; another book's pages raise a big red alarm

- The owner asked to calibrate what the text check shows. On the journal (30 checks, 10 orders): 103 rows →
  12, red 69 → 3 (the three are a real wrong-template book); all 4 real catches stay, one the model missed
  is now the program's own rule. Details — [features/text-check.md](features/text-check.md#calibration-2026-09-25).
- Code: `textcheck.py` (the rules, the wrong-book alarm, the journal keeps the model's verdicts and the
  owner's marks, route `POST /api/textcheck/mark`), `wording.py` (`Leo's` → `Leo`), `orders.js` /
  `app.css` (the red banner, the badge, the print question), new `app/tools/textcheck_replay.py`; 11 new tests.
- Data: the First Bible Stories passport — three words as in Canva (`.bak` kept).
- Checked: all 280 tests; the banner, "Це та книга" and the print question in the preview on made-up data
  (the check's answer faked in the page). Not checked: a real Gemma run on a wrong-template book.
- Pages: features/text-check.md, features/orders.md, decisions.md, glossary.md, owner/ui-principles.md,
  security.md, architecture/api-routes.md, code-map.md, dev/testing.md, index.md.

## [2026-09-25] update | The book pipeline makes a Workshop import file instead of rendered prompts

- The owner asked his `Etsy-Book-Pipeline` to produce a file the Workshop imports instead of `rendered-prompts.md`.
  In the pipeline (not in this repo): new `tools/build_workshop_json.py` → `workshop.json`; agents 3/4 keep a
  `## Cover` title section, agents 5 and 6 run the tool; `validate-book.py` warns when `## Cover` is missing.
- Book Studio's code unchanged. Checked: the tool on copies of all 31 books (25 written; the old 15-panorama
  books and one broken cover JSON refused), every file read by `parse_book_json()` with nothing missing but the
  cover title, and one imported into the preview's Workshop — 17 prompts, 17 texts.
- Pages: features/workshop.md.

## [2026-09-24] update | The Workshop: a dropped spread is flipped like his flipper and cut into two pages

- The owner: a 2:1 spread dropped into its frame should become "two nice squares like in the passport", flipped
  by his flipper's logic (`Etsy-Book-Pipeline\tools\mirror-alternate.py`, `slice-spreads.py`, read only). His
  answers: automatic + ⇄ by hand; a narrower picture cut top and bottom; only the two pages kept
  ([raw/2026-09-24-workshop-flipper-owner-answers.md](raw/2026-09-24-workshop-flipper-owner-answers.md)).
- `workshop.py`: `place_spread()` (cut to 2:1 around the centre, mirrored for 4–5, 8–9 … 28–29 — `MIRRORED`, two
  square PNG pages into `left`/`right`, the slot notes `mirrored` and `source`), `flip_spread()` (⇄: the pages
  mirrored and traded; twice — the same pixels), routes `/spread` and `/flip` (113 in all). `library._remove_asset`
  forgets the notes of an emptied spread. The page: two squares per spread, ⇄ lit while mirrored, «віддзеркалиться»
  on an empty frame of such a spread, «обрізано …» when the picture wasn't 2:1; the viewer shows the two pages.
  New icon `mirror`.
- Checked: tests (269; `SpreadsBecomeTwoPages` by pixel colours), the preview (the sample's spreads, a drop of
  2400×1100 onto 12–13 — mirrored and cut at the sides, ⇄ on 2–3).
- Pages: features/workshop.md (+ "A spread becomes two pages"), decisions.md, glossary.md, api-routes.md,
  index.md, library.md, rules/book-structure.md, frontend.md, dev/preview.md, dev/testing.md.

## [2026-09-24] decision | The inks swapped: Orders orange, Listings cyan

- The owner: the Workshop takes the colours the Studio has now, the Studio turns orange "like Etsy and Claude".
  `app.css`: the default `--accent*` tokens are orange (`#bf4f1a` / `#f0874d`, a deeper shade than Etsy's so white
  text on a button stays readable), `[data-mode="listings"]` — the former cyan; the dot of a mockup run going on
  elsewhere is cyan. Checked on the preview: both modes, dark and light.
- Pages: decisions.md, features/modes.md, features/workshop.md, features/mockups.md, architecture/frontend.md,
  glossary.md, index.md, overview.md, owner/ui-principles.md, plans/listings-mode.md, plans/roadmap.md;
  app/README.md.

## [2026-09-24] update | Two modes: Orders and Listings — the Workshop, the mockups inside Book Studio

- The owner: Book Studio gets a second mode for making listings, switched by a click on the brand icon, "like
  another program". Two rounds of questions, the plan approved without changes (his words —
  [raw/2026-09-24-listings-mode-owner-answers.md](raw/2026-09-24-listings-mode-owner-answers.md), the
  agreements — [plans/listings-mode.md](plans/listings-mode.md), [decisions](decisions.md)). Branch
  `photoshop-module` (from `audit-fixes`).
- **Two modes** ([features/modes.md](features/modes.md)): `MODES` and a mode per route in `app.js`; the brand
  icon (Alt+0) switches; Listings in magenta (`[data-mode="listings"]` tokens, both themes), its own rail
  (Майстерня, Мокапи) and title; each mode remembers its last page; always starts in Orders; the rails' own
  switch animation; a magenta dot while a mockup run goes on elsewhere. New icons `listing`, `workshop`,
  `prompt`.
- **The Workshop** ([features/workshop.md](features/workshop.md)): books in development — a library book with
  `"stage": "workshop"` and `"prompts"`, never in the orders (`all_books()` leaves it out); a new book by its
  title; 17 row cards (prompt, 2:1 frame, text) of moderate width; pictures one per frame, not-2:1 marked;
  prompts and texts from one JSON (a dry run asks before replacing), the agent's instruction; «Передати в
  бібліотеку» — the library's «Нова книга» dialog in its passing-on form. New `workshop.py`, `workshop.js`,
  `workshop-book.js`, 6 routes (111 in all).
- **The Mockups moved in** ([features/mockups.md](features/mockups.md)): a page of the Listings mode, working as
  before, kept when left; its files stay in `app/data/mockups`; the demo book gets a folder of its own
  (`mockups/book/`) — the utility wiped all dropped files, which inside Book Studio would have taken an order's;
  the utility's leftovers (~300 MB) go once. Removed: `Mockups.pyw`, `mockups_app.py`, `mockups.html`,
  `mockups-shell.js`, its icons, the «Мокапи» shortcut, `dev_server.py --mockups` (now part of `--sample`,
  with a Workshop book).
- Checked: tests (264, `test_workshop.py` new, `test_mockups.py` for the own folder); the preview — both modes,
  light and dark, the Workshop (edit, JSON with the replace question, drops incl. not 2:1 and two files,
  passing on with the duplicate refused), a whole mockup run with the owner in the orders meanwhile. Not
  checked live: the real Photoshop inside Book Studio, a real Etsy listing check.
- Pages: features/modes.md, features/workshop.md (new), features/mockups.md, features/library.md,
  architecture/frontend.md, runtime.md, server.md, api-routes.md, data.md, code-map.md, glossary.md,
  overview.md, security.md, recipes.md, dev/preview.md, setup.md, testing.md, owner/ui-principles.md,
  working-with-owner.md, rules/book-structure.md, flows/book-import.md, plans/roadmap.md,
  plans/listing-mockups.md, plans/listings-mode.md (new), index.md; README.md, app/README.md, AGENTS.md,
  CLAUDE.md.

## [2026-09-23] update | Mockups look like Book Studio, clean up after themselves; nothing on drive C

- «Мокапи» laid out like the Order Creator: four numbered steps (book field with the folder button and a
  badge — drop anywhere or the ZIP dialog; spreads in templates with the templates' own PSD previews, clicks
  and drags; where to save with «Та сама, що минулого разу»; Photoshop with per-template progress, the
  drawn "Yes", the saved pictures shown), the book's structure on the right; picks come back for a book
  dropped again; the sliders window for the templates / Photoshop folders.
- «Зберегти відкриті й закрити»: a second script saves the three hand-finished templates and closes them.
  "Done" when the window is behind: the taskbar button flashes, Windows' sound, the title.
- Cleaning: prepared pictures right after the script, the copies left open after «Зберегти відкриті» or at
  once with Photoshop closed (a day at most while it's open, a week for a copy the owner saved himself),
  one demo book at a time, everything temporary gone on close.
- Drive C: Book Studio and «Мокапи» give themselves and what they start a temp folder on D
  (`core.own_temp()`); tests and preview servers write to `.tmp\` in the repository; the tests' wipe fixed
  (an open log blocked it). 177 old `bstests-*` folders, the preview data and the agents' leftovers removed
  from `%TEMP%`.
- Pages: features/mockups.md (rewritten: use, cleaning table), architecture/runtime.md (temp files and
  drive C), data.md, api-routes.md (+7), security.md, decisions.md, dev/testing.md (247), dev/preview.md,
  plans/listing-mockups.md, glossary.md, owner/working-with-owner.md, index.md.

## [2026-09-23] update | Mockups: "I press it and nothing happens" — the button always answers now

- The owner's first try: no `work/` folder and no `places.json` in `app/data/mockups` — the run never
  started. The folder dialog opened in front in every reproduction (also from an Edge app window after a
  real click), so the cause was the greyed-out «Зробити мокапи» that ignored a press until all 8 slots
  were filled.
- Now the button always answers: empty slots blink and a message names them; the wait for the Windows
  dialog is shown; a dialog closed without a folder is said. Every step goes into
  `app/data/mockups/logs/app.log` (`_logged()`).
- Pages: [features/mockups.md](features/mockups.md) (+ "When something goes wrong"),
  [owner/ui-principles.md](owner/ui-principles.md) (a button never ignores a press in silence), tests
  (231).

## [2026-09-23] update | The «Мокапи» utility built: a Canva demo book → Photoshop listing pictures

- New page [features/mockups.md](features/mockups.md): a separate program (shortcut «Мокапи», port 47831,
  data folder `app/data/mockups`) — drop the Canva ZIP, pick 8 spreads, one Photoshop script saves 7 PNGs
  and leaves 1. Cover 1, Cover & Open 1, All & Open 1 open for the owner's front cover. The plan page now
  says "built" and keeps the templates and Photoshop findings (saving acts on the *active* document; a
  cold start reaches the "run this script?" question in ~5 s).
- The dropped-files code moved from creator.py into `drops.py` with Canva's naming rules
  (`export_files()`, `page_number()`, `COVER_NAME`); the routes are `/api/drop/*` now (98 routes in all,
  8 of them the utility's). Pages: api-routes, dropped-files, file-naming, code-map, runtime, server,
  data, frontend, glossary, book-import.
- Security: the utility only reads and copies the templates, never saves into them, refuses them as the
  output folder; new rule 11 — Photoshop's settings are the owner's. Decisions: why a separate data folder,
  the file names, the copies' lifetime.
- Checked: 229 tests (the Photoshop script itself runs under Node.js against a pretend Photoshop), the
  window on the preview server (`dev_server.py --mockups`), and live on the owner's PC with the real
  Photoshop and a made-up book (37 s from a cold start; the templates' dates unchanged).

## [2026-09-23] ingest | Listing mockups: the owner's video description, the templates, the agreed utility

- Sources: the owner's text description of his screen recording
  ([raw/2026-09-23-mockups-video-breakdown.md](raw/2026-09-23-mockups-video-breakdown.md)) and his chat
  answers ([raw/2026-09-23-mockups-owner-answers.md](raw/2026-09-23-mockups-owner-answers.md)); a
  read-only analysis of the six templates in `D:\Roman\Desktop\Трафарети мастхев` (layers, smart object
  sizes, linked copies, saved previews).
- Agreed: a separate "Mockups" utility first (Book Studio later); the script fills pages, spine, back
  cover (and the front cover's rim in the open-book templates); the owner fits the front cover by hand;
  PNG into a folder picked every time; the templates are read-only, the script opens copies.
- New page: [plans/listing-mockups.md](plans/listing-mockups.md). Updated:
  [plans/roadmap.md](plans/roadmap.md), [decisions.md](decisions.md), [glossary.md](glossary.md),
  [security.md](security.md) (rule 10), [owner/working-with-owner.md](owner/working-with-owner.md),
  [integrations/canva.md](integrations/canva.md), [plans/open-questions.md](plans/open-questions.md),
  [index.md](index.md), `AGENTS.md`. Corrected: `psd-tools` does read the large templates (the
  2026-09-19 "over ~350 MB" note). No code changed.
- **Photoshop scripting check** (on copies of two templates, made-up pictures): a `.jsx` launched from
  outside runs after a "run this script?" confirmation; replacing smart-object contents by layer name,
  swapping spreads and saving PNGs works — 11 s for two templates; hidden layers become visible when
  selected by a script; `Cover & Open 1`'s visible top copies change nothing. Results — in
  [plans/listing-mockups.md](plans/listing-mockups.md).

## [2026-09-23] update | Fixes from the owner's own audit (everything except accounting)

- **"Update passport"** no longer breaks the text: the name — only as a whole word, and only where the
  passport had `{Name}`; before saving, you can see exactly what will be saved.
- **The archive** trusts only a freshly loaded list from its own printer (`loaded` in the snapshot); a
  list that failed to load or was cut off at its cap proves nothing.
- **Gelato**: an unknown result when creating a draft is no longer "rejected" — the link stays valid.
  The network client no longer retries a POST that might have gone through; Printify and Gelato read
  errors the same way (`httpc.human()`).
- **The receipt number** is its own field on the book; `cloudflared` shuts down together with the
  program even after a crash; the preview server takes no keys; dialogs sit above the viewer; library
  import follows one set of rules; "own text" and the child's name are read the same way in the card and
  in the check (`wording.py`); a deleted file's `.bak` is no longer read; the wiki check cross-checks
  every mention of a number.
- What was deferred with accounting, and what was deliberately left alone, is in [decisions.md](decisions.md).
- Updated: [features/text-check.md](features/text-check.md), [features/archive.md](features/archive.md),
  [features/order-creator.md](features/order-creator.md), [features/orders.md](features/orders.md),
  [features/library.md](features/library.md), [features/settings.md](features/settings.md),
  [flows/book-import.md](flows/book-import.md), [flows/dropped-files.md](flows/dropped-files.md),
  [rules/file-naming.md](rules/file-naming.md), [rules/sync-policy.md](rules/sync-policy.md),
  [integrations/gelato.md](integrations/gelato.md), [integrations/printify.md](integrations/printify.md),
  [integrations/etsy.md](integrations/etsy.md), [architecture/server.md](architecture/server.md),
  [architecture/data.md](architecture/data.md), [architecture/frontend.md](architecture/frontend.md),
  [architecture/runtime.md](architecture/runtime.md), [architecture/api-routes.md](architecture/api-routes.md),
  [security.md](security.md), [dev/testing.md](dev/testing.md), [dev/preview.md](dev/preview.md),
  [dev/wiki-rules.md](dev/wiki-rules.md), [code-map.md](code-map.md), [decisions.md](decisions.md),
  [index.md](index.md), [plans/open-questions.md](plans/open-questions.md).

## [2026-09-22] update | Fixes from the external code audit

- Checked the findings from the audit the owner's colleague sent over against the code, and fixed what
  really hurt: **the text check now belongs to the book** (a receipt's second book no longer cuts off
  the first), **"Undo" survives a restart** (read from disk, not from the page's memory), **a receipt
  can have several print orders** — and all of them are counted in the cost (a new
  `profit/print-orders.json`, the "+N in print" chip in the queue).
- Tool safety: tests **always** take their own temporary folder, the preview server only writes to its
  own (marked `.book-studio-sample`, never the folder holding `vault.json`). An accounting error after
  a successful send is no longer silent. The library saves the book's record before deleting the old
  file. A page can't be swapped out while the book is being sent to the printer.
- The wiki check learned to catch stale numbers in the text (was: 117 tests vs. 182, 88 routes vs. 92);
  the numbers were fixed; `app/data` is ≈6.6 GB.
- What was deliberately left undone, and why — in [decisions.md](decisions.md).
- Updated: [features/text-check.md](features/text-check.md), [features/orders.md](features/orders.md),
  [features/order-creator.md](features/order-creator.md), [features/library.md](features/library.md),
  [rules/reconciliation.md](rules/reconciliation.md), [architecture/data.md](architecture/data.md),
  [security.md](security.md), [dev/testing.md](dev/testing.md), [dev/preview.md](dev/preview.md),
  [dev/wiki-rules.md](dev/wiki-rules.md), [code-map.md](code-map.md), [glossary.md](glossary.md),
  [decisions.md](decisions.md), [index.md](index.md), [plans/open-questions.md](plans/open-questions.md).

## [2026-09-20] update | Replacing a single page from the viewer — built

- In the page viewer — a button for each page of a spread: pick the fixed file on the computer, and it
  takes the old one's place. "Undo" sits next to it. Works both in the order card and in the Order
  Creator; new routes `pick-file`, `replace-page`, `restore-page`.
- After a replacement: a new picture (the address gets a version number), the files are re-checked, the
  text check restarts (the model re-asks only about this page), and this page's "not an error" marks are
  forgotten.
- "Not an error" marks are now also cleared by new files (the owner's request).
- Dropping one or two loose pictures onto an already-prepared book no longer wipes out the work — it now
  points to the viewer instead. Ollama no longer starts twice (the warm-up and the check share a lock).
- Updated: [features/orders.md](features/orders.md), [features/order-creator.md](features/order-creator.md),
  [features/text-check.md](features/text-check.md), [flows/order-to-print.md](flows/order-to-print.md),
  [rules/file-naming.md](rules/file-naming.md), [architecture/frontend.md](architecture/frontend.md),
  [architecture/api-routes.md](architecture/api-routes.md), [dev/testing.md](dev/testing.md),
  [code-map.md](code-map.md), [glossary.md](glossary.md), [decisions.md](decisions.md),
  [plans/roadmap.md](plans/roadmap.md).

## [2026-09-20] decision | Replacing a fixed page — from the viewer

- Discussed with the owner and recorded in the plans: replacement buttons in the viewer (two per
  spread), the native file-picker window, re-checking only that page, "Undo", both in the card and in
  the Order Creator. Waiting on his "go ahead". Also recorded there: the requirement to clear "not an
  error" marks when new files arrive.
- [plans/roadmap.md](plans/roadmap.md), [decisions.md](decisions.md).

## [2026-09-20] update | The model — only pages that might have text

- The owner's remark: why show the model every page if only half have text. Now the program looks at
  each page's preview itself (thin strokes gathered into rows = text) and only sends the model what
  might have text; in a 30-page book, reading disappears entirely for some pages — the page goes
  straight to comparison against the passport's reference.
- Measured on real books: 39.7 → 24.4 s (30 pages), 44.8 → 33.6 s (24 pages), 40.3 → 30.9 s (a complex
  book); the same problems found either way. The mark never decides anything on its own: "unsure" still
  goes to the model, an empty-looking spread is still read by the model, and if the mark is wrong the
  other half of the spread gets checked too. A switch lives in Settings.
- Fixed its own bug from that same morning: because of `setdefault()`, every page was queued to the
  model twice (56 requests instead of 29) — the check had become ~40% longer.
- Updated: [features/text-check.md](features/text-check.md), [features/settings.md](features/settings.md),
  [dev/testing.md](dev/testing.md), [code-map.md](code-map.md), [glossary.md](glossary.md),
  [decisions.md](decisions.md).

## [2026-09-20] update | Orders with several books — one draft to one address

- The owner's request: "so several books go into one draft for one address." In the card, each book of
  a receipt now has its own folder, comparison, and text check (the switcher just shows a different
  one), and "To print" takes every ready book from the same printer. Printify — one product per book and
  **one** "On hold" order with a line item for each; Gelato — one draft with a product and a PDF for
  each book.
- Updated: [features/orders.md](features/orders.md), [features/order-creator.md](features/order-creator.md),
  [flows/order-to-print.md](flows/order-to-print.md), [features/send-journal.md](features/send-journal.md),
  [integrations/printify.md](integrations/printify.md), [integrations/gelato.md](integrations/gelato.md),
  [architecture/frontend.md](architecture/frontend.md), [dev/preview.md](dev/preview.md),
  [dev/testing.md](dev/testing.md), [code-map.md](code-map.md), [glossary.md](glossary.md),
  [decisions.md](decisions.md), [plans/roadmap.md](plans/roadmap.md),
  [plans/open-questions.md](plans/open-questions.md).

## [2026-09-20] update | Text check: findings as the check runs, and warming up the model

- The owner's request (the first and second items from the "what else could be sped up" list): mistakes
  appear in the card as soon as a page is checked, and a spread goes to comparison right after its own
  pages are read (in a 30-page book); the model loads onto the graphics card as soon as the card takes
  in the files — a new route, `POST /api/textcheck/warm`.
- Honest about the payoff: the check's total time is almost the same (the queue to the model was already
  full); the saving comes from the warm-up (~4 s, versus up to ~70 s "cold"); the main win is that the
  owner sees the first mistakes sooner.
- Updated: [features/text-check.md](features/text-check.md), [architecture/server.md](architecture/server.md),
  [architecture/api-routes.md](architecture/api-routes.md), [architecture/frontend.md](architecture/frontend.md),
  [dev/testing.md](dev/testing.md), [code-map.md](code-map.md), [decisions.md](decisions.md),
  [plans/roadmap.md](plans/roadmap.md).

## [2026-09-20] update | An "X — done with this order" button

- The owner's request: after a successful send — an X button in the card (near the back arrow) and in
  the Order Creator's header; it forgets the order's saved work (`keep.finish()`) and opens the queue.
  Updated [features/orders.md](features/orders.md), [features/order-creator.md](features/order-creator.md),
  [architecture/frontend.md](architecture/frontend.md), [glossary.md](glossary.md), [code-map.md](code-map.md).

## [2026-09-19] update | Tooltips no longer get cut off; the menu doesn't linger after navigating

- The owner's remark: long tooltips ran off the edge of the panel. An automatic scan of every page
  (1480 and 1100 px): the rest of the text fits, the flaw was only in tooltips (5 different ones) — now
  they wrap. Along with it: the menu closes on navigation, Alt+1…5 no longer fire under a dialog or the
  viewer. [architecture/frontend.md](architecture/frontend.md),
  [owner/ui-principles.md](owner/ui-principles.md).

## [2026-09-19] update | The queue remembers its tab, search, and scroll position

- The owner's remark: "back" from a card led to "New" instead of the tab it came from. Now it returns to
  the same tab. [features/orders.md](features/orders.md), [owner/ui-principles.md](owner/ui-principles.md).

## [2026-09-19] update | Smoothness: fixes after the code review

- The model frees the graphics card right after a check; the check stops once it's no longer needed (a
  new route, `…/textcheck/cancel`); idle cards — no more than three; the preview cache is cleared
  (21 days); minor fixes from [plans/open-questions.md](plans/open-questions.md). Decisions —
  [decisions.md](decisions.md).
- Updated: [features/text-check.md](features/text-check.md), [features/orders.md](features/orders.md),
  [features/settings.md](features/settings.md), [features/library.md](features/library.md),
  [architecture/api-routes.md](architecture/api-routes.md), [architecture/frontend.md](architecture/frontend.md),
  [architecture/data.md](architecture/data.md), [architecture/runtime.md](architecture/runtime.md),
  [code-map.md](code-map.md), [dev/testing.md](dev/testing.md), [index.md](index.md).

## [2026-09-19] query | Code review: why it stopped feeling smooth, flaws found

- At the owner's request — an analysis of code quality and smoothness (no code changes): the server is
  fast, the main suspect is the model sitting on the graphics card during and after the text check; the
  list of flaws and the order to fix them — [plans/open-questions.md](plans/open-questions.md).

## [2026-09-19] update | Text check with a local model — built

- The order card, "Comparison" step: Gemma in Ollama reads the pages, the program checks them against
  the book's passport and the Etsy data; an icon, a problem list, frames on the pages, a question before
  printing, "Update passport"; a block in Settings. New page — [features/text-check.md](features/text-check.md).
- Checked on three real books from the archive and on a 24-page book with planted mistakes (all found,
  no false alarms); found that two books' passports had drifted from their Canva templates.
- Updated: [features/orders.md](features/orders.md), [flows/order-to-print.md](flows/order-to-print.md),
  [features/settings.md](features/settings.md), [features/library.md](features/library.md),
  [architecture/api-routes.md](architecture/api-routes.md), [architecture/data.md](architecture/data.md),
  [architecture/frontend.md](architecture/frontend.md), [security.md](security.md),
  [code-map.md](code-map.md), [glossary.md](glossary.md), [decisions.md](decisions.md),
  [plans/roadmap.md](plans/roadmap.md), [dev/testing.md](dev/testing.md), [dev/preview.md](dev/preview.md),
  [overview.md](overview.md), [index.md](index.md).

## [2026-09-19] decision | Ideas: pages without Canva, listing mockups via a Photoshop script

- Recorded at the owner's request ("we'll build it later"): the program draws its own pages and
  dedications (with Gemma's help), first as a "lab"; researched tools for Linux; listing mockups — a
  Photoshop CC 2019 script fills in the templates' pages, the owner still makes the covers himself.
  [plans/roadmap.md](plans/roadmap.md). No code changed.

## [2026-09-19] query | Thoughts: the text check as a program feature

- At the owner's request ("too early to build, just write it down") — what a check button in the order
  card could look like, what to compare against, the steps, and open questions:
  [plans/roadmap.md](plans/roadmap.md).

## [2026-09-19] update | Cut-off text: Gemma always finds it

- Two pages with text running off the edge (including a name that vanished entirely) — found in every
  variant. [plans/roadmap.md](plans/roadmap.md).

## [2026-09-19] update | Words stuck together: blind transcription can "add" a space; Qwen — dropped

- Page "Isabellawalked": Gemma without a hint missed it at 1024 px, with a hint it always found it. The
  design for the future feature — a hint plus the program's own comparison (6/6 at every size). The owner
  decided to drop Qwen. [plans/roadmap.md](plans/roadmap.md).

## [2026-09-19] update | The GPU: both models already run at full load, parallel processing — twice as fast

- Both models run 100% on the GPU; Qwen is louder because it reads the picture at full resolution. The
  owner turned on `OLLAMA_NUM_PARALLEL=4`: a hard test with 4 pages at once — 10.3 s, the same result.
  Updated [plans/roadmap.md](plans/roadmap.md), [owner/working-with-owner.md](owner/working-with-owner.md).

## [2026-09-19] update | A hard test on the owner's own pages: Gemma 5/5, no false positives

- 12 pages from real Canva templates (5 with mistakes, 7 clean, 2 of which were a real book the owner
  planted himself). Gemma 4 12B QAT: blind transcription plus the program's comparison — every mistake,
  no false alarms, even at 768 px, ~1.5 s per page; Qwen 3.5 9B was weaker. No code changed. Results —
  [plans/roadmap.md](plans/roadmap.md).

## [2026-09-19] update | Gemma 4 12B QAT: the text-check test passed in full

- Installed `gemma4:12b-it-qat` at the owner's request (on D). The same test: both methods with no
  mistakes (with a name hint — like Gemini; blind transcription 3 of 3), ~1–3 s per page. It's now the
  main candidate. No code changed. Updated [plans/roadmap.md](plans/roadmap.md).

## [2026-09-19] update | A local model installed (Ollama + qwen3.5:9b) and tested

- At the owner's request: Ollama in `D:\Programs\Regular\Ollama`, the model `qwen3.5:9b` on drive D.
  Tested on the same pages used for Gemini: with a name hint the model "corrects" the mistake in the
  name; blind transcription plus the program's comparison — every mistake found, ~2.5 s per page. No
  code changed.
- Updated [plans/roadmap.md](plans/roadmap.md), [owner/working-with-owner.md](owner/working-with-owner.md)
  (programs only on D).

## [2026-09-18] update | The order card: a long dedication in the note now scrolls

- The note on the first spread was cutting off long text (7 lines) — now it's fully visible, the note
  scrolls inside itself (`.proof-note`). Updated [features/orders.md](features/orders.md); the hidden-
  pane navigation trap is recorded in [dev/preview.md](dev/preview.md).

## [2026-09-18] update | Gelato: the "number - name" title, a made-up phone number, the 5" × 5" format

- From the owner's remarks: `orderReferenceId` = the book's name; an empty phone number →
  `+1 555 555 0100`; a small softcover from Etsy (`5" × 5"`) now goes straight to Softcover 5.5×5.5.
  Updated [integrations/gelato.md](integrations/gelato.md), [features/order-creator.md](features/order-creator.md),
  [rules/printer-rule.md](rules/printer-rule.md), [decisions.md](decisions.md), [glossary.md](glossary.md).

## [2026-09-18] update | Only a placed and paid printer order is counted

- The owner's wish: drafts, unpaid, and cancelled orders no longer move a receipt to "in progress",
  don't put the book in the archive, and don't turn the next send into a reprint (`is_placed()`). A
  draft-status chip in "New"; "Take files from the last send" in the card; a reprint only comes from a
  book that was actually printed.
- Updated: [rules/order-stages.md](rules/order-stages.md), [features/archive.md](features/archive.md),
  [features/orders.md](features/orders.md), [features/order-creator.md](features/order-creator.md),
  [features/profit.md](features/profit.md), [flows/order-to-print.md](flows/order-to-print.md),
  [architecture/api-routes.md](architecture/api-routes.md), [decisions.md](decisions.md),
  [glossary.md](glossary.md), [dev/preview.md](dev/preview.md), [dev/testing.md](dev/testing.md).

## [2026-09-18] update | Gelato: where "Page 0" comes from; blank pages at 300 dpi; reprinting a cancelled order

- Found out (reading two orders via the API, the old Order Creator's log, a PDF from 2026-09-17): the
  "correct" order with no Page 0 had gone through Gelato's own editor; the printed PDF has the same
  structure as ours.
- The PDF's blank pages — white 300 dpi instead of 16×16 px (because of which Gelato judged the book's
  print quality at 3 dpi).
- A reprint, when the first order was cancelled at the printer, is not marked as a replacement.
- A test draft via the old Order Creator (cover and pages as separate files): the cover ended up on
  every page — keeping one PDF, Page 0 is normal.
- Updated: [integrations/gelato.md](integrations/gelato.md), [decisions.md](decisions.md),
  [features/archive.md](features/archive.md), [rules/order-stages.md](rules/order-stages.md),
  [rules/book-structure.md](rules/book-structure.md), [dev/testing.md](dev/testing.md).

## [2026-09-18] update | Work on a new order is remembered across tab switches

- The owner's wish: come back to the same step of an order (files, comparison, the Order Creator, even
  the success screen), until the order leaves "New". Pages are now hidden and brought back (`keep.js`,
  `navigate()`); the "Orders" icon leads to the last open card; after success, the "Print" step says
  "draft created". An Order Creator opened by hand still starts empty.
- Updated: [architecture/frontend.md](architecture/frontend.md), [features/orders.md](features/orders.md),
  [features/order-creator.md](features/order-creator.md), [flows/order-to-print.md](flows/order-to-print.md),
  [owner/ui-principles.md](owner/ui-principles.md), [owner/working-with-owner.md](owner/working-with-owner.md),
  [decisions.md](decisions.md), [glossary.md](glossary.md), [code-map.md](code-map.md).

## [2026-09-18] update | Side menu: the icon no longer vanishes under the highlight square

- During a page change, the active item's highlight square was a separate snapshot over the icons and
  covered up the icon it was moving toward. Now the panel stays live through the transition: the square
  moves under the icons, the icon smoothly changes color. Updated
  [architecture/frontend.md](architecture/frontend.md), [owner/ui-principles.md](owner/ui-principles.md).

## [2026-09-18] update | Order archive built: files that went to print, 14 days, and reprints

- A new "Order archive" menu (Alt+4, Settings is now Alt+5): every send to Printify or Gelato saves a
  copy of the book's files into `data/archive/`; the book's page — comparison, order details, address,
  "Don't delete", reprint. Files delete themselves 14 days after "Sent"; with no order information,
  nothing is deleted. Description — [features/archive.md](features/archive.md).
- Reprint: Printify — a new On hold order from the same book (nothing re-uploaded; if the book is gone,
  it's rebuilt from the archive); Gelato — a new draft from the same files. The receipt is marked as a
  replacement, the queue stage doesn't change.
- Updated: [architecture/api-routes.md](architecture/api-routes.md), [architecture/data.md](architecture/data.md),
  [architecture/frontend.md](architecture/frontend.md), [architecture/runtime.md](architecture/runtime.md),
  [features/order-creator.md](features/order-creator.md), [features/profit.md](features/profit.md),
  [rules/order-stages.md](rules/order-stages.md), [rules/sync-policy.md](rules/sync-policy.md),
  [flows/order-to-print.md](flows/order-to-print.md), [security.md](security.md), [decisions.md](decisions.md),
  [glossary.md](glossary.md), [code-map.md](code-map.md), [plans/roadmap.md](plans/roadmap.md),
  [dev/preview.md](dev/preview.md), [dev/testing.md](dev/testing.md), [index.md](index.md).

## [2026-09-18] decision | Plan: "Order archive"; the program only runs on the Wrocław PC

- Agreed with the owner (no code changed): a separate "Order archive" menu with the files of books that
  went to print, comparison, and reprints; auto-deletion 14 days after "Sent", a "Don't delete" button,
  new orders only — [plans/roadmap.md](plans/roadmap.md), [decisions.md](decisions.md),
  [glossary.md](glossary.md).
- The owner doesn't run Book Studio on the Kyiv PC: clarified in [overview.md](overview.md),
  [owner/working-with-owner.md](owner/working-with-owner.md), [integrations/etsy.md](integrations/etsy.md);
  removed the question about a Kyiv-PC copy from [plans/open-questions.md](plans/open-questions.md).

## [2026-09-17] decision | Text check via Gemini — into the plans

- Discussed and tested on made-up pages (3.6 / 3.5 Flash found every planted mistake; 3.8 / 3.7 Flash
  were overloaded). No code changed; the owner saved the key `gemini_api_key` in the program's vault.
- The owner deferred building it; the free tier, only pages with text (up to 17). Plan —
  [plans/roadmap.md](plans/roadmap.md), the decision and Google's EEA terms — [decisions.md](decisions.md).

## [2026-09-17] update | The queue: one tone, copying the order number, a status next to the name

- From the owner's remarks on real data: the printer name, carrier, and number — one soft tone; the Etsy
  order number copies on click (in the queue and the card); in the card, the printer status sits next to
  the name, centered. Updated [features/orders.md](features/orders.md),
  [owner/ui-principles.md](owner/ui-principles.md), [glossary.md](glossary.md), [decisions.md](decisions.md).

## [2026-09-17] update | The queue: the "truck" tab, printer status, tracking numbers

- Built the owner's idea: a fourth stage, `sent` (the printer shipped it, not yet marked in Etsy), the
  Printify/Gelato status on the right (in English, in a human form, with a colored dot), the child's name
  bold in the grey row, a tracking-number chip (carrier | number, click to copy) — in the queue and the
  card's header.
- Sync: Printify saves `shipments`; Gelato reads shipped orders' tracking numbers one at a time
  (`attach_shipments()`, read-only). The "Gelato · 28 or 30 pages" chip — one font; chip text sits on one
  line.
- Updated: [rules/order-stages.md](rules/order-stages.md), [features/orders.md](features/orders.md),
  [integrations/printify.md](integrations/printify.md), [integrations/gelato.md](integrations/gelato.md),
  [rules/sync-policy.md](rules/sync-policy.md), [flows/order-to-print.md](flows/order-to-print.md),
  [architecture/frontend.md](architecture/frontend.md), [owner/ui-principles.md](owner/ui-principles.md),
  [security.md](security.md), [dev/preview.md](dev/preview.md), [dev/testing.md](dev/testing.md),
  [glossary.md](glossary.md), [decisions.md](decisions.md); the idea removed from [plans/roadmap.md](plans/roadmap.md).

## [2026-09-17] update | Send journal — a button in the Order Creator's header

- The owner couldn't find the journal icon (it only lived in the result and error cards). Now it's
  always in the header next to the Printify/Gelato switch, and opens the newest entry —
  [features/send-journal.md](features/send-journal.md), [features/order-creator.md](features/order-creator.md).
- The owner decided not to rotate the Gelato key pasted into chat ([decisions.md](decisions.md)).

## [2026-09-17] decision | Git: commit everything together

- The owner asks not to split changes into "mine / other sessions'" and not to complicate things with
  branches — everything together, the version history is there either way. Recorded in
  [dev/setup.md](dev/setup.md) and [owner/working-with-owner.md](owner/working-with-owner.md).

## [2026-09-17] update | Gelato: standards from real orders, the send journal

- Read (read-only) the owner's manual 28-page order and an old 30-page API order, broke down their print
  PDFs; made two test drafts with numbered pages.
- Findings — in [integrations/gelato.md](integrations/gelato.md) and [decisions.md](decisions.md):
  metric 20×20 / 14×14 cm products; the PDF "cover · blank · pages · blank" stays (without the blank
  pages the book shifts — checked); Page 0 in a draft is the endpaper; 28 pages — no shift.
- New: [features/send-journal.md](features/send-journal.md) (the send journal, route
  `POST /api/sends/open`), checking the link over public DNS, a cover-trim warning only past 10 mm.
- Also updated: [features/order-creator.md](features/order-creator.md), [rules/book-structure.md](rules/book-structure.md),
  [architecture/data.md](architecture/data.md), [security.md](security.md), [plans/open-questions.md](plans/open-questions.md),
  [glossary.md](glossary.md), [code-map.md](code-map.md), [recipes.md](recipes.md), [index.md](index.md).

## [2026-09-17] ingest | The owner's answers about the "truck" tab and statuses

- The truck — a fourth tab between "In progress" and "Sent": the printer has shipped it, not yet marked
  in Etsy; once marked in Etsy, the order moves to "Sent". The status on the right — exactly as
  Printify/Gelato give it, in English; no separate marks needed for drafts.
- Updated [plans/roadmap.md](plans/roadmap.md), [glossary.md](glossary.md) (the truck, the box, the
  clock), [rules/order-stages.md](rules/order-stages.md), [features/orders.md](features/orders.md); two
  questions removed from [plans/open-questions.md](plans/open-questions.md). No code changed.

## [2026-09-17] update | Gelato: a 28- or 30-page book

- Built the idea from the plans: the number of pages downloaded (28 or 30) decides the Gelato book's
  length; the decision — in [decisions.md](decisions.md), the item removed from [plans/roadmap.md](plans/roadmap.md).
- The program reads from Gelato's catalog how many pages each format prints; a new route,
  `GET /api/creator/gelato/page-counts` ([architecture/api-routes.md](architecture/api-routes.md)).
- A 28-page softcover — not checked live (Gelato's docs say "from 30"); the program will show the answer
  after a restart — [plans/open-questions.md](plans/open-questions.md).
- Updated: [integrations/gelato.md](integrations/gelato.md), [features/order-creator.md](features/order-creator.md),
  [features/orders.md](features/orders.md), [rules/printer-rule.md](rules/printer-rule.md),
  [rules/book-structure.md](rules/book-structure.md), [rules/file-naming.md](rules/file-naming.md), and others.

## [2026-09-17] ingest | Idea: shipped orders, status, and tracking number in the queue

- Source: [raw/2026-09-17-vidpravleni-i-trek-nomery.md](raw/2026-09-17-vidpravleni-i-trek-nomery.md)
  (the owner's text; the screenshot wasn't kept — it had real buyer names on it).
- Recorded in [plans/roadmap.md](plans/roadmap.md) (the truck tab, the status on the right, the name in
  the grey row, the tracking-number chip), questions — in [plans/open-questions.md](plans/open-questions.md),
  new terms — in [glossary.md](glossary.md), "planned" marks — in [features/orders.md](features/orders.md)
  and [rules/order-stages.md](rules/order-stages.md). No code changed.

## [2026-09-17] decision | The key file .secrets.txt now lives in the Book Studio root

- At the owner's request, the file was copied from Etsy OS without opening it (byte-for-byte identical);
  git ignores it. The original stayed in Etsy OS. Updated [security.md](security.md) and `AGENTS.md`.
- The owner is disconnecting the Etsy OS folder from work with the agent (its `.gitignore` had been
  deleted, and the "Commit changes" button could have saved the keys into git history).

## [2026-09-17] setup | Wiki created, the program moved into app/

- The owner proposed a knowledge base modeled on "LLM Wiki"; agreed on: `app/` + `wiki/` +
  `AGENTS.md`/`CLAUDE.md`, detailed links to code, keeping it current after every task.
- The program was moved into `app/` (`git mv`), `data/` and `bin/` along with it; fixed the path to the
  old programs in `settings_api.py`; rebuilt the shortcut; checked the tests and starting the server.
- Read the whole codebase; created 37 pages (plus the index and the log): overview, glossary, code map,
  security, structure (5), sections (5), services (4), rules (6), paths (3), owner (2), development (4),
  decisions, recipes, plans (2).
- Turned `docs/order-pipeline.md` into [flows/order-to-print.md](flows/order-to-print.md), and spread the
  rest of its content across the rules, decisions, and plans.
- Moved facts from the agent's memory into [decisions.md](decisions.md), [owner/](owner/working-with-owner.md),
  [security.md](security.md).
- Added `app/tools/wiki_check.py`, the test `test_wiki.py`, `app/tools/dev_server.py`, and Claude Code
  skills for the wiki.
