# Wiki change log

Newest entries at the top. Heading format: `## [YYYY-MM-DD] kind | what happened`
(kind: `setup`, `ingest`, `update`, `query`, `lint`, `decision`). Rules — [dev/wiki-rules.md](dev/wiki-rules.md).

Older entries (before 2026-10-18) live in [log-2026-09.md](log-2026-09.md) and [log-2026-10.md](log-2026-10.md).

## [2026-10-28] lint | The pages cleaned of history, duplicates and stale claims
- Dated «since/until/used to» asides, audit and incident stories, hand-kept counts and test logs cut from the feature, rule, flow, integration, architecture, dev and owner pages; duplicated facts reduced to a link to the owning page; the retired Printify flow marked read-only everywhere. `dev/testing.md` halved (suites by class); `cover.md` now owns the cover pipeline.
- Fixed against the code: backup password length (12), the rail has no search, Profit is a rail place, library books go to `library/trash`, `modes.md` lists «Обкладинка».
- Kept on purpose: three dated headings other pages link to (`mockups.md`, `slides.md`, `cover.md`).

## [2026-10-28] lint | The wiki slimmed: decisions split, history moved out of pages, stale claims fixed
- `decisions.md` keeps the current ones (from 11.10 and the 4.10 safety ones); older → `decisions-2026-09.md`, `decisions-2026-10-early.md`; the superseded «Два квадрати» and Canva-order-mode decisions cut to short notes.
- Moved to the logs: Gelato tax-certificate/Payoneer notes, the ledger experiment, the slides check lists. `printer-rule.md`: the retired Printify rule cut to a paragraph. Fixed: portable remote, code-map tests table (→ testing.md), runtime closed-window section, Workshop `n/7`, slides numbering, repo name in overview.
- Left for later (from three read-only audits): dated «since …» tags and history asides on the feature pages, facts told on more than one page.

## [2026-10-28] update | The log split: older entries moved to monthly archives
- Entries before 2026-10-18 → `log-2026-09.md`, `log-2026-10.md`; `wiki_check.py` treats `log-*.md` like `log.md` (no front matter, no name check). [Rules](dev/wiki-rules.md).

