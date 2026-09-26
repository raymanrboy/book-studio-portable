# Agent 3 — Book Text

**One job:** write the text for every spread from the Story Blueprint. Do not change the
story, scene order, or emotion — translate the blueprint into warm read-aloud text.

## Inputs
- `books/[number].[slug]/agent/story-blueprint.md` (the WHAT — authoritative, do not rewrite)
- `knowledge/text-rules.md` (constraints + sensitive-word context + {Name} rules + templates)
- `knowledge/audience.md` (emotional triggers; write for the parent reading at bedtime)
- The chosen formula's text pattern (`knowledge/formulas/[chosen].md`)

## Output: `books/[number].[slug]/agent/book-text.md`
```
## Cover — Title
[the cover title with {Name}, e.g. {Name}'s Baptism Day — one short line, the text placed on the front]

## Spread 01 — Dedication
[dedication template, {Name} + gifter]

## Spread 02 — [scene]
[text per the formula's pattern]
...
## Spread 15 — Finale
[closing line that lands hard]

## Afterword — Closing wishes (last page · separate square image · center-safe)
[1–2 short warm lines, distinct from the finale]
```

**The headings are machine-read** (the Workshop reads this file into its rows): keep exactly `## Cover`, `## Spread 01`…`## Spread 15`,
`## Afterword`. Everything under a heading is the text that goes on that page — no notes, stage
directions or page labels under it. Write the child's name as `{Name}` and the giver as `{Gifter}`.

## Hard rules — owned by `knowledge/text-rules.md` (read it; don't restate)
Quick reminders of its gates: 6 short lines / 25-35 words per spread; `{Name}` ≥ every 2–3 spreads.
`{Name}` MUST NEVER be the final rhyming word in a line. Weave `{Name}` in different roles (subject, object) not just as a direct address. Every emotional low resolves to warmth; finale lands.
**Most load-bearing:** the sensitive-word context rule (fair/white/light/dark/pale never for skin,
beauty, purity, goodness, or a child's appearance; never compare the child to another character) —
it prevented a real 1-star racist review.

## Aim high from the start
Write to the **Poetry quality & American English** standard in `knowledge/text-rules.md`:
simple, predictable, bouncing rhymes (AABBCC), short lines (4-5 words max), NO filler words ("And", "So") starting every line, US spelling/idiom, no Britishisms or AI-stock phrasing. The **Text Critic (Agent 4)** then audits and polishes — so hand it your best, not a draft.

## Craft method (do this before hand-off)
For each spread, write exactly 6 short lines of **uniform visual length** (4-5 full words, strictly 7-8 syllables per line):
- **Canva Rectangle Standard:** Lines must NOT vary wildly in length. No short 3-word line paired with an 8-word line. The stanza must form a clean visual rectangle so it fits Canva text boxes without awkward word wraps.
1. Lines 1-2 (Image & Action): What we see and what it does.
2. Lines 3-4 (Promise): How it connects to love or safety.
3. Lines 5-6 (Childward Turn & Finale): Bringing `{Name}` into the scene naturally.

Use this quality bar:
```
Morning sun is shining bright,
Little birds will take to flight.
Singing songs up in the tree,
Happy as a bird can be.
{Name}, a brand new day is here,
God is always standing near.
```

```
Little duck goes waddle, quack,
Water rolling off his back.
Puddles splashing in the street,
Cold around his little feet.
{Name}, when rainy days are cold,
You have loving hands to hold.
```

Do not use `{Name}` ONLY as a direct vocative/address. Integrate it as a subject or object sometimes.

For Formula B bedtime books, respect the blueprint's time-of-day arc. Do not let the poem become
a random list of pretty flowers/stars; each spread needs a new image family and a new emotional
function.

## Quick self-check (then hand to Agent 4 — Text Critic)
- [ ] No sensitive words used for skin/appearance/purity/goodness
- [ ] {Name} frequency + at least one line-initial {Name}
- [ ] Reads aloud naturally; no forced rhyme
- [ ] Uniform line length (4-5 words / 7-8 syllables per line; forms a clean visual rectangle for Canva)
- [ ] No repeated image crutches unless intentional (flowers, stars, sleep/rest/nest)
- [ ] Every stanza bridges image → promise; no disconnected pretty lines
- [ ] Finale is memorable and warm

## Hand-off
→ **Agent 4 (Text Critic)** polishes the text to the poetry / US-English standard; its output is final.
Text is overlaid in layout (Canva), NOT baked into images. Agent 5 (images) runs in parallel and
only cross-checks the per-spread emotion; it does not put text in prompts.
