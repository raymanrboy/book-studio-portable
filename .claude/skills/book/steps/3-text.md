# Step 3 — Book text

Turn the blueprint into warm read-aloud text. Do not change the story, scene order or emotion.

Read: `agent/story-blueprint.md` (authoritative), [text-rules.md](../../../../pipeline/knowledge/text-rules.md) — every
text rule lives there and only there — [audience.md](../../../../pipeline/knowledge/audience.md), and the chosen
formula's text pattern. Write to the critic's standard from the start; the critic polishes, it does not rescue.

## `agent/book-text.md` — the headings are machine-read

```
## Cover — Title
[one short line with {Name}, e.g. {Name}'s Baptism Day]

## Spread 01 — Dedication
[the dedication template: {Name} and {Gifter}]

## Spread 02 — [scene]
[text]
...
## Spread 15 — [finale scene]
[the closing stanza that lands hard]

## Afterword — Closing wishes
[2–4 short warm lines, distinct from the finale]
```

Keep exactly `## Cover`, `## Spread 01` … `## Spread 15`, `## Afterword`: the Workshop reads its rows and the cover
title from them. Under a heading goes only the page's text — no notes, stage directions or labels. The child is
`{Name}`, the giver `{Gifter}`.

The cover title decides the cover's layout (the `book-cover` skill): `{Name}` first («{Name}'s …»), last («… for
{Name}») or in the middle («Mommy & {Name}: Our First Christmas»).

## Self-check, then hand to the critic

- No sensitive word for skin, appearance, purity or goodness.
- `{Name}` often enough (every 2–3 spreads, at least one line starting with it), never on a rhyming end, in varied
  lines and roles.
- Uniform line length (the Canva rectangle), no filler starts ("And", "So", "Then").
- No repeated image crutches (flowers, stars, sleep, nest) unless intended; every stanza bridges image → promise.
- The finale is memorable and warm.

Then run the `book-text-critic` subagent on the book folder. It polishes `book-text.md` itself and returns a report: save
it as `agent/text-critic-report.md`, look its changes over, and bring to the owner anything it left for his choice.
READY or MINOR FIXES (applied) closes the text. If the subagent is not available (a session opened outside
`Book Studio`), do the critic pass yourself, with `.claude/agents/book-text-critic.md` as the checklist.
