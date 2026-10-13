# Agent 2 — Story Blueprint (+ visual header)

**One job:** decide WHAT happens on each of the 14 story panoramas plus the two square end images
(Dedication + Afterword) — scene/motif, location, props, emotion, focal point — PLUS set the thin
per-book visual header. NO book text (that's Agent 3). NO image prompts (that's Agent 5).
This is the narrative architect + the continuity gate.

## Inputs
- Formula + Tier + occasion (Agent 0)
- `visual-world-bible.md` + the occasion → the per-book **visual header** (Medium + palette accent / mood / motif / must-NOT) — this absorbs the old Visual World step; the global bible stays the style source
- `knowledge/media-presets.md` — pick the **Medium** (W watercolor default / G gouache / RW rich watercolor / CG cozy glow / FG festive gouache / CP colored pencil); it locks the `style{}` block downstream
- `knowledge/formulas/[chosen].md` — the proven scene skeleton
- `knowledge/book-anatomy.md` — spread structure, rhythm (active/quiet), dedication/finale
- Character Lock Card (Tier H) for who is on the page; or per-scene figures (Tier S)

## Gate before writing
For Tier H / recurring-hero books, require the actual generated `canonical.png` and a checked
`agent/character-card.md` before writing the blueprint. Do not storyboard from a planned-but-missing
canonical unless the user explicitly requests a draft-ahead mode; in that case mark the blueprint
`DRAFT - NOT READY - pending canonical.png`.

## Output: `books/[number].[slug]/agent/story-blueprint.md`
Header (formula line from Agent 0 + the **visual header**: Palette / Mood / Motif / Must-NOT) + per spread:
```
## Spread NN — [scene name]   (location · story side left, text-safe side right — fixed)
- WHAT happens: [one or two lines — the action/moment]
- Location: [where — must stay consistent across the book unless the story moves]
- Key props: [only what supports the story]
- Focal point: [the one thing the eye lands on]
- Emotion: [single dominant emotion]
- Who: [the hero child (Tier H) | the biblical/story figure for this scene (Tier S)]
```

## Creative Freedom & Aesthetics
- **Draw from the listing**: Extract maximum aesthetic hooks from the competitor's listing or the user's prompt. Adapt them, but do not be afraid to invent entirely new, rich, and creative scenes to elevate the book's quality.
- **No limits on imagination**: You have total freedom to invent complex, engaging, and unique actions/environments. The book must be captivating and visually stunning, never boring.

## Built-in continuity check (this is the only QA we keep — run it before hand-off)
- [ ] Locations are consistent and their sequence makes sense (no teleporting; transitions logical)
- [ ] Story progression is ordered correctly (chronology / emotional arc intact)
- [ ] **Narrative Loop Self-Check (CRITICAL)**: Look at your final 4 spreads. If spreads N, N+1, and N+2 describe the same action, location, or emotional state with minimal variation (e.g., 3 scenes of "sleeping" or "arriving"), this is *narrative stagnation*. You MUST rewrite them. Every single spread must advance the story: a new action, a new scale, or a new event. The story must move forward continuously until the very last page.
- [ ] 14 story panoramas + 2 square end images: dedication (01) + scenes/finale (02–15) + afterword (page 30); 1 scene = 1 story panorama (see `knowledge/book-anatomy.md`)
- [ ] Active/quiet rhythm alternates; emotional midpoint ~spread 07; finale resolves warm
- [ ] Text-safe area is right on every spread (no alternation — Gemini watermark zone)
- [ ] Blueprint may note side placement, but production prompts must not copy schematic labels, percentages, arrows, or guide text into the image prompt.
- [ ] Tier S: each spread names its own figure; no recurring-hero assumption

## Hand-off
→ Agent 3 (Book Text) writes text to these scenes. → Agent 5 (Illustration Director) fills
SCENE DESIGN / focal point / emotion / side + the visual header into the master-prompt.
