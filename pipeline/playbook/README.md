# Playbook — Navigation

Entry point is `../AGENTS.md`. This is the playbook map.

The story pipeline is 6 single-responsibility agents (0–5). Agent 6 runs later for the final wide
image. Each reads from `knowledge/` and the bibles, writes one short file into `books/[number].[slug]/agent/`,
and keeps generator-facing prompts image-only.

```
playbook/
  README.md                  ← you are here
  master-prompt.md           ← ★ skeleton of ALL image prompts (filled by agents)
  master-prompt-anatomy.md   ← which blocks are load-bearing (why it works)
  visual-world-bible.md      ← ★ global style DNA
  workflow.md                ← full pipeline, step by step
  onboarding.md              ← interactive "lead by the hand" (drip-fed input)
  build-book.md              ← autonomous orchestrator (full brief → ready-to-generate)
  agents/
    0-formula-router.md      → formula + Tier
    1-character.md           → canonical.png prompt + character-card (Tier H)
    2-story-blueprint.md     → visual header + WHAT per spread + continuity check
    3-book-text.md           → cover title + text per spread
    4-text-critic.md         → polishes text (poetry + native US-English) + repetition gate
    5-illustration-director.md → story panorama prompts + square end-image prompts + pre-flight GO/NO-GO
    6-wraparound-image-director.md → final wide-image prompt → cover-prompts-json
  knowledge/
    listing-to-formula.md    ← pick a formula from a listing
    formulas/                ← A..F storytelling formulas (F = ABC square exception)
    book-anatomy.md          ← spread structure, rhythm, page types
    text-rules.md            ← word count, rhyme, sensitive-word context, {Name}
    audience.md              ← who buys, why, emotional triggers
    archetypes.md            ← 14 swappable_attributes presets (skin/hair/eyes/gender) for the character engine
    repetition-gate.md       ← one anti-repetition gate (text + prompt storyboard)
```

## Core constraints (never break)
- **Exception:** Formula F / ABC Alphabet Square Book uses 2 dedication squares + 26 A-Z square
  illustrations. No 2:1 interior panoramas, no slicing, no recurring hero, and no `canonical.png`
  unless the user explicitly changes the format.
- 30 pages = first page (dedication square) + 14 story spreads + last page (afterword square);
  see `knowledge/book-anatomy.md`. One scene per story spread.
- {Name} at least every 2–3 spreads.
- Treat fair/white/light/dark/pale as context-sensitive: avoid for skin, beauty, purity,
  goodness, or human appearance; allow normal scenery uses like morning light or dark sky —
  see `knowledge/text-rules.md`.
- Story panorama prompts use the `master-prompt.md` skeleton filled by Agent 5 — no improvised structures.
- Dedication and Afterword are two separate 1:1 square image prompts from Agent 5.
- The final wide-image prompt uses Agent 6 and must still describe only one standalone 2:1 panorama.
- Generator-facing prompt bodies never mention book/page/spread/cover/front/back/spine/fold/gutter/seam,
  including inside negatives.
- 2:1 story panoramas, 1:1 square end images, text-safe/overlay area, and safe text/style negatives.
  Watercolor only unless a different locked medium preset is chosen; no 3D/vector/anime/photoreal.

## Entry points
`AGENTS.md` in the project root is the one entry point for book agents (any agent reads it; the separate
`GEMINI.md` copy was dropped on 2026-10-03). `CLAUDE.md` is different on purpose: a fork for coding
agents working on Book Studio's code (the Workshop is part of it).
