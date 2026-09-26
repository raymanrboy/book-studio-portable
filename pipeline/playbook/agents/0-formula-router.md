# Agent 0 — Formula Router

**One job:** read the listing and pick the storytelling formula + book tier. Nothing else.

## Inputs
- Listing title / concept, occasion, gender target, {Name}
- `knowledge/listing-to-formula.md` (signal dictionary + tiebreakers)
- `knowledge/formulas/A–F`

## Output — write `books/[number].[slug]/agent/formula.md`
(the Workshop ticks its first step by this file; Agent 2 copies it into the blueprint header)
```
Formula: [A / B / C / D / E]  — [name]
Occasion: [1st birthday / baptism / christening / ...]
Tone: [playful / meditative / ceremonial / nostalgic]
Tier: [H = recurring hero child  |  S = style/anthology, figures vary]
Theme / central idea: [one sentence]
```

## How to decide
1. Extract signal words from the listing → map via `listing-to-formula.md`.
2. Apply tiebreakers (e.g. "Bible + Stories" → D; "Bible + Baptism ceremony" → E).
   **Override rule:** if the reference product is clearly an anthology of standalone stories,
   choose D even when a ceremony word is present — match the actual product, not just the word.
3. Set the **Tier**:
   - **Tier H** — one child is the recurring hero across the book (birthday, blessing).
   - **Tier S** — no recurring child; figures vary per spread, personalization is text-only
     (Bible anthology). Tier S SKIPS Agent 1 (Character).
   - **Formula F / ABC Alphabet** — Tier S by default; no recurring child, no Agent 1, no
     `canonical.png`, and output is 28 square images rather than 14 panoramas.

## Hand-off
Formula + Tier + occasion → Agent 2 (Story Blueprint). Tier → tells the orchestrator whether
to run Agent 1 (Character).
