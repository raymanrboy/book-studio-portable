---
title: Listing slides — the six Etsy pictures after the Mockups, and their editor
type: feature
updated: 2026-09-29
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
> background** («Без фону»); after the run, «Зробити слайди» makes the six by themselves; «Відкрити в редакторі» opens a
> Canva-like editor for the owner's touches. Built on 2026-09-29 from [the plan](../plans/listing-pictures.md) (its
> history: the design, the cut-out, the external prototype); the owner may also have them changed **through an agent**
> — the skill `/listing-slides` (`.claude/skills/listing-slides/SKILL.md`).

## How the owner uses it

1. **Мокапи** as always ([mockups](mockups.md)). Each picture Photoshop saves is handed to the slides' cutter at once
   (`mockups.watch()` → `_cut_without_background()`); the book with its real shadow, on a transparent background,
   lands in the same folder's **`Без фону\`** under the mockup's own name — **full size** (≈3700 px), ready for any use.
   Only **Open 1, Open 2 and Cover 1** can be cut (one book on the studio background, with a book mask in the template);
   Cover & Open 1, All & Open 1 are whole scenes and Dedication a table scene — they stay as they are. The ones left open
   for the owner go the same way right after «Зберегти відкриті». ~3–6 s a mockup, in the background.
2. **Step 4 «Слайди для лістингу»** appears under the Photoshop step once a run has saved pictures: a line «Без фону ·
   5/6» (a spinner while cutting, the folder button when some are ready), the two numbers **Сторінок** (24) and
   **Віршів** (11), six numbered outlines, and **«Зробити слайди»**. The button always answers: while Cover 1 and
   Dedication still wait in Photoshop it says slides 2 and 3 need them and blinks «Зберегти відкриті».
