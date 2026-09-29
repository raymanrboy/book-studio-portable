---
name: listing-slides
description: Change, look at and bake Book Studio's six Etsy listing slides (the «Слайди для лістингу» made after the Mockups) through their files — move/turn/resize an element, change a text, colour, shadow, arrow, sticker, the book's numbers, a slide's mockup; save or put on a scheme (Nature, Night…); bake the pictures. Use when the owner asks to edit a listing slide, a book's slides or a scheme in words («підвинь», «зміни текст на слайді», «зроби тінь сильнішою», «запікай») instead of in the editor.
---

# Listing slides — working through the files

The owner makes the six square 2000×2000 Etsy pictures of a book in Book Studio: the Workshop book's «Мокапи» → the
Mockups page → «Зробити слайди» → the editor (`#/slides/<book>/<1–6>`). A book's slides live in its Workshop folder
(`pipeline/books/<n>.<slug>/mockups/slides/`); their look is a **scheme** — the six scenes as a whole, named (Nature —
the default for new books, Night, his own). Sometimes he'd rather tell an agent what to change (29.09.2026:
"sometimes it will be easier for me to work through an LLM"). You change the **same files** the editor saves; an open
editor picks your change up by itself within 1.5 s («Слайд змінено ззовні — показано новий»), so he never has to
reload. How it all works: `wiki/features/slides.md`.

Reply to the owner in Ukrainian, in plain words. Run everything from the repository root with
`PYTHONIOENCODING=utf-8`.

## 1. Find the slide

```
python app/tools/slides.py list
```

prints the schemes (`scheme:nature  Nature — for new books`, `scheme:night  Night`, …) and the books' slides — the
Workshop books first (`25.sleepy-trucks-bedtime  №25 Sleepy trucks bedtime  <its mockups folder>  books: … pictures: …
numbers: …`), then older sets by time. "The slides" = the book he names («№25», «сонні вантажівки»), else the newest.
"For all new books" / «шаблон» / the default scheme = `template` (it edits the default scheme in place).

Slides are `slide1 … slide6`:

