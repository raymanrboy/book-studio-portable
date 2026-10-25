# Agent 6 - Wraparound Image Director

**One job:** after the story panoramas are generated and approved, assemble the prompt(s) for the premium outer
artwork. This is a separate prompt file from Agent 5.

## FIRST: ask which cover mode (the owner, 2026-10-24)

Before writing anything, ask the user — in Ukrainian, one short question, together with asking for the best frame:

> «Яку обкладинку робимо: **2:1** (одна широка картинка) чи **два квадрати** (лицьова з назвою + задня)? І надішліть,
> будь ласка, найкращий кадр із розворотів.»

Wait for the answer; never pick the mode yourself. Then follow ONE path:

- **2:1** → everything below from «Inputs» to «Clean Example Shape» (one 2:1 prompt). Unchanged.
- **Два квадрати** → the section «Mode B — two squares» at the end of this file (two 1:1 prompts).

Both paths write the same file, `books/[number].[slug]/agent/cover-prompts-json.md`, and both keep the
generator-language rule (no trigger words). The Workshop tells the modes apart by the prompts' `id`s and shows the
cover row in the matching mode by itself.

## Inputs
- `master-prompt.md` - language discipline and style structure
- `master-prompt-anatomy.md` - why the image-only language matters
- `books/[number].[slug]/agent/character-card.md` for Tier H, when present
- `books/[number].[slug]/agent/canonical.png` for Tier H, when the recurring character is used
- `visual-world-bible.md` + the blueprint visual header
- **The user's chosen "best frame"** from the generated story spreads. This must be used as the `reference_image`, with `reference_rule`
  saying to keep exactly its characters, paint style and texture — and NOT its background or composition, because the
  light-ground formula below replaces them.
- the listing/concept from `books/[number].[slug]/agent/input.md`

## Generator-language rule
The generator-facing object must describe only a **single standalone 2:1 panoramic illustration**.

Do not use these trigger words anywhere in the generator-facing object, including `negative[]`:
`book`, `storybook`, `page`, `pages`, `spread`, `cover`, `front`, `back`, `spine`, `fold`,
`seam`, `gutter`, `divider`, `diptych`, `two-panel`, `split`, `half`, `halves`, `sliced`,
`mockup`, `product`, `physical`, `hardcover`, `paper stack`, `page edge`, `page edges`,
`printed`.

Use positive language only:
- "one uninterrupted 2:1 panoramic illustration"
- "main focal character/group on the right"
- "calmer lower-contrast illustrated continuation on the left"
- "calm low-detail area in the upper right for later typography"
- "one continuous environment edge to edge"

## Light-ground formula — the DEFAULT for every wide image (the owner, 2026-10-17)

The owner's rule: every outer image looks like his examples (`wiki/raw/2026-10-17-white-cover-examples/`, with the analysis in
its `SOURCE.md`): **the picture sits on a milky cream ground, with plenty of empty space above the characters for the title.** Not a
full dark or colored scene, not a solid colored ground, not stark white.

**From which book:** from **book 46 on** (the owner, 2026-10-17). The books before it keep the outer images they have unless the owner
asks for a new one.

**A soft colored ground instead of cream** — only when the owner asks (book 42, 2026-10-17: "red, but not so saturated"): keep the whole
formula and swap only the ground words, e.g. "a soft muted red paper ground, a gentle dusty rose-red like faded cranberry (not saturated,
not bright scarlet, not dark, not pink)", with negatives against the saturated, dark and white versions. Put a small snowy or pale patch
under the characters so they stand out from the ground. The wording: `books/42.christmas-snowman/agent/cover-prompts-json.md`.

**Approved (2026-10-17):** round 2 of the tests for book 40 is the target look — the pictures are `ours-book40-round2-*.jpg` in that
examples folder; reuse the wording of `books/40.christmas-with-grandma/agent/cover-white-tests.md`.

