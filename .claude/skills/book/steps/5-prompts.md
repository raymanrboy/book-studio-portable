# Step 5 — Image prompts and the GO check

Assemble the production prompts: 14 story panoramas from [master-prompt.md](../../../../pipeline/knowledge/master-prompt.md)
and the two squares by the square contract below. Do not invent a new structure.

Read: `master-prompt.md` (the skeleton and why each block is there), the character card (Tier H) or the animals' fixed
descriptions (Tier S), [visual-world-bible.md](../../../../pipeline/knowledge/visual-world-bible.md) + the blueprint's
visual header, `story-blueprint.md`.

## The style block — from the script, verbatim

`python pipeline/scripts/preset.py <CODE>` prints the medium's full `style{}` JSON and its extra negatives. Paste it
whole into every prompt; change only `detail` / `color` / `light` to add this scene's things and lean, as the existing
books do. Never shorten it to one sentence: the paint system is what makes the frames look like one book. (A preset's
`forms` line written for children is rewritten for animals in an animal book — once, then the same in every prompt.)

## Slots

| Block | From |
|---|---|
| `character` | the lock card (Tier H) or the animals' fixed description (Tier S), word for word every time |
| `scene` | the blueprint: what happens, props, focal point, location; how the scene continues calmly to the right |
| `style` | the preset (above) + the visual header's palette |
| `text_safe_area` | the calm illustrated area on the right |
| `emotional_goal` | the blueprint's emotion |

`reference_image` + `reference_rule` only when there is a real `canonical.png` (Tier H); never null fields.

## Files (the Workshop reads them into its rows; each prompt is one complete JSON object)

- `agent/spread-prompts-json.md` — exactly 14 story panoramas, Spread 02 first. Flat schema:
  `task, aspect_ratio, canvas, [reference_image, reference_rule,] character{}, scene{}, style{}, text_safe_area{}, emotional_goal, negative[], output`.
- `agent/endpage-prompts-json.md` — exactly 2 squares: Dedication, then Afterword. Schema:
  `task, aspect_ratio, canvas, character_or_motif{}, scene{}, style{}, central_overlay_space{}, emotional_goal, negative[], output`.
- `agent/preflight-report.md` — your gates and the verdict.

Negatives: only text leakage and style drift (`text`, `letters`, `typography`, `numbers`, `logo`, `watermark`, `labels`,
`guide marks`, `visible words`, `UI marks`, `metadata`, `JSON terms`) + the preset's `negative+`.

## Non-negotiables

- Panoramas: 2:1, full bleed, one continuous image; the subject and action on the left; a calm, still illustrated area on
  the right (the same sky, ground, water or room at lower contrast — never blank).
- Squares: 1:1, full bleed, decorative details in the corners and along the edges, a calm rounded central area, softly
  illustrated (no empty white box). The dedication feels like a beginning, the afterword a closing wish — a pair, not
  duplicates.
- No percent signs, ratios, all-caps zone labels or guide marks; no trigger words (master-prompt.md).
- A big object (a vehicle, a house) drifts to the middle unless its place and size are said
  ([lessons.md](../../../../pipeline/knowledge/lessons.md)).

## Square example

```json
{
  "id": "dedication-square",
  "task": "Create a premium standalone 1:1 square illustration in [MEDIUM STYLE].",
  "aspect_ratio": "1:1",
  "canvas": "One standalone square illustration, full bleed, softly composed edge to edge.",
  "character_or_motif": {
    "main_motif": "[small recurring character, symbolic object, floral/sky/ocean motif]",
    "placement": "small decorative details in the corners and along the edges"
  },
  "scene": {
    "name": "[quiet keepsake opening image]",
    "composition": "Place soft decorative details in the corners and along the edges. Reserve a calm rounded central area for later text overlay. Keep the central area softly illustrated with low-contrast texture and gentle atmosphere, not empty."
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

## GO / NO-GO

1. `python pipeline/check_book.py "pipeline/books/<folder>"` — 0 FAILs (the hook has been showing them after each write).
2. Your gates: the repetition gate on the prompts as a storyboard (pose, props, setting, composition per spread);
   every prompt carries the full preset; the character text is identical everywhere.
3. Write `preflight-report.md`, tell the owner: GO — the prompts are in the Workshop, «Генерувати» on each row; generate
   all 14 panoramas and both squares in ONE Gemini chat (with `canonical.png` attached for Tier H). If a frame is ~80%
   there, fix it in the same chat rather than regenerating. Or NO-GO with the fix list.
