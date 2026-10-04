# Wiki change log

Newest entries at the top. Heading format: `## [YYYY-MM-DD] kind | what happened`
(kind: `setup`, `ingest`, `update`, `query`, `lint`, `decision`). Rules — [dev/wiki-rules.md](dev/wiki-rules.md).

## [2026-10-03] update | The portable folder shows one shortcut

- `make_shortcut.py` in the portable copy also writes `Book Studio.lnk` into the portable folder itself (and `Book Studio Portable.lnk` on the desktop). The `.bat` files, `ROADMAP.md` and `ПРОЧИТАЙ.md` in the folder's root are hidden (the owner: he only needs a shortcut); `ПРОЧИТАЙ.md` says how to show them and what to do after the folder is moved.

## [2026-10-04] update | The portable copy gets its own private GitHub repository

- `raymanrboy/book-studio-portable` (private): the whole copy committed and pushed once (the owner asked). A scan of the 282 files to commit found no key or token; nothing from `app/data`, `app/bin`, `pipeline/books`, `.secrets.txt`. The docs said «the repository is `raymanrboy/book-studio`» — that is the original's: rewritten to the new one (AGENTS.md, CLAUDE.md, setup.md, decisions.md).

## [2026-10-04] update | The Workshop's «Прибрати» acts at once and offers «Скасувати»

- `pictures.remove()` returns `undo`; new `pictures.restore()` and `POST /api/workshop/books/<id>/restore`; the page no longer asks, it removes and shows «Картинку прибрано · Скасувати» (checked in the portable copy's own preview on the made-up book: removed, then restored, the row's marks back). The book photo's «Прибрати» keeps its question.

## [2026-10-04] update | The audit's findings fixed (second pass: everything that was left)

