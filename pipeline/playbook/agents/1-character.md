# Agent 1 — Character (Tier H only)

**One job:** turn the character source into (a) a canonical portrait prompt and (b) a short
**Character Lock Card**. SKIP this agent entirely for Tier S (anthology) books.

Characters are always SIMPLIFIED, low-detail. This is a short card, NOT a 100-field bible.
Do not over-engineer — no ear blueprints, chin projections, or movement language.

## Inputs
- Character source: a reference photo, a text description, or a chosen archetype
- `visual-world-bible.md` (style DNA — the character must be drawn in this style)

## Outputs
1. **Canonical portrait prompt** — user generates `canonical.png` from it (front-facing,
   neutral pose, plain background, the book's watercolor style). One clean reference.
2. **`books/[number].[slug]/agent/character-card.md`** — the Lock Card (≈8–12 lines). This text becomes the
   CHARACTER CONSISTENCY block of every image prompt.

## Hard stop
For Tier H, Agent 1 ends at STOP 1 until `canonical.png` exists in the book's `agent/` folder. Do not proceed to
Story Blueprint, Book Text, Illustration Director, or pre-flight GO from an imagined character.
If the user explicitly asks to draft ahead before canonical, label downstream files/reports
`DRAFT - NOT READY` and do not present GO. After `canonical.png` arrives, check the Lock Card against
the actual image and revise the card before Agent 2 or Agent 5 use it.

## Character Lock Card template (keep it this short)
```
# Character Lock Card — {Name}'s book

- age: [≈1 year old toddler]
- hair: [color, texture — e.g. fluffy dark-brown curls]
- eyes: [size, color — e.g. large warm brown]
- face: [round face, rosy cheeks, small button nose]
- proportions: [soft baby proportions / chibi: oversized round head, small body]
- skin tone: [warm medium / golden / olive / brown / deep brown etc. — avoid ambiguous words
  like fair/white/light/dark/pale in skin-tone descriptions]
- outfit: [e.g. sage-green short-sleeve onesie, bare feet]
- expression baseline: [gentle, sweet, curious]
- NEVER change: hair color, hair texture, eye color, face shape, cheek volume, proportions, age
```

## Canonical character prompt = JSON (default), 3:4
Output this filled, into `books/[number].[slug]/agent/canonical-prompt.md`. The user attaches the reference,
pastes the JSON, and generates `canonical.png`. That raw character photo is used ONLY here to make
`canonical.png` — it is NEVER attached to spread generation; every spread uses `canonical.png` only. JSON is the default (best consistency on Nano
Banana 2) AND it doubles as the **archetype engine** — see below.
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

## Archetype engine (one base → many consistent variants)
Change ONLY `swappable_attributes` (gender / hair_color / eye_color / clothing_color / skin_tone) → the SAME
child returns with that one change; face, pose, blush, style stay locked. Proven in testing. This
builds the archetype library and powers order-time personalization (customer picks closest variant).
Rules: (1) **girl → mandatory long eyelashes and/or a bow** (else girls read as boys);
(2) real color only (no leftover words like "sage" before "pink");
(3) never tag a changed attribute as "identical to canonical".

## Duo books (Daddy&Me / Mommy&Me) — two recurring characters
Some Formula A books have TWO recurring characters (parent + child), often as matching animals. Then:
- Generate TWO canonical references (e.g. `canonical-daddy.png` + `canonical-child.png`), each from
  its own filled canonical prompt; save both.
- The Lock Card holds BOTH figures (one short block each + a shared "NEVER change" line).
- In every spread prompt, `reference_image` is an ARRAY of both files; the CHARACTER block names
  both figures and how they relate. Style, zones, and negatives are unchanged.
- Order-time personalization still swaps only the CHILD's `swappable_attributes`; the parent stays.

## Notes
- The canonical portrait is the source of truth; the Lock Card is its text twin.
- The generated `canonical.png`, not the intended prompt, is authoritative. If the image differs
  from the prompt, update the Lock Card and downstream character wording to match the image.
- Keep skin-tone wording safe (see the context rule in `knowledge/text-rules.md`).
- Hand-off: `character-card.md` → Agent 5 (Illustration Director) fills the CHARACTER block.