## [2026-10-28] update | Hardcover 11×11: a fourth Gelato format
- `hardcover_11x11` in `DEFAULT_SETTINGS` (the product of the owner's template «Hardcover 11x11», read-only); `plan_for()` picks it by the chosen format variation only (`reconcile.is_large()`, `LARGE`: `11.11`, `11x11`, `11" × 11"`, `28 × 28 cm`) — never by the title or the buyer's own words (a dedication «11.11»), never Printify; the card's tip and the queue's «Hardcover 11×11 книга» name the format (`planText()`, `cover_label()`); the description template's «AVAILABLE FORMATS» gets the 11″ line. The four templates checked against the program: all match. [Printer rule](rules/printer-rule.md), [Gelato](integrations/gelato.md), [decision](decisions.md). Tests in `PrinterRule`, `GelatoDraftFlow`.

## [2026-10-28] decision | Listing descriptions: matte only, no glossy choice
- `seo/knowledge/description-template.md` and books 34–45's `listing-seo.md`; [decisions](decisions.md).

## [2026-10-28] update | SEO for book 44 (Santa's Workshop); its listing files on Google Drive
- `seo.py to-drive 44` (15 files); `/etsy-seo`: title with « | », 13 tags, description (30-page). Own angle: workshop + elf + toy. 1 eRank search.

## [2026-10-27] decision | The cover: back to 2:1 + outpaint, «Два квадрати» taken out, a layout guide for the 2:1 picture
- The owner chose book 44's 2:1 test (the scene on the whole picture, the title painted, a big empty room for the name, a 2:1 guide attached). The tool «Обкладинка» keeps only 2:1: «Генерувати» pastes the reference, the guide (`wide-name-title` / `wide-title-name`, by the title), the prompt with the guide's words (`cover.items()`); route `cover-squares` → `cover-tool`, `cover-mode` gone; the squares' code (`compose()`, `assemble()`, `squares_next()`, `set_cover_mode()`, `cover_mode()`) and guides removed. Agent 6: one 2:1 prompt by the full-scene formula, no mode question; build-book, onboarding, workflow, pipeline/AGENTS updated. [Cover](features/cover.md), [decision](decisions.md). Tests in `CoverTool`.

## [2026-10-27] update | The Canva cover for the photo mockups cut to the contour
- The owner: the grandmother's reference without the hardcover's wrap. `set_canva_cover()` cuts a Gelato (458×246 mm, 20 mm off all round) or Printify (17.90×9.50″ → 16.40×8.00″) cover file to the finished cover; a cover kept with its wrap is cut once when the step opens (`trim_kept_cover()`, the whole one to `.replaced/`); a 2:1 cover stays whole. [Photo mockups](features/photo-mockups.md), [decision](decisions.md). Tests in `TheMockupsKeepTheCanvaCover`.

## [2026-10-27] update | The crop window: All & Open 1 crops the back too
- A second frame «Задня» over the back beside «Лицьова» (the same corners, one shade outside both); each side moved by itself, ↶ resets both, «Зберегти» keeps both (`crop.back`); the server cuts the back from its own window (`cover_pictures()`, `_window()`, `BACK_X`), without one — the left half as before. [Mockups](features/mockups.md), [decision](decisions.md). Tests in `TheFrontsCrop`, `DrawnRun`.

## [2026-10-27] update | The cover tool's new guides, the defaults
- Five guides of the full-scene formula in `web/img/cover-guides/` and `GUIDES`; the front's default by the title (`default_guides()`), only a picked guide saved (`"v": 2`). [cover](features/cover.md#the-guides). Tests in `TwoSquares`.

## [2026-10-27] decision | The cover's squares: a full scene, a thin border, a big empty room for the name
- Agent 6's «Mode B» takes book 44's test v3 as the target: the light-patch formula (A) or the open top (B), the name room as big as the title's main line, the reverse a full scene. [Decision](decisions.md).

## [2026-10-27] decision | Girl archetypes G4 and G6 removed; the other numbers kept
- The owner: G4 (olive / Mediterranean) and G6 (South Asian) are not used — deleted from `pipeline/playbook/knowledge/archetypes.md` (now 12: 5 girls, 7 boys; the coverage note updated). The numbers are not shifted, by his choice. [Decision](decisions.md).

## [2026-10-27] update | Workshop: the book's own hero drawn small, like a variant's
- The owner: the «Герой» panel showed `canonical.png` as a huge picture; he wants it small and neat like the variants' heroes. Now the panel's `canonical.png` tab is the variant layout: a 180 px 3:4 thumbnail (a click opens it big), the buttons and the hero prompt beside it (`.ws-hero-side`). Checked in the preview: light and dark, a narrow window. [Workshop](features/workshop.md).

## [2026-10-27] update | Book 41: five hero variants of the girl from the owner's pictures
- The owner made five looks of the girl himself (`D:\Roman\Desktop\output\imagegen\girl-variations-2026-10-27`) and asked for them as the book's character variants in the Workshop. Copied as `hero.png` into `agent/variants/` — `G1_blonde`, `G2_dark_haired`, `G3_east_asian`, `G5_black_curly`, `G7_redhead` (names after `playbook/knowledge/archetypes.md`) — each with `hero-prompt.md` (the edit prompt + his own generation prompt) and 14 swap prompts `2.json … 15.json` (Image 1 = the spread, Image 2 = hero.png; only hair, eyebrows, the bow and skin change). The Workshop reads all five (14 rows each); book check GO, 0 FAIL.

## [2026-10-27] update | The description says the listing's photos are digital mockups

- The owner: a quiet line, no heading, inside «📘 MADE TO ORDER WITH CARE» of the description template — the lifestyle
  photos and videos are digital mockups made with digital tools; the book is personalized, laid out and prepared for
  print by us. `/etsy-seo` puts it into every new description. [SEO](features/seo.md).

## [2026-10-27] update | The pictures and videos of a book's etsy/ without their metadata

- The owner: Etsy reads the photos' metadata now. `scrub.py` cuts every new PNG/JPEG/WEBP in `etsy/` down to the picture
  (C2PA, XMP, EXIF, ICC, DPI, text, comments go; the pixels stay) and copies every new MP4/MOV without its tags — in
  `tidy_etsy()` and in the background for files dropped in by hand (`detail()` → `scrub.soon()`); the trimmed video is
  made clean. The files already there are left (`NEW_FROM`). [Photo mockups](features/photo-mockups.md) ·
  [decisions](decisions.md) · code-map. Checked: tests (`test_scrub.py`), a dry run over the 240 real PNGs in `etsy/`
  (137 had metadata, pixels identical after), copies of real Gemini and etsy/ videos (clean after, same length).

## [2026-10-25] update | A book's tile shows only the face of a cover made of two squares

The owner: the tile caught the hinge and the wrap. Now a cover made of the squares is cut at the hinge line in the tile
(`summary()` → `thumb.face`, CSS `.book-cover img.face`); [cover](features/cover.md). A test in `TwoSquares`.

## [2026-10-25] update | «Обкладинка» — the cover's own tool; two squares made into the cover without the generator

- A new tool in «Інструменти» (`#/cover/<book>`, cover.js): the Workshop's cover card moved there; the strip's step «Обкладинка» leads to it (`coverBody()`).
- «Два квадрати»: both squares in → Cover.png 5409×2906 made by Book Studio (cover.py: the spine and wrap filled from a 4 mm ring along the squares' edges, soft edge 0–6 mm). No outpaint, no canvas.
- Five layout guides (web/img/cover-guides) picked under each square; «Генерувати» pastes the reference / the front, the guide, the prompt with `layout_guide` put in.
- After a review: the page no longer breaks when the square prompts are there (an empty part given to patch()); «Скласти обкладинку» and a switch back to the squares make the cover again; the back only after the front; no reference picture → the prompt names none; a 2:1 book never overwritten by the squares.
- Pages: cover (new), workshop, glossary, api-routes, code-map, decisions, index. Checked: tests, the preview (the tool, the Workshop step). Not checked: a real generation in Gemini with the guides through the tool.

## [2026-10-24] update | «Нагору»: a floating button back to the top of a long page
- The owner: a floating button that takes him to the top (the Workshop's book is long and he scrolls back up a lot). On every page: a round arrow at the bottom right, shown once the page is scrolled more than a screen down; the toasts move up above it. Checked in the preview, light and dark. [Frontend](architecture/frontend.md).

## [2026-10-24] update | Start-up: a start made while Book Studio was closing no longer blocks every next start
- The owner: Book Studio stopped opening. Not the day's Workshop change: a start at 13:54 came while the old copy was still closing (since 13:52); it took the one-copy lock as "another copy is starting", waited for a server that never came — and held the lock while waiting, so every next double-click waited for it in turn. Now a waiting copy lets the lock go, and when nobody answered and the lock is free, it starts itself (`main._release_lock()`; a test in `OneCopy`). The two stuck processes were stopped. [Runtime](architecture/runtime.md).

## [2026-10-24] update | Book 41 (Night Before Christmas, a girl): the two-square cover prompts
- The owner chose «Два квадрати» and sent the best frame («A Cookie Together», spread 08 → `agent/ref_cover_spread-14-15.jpg`). `title-square`: the painted «Night Before Christmas» with the open room for «{Name}'s» above it, Santa and the girl sharing cookies low on a little rug by a small tree, milky cream ground (CG); `quiet-square`: Christmas morning by the tree — crumbs, an empty milk glass, a bitten carrot, the silver bell, a stocking. Book check GO, 0 FAIL.

## [2026-10-24] update | Workshop: «Референс у буфер» on the cover row
- The owner: when the cover prompt has a reference, a shortcut to put it into the clipboard instead of hunting for it in the folder. A picture icon left of «Генерувати» on each cover square (and on the 2:1 row): the `reference_image` of that prompt, if it is a picture in `agent/`, goes into the clipboard as an image (`rows.reference_file()`, `cover.refs`, route `copy-reference`). A test in `TwoSquares`. [Workshop](features/workshop.md) · [API routes](architecture/api-routes.md).

## [2026-10-24] update | Book 46: the two-square cover prompts (title «Grandma» + a small «&»)
- The owner: generate book 46's cover by the new «Два квадрати» way; the title «Grandma», a small «&» under it, then the open room for the name; the picture after his liked look (the kneeling hug in the rose garden by the picket fence), the gate frame attached. Written `agent/cover-prompts-json.md` (`title-square` + `quiet-square`, the bench after a happy day); the frame copied to `agent/ref_cover_spread-28-29.jpg`. Book check GO, 0 FAIL. Agent 6's Mode B fixed: its shape said `"reference_image": "Image 1"`, which the book check fails — now the title square names a real `ref_cover_*.jpg` and the quiet square has no `reference_image`.

## [2026-10-24] update | Agent 6 asks: 2:1 or «два квадрати»

- Agent 6 first asks the owner which cover (with the best frame) and follows one path; «Mode B — two squares»: `title-square` (the painted title without the name, open cream room for the name, the characters low) + `quiet-square` (the story's things, no characters, no text). Also in build-book.md (STOP 4), onboarding.md (step 10), workflow.md, pipeline AGENTS.md.
- The Workshop's cover row follows the prompts: only the two square prompts → «Два квадрати» by itself (`cover_mode()`); the owner's switch is now written either way and wins.
- The test prompts of book 46 lost three trigger words the check would have failed ("storybook", "half", "front").

## [2026-10-24] update | The Workshop's cover: «Два квадрати» — two squares on Gelato's template

- A switch in the cover row: 2:1 or two squares (back + front with the title); both laid on Gelato's 458×246 mm template on a 16:9 canvas, the rest outpainted → Cover.png 5409×2906, 300 dpi.
- The squares' prompts come from `cover-prompts-json.md` by id (`title-square`, `quiet-square`); the check doesn't ask the 2:1 contract of them.
- The back goes with the front attached; the next square and then the outpaint follow by themselves.
- After a review: a 2:1 cover after a squares one is no longer taken for squares (the `squares` mark always written); a 2:1 picture switches the mode back; the switch ends a waiting cover outpaint; «Скасувати» of a square rebuilds the canvas; the stage-2 lines follow the cover actually shown.
- Pages: workshop, api-routes, frontend, testing, security, glossary, decisions. Checked: tests, the preview in light and dark. Not checked: a real Nano Banana outpaint.

## [2026-10-21] update | Profit: the page switch shows a table and a calendar icon

- The owner: the two dots didn't say what the pages are. Now the table / calendar icons (a new `table` icon in `icons.js`), the page shown lit. Page: profit.

## [2026-10-21] update | Profit: the calendar page (the owner's whiteboard)

- An arrow in the Profit head flips to a month calendar: a red dot per sale, a hover card (profit, sales, money in, ads), each week's
  profit at the end of its row, the month's in the head; soft round design on the owner's word. New `profit-calendar.js`;
  `kpi()` / `overhead()` / `adsSpend()` take the days. Pages: profit, code-map, frontend, decisions.

## [2026-10-19] update | Text-check calibration on 103 checks and the print archive

- Owner-marked rows still shown 37 → 13 (11 of them the two orders edited through Etsy messages), red 27 → 11, real catches kept.
- On the owner's word, the Sleepy Trucks passport cover is «Sweet Dreams {Name}» (was «Good Night, Little Trucks»; backup in `data/merge-backup/2026-10-19-sleepy-trucks-cover/`).
- `texts.printed_name()` (a lowercase name capitalised; replay uses it too), `texts._spelled()` in `diff()` (hyphen = space, «James'» =
  «James's»), `_WISH` (a first «Happy…/Merry…»); `rules._own_greeting()` / `_love_line()`, `_vocabulary()` takes hyphen parts, `_LINES` «один
  рядок», `_CLAIM` «замін». Test: `test_the_owners_marks_of_the_nineteenth_of_october`. Pages: text-check, decisions.

## [2026-10-19] decision | Ollama starts hidden with the program; the model warms when a new order opens
- `textcheck.run.start_quietly()` (8 s after the start, no model), called from `main()`; `start_ollama()` never starts Ollama on made-up or test data (`core.SANDBOX`), `warm()` / `start_quietly()` do nothing there.
- `ollama._ollama_command(hidden)` / `start_ollama(hidden)`: the program's own starts (start-up, `_ready()`) are `ollama.exe serve`, never the tray app.
- Order card: `warmModel(true)` (silent) when a new, unsent order's card opens. Tests: `test_ollama_starts_quietly_without_the_model`, `test_test_data_never_starts_the_real_ollama`, `test_the_hidden_start_never_opens_the_tray_app`.
- Pages: text-check, runtime, orders, api-routes, security, decisions.

## [2026-10-18] decision | Etsy titles: one or two « | », then commas
- The owner's format for every title; `seo.py lint` checks it; rules §2, `/etsy-seo`, [features/seo](features/seo.md), [decisions](decisions.md).

## [2026-10-18] update | SEO for Christmas books 38, 42, 43, 45; their listing files on Google Drive
- `seo.py to-drive` copied each book's 15 listing files (photos, slides, video) into `G:\My Drive\MoonMeadowStories\<n>.<slug>\`.
- `/etsy-seo`: `agent/listing-seo.md` with title, tags, description (30-page). Own angles: 38 = Night Before Christmas + Santa and
  reindeer + fox family; 42 = snowman + winter; 43 = letter from Santa + North Pole; 45 = reindeer + the lost reindeer + wish star.
  8 eRank searches (100 phrases + 3 idea lists).

## [2026-10-18] decision | A reprint with new files: the «Передрук» tick, «Друкується» while made, a tab per print
- Order Creator: `alreadyPrinted` → the «Передрук» tick (Gelato `reprint: true` → replacement, archive `reprint`/`reprintOf`).
- `stages.live_reprint()` / `prints()`; matching takes the earliest order naming a receipt; replacement picker offers the first print too.
- Order card: `printsTabs()` / `showPrint()`, history `?order=`; queue chip «передрук»; sample data: Liam's reprint marked.
- Real data: the complaint order's replacement now names the 18.10 reprint, its archive record is a reprint. Tests: `ReprintWithNewFiles`,
  `GelatoReprint.test_a_reprint_with_new_files*`. Pages: order-stages, reconciliation, profit, archive, order-creator, orders, order-to-print, decisions.

## [2026-10-18] update | Wiki catches up with «no Antigravity» (code of 16.10)
- workshop.md, api-routes, code-map, testing, security, portable and a new decision now say the Workshop starts no IDE; `antigravity()` is gone from the page's code list.

## [2026-10-18] update | The copy's first page deleted by itself, no confirm
- `watchOrder` runs the delete once per named copy (`firstTried`); a Canva confirm dialog, if any, is pressed by the extension.

## [2026-10-18] fix | The Canva copy's tab now goes on by itself
- The owner: the copy opened, nothing renamed or deleted. `current()` didn't know a fresh copy's tab; the check ran once, before Canva named the tab. Now `isFreshCopy` is part of `current()`, `copyAt`/`templateName` are kept, and `watchOrder()` looks every second. Checked with the real order.js under node (template, copy in three namings, another design, too late).

## [2026-10-18] update | Three order steps back in the Canva extension (0.4.0)
- The owner kept: the template's copy named after the order, the copy's first page deleted, the ZIP caught from Downloads. New `order.js`
  (the first one was lost, never committed) and `early.js`; the panel's small order card; the card's `canvaLink()`/`awaitZip()`, the `canva-zip`
  route, `find_canva_zip()` and the test class are back. Tried live in the owner's signed-in Canva (rename and back, delete page 1 and Ctrl+Z,
  the template restored); «Файл → Копіювати» not tried (new tab). Run the first real order in his Chrome.

## [2026-10-18] update | The Canva extension's order mode removed
- Extension 0.3.0: early.js, order.js, the panel's order steps gone. Book Studio: the card's Canva button only opens the template; the hand-over, the ZIP wait, the canva-zip route, the ZIP finder and its test class removed. Decision of 2026-10-15 reversed.

## [2026-10-24] ingest | Gelato resale certificates made again: 16 states pending
- The 14.10 certificates were not in Gelato or Avalara. 15 SST states + Pennsylvania filed in the owner's CertExpress (all PENDING);
  the states that need their own registration skipped, with reasons. Page: [integrations/gelato](integrations/gelato.md).