3. **Made by themselves** (~10 s): the rows 1–6 (waiting / drawing / ✓) and a bar; then the card **«Готово · 6 слайдів»**
   with the pictures (a click → the viewer, whose «Правити» opens that slide in the editor; the original opens the file),
   a ✎ on each, the folder button, **«Відкрити в редакторі»**, and ↻ «Зробити заново» (from the template again — asks
   first: the book's edits go). A slot without a mockup (e.g. one Open 2 only) is named in a yellow line; the slide shows
   a dashed placeholder there. Files: **`Listing 1.png … Listing 6.png`** in the mockups' folder, never over another
   file (` (2)`); the window's title, the taskbar flash and Windows' sound when the window is behind.
4. **The header's ▣ «Слайди для лістингу — книг і шаблон»** (beside the sliders): the template and the last dozen books'
   slides — the editor is one click away even after a restart (the card lives only in the window's memory).

## The editor (`#/slides/<set | template>/<1–6>`)

Its own module, **loaded only when opened** (`app.js` leaves it out of the pages' warm-up — the owner: "a separate
module called only when needed") with its own styles (`css/slides.css`, linked by the editor itself). The rail keeps
«Мокапи» lit; ← / the back link goes to the Mockups. Book Studio's look: its tokens and both themes, the Listings'
cyan, `ib()` icons with tooltips.

- **The bar**: back · «Слайди» with the book's name · the segmented **1–6** · undo / redo · «Скинути слайд» (a book's
  slide → the template; the template → its first design) · «Зробити шаблоном» (a book's slide becomes the template for
  every new book; books already made don't change) · the saved state («Збережено», «Не збереглось», «Малюю 3 з 6») ·
  **«Зберегти картинки»** (a book only: the six baked again into the same `Listing N.png`, the Mockups' card shows them).
- **Layers** (left, the top one in front): the kind's glyph, the name, 🔒 (not moved by the mouse) and 👁 on hover or
  when set; **dragged** to another depth; **«+»** adds text, a sticker, a ribbon, an arrow, a sparkle, a heart, a torn
  strip, a stain, dashes, a mockup, a picture.
- **The slide** in the middle on a dotted board: drag to move, the round handle turns (Shift — 15°), corners resize
  keeping the shape, edges stretch the kinds that stretch. Keys: arrows 1 px (Shift 10), `[` `]` turn, Ctrl+Z / Y /
  Shift+Z, Ctrl+D a copy, Delete takes it off (Ctrl+Z brings it back), Esc lets go.
- **Properties** (right), grouped: the name; **Мокап** / **Картинка** (which slot; a picture of a book can be replaced
  — «Інша картинка…», the Windows dialog), **Текст** (lines; `{pages}` / `{poems}` — the book's numbers; size, line
  height, **arc** −180…180°, alignment), **Форма** of an arrow (bow, loop, where, which side, thickness),
  **Положення** (X, Y, angle, size), **Вигляд** (the slide's own colours as swatches + a picker, opacity, the kind's
  own knobs), **Тінь** (the book's «З Photoshop» 0.6 and «Додаткова» 0.18; the text's shadow 0.7; an arrow's 0.45);
  ↔ ↕ mirror, copy, remove in its header. Nothing selected: the slide's background and the book's two numbers.
- **Saving**: every change goes to disk ~0.5 s later with the version it was made on (`POST /api/slides/scene`).
  **What an agent changes in the files shows up by itself**: the signature is asked every 1.5 s (and at once when the
  window comes back) — «Слайд змінено ззовні — показано новий»; a save made on an old version is refused (409) and the
  editor takes the new one («ваша остання зміна не збереглась»); Ctrl+Z still goes back.

## The template, a book's set, slots

| What | Where |
|---|---|
| The first design (the agent's drawing of his Canva slides) | `app/studio/slides/design/slide1…6.json` (in git) |
| **The template** — the owner's touches (from the external editor on 29.09.2026) | `app/data/slides/design/slideN.json` |
| **A book's set** — `set.json` (name, folder, numbers, slots, baked files), `scenes/`, `books/<slot>.png` + `_shadow.png`, `pictures/dedication.png`, `page30.png` | `app/data/slides/sets/<time>-<id>/` (the last 12 kept) |
| Every cut-out once (the book and its shadow, 2600 px, where the book sits) | `app/data/slides/cuts/<key>/` |

A book on a slide names its **slot**, not a file: `open1:1…4` (the Open 1 mockups in the owner's picks order — slides
1 and 4), `open2:1…2` (slides 5, 6), `cover` (slide 2, twice); a flat picture — `dedication` (the whole Dedication
mockup), `page30` (the demo book's last page, taken from the Mockups' demo book while it is loaded; «Інша картинка…»
otherwise). A new set copies the template's six scenes; `set.json` maps the slots to its pictures. The template is
shown in the editor with the newest book's pictures.

The first set, **«Приклад»**, is the owner's sample book as the external editor showed it (its baked pictures in
`examples\Слайди — приклад\` match the external tool's pixel for pixel; slide 2 differs in a few pixels).

**The examples** (the owner, 29.09.2026: "only the examples are needed"): his desktop folder `moсkup studio` moved into
the Book Studio folder as **`examples\`** (git-ignored, in the backup): `Canva resoult\` — his six Canva slides (what the
agent compares with), `Photoshop prep\` — his sample mockups (a real cut-out is checked on copies of them),
`Слайди — приклад\` — the sample set's baked six. The external tool went to the Recycle Bin. Beside it, **`Трафарети
мастхев (копія)\`** — a spare copy of the mockup templates (read-only files; git-ignored; left out of the backup — the
templates themselves are in it); the program never reads it, the Mockups use `D:\Roman\Desktop\Трафарети мастхев`.

## How it works inside

- **The cut** (`cutout.py`): the template's `BOOK/OBJECT` mask is the book; its Multiply / Screen shadow layers become
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
  `sig()` — the files' times, what the editor asks for.
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

## Where in the code

- [app/studio/slides/cutout.py](../../app/studio/slides/cutout.py) — `kind_of()`, `spread_of()`, `KINDS`, `NO_BG`, `CUTS`, `HAZE`, `MAX_WIDTH`, `read_psd()`, `_near_book()`, `READER`, `template()`, `cut()`, `smaller()`, `combined()`, `ensure()`, `Cutter`, `cutter`
- [app/studio/slides/store.py](../../app/studio/slides/store.py) — `SLIDES`, `FACTORY`, `DESIGN`, `SETS`, `TEMPLATE`, `BOOK_SLOTS`, `PICTURE_SLOTS`, `SLOT_LABEL`, `NUMBERS`, `KINDS`, `load()`, `check()`, `save()`, `reset()`, `to_template()`, `sig()`, `new_set()`, `put_book()`, `put_picture()`, `list_sets()`, `forget_old_sets()`
- [app/studio/slides/work.py](../../app/studio/slides/work.py) — `make()`, `bake_set()`, `mockups_in()`, `slots_of()`, `pictures()`, `title()`
- [app/studio/slides/bake.py](../../app/studio/slides/bake.py) — `bake()`, `render()`, `outputs()`, `run_browser()`, `NAME`, `AT_ONCE`
- [app/studio/slides/routes.py](../../app/studio/slides/routes.py) — `assets()`, `_make()`, `_bake()`, `_cutouts()`, `_save()`, `_sets()`
- [app/studio/mockups.py](../../app/studio/mockups.py) — `watch()` → `_cut_without_background()`
- [app/web/js/slides/engine.js](../../app/web/js/slides/engine.js) — `setAssets()`, `ready()`, `boxOf()`, `DRAW`, `drawElement()`, `drawScene()`, `fill()`, `elTransform()`
- [app/web/slides/render.html](../../app/web/slides/render.html) — the page headless Edge bakes
- [app/web/js/pages/mockups-slides.js](../../app/web/js/pages/mockups-slides.js) — `slidesStep()`: the cut-outs line, the card, «Зробити слайди», the viewer, `openSets()`
- [app/web/js/pages/slides-editor.js](../../app/web/js/pages/slides-editor.js) — `mount()`, `SPEC`, `NEW`, `KIND`
- [app/web/css/slides.css](../../app/web/css/slides.css) — the editor's look
- [app/web/js/app.js](../../app/web/js/app.js) — the route `#/slides/…` (`'lazy'`), the rail's «Мокапи» lit for it
- [app/tools/slides.py](../../app/tools/slides.py) — `main()`
- Tests: [app/tests/test_slides.py](../../app/tests/test_slides.py) (`TheCut`, `Scenes`, `MakingThem`, `CommandLine`)

## Related

- [Mockups](mockups.md) · [The plan and its history](../plans/listing-pictures.md) · [Two modes](modes.md) ·
  [Decisions](../decisions.md) · [Security](../security.md)
