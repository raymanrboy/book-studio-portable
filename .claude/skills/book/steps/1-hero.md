# Step 1 — Hero (Tier H only)

Turn the character source (a reference photo, a description, or an archetype from
[archetypes.md](../../../../pipeline/knowledge/archetypes.md)) into a canonical portrait prompt and a short lock card.
Characters are simplified and low-detail: a short card, not a 100-field bible.

## Outputs

1. **`agent/canonical-prompt.md`** — the JSON below, filled. The owner attaches his reference, generates
   `canonical.png` (3:4) and saves it in `agent/` (the Workshop's «Герой» step catches it). That raw photo is used only
   here; every spread uses `canonical.png`.
2. **`agent/character-card.md`** — the lock card, 8–12 lines. It becomes the CHARACTER block of every image prompt.

Then **stop** (the Hero stop in SKILL.md). When `canonical.png` is there, compare the card with the actual picture and
fix the card — the picture, not the prompt, is the truth.

## Lock card

```
# Character Lock Card — {Name}'s book

- age: [≈1 year old toddler]
- hair: [color, texture]
- eyes: [size, color]
- face: [round face, rosy cheeks, small button nose]
- proportions: [soft baby proportions / chibi: oversized round head, small body]
- skin tone: [warm medium / golden / olive / brown / deep brown — never fair/white/light/dark/pale for skin]
- outfit: [e.g. sage-green short-sleeve onesie, bare feet]
- expression baseline: [gentle, sweet, curious]
- NEVER change: hair color, hair texture, eye color, face shape, cheek volume, proportions, age
```

## Canonical prompt (JSON, 3:4) — also the archetype engine

```json
{
  "task": "full-body character reference render (canonical)",
  "reference_image": "attached reference",
  "reference_rule": "Match the reference exactly EXCEPT the fields in `swappable_attributes`; keep identical face structure, proportions, pose, blush, and art style; do not tag a changed attribute as 'identical'.",
  "aspect_ratio": "3:4",
  "canvas": "full body, forward-facing, centered; cream textured watercolor paper; soft wash under bare feet; no scene/props/text",
  "swappable_attributes": {
    "gender_presentation": "neutral | girl | boy",
    "hair_color": "...", "eye_color": "...", "clothing_color": "...", "skin_tone": "...",
    "girl_marker": "if girl: MANDATORY long eyelashes AND/OR a small bow"
  },
  "character": { "age": "~1yo", "hair": "tousled curls, color=swappable_attributes.hair_color", "eyes": "large round, color=swappable_attributes.eye_color", "face": "round, circular rosy blushes, button nose, soft smile", "proportions": "soft chubby, natural head", "skin": "swappable_attributes.skin_tone", "outfit": "short-sleeve onesie, color=swappable_attributes.clothing_color, bare feet" },
  "pose": "full-body forward, arms relaxed, gentle happy expression",
  "style": { "medium": "hand-painted watercolor", "linework": "delicate fine pencil/ink", "texture": "natural paper", "lighting": "soft even" },
  "negative": ["harsh/heavy black outlines","3D render","vector","anime","photorealism","AI-art look","text","scene background","props"]
}
```

Changing only `swappable_attributes` returns the same child with that one change (tested) — the archetype library and the
order-time variants rest on it. Rules: a girl gets long eyelashes and/or a bow (else she reads as a boy); the real
color only (no leftover "sage" before "pink"); never call a changed attribute "identical to canonical".

## Duo books (Daddy & Me, Mommy & Me) with two recurring characters

Two canonical prompts and pictures (`canonical-daddy.png`, `canonical-child.png`); the card holds both figures; in every
spread prompt `reference_image` is an array of both; order-time variants swap only the child.
