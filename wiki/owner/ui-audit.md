---
title: The interface audit (November 2026)
type: owner
updated: 2026-11-02
code:
  - app/web/css/app.css
---
# The interface audit (November 2026)

> A deep audit of the whole interface (1–2 November 2026): three passes over every page on made-up data, the owner's
> rules from [ui-principles](ui-principles.md), and the **unslop-ui** skill. What is already fixed lives in
> [log.md](../log.md); this page keeps what was found and **what is still open** — the starting point for the next
> polishing pass. The owner is looking for more skills for that pass; until then nothing here is to be fixed.

## How it was done

- **Pass 1 — screenshots.** A crawler (headless Edge on a stubbed dev server, never a button that leaves Book Studio)
  walked every page and opened every card, pressed every control on it and shot each at 1440 / 1100 / 940 px, light theme.
  Six reviewers judged the shots against the owner's rules and the unslop-ui rules.
- **Pass 2 — measures.** Fonts, sizes, line heights, paddings, gaps, card nesting, saturated colours, sentences and loud
  buttons per page, read from the live DOM.
- **Pass 3 — logic.** The order's and the book's paths stage by stage: is the loudest thing the next step? Every link
  between pages followed (no broken routes, no console errors).
- A separate reviewer checked the key claims against the shots: most confirmed, some partly, none refuted.
- The presentation of the results — a private Claude artifact (34 slides): https://claude.ai/artifact/JVMuYzPQqfLAV18uthyyTL
- The crawler's shots and raw measures were kept only in a temporary folder of that session — to repeat the audit,
  run a crawl again.

## The unslop-ui skill

[github.com/yuwen-lu/unslop-ui](https://github.com/yuwen-lu/unslop-ui) — one `SKILL.md`, ten sections against "vibe-coded"
UI: colour 70/20/10 (no same-hue goo), no icon in a tinted rounded square, no emoji as visuals, no default serif, no
glassmorphism, gradients and shadows with restraint (no coloured shadows), no card-in-card, animations purposeful and
fast (150–300 ms), a clear #1 thing to look at, no `border-left` with `border-radius`.

**What it does not cover:** a spacing grid, a type scale, line heights, letter spacing. Those come from the owner's own
request ("однакові відступи, правильні шрифти") and need another method or skill.

**The run over the audit's data (2026-11-02):**
- Fixed: the icons in tinted squares (Tools, the drop menu, the order card's print row, Profit's «Період», the offline
  screen) and the coloured shadow of the calendar dots.
- Passes: no glassmorphism, no emoji visuals (✓ in a few texts is a typographic mark), gradients only with a job
  (paper patterns, skeletons, progress), nesting no deeper than one, one loud button per screen.
- Kept against the skill by the owner's decisions: smooth entrances and transitions (420–700 ms — his 170 Hz screen),
  the step squares (their fill *is* the state), Sitka only for book titles, the purple chips (replacement, bundle,
  archived book — each a meaning).

## Still open

### Spacing
- The `--sp-1…8` tokens (4 px grid) now replace the values that already sat on the grid; **the rest is off the grid** —
  in the audit 440 of 716 spacing values, 37 different values in all.
- On screen: 25 different gaps (6, 8, 10, 12, 14 px lead; also 2, 3, 5, 7, 11, 18, 22, 26 px) and 13 different card
  paddings (18/20 and 12/14 px lead; also 14/10, 10/12, 16/18 …).
- Wanted: a few gaps (4 / 8 / 12 / 16 / 24) and two or three card paddings, then everything mapped onto them, with
  before/after shots.

### Type
- Families by share of text: Segoe UI ~59 %, Consolas (mono) ~18 %, Bahnschrift ~15 %, Sitka ~7 %. Mono is still used
  for more than codes (paths, receipts, IDs — fine; some meta lines — to check).
- Sizes off the scale: 11.96, 13.34, 20.208, 45.468, 11.04 px (from `em` multiplications), also 29 and 44 px in the
  slide editor.
- Line heights: mostly 1.6 and 1.4; a few 1.05–1.2 and 0 — to check.
- Wanted: one type scale (sizes, weights, line heights) as tokens, every page on it.

### Words instead of signs
- Sentences per page (audit): the Workshop book pages 33–34, the book passport 31, Settings 26 — the owner's rule is
  "show, don't tell". The empty frames repeat the same caption; zones and steps explain what the picture shows.

### Smaller
- Profit's table: at ~800 px the «Не оплачено» pill touches the card's edge (940 px is fixed).
- The order history overlapping the address was not reproduced on the sample orders — check on real data.
- Switch styles: `switch` (Settings), `check` (lists), `seg` (modes) — one role each, kept for now.

## Related
- [The interface the owner wants](ui-principles.md)
- [Design skills](../dev/design-skills.md)
- [Interface preview](../dev/preview.md)
