---
title: Cover tool
type: feature
updated: 2026-11-12
code:
  - app/studio/workshop/cover.py
  - app/studio/workshop/rows.py
  - app/studio/workshop/pictures.py
  - app/web/js/pages/cover.js
  - app/web/img/cover-guides/
---
# Cover («Обкладинка»)

> The book's cover is a step of its own: a tool under «Інструменти» (`#/cover`, a book at `#/cover/<book>`) that works on one Workshop book. The Workshop's path-strip step «Обкладинка» opens it with the book (`coverBody()` shows what the book has and «Зробити / Відкрити обкладинку»); back leads to the book. The method for the cover prompt is the `book-cover` skill (`.claude/skills/book-cover/SKILL.md`).

## Two stages
1. **Картинка** — the skill's 2:1 prompt (the scene on the whole picture, the title painted in the right area, a big empty room for the name, the characters in the guide's yellow zone). **«Генерувати»** puts into the clipboard, one by one (Ctrl+V in Chrome advances): **the layout guide** (always Image 1), **the reference** (Image 2), **the prompt** (`items()`, `prompt_with_guide()`). The guide's words are put into the prompt as `layout_guide` after `canvas`, and `reference_image` is renamed «Image 2 (the reference picture)» (plain «Image 1» without a guide). With no reference the prompt loses its `reference_image` / `reference_rule`.
   - **Reference chip**: the picture the cover prompt names (`agent/ref_cover_….jpg`, the default), a spread of the book, or none. «Референс у буфер» works only when that file lies right in `agent/`.
   - **«Схема»** under the picture: the guides as thumbnails and «без схеми».
2. **Поля** — the caught picture (`originals/cover-art.*`) is laid on **the printer's template** with white all round: a canvas `MARGIN_ROOM` (×1.06) the template's size, so margins are about 1.7× the template's own at the sides and 1.4× at top and bottom. On `Cover.png` the picture ends about 0.46″ inside the trim line at the sides and about 0.13″ at top and bottom. The result is `cover-expanded.png`; the generator fills the margins (outpaint: that picture and `outpaint_prompt()`, with the template's lines as a toggle) and the answer becomes `pictures/Cover.png`, exactly 5370×2850 px at 300 dpi (`fit_template()`). «Без полів» takes the picture as it is. Upscaling: [workshop](workshop.md).

`TEMPLATE` (`rows.py`): hardcover 8×8 with wrap 17.90″×9.50″, finished 16.40″×8.00″, spine 0.40″. The cover file for mockups is the finished cover without the wrap ([photo mockups](photo-mockups.md)).

The book's choices live in `book.json` under `"coverTool"`: `{"guide": name | "none", "ref": "" | "none" | "spreadN"}` (`settings()`, `set_settings()`, `POST /api/workshop/books/<id>/cover-tool`).

## The guides
Pictures in `app/web/img/cover-guides/` (2048×1024): the whole field **green-grey** = the scene everywhere; in the right area (the book's front) shapes stacked on one centre line at ¾ of the width: **pale blue** = room for the name (plain background; the name goes on in Canva), **brown-grey** = the title, **yellow** = the main characters. `GUIDES` in `cover.py` gives each one's label and its words for the prompt: a **strict position map** — characters only inside the yellow area, none left of it, one centre line, **no trace of the map** in the picture.

| Guide | Zones from the top | Default when |
|---|---|---|
| `wide-name-title` | name 72–232, title 248–440, characters 456–952 | the title starts with `{Name}` |
| `wide-title-name` | title 72–330 (up to three lines), name 346–490, characters 506–952 | nothing but marks follows `{Name}`, or the title has none |
| `wide-title-name-title` | big word and small «&» 60–262, name 274–414, small last line 426–486, characters 500–960 | words stand on both sides of `{Name}` |

`default_guide()` follows the title; a guide the owner picks (or «без схеми») is kept for the book. A title with `{Name}` in the middle of a phrase the default does not fit (book 46, «Grandma & {Name}») needs `wide-title-name` picked by hand.

## The look
The outer picture sits on a milky cream ground with the characters low and small; another ground only on request. A white-ground cover keeps the upper 40–55 % empty for the title and the characters large below it. The calm look is the owner's approved formula; the prompt method is in the skill.

## Cover of two squares (an option)
A book marked `"squares": true` in `book.json` keeps a `Cover.png` made of two squares: it is shown with Gelato's lines (`squares_guides()`, 458×246 mm), the tile shows only its face (`thumb.face`), the upscaler never remakes it, and its square prompts (`OLD_SQUARE_IDS`) are set aside with a note. A new cover made with the two-stage method replaces it.

## Why
- One way only: the 2:1 picture plus a guide, then outpaint. Outpaint margins exist because the picture alone barely fills the printer template.
- The guide is always Image 1: the generator holds the first picture's layout best.
- A strict position map, because soft words let characters drift toward the spine, and wording like "paint over the guide" or "glow behind the title" prints the guide's patches.
- The guide for a title with `{Name}` inside the phrase is picked by hand because the default cannot read the words.

## Where in the code
- [app/studio/workshop/cover.py](../../app/studio/workshop/cover.py) — `GUIDES`, `STATE_KEY`, `default_guide()`, `prompt_with_guide()`, `items()`
- [app/studio/workshop/rows.py](../../app/studio/workshop/rows.py) — `TEMPLATE`, `MARGIN_ROOM`, `template_layout()`, `outpaint_prompt()`, `cover_state()`, `squares_guides()`
- [app/studio/workshop/pictures.py](../../app/studio/workshop/pictures.py) — `fit_template()`
- [app/web/js/pages/cover.js](../../app/web/js/pages/cover.js) — `mount()`, `pickBook()`, `bookPage()`

## Related
- [Workshop](workshop.md) · [Photo mockups](photo-mockups.md) · [Gelato](../integrations/gelato.md) · [Workshop books](../owner/workshop-books.md)
