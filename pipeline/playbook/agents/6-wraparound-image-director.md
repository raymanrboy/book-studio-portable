# Agent 6 - Wraparound Image Director

**One job:** after the story panoramas are generated and approved, assemble the prompt for the premium outer
artwork — **one 2:1 picture** (the owner, 2026-10-27: back to 2:1 and the outpaint; «Два квадрати» of 2026-10-24…27
taken out — never write square prompts). This is a separate prompt file from Agent 5.

## FIRST: ask for the best frame

Before writing anything, ask the user — in Ukrainian, one short question: «Надішліть, будь ласка, найкращий кадр із
розворотів для обкладинки.» Then write the one prompt by **the full-scene formula with the painted title** below.

## Inputs
- `master-prompt.md` - language discipline and style structure
- `master-prompt-anatomy.md` - why the image-only language matters
- `books/[number].[slug]/agent/character-card.md` for Tier H, when present
- `books/[number].[slug]/agent/canonical.png` for Tier H, when the recurring character is used
- `visual-world-bible.md` + the blueprint visual header
- **The user's chosen "best frame"** from the generated story spreads. This must be used as the `reference_image`, with `reference_rule`
  saying to keep exactly its characters, paint style and texture — and NOT its composition, because the full-scene
  formula below replaces it.
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

## The full-scene formula with the painted title — the DEFAULT (the owner, 2026-10-27)

Why: competitors' covers have the title **painted into the picture** in a beautiful font, and only the child's name is
added later; and the name is the selling element, so it needs a **big** place. Tested on book 44
(`D:\Roman\Desktop\Cover Squares Test\prompts\44-santas-workshop-wide.md` — the target wording) — the owner chose it.

How the picture is used: its **right area** is the front of the book (the title and the name there, centred at about
three quarters of the width), the **left area** the reverse, the **middle** the spine; the Workshop's cover tool lays
it on the printer's template and the margins are outpainted. The tool pastes the reference first, then a **layout
guide** picture (a green-grey field = the scene everywhere; in the right area a brown-grey shape = the title, a pale
blue one = the name's room), then the prompt — and it **adds the guide's words itself** (`layout_guide`). Do not write a
`layout_guide` field and do not describe the guide.

- **The scene fills the whole picture**, edge to edge — no cream ground, no vignette, no frame, no light patch or cloud
  behind the text.
- **The title** = the first line under `## Cover` in `book-text.md`, **without `{Name}`** — the name is never painted
  (the owner sets it in Canva). Spell the painted words letter by letter in a `spelling` field and say "nothing else
  written anywhere". Placement: in the right area, centred at about three quarters of the image width, spanning about
  two fifths of the width. Lettering in the medium (the paint's texture; a soft light glow around the letters so they
  read over the scene), the palette's strong warm tones; a small ornament under it is welcome.
- **The name's room — big and EMPTY**, in the right area on the same centre line: **above** the title when the title
  starts with `{Name}` (`{Name}'s Moonlit Garden` → paint «Moonlit Garden»), else **below** it (`A Christmas Story for
  {Name}` → paint «A Christmas Story for»). About as big as the title's main line (about one sixth of the height tall,
  three tenths of the width across). Describe it in an `open_space` field: "a calm, plain, low-detail part of the scene
  itself (a soft glow of a wall, a sky, snow, mist) with nothing painted in it; NOT a panel, cloud, ribbon or white
  box", and that "a name will be set there later as large as the title's main line". The tool's guide has the same
  order (it picks it by the title).
- **The hero/group** in the right area, below the title (or the title and the room), large, centred at about three
  quarters of the width, readable at thumbnail size, the strongest color and emotion there.
- **The left area** — a quieter, rich continuation of the same place, **no characters** (the story's things: props,
  food, toys, the place), no letters.
- **The middle of the width** (the spine) — only ordinary continuous scenery: no key object, face or letter there.
- **Every edge** — the outermost strip calm, simple scenery (the margins are outpainted from it); the title, the room
  and every face at least one tenth of the height away from the top, bottom and right edges.
- `reference_image` + `reference_rule`: the best frame (a real file in `agent/`: copy it from `originals/` as
  `ref_cover_<frame>.jpg`), for the characters and the look only — not its composition.