- **Server:** one copy per data (a named Windows mutex); a refused length no longer moves the dropped files (`arrange_pages(precheck=…)`); `data/tmp` leftovers swept at start (`core.sweep_tmp()`); closing waits for the upscaler; a new backup is opened and checked before old ones are pruned, the two programs' copies are told apart by name (`Book Studio Portable …`), a young `.part` is not deleted, a 12-character password; the portable Ollama is stopped with the program; a key's redirect to another host drops the key (`httpc._SafeRedirects`); a missing file is a 404, an expected failure a 400; `book.json` is no longer overwritten after a failed read; a cut-short Cutter, `write_json` leaving `.tmp`/damaging `.bak`, a vault warning on every request, an Etsy photo without a size limit — all fixed; `visual C++` check by version, its «no» remembered, its result said.
- **Interface (by an agent, reviewed here):** keyboard and screen reader (menus, viewer, picker rows, chips, `data-press`), no silent grey buttons (Settings and Mockups say what is missing), typed text kept after a failed save, one loud button per view, `--text-3` for real information, plurals and words, escaped attributes, dead code out.
- **Wiki and docs:** the dead names, `app/README.md`, `CLAUDE.md`/`setup.md` (the portable copy), the glossary, the data page; `wiki_check` now also flags a `name()` that is nowhere in the code (the log is exempt).
- **Not changed on purpose:** «Повернути» walks back version by version (the owner's design); the Workshop's «Прибрати» keeps its question (no restore route); `/api/orders` still follows the Workshop's files (the slow-request log will say whether it matters).
- **Caught late:** the preview of this session runs the ORIGINAL program (its `launch.json`); the portable copy's own dev server must be started by hand with `runtime/python/python.exe -B app/tools/dev_server.py --sample`. 556 tests.

## [2026-10-04] update | Quiet model read-in, hidden Ollama windows, the link stays, the window no longer shuts when covered

- Black windows: measured with a window watcher — the flashing came from Ollama's helpers (`llama-server.exe`, `gpu-discover`) of an Ollama started the old way; started with `CREATE_NO_WINDOW` nothing appears. The portable Ollama was restarted that way.
- `run.prime()`: the model is read in quietly 8 s after the start and let go.
- A Gelato draft's link stays in the order's card after «Завершити» while it lives (`keep.linkOf`).
- Shutting down by itself: the window is started without throttling, and the «closed» rules are stricter (see runtime.md). `main()` crashed at start for a moment during this work (`transfer` used before its import) — fixed, and `test_server_http.StartUp` now starts the real program in a process.
- `/api/app` no longer follows every Workshop book (`library.counts()`); slow requests are logged.
- The Etsy shop's name (as Etsy gives it) is in the window's title.

## [2026-10-04] update | Self-improvement audit: findings fixed

- Five read-only audits (server core, portability, interface, security, tests/docs). Fixed in code:
  - `images.py`: previews and the folder check could deadlock each other (opposite lock order) — one order now; the page strips could hang for good.
  - Settings transfer no longer carries or accepts `security.*` and Printify's read-only switches; keys file removed right after reading, leftovers swept at start; only known key names go to the vault.
  - `desktop.to_recycle_bin` warns when Windows would delete for good; the file dialogs work with Cyrillic paths (`-X utf8`); `make_shortcut.py` too.
  - A second launch on the same PC no longer opens the other Book Studio's window (`/api/ping` carries `data`); HTTP replies forbid framing; Etsy host guard normalised.
  - Modules: a cut-short Ollama unpacking is redone, the Upscayl engine and its model count only whole, a module ZIP may hold only its own folder, no path on the plain install route.
  - The upscale thread survives any error; a failed Gelato PDF build removes its folder; negative Content-Length clamped.
  - Interface: a failed text save keeps the typed text; «посилання закрито» only when it is; a page that failed to redraw retries; the modules progress cannot show «NaN%»; a stale window says to press F5; a late Etsy-link answer cannot overwrite a newer one.
  - Tests: five files get the made-up data folder when run alone; new `test_server_http.py` (the HTTP layer) and transfer tests. 536 tests.
  - The colleague-copy builder no longer carries the owner's names itself and scrubs the Desktop path too.
- Left for the owner's choice or a later day: see ROADMAP «Аудит 04.10».

## [2026-10-03] update | Ollama starts without blinking windows; the interface says it is starting

- `_start_ollama` uses `CREATE_NO_WINDOW` instead of `DETACHED_PROCESS`: Ollama's helper processes no longer open a black console each (they blinked).
- `status()` has `starting`; `/api/textcheck/warm` answers `starting` when it is about to start Ollama; the order card shows «Запускається Ollama…» and then «Ollama запущена».
- The module install window no longer says the program can be used meanwhile (it is blocked): «Вікно не закривайте — воно саме закриється».

## [2026-10-03] update | The spare copy of the templates removed from the portable copy

- `Трафарети мастхев (копія)` (1.5 GB) in the repository folder went to the Recycle Bin (the owner agreed): it was never read by the program, and all 9 files
  match `runtime/Templates`. The line is gone from this copy's `AGENTS.md`.

## [2026-10-03] update | The text check's settings moved under its module

- The «Перевірка тексту» card is gone from Settings: its switches, model and «Запустити» are nested under the installed «Розумна вичитка тексту» in «Модулі»
  (`textcheckSettings()`); `#/settings/textcheck` and the search lead to «Модулі». Checked in the preview, both installed and not installed.

## [2026-10-03] update | Modules isolated from the PC's own Ollama and Upscayl (before the owner's remove-and-reinstall test)

- The copy's Ollama: own port 11435, `OLLAMA_MODELS` always in `runtime/`, started by its exe; Upscayl only from `runtime/`; `installed()` strict;
  removal closes the module's processes first. Tests added (16 in test_modules). Page: [optional modules](features/modules.md).

## [2026-10-03] update | The manual proofread against the live program

- Every claim of `MANUAL.md` checked against the running program (sample data, a clean start, the code): the labels (the queue's tabs, the order
  card's steps and buttons «До друку в Gelato» / «Створити чернетку» / «Передрук у Gelato», the Mockups' four steps, the Workshop's strip and
  «Генерувати решту», the photo categories, Settings), the shortcuts, the shutdown, the paths. About a dozen wrong or stale statements were
  fixed; new facts added: Chrome for the generation mode (Ctrl+V / F8), the Etsy Callback URL and the port, the Printify preset, slide 7. One
  real bug found and fixed on the way: a fresh install had no `browser.hosts`, so Gelato and Canva would not open in the program's own Edge
  profile — the defaults now name `gelato.com` and `canva.com` (`core.DEFAULT_SETTINGS`).

## [2026-10-03] update | Optional modules: the text check and upscaling installed from the interface

- New `studio/modules.py`, `web/js/modules-ui.js`, Settings → «Модулі», offers in the Workshop and the order card; the colleague copy leaves Ollama and
  Upscayl out and ships a lean Python and ffmpeg. The upscale install was run for real. Page: [optional modules](features/modules.md).

## [2026-10-03] update | The portable copy independent of the place: paths follow the folder, quiet install of Windows prerequisites

- `portable.rebase_paths()` (paths in the data follow a moved repository, the old files backed up), `portable.prerequisites()` / `install()`
  (Visual C++ x64 offered at start and installed quietly: a bundled installer or winget). Page: [the portable copy](dev/portable.md).

## [2026-10-03] update | The code cleaned of the owner's paths, a manual for agents, stock Photoshop in the colleague copy

- The light theme is now the code's default; the owner's `D:\\…` paths are gone from the code (the mockups' defaults are the portable layout);
  the start-up window is shorter (a list of missing programs and one line of what to do) — seen on the screen. New `MANUAL.md` for agents;
  the colleague copy takes a stock Photoshop and mentions the manual in its note. Page: [the portable copy](dev/portable.md).

## [2026-10-03] update | A copy for the colleague: his own agents' docs, light theme, Photoshop and templates in

- `make_colleague_copy.py` puts in neutral `AGENTS.md`/`CLAUDE.md`/working-with-the-owner (templates in `app/tools/colleague_docs/`), cuts the
  owner's personal rules out of `security.md`, seeds the light theme, takes Photoshop and the templates by default. Rebuilt and checked:
  501 tests and the wiki check pass inside the copy.

## [2026-10-03] update | The portable copy, stage 7 (part): audit, switchable owner rules, a copy for a colleague

- Audit of the whole code (syntax warnings, JS, unused imports, risky calls, the server, a clean start on empty data): clean. Found and
  fixed: Etsy-only-from-Kyiv and Printify-read-only-from-1-Oct were hard-wired → settings; new `tools/make_colleague_copy.py`. Page: [the portable copy](dev/portable.md).

## [2026-10-03] update | The portable copy, stage 6 (part): export/import of settings and keys

- New `studio/transfer.py`, the Settings block «Перенесення налаштувань», `desktop.pick_7z()`, the tests. Page: [moving the settings](features/settings-transfer.md).
  Not yet: carrying it over to the ordinary Book Studio (it is built only in the portable copy), and syncing.

## [2026-10-03] update | The portable copy, stage 5: the copy as a project

- `AGENTS.md` §0 (what this copy is), `ПРОЧИТАЙ.md` for the owner, no git remote; page [the portable copy](dev/portable.md).

## [2026-10-03] update | The portable copy, stage 4 (part): checked after moving the folder

- The folder moved to another name: the paths of Photoshop, templates, Antigravity, ffmpeg and Upscayl (also the one saved in
  `settings.json`) follow it; 489 tests pass there. Antigravity from `runtime/` writes only to its own `user-data` and `home`;
  Ollama (own port), Upscayl and ffmpeg run from `runtime/`. Still for a human/another PC: see the ROADMAP.

## [2026-10-03] update | The portable copy, stage 3: Antigravity's own profile, Edge instead of Cent, AGENTS.md

- Antigravity starts from `runtime/` with its own user-data folder and home (`.gemini`); Gelato/Canva open in Edge with a
  profile of the copy; Cent Browser removed from the copy; `pipeline/GEMINI.md` dropped, `AGENTS.md` is the one rules file
  (code, tests, wiki, playbook updated). Page: [the portable copy](dev/portable.md).

## [2026-10-03] update | The portable copy, stage 2: launchers and the start-up check

- `Start Book Studio.bat` and two more in the root; `portable.check()` / `startup_report()` (what is missing, what to log in to,
  once per computer); the shortcut tool names the portable shortcut apart. Found: the keys are DPAPI-locked to the Windows
  user and do not open on another PC — reported at start, the choice is the owner's. Page: [the portable copy](dev/portable.md).

## [2026-10-03] update | The portable copy, stage 1: the path layer

- The copy's own folder `Book Studio Portable/` (the original untouched). New `studio/portable.py`; Photoshop, templates,
  Antigravity, Ollama, Upscayl, ffmpeg and the Cent Browser profile are found in `runtime/`; saved old-PC paths are taken into
  it. Tests isolate themselves from it. Page: [the portable copy](dev/portable.md).

## [2026-10-03] lint | The wiki as a finished product: plans and ideas removed, pages synced with the code

- Removed `wiki/plans/` (the roadmap, open questions and seven build plans/histories — all stay in git history). What was
  durable moved: the Photoshop templates' structure and scripting facts → [mockups](features/mockups.md#the-templates); the
  model research → [text check](features/text-check.md#why-this-model-and-this-design); limits and what was only tried against
  fakes → the new [known limits](dev/limits.md).
- Pages that still described the pre-October (Printify) or two-mode state as current were rewritten to how it is now
  (overview, index, orders, order-creator, order-to-print, printer rule, security, gelato, printify, modes, runtime, preview,
  glossary); forward-looking words ("for now", "later", "planned") and counts in prose removed; dangling links to the removed
  pages turned into plain text in the log and the decisions.
- `app/README.md` and `README.md` rewritten for the current product; code comments no longer point at removed pages; the wiki
  skills and `AGENTS.md` no longer mention plans; the `plan` page type left `wiki_check.py`.
- Checked: `wiki_check.py` and the tests pass; constants in the text (text-check, archive, backup, mockups, tunnel, accounting
  date) compared with the code.

## [2026-10-03] query | The text check after Ollama 0.35.1: the model loops on one correct page

- Diagnosis only, no code changed; the deferred fix — open-questions ("Waiting to see if it
  happens again").

## [2026-10-02] update | Slide 7: the caption under a look's frame is the owner's own

- The owner asked to edit the caption under a «зірочка»: «Підпис» in the frame's properties — his text (lines,
  `{name}` — the look's name), empty — the name as before ([slides](features/slides.md)). Checked in the preview and a bake.

## [2026-10-02] update | Listing slide 7 — the hero's looks

- A seventh listing slide for a book whose hero has looks (two or more `hero.png` in `agent/variants/`), drawn on slide 4
  after the owner's reference: each look in its own frame with its name, on its white background
  ([slides](features/slides.md#slide-7--the-heros-looks-since-2026-10-02), [decisions](decisions.md)).
- The frame («Картинка») got Зірочка / Прямокутна, Наблизити, Що видно, and a name under / over it; `{looks}` in texts.
- Old schemes get it in their own colours; `etsy/15 Listing 7.png` ([photo mockups](features/photo-mockups.md)).
- Checked: tests (made-up looks), the bake with the looks of book 28 copied into the preview's temporary book, the editor.

## [2026-10-02] decision | The portable Book Studio set aside

- At the owner's word; recorded in [decisions](decisions.md) and the roadmap.

## [2026-10-02] update | The Mockups opened from a book no longer trap the owner

- The owner: from a book into the Mockups, and after a step elsewhere he couldn't get back — the arrow led to
  «Інструменти», «Книги» led into the Mockups. The page took itself for a tool on its own whenever it was come back
  to from anything but the book; meanwhile «Книги» still remembered the Mockups as its last page.
- Now the Mockups stay the book's step until opened from «Інструменти» or for another book (`arrived()`), and a rail
  place returns only to a page that still belongs to it (`placeAt` in `entryOf()`)
  ([mockups](features/mockups.md), [frontend](architecture/frontend.md)). Checked in the preview: a kept page with a
  demo book, a page opened clean, the tools' Mockups, the rail's «Книги».

## [2026-10-01] update | The Gelato draft's card stays in the order card while its link lives

- The new `gelato-result.js` holds the Gelato result card. The Order Creator and the order card both draw it, and the
  order card keeps it while the temporary link lives. The button is now «Замовлення в Gelato», in the archive too. The
  yellow notice stays, with a true text ([decisions](decisions.md), [orders](features/orders.md),
  [order-creator](features/order-creator.md)).

## [2026-10-01] update | «Gelato Dashboard» opens the orders list, in the browser profile «Work»

- At the owner's request, the Gelato button after a draft is created (the Order Creator) and in the archive now opens
  `dashboard.gelato.com/orders/list`, not Gelato's home page ([order-creator](features/order-creator.md),
  [archive](features/archive.md)).
- Gelato and Canva links open in Cent Browser's profile «Work» (`Profile 6`). This uses the settings' `browser` section
  and `_open_in_profile()`; every other link opens in the default browser
  ([decisions](decisions.md), [settings](features/settings.md)).

## [2026-09-30] update | The owner switched to his own Gelato account

- The owner used «Перейти на новий акаунт Gelato» at 23:26. Right after, both accounts were read whole: the old one has 595
  orders (all still there), the new one has 1 old draft from July. Etsy's 88 receipts are unchanged.
- Read-only check: the new key sees the same catalog (28–200 pages, the same sizes as [gelato](integrations/gelato.md)) and
  the same base prices as the old one.
- With the owner's permission in chat: one TEST draft was sent to the new account from a script, with made-up numbered
  pages (hardcover 8×8, 28 pages), not through the program. It was created as a draft, and Gelato fetched the PDF through
  the temporary link. Its reference is «TEST Book Studio - new account check (do not print)». The owner deletes it in Gelato.
- The old account's orders have «CozyCovenant» on the return address, billing in EUR (Germany), a card, and USPS Ground
  Advantage. A draft shows none of these, so the new account's settings get checked in Gelato itself.

## [2026-09-30] update | «Сьогодні» removed; the tools open clean

- «Сьогодні» is deleted as a function (the owner's word); a tool opened from «Інструменти» starts clean — live work excepted ([decisions](decisions.md)).

## [2026-09-30] update | Schemes inside the slides editor and before the six are made

- A scheme (Nature, Night, his own) is edited in place by its key and picked with the editor's «Схема» button even when it is opened on its own; the Mockups' step 4
  offers the same choice before «Зробити слайди». **Restart Book Studio** (server routes changed).

## [2026-09-30] update | The owner's first look at the real data: the wheel trap, the tools' way back, the slide reset

- The order card's data column no longer scrolls on its own (`stickyFit()`); «Інструменти» always opens the list and a tool opened on its own has a back
  arrow (`backToTools()`); the slides' back leads to where he came from and «Повернути слайд» returns to the session's start; the Mockups take a book only
  when asked. Start time: measured, not reproduced — [decisions](decisions.md).

## [2026-09-30] update | The top-level docs follow the rail

- README, app/README, AGENTS and CLAUDE no longer say «two modes»: the rail, «Сьогодні», the light theme as the main one, and the skill
  `book-studio-ui-logic` are named where an agent or the owner starts reading.

## [2026-09-30] update | Wave 8: a drop anywhere, a picture that comes back, a working keyboard

- A file dropped outside a page's own field asks «Куди?» (the Mockups / the Order Creator) and is handed over (`drop-anywhere.js`); a removed
  library picture is set aside and «Скасувати» restores it (`POST …/assets/restore`, tested); a real Tab walk fixed three faults (a tab group is one
  stop with arrows, the focus lands on the new page's title, a dialog keeps Tab inside and returns the focus). Plan: ui-waves.
- **Restart Book Studio** (a server route was added).

## [2026-09-30] update | One plan for all the interface waves

- plans/ui-waves.md: waves 0–7 and the icons with step-by-step instructions (files, functions, checks), what was left out
  on purpose, and wave 8 — what is still open, in the order to take it.

## [2026-09-30] update | The final waves: undo, one review before print, «Сьогодні», Ctrl+K verbs

- A library book is removed at once and «Скасувати» brings it back (`POST /api/library/trash/restore`, tested); the print
  send's up-to-four questions are one review; the brand mark opens «Сьогодні» (`pages/today.js`); Ctrl+K gets «Мокапи · №41» /
  «Слайди · №41»; the Settings' caption went. Not done (and why) — [decisions](decisions.md).
- **Restart Book Studio** (a server route was added).

## [2026-09-30] update | Waves 3–4: one book tile, one bar, the Workshop's steps as pictures

- The library's and the Workshop's book tiles are one component (`book-tile.js`); a book's progress is one bar (4 segments in
  the library, 11 in the Workshop); the Workshop's eleven steps are drawn by the order path's `pathStep()` — a picture per
  step, the word and the numbers in the tooltip. The state alphabet is written into [ui-principles](owner/ui-principles.md).
- The Tools' tiles, the Mockups' paragraph and the Workshop's header/prompt were quieted earlier in the same pass.

## [2026-09-30] update | Wave 1–2 of the third pass: the hammer and ruler, a tick for «done», quieter Workshop

- The Workshop's glyph is a hammer and a ruler crossed (the owner's wish); `×` no longer means «finish» — a ✓ and a toast.
- Type and press tokens (`--lh-tight/--lh/--lh-read`, `--press`, `--press-soft`), weights 500/700 cleaned, `--text-3`
  in light to AA, the proof note's labels out of tracked capitals, a chip 24 px, `aria-disabled` on the waiting make button.
- The Workshop header: folder and shelf as icons, one labelled button when the book is ready; a prompt shows three lines.
  Pages and decisions: [frontend](architecture/frontend.md), [workshop](features/workshop.md), [decisions](decisions.md).

## [2026-09-30] update | Three weakest icons redrawn, the book card's keyboard ring

- `pin` (was read as a flask) is a push-pin now, `original` a picture in frame corners, and a new `video` icon takes the
  Omni video from `motion` (which stays the reduce-motion switch — one icon, one meaning); the full icon sheet was looked
  over at 96 px and at 16–20 px, the rest of the set stays ([frontend](architecture/frontend.md)).
- A library/Workshop book card had no visible keyboard focus (`outline: none` with no replacement) — the frame takes the ring.
- An analysis pass of every page in light found more to do; the plan comes next (ui-redesign).

## [2026-09-30] update | Show, don't tell: the rail and the tabs as icons, a printer bug, design skills

- The owner's corrections: the rail icons only with search last, the queue's and the books' tabs as icons with counts,
  an order's path as pictures, the next-step sentences gone (a «Позначте в Etsy» that only opened the order); the order
  card's chip names the printer the order really went to ([ui-principles](owner/ui-principles.md), [decisions](decisions.md)).
- Agent skills for interface logic, icons, visual craft and code installed (text only, local) plus the project's own
  `book-studio-ui-logic` — [design-skills](dev/design-skills.md).

## [2026-09-30] ingest | The light theme is the owner's main one

- From now on design decisions are taken and checked in the light theme first ([ui-principles](owner/ui-principles.md));
  the redesign was screenshot in dark, so a light pass is owed.

## [2026-09-30] update | The interface redesign built: objects with their path, tools on their own, one labelled rail

- The rail: Пошук (Ctrl+K) · Замовлення · Книги · Прибуток | Інструменти, Settings at the bottom; the two modes went,
  the inks follow the area ([the rail](features/modes.md), [decisions](decisions.md)).
- «Книги» — Майстерня · Бібліотека · Архів; «Інструменти» — the Order Creator, the print archive, the Mockups, the
  photo mockups, the slides, each on its own or inside its object.
- The order: the queue's tabs in words, each row's next step, the path in the card and in its print step, a printed
  order's card with what went to print (`archive.card_facts()` → `printed`).
- Five type sizes, radii on tokens, readable faint text, labelled fields, no silent grey buttons, three widths.
- Pages updated: modes, frontend, code-map, glossary, recipes, ui-principles, orders, order-creator, archive, library,
  workshop, mockups, photo-mockups, profit, settings, slides, text-check, the flows, the plan.

## [2026-09-30] decision | The interface redesign planned

- A UI/UX audit of every page (made-up data, four widths) and the flows; eight design skills installed into
  `.claude/skills/` (texts only, not in git). The owner agreed to one strict visual system and asked for the most
  effort on intuitiveness — plans/ui-redesign.md: the findings, the proposed structure (an
  order and a book each in one place with its path), the open decisions asked one at a time. Nothing built yet.

## [2026-09-30] update | The Mockups' header loses its «Слайди для лістингу» button

- The ▣ menu (the default scheme, the books with slides, older sets) removed at the owner's request, with its route
  `/api/slides/sets` ([decisions](decisions.md)); slides open from the book, new books' design is set in the editor.

## [2026-09-30] update | The etsy/ folder numbered in the listing's order

- A book's `etsy/` files carry their number in the owner's listing order («01 photo-main.png» … «14 photo-shelf.png»),
  the open-book photo taking Cover & Open 1's place; the owner's own files keep their names and sort last
  ([photo mockups](features/photo-mockups.md#where-things-are), [decisions](decisions.md)).
- `photos.tidy_etsy()` after every photo, video, scene copy and slide bake; everything finds its file by the name
  without the number (`bare()`); the slides' re-bake keeps writing into the numbered file.
- Book 25's `etsy/` renamed once — exactly the owner's list.

## [2026-09-30] update | «У руках дитини»: two more templates

- The owner's two new photos (a boy holding the blank book: a nursery, a bedroom in the evening) copied into
  `photo-mockups/child/` as `child-04-boy-nursery` and `child-05-boy-bedroom-evening`; the three others of his folder
  were there already. No code changed.

## [2026-09-30] update | «Розмір»: five more templates

- The owner's `Заготовки обкладинок\Книга в руках у людини` (a woman holds the small softcover and the large hardcover
  side by side, at home) copied into `photo-mockups/size/` as `size-02-nursery` … `size-06-terrace`. No code changed —
  the category's prompt already describes this scene.

## [2026-09-30] update | The Omni video is caught and its first 2 seconds cut; the card that blocked the page

- The owner: the step «Фото» froze — a blue frame, no clicks. The video card was not inside a `ws-drop`, so its
  absolute button covered the whole panel. Now it is a card like the others.
- «Книга в руках у людини»: the video from Downloads is caught, ffmpeg cuts its first 2 s into `etsy/video-hands.mp4`,
  the uncut one goes into `originals/`; a video can be dropped on the card; the card plays it; the step is `n/8`.
- `picture()` no longer sends `w=undefined` when asked for the file itself (the video came back as an error).
- Tests: `TheOmniVideo` makes real little videos with ffmpeg.

## [2026-09-30] update | Photo mockups: «Книга в руках у людини» — the owner's Gemini Omni video prompt

- A new category, seventh of eight: `hands` «Книга в руках у людини», the owner's five 9:16 photos (a woman holding
  a blank book) copied into `app/data/photo-mockups/hands/`.
- Its prompt is the owner's own, tested in Gemini Omni, kept word for word (`OMNI_PROMPTS`, plain text).
- A video: nothing is caught, no photo is kept for it, the «Фото» step still counts seven; its card has a film icon and
  a note. Tests — `TheOmniVideo`.

## [2026-09-30] lint | Anchors after the rewrite, the mockups' real sizes, the generator, two questions

- Four links to sections that no longer exist (three into the rewritten Mockups page, one in the roadmap) — fixed;
  `wiki_check.py` doesn't look at `#anchors`, a script did.
- The Mockups page said every picture is 4000×2670, ≈5 MB: book 25's are 3727×2397 / 3227×2248 (5–7 MB), the
  whole scenes 4000×3000 (16–18 MB) — corrected. The tests page still said five photo categories — seven.
- Photo mockups: book 25's came from ChatGPT, not Gemini — the page says either.
- Checked and in order: the numbers on the rewritten pages against the code, the "1 October" rule on every page, no
  page linked only from the index, the built plans each point to their feature page.
- Two questions for the owner in open questions: what of `etsy/` goes into the listing
  (and Etsy's limits), which generator runs in which browser.

## [2026-09-30] update | The wiki's own rules: the present only, one fact — one page, no counts

- The owner agreed to three changes after the review of the wiki: pages say how things are **now** (history in the
  log and decisions), **each fact in one place** with links elsewhere, **no counts** kept by hand
  ([wiki rules](dev/wiki-rules.md)).
- `wiki_check.py` no longer checks the numbers of tests and routes (`stale_numbers()` removed); the pages don't state
  them.
- Rewritten to the present: [Workshop](features/workshop.md) (335 → 210 lines), [Mockups](features/mockups.md)
  (300 → 154), [Text check](features/text-check.md) (the calibration and measurements kept as a short "why").

## [2026-09-30] update | The generation bar no longer comes in again at every part

- The owner: when the next part (a picture, the prompt) went into the clipboard "the whole program blinks". The bar was
  drawn anew with its entrance animation each time; now `paintGenBar()` (workshop-live.js) slides it in once, when a
  wait begins, and the next part only glides its line «У буфері: …» in ([workshop](features/workshop.md)).

## [2026-09-30] update | Photo mockups: the Workshop's step «Фото» and the «Фотомокапи» page; etsy/ in every book

- New [photo mockups](features/photo-mockups.md): seven categories of the owner's templates («Для відео» — three 9:16
  phone photos; «Розмір» — the two formats side by side; a book's «Папка книги» now a blue button beside «Передати в
  бібліотеку») (copied into
  `app/data/photo-mockups` with English names); in a book — template → its reference (Cover 1 / Cover & Open 1 / the
  Canva cover) → a JSON prompt per category, the photo caught into `etsy/photo-<category>`; the page «Фотомокапи»
  (a camera on the rail) — the template and the prompt only.
- **`etsy/`** in every Workshop book, as the owner's book 25: the slides bake there as `Listing N.png`, the Mockups copy
  Cover & Open 1 and All & Open 1 there; the cut-outs' folder is
  `no-background/`; the Mockups keep the Canva cover as `mockups/canva-cover.png`; book 24's hand-made `mokaps/` renamed
  `mockups/`.
- Pages: workshop, slides, mockups, modes, frontend, api-routes, preview, security, testing, code-map, glossary,
  decisions, index.

## [2026-09-29] update | Listing slides: schemes, the Workshop book's folder, locked by default, Dedication without its floor

- The owner's eleven wishes built ([slides](features/slides.md), plan): **schemes** in the
  editor («Схема ▾»: Nature — the default, Night, his own, the other Workshop books' slides as presets; «Зберегти ці слайди
  як схему…»; «Зробити шаблоном» went); **«Тло»** as the bottom layer; **«З інших слайдів»** colours; «Який мокап» without
  the file name; **every element locked by default** (a click selects it, the mouse and arrows don't move it, the lock
  frees it; new ones free); **Dedication** cut without its floor — the desk and the book stay, the shadows kept, its
  frame kept for slide 3.
- **The Mockups go into the Workshop book's folder** (`mockups\`, step 2 «Книга», no dialog; «Інша папка…» still
  there); a book's slides live there (`mockups\slides\`), made again they keep the owner's touches; its page 30 its own;
  the Workshop's «Мокапи» step ticks itself and offers «Редагувати мокапи», «Редагувати слайди», «Відкрити папку мокапів».
- **Cleaning**: the cut-outs' cache and the bake's browser files at launch and close; a book's slides' cache when it is
  passed to the library, its six scenes kept as a preset.
- **Numbering** as his Etsy listings: the rule in `pipeline/GEMINI.md` (= `AGENTS.md`); with Book Studio closed the two
  book folders were renamed 40.spooky-stories → 24.spooky-stories, 41.sleepy-trucks-bedtime → 25.sleepy-trucks-bedtime
  (the agents' file headers too), and the library book passed from Spooky stories points at the new folder (its 31
  pages found).
- Checked: tests (450; `test_slides.py` 26), the preview (the Workshop → the Mockups for the book → «Без фону · 8/8» →
  six slides in the book's folder, the step ticked → the editor: the background row, other slides' colours, a locked
  sticker not dragged, freed and dragged, a scheme saved and put on), a real Dedication cut with the real template.

## [2026-09-29] decision | Listing slides: schemes — Nature and Night recorded

- The owner: a scheme is "not only the colours but the settings of the whole mockup" — the six scenes, named. His
  hand-set colours on «4k Трафарет, копія» saved as **Night**, the template as **Nature** (the default), in
  `app/data/slides/schemes/` (a copy of the six also in `app/data/slides/saved-colours/`). The editor's scheme choice
  and five more touches (the background as a layer, colours from the other slides, no file name in «Який мокап», locked
  by default, Dedication without its wall) agreed, waiting for his word (plan).
- Added the same evening: books numbered as his Etsy listings (№41 → №25), the mockups saved into the Workshop book's
  folder without asking, and the Workshop's «Мокапи» step leading back to the mockups (its folder, the editor),
  ticking itself.
- And: a book's slides tied to its Workshop book instead of a «Зробити слайди» session; temporary files erased when
  the program closes, the book's cache when the book is done; everything in the program's folder (portable).
  A book's slide settings stay for good — presets for other books (e.g. another bedtime book).

## [2026-09-29] update | The examples and a spare copy of the templates in the Book Studio folder

- The owner: "put everything into the Book Studio project folder… and the Photoshop mockups too, to be kept there as
  well", then "only the examples are needed". His desktop folder `moсkup studio` → `examples\` (`Canva resoult`,
  `Photoshop prep`, `Слайди — приклад`; the old external editor to the Recycle Bin); `Трафарети мастхев (копія)\` —
  the templates copied (9 files, sizes equal, marked read-only). Both git-ignored; the copy left out of the backup
  (`backup.SKIP`). The sample set, the skill and the wiki point at the new place ([slides](features/slides.md)).

## [2026-09-29] update | Listing slides moved into Book Studio: «Без фону», «Зробити слайди», the editor, the skill

- The plan's five phases built ([slides](features/slides.md), plan). The package
  `app/studio/slides/` (the cut-out and its background cutter, the template and a book's sets with versions, «Зробити
  слайди», the headless bake) — nothing of it runs at launch; the drawing engine `web/js/slides/engine.js` and the page
  `web/slides/render.html`; Comica in `web/fonts/`; the command line `app/tools/slides.py`.
- The Mockups: every picture Photoshop saves is cut out without background into `Без фону\` (Open 1, Open 2, Cover 1 —
  the others are whole scenes), step 4 «Слайди для лістингу» makes the six (`Listing 1…6.png`) and opens the editor; the
  header's ▣ opens the template's and the last books' slides.
- The editor `#/slides/<set | template>/<1–6>` — loaded only when opened (left out of the warm-up), its own
  `css/slides.css`, Book Studio's look: layers dragged into order, «+», grouped properties with sliders and the slide's
  swatches, «Скинути слайд», «Зробити шаблоном», «Зберегти картинки»; an agent's change in the files shows up by itself.
- The owner's work moved in: the external editor's first design → `app/studio/slides/design/` (slots instead of file
  names, `{pages}` / `{poems}`), his touches → the template, his sample book → the set «Приклад». The external folder was
  only read; the `slide-editor` entry left `.claude/launch.json`. The skill `/listing-slides`; `psd-tools`, `numpy` in
  `requirements.txt`.
- Checked: tests (443, `test_slides.py` 19); «Приклад» baked through Book Studio equals the external tool's six (slide 2 —
  a few pixels); a copy of his real `2. Open 1.png` cut with the real template in ~6 s; the preview — a whole run →
  «Без фону» → «Зробити слайди» → the editor (both themes), a scene file changed on disk shown in the open editor.
  Not checked live: a real Photoshop run handing pictures to the cutter.

## [2026-09-29] update | Mockups: the demo book's own step went — it comes into «Структура»

- The owner: the step «Демо-книга з Canva» and the structure both took the ZIP — a double. The step is gone (the
  steps are 1 Розвороти · 2 Куди зберегти · 3 Photoshop); the structure's veil takes a drop or a click (the Windows
  dialog), its header shows the book, a badge while another comes in and a folder button for another book; a
  book that can't be read is a red line there; «Зробити мокапи» with no book blinks the veil
  ([mockups](features/mockups.md)). Checked: tests; the preview — the three steps, a click on the veil → the
  pretend dialog → the book, the header's button, the blink, «Завершити» back to the veil.

## [2026-09-29] decision | Listing slides: the plan to move them into Book Studio

- The owner asked to bring the slide tool into Book Studio as a separate module called only when needed, in Book
  Studio's style, and a skill for working on slides through an agent. Five phases written down (the engine and
  data, the «Слайди» page, the editor, the skill with live redraw, checks) with three questions and their
  defaults (plan, [decisions](decisions.md)). All six re-baked with his touches first.
