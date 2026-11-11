# Master scene prompt

The skeleton of every 2:1 story panorama (step 5 of the book skill fills only the variable blocks), and why each block
is there. It came out of many failed tries: **verbose beats minimal** — short "reference-only" prompts lost the
character and the model drew at random; the big structured prompt with explicit limits is what holds. Do not simplify
the structure. The style itself, on the contrary, stays simple: big calm fields, simple shapes, low detail.

## Generator language

A generator-facing prompt describes **one standalone picture** — never a printed object, a publishing artifact or a
physical layout. Image models draw what they are told *not* to draw, so these words stay out of every prompt object,
**including `negative[]`**:

`book`, `storybook`, `page`, `pages`, `spread`, `cover`, `front`, `back`, `spine`, `fold`, `seam`, `gutter`,
`divider`, `diptych`, `two-panel`, `split`, `half`, `halves`, `sliced`, `mockup`, `product`, `physical`, `hardcover`,
`paper stack`, `page edge`, `page edges`, `printed`.

The book check (`pipeline/check_book.py`) fails a prompt that has one. Say it positively instead:
"one uninterrupted 2:1 panoramic illustration", "main subject on the left", "calm illustrated area on the right for
later text overlay", "one continuous environment", "one standalone 1:1 square illustration".

**The centre line.** Gemini draws a vertical line down the middle of a 2:1 picture when the prompt names publishing
or multi-region layout. The Workshop cuts every panorama exactly in the middle, so a line ruins both pages. Frame it as
ONE wide panorama, keep the middle ordinary continuous scenery (grass, sky, water), carry one continuity anchor across
(a horizon, a path, a cloud band), keep strong verticals and abrupt light changes away from the centre.

No percent signs, ratios, `LEFT/RIGHT` labels, arrows or guide marks in a prompt either — the model draws them. Brief
and reference photos are for orienting yourself only; they never go into a production prompt.

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
[THE FULL STYLE PRESET — pipeline/scripts/preset.py]

SCENE DESIGN
[What happens, key props, location, focal point; how the environment continues quietly into the right-side calm area
without becoming empty.]

TEXT OVERLAY SPACE
Reserve a calm illustrated area on the right for later text overlay.
No text, letters, typography, numbers, symbols, logos, watermarks, labels, signs, arrows, or guide marks.
Keep this area low contrast, uncluttered, and softly painted while still belonging to the same environment.

LIGHTING
[Time of day and quality of light.]

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

The prompts are written as **flat JSON** with these blocks as fields (the schema is in step 5): JSON held the
character's signature features markedly closer than prose in an A/B test; keep it flat — deep nesting gets ignored.

## The load-bearing blocks — change only with a test on one spread

| Block | What it holds | Without it |
|---|---|---|
| "one uninterrupted 2:1 panoramic illustration" | one continuous scene, no layout signal | two pictures, a frame, an object |
| the character / subject list | the identity anchor in words | the reference "averages" into another child |
| negatives for text and style only | text noise and style drift, without naming a format | the model latches on a named concept and draws it |
| the text area: a side + "no text", part of the scene | a calm illustrated space for the text | a white hole, a frame or a cut-off half |
| 2:1 + full bleed + the ratio line | the format | wrong proportions (a 2:1 once came out 1:1 — say the ratio in the request text too) |
| story left, calm area right, always | the generator's watermark lands on the calm right | a seam, an empty half, label leakage |
| the full style preset | one paint system across the book | frames that look like different books |

The variable blocks: scene, lighting, emotion (from the blueprint), character (the card or the animals' description),
style (the preset + the book's palette). Tier S: no reference fields; consistency is carried by style and the repeated
character text alone.

Two-pass "generate the scene, then swap the child" failed — the second pass keeps the realistic bone structure. Generate
at once with the full prompt (variants are a different, tested edit — the book-variant skill).

Dedication and afterword squares use the square contract (step 5); the cover uses the book-cover skill.
