---
title: Etsy SEO
type: feature
updated: 2026-11-12
code:
  - seo/seo.py
  - seo/README.md
  - seo/knowledge/rules.md
  - seo/knowledge/erank-browser.md
  - seo/knowledge/description-template.md
  - seo/knowledge/blocklist.tsv
  - .claude/skills/etsy-seo/SKILL.md
---
# Etsy SEO

> A self-contained agent tool for a listing's title, tags and description. It has no screen in the program: the agent runs it on the owner's words («зроби SEO для 35», `/etsy-seo 35`) through the skill `.claude/skills/etsy-seo/SKILL.md`, which holds the steps and the report rules (plain Ukrainian to the owner, the listing itself in English).

## What it produces

For a Workshop book the agent writes `pipeline/books/<n>.<slug>/agent/listing-seo.md`:

- **A long title**, 110–140 characters in phrase blocks that buyers really type; the first one or two blocks are split by ` | `, the rest by `, ` (`seo.py lint` checks it).
- **13 tags**, chosen by numbers and buyer intent (product, theme, recipient, occasion, giver, keepsake).
- **The description** from `seo/knowledge/description-template.md`; only the parts about the book change. A new book is always «30-page»; an existing listing keeps the page count its description already says (books 1–23 are 24-page). Hardcovers are described as matte. «MADE TO ORDER WITH CARE» says, without a heading, that photos and videos are digital mockups.

Then `seo.py to-drive <n>` **copies** the book's listing photos and video (`etsy/`) into `G:\My Drive\MoonMeadowStories\<n>.<slug>\` (`DRIVE`; the folder is made if missing). Copy, not move — the Workshop counts the slides in `etsy/`; nothing on the Drive is overwritten or deleted.

## Where the numbers come from

1. **The keyword database** `seo/data/seo.sqlite` (local, not in git): eRank «Shop tags» exports the owner supplies, and every eRank lookup the agent makes. Also local: `seo/data/inbox/` (what was read from eRank, as text), `seo/data/work/` (a book's candidate list).
2. **eRank in the browser pane** (Pro, signed in by the owner; the whole daily limit of 200 searches may be used, a bulk batch of 20 phrases costs 1). Three pages with fixed snippets in `seo/knowledge/erank-browser.md`: the Bulk Keyword Tool, the Keyword Tool's ideas (with trend) and Top Listings (competitors' titles, sales, 13 tags). Results pass through the agent as compact text because the browser pane blocks a page from sending data to this PC.
3. **The shop's own Etsy Stats → Search terms** (screens the owner sends; `import-own`, `own`): the strongest evidence. A phrase buyers already reach the shop by is marked ★ and ranked higher; tags holding the item noun count ×1.25 (`BOOK_NOUN_BONUS`).
4. **What is known about Etsy search:** `seo/knowledge/rules.md`, every rule with its evidence level (Etsy / eRank / practitioners / owner) and source.

Etsy itself is opened only as a visitor, never signed in ([security](../security.md)); the numbers come from eRank.

## Commands

All through `seo/seo.py` (the skill gives the exact line): `import-tagreport`, `import-erank`, `known`, `import-own`, `own`, `related`, `competitors`, `pick`, `lint`, `block`, `save`, `summary`, `to-drive`, `audit`.

- **`audit <listings.csv> --sales <items.csv>`** (Etsy's own exports) lists every listing's score next to its sales. A listing with at least `KEEP_SOLD` (3) sales is marked to keep and is never rewritten.
- **How a tag is judged** (`evaluate()`): demand is summed over the phrase's plural group (`group_key()`; eRank counts `gift` and `gifts` apart, Etsy matches both). Score = 45 % demand + 40 % low competition per search + 15 % CTR. A phrase eRank has never seen scores `UNSEEN_SCORE` (45) when it is exactly this book, up to 5 such tags per listing.
- **The picker** (`pick`) takes the best tag of every facet first, never two of one plural group, never a tag whose words all sit inside another chosen tag, at most 5 per facet; the agent then judges the result by hand.
- **The title check** (`lint`, `title_phrases()`) lists the exact buyer phrases inside the title with their demand and marks a phrase that forms across a comma (Etsy reads past punctuation): "…from Godparent, Gift for…" makes `godparent gift`.
- **The blocklist** `seo/knowledge/blocklist.tsv` keeps misleading phrases (`angel baby` means baby-loss on Etsy); `block` adds one.

## Limits

- eRank's numbers are Etsy-US 12-month averages; the shop's own search terms come only as screens (Etsy has no export there), so ratios compare terms with each other.
- eRank's pages change: the snippets then need fixing in `erank-browser.md`.
- eRank allows one session at a time.

## Why

- Long titles only, no short-title tests.
- No eRank data is not "bad": eRank cannot see under about 20 searches a month and has never seen a new phrase; such a phrase is judged by its competition.
- A listing that sells is never rewritten: the score does not predict sales.
- The agent never signs in to Etsy or eRank, changes eRank's settings, or presses «Sync Listings».

## Where in the code

- [seo/seo.py](../../seo/seo.py) — `evaluate()`, `group_key()`, `cmd_pick()`, `cmd_lint()`, `cmd_audit()`, `cmd_to_drive()`, `DRIVE`, `KEEP_SOLD`
- [.claude/skills/etsy-seo/SKILL.md](../../.claude/skills/etsy-seo/SKILL.md) — the agent's steps
- [seo/knowledge/](../../seo/knowledge/rules.md) — rules, eRank snippets, description template, blocklist; [seo/README.md](../../seo/README.md)

## Related

- [Workshop](workshop.md) · [Photo mockups](photo-mockups.md) · [Security](../security.md) · [Ideas](../owner/ideas.md)
