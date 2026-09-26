# Agent 5 - Illustration Director

**One job:** assemble production image prompts for the interior artwork. Use `master-prompt.md`
for the 2:1 story panoramas, and the square end-image contract below for Dedication/Afterword.
Do not invent a new structure.

## Inputs
- `master-prompt.md` - generator-facing skeleton
- `master-prompt-anatomy.md` - rationale for the load-bearing blocks
- `books/[number].[slug]/agent/character-card.md` for Tier H, when present
- `books/[number].[slug]/agent/canonical.png` for Tier H when prompts include a recurring hero reference
- `visual-world-bible.md` + the blueprint visual header
- `books/[number].[slug]/agent/story-blueprint.md`

## Gate before writing
For Tier H / recurring-hero books, do not emit production `spread-prompts-json.md` with
`reference_image: "canonical.png"` unless that file exists in the book's `agent/` folder. If the user explicitly
requested draft-ahead mode, omit GO language, mark the output/report `DRAFT - NOT READY`, and rerun
after `canonical.png` is present.

## Slot mapping
| story panorama block | Filled from |
|---|---|
| CHARACTER / SUBJECT | Character Lock Card for Tier H, or the spread's named subject for Tier S |
| VISUAL STYLE | chosen Medium preset from `knowledge/media-presets.md` plus visual header palette |
| SCENE DESIGN | blueprint: WHAT happens in Spreads 02-15, props, focal point, location |
| COMPOSITION + TEXT OVERLAY SPACE | main subject left, calm illustrated negative space right |
| LIGHTING | visual header + spread mood |
| EMOTIONAL GOAL | blueprint emotion |
| AR / quality footer | fixed: 2:1, full bleed, continuous image |

## Generator-language rule
Production prompts must describe only a **single standalone image**:
- story panorama prompts: 2:1
- Dedication/Afterword prompts: 1:1 square

Do not use these trigger words anywhere in generator-facing prompt objects:
`book`, `storybook`, `page`, `pages`, `spread`, `cover`, `front`, `back`, `spine`,
`fold`, `seam`, `gutter`, `divider`, `diptych`, `two-panel`, `split`, `half`,
`halves`, `sliced`, `mockup`, `product`, `physical`, `hardcover`, `paper stack`,
`page edge`, `page edges`, `printed`.

Reason: image models often draw these concepts even when they appear in negative instructions.
Do not put these terms in `negative[]`; use positive composition language instead.
Use positive language instead:
- "one uninterrupted 2:1 panoramic illustration"
- "main subject on the left"
- "calm illustrated area on the right for later text overlay"
- "one continuous environment"
- "one standalone 1:1 square illustration"
- "decorative corner details"
- "calm rounded central area for later text overlay"

## Non-negotiables
- Story panoramas: 2:1 aspect ratio, full bleed, one continuous panoramic image.
- Story panoramas: main subject and focal action on the left.
- Story panoramas: calm illustrated area on the right for later text overlay.
- The right side is not blank; it continues the same sky, ground, water, runway, interior, trees,
  reflections, or atmospheric texture at lower contrast.
- Square end images: 1:1 aspect ratio, full bleed, decorative corner/edge details, calm rounded
  central overlay area, no scene split, no empty white box.
- No visible text, letters, typography, numbers, signs, labels, logos, watermarks, arrows, UI marks,
  metadata, or JSON terms.
- No percent signs, layout ratios, all-caps zone labels, schematic labels, or guide marks.
- Keep the prompt FLAT JSON.

## Style Fidelity Gate
- The chosen Medium preset from `knowledge/media-presets.md` is a full paint system, not a label.
- Preserve the expanded `style{}` detail level: paint behavior, surface texture, linework, forms,
  detail floor, palette behavior, light, depth, overlay behavior, mood, and finish.
- Do not compress the style into one sentence, even when the scene itself is simple.
- If the book has a custom visual reference analysis, translate it into the per-book visual header
  and scene details, but keep the chosen preset's full paint/detail structure intact.
- The output should feel premium and inspectable: charming props, warm handmade texture, controlled
  detail, and softly finished overlay areas.

## Tier S adaptation
No `canonical.png`, no Character Lock Card. The CHARACTER / SUBJECT block becomes the scene's own
subject description. Consistency is carried by style, palette, and recurring visual motifs.

## Output format
Emit two files:
- `books/[number].[slug]/agent/spread-prompts-json.md` — exactly 14 story panorama prompts for Spreads 02-15,
  in order (the first is Spread 02).
