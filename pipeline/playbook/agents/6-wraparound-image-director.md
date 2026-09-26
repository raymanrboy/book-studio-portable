# Agent 6 - Wraparound Image Director

**One job:** after the story panoramas are generated and approved, assemble one final wide-image
prompt for the premium outer artwork. This is a separate prompt file from Agent 5.

## Inputs
- `master-prompt.md` - language discipline and style structure
- `master-prompt-anatomy.md` - why the image-only language matters
- `books/[number].[slug]/agent/character-card.md` for Tier H, when present
- `books/[number].[slug]/agent/canonical.png` for Tier H, when the recurring character is used
- `visual-world-bible.md` + the blueprint visual header
- **The user's chosen "best frame"** from the generated story spreads. This must be used as the `reference_image` (with `reference_rule` set to strongly follow its composition and style) to ensure the cover perfectly matches the inside of the book.
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

## Composition Contract
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
- Omit `reference_image` and `reference_rule` unless there is a real canonical character reference.
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
  "canvas": "One uninterrupted 2:1 panoramic illustration, full bleed, continuous edge to edge.",
  "character": {
    "hero": "[main character/group identity]",
    "pose": "on the right area, [clear charming action or pose]",
    "expression": "[warm emotional read]"
  },
  "scene": {
    "name": "[right-focused continuous panorama]",
    "action": "[what the focal character/group is doing]",
    "location": "[single continuous environment]",
    "composition": "Place the main focal character/group and strongest visual interest on the right. Keep the left area calmer, lower contrast, and softly detailed as the same environment continues. Reserve a calm low-detail area in the upper right for later typography. Carry the environment across the full image as one uninterrupted panorama."
  },
  "style": {},
  "overlay_space": {
    "placement": "upper right calm illustrated area, with optional quieter left area",
    "requirements": "No visible text, letters, typography, numbers, logos, watermarks, labels, signs, arrows, or guide marks."
  },
  "emotional_goal": "[premium, tender, giftable, clear thumbnail read]",
  "negative": ["text", "letters", "typography", "numbers", "logo", "watermark", "labels", "signs", "arrows", "guide marks", "visible words", "UI marks", "metadata", "JSON terms"],
  "output": "one flat 2:1 continuous panoramic illustration, no visible text"
}
```
