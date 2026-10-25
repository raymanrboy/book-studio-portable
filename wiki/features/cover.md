---
title: The cover — its own tool («Обкладинка»), two squares made into a Gelato cover without the generator
type: feature
updated: 2026-10-25
code:
  - app/studio/workshop/cover.py
  - app/web/js/pages/cover.js
  - app/web/img/cover-guides/
---
# Обкладинка

> The book's cover is a step of its own, like the Mockups and the photo mockups (the owner, 2026-10-25: "етап обкладинки
> тепер окремий… це повноцінний крок"). A tool in «Інструменти» that works on one Workshop book; the Workshop's path
> strip step «Обкладинка» opens it with the book. The cover card that stood under the rows (after page 30) moved here.
> Why the squares — [decisions](../decisions.md) (2026-10-24/25).

## Where

- **«Інструменти» → «Обкладинка»** (`#/cover`): which book? — the Workshop's books as tiles; a click opens `#/cover/<book>`.
- **A Workshop book, step «Обкладинка»** (`coverBody()` in workshop-book.js): what the book has (the Cover.png shown, how it
  was made) and «Зробити / Відкрити обкладинку». Back from the tool leads to the book.

## Two ways — the switch in the page's head

The book's own choice, `"coverMode"` in `book.json` (`cover_mode()`): the owner's switch, or the last picture put in,
wins; until then Agent 6's prompts decide — only `title-square` + `quiet-square` → «Два квадрати» (Agent 6 asks the owner
«2:1 чи два квадрати?» before writing).

### «Два квадрати» (the default for new books)

- **The spread on top**: the cover made of the squares (`pictures/Cover.png`, 5409×2906 px, 300 dpi — Gelato's 8×8
  hardcover, 458×246 mm); before both squares are in, the squares shown where they will stand. Gelato's lines as a toggle
  (wrap, hinges, spine, the two squares — `squares_guides()`). **М'який край 0 · 2 · 4 · 6 мм** — the squares' soft edge;
  a change makes the cover again at once.
- **Two columns, Задня · Лицьова**: each its square frame (drop, «Обрати файл», «Ще раз», trash with «Скасувати»), its
  **layout guide** (thumbnails — the owner, 2026-10-25: "схеми дають значно більше контролю"), Agent 6's prompt.
  The front has its **reference** chip: the picture Agent 6 named in the prompt (`agent/ref_cover_….jpg`, by default), a
  spread of the book, or none.
- **«Генерувати»** puts into the clipboard, one by one (Ctrl+V in Chrome switches): the front — the reference, the guide,
  the prompt; the back — the finished front, the guide, the prompt. The prompt gets the guide's words as `layout_guide`
  right after `reference_rule`, with the guide's number among the pictures (`prompt_with_guide()`). The caught front goes
  on to the back by itself (`generate.squares_next()`).
- **Both squares in → the cover is made at once, no generator** (`cover.assemble()` → `compose()`): the squares on Gelato's
  spread (each side with its hinge a 206 mm square: back 20–226 mm, front 232–438 mm, top 20–226 mm); the spine and the
  wrap filled from a **4 mm ring along each square's edge** (what is inside never tints them) — averaged down and filled
  back up (push-pull), blurred ~1.5 mm, so the spine passes smoothly from the back's colours to the front's; the squares on
  top with the soft edge. Works best when the scene dissolves into the cream before the square's edges (the prompts ask
  it; the guides show it).
- A 2:1 Cover.png already there stays until both squares are in. A new square makes the cover again; taking one away
  leaves the cover; «Скасувати» makes it again from the squares as they are; switching back to «Два квадрати» makes it
  again too, and «Скласти обкладинку» shows when both squares are there but no cover is made of them. A 2:1 book's
  cover is never overwritten by the squares (`assemble()` checks the mode). A wide picture can't be put in this way (it
  says to switch to 2:1).
- The back is generated only after the front (its reference); with no reference picture pasted, the prompt loses its
  `reference_image` / `reference_rule`, so «the attached image» never means the guide.
- **Not upscaled**: the squares are stretched to 2433 px (206 mm at 300 dpi) as they come — Nano Banana's 2K squares
  (2048 px) are fine, 1K ones (1024 px) are soft. The upscaler never remakes a cover made of squares.

### 2:1 (the old way, unchanged)

The two stages the Workshop had since 2026-09-26: the wide picture from Agent 6's prompt, then its margins outpainted on
the printer's template → Cover.png 5370×2850 ([workshop](workshop.md#a-picture-into-its-row)). «Референс у буфер»,
«Без полів», upscaling — as before.

## The guides

Pictures of the program (`app/web/img/cover-guides/`, 1024 px): a cream square with soft shapes — **brown-grey** the title,
**pale blue** the name's room (plain paper, the name goes on in Canva), **green-grey** the scene. `GUIDES` in cover.py:
each one's side, its label and its words for the prompt. Tested on book 46 (2026-10-25): the title + scene guide was the
best, the scene-only one very good; without a guide too little room for the name.

| Guide | When |
|---|---|
| `front-title-scene` | the default front: the title, open room under it, the scene |
| `front-title-name-scene` | the title, the name under it — «Grandma & {Name}» |
| `front-name-title-scene` | the name above the title — «{Name}'s Moonlit Garden» |
| `front-scene` | only where the scene goes; the top is the prompt's |
| `back-scene` | the back: the scene, the top open |

## Where in the code

- [app/studio/workshop/cover.py](../../app/studio/workshop/cover.py) — `GUIDES`, `DEFAULT_GUIDES`, `FEATHERS`, `settings()`, `set_settings()`, `tool_state()`, `reference()`, `prompt_with_guide()`, `items()`, `compose()`, `assemble()`
- [app/web/js/pages/cover.js](../../app/web/js/pages/cover.js) — `mount()`, `pickBook()`, `bookPage()` (`spreadCard()`, `squareCol()`, `guidePicker()`, `refChip()`, `wideBody()`)
- [app/studio/workshop/rows.py](../../app/studio/workshop/rows.py) — `SQUARES`, `SQUARE_KEYS`, `SQUARE_IDS`, `squares_layout()`, `squares_guides()`, `cover_mode()`, `cover_state()`
- [app/studio/workshop/pictures.py](../../app/studio/workshop/pictures.py) — `place()` (the squares), `set_cover_mode()`, `remove()`, `restore()`
- Route `POST /api/workshop/books/<id>/cover-squares` ([api-routes](../architecture/api-routes.md)); the switch — `cover-mode`.