- **The full Medium preset** (the Style Fidelity Gate below); override only `washes` (the scene's own tones, a soft glow
  behind the title and the room) and `overlay_behavior` (the name's room calm and plain).
- **Negatives:** "any other text", "a name", "extra letters", "misspelled title", "subtitle", "letters in the left
  area", "anything painted in the open room", "a white box, panel, cloud, plaque, ribbon or banner behind the title", "a
  key object or face in the center of the width", "a vertical line through the image", "a frame or border", "a
  vignette", "a cream background", "characters in the left area", plus the safe text guards and the medium's
  negatives. Never "seam" or "divider" — they are trigger words.
- The book check still needs its wraparound words: `2:1`, continuous/uninterrupted, right, left, **`upper right`** (say
  where the name's room is: "in the upper right"), typography/overlay ("for later typography").
- **The owner's own title layout wins** when he gives one — e.g. book 46: «Grandma» large, a **small** «&» under it, then
  the room for the name.

## Light-ground formula — the older default (2026-10-17 → 2026-10-27; only when the owner asks)

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
Tell the user: «Промпт обкладинки готовий — відкрийте крок «Обкладинка» (інструмент «Обкладинка»): «Генерувати» сам
покладе в буфер референс, схему й промпт».

Flat JSON schema:
`task, aspect_ratio, canvas, reference_image?, reference_rule?, title{}, open_space{}, character{}, scene{}, style{}, emotional_goal, negative[], output`.

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
  "task": "Create a premium flat 2D 2:1 panoramic illustration in [MEDIUM STYLE], one rich scene filling the whole image, with hand-painted title lettering in the right area.",
  "aspect_ratio": "2:1",
  "canvas": "one uninterrupted 2:1 panoramic illustration, full bleed, one continuous scene from edge to edge, with no frame, no border and no vignette",
  "reference_image": "ref_cover_[frame].jpg",
  "reference_rule": "Use the attached image only for the characters and the look: keep exactly the same characters and the same paint style and texture. Do NOT copy its composition.",
  "title": {
    "text": "[the title without the name]",
    "spelling": "exactly these letters: [L-e-t-t-e-r-s] — nothing else written anywhere",
    "placement": "in the right area, centered at about three quarters of the image width, [above / below the open room], spanning about two fifths of the image width",
    "lettering": "[hand-painted title lettering in the medium, a soft light glow around the letters so they read over the scene]",
    "ornament": "[a sprig, a star …]"
  },
  "open_space": {
    "placement": "in the upper right, [ABOVE / BELOW] the title, centered on the same line at about three quarters of the image width, about one sixth of the height tall and three tenths of the width across — big, because a name will be set there later as large as the title's main line, for later typography",
    "rule": "a calm, plain, low-detail part of the scene itself — [a soft glow of the wall / sky / snow / mist] — with nothing painted in it; NOT a panel, cloud, ribbon or white box"
  },
  "character": {
    "subject": "[the fixed description]",
    "pose": "in the right area, below the title, centered at about three quarters of the image width, large: [what they do]",
    "expression": "[warm emotional read]"
  },
  "scene": {
    "name": "[…]",
    "location": "[the story's place, one continuous scene across the whole image]",
    "left_area": "[the quieter continuation of the same place, no characters: the story's things]",
    "composition": "One continuous scene edge to edge. The right area holds the title, the open room and the hero; the left area is calmer. Around the center of the width only ordinary continuous scenery — no key object, face or letter there. The outermost strip along every edge is calm, simple scenery."
  },
  "style": {"...": "the full Medium preset, with washes and overlay_behavior as the formula says"},
  "emotional_goal": "[premium, giftable; a big readable title and a big calm place for a name]",
  "negative": ["any other text", "a name", "extra letters", "misspelled title", "subtitle", "letters in the left area", "anything painted in the open room", "a white box, panel, cloud, plaque, ribbon or banner behind the title", "a key object or face in the center of the width", "a vertical line through the image", "a frame or border", "a vignette", "a cream background", "characters in the left area", "numbers", "logo", "watermark", "..."],
  "output": "one flat 2:1 continuous panoramic illustration filling the whole image, the hand-painted title and open room in the right area for later typography"
}
```

---

*«Два квадрати» (2026-10-24…27): two 1:1 prompts (`title-square`, `quiet-square`) made into the cover by Book Studio
without the generator — taken out by the owner on 2026-10-27 in favour of the 2:1 full-scene formula above. Never write
square prompts; books written then keep theirs, and the Workshop ignores them.*