| № | What's on it |
|---|---|
| 1 | Made just for them — two Open 1 spreads, «{pages} unique pages» sticker, arrows |
| 2 | Choose your format — Cover 1 twice (5×5, 8×8), a ribbon «2 sizes & covers», arrows |
| 3 | Dedication & afterword — the Dedication mockup (the desk and the book; its floor see-through, so the slide's background shows), page 30 in a scalloped frame, «Last page» on an arc |
| 4 | Unique little poems — two Open 1 spreads, «{poems} unique little poems» sticker |
| 5 | Personalization made simple — one Open 2, two step cards |
| 6 | Thank you for shopping small — one Open 2, a heart with a thumbs-up |

```
python app/tools/slides.py path slide3 --set <id|template>
```

prints the scene's JSON file. A scheme's own files: `app/data/slides/schemes/<key>/slide1…6.json` (+ `scheme.json`:
name, default, colours by role).

## 2. Look before and after — always

```
python app/tools/slides.py render slide3 --set <id|template> --to "<scratchpad>/slide3.png"
```

draws the slide exactly as it will be baked (headless Edge, the same drawing code, ~3 s), with the book's own
mockups. Open the PNG with Read and check it yourself before telling the owner it's done; show him the picture
(SendUserFile) when the change is visual. His original Canva pictures, for comparison:
`examples\Canva resoult\1.png … 6.png` in the Book Studio folder (and his sample mockups in `examples\Photoshop prep\`).

## 3. Change the scene file

A scene is `{"id": "slide3", "title": "…", "bg": "#eedec7", "items": [ … ]}` — the stage is **1000×1000**, every
element's `x`, `y` is its **centre**, `rot` degrees clockwise. Items are drawn in order: **later = in front**.
Find an element by its `name` (the names the owner sees in the editor's layers: «Заголовок», «Наліпка «24»»,
«Розворот верхній», «Стрілка до нижнього»…). Edit with Python (read JSON, change, write back with
`ensure_ascii=False, indent=1`, UTF-8) — never by hand-mangling text. Keep every other field as it is.

Every element may have: `name`, `x`, `y`, `rot`, `flipX` / `flipY` (mirror ↔ / ↕), `opacity` (0–1), `hidden`,
`locked`, `uid`. By kind:

| `type` | Fields (default) |
|---|---|
| `book` | `slot` — which mockup: `open1:1…4`, `open2:1…2`, `cover`; `w` width (height follows the book); `bake` — the shadow from Photoshop (0.6); `shadow` — the extra soft lift (0.18) |
| `image` | `slot`: `dedication` or `page30`; `w`, `h`; `shape: "scallop"` (a wavy die-cut frame) with `bumps` (10), `depth` (0.07); `rim` — white edge px; `shadow: false` turns its shadow off |
| `text` | `text` (`\n` = new line; `{pages}` / `{poems}` = the book's numbers); `size` letter size; `w` frame width; `lh` line height (1.18); `align` left/center/right; `color` (#fff); `tshadow` text shadow (0.7); `arc` degrees the line bends (+ arch ∩, − smile ∪, 0 straight); `font: "sans"` for plain Segoe UI (else Comica, capitals, stretched 1.32×) |
| `sticker` | scalloped die-cut badge: `r` radius; `color`; `lines: [{"t": "24", "k": 2.5}, {"t": "unique"}, …]` — `k` makes a line bigger; text fits itself evenly; `pad` margin (0.22); `tape: [dx, angle]` washi tape (omit = none); `bumps` (14); `tshadow` |
| `ribbon` | bookmark with a V-notch: `w`, `h`, `color`, `lines` (as sticker), `pad` (0.16), `rim` (7), `notch` (0.13), `tshadow` |
| `arrow` | `pts` — first and last point (in a `w0`×`h0` box, stretched to `w`×`h`); `bow` arc (−0.5…0.5, sign = side); `loop` round loop size (0 = none), `loopAt` where (0–1, 0.45), `loopDir` 1/−1; `sw` line width (7); `solid: true` sharp filled head; `color` (#6b3a3a); `tshadow` (0.45) |
| `heart` | `w`, `h`, `color`, `icon`: `thumb` / `heart`, `iconSize` (0.4) |
| `sparkle` | four-point star: `size`, `color` |
| `band` | torn-paper strip: `w`, `h`, `color`, `seed` (edge pattern), `rim` white fibre edge (8) |
| `blob` | soft stain: `w`, `h`, `color`, `seed` |
| `dashes` | `w`, `h`, `count` (11), `dash` length (62), `color` |
| `leaves` | the faint window-leaf shadow (multiply): `w`, `h`, `opacity` |
| `grain` | paper grain over everything: `opacity` |

The palette of his design: cream `#eedec7`, olive `#a2a066`, peach `#e8c59d`, brown `#6b3a3a`, white `#ffffff`.

Recipes:
- **Move / turn / resize**: `x`, `y` (+ right/down), `rot`; size — `w` (and `h`), `r` for a sticker, `size` for text
  and sparkles. "A bit" ≈ 10–20 units.
- **Text**: `text` (or a sticker's/ribbon's `lines[i].t`); letters bigger — `size`; the shadow stronger — `tshadow`.
- **A book's shadow lighter**: `bake` down (e.g. 0.4) and/or `shadow` down.
- **Another mockup on a slide**: the book's `slot` (the set's `books` in `slides.py list` say which exist).
- **The book's numbers** (24 pages, 11 poems) live in the set, not the scene: the book's `mockups/slides/set.json` (an older set: `app/data/slides/sets/<id>/set.json`)
  → `numbers: {"pages": …, "poems": …}`; the texts say `{pages}` / `{poems}`.
- **Add** an element: copy a similar one, give it a new `name` and `uid`, insert it where it should sit in depth.
- **Remove**: take it out of `items` (or `"hidden": true` if he may want it back).

## 4. Schemes, and baking

- **A scheme** = the whole look of the six (colours, positions, shadows, texts). "Make this book look like Night" →
  write each of the scheme's six scenes over the book's (`schemes/night/slideN.json` → the book's
  `scenes/slideN.json`) and set `"scheme": "night"` in the book's `set.json` — the editor's «Схема ▾» does exactly
  that; the book's mockups (slots) and numbers stay. Another book's slides work the same way (a preset: "like the
  other bedtime book").
- "Save this as a scheme" → copy the book's six scenes into `app/data/slides/schemes/<key>/` with a `scheme.json`
  (`{"name": "…", "default": false}`) — the editor's «Зберегти ці слайди як схему…». "New books should start from it"
  → `"default": true` there and false in every other `scheme.json` (only one default).
- "Back to how it was" → the editor's «Скинути слайд» (a book's slide → its scheme; the default scheme → the first
  design in `app/studio/slides/design/`).
- **Elements are locked by default** (no `locked` = locked; `"locked": false` = the mouse may move it) — that only
  concerns the mouse in the editor; you change `x`, `y` in the file either way.
- **«Запікай» / bake** — the book's six (or some) pictures into its folder, over the ones made before:
  ```
  python app/tools/slides.py bake --set <book>            # all six
  python app/tools/slides.py bake slide2 slide3 --set <book>
  ```
  They land as `Listing 1.png … Listing 6.png` in the book's `mockups\` (the Mockups' card and the editor's
  «Зберегти картинки» do the same). Tell him where they are.

## 5. Rules

- The mockup templates `D:\Roman\Desktop\Трафарети мастхев` are **only read** (the cut-out reads their book mask) —
  never edit, save over or delete them.
- Never write over the owner's own pictures; the program's `Listing N.png` are its own and are replaced by a bake.
- `app/data/` never goes into git. Commit only when the owner asks.
- Don't open Etsy from this PC.
- If a change is about how the program works (a new kind of element, the editor), it is a code task: read
  `wiki/features/slides.md` and follow AGENTS.md (tests, wiki, log).
