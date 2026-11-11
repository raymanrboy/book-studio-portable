---
title: Claude Code setup — rules, skills, hooks
type: dev
updated: 2026-11-11
code: []
---
# Claude Code setup — rules, skills, hooks

> Since 2026-11-11 the project is worked on with Claude Code only, and its instructions are laid out the way Claude Code
> loads them: one short `CLAUDE.md` always, rules that load with the folders they cover, skills for procedures, a
> subagent for a fresh-eyes check, hooks for what must never be skipped ([decisions](../decisions.md)).

## What lives where

| Kind | Where | Loads |
|---|---|---|
| The project in brief, the owner, the "never" list, where to start, commands | `CLAUDE.md` (repository root) | every session that touches the repository |
| Rules for an area | `.claude/rules/code.md` (`app/`), `ui.md` (`app/web/` — the owner's interface logic), `wiki.md` (`wiki/`), `books.md` (`pipeline/`) | when Claude reads or edits a file there |
| Procedures | `.claude/skills/`: `book`, `book-cover`, `book-variant` (making books), `etsy-seo`, `listing-slides`, `wiki-update`, `wiki-ingest`, `wiki-lint` | by their description or `/name` |
| A fresh-eyes check | `.claude/agents/book-text-critic.md` | when the `book` skill hands it a book's text |
| Guards | `.claude/hooks/book_guard.py`, wired in `.claude/settings.json` | on every write / shell command (below) |
| Never read | `permissions.deny` in `.claude/settings.json`: `.secrets.txt`, `app/data/vault.json` | always |

**Open `Book Studio` as the session's folder**: Claude Code takes `.claude/settings.json` (the permissions and hooks)
only from the folder a session starts in. The parent `Book Studio Portable\.claude\settings.json` (not in git) holds the
same permissions and hooks as a safety net for sessions started there. The rules, skills and `CLAUDE.md` of
`Book Studio` load in either case, when its files are touched.

## The hooks (`book_guard.py`)

- **Before a write** into `pipeline/books/<book>/`: only `agent/` is the agent's — `book.json`, `pictures/`,
  `originals/`… are refused; a Tier H book's story, text and prompts are refused until `agent/canonical.png` exists,
  unless the file starts with `DRAFT - NOT READY` (the owner asked to draft ahead).
- **Before a shell command**: one that would print `.secrets.txt` or `vault.json` is refused.
- **After a write** of a book's `agent/*.md`: the book check runs and its FAILs go back to Claude.

A hook that cannot read its input lets the call through — it must never stop unrelated work.

## Third-party skills

Installed on 2026-09-30 (texts only), **local only** (`.gitignore`: some carry no licence). Kept: `impeccable` (trimmed,
with project overrides at its top; no launcher), `make-interfaces-feel-better`, `laws-of-ux`, `ux-heuristics`,
`cognitive-load-audit` (its subtraction test is the closest to "does this earn its place"), `systematic-debugging`. The
owner's interface rules (`.claude/rules/ui.md`) win over them. Taken out on 2026-11-11 (React/Tailwind or UX-strategy
guidance that does not fit a plain-JS program, or duplicates): they wait in `..\_archive\claude-skills\`.

## Rules for using them

- A skill's own advice never overrides `CLAUDE.md`: no commits unless asked, no live writes, the owner's words first.
- Third-party skills are read before installing (commits, network, forced lines, scripts); none is run as code.
- The owner's correction of an interface goes into `.claude/rules/ui.md` **and** [ui-principles](../owner/ui-principles.md)
  the same day.

## Related

- [The interface the owner wants](../owner/ui-principles.md) · [Preview](preview.md) · [How to run this wiki](wiki-rules.md)