- His addition: the Mockups also save every picture **without background** (cut out by the program while Photoshop
  works, into `Без фону\`), then offer «Зробити слайди» — made by themselves — and «Відкрити в редакторі»; no
  separate page in the rail.

## [2026-09-29] update | Listing slides: all six drawn

- Slides 1, 2, 3, 5, 6 measured off the owner's Canva pictures and drawn in slide №4's style; the editor learned
  texts, arrows, flat pictures (a scalloped page), ribbons and a heart, and got a slide switcher
  (plan). Checked: all six baked at 2000², slide 2 opened and edited in the editor.

## [2026-09-29] decision | Listing slides: a hand editor, kept outside Book Studio

- Slide №4 made in the owner's own layout + torn edges, a die-cut sticker (its text fitted by the letters' real
  ink), sparkles, faint leaf shadows. For the "super small" touches — a Canva-like editor (layers, move, rotate,
  resize, Ctrl+Z; every change saved to disk), then "bake" at 2000².
- The owner: not in Book Studio yet — an external tool in `D:\Roman\Desktop\moсkup studio\Slide Editor\`
  (launcher `Відкрити редактор.bat`); the repo gets only the `slide-editor` preview entry in `.claude/launch.json`
  (plan, [decisions](decisions.md)).
- Checked: cut-outs regenerated by `cutout.py` match the prototype's; saving from the editor lands on disk;
  `bake.py slide4` → 2000×2000.

## [2026-09-29] decision | The six listing pictures without Canva — plan and a first slide

- The owner makes 6 square Etsy pictures from the mockups in Canva by hand; agreed: Book Studio's own tool does
  it (no Canva), he picks the mockup per slide, 24 pages / 11 poems, font Comica, full creative freedom
  (plan).
- Solved: cutting the book out of the grey background with its real shadow (the templates' Multiply/Screen
  layers turned into transparent black/white; the outline from `BOOK/OBJECT`'s mask) — checked on Open 1,
  Open 2, Cover 1. Prototype of slide №4 in the scratchpad; no code in `app/` yet.

## [2026-09-29] update | Ready for 1 October: his own Gelato account, Printify read-only, Profit turned on

- **His own Gelato account** — the smooth switch agreed on 2026-09-27: Settings → «Перейти на новий акаунт Gelato»;
  the old key is only read; every sync reads both; an order is dropped only by its own account's whole list
  (`gelato_accounts.py`, `sync._gelato_part()`, [gelato](integrations/gelato.md)).
- **Printify read-only from 1 October 2026** (`printify.retired()`): every book to Gelato, no Printify in the card,
  the Order Creator or the archive's reprint; nothing written there ([printer-rule](rules/printer-rule.md)).
- **Profit** in the rail (Alt+5), only sales and print orders from 1 October; the queue keeps every order
  ([profit](features/profit.md)).
- Checked: 424 tests (`test_gelato_accounts.py`, `GelatoOnly`, `BookkeepingStart`); in the preview — Profit empty
  «Продажів від 1 жовтня ще немає», the Gelato block before and after the switch (the answers stood in by the
  browser, the preview server has no keys), the Order Creator without the switch and the archive's Printify book
  without «Передрук» (1 October stood in the same way). Not checked: a real Gelato key — the switch is the owner's.

## [2026-09-28] decision | Printify "Fulfilled" shows as In transit / Delivered

- The owner: Printify's "Fulfilled" beside Gelato's "Delivered" looked inconsistent. "Fulfilled" only means shipped, so
  the chip now says **In transit**, and **Delivered** once the carrier's `delivered_at` is on every parcel
  (`printify.slim_order()` keeps it now, `printorders.shown_status()`). Stages are unchanged. Unverified: whether
  Printify fills `delivered_at` for the owner's parcels — seen after the next sync.

## [2026-09-28] update | Book 41 opens at once; a held picture names who holds it; Upscayl works on a copy

- **Slow book 41**: `upscale._size()` asked every PNG for its EXIF — Pillow unpacked all 370 pictures, 31 s on the first
  look; now only the header is read — 0.14 s.
- **«WinError 32» on replacing a page** (the owner, book 41, variants Girl_2/Girl_3): the old original was held by
  another program — it stayed held across a Book Studio restart, so not Book Studio itself. Now the Workshop waits
  ~5 s, then names the program (`desktop.file_holders()`, Windows' Restart Manager) and says nothing was changed.
- Upscayl is given a copy of the original, so it never holds the book's file.
- The first real message named **Microsoft Edge — Book Studio's own window**: the pictures were dragged in straight out
  of `originals/`. A picture byte for byte the row's original now replaces nothing — the pages are only cut again;
  an Edge holder gets its own words ("reopen Book Studio"). 405 tests.
- Checked: 404 tests (3 new); the holder lookup live on Windows (named the process holding a test file). Not checked:
  which program held the owner's file that night — the next time the error says it.
- Pages: features/workshop.md, dev/testing.md, code-map.md.

## [2026-09-27] update | Upscaling knows big pictures; the size chip lined up; the viewer on a variant's tab

- **Big pictures**: a page of 2400 px or more (`upscale.BIG`) isn't queued or offered; the pages in `pictures/` are
  measured (`sides()`). Book 41 (read only): Boy_2's originals were upscaled by hand (5824 px) while its pages stayed
  1440 px — such rows are now «Перерізати з великих оригіналів» (cut again, no Upscayl). «Апскейлити решту» and the new
  button count the open tab only.
- **The chip** «✦ ×2 | 2880 px» — the digits in the chip's own face (the display face made «×» jump), every part on one
  line; a size on every picture (upscaled / big / not yet / to be cut again).
- **The viewer** on a hero variant's tab shows the variant's own spreads and cover (its cover didn't open, its spreads
  opened the base book's); «the original» opens the variant's file (`books.open_in_windows(variant=)`).
- Code: `upscale.py`, `routes.py` (`_upscale_start` `keys`, `_open` `variant`), `books.py`, `workshop-book.js`,
  `workshop-rows.js`, `listings.css`.
- Checked: all 401 tests (3 new); in the preview — the chips' parts centred on one line in one face, the variant's
  cover opening in the viewer with its own picture.

## [2026-09-27] update | The variant's tab without «Генерувати варіант»

- The owner: "this one is extra, I do them one by one". The button is gone from a hero variant's tab (`paintRows()` in
  `workshop-book.js`); each row's «Генерувати» stays, the base book keeps «Генерувати всю книгу».
- Checked: all tests; in the preview — the variant's tab without the button, the base tab with it.

## [2026-09-27] update | «Підхопити з папки»: pictures put into originals/ by hand go the usual way

- The owner put book 41's variants' spreads into `originals/variants/<Boy_…>/` and they weren't picked up —
  `originals/` is the Workshop's store, nothing there is read to make pages. Now the rows' heading shows «Підхопити з
  папки (N)» when such pictures (right names, rows without pages) are there: cut, flipped, the cover on its template,
  the variant's hero into place, then upscaled; the files stay where they are.
- Code: `pictures.py` (`left_behind()`, `adopt()`, `place(kept=)`), `routes.py` (`_adopt`, `book.leftBehind`),
  `workshop-book.js` (`adoptBtn()`, `adopt()`).
- Checked: all 398 tests (3 new); in the preview — a variant's spread put into its originals folder, «Підхопити з
  папки (1)», «Підхоплюю…», the pages cut, mirrored and marked «×2».

## [2026-09-27] update | Upscaling in the hero variants too

- The owner: "there's no upscale in the variants" — the agent had read "the hero — no" as the variants too. Now each
  variant's spreads and cover are upscaled like the base book's (its own originals and pages folders, its own marks
  `G2_brunette/spread3`); the hero pictures (`canonical.png`, `hero.png`) still aren't. «Апскейлити решту» takes the
  variants too; the switch shows on the variants' tabs; the chip and ✦ on a variant's spread and cover.
- Code: `upscale.py` (`slots()`, `split()`, `_source()`, `upscale_row()`, `after_place()`), `pictures.place()`,
  `workshop-rows.js` (`slot()`), `workshop-book.js` (`variantCover()`, `upSwitch()`, `missingSummary()`).
- Fixed on the way: a book's page (and the gallery) took the signature of what it was drawn from **after** reading
  the book — an upscale ending in between left «апскейл 0%» on screen for good; now the signature is taken first
  (`routes._get()`, `_list()`).
- Checked: all 395 tests (a variant's spread and cover upscaled, «Апскейлити решту» with the variants); in the
  preview — a variant's spread and cover dropped, both marked «×2», the heading's «апскейл · ще 1» gone after.

## [2026-09-27] update | The Workshop upscales: ×2 by the owner's Upscayl, right after a picture lands; a switch per book

- The owner's answers: just ×2 whatever the size; skipped for the whole book; on by default; the spreads, pages 1
  and 30 and the cover — not the hero or the variants.
- A picture that lands in its row (caught, dropped, «Без полів») goes to be upscaled in the background: its original
  ×2 by Upscayl's engine (upscayl-standard-4x, found by Upscayl's own log), mirrored and cut again, the big pages in
  place of the small ones. The page: the switch «Апскейл ×2», «Апскейлити решту (N)», a chip over each picture
  (progress / waiting / failed / ×2), ✦ «Апскейлити ще раз»; passing to the library names what isn't upscaled.
- Code: new `workshop/upscale.py`; `pictures.py` (`WRITING`, `place()` → `after_place()`, the row's `pic` mark),
  `routes.py` (two routes, the book's `upscale`, the page's sig), `workshop-book.js`, `workshop-rows.js`,
  `listings.css`; `pipeline/playbook/workflow.md` step 4.
- Checked: all 394 tests (14 new, `test_upscale.py`); the real Upscayl found by its log and run by `upscale.py` on a
  test picture in a temporary folder (1456×720 → 2912×1440, the progress read, a Cyrillic path); in the preview — a
  caught spread upscaled and marked «×2», the switch off, «Апскейлити решту (1)», the progress chip. **Not
  checked:** a whole book in the running program on his books (the preview uses a pretend engine).
- Pages: [workshop](features/workshop.md#upscaling), [decisions](decisions.md), roadmap,
  book-console, [api-routes](architecture/api-routes.md), [data](architecture/data.md),
  [glossary](glossary.md), [code-map](code-map.md), [testing](dev/testing.md), [index](index.md).

## [2026-09-27] update | The Workshop: the hero with every spread's prompt, Ctrl+V in Chrome turns to the next part, a cover per variant

- A spread of a book with a hero puts the hero, then the prompt into the clipboard (pages 1 and 30 — the prompt
  alone); **Ctrl+V in Chrome** puts the next part in by itself (`clipboard.PasteWatch`, the keys only looked at);
  «Далі»/F8 stay. The bar and the buttons' tips say so.
- Every hero variant's tab ends with its own cover: one frame for the finished wide cover, brought to the template →
  `pictures/variants/<name>/Cover.png`; «Генерувати» there — the base cover and the variant's hero into the clipboard.
- Code: `clipboard.py`, `workshop/generate.py` (`_items()`, `_hero()`), `pictures.py` (`place()`, `remove()`),
  `rows.py` (`variants()` → `cover`), `workshop-book.js` (`variantCover()`), `workshop-rows.js`, `workshop-live.js`.
- Checked: all 380 tests (4 new); in the preview — the variant's cover caught from Downloads and fitted, a spread's
  hero then prompt in the clipboard, the bar's words. **Not checked live:** Ctrl+V in the real Chrome.
- Pages: features/workshop.md, security.md, decisions.md, dev/testing.md.

## [2026-09-27] update | One place for a Workshop book's pages

- A book passed on from the Workshop takes its cover and pages from the Workshop's folder — no copy in the library
  (`library.follow()`, `asset_path()`, `"pagesFrom": "workshop"`); a page changed there is the library's at once (a
  new address, so no old picture stays cached). The passport only shows them («Змінити в Майстерні»; the server
  refuses a picture write, 409); the thumbnail and texts are its own; export and «відкрити оригінал» read the
  Workshop's files.
- Deleting the Workshop book copies its pages into the library first (`keep_pages()`; the dialog says so). The one
  book passed on before (31 of 31 pages identical) moves onto the Workshop's pages at start-up
  (`link_workshop_books()`), its copies to the Recycle Bin.
- Checked: 9 new tests (`OnePlaceForThePages`); the preview — the earlier book moved over at start-up (11 copies to
  the preview's bin), its passport (only the thumbnail changeable, «ще немає в Майстерні» on empty places), a spread
  dropped in the Workshop shown in the library at once (7 → 8 of 16), «Змінити в Майстерні», a book passed on the
  new way, a passed book deleted in the Workshop — the library kept its cover and all its pages.
- Not checked: the owner's real book (it moves at his next start of the program).
- Pages: features (library, workshop), architecture/data, decisions, dev/testing.

## [2026-09-27] update | Backup of the whole program to Google Drive

- Google Drive for desktop installed (the owner signed in; its cache on `D:\Google Drive Cache`); 7-Zip 26.03's
  `7za.exe` into `app/bin` (the official release, hash checked).
- New `backup.py`: every 3 days on launch — the whole program folder and the mockup templates, with the keys
  readable inside, in one 7-Zip archive under the owner's password to `My Drive\Book Studio — резервні копії`;
  the last 7 and one a month stay. Settings → «Резервна копія». `restore_keys.py` for a restore on another PC.
- Tests: `test_backup.py` (rules and a real 7-Zip run on a made-up folder).
- Pages: features/backup (new), settings, data, security, runtime, api-routes, code-map, testing, overview,
  index, decisions, plans/roadmap.

## [2026-09-27] plan | His own Gelato account: a smooth switch

- Found: swapping the Gelato key would drop the old account's orders — the queue's in-flight orders back to «нове»
  without tracking, and the archive deleting their books' files a few days later (a print order missing from a
  list loaded whole counts as "never went to print").
- The owner chose the smooth switch: the old orders are never forgotten, and for the transition both accounts are
  read (the old key only reads). Planned in the roadmap, not built; his account opens about 1 October; until then
  the key isn't replaced. A scheduled reminder (Mondays and Thursdays) at his request.
- Pages: plans/roadmap, plans/open-questions, decisions.

## [2026-09-27] decision | Profit from 1 October only; Gelato's currencies are other people's orders

- The owner: accounting starts on 1 October and must not include earlier orders — recorded (decisions, open
  questions); not in the code yet, to be done before the page is turned on.
- Checked in his local data (counts only): the Gelato account has 568 orders, most not his; of his 30 Gelato sales
  28 are billed in dollars, 2 (5 August) in euros; the 5 in crowns are none of his. The euro question is closed; the
  wiki's "524 of 561, ~5% low" and "the owner's five orders in crowns" were wrong and are corrected.
- Found: after a switch to his own Gelato account the sync would drop the old account's orders — orders not yet
  marked shipped on Etsy would fall back to «нове». Recorded in open questions, to be handled before the switch.
- Checked in the preview: on every page with pictures (15 pages), no picture is left without its fade-in started.
- Stale line removed: the book's `notes` field (gone in phase 5).
- Pages: decisions, plans/open-questions, rules/reconciliation.

## [2026-09-27] update | Cleanup phase 6: big files cut by job

- Server: `textcheck.py` → the package `textcheck/` (the replay gave the same output, byte for byte); `creator.py`
  → `creator/` with one send frame for Printify and Gelato (`sending.py`); `library.py` → the model and its routes +
  `library_files.py` (the text JSON, the folder import, the export, the guide — its words in `library_guide.md`).
- Interface: the queue and the order card apart; the Order Creator's picker, the passport's dialogs, Settings'
  dialogs, «Додати книгу», the mockups' step 4, a Workshop book's rows and Profit's rows in modules of their own
  (each page 9–40 % shorter); the styles in five files by section; the preview
  server by job.
- Checks: a missing or unused import between the scripts fails `test_scripts.py`; the wiki check wants a name
  defined in the file its line links to — it found eight stale lines (functions moved by the splits), fixed.
- Checked: 357 tests; the preview — every page split compared with the page as it was (the same HTML): the queue
  and the card, the Creator's picker filling the form, the settings, «Додати книгу», the Workshop's gallery and
  book (a picture dropped in and removed, the whole prompt), the passport (a folder imported, the JSON pasted, the
  Canva link, the whole text copied), the mockups with the pretend Photoshop from the book to «Зберегти відкриті»,
  Profit's rows and all 16 panels; the styles' computed values on every page in both themes.
- Found on the way and fixed: the first cut of Profit's rows left a list behind (the state switch) — the panel would
  not open; caught in the preview before the commit; `test_scripts.py` now fails on any such name (`ScriptsImport.test_every_name_is_declared`).
- Pages: code-map, glossary, decisions, plans/cleanup, dev (testing, wiki-rules, preview), architecture (frontend,
  server), features (orders, order-creator, library, mockups, workshop, text-check, profit), flows (order-to-print,
  book-import), rules (sync-policy, book-structure).

## [2026-09-27] update | Cleanup phase 5: one copy of everything, no dead code

- Server: the one-time migrations removed (they had run on the owner's PC: nothing of the old data was left);
  `core.IMAGE_EXTS`, `core.inside()`, `images.flat_rgb()`, `wording.guess_child_name()`/`alike()` instead of 3–5
  copies each; the Workshop's rows from `books.ROWS`; the text check's model lists read one way; an HTTP error's
  reply closed at once; the Order Creator's picker reads `/api/orders` (`/api/creator/etsy-orders` gone — 128 routes).
- Interface: `folder-viewer.js` — the viewer with a page replaced and put back, one for the order card and the Order
  Creator; `order-bits.js` — the proof and its strip, fields, address, printer chip, files' badge and notices, the
  order list's counts and empty states; `lib.js` — `post()` (85 calls), `escBack()`, `notFound()` (no inline
  `onclick`), `confirmChecked()`, `glide()`, `tellBusy()`, one `money()` («-$5.00»). Unused icons, exports and
  leftovers removed; one CSS rule fades every picture in; the Gelato blue written once.
- Tests: `tests/fixtures.py` (one Printify fake, the PNG and print-folder helpers), one stand-in model answer; a new
  test for the mockups' «Зупинити». The mockups: one book slot, one stop event, `_run_script()`.
- Checked: 352 tests; the preview — the order card (the proof, fields, address, a page replaced and put back, Esc,
  a card that can't open), the archive's book, the Order Creator (the picker, the structure viewer with a page
  replaced), the Gelato and Printify colours in both themes, the dialog with a box to tick, every page opens.
- Not checked live: the pictures' fade in a visible window (the hidden preview doesn't decode pictures) — the rule
  is the same one for every page.
- Pages: architecture (frontend, data, runtime, server, api-routes), features (orders, order-creator, archive,
  library, mockups, text-check), flows/order-to-print, integrations/gelato, security, code-map, glossary, recipes,
  dev/testing, decisions, plans (cleanup, open-questions), index.

## [2026-09-27] update | Cleanup phase 4: no blinking

- The queue and the archive list are drawn once; a search hides rows (no thumbnail reloads, no entrance replayed per
  letter). The order card's flow, the Order Creator's step cards and structure, the passport's regions and rows, the
  mockups' templates — redrawn in place (`patch()`), each part keeping the pictures it already showed.
- A replaced page reloads only its own pictures (`pageVersion()`, per-page versions instead of one stamp); the strip
  keeps its place. A text-check finding slides in once (`markSeen()`; the alarm's state no longer written inside a
  render). The Workshop's one-shot animations go on after the redraw; an open text step is fetched again only when
  its file changed (`versions()` now tags every file). `enterOnce()`, `patch(…, redraw)` in lib.js.
- Found on the way and fixed: a name declared twice in creator.js, and the passport's local `patch()` (an HTTP PATCH)
  renamed `saveBook()` — its new name first clashed with a parameter. `node --check` let the first through (a `.js`
  file isn't parsed as a module): `test_scripts.py` checks every script as one now.
- Checked: 355 tests; the preview — the queue's and the archive's search keep their rows, the Order Creator's
  Printify/Gelato switch keeps its cards, the passport's text edit and cancel, the Workshop's text step, the mockups.
- Pages: architecture/frontend.md, features/orders.md, features/order-creator.md, features/archive.md,
  features/library.md, features/workshop.md, features/mockups.md, dev/testing.md, plans/cleanup.md.

## [2026-09-27] update | Cleanup phase 3: the waits made shorter

- Text check: the model is loaded only when a question isn't answered from memory (`_Run.ready()`); answers are kept
  by the page's content (`_digest()`), so a book dropped again asks only about its changed page; a page's JPEG made
  once per check; the card warms the model after a replaced page.
- Files: `images.check_png()` reads a file once per version of it and, for the page's own check, makes its 1400 and
  360 px previews from that decode (`VIEW_SIDES`); a replaced page is the only one read again; `images.digest()`
  replaces `sha256_file()`; the archive copies the previews already made (`copy_previews()`). The folder cache,
  `_forget_validation()` and the background preview reader of creator.py went.
- The Gelato PDF written straight into its file (`_Page`, `_blank_png()`), no temporary copies, the same bytes;
  pikepdf named as the engine and added to `requirements.txt` and the launcher's check. Printify uploads built as
  bytes (`httpc.request(json_bytes=…)`).
- Workshop: folders by `os.scandir`, a book page's parts once, the gallery's thumbnail version from one stat; the
  generation mode started only when used (`generate.status()`, `generate.stop()`); the background look asks
  `/api/workshop/gen` only. The clipboard's PNG saved at `compress_level=1`. Library pictures stored outside the lock
  (`library._put_asset()`).
- Interface: module preload hints in `index.html`; `patch()` removes gone parts first and moves with `moveBefore()`;
  `flip()` measures every card before animating; `setProgress()` — bars by transform; the lightbox writes its zoom
  label only when it changes and measures its stage once per size; `toggleText()`.
- Checked: 354 tests (5 new); the PDF compared byte for byte with the old way on a 30-page book; the preview — the
  Workshop's search, the archive's viewer, no console errors. Not checked: a real Gelato send (the same bytes).
- Pages: features/text-check.md, features/order-creator.md, features/orders.md, features/archive.md,
  features/workshop.md, features/library.md, integrations/printify.md, architecture/frontend.md,
  architecture/api-routes.md, architecture/runtime.md, code-map.md, dev/setup.md, overview.md, recipes.md,
  plans/cleanup.md, dev/testing.md.

## [2026-09-27] update | Cleanup phase 2: matching and money rebuilt, the Profit page ready for 1 October

- New modules: `printorders.py` (one reading of a print order), `records.py` (the files), `stages.py` (the queue's
  stages, once per view), `sync.py` (pulling the orders); `profit.py` is the Profit view only; `reconcile.py`
  matches one receipt at a time, numbers before names; `outcomes.py` works out the money once (`rows()`). The
  archive ↔ profit cycle and every late import between them are gone.
- The accounting items deferred on 2026-09-23 fixed: only placed and paid orders cost money; crowns, pounds and
  zlotys converted at the ECB's rates (a currency without one is never dollars); the cover type from the buyer's
  choice only; a cancelled first order keeps the second one's cost. The euro's rate left for the owner.
- Also: the order card reads its order and the archive once (`stages.picker_order()`, `archive.card_facts()`); the
  queue reads the printer rules once (`orders.printing()`); refund notes unescaped; nothing unescaped twice;
  dropped receipt fields (the buyer's e-mail among them); `gelato.SHIPPED` → `printorders.GELATO_SHIPPED`.
- The Profit page: icons and the shared tips, no emoji or English, classes instead of inline styles, «Не оплачено»
  and the currency state.
- Checked: 349 tests (13 new: `MatchingOrder`, `MoneyRules`, `PickerFacts`, the name index against the rule, the
  cover, the pounds); the golden parity test kept, the pound rows marked; the Profit page on the preview server.
- Pages: rules/reconciliation.md, rules/order-stages.md, rules/sync-policy.md, features/profit.md,
  features/archive.md, features/orders.md, architecture/api-routes.md, architecture/data.md,
  architecture/runtime.md, code-map.md, glossary.md, flows/order-to-print.md, integrations/*.md, recipes.md,
  decisions.md, plans/open-questions.md, plans/cleanup.md, dev/testing.md.

## [2026-09-26] update | Cleanup phase 1: 22 bugs fixed, each with a test

- Money and safety: `httpc.request()` reads a reply cut short as "result unknown"; the Etsy callback page escapes
  the link's text; Gelato's link goes to the registry as soon as the draft exists; Printify uploads every book's
  pictures before making any book; a full Etsy read keeps each receipt once.
- The rest: Esc in a Workshop dialog stays in the book; «Готово · N картинок» in the title (the shell alone writes
  it); «Стоп» during placing stays a stop; the variant checked before anything is written; `_work/` in the book
  check's key; no `.tmp` left by a locked page (`core.replace_file()`); `Request.int_param()` for numbers in a
  query; no deleting a library book mid-import; the Order Creator's badge per book, its running guard and its
  debounce cancelled on leaving; a ZIP or folder dropped on a passport slot is an import; the text check caches
  no broken answer and never retries a timeout; the Profit page's saved period and its poll; dropped folders kept
  a day unused; one `remembered()`/`remember()` for the pages' own preferences.
- Checked: 336 tests (14 new), the wiki check; the preview — every page opens without a console error, Esc in the
  Workshop's dialog, the done title. Not checked: a real send (tests and fakes only, as always).
- Pages: plans/cleanup.md, decisions.md, security.md, architecture/server.md, architecture/frontend.md,
  features/order-creator.md, features/text-check.md, features/library.md, features/workshop.md,
  features/mockups.md, flows/dropped-files.md, rules/sync-policy.md, dev/testing.md.

## [2026-09-26] decision | The big cleanup agreed: every finding of the code study to be fixed

- The owner, after the study (7 parallel audits, report as a private page): "fix everything you found — a
  flawless app; the wiki and GitHub up to date". The parallel mockups work committed, `book-console` merged into
  `main` and pushed; the work goes on in the branch `cleanup`, merged after every phase.
- The plan and its progress: plans/cleanup.md. Pages: index.md.

## [2026-09-26] update | Mockups: Dedication left open for its background and table colours

- The owner: Dedication must stay open too — he picks the background and table colours there.
- `mockups.py`: `"keep": "colours"` on Dedication, `kept_open()` (hand or keep), no automatic Dedication shot, the
  kept ones last in `RUN_ORDER`; `state()` passes `keep`. `mockups.js`: ✋ on Dedication with its own tip, «6
  картинок, а 4 шаблони…», the turn card names Dedication's colours.
- Checked: the mockups tests updated (6 saved, 4 open, Dedication filled and open, saved by «Зберегти відкриті»);
  the preview — a whole run and «Зберегти відкриті» (4 pictures, Dedication among them). Not checked: the real
  Photoshop. Pages: features/mockups.md, plans/listing-mockups.md, decisions.md.

## [2026-09-26] update | The «Ще раз» icon redrawn

- The owner: the «Ще раз» button "looks broken" — the `regenerate` arc and its arrowhead were two loose strokes.
  Now one line runs from the arc into the arrowhead's corner (`icons.js`), the `sync` icon's family.
- Checked: the preview, the button and the icon large, light theme. Pages: none beyond this log (the icon's
  meaning in architecture/frontend.md is unchanged).

## [2026-09-26] update | Mockups: the book's Cover opens in Photoshop; «×» finishes the page

- The owner: open the Cover image in Photoshop beside the PSDs left open; a cross on the Mockups page to finish.
- `mockups.py`: `plan()` names the cover's copy (`Cover.png` in the run), `prepare()` copies it, `script()` and
  `finish_plan()` pass it on, `make()` says `coverOpen`, `pending()` skips a `dismissed` run; `close()` and the route
  `/api/mockups/close`. `mockups.jsx`: `openCover()` after the templates, `closeCover()` in the second script (only
  an unchanged one); `findOpen()`'s double `path` renamed. `mockups.js`: the header's `.tools` with «×»,
  `finishPage()`, the turn card names the cover. The preview's pretend Photoshop "opens" the cover too.
- Checked: 324 tests (the pretend Photoshop opens pictures and knows a changed document; new: the cover opened last
  and left open, a missing cover told, the second script closing only an unchanged cover, «×» forgetting the run and
  the book, waiting for a run); the preview — a whole run, the card, «×» with its question, a reload with nothing
  offered. Not checked: the real Photoshop. Pages: features/mockups.md, api-routes.md, decisions.md, index.md,
  dev/testing.md.

## [2026-09-26] update | Workshop: the book's folder in the header; a picture dragged from the page never drops in

- The owner: the header's folder must be the book's folder (not behind «Ще»), the originals — a separate button with
  a wide picture; and a spread dragged a little and let go on itself replaced itself with a cut square.
- `workshop-book.js`: the header's group — agent │ the book's folder │ the pages (`images`) │ the originals (new
  icon `original`) │ «Ще» (delete only). `app.js`: a drag that starts in the window is shut out of every drop zone
  while it carries files (the browser hands a dragged picture over as a file) — the Workshop, the passport, the
  order card alike; the mockups' own drags carry no files.
- Checked: 319 tests; the preview — the header's icons; a drag started on a spread's own picture and let go on it:
  no highlight, no upload; a file from outside: taken as before. Pages: features/workshop.md,
  flows/dropped-files.md, architecture/frontend.md.

## [2026-09-26] update | Mockups: Photoshop stopped the script — "Error 25: Expected: )", fixed

- The owner's screenshot: line 474, `t.file.replace(/^.*[\\/]/, "")` in `findOpen()` (added on 2026-09-23 after the
  last working run). Photoshop 2019's ExtendScript ends a regex at a `/` inside `[...]`, so the whole script failed
  to parse — before its first status, so Book Studio only saw "Photoshop asks about the script". Node (the tests'
  pretend Photoshop) reads it fine, which is why the tests passed.
- `mockups.jsx`: the name cut with `lastIndexOf`. A new test reads the script for a `/` inside a regex class.
- Checked: 319 tests. Not checked: the real Photoshop — the owner's run. Pages: features/mockups.md, dev/testing.md.

## [2026-09-26] update | The Workshop redrawn in Book Studio's style; new icons, no magic wand

- The owner: the Workshop's icons, fonts and text look like another style; go over the typography everywhere; redraw
  the icons, the magic wand especially.
- `icons.js`: `agent`, `workshop`, `mirror`, `guides` redrawn; `prompt` (the wand) → `>_`; new `generate`,
  `regenerate`. `workshop-book.js`: the header's actions → one group of icons; the rows' heading → the section
  title; the rows' three dots removed; drop zones → the passport's; the cover's guides → an icon toggle.
  `app.css` (`.ws-*`): sizes on the program's scale, square step markers, the dotted endpaper.
- Checked: 318 tests; the preview (sandbox) — the gallery, books 40 and 41, a row, an empty frame, the cover, the
  hero's panel, the generation bar, both themes, at 1:1. Not checked: the owner's own screen. Pages:
  features/workshop.md, architecture/frontend.md, owner/ui-principles.md, decisions.md.

## [2026-09-26] update | «Відкрити агента» wrote books into the prototype's folder — fixed

- The owner: "on opening the agent it saves books into the old directory of the separate module". Found: Antigravity
  2.17 ignores the folder it is started with; a new chat ran in its last picked project, the prototype's
  `Book Console`, so book 40 was written into `D:\Roman\Desktop\Book Console\books` (then copied into
  `pipeline/books`).
- `books.agent_words()`: the clipboard's words carry the full paths (the rules `…\pipeline\GEMINI.md`, the book's
  folder); Antigravity is only started. The toasts and tips of «Відкрити агента» / «Нова книга» say so.
- Checked: 318 tests (a new one for the words). Not checked: the real Antigravity window. The owner, once: a project
  on `Book Studio\pipeline` in Antigravity. Pages: features/workshop.md, plans/book-console.md, decisions.md,
  code-map.md, dev/testing.md (its Workshop row brought up to date).

## [2026-09-26] update | The book console moves into the Workshop (branch book-console)

- The owner: "create a new branch on GitHub and integrate the console into the Workshop — a plan, then the
  integration". The plan — plans/book-console.md.
- The pipeline moved into the project (`pipeline/`: the agents' rules with a Book Studio fork, the playbook, notes,
  listing prompts, `check_book.py`); its `books/` kept out of git. The root `AGENTS.md` got a fork for book agents.
- The Workshop rebuilt as the console: `app/studio/workshop/` (books, rows, pictures, generate, check, routes),
  `clipboard.py`, the Recycle Bin and «Зберегти як» in `desktop.py`, `core.SANDBOX`; the old Workshop model
  (`stage`/`prompts` in the library, the JSON, the instruction) removed; passing to the library copies the pages and
  texts into a new library book (a job).
- The page: the gallery and a book's page live (`workshop-live.js`, `patch()` — a redraw in place that keeps
  pictures), the generation bar, the rail's dot and the window's title while a picture is awaited elsewhere.
- Tests: 52 of the Workshop (the prototype's, ported, plus the library and the sandbox), 317 in all; checked in
  the preview on made-up books in both themes. Pages: features/workshop.md (rewritten), plans/book-console.md (the
  steps page folded in and removed), decisions.md, glossary.md, code-map.md, api-routes.md, data.md, frontend.md,
  modes.md, runtime.md, preview.md, testing.md, security.md, library.md, overview.md, index.md, roadmap.md.

## [2026-09-26] update | Book console: the cover's margins by the printer's template; deleting a book

- The owner gave the printer's cover template (8×8 hardcover, Printify SKU 11688-12031). The console now lays the
  cover's picture on it by width (`rows.TEMPLATE`, `template_layout()`, `template_guides()`), shows its lines, and
  brings the outpainted cover to 5370×2850 px, 300 dpi (`place.fit_template()`); the − / + margin control is gone.
- «Видалити книгу» on a book's page: the folder to the Windows Recycle Bin (`dialogs.to_recycle_bin()`,
  `books.delete_book()`), a question in the console's own look (it also replaced the browser's confirm on removing a
  picture). Found and fixed on the way: the delete button did nothing after the question (the event forgot its
  button after the wait).
- Checked: 46 tests; the sandbox preview (a real-size 5824×2880 cover on the template, deleting two made-up books);
  the real Recycle Bin with a made-up folder. Pages: plans/book-console-steps.md, decisions.md.

## [2026-09-26] update | Book console after the first real book: polish, downloads moved in, the cover's margins

- The owner made his first book in the console ("it all works really great") and asked: polish the interface and
  the flow; remove the listing photos (and the cover's mockup/reference); move a download out of Downloads into
  the program, a way to the cut pages' folder, save any picture anywhere; the cover as the last card in two
  stages with an outpaint of added margins.
- Built in `Book Console/console/`: `originals/` (a download moved there, named by its row), `pictures/` opened by
  «Сторінки», «Зберегти як…» on every page, «Копіювати картинку»; the cover's two stages (`cover_state()`,
  `build_expanded()`, `outpaint_prompt()`, `set_margin()`, `skip_margins()`, the old Cover.png migrated); pictures
  with versions (no blinking), the queue's progress, following the waiting row. The listing photos and the
  picking of files removed; `GEMINI.md`/`AGENTS.md` and `playbook/workflow.md` say `originals/` instead of
  `listing/` and describe the margins.
- Checked: the sandbox preview in both themes, 43 tests. Not checked: Gemini's real outpaint, the window on the
  owner's screen. Book Studio's code not touched. Pages: plans/book-console-steps.md, decisions.md.

## [2026-09-26] update | Book console prototype, steps 7–15: the generation mode and everything after it

- The owner: "the rest in a row, without steps". Built in `Book Console/console/`: «Відкрити агента»
  (Antigravity on the root, the book's line in the clipboard); a picture into a row by hand (cut, flipped, ⇄,
  replace, remove — the old copies to `.replaced/`); «Генерувати» for a row and for the whole book (the program's
  own clipboard, Downloads watched and only copied from, the next prompt ready after each catch); the hero, the
  cover (mockup → reference → prompt, «Далі» or F8), the listing photos (the book's mockup → prompt → ChatGPT's
  JPEG), the Canva folder and the Workshop's JSON, hero variants (tabs, `agent/variants/<name>/` — the rule added to
  `GEMINI.md`/`AGENTS.md`). New: `pult/gen.py`, `place.py`, `winclip.py`, `dialogs.py`, `paths.py`; a sandbox for
  the preview and the tests.
- Checked: the sandbox preview (a whole book caught row by row, mirroring and cutting, a listing photo, a variant),
  39 tests; the real clipboard and F8 briefly (the owner's clipboard put back). Fixed on the way: a kept copy
  overwritten by a second replacement in the same second; a variant's spread starting without its base. Not
  checked: a real Gemini/ChatGPT download and paste, the Antigravity window. Step 16 waits for the owner's book.
- Book Studio's code not touched (the preview entry added and removed). Pages: plans/book-console-steps.md,
  decisions.md.

## [2026-09-26] update | Book console prototype, steps 5–6: the book's rows and the GO check

- `console/pult/rows.py`: the 17 rows (prompt · 2:1 frame · text), read from the agents' files the way the old
  `build_workshop_json.py` read them; short or broken prompt files named above the rows. The page shows them in a
  820 px column under the strip, prompts folded and copyable, `{Name}`/`{Gifter}` marked; the step's panel folds.
- The book check in the window: `check_book.run()` (the rules unchanged) once any prompt file is there, cached until
  an agent's file changes; GO / «N помилок» on the strip, on the card and in the «Перевірка» tab.
- Found while checking: a broken line in `check_book.py` after adding `run()` (fixed; the report compared with the
  old validator again — the same); a style name clash that shrank the empty frames (fixed).
- Checked: made-up books in the preview (rows, live text fix, GO on a copy of book 39's files in `.tmp`, 10 errors
  on another); 25 tests. Book Studio's code not touched (the preview entry added and removed). Pages:
  plans/book-console-steps.md.

## [2026-09-26] update | Book console prototype, steps 3–4: the window, the book list, the path strip

- `Book Console/console/`: `Book Console.pyw` + `pult/` (a stdlib server on 127.0.0.1:47850 with a session token,
  its own Edge window closed like Book Studio's, temp files in `console/data/tmp` on D), `web/` (Book Studio's
  look in the Listings cyan), the desktop shortcut «Пульт книги» with its own icon. The book list (cards: number,
  title, the cover's title, thumbnail, a 10-step bar, «Далі», «Картинки n/16») and a book's page with the path
  strip ticked by the files, a panel per step (the agent's file, the hero, the 16 rows), Canva/Mockups/Library
  ticked by hand into `book.json`; the page redraws itself within 1.5 s of a file changing.
- Pictures count 16 rows, the cover is its own step (the plan said `n/17`). Found and fixed while checking: an
  unread request body broke the next request on the same connection (`{}GET` → 501).
- Checked: made-up books (`console/dev_server.py --sample`) in the preview — list, strip, panels, live ticks,
  marks, light theme, refused paths and missing token; 15 tests (`console/tests`); the real launcher without a
  window. Not checked: the window on the owner's screen. Book Studio's code not touched (a preview entry added
  to `.claude/launch.json` for the check and removed). Pages: plans/book-console-steps.md, plans/book-console.md.

## [2026-09-26] update | Book console prototype, steps 1–2: the folder, the clean copy, the agents' rules

- The owner: «роби»; the folder `Book Console` — yes, `seo-intelligence` — not taken, no git until the move.
- `D:\Roman\Desktop\Book Console`: the playbook, `notes/discoveries.md`, the three listing prompts + README
  copied; the old pipeline checked unchanged (4443 files, the same sizes and times). `GEMINI.md` = `AGENTS.md`
  (book agents, files only in `books/<n>.<slug>/agent/`, numbers from 40), `CLAUDE.md` — the fork for coding
  agents, `console/check_book.py` — the old validator reading `agent/` (the same report on a copy of book 39).
  Every `BOOKS_NEW/…/_work` path, `workshop.json`, slicing, flipping and cover-splitting instruction rewritten.
- Book Studio's code not touched. Pages: plans/book-console-steps.md, plans/book-console.md, decisions.md.

## [2026-09-26] decision | The book console prototype: its look and its steps

- The owner: start the prototype — a plan first, no code. The agent's proposal: the folder
  `D:\Roman\Desktop\Book Console` (name to confirm), a clean copy of the pipeline's playbook, one folder per
  book with `agent/` (only agents write) and `pictures/` (only the console writes), the console as the
  Workshop's book page on its own small server in its own window; Downloads (`D:\Roman\Downloads`) only
  read, a caught file copied. 17 small steps (0–16), each with what the owner sees — new temporary page
  plans/book-console-steps.md (a temporary page, folded into plans/book-console.md on the move); step 0 done. Nothing built until «роби».
- No code changed. Pages: plans/book-console-steps.md, plans/book-console.md, index.md.

## [2026-09-25] decision | The book console planned: the pipeline and the Workshop as one place

- The owner: into the roadmap, a prototype apart from Book Studio first, then a separate branch; only planning
  for now. New page plans/book-console.md: the path strip, the generation mode
  (Downloads → the row, the next prompt in the clipboard), hero variants, the pipeline moved in cleaned (agents
  write only into `agent/`), the catches. His agents run in Antigravity; spreads — Gemini (PNG), listing photos —
  ChatGPT (JPEG). No code changed. Pages: plans/book-console.md, plans/roadmap.md, index.md.

## [2026-09-25] decision | No image API; bold ideas around the ChatGPT chat recorded for discussion

- The owner generates on the websites — spreads in Gemini, listing photos in ChatGPT (subscriptions), no paid API; Tier H heroes swapped per order,
  every look made in advance — later. Ideas under discussion in plans/roadmap.md: a live bridge to
  `Etsy-Book-Pipeline`, catching downloads into Workshop rows, a hero-swap helper in the order card, listing
  photos. No code changed. Pages: decisions.md, plans/roadmap.md.

## [2026-09-25] decision | The plans reviewed with the owner: kept, turned down, new

- An agent offered ten ideas; the owner answered each. **New in the plans:** the ship-by date as a quiet line
  on a new order's card; upscaling right after a drop in the Workshop; a clean slate for accounting on
  1 October; an automatic encrypted backup of the whole program to Google Drive; maybe the listing's texts by
  Gemma (a test first). **Later:** pages from the library instead of Canva. **Covered already (to confirm):**
  the "product already created in Printify" mark — the queue's `On hold` / `Draft` chip.
- **Turned down:** upscaling for orders, a demo book without Canva, a character-consistency check, a
  print-quality journal, profit by book — reasons in decisions.md.
- Checked in the code: accounting has no requests of its own (one sync feeds the queue too); Etsy's
  `expected_ship_date` isn't kept by `normalize_receipt()`; the vault's DPAPI won't open on another PC.
- No code changed. Pages: plans/roadmap.md, decisions.md.

## [2026-09-25] update | The flaky test fixed: a send's folder check no longer warms previews in the background

- About one full test run in five ended with `PermissionError` in
  `GelatoDraftFlow.test_an_unclear_draft_keeps_its_files_reachable` and left `.tmp\tmpXXXX` (Cover.png, 5–9.png…):
  `creator.validate()` started the background preview warm-up, which was still reading a page when the test
  removed its folder (Windows can't delete an open file).
- A real race, not only the test's: a send's own check (no job) is followed by the PDF or the uploads reading
  every file anyway. Now only the check the page asks for warms previews (`_warm_in_background()`); the
  order card's strip and viewer are as fast as before. Test `test_only_the_pages_check_warms_the_previews`.
- Checked: 10 full runs in a row (284 tests) — no error, nothing left in `.tmp`.
- Pages: dev/testing.md, features/orders.md.

## [2026-09-25] update | Gelato blue again in the Order Creator

- Since Orders turned orange (2026-09-24) the Order Creator's Gelato mode had taken the orange too; the owner
  asked for the blue "як було". `app.css`: `.creator.mode-gelato` sets the old accent (light and dark).
- Pages: [architecture/frontend.md](architecture/frontend.md), [features/order-creator.md](features/order-creator.md).

## [2026-09-25] update | No "?" on the card's printer chip; carrier and tracking number copy separately

- The owner: the "Printify? · 24 стор." question mark was needless — removed (`renderPlan()`).
- The tracking chip: a click on the carrier copies the carrier, on the number — the number (`trackChips()`,
  `.ord-track` hover underline in `app.css`). Pages: [features/orders.md](features/orders.md),
  [rules/printer-rule.md](rules/printer-rule.md).

## [2026-09-25] update | Gelato draft with a dead file link: a refused Cloudflare tunnel was taken for the address

- A real order's Gelato draft (its number and the child's name stay out of the repository): cloudflared failed
  to get a quick tunnel, its error line with
  `https://api.trycloudflare.com` matched the address pattern, the draft went out with
  `https://api.trycloudflare.com/book.pdf` — Gelato could never load it.
- `tunnel.py`: `_URL_RE` skips `api.`; no address → `TunnelError` at once (also when cloudflared exits),
  cloudflared's last lines in `app.log`; no draft is created. Test in `test_flows.py`.
- Page: [integrations/gelato.md](integrations/gelato.md).

## [2026-09-25] update | A hardcover's printer is decided by its files (24 → Printify, 28/30 → Gelato)

- The owner, because of Printify's faulty prints: for now every hardcover goes where its files say;
  softcovers (and the small one) stay Gelato's; the US rule is only the suggestion in the queue.
- Code: `orders.py` (`plan_for()` → `choice`, `provider_by_pages()`, `_files()` takes `provider: "files"`),
  `orders.js` (`byFiles()`, `decided`, the "Printify?" chip), `order-bits.js` (`planText()`, `pagesText()`
  "24, 28 або 30"); tests in `test_orders.py`.
- Pages: [rules/printer-rule.md](rules/printer-rule.md), [features/orders.md](features/orders.md),
  [flows/order-to-print.md](flows/order-to-print.md), [decisions.md](decisions.md), api-routes, testing.

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
  agreements — plans/listings-mode.md, [decisions](decisions.md)). Branch
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
- New page: plans/listing-mockups.md. Updated:
  plans/roadmap.md, [decisions.md](decisions.md), [glossary.md](glossary.md),
  [security.md](security.md) (rule 10), [owner/working-with-owner.md](owner/working-with-owner.md),
  [integrations/canva.md](integrations/canva.md), plans/open-questions.md,
  [index.md](index.md), `AGENTS.md`. Corrected: `psd-tools` does read the large templates (the
  2026-09-19 "over ~350 MB" note). No code changed.
