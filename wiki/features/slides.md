---
title: Listing slides — the six Etsy pictures after the Mockups, and their editor
type: feature
updated: 2026-09-30
code:
  - app/studio/slides/
  - app/studio/slides/__init__.py
  - app/studio/slides/cutout.py
  - app/studio/slides/store.py
  - app/studio/slides/work.py
  - app/studio/slides/bake.py
  - app/studio/slides/routes.py
  - app/web/js/slides/engine.js
  - app/web/slides/render.html
  - app/web/js/pages/mockups-slides.js
  - app/web/js/pages/slides-editor.js
  - app/web/css/slides.css
  - app/tools/slides.py
---
# Listing slides (Слайди для лістингу)

> The six square **2000×2000** Etsy pictures of a book (his Canva layout, with torn paper, a die-cut sticker,
> sparkles and faint leaf shadows), made by Book Studio from the book's mockups — **no Canva**. They are **the
> Mockups' next steps**, not a page of their own: while Photoshop works, every mockup is cut out **without its
> background** (`no-background\`, «Без фону» until 30.09.2026); after the run, «Зробити слайди» makes the six by themselves; «Відкрити в редакторі» opens a
> Canva-like editor for the owner's touches. **A book's slides belong to its Workshop book** (its scenes in
> `mockups\slides\`, the six pictures in **`etsy\`** beside its [photo mockups](photo-mockups.md) since 30.09.2026), their look is a **scheme** (Nature, Night, the owner's own — "not only the colours but the settings of
> the whole mockup"). Built on 2026-09-29 from [the plan](../plans/listing-pictures.md) (its
> history: the design, the cut-out, the external prototype); the owner may also have them changed **through an agent**
> — the skill `/listing-slides` (`.claude/skills/listing-slides/SKILL.md`).

## How the owner uses it

0. **From the Workshop book** (its step «Мокапи»: «Зробити мокапи» / «Редагувати мокапи») the Mockups open for that
   book; step 2 of the Mockups is **«Книга»** — the Workshop's books, the chosen one's folder `mockups\` takes
   everything, **nothing asked** (the owner, 29.09.2026); «Інша папка…» is still there for a folder of his own.
1. **Мокапи** as always ([mockups](mockups.md)). Each picture Photoshop saves is handed to the slides' cutter at once
   (`mockups.watch()` → `_cut_without_background()`); the book with its real shadow, on a transparent background,
   lands in the same folder's **`no-background\`** (English inside the book, the owner 30.09.2026; «Без фону» before) under the mockup's own name — **full size** (≈3700 px), ready for any use.
   **Open 1, Open 2 and Cover 1** are cut to the book (one book on the studio background, a book mask in the template);
   **Dedication** keeps **the desk and the book** and loses **the floor** under the book, its shadows kept (the owner:
   "the table stays, the background goes, without losing the shadows" — in the template the desk is
   «BACKGROUND_desk color», the colour he picks for the table, the floor the smart object «BACKGROUND» with its own
   mask); it keeps its full frame, so it lies on slide 3 where the whole mockup lay, the slide showing through.
   Cover & Open 1 and All & Open 1 are whole scenes — they stay as they are. The ones left open for the owner go the
   same way right after «Зберегти відкриті». ~3–7 s a mockup, in the background.
2. **Step 4 «Слайди для лістингу»** appears under the Photoshop step once a run has saved pictures: a line «Без фону ·
   5/6» (a spinner while cutting, the folder button when some are ready), the two numbers **Сторінок** (24) and
   **Віршів** (11), six numbered outlines, and **«Зробити слайди»**. The button always answers: while Cover 1 and
   Dedication still wait in Photoshop it says slides 2 and 3 need them and blinks «Зберегти відкриті».
3. **Made by themselves** (~10 s): the rows 1–6 (waiting / drawing / ✓) and a bar; then the card **«Готово · 6 слайдів»**
   with the pictures (a click → the viewer, whose «Правити» opens that slide in the editor; the original opens the file),
   a ✎ on each, the folder button, **«Відкрити в редакторі»**, and ↻ «Зробити заново» (from the scheme again — asks
   first: the book's edits go). A book whose slides exist gets **new pictures and keeps its six scenes** when the
   mockups are made again; its page 30 is the Workshop book's own `pictures\30.png` when the demo book isn't loaded;
   the Workshop's «Мокапи» step **ticks itself**. A slot without a mockup (e.g. one Open 2 only) is named in a yellow line; the slide shows
   a dashed placeholder there. Files: a Workshop book's **`etsy\Listing 1.png … Listing 6.png`**, each with its number in the
   listing's order («05 Listing 1.png» — [photo mockups](photo-mockups.md#where-things-are)) (since 30.09.2026 —
   the owner: "an etsy folder in every book for the slides and the photo mockups"; `Listing N.png` beside the mockups
   before), for a folder of his own **`Listing 1.png … Listing 6.png`** beside the mockups; never over another file
   (` (2)`); the result's folder button opens that folder; the window's title, the taskbar flash and Windows' sound when the window is behind.
4. **From the Workshop at any time** (its step «Мокапи», [workshop](workshop.md)): «Редагувати мокапи», «Редагувати
   слайди», «Відкрити папку мокапів», «Зняти позначку».

## The editor (`#/slides/<book | set | template>/<1–6>`)

Its own module, **loaded only when opened** (`app.js` leaves it out of the pages' warm-up — the owner: "a separate
module called only when needed") with its own styles (`css/slides.css`, linked by the editor itself). The rail keeps
«Мокапи» lit; ← goes back where it came from (the Workshop book or the Mockups). Book Studio's look: its tokens and both themes, the Listings'
cyan, `ib()` icons with tooltips.

- **The bar**: back · «Слайди» with the book's name · the segmented **1–6** · undo / redo · «Скинути слайд» (a book's
  slide → its scheme; the default scheme → its first design) · **«Схема: Night ▾»** — the schemes (the default marked
  «для нових книг») and the other Workshop books' slides as presets ("e.g. another bedtime book"): a click puts one on
  all six (asks first; the book's mockups and numbers stay); «Зберегти ці слайди як схему…» (a name — the same name
  replaces that scheme; «Нові книги починаються з цієї схеми»); «Нові книги — зі схеми «…»» · the saved state («Збережено», «Не збереглось», «Малюю 3 з 6») ·
  **«Зберегти картинки»** (a book only: the six baked again into the same `Listing N.png` in `etsy\`, the Mockups' card shows them).
- **Layers** (left, the top one in front): the kind's glyph, the name, the lock and 👁 on hover (a freed element's open
  lock stays shown); **dragged** to another depth; **«Тло» — the background as the bottom row** (its colour chip; a
  click opens its colours); **«+»** adds text, a sticker, a ribbon, an arrow, a sparkle, a heart, a torn strip, a
  stain, dashes, a mockup, a picture.
- **Every element is locked by default** (the owner, 29.09.2026): a click selects it (a dashed box, no handles) and its
  properties open; the mouse and the arrow keys don't move it — «Закріплено — зніміть замок…»; the lock in its row or
  in the properties' header frees it (`locked: false`). New elements and copies come free. The leaf shadow and the
  paper grain never catch a click.
- **The slide** in the middle on a dotted board: drag to move, the round handle turns (Shift — 15°), corners resize
  keeping the shape, edges stretch the kinds that stretch. Keys: arrows 1 px (Shift 10), `[` `]` turn, Ctrl+Z / Y /
  Shift+Z, Ctrl+D a copy, Delete takes it off (Ctrl+Z brings it back), Esc lets go.
- **Properties** (right), grouped: the name; **Мокап** / **Картинка** (which slot; a picture of a book can be replaced
  — «Інша картинка…», the Windows dialog), **Текст** (lines; `{pages}` / `{poems}` — the book's numbers; size, line
  height, **arc** −180…180°, alignment; «Який мокап» names the slot only — «Open 1 · 4»), **Форма** of an arrow (bow, loop, where, which side, thickness),
  **Положення** (X, Y, angle, size), **Вигляд** (the slide's own colours as swatches, then **«З інших слайдів»** — the
  other five slides' colours, + a picker; opacity; the kind's own knobs), **Тінь** (the book's «З Photoshop» 0.6 and «Додаткова» 0.18; the text's shadow 0.7; an arrow's 0.45);
  ↔ ↕ mirror, copy, remove in its header. Nothing selected: the slide's background and the book's two numbers.
- **Saving**: every change goes to disk ~0.5 s later with the version it was made on (`POST /api/slides/scene`).
  **What an agent changes in the files shows up by itself**: the signature is asked every 1.5 s (and at once when the
  window comes back) — «Слайд змінено ззовні — показано новий»; a save made on an old version is refused (409) and the
  editor takes the new one («ваша остання зміна не збереглась»); Ctrl+Z still goes back.

## Schemes, a book's slides, slots

| What | Where |
|---|---|
| The first design (the agent's drawing of his Canva slides) | `app/studio/slides/design/slide1…6.json` (in git) |
| **The schemes** — `scheme.json` (name, default, colours by role) + the six scenes: **Nature** (the default — the template as it was), **Night** (his blue slides), his own | `app/data/slides/schemes/<key>/` |
| **A Workshop book's slides** — `set.json` (numbers, slots, the scheme put on, baked files), `scenes/`, `books/<slot>.png` + `_shadow.png`, `pictures/` | `pipeline/books/<n>.<slug>/mockups/slides/` (beside its mockups and `no-background/`; the six baked — `etsy/Listing 1…6.png`) |
| Slides made before 29.09.2026 evening, or for a folder that is no Workshop book | `app/data/slides/sets/<time>-<id>/` (the last 12 kept) |
| Every cut-out once (the book and its shadow, 2600 px, where the book sits) | `app/data/slides/cuts/<key>/` — **gone when the program starts and closes** |

**Cleaning** (the owner, 29.09.2026: "all the cache must be erased once the book is done, the quite temporary things
when I close the program, everything in the program's folder"): the cut-outs' cache and the bake's browser files go
at launch and close (`store.clean_temporary()`); when a book is passed to the library its slides' cache (`books/`,
`pictures/` — the editor's smaller copies) goes (`store.book_done()`); **the six scenes stay** — "presets that will be
used in other books too" — and the finished pictures stay in the book's folder. The old `app/data/slides/design/` (the
template) became the scheme Nature and is no longer read.

A book on a slide names its **slot**, not a file: `open1:1…4` (the Open 1 mockups in the owner's picks order — slides
1 and 4), `open2:1…2` (slides 5, 6), `cover` (slide 2, twice); a flat picture — `dedication` (the whole Dedication
mockup), `page30` (the demo book's last page, taken from the Mockups' demo book while it is loaded; «Інша картинка…»
otherwise; for a Workshop book — its own page 30). A new set copies the default scheme's six scenes; `set.json` maps
the slots to its pictures. The default scheme is shown in the editor with the newest book's pictures.

The first set, **«Приклад»**, is the owner's sample book as the external editor showed it (its baked pictures in
`examples\Слайди — приклад\` match the external tool's pixel for pixel; slide 2 differs in a few pixels).

**The examples** (the owner, 29.09.2026: "only the examples are needed"): his desktop folder `moсkup studio` moved into
the Book Studio folder as **`examples\`** (git-ignored, in the backup): `Canva resoult\` — his six Canva slides (what the
agent compares with), `Photoshop prep\` — his sample mockups (a real cut-out is checked on copies of them),
`Слайди — приклад\` — the sample set's baked six. The external tool went to the Recycle Bin. Beside it, **`Трафарети
мастхев (копія)\`** — a spare copy of the mockup templates (read-only files; git-ignored; left out of the backup — the
templates themselves are in it); the program never reads it, the Mockups use `D:\Roman\Desktop\Трафарети мастхев`.

## How it works inside

- **The cut** (`cutout.py`): the template's `BOOK/OBJECT` mask is the book (Dedication: `read_psd(desk=True)` — the
  book and everything but the floor; `DESK_READER`; `cut(crop=False)` keeps its frame); its Multiply / Screen shadow layers become
  black / white with alpha (a grey `v` in Multiply = black with alpha 1 − v), kept near the book (a soft falloff), the
  whole-canvas haze (3.5 %) cut — `read_psd()` (psd_tools, imported inside the call), `cut()`, `combined()`, `ensure()`
  (the cache, the full-size «Без фону» never over a file that is there), `Cutter` (one background thread, a queue,
  every picture's state per folder; the template's arrays go when the queue is empty). `READER` — the preview server
  and the tests put a pretend template there.
- **The drawing** (`web/js/slides/engine.js`): a scene = `{id, title, bg, items[]}` on a 1000×1000 stage; each element
  is a positioned div (centre, angle, mirror) with SVG inside — torn bands (feTurbulence + feDisplacementMap), the
  scallop, text fitted by its real ink (`fitLines()`), stretched Comica (1.32×, capitals with a small "i"), arc text,
  smooth arrows with a loop, the book as its two layers (the Photoshop shadow and the book with a soft lift). The font:
  `web/fonts/ComicaRegular.otf` (SIL OFL, its licence beside it).
- **Baking** (`bake.py`): headless Edge (or Chrome, `desktop.find_browser()`) opens Book Studio's own
  `/slides/render.html?w=&s=&t=` at 1000² × 2, `--virtual-time-budget` waits for the pictures, `--screenshot` into a
  temporary file, then into place; three at once, a profile per slide in `app/data/tmp/slides-browser/`, removed after.
  The page reads its scene and pictures through media routes (the token in the query).
- **Making them** (`work.py`): `mockups_in()` / `slots_of()` (the owner's picks order from the run's result, else by
  spread), the cuts (waiting for the background cutter), `store.new_set()`, `put_book()` / `put_picture()`, then
  `bake_set()` — the job `slides` (one at a time) shares the rows.
- **Saving** (`store.py`): `save()` checks the scene (a known kind, numeric centre, ≤ 200 elements) and the version;
  `sig()` — the files' times, what the editor asks for. Schemes: `list_schemes()`, `save_scheme()`, `set_default()`,
  `presets()`, `apply_preset()`; a Workshop book's slides: `is_book()`, `set_dir()`, `mockups_dir()`, `new_set(book=,
  fresh=)`; cleaning: `clean_temporary()`, `book_done()`.
- **The command line** `app/tools/slides.py`: `list`, `path`, `render <slide> --to x.png`, `bake --set`, `cutout` —
  for the agent (the skill) and the tests; it starts its own small server, so it works with the window closed.

## What was checked (2026-09-29)

- Tests `test_slides.py` (19, made-up pictures): the cut (the book opaque, a grey 0.5 Multiply → black 48 % after the
  haze, no whole-canvas haze, cropped, where the book sits), a wrong size refused, «Без фону» never over a file, the
  background cutter (and what can't be cut), the Mockups hand every saved picture once; the template and a set, a stale
  save refused with the scene as it is now, a wrong scene refused, reset and «Зробити шаблоном», the signature, the
  first design has slots and `{pages}` / `{poems}`; the slots follow the picks, «Зробити слайди» end to end with a
  pretend browser (six files, the missing slot named, the numbers, the browser's arguments, its profile removed, a
  re-bake into the same files), names never over the owner's files, nothing to show / a browser drawing nothing said;
  the command line.
- The preview (`dev_server.py --sample`, a pretend Photoshop and pretend templates): a whole run → «Без фону · 6/6» →
  «Зробити слайди» asks for «Зберегти відкриті» → after it six slides in 7 s → the editor (select, drag, save, «+» text,
  arc, undo / redo, delete, «Зберегти картинки» into the same six files), a change written into the scene file shows up
  in the open editor, the header's menu → the template; both themes.
- On the owner's PC with his real files: the six of «Приклад» baked through Book Studio equal the external tool's
  pictures; a copy of his real `2. Open 1.png` cut with the real template in ~6 s (the book and its shadow on a
  transparent background). **Not checked live:** a real Photoshop run handing its pictures to the cutter, the real
  window (its taskbar flash for the slides).

**2026-09-29 evening** (the owner's eleven wishes): tests `test_slides.py` 26 (+ Dedication: the desk and the book stay,
the floor goes, the book's shadow on it kept; schemes: Nature first, an old template becomes it, the six saved / put on
/ reset to their scheme / the default; a Workshop book's slides in its folder, named «№25 …», touches kept when the
mockups are made again, «Зробити заново» from the scheme; a done book's cache gone and its six a preset for another
book; the «Мокапи» step ticks itself and counts; the quite temporary goes; «Зробити слайди» for a Workshop book with its
own page 30). The preview: the Workshop book's «Мокапи» → the Mockups for it (no folder asked) → «Без фону · 8/8» (with
Dedication) → six slides → everything in `workshop-books\40…\mockups\`, the step ticked → the editor: «Тло» row,
«З інших слайдів», a locked sticker selected but not dragged (the notice), freed and dragged, «Зберегти як схему»,
«Nature» put on again; slide 3 with the floor see-through. A real Dedication (his own `4. Dedication.png`) cut with the
real template: the desk and the book kept, the floor gone, the book's soft shadow on it kept (~7 s).

## Where in the code

- [app/studio/slides/cutout.py](../../app/studio/slides/cutout.py) — `read_psd_desk()`, `DESK_READER`, `kind_of()`, `spread_of()`, `KINDS`, `NO_BG`, `CUTS`, `HAZE`, `MAX_WIDTH`, `read_psd()`, `_near_book()`, `READER`, `template()`, `cut()`, `smaller()`, `combined()`, `ensure()`, `Cutter`, `cutter`
- [app/studio/slides/store.py](../../app/studio/slides/store.py) — `SLIDES`, `FACTORY`, `SCHEMES`, `SETS`, `TEMPLATE`, `BOOK_SLOTS`, `PICTURE_SLOTS`, `SLOT_LABEL`, `NUMBERS`, `KINDS`, `ensure_schemes()`, `list_schemes()`, `default_scheme()`, `save_scheme()`, `set_default()`, `presets()`, `apply_preset()`, `is_book()`, `mockups_dir()`, `load()`, `check()`, `save()`, `reset()`, `sig()`, `new_set()`, `put_book()`, `put_picture()`, `list_sets()`, `workshop_sets()`, `forget_old_sets()`, `clean_temporary()`, `book_done()`
- [app/studio/slides/work.py](../../app/studio/slides/work.py) — `_book_page30()`, `_tick()`, `make()`, `bake_set()`, `mockups_in()`, `slots_of()`, `pictures()`, `title()`
- [app/studio/slides/bake.py](../../app/studio/slides/bake.py) — `bake()`, `render()`, `outputs()`, `run_browser()`, `NAME`, `AT_ONCE`
- [app/studio/slides/routes.py](../../app/studio/slides/routes.py) — `assets()`, `_make()`, `_bake()`, `_cutouts()`, `_save()`, `_presets()`, `_apply()`, `_save_scheme()`, `_default_scheme()`
- [app/studio/workshop/books.py](../../app/studio/workshop/books.py) — `mockups_state()`, `MOCKUPS`, `_slides_done()` (in `to_library()`)
- [app/studio/main.py](../../app/studio/main.py) — `slides.store.clean_temporary()` at launch and close
- [app/studio/mockups.py](../../app/studio/mockups.py) — `watch()` → `_cut_without_background()`
- [app/web/js/slides/engine.js](../../app/web/js/slides/engine.js) — `setAssets()`, `ready()`, `boxOf()`, `DRAW`, `drawElement()`, `drawScene()`, `fill()`, `elTransform()`
- [app/web/slides/render.html](../../app/web/slides/render.html) — the page headless Edge bakes
- [app/web/js/pages/mockups-slides.js](../../app/web/js/pages/mockups-slides.js) — `slidesStep()`: the cut-outs line, the card, «Зробити слайди», the viewer
- [app/web/js/pages/slides-editor.js](../../app/web/js/pages/slides-editor.js) — `mount()`, `SPEC`, `NEW`, `KIND` (inside: `isLocked`, `palettes()`, `swatches()`, `loadOthers()`, `openSchemes()`, `applyScheme()`, `saveScheme()`)
- [app/web/css/slides.css](../../app/web/css/slides.css) — the editor's look
- [app/web/js/app.js](../../app/web/js/app.js) — the route `#/slides/…` (`'lazy'`), the rail's «Мокапи» lit for it
- [app/tools/slides.py](../../app/tools/slides.py) — `main()`
- Tests: [app/tests/test_slides.py](../../app/tests/test_slides.py) (`TheCut`, `Scenes`, `WorkshopBooks`, `MakingThem`, `CommandLine`)

## Related

- [Mockups](mockups.md) · [The plan and its history](../plans/listing-pictures.md) · [Two modes](modes.md) ·
  [Decisions](../decisions.md) · [Security](../security.md)
