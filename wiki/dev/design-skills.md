---
title: Design and code skills for agents
type: dev
updated: 2026-10-03
code: []
---
# Design and code skills for agents

> Agent skills installed in `.claude/skills/` on 2026-09-30 (texts only — no scripts, no hooks), found and read at the owner's
> request: "the best skills for interface logic, icons and visual language, and technically flawless code". The third-party
> ones are **local only** (`.gitignore`: some carry no licence); the project's own skills are in git. How the owner wants
> the interface to behave — [ui-principles](../owner/ui-principles.md); the project's own skill
> `book-studio-ui-logic` turns that into a checklist an agent applies before writing UI.

## Which skill for what

| Job | Skill | Notes |
|---|---|---|
| **The owner's interface logic** (show don't tell, a label does what it says, nothing redundant, the real state, one loud button, light first) | `book-studio-ui-logic` (project's own) | Wins over the general ones below |
| UX audit, information architecture, flows, states | `uxcraft`, `product-design`, `ux-heuristics`, `laws-of-ux`, `cognitive-load-audit` | `cognitive-load-audit`'s subtraction test is the closest to "does this earn its place" (its conversion framing is ignored) |
| Plan before building | `planning` | |
| Visual craft, typography, spacing, colour, polish | `impeccable` (trimmed, with project overrides at its top), `make-interfaces-feel-better`, `frontend-design`, `frontend-design-v2`, `ui-design`, `typography-audit` | `impeccable`: no launcher/live/init (not installed); never creates PRODUCT.md/DESIGN.md; refinement inside the owner's look, not replacement |
| **Icons** | `icon-set-generator`, `icon-design` (+ the reviewer's rubric in `icon-design/references/critique-rubric.md`) | Their own strokes are 2 px; ours is 1.6 on a 24 grid, one meaning per icon ([icons.js](../architecture/frontend.md)) — ours wins |
| Checking a rendered interface | `ui-verification` (no Playwright here: the built-in browser and headless Edge — [preview](preview.md)) | |
| **Code**: review, simplification, debugging, proof | `tidy`, `code-simplification`, `systematic-debugging`, `verification-before-completion`, `python-performance-optimization` | Apply modes never commit; the repo's own tests and `wiki_check.py` are the proof |

## Not installed, and why

`taste-skill`, `minimalist-skill` (React/Tailwind, landing pages), `nothing-design` (a foreign aesthetic with mandatory
fonts — kept only as a model of how to write tokens/components), `oklch-skill` (no licence), `emil-design-eng` (a forced
"Initial Response" line), `canvas-design` (posters), `ui-ux-pro-max` (a 1 MB data dump and Python scripts), `ux-auditor`
(Playwright and a browser download), `test-driven-development` ("delete code written before its test" — too hard for UI work),
Trail of Bits' `differential-review` (crypto-oriented), `code-improver` (an autonomous loop), `commit-commands` and
`ralph-wiggum` (against "commit only when asked").

## Rules for using them

- A skill's own advice never overrides [AGENTS.md](../../AGENTS.md): no commits, no live writes, the owner's words first.
- Third-party skills are read before installing (`grep` for commits, network, forced lines, scripts); none is run as code.
- The owner's correction of an interface is a rule for `book-studio-ui-logic` **and** `owner/ui-principles.md` — the same
  day.

## Related

- [The interface the owner wants](../owner/ui-principles.md) · [Preview](preview.md)
