---
name: book-cover
description: "Write a Workshop book's cover prompt (pipeline/books/<book>/agent/cover-prompts-json.md) — one 2:1 full-scene picture with the painted title, a big empty room for the name and the characters in the layout guide's yellow zone — after the book's pictures are generated. Use when the owner says «обкладинка №48», «промпт обкладинки», sends best frames for a cover, or asks to test or adapt a cover prompt."
argument-hint: "[book number]"
---

# The cover prompt

The cover is one 2:1 picture. Its **right part** is the front (title and name, centred at ¾ of the width), the **left
part** the back, the **middle** the spine. Book Studio's tool «Обкладинка» pastes, in order: a **layout guide** (Image 1
— a position map), the **reference** (Image 2), then this prompt with the guide's words added; then it lays the picture
on the printer's template and the margins are outpainted. Paths are relative to the repository root
(`${CLAUDE_SKILL_DIR}/../../..`).

## Steps

1. **Ask for the best frames** (one short question in Ukrainian), unless he already sent them: «Надішліть, будь ласка,
   найкращі кадри з розворотів для обкладинки.» Match his screenshots to `originals/spread-NN-NN.jpg`.
2. **The reference**: `python "${CLAUDE_SKILL_DIR}/scripts/stack_frames.py" "pipeline/books/<folder>" 04-05 06-07 …` (`python` = the portable
   `../runtime/python/python.exe`) →
   `agent/ref_cover_….jpg` (one frame or several stacked; the tool takes one picture).
3. **Read**: the title (the first line under `## Cover` in `agent/book-text.md`), `input.md`, the blueprint's header and
   the animals' / hero's fixed description, the style block of the book's prompts (`spread-prompts-json.md`), and the
   example closest to this title: [examples/](examples/).
