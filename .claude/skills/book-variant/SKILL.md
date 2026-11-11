---
name: book-variant
description: "Make a hero variant of a Tier H Workshop book (a human child hero with canonical.png) — the same book with another child look (G1 blonde, B5 deep skin …): the variant's hero edit prompt and the 14 swap prompts that replace only the child in each finished spread. Use when the owner asks for a variant, another archetype, «блондинка для книги 41», «варіанти героя»."
argument-hint: "[book number] [archetype codes]"
---

# Hero variants (Tier H only)

One book, the same 14 spreads, another child. Paths are relative to the repository root (`${CLAUDE_SKILL_DIR}/../../..`).

```
pipeline/books/<book>/agent/variants/<G#_name>/    e.g. G2_dark_haired — the codes are in pipeline/knowledge/archetypes.md
  hero-prompt.md    the edit prompt for canonical.png (one ```json block): change only the swappable attributes
  2.json … 15.json  one swap prompt per story spread, named by its number (2 = pages 2–3 … 15 = 28–29)
  hero.png          the owner saves it (the Workshop catches it) — never write it
```

The Workshop shows each variant as a tab: the original spread (un-mirrored), the variant's hero, then the swap prompt,
and files the results under `pictures/variants/<name>/`. A variant also gets its own cover in the cover tool.

## hero-prompt.md

Image: `canonical.png`. "Edit the attached reference image: the same child, changing only the swappable attributes."
`reference_rule` lists everything that stays identical (style, pose, face, outfit word for word from the character
card, background); `swappable_attributes` holds only the archetype's block from `archetypes.md` (a girl gets long
eyelashes and/or a bow; the real color only). The archetype numbers never change meaning: G1 is the same child in every
book.

## 2.json … 15.json — the swap prompt (flat JSON)

`task` ("Edit Image 1: replace only the child with the child from Image 2. Everything else in Image 1 stays exactly as
it is."), `images` (image_1 = the original 2:1 panoramic illustration, image_2 = the new child, hero.png),
`aspect_ratio` 2:1, `child_to_replace` (who, and that spread's scene in a line from the blueprint),
`new_child_identity` (hair, eyebrows, skin, bow — from Image 2), `keep_from_image_1` (composition, camera, background,
lighting, every prop and other figure, the child's pose, expression, position, size and the outfit word for word, the
calm area on the right, the style), `rules` (change only hair, eyebrows, bow and skin — on every visible skin; never the
pose or background from Image 2; under a hat the hair stays where Image 1 shows hair), `negative` (the preset's
negatives, the text guards, "changed composition", "changed background", "changed outfit", "extra characters",
"cropped edges"), `output`.

A complete example: `pipeline/books/41.night-before-christmas-child/agent/variants/G1_blonde/`.
The generator-language rule holds here too ([master-prompt.md](../../../pipeline/knowledge/master-prompt.md#generator-language)).
