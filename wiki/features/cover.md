---
title: The cover — its own tool («Обкладинка»): a 2:1 picture with a layout guide, then its margins outpainted
type: feature
updated: 2026-11-01
code:
  - app/studio/workshop/cover.py
  - app/web/js/pages/cover.js
  - app/web/img/cover-guides/
---
# Обкладинка

> The book's cover is a step of its own, like the Mockups and the photo mockups (the owner: "етап обкладинки
> тепер окремий… це повноцінний крок"). A tool in «Інструменти» that works on one Workshop book; the Workshop's path
> strip step «Обкладинка» opens it with the book. One way only — the 2:1 picture with a layout guide ([decisions](../decisions.md)).

## Where

- **«Інструменти» → «Обкладинка»** (`#/cover`): which book? — the Workshop's books as tiles; a click opens `#/cover/<book>`.
- **A Workshop book, step «Обкладинка»** (`coverBody()` in workshop-book.js): what the book has (the Cover.png shown) and
  «Зробити / Відкрити обкладинку». Back from the tool leads to the book.

## Two stages

The cover is made in two stages (the rest of a picture's way into its row — [workshop](workshop.md#a-picture-into-its-row)):

1. **Картинка** — Agent 6's 2:1 prompt (the full-scene formula: the scene on the whole picture, the title painted in the
   right area, a big empty room for the name, the characters in the guide's yellow zone —
   `pipeline/playbook/agents/6-wraparound-image-director.md`).
   **«Генерувати»** puts into the clipboard, one by one (Ctrl+V in Chrome switches): **the layout guide** (always
   Image 1 — the generator holds the first picture's layout best), **the reference** (Image 2), **the prompt** with the
   guide's words put in as `layout_guide` right after `canvas` and its `reference_image` renamed «Image 2 (the reference
   picture)» — «Image 1» without a guide (`cover.items()`, `prompt_with_guide()`). With no reference picture pasted the
   prompt loses its `reference_image` / `reference_rule`.
   - **The reference chip** (beside «Генерувати»): the picture Agent 6 named in the prompt (`agent/ref_cover_….jpg`, by
     default), a spread of the book, or none.
   - **«Схема»** under the picture: the guides as thumbnails and «без схеми».
2. **Поля** — the caught picture (`originals/cover-art.*`) goes on by itself: laid on **the printer's template** (`TEMPLATE`:
   8×8 hardcover, 17.90″×9.50″ with the wrap, finished 16.40″×8.00″; `template_layout()`) with white all round →
   `cover-expanded.png`; the generator fills the margins (outpaint: that picture and `outpaint_prompt()`, the template's
   lines as a toggle) → `pictures/Cover.png`, exactly 5370×2850 px, 300 dpi (`fit_template()`). «Без полів» takes the
   picture as it is. «Референс у буфер» puts the picture the cover prompt names as its `reference_image` (Agent 6's
   `agent/ref_cover_….jpg`) into the clipboard — only when it lies right in `agent/`; the tool pastes it itself, after the guide, with
   «Генерувати». Upscaling — [workshop](workshop.md#upscaling).

The book's choices: `"coverTool"` in `book.json` — `{"guide": name | "none", "ref": "" | "none" | "spreadN"}`
(`settings()`, `set_settings()`, route `POST …/cover-tool`).

## The guides

Pictures of the program (`app/web/img/cover-guides/`, 2048×1024): the whole field **green-grey** = the scene everywhere;
in the right area (the front on the book) three shapes stacked with small gaps on one centre line at ¾ of the width
(x = 1536): a **pale blue** one = the name's room (plain background, the name goes on in Canva), a **brown-grey** one =
the title, a **yellow** one = the main characters (since 2026-11-01; drawn by `make_characters_guide.py` /
`make_title_name_characters_guide.py` in `D:\Roman\Desktop\Cover Squares Test\guides\`). `GUIDES` in cover.py: each
one's label and its words for the prompt — a **strict position map**: the characters only inside the yellow area, none
left of it, one centre line, and **no trace of the map** in the picture. The owner's tests on books 41 and 50: soft words
let the characters drift toward the spine; "paint over the guide" and a "glow behind the title" printed its patches.

| Guide | Zones from the top | When |
|---|---|---|
| `wide-name-title` | name y 72–232, title 248–440, characters 456–952 | the default when the title starts with `{Name}` («{Name}'s Night Before Christmas») |
| `wide-title-name` | title y 72–330 (up to three lines), name 346–490, characters 506–952 | the default otherwise («Welcome to the World, Little {Name}») |

The default follows the title (`default_guide()`); a guide the owner picks (or «без схеми») is kept for the book.

## A cover made of two squares (2026-10-25…27)

Books whose Cover.png was once made of two squares (marked `squares` in `cover-wrap`) keep it until a new
cover comes: shown with Gelato's lines (`squares_guides()`, 458×246 mm), the tile shows only its face
(`summary()` → `thumb.face`, CSS `.book-cover img.face`), the upscaler never remakes it. Their square prompts in
`cover-prompts-json.md` (`title-square`, `quiet-square`) are left aside with a note (`OLD_SQUARE_IDS`); the book check still
takes them as 1:1. The squares' pictures (`originals/cover-front.*`, `cover-back.*`) stay where they are, unused.

## Where in the code

- [app/studio/workshop/cover.py](../../app/studio/workshop/cover.py) — `GUIDES`, `STATE_KEY`, `default_guide()`, `settings()`, `set_settings()`, `tool_state()`, `reference()`, `prompt_with_guide()`, `items()`
- [app/web/js/pages/cover.js](../../app/web/js/pages/cover.js) — `mount()`, `pickBook()`, `bookPage()` (`refChip()`, `guidePicker()`, `wideBody()`, `gelatoLines()`)
- [app/studio/workshop/rows.py](../../app/studio/workshop/rows.py) — `cover_state()`, `outpaint_prompt()`, `TEMPLATE`, `template_layout()`, `SQUARES`, `OLD_SQUARE_IDS`, `squares_guides()`
- [app/studio/workshop/pictures.py](../../app/studio/workshop/pictures.py) — `fit_template()`
- [app/studio/workshop/generate.py](../../app/studio/workshop/generate.py) — `_items()` (the cover → `cover.items()`)
- Route `POST /api/workshop/books/<id>/cover-tool` ([api-routes](../architecture/api-routes.md)).