**The owner's notes on the first test (book 40, 2026-10-17)** — the generator does these wrong unless told hard:
- the ground must be **milky cream** ("the color of warm milk, not stark white, not yellow") — plain "white" came out too cold;
- the characters came out **too tall** — their heads nearly touched the top, so there was no room for the title. Say the size in
  numbers (the group fills only the bottom two fifths of the height; the top of the tallest head stays below the middle), repeat it in
  `pose`, `composition` and `overlay_space`, and add negatives ("characters reaching into the upper part of the image", "heads near
  the top edge", "oversized characters filling the image height"). A tall framing tree pushes everything up — keep any tree only a
  little taller than the characters;
- the group was **pressed to the right edge** — center it in the right area (about three quarters of the width from the left edge);
- the left area was **too empty** — give it a minimal but present sprinkle of small details (see below).

Remember how the 2:1 image is used: its **right area** is what the buyer sees first (the title goes in its upper part); its
**left area** is the quiet reverse side. Write it like this:

- **Ground:** "a soft milky cream paper ground, the color of warm milk (not stark white, not yellow)" filling the whole image — the
  same cream from edge to edge, continuous through the centre, with no frame and no border.
- **Right area, upper part (from the top edge down to about the middle of the height):** plain milky cream for later typography; at
  most a few tiny gold stars, sparkles, confetti, petals or snowflakes near its edges, never in its middle.
- **Right area, lower part (about the bottom two fifths):** the hero/group, **compact, close and emotional** (a hug, a big smile, eye
  contact or a look at each other), centered in the right area, readable at thumbnail size; color, contrast and detail are concentrated
  here.
- **Choose ONE placement per prompt:**
  - **A — Vignette:** a small piece of the characters' world (snowy ground, garden, tree, cottage corner) behind them, whose edges
    **dissolve softly into the white** with feathered painterly edges, no frame.
  - **B — Alone on white:** no scenery at all; the characters sit or stand on the white with a soft ground shadow and a few props
    around them (gifts, flowers, toys), a few tiny decorations scattered sparsely in the white.
  - **C — Framing element:** like A or B, plus one element beside the group (a small decorated tree, a rose bush, a tall flower) —
    only a little taller than the characters, never up to the top.
- **Left area:** a **minimal but present** sprinkle of small details, spaced out with plenty of cream between them: one small motif low
  at the far left (a lantern, a little tree, a gift stack, a flower pot), one or two small props near the bottom (a sled, a mitten, a
  candy cane, a watering can), two or three small things hanging from the top edge (baubles, paper stars, bunting) or a little bird on a
  twig, and a light scatter of tiny stars or petals. The middle of the left area stays calm and open for a later overlay.
- **Style overrides (on top of the full Medium preset):** `washes` = the milky cream paper ground + color only in the illustrated group,
  edges dissolving into cream; `light` = bright, clean, high-key, soft and even (no dark vignette, no heavy dusk); `overlay_behavior`
  = "plain milky cream paper with at most a few tiny sparkles near its edges". Keep every other preset key.
- **Negatives to add:** "characters reaching into the upper part of the image", "heads near the top edge", "oversized characters filling
  the image height", "a group pressed against the right edge", "a full background scene from edge to edge", "a dark or saturated
  background", "a stark pure white background", "a solid strongly colored background", "a frame or border around the image", "a
  hard-edged rectangle of scenery", "objects in the upper part of the right area", "an empty bare left area", "a busy left area", "tiny
  distant characters", plus a color-cast guard if the preset is warm ("yellow color cast", "sepia tint").
- **The exception (example 2, the Santa letter):** a full scene is allowed only when one big light object in it (an envelope, a
  cloud, a banner shape) is itself the title space — use only when the owner asks.

Composition sentence to adapt (the tested wording: `books/40.christmas-with-grandma/agent/cover-white-tests.md`): *"Set the
illustration on a soft milky cream paper ground, the color of warm milk (not stark white, not yellow), that fills the whole image. Place
the main group as a compact group placed low, centered within the right area at about three quarters of the image width from the left
edge, well away from the right edge; the group fills only about the bottom two fifths of the image height, so the top of the tallest
head stays below the middle of the image height, with the strongest color, contrast and emotion there; [A: a small piece of their world
close behind them, no taller than they are, dissolving softly into the cream / B: no scenery, only a soft ground shadow and a few props
/ C: one small X beside them, only a little taller than they are]. Leave the entire upper right area, from the top edge down to about
the middle of the image height, as plain milky cream for later typography and overlay. Fill the left area with a minimal but charming
sprinkle of small details, spaced out with plenty of cream between them: [...]; keep the middle of the left area calm and open. The
cream ground runs continuous and uninterrupted from edge to edge, with no frame and no border."*

The checker still needs its wraparound words: `2:1`, continuous/uninterrupted, right, left, `upper right`, typography/overlay.

### The old full-scene contract (only when the owner asks for it)
- Right area: main character, hero group, or key symbolic object; strongest detail, contrast,
  emotion, and thumbnail readability.
- Upper right: calm sky, water, meadow, wall, glow, or other low-detail illustrated area for later
  typography. It must remain part of the same world.
- Left area: quieter continuation of the same environment with lower contrast and fewer details,
  suitable for later overlay if needed.
- Center: ordinary continuous scenery only. No marks, divisions, guide lines, mirrored duplicate
  compositions, or object boundaries.
- The image should be slightly richer and more polished than the story panoramas while preserving
  the chosen medium and nursery-safe tone.
- The solid-color ground tests of books 42–44 (2026-10-14) were this kind of experiment.

## Style Fidelity Gate
- Reuse the full expanded Medium preset from `knowledge/media-presets.md`; do not summarize it to a
  short style phrase.
- Preserve the same paint behavior, surface texture, linework, palette behavior, light, depth,
  overlay behavior, mood, and finish used inside the generated story images.
- The final wide image may be slightly richer for thumbnail appeal, but it must still look like the
  same handmade visual world, not a different renderer.

## Output Format
Emit one file: `books/[number].[slug]/agent/cover-prompts-json.md` — one prompt (the Workshop's cover row takes
the first one). Then run the book check again:
```bash
python check_book.py "books/[number].[slug]"
```
Tell the user the cover prompt is in the Workshop's cover row.

Flat JSON schema:
`task, aspect_ratio, canvas, reference_image?, reference_rule?, character{}, scene{}, style{}, overlay_space{}, emotional_goal, negative[], output`.

Rules:
- Use `reference_image` + `reference_rule` for the owner's best frame (or the canonical character); omit both when there is none.
- Do not write null reference fields.
- Reuse the full chosen Medium preset, preserving the expanded paint/detail keys and rewriting any
  generator-trigger vocabulary before output.
- Keep `negative[]` focused on safe text/style guards only: `text`, `letters`, `typography`,
  `numbers`, `logo`, `watermark`, `labels`, `signs`, `arrows`, `guide marks`, `visible words`,
  `UI marks`, `metadata`, `JSON terms`, plus safe medium-specific negatives.

## Clean Example Shape
```json
{
  "id": "final-wide-image",
  "task": "Create a premium flat 2D 2:1 panoramic illustration in [MEDIUM STYLE].",
  "aspect_ratio": "2:1",
  "canvas": "One uninterrupted 2:1 panoramic illustration on a soft milky cream paper ground, continuous edge to edge, with no frame and no border.",
  "reference_image": "ref_cover_[frame].jpg",
  "reference_rule": "Use the attached image only for the characters and the look: keep exactly the same characters and the same paint style and texture. Do NOT copy its background or composition: the characters sit small and low on a milky cream ground as described.",
  "character": {
    "hero": "[main character/group identity]",
    "pose": "low in the right area, a compact group filling only the bottom two fifths of the height, centered in the right area: [a hug, a smile, a look at each other]",
    "expression": "[warm emotional read]"
  },
  "scene": {
    "name": "[the characters on a milky cream ground]",
    "action": "[what the focal character/group is doing]",
    "location": "[A: a small piece of their world dissolving into cream / B: no scenery, the cream ground only]",
    "composition": "[the composition sentence of the light-ground formula, adapted]"
  },
  "style": {"...": "the full Medium preset, with washes, light and overlay_behavior overridden for the white ground"},
  "overlay_space": {
    "placement": "the upper right area, down to about the middle of the height, of plain milky cream above the characters; an optional calm open middle in the left area",
    "requirements": "No visible text, letters, typography, numbers, logos, watermarks, labels, signs, arrows, or guide marks."
  },
  "emotional_goal": "[premium, tender, giftable, clear thumbnail read]",
  "negative": ["text", "letters", "typography", "numbers", "logo", "watermark", "labels", "signs", "arrows", "guide marks", "visible words", "UI marks", "metadata", "JSON terms"],
  "output": "one flat 2:1 continuous panoramic illustration, no visible text"
}
```

---

## Mode B — two squares («Два квадрати», the owner, 2026-10-24)

Why: competitors' covers have the title **painted into the picture** in a beautiful font, and only the child's
name is added later. In 2:1 the generator never centres anything on the front; a square is centred by itself. The
cover tool («Обкладинка») then lays both squares on the printer's template and fills the spine and the edges itself
from the squares' own cream ground — no outpaint (2026-10-25). So **the scene must dissolve into the cream before the
square's edges**: a scene cut off by the edge leaves a hard line at the spine (the owner adds the name in Canva).

### What to write

`cover-prompts-json.md` with **exactly two** prompts, in this order, both `"aspect_ratio": "1:1"`:

| `id` | What it is | Reference the user attaches |
|---|---|---|
| `title-square` | the main square: the painted **title**, open room for the name, the characters | the best frame (the characters and the look) |
| `quiet-square` | the reverse square: a calm scene of the story's things, **no characters, no text** | the finished `title-square` picture — the Workshop pastes it in first by itself |

The `id`s are exactly these (the Workshop and the book check read them). Never use "front", "back", "cover", "spine" or
any other trigger word — not in the `id`, not anywhere in the prompt. The ones that slip in here most easily (the
first test, 2026-10-24): **"storybook title"** (say "title lettering"), **"upper half" / "bottom half"** (say "upper
part" / "lower part"), **"an echo of the front"** (say "of Image 1").

### `title-square` — the title square

- **The title text** = the first line under `## Cover` in `book-text.md`, **without `{Name}`** — the name is never
  painted (the owner puts it on in Canva in a font he picks). Spell the painted words letter by letter in a
  `spelling` field, and say "nothing else written anywhere".
  - `{Name}'s Moonlit Garden` → paint «Moonlit Garden»; leave the open room **above** it.
  - `A Christmas Story for {Name}` → paint «A Christmas Story for»; leave the open room **below** it.
  - No `{Name}` in the title → paint the whole title; leave the open room below it.
- **The room for the name** — just open milky cream paper, about one fifth of the square's height, right where the
  name goes. **No stripe, ribbon, banner, panel or frame** — the owner: "empty space, not a band". Say it in an
  `open_space` field: "nothing painted there at all", and add negatives against a stripe/ribbon/banner/panel and
  against anything painted in that room.
- **Lettering** — hand-painted title lettering in the medium of the story pictures (letters with the paint's texture and a
  thin pencil or ink outline when the medium has one), in the palette's warm darker tones; a small ornament under it
  (a thin line with a tiny heart, a sprig, a star) is welcome.
- **The light-ground formula, made square:** the milky cream ground edge to edge; the title in the upper part, the
  open room, then the characters **low and centred, filling only the bottom two fifths**, the top of the tallest head
  below the middle; a small piece of their world close behind them dissolving into the cream (placement A, B or C
  from the formula above). Keep the title and every face **at least one tenth of the width away from every edge**.
- `reference_image` + `reference_rule`: the best frame, for the characters and the look only — not its background
  or composition. **`reference_image` must be a real file in `agent/`** (the book check fails «Image 1»): copy the frame
  from `originals/` as `ref_cover_<frame>.jpg` and name that file (book 46, 2026-10-24).
- **The owner's own title layout wins** when he gives one — e.g. book 46: «Grandma» large, a **small** «&» under it, then
  the open room for the name (the ampersand about one third of the height of the word, in a lighter script).

### `quiet-square` — the reverse square

- **No characters at all** — no people, no animals, no birds (unless the user asks for a small one). Only the
  story's things: its props, flowers, food, toys, the place — e.g. "the garden bench after a happy day" with the
  scarf, glasses, a teacup and a basket of berries left on it. It continues the story quietly.
- **No text of any kind**, and **no empty panel or cloud-shaped space in the middle** (it is not a place for text).
  A calm, balanced vignette in the lower-middle, dissolving into the same milky cream; the upper part open with a few
  drifting petals or sparkles; every object at least one tenth of the width away from each edge.
- **No `reference_image` field** (the finished title square is not a file yet — the Workshop pastes it in by itself); only
  `reference_rule`: "Match the attached image (the finished title square) exactly in paint style, linework, palette, light
  and paper; do NOT copy its characters, its lettering or its layout." Say "the attached image", never "Image 1".

### Both squares

- The full expanded Medium preset (the Style Fidelity Gate above), with the light-ground overrides of `washes`,
  `light`, `overlay_behavior`.
- `negative[]` — the safe text guards (`text` must be one of the words: in `title-square` write "any other text",
  "extra letters", "misspelled title", "subtitle"), the formula's composition negatives, the medium's negatives.
- `canvas`: "one square illustration … continuous edge to edge, with no frame and no border"; `output`: "one square
  1:1 illustration …".
- `reference_image`: write **"Image 1"** — the cover tool pastes the reference first, then a **layout guide** picture,
  then the prompt, and it adds the guide's words to the prompt itself (`layout_guide`, with the guide's number). Do not
  describe the guide; the percentages in `layout_in_numbers` still help.
- Then run the book check as usual and tell the user: «Промпти обох квадратів готові — відкрийте крок «Обкладинка»
  (інструмент «Обкладинка», режим «Два квадрати» увімкнеться сам). Обкладинку з квадратів Book Studio складе сам».

### Shape

```json
[
  {
    "id": "title-square",
    "task": "Create a premium square 1:1 children's illustration in [MEDIUM STYLE], with a hand-painted title.",
    "aspect_ratio": "1:1",
    "canvas": "one square illustration on a soft milky cream paper ground, the color of warm milk (not stark white, not yellow), continuous edge to edge, with no frame and no border",
    "reference_image": "ref_cover_[frame].jpg",
    "reference_rule": "Use the attached image only for the characters and the look: keep exactly the same characters, paint style and paper texture. Do NOT copy its background or composition.",
    "title": {
      "text": "[the title without the name]",
      "spelling": "exactly these letters: [L-e-t-t-e-r-s] — nothing else written anywhere",
      "placement": "[centered in the upper part …]",
      "lettering": "[hand-painted title lettering in the medium …]",
      "ornament": "[a thin line with a tiny heart …]"
    },
    "open_space": {
      "placement": "[above / below the title], roughly one fifth of the square's height of open milky cream paper",
      "rule": "just the same cream ground continuing — nothing painted there at all: no letters, no shapes, no panel, no ribbon, no stripe, no flowers, no sparkles"
    },
    "character": {"subject": "[the fixed description]", "pose": "[low and centred, the bottom two fifths …]", "expression": "[…]"},
    "scene": {"name": "[…]", "location": "[a small piece of their world dissolving into cream]", "composition": "[title, open room, characters low; one tenth off every edge]"},
    "style": {"...": "the full Medium preset with the light-ground overrides"},
    "emotional_goal": "[premium, tender, giftable; reads at thumbnail size]",
    "negative": ["any other text", "extra letters", "misspelled title", "subtitle", "anything painted in the open room", "a stripe, ribbon, banner or panel", "numbers", "logo", "watermark", "characters reaching into the upper part", "characters touching the edges", "a frame or border", "..."],
    "output": "one square 1:1 illustration with the hand-painted title and open cream paper for later typography"
  },
  {
    "id": "quiet-square",
    "task": "Create a premium square 1:1 children's illustration in exactly the same art style as the attached image: a calm still-life vignette of [the story's things], with no characters and no text.",
    "aspect_ratio": "1:1",
    "canvas": "one square illustration on the same soft milky cream paper ground as the attached image, continuous edge to edge, with no frame and no border",
    "reference_rule": "Match the attached image (the finished title square) exactly in paint style, linework, palette, light and paper texture. Do NOT copy its characters, its lettering or its layout.",
    "scene": {"name": "[…]", "description": "[the props, the place]", "composition": "[one gentle vignette in the lower-middle dissolving into cream; the upper part open; one tenth off every edge]"},
    "style": {"...": "the full Medium preset with the light-ground overrides"},
    "emotional_goal": "calm, cozy, giftable; a gentle echo of the title square",
    "negative": ["text", "letters", "typography", "words", "numbers", "logo", "watermark", "people", "animals", "birds", "characters", "a plain blank panel in the middle", "a cloud-shaped empty area", "a frame or border", "..."],
    "output": "one square 1:1 illustration, no characters, no visible text"
  }
]
```

A tested pair (book 46, 2026-10-24): `D:\Roman\Desktop\Cover Squares Test\prompts\46-grandma-and-me.md`; the version in the
Workshop, with the owner's «Grandma &» layout and passing the book check: `books/46.grandma-and-me/agent/cover-prompts-json.md`.
