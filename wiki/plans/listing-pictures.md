---
title: Listing pictures — the six Etsy slides without Canva (plan)
type: plan
updated: 2026-09-29
code: []
---
# Listing pictures (plan)

> After the [Mockups](../features/mockups.md) the owner turns the Photoshop PNGs into **6 square Etsy
> listing pictures in Canva** by hand (a background, bands, badges, text, a drop shadow under the book).
> **Agreed on 2026-09-29:** Book Studio makes these 6 pictures itself — **its own tool, no Canva and no
> Canva connector** (the owner's words: "create an entirely new tool of your own"). All six are drawn by an
> external tool with a hand editor, then **moved into Book Studio the same evening** — how it works now:
> [features/slides.md](../features/slides.md).

## What the owner does today (his examples, 2026-09-29)

His samples (since 2026-09-29 in the Book Studio folder's `examples\`; first on the desktop as `moсkup studio\`): `Photoshop prep\` (the mockups' PNGs, 4000×2670 on
the templates' grey studio background; `Cover 1.png` 2670²) and `Canva resoult\` (the finished pictures,
**2000×2000**). The same six for every book — his standard Canva template:

| № | Heading on it | What's placed |
|---|---|---|
| 1 | Made just for them · "24 unique pages" | two `2. Open 1` spreads, arrows |
| 2 | Choose your perfect format · 5x5 / 8x8, "2 sizes & covers" | `1. Cover 1` twice (small and large) |
| 3 | Dedication & afterword · "Last page", "Custom message" | `4. Dedication` on its own background + **page 30** (the afterword) in a scalloped frame |
| 4 | "12 unique little poems" | the other two `2. Open 1` spreads |
| 5 | Personalization made simple · How to order? (two steps) | `3. Open 2`, enlarged and cropped |
| 6 | Thank you for shopping small | the other `3. Open 2`, a heart |

`Cover & Open 1` and `All & Open 1` are not in these six. `4. Dedication.png` in `Canva resoult\` is the
mockup itself, not a Canva slide.

## Agreed (2026-09-29)

- **The owner picks** which mockup goes on which slide (the default follows the table: exactly 4 × Open 1,
  2 × Open 2, 1 × Cover 1, 1 × Dedication — the Mockups' output). Page 30 comes from the demo book's ZIP.
- The numbers: **24 unique pages, 11 poems** (his Canva showed "12"; he said 11) — an editable field.
- **Font — Comica** (`ComicaRegular.otf`, SIL Open Font License, the owner's `D:\Roman\Desktop\comica.zip`).
  His Canva look = the same glyphs **stretched ~1.35× wide**, capitals with a **small dotted "i"**
  (`UNiQUE`), white with a soft shadow.
- **Creative freedom** (the owner, 2026-09-29): "don't copy mine one to one — make something unique and
  beautiful". Shadows and a sense of volume are a must.
- Runs after the Mockups have saved everything (incl. «Зберегти відкриті» — the cover and the Dedication
  colours are his hand work).

## Cutting the book out of the grey background — solved (2026-09-29)

The owner: hiding the background in Photoshop "cuts some shadow" — **why:** the templates' shadows are
opaque grey layers in **Multiply** over the grey background (`BACKGROUND/SHADOW_global`,
`BOOK/UNDER L/S/SHADOW_separated`), plus **Screen** lights. The fix, needing nothing from the owner:
- the book's outline = the mask of the `BOOK/OBJECT` group (read from the template with `psd-tools`, read-only);
- a Multiply layer of grey `v` is exactly black with alpha `1 − v`; a Screen layer — white with alpha `v`
  (× the layer's opacity) → a real transparent shadow that lies right on any background;
- the book's pixels come from the owner's PNG under the mask; the shadow kept only near the book (a soft
  falloff from the outline) and its faint whole-canvas haze (~3–5 %) cut.
Checked on `2. Open 1`, `3. Open 2`, `1. Cover 1`: clean edges (the spine and the gutter at full size),
~3–11 s per template. A naive colour-difference cut-out was tried first and failed (holes where pale pages
meet the grey, ragged soft-shadow edges).

## The design (prototype, 2026-09-29)

"Grandma's keepsake scrapbook": cream paper with grain and soft watercolour stains; **torn-paper** strips
(sage, peach) instead of flat bands; die-cut **stickers** with a white rim and washi tape; a **running
stitch** instead of the dashed line; hand-drawn hearts and sparkles; **window light** — soft beams and
leaf shadows over everything, books included, so the cut-out books sit in one photo. Palette: his sage
`#9a9c66`, peach `#e6bd92`, cream `#f3e8d8`.

**Direction B — "like a website"** (the owner asked mid-way, 2026-09-29: "approach it as if you were making a
site — aesthetics matter a lot"): a landing-page hero — an eyebrow pill («INSIDE THE BOOK»), a big dark
headline with the number in peach, an italic serif subline, a round sage seal with text around it
(«PERSONALIZED · MADE WITH LOVE»), glassy feature chips with line icons, soft colour glows instead of
bands, the books large and barely overlapping (the illustrations stay visible). Fonts: the headline in
Comica, the rest Segoe UI / Sitka (Windows). **The font is free too** (the owner: "don't cling to Comica,
pick a similar one").

**The owner's steer (2026-09-29, later):** "the spreads are the main thing — the person must see them, all the
other text is just an add-on"; asked to reproduce **his own layout as closely as possible, only with the torn
edges** ("came out really well"), and of the scrapbook slide said "cool in a way, just polish it". Two
candidates made: **C — his Canva layout measured off his picture** (the same book positions, angles, colours
`#eedec7` / olive `#a2a066` / peach `#e8c59d`, starburst badge, white dashes) with torn olive and peach
bands; **A2 — the scrapbook polished** (books larger, the headline strip smaller, the window light quieter).
Books are placed by the book's own centre, width and angle (not the picture's), so any mockup lands the same.

**Chosen (the owner, 2026-09-29): C** — his layout with torn edges — plus the scrapbook's **die-cut sticker**
(scalloped, white rim, washi tape) instead of the starburst, the **four-point sparkles**, and **barely visible
leaf shadows** from a window (top-right, multiply ~8 %). He asked for the sticker's text to sit "neatly and
evenly": it is laid out by the letters' real ink (canvas `measureText`), the label rows share one cap
height, and the largest size is found at which every row fits the circle with an even margin (~22 % of the
radius) — so any text fits any sticker by itself.

How it's drawn: each slide is an HTML page (SVG for paper, stains, stickers, light) with the cut-out books
as images; headless Chrome/Edge saves it at 1000² × 2 = **2000×2000 PNG** in ~3 s.

## The hand editor (prototype, 2026-09-29)

The owner: the remaining touches are "super small — easier to move them myself"; asked for a Canva-like
editor "with layers, rotating and moving", after which the agent **bakes** the result. Built in the
scratchpad: a slide is now a **scene** — a list of elements (`book`, torn `band`, `blob`, `dashes`,
`leaves`, `sticker`, `sparkle`, `grain`), each with a centre, size and angle; one drawing code serves the
editor and the final picture. The editor: layers (order, hide), drag / rotate handle (Shift — 15°) / corners
(size) / edge handles for bands, arrows nudge, `[` `]` rotate, Ctrl+Z/Y/D, numbers and colours on the
right, the sticker's text lines. Every change is written to disk by a tiny local server (POST
`/save/<id>`); "bake" = draw the saved scene at 2000² with headless Chrome. Opened in the app's browser
pane via the `slide-editor` entry in `.claude/launch.json` (port 47895).

**Where it lives — outside Book Studio for now** (the owner, 2026-09-29: "don't integrate it into Book Studio yet,
let it be an external tool"; the same evening he asked to move it in — the plan below): `D:\Roman\Desktop\moсkup studio\Slide Editor\` (note the Cyrillic "с" in
"moсkup"). Not in the repo, not in git:

| File | What it does |
|---|---|
| `Відкрити редактор.bat` | the owner's launcher: starts `serve.py`, opens the editor in the browser |
| `serve.py` | the local server (port 47895): the editor's files, `data/`, `POST /save/<id>` → `data/saved/<id>.json` |
| `editor.html` | the editor (`?id=slide4`); `engine.js` — draws a scene (shared with the final picture); `slide.html?id=` — the final picture |
| `scenes/<id>.json` | a slide's default design («Скинути все» returns to it); `data/saved/<id>.json` — the owner's edited version |
| `cutout.py` | the mockups' PNGs → `data/books/<name>.png` (the book) + `<name>_shadow.png` (its Photoshop shadow, a separate layer since 2026-09-29 — the owner found slides 1, 2, 4 "too heavy") + `books.json` |
| `bake.py [id…]` | "bake": headless Chrome/Edge → `data/out/<id>.png`, 2000×2000 |
| `fonts/` | Comica + its SIL OFL licence |

In the Claude app the agent starts it with `preview_start("slide-editor")`; the owner's bookmark is
`http://localhost:47895/slides/editor.html` (a switcher at the top picks the slide; `?id=slide1…6`).

**All six slides (2026-09-29):** after №4 the owner asked to "reproduce all the others the same way"; slides 1, 2,
3, 5, 6 were measured off his Canva pictures (positions, angles, texts) and drawn in the same style — torn bands,
the die-cut sticker instead of his stars, sparkles, faint leaf shadows. New element kinds for them: `text` (Comica
stretched, or a plain sans), `arrow` (hand-drawn, through points; solid heads for the straight ones), `image` (a
flat picture — the Dedication mockup, page 30 in a scalloped frame), `ribbon` (a bookmark with a V-notch, text
fitted to its rectangle), `heart` (die-cut, with a thumbs-up icon). Pictures: `data/pictures/` (`Dedication.png` —
the owner's `4. Dedication.png`; `page30.png` — the afterword page he sent). The default designs are made by
the agent's one-off generator (not kept in the tool): positions came from a measuring grid over each picture.

## The editor's knobs

The owner makes the small touches on all six in the editor; the agent bakes them. Book shadows are two knobs
per book: «Тінь з Photoshop» (`bake`, default 0.6) and «Додаткова тінь» (`shadow`, default 0.18).
Letters (texts, stickers, ribbons) have «Тінь тексту» (`tshadow`, default 0.7 — the owner's pick — one soft shadow, offset down; the owner:
the text "blends in a bit", and a second tight shadow made it look "embossed" — he wants flat letters with a shadow). Straight arrows have sharp filled heads (the line stops inside the head).
**Arrows are smooth curves** (the owner, 2026-09-29: "make them smoother", slides 1 and 3): from the first to
the last point, an arc (`bow`) with an optional round loop (`loop`, `loopAt`, `loopDir`); a colour and a shadow
(`tshadow`, default 0.45). Arrows saved before keep their ends — their arc and loop are read off the old points.
**Text on an arc** (`arc`, degrees the line spans; − bends it down) — every letter placed and turned on the circle
by itself, keeping the stretched Comica; «Last page» on slide 3 is an arch (50°). **Mirroring** any element —
`flipX` ↔ / `flipY` ↕, two buttons in the editor (the owner asked, 2026-09-29).

## Moving into Book Studio — the plan (2026-09-29, **built the same day** — [features/slides.md](../features/slides.md))

The owner, after the six were baked with his touches (2026-09-29): "integrate it into our program at once — that is
first. Second, make a skill that says how to set up and work with this editor — sometimes it will be easier for me to
work through an LLM than by hand. In Book Studio it must be a **separate module that is called only when needed**
(the editor), with a decent frontend and UI/UX **in Book Studio's style**. Write the plan, then we implement it by the
plan." This replaces "outside Book Studio for now" ([decisions](../decisions.md)). Phases 1–3 are the integration,
phase 4 the skill, phase 5 the checks; each phase ends working and is shown to the owner.

### Phase 1 — the engine moves in (no new screens yet)

- **`app/studio/slides/`** — its own package, like the Workshop: `__init__.py` (what's where), `scenes.py` (a scene:
  read, check, save atomically; the template vs a book's copy; `{pages}` / `{poems}` in texts), `cutout.py` (the
  mockups' PNGs → the book + its shadow; `psd_tools` imported **inside** the call, the templates only read),
  `bake.py` (headless Edge/Chrome, found the way `desktop.py` finds it, draws Book Studio's own
  `/slides/render.html` at 1000² × 2; its profile and temp in `app/data/tmp/`, removed after — nothing on drive C),
  `routes.py`. **"Only when needed":** nothing runs at launch — no timers, no browser, no `psd_tools` until a
  Mockups run saves a picture or the owner presses a button.
- **Front**: `app/web/js/slides/engine.js` (the drawing, one for the page, the editor and the bake — moved as it is),
  `app/web/fonts/` — Comica with its SIL OFL licence (the licence allows shipping it).
- **Data** `app/data/slides/` (not in git): `design/slide1…6.json` — **the template** (the owner's current edits);
  `sets/<book>/` — a book's slides: `books/` (cut-outs + `books.json`), `pictures/` (Dedication, page 30),
  `scenes/`; the cut-outs are cached by file size + time (the second time is instant).
- **Slots, not file names**: a scene's book says *which* mockup it wants (`open1:1…4`, `open2:1…2`, `cover`,
  `dedication`, `page30`); a book's set maps the slots to its cut-outs — the same six drawings serve every book.
- **`app/tools/slides.py`** — the agent's and the tests' command line, works with the window closed:
  `cutout <folder>`, `render <slide> [--set] --to <png>` (one picture to look at), `bake [--set] [slides]`.
- **Moving the owner's work in**: the external folder is only **read** — its `data/saved/` becomes the template, its
  cut-outs and pictures a first set «Приклад». `D:\Roman\Desktop\moсkup studio\Slide Editor\` stays as it is; the
  owner deletes it when he is happy. (Done 2026-09-29: the folder moved into Book Studio as `examples\`, the old editor to the Recycle Bin.) The `slide-editor` entry leaves `.claude/launch.json`. Check: the same slide
  baked by the old tool and by Book Studio match pixel for pixel.

### Phase 2 — the Mockups go on: pictures without background, then the slides (no new page in the rail)

The owner's steer (2026-09-29, on the plan): "the Mockups, where we have the Photoshop automation, must now also save
the pictures **without background**, fit for these templates. After the Photoshop script has worked, the Mockups page
**offers me the next step — making the listing slides**; I press it and they are made by themselves. After that a
button **offers to go into our editor** and correct them if needed." So the slides are **the Mockups' next steps**,
not a page of their own.

1. **Without background — by itself, while Photoshop works.** Every picture the script saves (`watch()` sees it)
   is cut out at once by `slides.cutout` — the book with its real shadow on a transparent background — and saved
   beside it in the run's folder: **`Без фону\2. Open 1 (6-7).png`** etc. (one PNG, the book and its shadow
   together, fit for anything, Canva too; the slides keep their own two-layer copy — the book and the shadow apart,
   for the two shadow knobs). The ones left open go the same way right after «Зберегти відкриті». Photoshop itself
   can't do it — its shadows are grey Multiply layers over the grey background; our cut needs nothing from the
   templates (only read). ~3–11 s a mockup, in the background: most are ready before the owner finishes his part.
   Dedication is a flat picture on the slide — kept whole. The run's rows show «✓ без фону» per template;
   `Cover & Open 1` / `All & Open 1` are cut too once their templates are checked to have the book's mask.
2. **«Слайди для лістингу»** — a new card under the result (step 5) once the run is done: the six slides as small
   previews of the template, and **«Зробити слайди»**. The slots fill themselves in the Mockups' order (Open 1 →
   slides 1 and 4, Open 2 → 5 and 6, Cover 1 → 2, Dedication + page 30 → 3; page 30 from the demo book already
   loaded); **Сторінок** and **Віршів** are taken from the book (24 / 11 by default, editable on the card).
   The button always answers: Cover 1 and Dedication not saved yet → the «Зберегти відкриті» button blinks and a
   toast says slides 2 and 3 need them.
3. **Made by themselves** — a row per slide (waiting / drawing / ✓) and a progress bar, ~3 s a slide, then **the six
   pictures** in the card (a click → the viewer) saved into the same folder; the taskbar flash + sound + title
   when the window is behind, as for the Photoshop run.
4. **«Відкрити в редакторі»** — under the six (and a ✎ on each one → that slide): the editor (phase 3). Its
   «Зберегти картинки» bakes the six again into the same files (they are the program's own, made a minute ago —
   not the owner's), and the Mockups' card shows the new ones.

The page keeps all of it when the owner steps away (`keep()` / `revive()` as now); «×» Завершити also closes the
book's slides (its set stays on disk, so the agent can still work on it).

### Phase 3 — the editor inside Book Studio (loaded only when opened)

- `#/slides/edit/<n>` → `pages/slides-editor.js` + `css/slides.css`; **left out of the idle warm-up** of the pages'
  code — loaded the first time it is opened. No item in the rail: it is reached from the Mockups' card; the rail
  stays; Esc / ← back to the Mockups.
- **Book Studio's look**: its tokens and both themes (dark by default), the Listings' cyan, icons from `icons.js`
  (`ib()` with tooltips — new ones: layers, eye, lock, mirror ↔ / ↕, copy, undo, redo, arc), the program's font
  scale; the slide switcher as a segmented 1–6; a «Збережено» chip; toasts instead of the status line.
- **Layout**: a header bar (back, 1–6, undo / redo, fit, «Скинути слайд»); on the left the layers with their kind's
  icon, eye and lock, **dragged** to reorder; the canvas in the middle on a quiet board with the handles as now;
  on the right the properties **grouped** — Положення (X, Y, кут, розмір, ↔ ↕), Вигляд (колір — the design's palette
  as swatches + a picker, прозорість), Тінь, Текст (lines, size, arc) — sliders with a number beside them.
- **«+» adds an element** (text, sparkle, arrow, sticker, ribbon, heart, torn strip) — the old editor could only
  copy. Everything else as now: autosave, keys (arrows, `[` `]`, Ctrl+Z / Y / D), mirroring, arc text.
- Whose edit: **this book** or **the template** (question 1 below).

### Phase 4 — working through the agent (the skill)

- **`.claude/skills/listing-slides/SKILL.md`**: where things are; the scene format — the 1000×1000 canvas, x / y the
  centre, every kind and its fields with defaults; how to change a slide (the right file, written atomically);
  **how to look** (`slides.py render` into the scratchpad; the agent opens the PNG before it reports; the owner's
  Canva pictures to compare with); how to bake and cut new mockups; recipes (move / turn / resize, texts and
  numbers, colours, shadows, an arrow's arc and loop, arc text, mirror, add a sparkle, hide); the rules (templates
  only read, never over the owner's files, data not in git, reply in Ukrainian). Listed in `CLAUDE.md` with the
  other skills.
- **What the agent changes shows up by itself**: the Mockups' slides card and the editor ask the server for the scenes' signature
  every 1.5 s while they are open (as the Workshop does) and redraw — no more F5. The editor never overwrites a
  change it hasn't seen: a save carries the version it started from; a stale one is refused, the editor takes the
  new file and says «Слайд змінив агент — оновлено» (its undo still works).

### Phase 5 — checks and the wiki

- `test_slides.py`, made-up data only: the shadow maths (Multiply / Screen → alpha) on tiny arrays, a cut-out with a
  pretend template, slots, a scene's check and save (a stale version refused), `{pages}` / `{poems}`, names that
  never overwrite, the bake with a pretend browser (headless, its profile on D, removed after), the command line.
- The preview (`dev_server.py --sample`, the pretend Photoshop): a whole run → «Без фону» → «Зробити слайди» →
  the editor, in both themes.
- Wiki: `features/slides.md`, `features/mockups.md` (steps 5–6, «Без фону»), the interface, routes, code map, glossary («Слайди», «запекти», «шаблон
  слайдів»), log.

### How it was built (2026-09-29)

All five phases, as planned, with the defaults below (the owner said «Приступай до виконання плану» without answering
them). Beyond the plan: the Mockups' header got ▣ «Слайди для лістингу — книг і шаблон» (after a restart the card is
gone — the editor and the template stay one click away); «Без фону» keeps the full size (≈3700 px), the slides'
copy 2600 px; the external tool's `slide-editor` entry left `.claude/launch.json`. The skill: `/listing-slides`.

### The eleven wishes — built (2026-09-29, late evening)

All of them ([features/slides.md](../features/slides.md)), the owner's word «поїхали»: the schemes in the editor, the
background as a layer, the colours of the other slides, «Який мокап» without the file name, locked by default,
Dedication without its floor (in the template the *desk* is «BACKGROUND_desk color» and the *floor* under the book
«BACKGROUND» — the desk and the book stay), the numbering as his Etsy listings, the mockups into the Workshop book's
folder, the Workshop's «Мокапи» step back to the mockups and ticking itself, a book's slides in its folder, the
cleaning; a done book's six are presets.

### Questions for the owner (the defaults the plan takes if he says nothing)

1. **One template for every book?** Default: yes — a book gets a copy of the template; an edit in a book stays in
   that book; «Зробити шаблоном» carries it to every future book.
2. **Names and folder**: `Listing 1.png … Listing 6.png` in the mockups' folder; the cut-outs in its `Без фону\`.
3. ~~The rail's name~~ — no rail item: the slides are the Mockups' next steps (the owner, 2026-09-29).

## Schemes and the editor's next touches (agreed 2026-09-29, not built)

The owner, after setting up his own colours by hand on a book's six slides: "the editor should have a choice of
template — a colour scheme you can save while working in the editor"; then **"a scheme includes not only the colours
but the settings of the whole mockup"** — so a **scheme is a whole design: the six scenes** (colours, positions,
shadows, texts), named. Two are recorded, in `app/data/slides/schemes/<key>/` (`scheme.json` — name, default, where
it came from, its colours by role; `slide1…6.json` — the scenes, with slots and `{pages}` / `{poems}`, so they fit any
book):

| Scheme | What | Colours by role |
|---|---|---|
| **Nature** (the default) | the template as it was on 29.09.2026 (`app/data/slides/design/`) | cream #eedec7, light stains #f5e9d8, olive #a2a066, peach #d5ae81, text white, arrows #6b3a3a; slide 3 — #7a6650 |
| **Night** | the owner's slides of «4k Трафарет, копія» (set `20260929-211854-2d9515`, 21:42) | blue-grey #555876, stains #706880, teal-grey #5c7d88, warm grey #706b68, stickers yellow #e8d48a, text white; slide 3 — peach #d5ae81 |

Night's shades were picked by eye slide by slide, so a colour has near variants (the teal: #5c7d88, #5e7e86, #5d7d88,
#658081; slide 4's background #4e5373) — the scheme feature is where they become one.

Asked for the editor at the same time (waiting for the owner's word — he is mid-work in the open program; the
frontend ones can go in without restarting Book Studio, the rest need a restart):
1. the choice of a scheme in the editor, and «save as a scheme» while working (files — after a restart);
2. the background as a layer of its own (a «Тло» row at the bottom of the layers);
3. the suggested colours taken from the other slides too, not only the ones on this slide;
4. «Який мокап» without the file name («Open 1 · 4»);
5. every element **locked against moving by default** (a click selects it, the mouse doesn't move it; the lock in the
   layers frees it; new elements from «+» free);
6. **Dedication without its background** — the table stays, the wall goes, the shadows kept: its template has the same
   family structure (`BACKGROUND_desk color` — the table, `BACKGROUND` with its own mask — the wall, `SHADOW_global`
   Multiply, `BOOK/OBJECT` with its mask), so the cut can keep the desk layer and drop the wall (Python — a restart).

### The Workshop and the Mockups together (the owner, 2026-09-29 — waiting for his word)

7. **Books are numbered as his Etsy listings**: "numbering starts not from 41 but from 24" — the book now №41 (Sleepy
   trucks bedtime) becomes **№25**, the one before it (Spooky stories, №40) №24; the next new book №26. A book's number
   is its folder's prefix (the owner confirmed: Spooky stories was his 24th listing) (`pipeline/books/41.sleepy-trucks-bedtime`), and the pipeline's rule says "the first book here
   is 40" (`pipeline/GEMINI.md`) — so the two folders get renamed and the rule changed; everything that names a book by
   its folder (the Workshop's address, marks, the generation mode, the library book it was passed as) checked first.
8. **The mockups go into the Workshop book's own folder** (e.g. `pipeline/books/25.…/mockups/`), with «Без фону» and the
   slides — **no "where to save" question** when the Mockups were opened from the book.
9. **From the Workshop back to the mockups at any time**, even when all is saved: the step «Мокапи»'s panel now says
   "made outside Book Studio? tick it when done" with «Відкрити Мокапи» / «Зняти позначку» — it should offer **«Відкрити
   папку мокапів»** (and the way back into the Mockups / the slides' editor for this book) and «Зняти позначку»; **the
   step ticks itself** when the mockups were made from there.

### A book's slides belong to its Workshop book; temporary files go (the owner, 2026-09-29 — waiting for his word)

The owner, on the Mockups header's ▣ menu (the template, «4k Трафарет, копія · 21:18», «Приклад · 18:16» — a set per
«Зробити слайди», named by the demo ZIP and the time): "some saving of states is already there, but I want it tied to
the book in the Workshop, not to a session; all the cache and everything temporary must be erased once the book is
done, the quite temporary things must vanish when I close the program, and all the cache kept in the program's folder
— it must be as portable as possible". Today everything is in `app/data` already (nothing on drive C), but the cuts
(`slides/cuts/`) and the sets are never erased (the sets — only the last 12 kept).

10. **The slides live with the Workshop book**: its folder (`pipeline/books/<n>.<slug>/mockups/`) holds the mockups,
    «Без фону», `Listing 1–6` and the slides' scenes; the editor opens from the book's «Мокапи» step (the ▣ menu, if
    kept, names books as «№25 Sleepy trucks bedtime»).
11. **Cleaning**: the quite temporary (the cuts' cache, the unpacked demo book, the bake's browser files) — when the
    program closes; the book's cache (the editor's smaller copies of the books) — when the book is done (passed to the
    library); the finished pictures stay in the book's folder. **The slides' settings are never erased** (the owner:
    "no — these are presets that will be used in other books too, e.g. in another bedtime book"): a book's six scenes
    stay as a preset to pick for a new book, beside Nature and Night (the agent's suggestion: named by the book,
    «№25 Sleepy trucks bedtime», in the same scheme choice).

## Related
- [Mockups](../features/mockups.md) · [Listing mockups plan and templates](listing-mockups.md) ·
  [Plans](roadmap.md)
