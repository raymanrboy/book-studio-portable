---
title: Listing slides
type: feature
updated: 2026-11-12
code:
  - app/studio/slides/cutout.py
  - app/studio/slides/store.py
  - app/studio/slides/work.py
  - app/studio/slides/bake.py
  - app/studio/slides/routes.py
  - app/studio/slides/design/slide1.json
  - app/web/js/slides/engine.js
  - app/web/slides/render.html
  - app/web/js/pages/mockups-slides.js
  - app/web/js/pages/slides-editor.js
  - app/web/css/slides.css
  - app/tools/slides.py
  - app/studio/slides/__init__.py
---
# Listing slides (Слайди для лістингу)

> The six square 2000×2000 Etsy pictures of a book (torn paper, a die-cut sticker, sparkles, faint leaf shadows), made by Book Studio from the book's mockups — no Canva. They are step 4 of [Mockups](mockups.md), not a page of their own. A seventh slide exists for a book whose hero has two looks or more. A Workshop book's slides belong to its book; their look is a **scheme**. An agent can change them too: skill `/listing-slides` (`.claude/skills/listing-slides/SKILL.md`).

## Flow

1. **Cut-outs.** Every mockup a run saves is cut out without its background at once (`mockups.watch()` → `_cut_without_background()`; a drawn one: `cut_drawn()`) into the folder's `no-background\` under its own name, full size, book plus its real shadow on transparent. Open 1, Open 2 and Cover 1 are cut to the book; Dedication keeps its desk and book and loses the floor (shadows kept); Cover & Open 1 and All & Open 1 stay whole scenes. Cutting runs in the background.
2. **Step 4 in Mockups** (`slidesStep()` in `mockups-slides.js`): a line «Без фону · 5/6», the two numbers **Сторінок** and **Віршів**, **«Схема: Nature ▾»** (the scheme the six start from), six numbered outlines and **«Зробити слайди»**. The button always answers; slides 2 and 3 need Cover 1 and Dedication to be saved first.
3. **A part of the six.** Each outline is a tick. Ticked templates tick their slides (Open 1 → slides 1 and 4, Open 2 → 5 and 6, Cover 1 → 2, Dedication → 3); the scene templates are on no slide. The button says «Зробити слайди: 1 з 6». `work.make(only=…)` cuts and bakes only the ticked slides (`store.SLIDE_SLOTS`), keeps the other scenes and files, and does not tick the Workshop's «Мокапи» step.
4. **Made another day.** Step 4 starts from the Workshop book's folder as it is: the mockups there are the material, slides already made show as «Зроблено 1 з 6 слайдів» with **«Доробити слайди 1, 2, 4, 5, 6»** — only slides not baked yet (`work.not_baked()`). A mockup redone later lies beside the old one (`… (2).png`); `mockups_in()` takes only the newest of a kind and spread.
5. **Result** (~10 s): rows waiting / drawing / done, then «Готово · 6 слайдів» with the pictures (a click opens the viewer, «Правити» opens that slide in the editor), «Відкрити в редакторі» and ↻ «Зробити заново» (from the scheme again; asks first because the book's edits go). A book whose slides exist gets new pictures and **keeps its six scenes** when the mockups are made again. A slot without a mockup is named in a yellow line and shows a dashed placeholder. The Workshop's «Мокапи» step ticks itself on a whole run.
6. **From the Workshop** at any time (step «Мокапи»): «Редагувати мокапи», «Редагувати слайди», «Відкрити папку мокапів», «Зняти позначку» ([workshop](workshop.md)).

**Files:** a Workshop book's `etsy\Listing 1.png … Listing 7.png`, numbered in the listing's order ([photo mockups](photo-mockups.md)); for a folder that is no Workshop book `Listing N.png` beside the mockups. Never over another file (` (2)`).

## Slide 7 — the hero's looks

Only for a Workshop book whose hero has two looks or more (`agent/variants/<B2_blond>/hero.png`, read by `work.looks()`; `store.LOOKS_SLIDE = "slide7"`).

- Frames `hero:1…7`, filled in the order of the looks' numbers; the name is the folder's start («B2_blond» → «B2»). `hero:1` is the big look on the left, `hero:2…7` a grid of six scalloped «зірочки» with the name under each.
- The pictures keep their white background — no cutting. A frame with no look shows a dashed «Герой N — немає» in the editor only.
- Looks made after the slides are taken when the editor opens or the slides are made (`work.sync_heroes()`).
- The sticker says `{looks}`; the texts are defaults the owner rewrites. A frame has its own knobs (frame shape, zoom, which part shows, caption text via `labelText`).
- Every scheme has slide 7.

## The editor

`#/slides/<book | set | template | scheme:key>/<1–7>` (`slides-editor.js`) is a separate module **loaded only when opened**, with its own `slides.css`. `navFor()` keeps the rail on «Книги» for a book's slides and on «Інструменти» for a scheme; back leads where the owner came from.

- **Bar:** back, «Слайди» with the book name, the segmented 1–7, undo / redo, «Повернути слайд» (back to how the slide was when the editor opened), **«Схема ▾»** (the schemes, the default marked «для нових книг», and other Workshop books' slides as presets; applying one to all slides asks first), «Зберегти ці слайди як схему…», the saved state, **«Книга ▾»** (the Workshop's books, `GET /api/slides/books`: books with slides open here, others go to Mockups) and **«Зберегти картинки»** (a book only: re-bake the six into `etsy\`).
- **Layers** (left): the kind's glyph, name, lock and eye; draggable depth; «Тло» as the bottom row; «+» adds text, sticker, ribbon, arrow, sparkle, heart, torn strip, stain, dashes, a mockup or a picture.
- **Canvas** (middle): drag to move, a round handle turns, corners resize.
- **Properties** (right), grouped per element kind: name, mockup / picture slot, text (with `{pages}` and `{poems}`, size, arc), position, look (the slide's colours first, then colours of the other slides), shadow. Nothing selected: the slide background and the book's two numbers. The full list lives in `SPEC` and `KIND` in `slides-editor.js`.
- **Saving:** every change goes to disk about 0.5 s later with the version it was made on (`POST /api/slides/scene`). A save on a stale version is refused (409) and the editor takes the new one. The editor polls the files' signature every 1.5 s (every 4 s after 30 s idle), so an agent's edits show up by themselves.

## Schemes, sets, slots

| What | Where |
|---|---|
| The factory scenes | `app/studio/slides/design/slide1…7.json` (in git) |
| Schemes: `scheme.json` (name, default, colours by role) + six scenes — **Nature** (default), **Night**, the owner's own | `app/data/slides/schemes/<key>/` |
| A Workshop book's set: `set.json`, `scenes/`, `books/`, `pictures/` | `pipeline/books/<n>.<slug>/mockups/slides/` |
| A set for a folder that is no Workshop book | `app/data/slides/sets/<time>-<id>/` |
| Cut-out cache | `app/data/slides/cuts/<key>/` |
| Baked pictures | `etsy/Listing N.png` of the book |

A book on a slide names its **slot**, not a file: `open1:1…4`, `open2:1…2`, `cover` (slide 2, twice), `dedication` (the whole Dedication mockup), `page30` (the demo book's last page while it is loaded, else the Workshop book's own `pictures\30.png`; «Інша картинка…» otherwise), `hero:1…7`. A new set copies the default scheme's six scenes.

**Cleaning:** the cut cache and the bake's browser files go at launch and close (`store.clean_temporary()`); when a book is passed to the library its slides' working copies go (`store.book_done()`); the six scenes stay as presets for other books and the finished pictures stay in the book.

## How it works

- **Cut** (`cutout.py`): the template's `BOOK/OBJECT` mask is the book (Dedication also keeps its desk); Multiply / Screen shadow layers become black / white with alpha, kept near the book; `cut()` makes it, `ensure()` caches the full-size file (never over a file already there unless `replace=True`, used when the crop window redraws a mockup), `Cutter` runs one background queue. A drawn mockup kept only in «Без фону» notes in the file where it lay (`cut_drawn()`, `_split()`); `alone()` lists such files.
- **Drawing** (`web/js/slides/engine.js`): a scene is `{id, title, bg, items[]}` on a 1000×1000 stage, each element a positioned div with SVG inside (torn bands, scallop, text fitted by its ink, arc text, arrows). The font is `web/fonts/ComicaRegular.otf` (SIL OFL).
- **Baking** (`bake.py`): headless Edge or Chrome (`desktop.find_browser()`) opens Book Studio's own `/slides/render.html` at 1000² × 2, several slides at once (`AT_ONCE`), a temporary profile per slide in `app/data/tmp/slides-browser/`, removed after.
- **Making** (`work.py`): `mockups_in()` finds the mockups, the cuts are awaited, `store.new_set()` and `put_book()` build the set, `bake_set()` bakes it as one job.
- **Command line** `app/tools/slides.py` (`list`, `path`, `render`, `bake`, `cutout`) starts its own small server and works with the window closed; the skill uses it.

## Why

- Every element is **locked by default**: a click must not move things; `locked: false` frees it. New elements and copies come free.
- The editor is lazy-loaded: it stays out of the pages' warm-up.
- Scenes survive a redo and stay as presets; only the slide whose mockup changed is redone.
- A scheme is the settings of the whole mockup, not only its colours.
- Slide 7 keeps its white background; the owner arranges its frames himself.
- Stale saves are refused so an agent's and the owner's edits never overwrite each other silently.
- The Dedication mockup is cut without its floor on purpose.

## Where in the code

- [app/studio/slides/cutout.py](../../app/studio/slides/cutout.py) — `cut()`, `ensure()`, `cut_drawn()`, `_split()`, `alone()`, `Cutter`
- [app/studio/slides/store.py](../../app/studio/slides/store.py) — `SLIDE_SLOTS`, `LOOKS_SLIDE`, `save()`, `sig()`, `new_set()`, `list_schemes()`, `clean_temporary()`
- [app/studio/slides/work.py](../../app/studio/slides/work.py) — `make()`, `mockups_in()`, `not_baked()`, `looks()`, `sync_heroes()`, `bake_set()`
- [app/studio/slides/bake.py](../../app/studio/slides/bake.py) — `bake()`, `AT_ONCE`
- [app/web/js/pages/slides-editor.js](../../app/web/js/pages/slides-editor.js) — `mount()`, `SPEC`, `KIND`; [mockups-slides.js](../../app/web/js/pages/mockups-slides.js) — `slidesStep()`
- [app/tools/slides.py](../../app/tools/slides.py) — `main()`

## Related

- [Mockups](mockups.md) · [Mockups engine](mockups-engine.md) · [Photo mockups](photo-mockups.md) · [Workshop](workshop.md) · [Rail](rail.md) · [Security](../security.md)
