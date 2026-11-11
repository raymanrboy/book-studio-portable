# Step 2 — Story blueprint

Decide WHAT happens on each of the 14 story panoramas and the two squares (dedication, afterword), and set the book's
thin visual header. No book text (step 3), no image prompts (step 5).

Read: the formula file ([formulas/](../../../../pipeline/knowledge/formulas/)), [book-anatomy.md](../../../../pipeline/knowledge/book-anatomy.md)
(structure, rhythm), [visual-world-bible.md](../../../../pipeline/knowledge/visual-world-bible.md) (style DNA), the
character card (Tier H) or the fixed descriptions of the animals (Tier S).

The **Medium** comes from `input.md` (asked at the Medium stop): one code from
[media-presets.md](../../../../pipeline/knowledge/media-presets.md). It locks the `style{}` of every prompt.

## `agent/story-blueprint.md`

Header: the formula block from `formula.md` + `Medium: <code> — <name>` + the visual header (Palette / Mood / Motif /
Must-NOT) + for Tier S the fixed description of every recurring animal (fur, clothes, colors — repeated word for word in
every prompt). Then per spread:

```
## Spread NN — [scene name]
- WHAT happens: [one or two lines — the action/moment]
- Location: [consistent unless the story moves]
- Key props: [only what supports the story]
- Focal point: [the one thing the eye lands on]
- Emotion: [single dominant emotion]
- Who: [the hero / the animals / this scene's figure (anthology)]
```

Spread 01 is the dedication square, 02–15 the 14 panoramas (15 = the finale scene), then `## Afterword` — the
afterword square.

Invent freely: take every aesthetic hook from the listing, but rich, new scenes beat a copy. The book must never be
boring.

## Continuity check (before hand-off)

- Locations consistent, transitions logical, chronology / emotional arc intact.
- **No narrative loop**: if spreads N, N+1, N+2 repeat the same action, place or state with small variation (three
  "sleeping" scenes), rewrite them — every spread moves the story on. Look hardest at the last four.
  [repetition-gate.md](../../../../pipeline/knowledge/repetition-gate.md).
- Active / quiet spreads alternate; the warmth peak near spread 07; the finale resolves warm.
- The story sits left, the calm text area right, on every spread (no alternation — the generator's watermark lands
  right). Write it in words; never percentages, arrows or labels — they leak into prompts.