4. **Pick the layout by the title** — the tool picks the same guide by itself:

   | Title | Guide | Paint | The empty room for the name |
   |---|---|---|---|
   | starts with `{Name}` («{Name}'s Night Before Christmas») | `wide-name-title` | «Night Before Christmas» | above the title |
   | ends with `{Name}` («Welcome to the World, Little {Name}») | `wide-title-name` | «Welcome to the World, Little» | under the title |
   | words on both sides («Mommy & {Name}: Our First Christmas») | `wide-title-name-title` | a very large «Mommy», a small «&» alone under it; a small last line «Our First Christmas» (≈⅓ of the big word) | between them |

   The name is never painted (he sets it in Canva) and is the selling element — its room is as big as the title's main
   word. **His own title layout wins** when he gives one (book 46: «Grandma» large, a small «&», then the room — and no
   tail).
5. **Write** `agent/cover-prompts-json.md` by the formula below; one prompt, `"id": "final-wide-image"`.
6. **Check**: the hook runs the book check after the write; 0 FAILs. Tell him: «Промпт обкладинки готовий — відкрийте
   «Обкладинка», «Генерувати» сам покладе в буфер схему, референс і промпт.»

When he wants to **test in chat first** (he often does): give the full prompt in the reply with a `layout_guide` field
written out, the guide picture path (`app/web/img/cover-guides/<guide>.png`) as Image 1 and the reference as Image 2;
keep the book file for after the test.

## The formula (tested on books 41, 50, 48 — the owner: «ідеал»)

- **Composition first.** `task`: "Composition is the top priority: place everything exactly where the position map in
  Image 1 shows — the main characters only inside its yellow area. Image 1 gives positions only; none of its colors
  appear in the picture." Never write a `layout_guide` field into the book file — the tool adds it.
- **The scene fills the picture**, edge to edge: no cream ground, vignette, frame, light patch or cloud behind the text.
- **One smooth background behind the right part** — an even wall, an open sky, snow: "the same even wall color / smooth
  sky wash as around it". Light comes **only from real sources** (lamps, fire, window, moon, the sky). Never "a soft
  glow behind the title / the room / the characters", never a spotlight — that printed the guide's patches onto the
  background.
- **Title**: `title.text`, a `spelling` field letter by letter + "nothing else written anywhere", placement "where the
  brown-grey area of Image 1 is, centered at three quarters of the image width", lettering in the medium with "a thin
  soft light halo hugging only the outline of each letter … no colored cloud or haze behind the words"; a small
  ornament is welcome. On a light background a deep color (cranberry, rosy coral), not cream.
- **The name's room** (`open_space`): "where the pale blue area of Image 1 is", "big, because a name will be set there
  later as large as [the main word], for later typography"; rule: "simply the [wall / sky] continuing … nothing painted
  in it: no letters, no objects, no stars, no sparkles, no haze, no lighter or bluer band; NOT a panel, cloud, ribbon,
  glow or box".
- **Characters — inside the yellow area only**, one compact group, each placed **in fractions of the width** (one face
  at ≈⅔, the other at ≈⅚, the key prop exactly at ¾ under the middle of the title's main word), everything they hold
  inside too, "sized to fit inside the yellow area — smaller rather than spilling out of it", "no spotlight or glow
  behind them". **Few characters** (the hero and the closest ones, at most 3–7 small animals) — a crowd breeds
  artifacts. Soft words ("a gentle hint, not a box") let them drift toward the spine.
- **Three bands across the width** in `scene`: `left_area` "from the left edge to about two fifths of the image width,
  with no characters" — the story's things, any tall tree at ≈¼ with branches ending before ⅖; `middle` "from about two
  fifths to about three fifths: only the plain [wall / sky] and the floor/ground — no tree, key object, characters or
  faces"; the right band — room, title, characters on one line at ¾. `composition` names the three bands.
- **Edges** calm and simple (the margins are outpainted from them); the title, the room and every face ≥ ⅒ of the height
  from the top, bottom and right edges.
- **Reference**: `reference_image` = the `ref_cover_….jpg` file name (the tool renames it «Image 2»); `reference_rule`:
  "Use the reference picture ONLY for how the characters look and for the painting style … Do NOT copy its composition
  or where the characters stand — positions come only from the position map." With several stacked frames: "holds N
  earlier illustrations … one single continuous scene".
- **Style**: the book's full preset (the same `style{}` as its prompts); override `washes` and `light` (one smooth
  background, real light), `overlay_behavior` (the room is just the plain wall / sky), `detail` ("medium detail,
  charming but never busy" + this picture's things); thin floating sparkles / dust / fireflies to "a few".
- **Negatives**: "any other text", "a name", "extra letters", "misspelled title", "subtitle", "letters in the left
  area", "anything painted in the empty [wall / sky] …", "a white box, panel, cloud, plaque, ribbon or banner behind the
  title"; the map's traces — "visible traces of the position map", "a pale blue band or haze on the [wall / sky]", "a
  pink, red or brown cloud or haze behind the title", "a yellow glow or spotlight behind the characters", "lighter or
  tinted rounded rectangles on the [wall / sky]", "colored patches on the [wall / sky]", "uneven blotchy [wall / sky]";
  the positions — "characters outside the yellow area", "characters shifted to the left of the title", "characters in
  the middle of the image width", "characters in the left area", "copying the composition of the reference picture",
  "characters pressed against the right edge", "a tree crossing the middle of the image width", "a tree, key object or
  face in the center of the width"; and "a vertical line through the image", "a frame or border", "a vignette", "a cream
  background", the text guards and the preset's negatives. For the middle-name title also "the title lines joined
  together", "a large ampersand", "the small line as large as the big word".
- **Generator language**: one standalone 2:1 panoramic illustration — no trigger words even in negatives
  ([master-prompt.md](../../../pipeline/knowledge/master-prompt.md#generator-language)). The book check wants the
  wraparound words: `2:1`, continuous/uninterrupted, right, left, `upper right`, "for later typography".

Flat schema: `id, task, aspect_ratio, canvas, reference_image, reference_rule, title{text, spelling, placement,
lettering, ornament}, open_space{placement, rule}, character{subject, pose, expression}, scene{name, location,
left_area, middle, composition}, style{}, emotional_goal, negative[], output`.

Older formulas (cream ground, two squares) are in [history.md](history.md) — only when the owner asks for one by name.