- **Photoshop scripting check** (on copies of two templates, made-up pictures): a `.jsx` launched from
  outside runs after a "run this script?" confirmation; replacing smart-object contents by layer name,
  swapping spreads and saving PNGs works — 11 s for two templates; hidden layers become visible when
  selected by a script; `Cover & Open 1`'s visible top copies change nothing. Results — in
  plans/listing-mockups.md.

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
  [index.md](index.md), plans/open-questions.md.

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
  [decisions.md](decisions.md), [index.md](index.md), plans/open-questions.md.

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
  plans/roadmap.md.

## [2026-09-20] decision | Replacing a fixed page — from the viewer

- Discussed with the owner and recorded in the plans: replacement buttons in the viewer (two per
  spread), the native file-picker window, re-checking only that page, "Undo", both in the card and in
  the Order Creator. Waiting on his "go ahead". Also recorded there: the requirement to clear "not an
  error" marks when new files arrive.
- plans/roadmap.md, [decisions.md](decisions.md).

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
  [decisions.md](decisions.md), plans/roadmap.md,
  plans/open-questions.md.

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
  plans/roadmap.md.

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
  (21 days); minor fixes from plans/open-questions.md. Decisions —
  [decisions.md](decisions.md).
- Updated: [features/text-check.md](features/text-check.md), [features/orders.md](features/orders.md),
  [features/settings.md](features/settings.md), [features/library.md](features/library.md),
  [architecture/api-routes.md](architecture/api-routes.md), [architecture/frontend.md](architecture/frontend.md),
  [architecture/data.md](architecture/data.md), [architecture/runtime.md](architecture/runtime.md),
  [code-map.md](code-map.md), [dev/testing.md](dev/testing.md), [index.md](index.md).

