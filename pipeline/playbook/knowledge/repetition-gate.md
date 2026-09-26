# Repetition Gate

The one rule against a repetitive, visually static book. Applied at **two checkpoints** — text +
blueprint (Text Critic) and the final prompt storyboard (Illustration Director) — same logic, two
artifacts. Reject and rewrite any run that repeats the same scene engine, even if the wording changes.

## The rule
Every spread must give a **distinct drawable moment**: a different body action, pose, prop,
environment, scale, direction of movement, and focal relationship. "Same emotion, different scenery"
is NOT enough. A gentle/bedtime book may stay soft, but it cannot be visually static — each spread
needs its own page-turn reason.

## Hard-reject patterns
- 3–4 spreads in a row with the same pose (holding / cuddling / carrying the child the same way).
- Multiple "sleeping under moon/stars" scenes that differ only in lighting.
- Repeated nest / grass / clover / moon / rest images with no new action or prop.
- The final 4 spreads all resolving as the same cuddle / sleep / rest image.

## Where to look
- **Text + blueprint** (`book-text.md`, `story-blueprint.md`): each spread has a distinct visible
  action, prop, setting, emotional beat, and page-turn reason.
- **Prompt storyboard** (`spread-prompts-json--*.md`, when they exist): scan as a storyboard, not as
  isolated prompts. Compare each prompt's `scene` (action / focal / pose / props / setting),
  `composition`, `lighting`, `text_safe_area`, `emotional_goal`, `output`. Prompts add pose and
  composition the blueprint didn't carry, so this is a genuine second checkpoint.
- **The final 4 spreads** especially: force a clear sequence of different beats, e.g.
  guided path → song/listening → dream/flight → dawn/ritual — NOT cuddle → moon cuddle → sleep
  cuddle → dawn cuddle.

## Verdict
- 2 nearby spreads too similar → rewrite one.
- 3+ repeating the same visual/narrative idea → mark the run **NOT READY** and rewrite the whole run
  **before any image generation**.
