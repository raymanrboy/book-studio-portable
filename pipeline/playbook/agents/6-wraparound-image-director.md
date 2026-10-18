# Agent 6 - Wraparound Image Director

**One job:** after the story panoramas are generated and approved, assemble one final wide-image
prompt for the premium outer artwork. This is a separate prompt file from Agent 5.

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