## [2026-09-19] query | Code review: why it stopped feeling smooth, flaws found

- At the owner's request — an analysis of code quality and smoothness (no code changes): the server is
  fast, the main suspect is the model sitting on the graphics card during and after the text check; the
  list of flaws and the order to fix them — plans/open-questions.md.

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
  plans/roadmap.md, [dev/testing.md](dev/testing.md), [dev/preview.md](dev/preview.md),
  [overview.md](overview.md), [index.md](index.md).

## [2026-09-19] decision | Ideas: pages without Canva, listing mockups via a Photoshop script

- Recorded at the owner's request ("we'll build it later"): the program draws its own pages and
  dedications (with Gemma's help), first as a "lab"; researched tools for Linux; listing mockups — a
  Photoshop CC 2019 script fills in the templates' pages, the owner still makes the covers himself.
  plans/roadmap.md. No code changed.

## [2026-09-19] query | Thoughts: the text check as a program feature

- At the owner's request ("too early to build, just write it down") — what a check button in the order
  card could look like, what to compare against, the steps, and open questions:
  plans/roadmap.md.

## [2026-09-19] update | Cut-off text: Gemma always finds it

- Two pages with text running off the edge (including a name that vanished entirely) — found in every
  variant. plans/roadmap.md.

## [2026-09-19] update | Words stuck together: blind transcription can "add" a space; Qwen — dropped

- Page "Isabellawalked": Gemma without a hint missed it at 1024 px, with a hint it always found it. The
  design for the future feature — a hint plus the program's own comparison (6/6 at every size). The owner
  decided to drop Qwen. plans/roadmap.md.

## [2026-09-19] update | The GPU: both models already run at full load, parallel processing — twice as fast

- Both models run 100% on the GPU; Qwen is louder because it reads the picture at full resolution. The
  owner turned on `OLLAMA_NUM_PARALLEL=4`: a hard test with 4 pages at once — 10.3 s, the same result.
  Updated plans/roadmap.md, [owner/working-with-owner.md](owner/working-with-owner.md).

## [2026-09-19] update | A hard test on the owner's own pages: Gemma 5/5, no false positives

- 12 pages from real Canva templates (5 with mistakes, 7 clean, 2 of which were a real book the owner
  planted himself). Gemma 4 12B QAT: blind transcription plus the program's comparison — every mistake,
  no false alarms, even at 768 px, ~1.5 s per page; Qwen 3.5 9B was weaker. No code changed. Results —
  plans/roadmap.md.

## [2026-09-19] update | Gemma 4 12B QAT: the text-check test passed in full

- Installed `gemma4:12b-it-qat` at the owner's request (on D). The same test: both methods with no
  mistakes (with a name hint — like Gemini; blind transcription 3 of 3), ~1–3 s per page. It's now the
  main candidate. No code changed. Updated plans/roadmap.md.

## [2026-09-19] update | A local model installed (Ollama + qwen3.5:9b) and tested

- At the owner's request: Ollama in `D:\Programs\Regular\Ollama`, the model `qwen3.5:9b` on drive D.
  Tested on the same pages used for Gemini: with a name hint the model "corrects" the mistake in the
  name; blind transcription plus the program's comparison — every mistake found, ~2.5 s per page. No
  code changed.
- Updated plans/roadmap.md, [owner/working-with-owner.md](owner/working-with-owner.md)
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
  [glossary.md](glossary.md), [code-map.md](code-map.md), plans/roadmap.md,
  [dev/preview.md](dev/preview.md), [dev/testing.md](dev/testing.md), [index.md](index.md).

## [2026-09-18] decision | Plan: "Order archive"; the program only runs on the Wrocław PC

- Agreed with the owner (no code changed): a separate "Order archive" menu with the files of books that
  went to print, comparison, and reprints; auto-deletion 14 days after "Sent", a "Don't delete" button,
  new orders only — plans/roadmap.md, [decisions.md](decisions.md),
  [glossary.md](glossary.md).
- The owner doesn't run Book Studio on the Kyiv PC: clarified in [overview.md](overview.md),
  [owner/working-with-owner.md](owner/working-with-owner.md), [integrations/etsy.md](integrations/etsy.md);
  removed the question about a Kyiv-PC copy from plans/open-questions.md.

## [2026-09-17] decision | Text check via Gemini — into the plans

- Discussed and tested on made-up pages (3.6 / 3.5 Flash found every planted mistake; 3.8 / 3.7 Flash
  were overloaded). No code changed; the owner saved the key `gemini_api_key` in the program's vault.
- The owner deferred building it; the free tier, only pages with text (up to 17). Plan —
  plans/roadmap.md, the decision and Google's EEA terms — [decisions.md](decisions.md).

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
  [glossary.md](glossary.md), [decisions.md](decisions.md); the idea removed from plans/roadmap.md.

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
  [architecture/data.md](architecture/data.md), [security.md](security.md), plans/open-questions.md,
  [glossary.md](glossary.md), [code-map.md](code-map.md), [recipes.md](recipes.md), [index.md](index.md).

## [2026-09-17] ingest | The owner's answers about the "truck" tab and statuses

- The truck — a fourth tab between "In progress" and "Sent": the printer has shipped it, not yet marked
  in Etsy; once marked in Etsy, the order moves to "Sent". The status on the right — exactly as
  Printify/Gelato give it, in English; no separate marks needed for drafts.
- Updated plans/roadmap.md, [glossary.md](glossary.md) (the truck, the box, the
  clock), [rules/order-stages.md](rules/order-stages.md), [features/orders.md](features/orders.md); two
  questions removed from plans/open-questions.md. No code changed.

## [2026-09-17] update | Gelato: a 28- or 30-page book

- Built the idea from the plans: the number of pages downloaded (28 or 30) decides the Gelato book's
  length; the decision — in [decisions.md](decisions.md), the item removed from plans/roadmap.md.
- The program reads from Gelato's catalog how many pages each format prints; a new route,
  `GET /api/creator/gelato/page-counts` ([architecture/api-routes.md](architecture/api-routes.md)).
- A 28-page softcover — not checked live (Gelato's docs say "from 30"); the program will show the answer
  after a restart — plans/open-questions.md.
- Updated: [integrations/gelato.md](integrations/gelato.md), [features/order-creator.md](features/order-creator.md),
  [features/orders.md](features/orders.md), [rules/printer-rule.md](rules/printer-rule.md),
  [rules/book-structure.md](rules/book-structure.md), [rules/file-naming.md](rules/file-naming.md), and others.

## [2026-09-17] ingest | Idea: shipped orders, status, and tracking number in the queue

- Source: [raw/2026-09-17-vidpravleni-i-trek-nomery.md](raw/2026-09-17-vidpravleni-i-trek-nomery.md)
  (the owner's text; the screenshot wasn't kept — it had real buyer names on it).
- Recorded in plans/roadmap.md (the truck tab, the status on the right, the name in
  the grey row, the tracking-number chip), questions — in plans/open-questions.md,
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