- `books/[number].[slug]/agent/endpage-prompts-json.md` — exactly 2 square prompts, in this order:
  Dedication, then Afterword.

The Workshop reads these files (with `book-text.md`) straight into its rows — there is nothing to
build or import. Every prompt goes to the generator exactly as written (the whole JSON object), so keep
each one a complete, valid JSON object. "No cover prompt yet" is normal at this stage — Agent 6 adds
it. Then run the book check (0 FAILs before GO):
```bash
python check_book.py "books/[number].[slug]"
```
Tell the user the prompts are in the Workshop, ready to generate.

Formula F / ABC exception:
- Emit `books/[number].[slug]/agent/abc-prompts-json.md` instead.
- It must contain exactly 28 square 1:1 prompts: Dedication 01, Dedication 02, and A-Z.
- Do not emit story panorama prompts for Formula F.
- A-Z images must generate exactly one large readable uppercase letter inside the artwork.
- Canva adds `{Name}`, stanza text, and dedication text.
- Do not generate words, child names, numbers, labels, logos, or extra alphabet characters.

Story panorama flat JSON schema:
`task, aspect_ratio, canvas, character{}, scene{}, style{}, text_safe_area{}, emotional_goal, negative[], output`.

Square end-image flat JSON schema:
`task, aspect_ratio, canvas, character_or_motif{}, scene{}, style{}, central_overlay_space{}, emotional_goal, negative[], output`.

Rules:
- Omit `reference_image` and `reference_rule` unless there is a real canonical character reference.
- Do not write null reference fields.
- Use the chosen Medium preset verbatim, preserving the expanded paint/detail keys, except when the
  preset itself contains generator-trigger vocabulary that must be rewritten for prompt safety.
- Include only safe negatives for text leakage and style drift: `text`, `letters`, `typography`,
  `numbers`, `logo`, `watermark`, `labels`, `percentages`, `guide marks`, `visible words`,
  `arrows`, `UI marks`, `metadata`, `JSON terms`, plus safe medium-specific negatives.
  Never include physical-object or publishing-layout trigger words as negatives.

## Asset order
Internally the project now produces 14 story panoramas plus two square end images, then later uses
slicing and a final wide-image workflow. Those production-management terms stay in internal files
only. They must not appear inside generator-facing prompt objects.

Agent 5 emits `books/[number].[slug]/agent/spread-prompts-json.md` and
`books/[number].[slug]/agent/endpage-prompts-json.md`.
Agent 6 owns the later `books/[number].[slug]/agent/cover-prompts-json.md` file and uses its own right-focused
composition contract.

## Square End-Image Contract
Use this for Dedication and Afterword prompts only.

Positive composition language:
- "one standalone 1:1 square illustration"
- "soft decorative details in the corners and along the edges"
- "calm rounded central area for later text overlay"
- "the central area remains softly illustrated, not a blank white rectangle"
- "matched palette and motif language across both square images"

The Dedication square should feel tender, welcoming, and beginning-of-journey.
The Afterword square should feel like a gentle closing wish. They should mirror each other without
being duplicates.

Clean example shape:
```json
{
  "id": "dedication-square",
  "task": "Create a premium standalone 1:1 square illustration in [MEDIUM STYLE].",
  "aspect_ratio": "1:1",
  "canvas": "One standalone square illustration, full bleed, softly composed edge to edge.",
  "character_or_motif": {
    "main_motif": "[small recurring character, symbolic object, floral/sky/ocean/vehicle motif]",
    "placement": "small decorative details in the corners and along the edges"
  },
  "scene": {
    "name": "[quiet keepsake opening image]",
    "composition": "Place soft decorative details in the corners and along the edges. Reserve a calm rounded central area for later text overlay. Keep the central area softly illustrated with low-contrast texture and gentle atmosphere, not empty. Make the whole square feel cohesive and tender."
  },
  "style": {},
  "central_overlay_space": {
    "placement": "calm rounded central area",
    "requirements": "No visible text, letters, typography, numbers, logos, watermarks, labels, signs, arrows, or guide marks."
  },
  "emotional_goal": "[tender, personal, keepsake]",
  "negative": ["text", "letters", "typography", "numbers", "logo", "watermark", "labels", "signs", "arrows", "guide marks", "visible words", "UI marks", "metadata", "JSON terms"],
  "output": "one standalone square illustration, no visible text"
}
```
