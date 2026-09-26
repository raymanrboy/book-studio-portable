# MASTER SCENE PROMPT

This is the canonical production prompt skeleton for generated story images.
Agent 5 fills only the variable blocks. Keep the generator-facing language clean:
describe a single standalone 2:1 image, not a printed object, publishing artifact,
or physical layout.

Generator-facing prompts must avoid physical-object and layout-artifact vocabulary
everywhere, including `negative[]`. Do not mention the forbidden concepts even as
things to avoid; Nano Banana may still draw them when named.

Use positive visual language instead:
- one uninterrupted 2:1 panoramic illustration
- main focal subject and storytelling action on the left
- calm illustrated area on the right for later text overlay
- one continuous environment across the full image

---

## Template

```text
Create a premium children's illustration in [MEDIUM STYLE].

Canvas: one uninterrupted 2:1 panoramic illustration, full bleed, extending all the way to the absolute edges. There must be no white border, no paper margins, no rounded corners of the image frame, and no sticker outlines.

COMPOSITION
Place the main subject, focal action, and strongest visual interest on the left.
Let the environment open naturally into a calm, spacious illustrated area on the right for later text overlay.
The right area must remain part of the same world: quiet sky, ground, water, clouds, runway, distant trees,
soft reflections, atmospheric texture, or other low-contrast scenery may continue there.
Keep the full image flowing as one continuous cinematic scene.
Do not add visible words, labels, captions, measurements, arrows, guides, UI marks, logos, or watermarks.

CHARACTER / SUBJECT
[CHARACTER OR SUBJECT CONSISTENCY]

VISUAL STYLE
[FULL EXPANDED STYLE PRESET FROM media-presets.md: preserve paint behavior, surface texture,
linework, forms, detail floor, palette behavior, light, depth, overlay behavior, mood, and finish.]

SCENE DESIGN
[SCENE DESIGN: what happens, key props, location, focal point. Mention how the environment continues
quietly into the right-side calm area without becoming empty.]

TEXT OVERLAY SPACE
Reserve a calm illustrated area on the right for later text overlay.
No text, letters, typography, numbers, symbols, logos, watermarks, labels, signs, arrows, or guide marks.
Keep this area low contrast, uncluttered, and softly painted while still belonging to the same environment.

LIGHTING
[LIGHTING: time of day and quality of light.]

DEPTH
Use foreground, midground, and background layers to carry the scene across the full 2:1 image.
Keep the strongest contrast and detail near the main subject; soften detail toward the right.

EMOTIONAL GOAL
[EMOTIONAL GOAL]

QUALITY REQUIREMENTS
Premium children's illustration quality. Clean composition. Simple readable shapes. Low visual noise.
Natural visual flow. Beautiful calm overlay space. The right area remains softly illustrated
with low-contrast scenery and atmospheric texture. Avoid framing, collage, mirrored duplicate scene,
distorted parts, visible words, logos, or watermarks.

Aspect ratio: 2:1. Full bleed. One continuous panoramic illustration.
```

---

## Notes

- For Tier H, include the actual canonical character reference only when one exists.
- For Tier S, omit reference fields entirely and describe the scene's subject directly.
- Brief/reference photos are for agent orientation only. They do not go into production prompts.
- Medium swaps only replace the VISUAL STYLE block with a preset from `knowledge/media-presets.md`.
- For Dedication and Afterword square images, use the Agent 5 square end-image contract instead of
  this 2:1 story panorama template.
- For the final wide marketing/wrap image, use Agent 6. It follows the same image-only language
  rule but places the focal subject on the right and the calmer continuation on the left.
