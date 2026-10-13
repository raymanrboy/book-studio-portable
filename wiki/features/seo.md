---
title: Etsy SEO studio — a book's title, tags and description
type: feature
updated: 2026-10-11
code:
  - seo/seo.py
  - seo/README.md
  - seo/knowledge/rules.md
  - seo/knowledge/erank-browser.md
  - seo/knowledge/description-template.md
  - seo/knowledge/blocklist.tsv
  - .claude/skills/etsy-seo/SKILL.md
---
# Etsy SEO studio

> The owner asked (2026-10-09) for "an ultimate tool" for his listings' SEO, used through Claude Code. It is not part
> of the program's interface: the agent runs it on the owner's words («зроби SEO для 35», `/etsy-seo 35`).

## What it does

For a Workshop book, the agent writes into `pipeline/books/<n>.<slug>/agent/listing-seo.md`:

- **a long title** (110–140 characters, "phrase blocks": every block is a phrase buyers really type) — the owner's
  rule, no short titles;
- **13 tags**, chosen by numbers and by buyer intent (product, theme, recipient, occasion, giver, keepsake);
- **the description** — the owner's template, only the parts about the book change; always "30-page".

Then (the owner, 2026-10-11) `seo.py to-drive <n>` **copies** the book's listing photos and video (`pipeline/books/<n>.<slug>/etsy/`)
into his Google Drive, `G:\My Drive\MoonMeadowStories\<n>.<slug>\` — the folder is made if missing. Copy, not move: the
Workshop counts the slides in `etsy/`. Nothing on the Drive is overwritten or deleted.

Where the numbers come from:

1. **The keyword database** `seo/data/seo.sqlite` (local, not in git): the eRank «Shop tags» exports the owner gives
   (4 competitor shops on 2026-10-09), the old `seo-intelligence` competitor listings (copied once), and every eRank
   lookup the agent makes.
2. **eRank in the browser pane** — the owner is signed in there (Pro, 200 searches a day; he allows the whole limit).
   The agent reads three pages with fixed snippets ([`seo/knowledge/erank-browser.md`](../../seo/knowledge/erank-browser.md)):
   the Bulk Keyword Tool (20 phrases for 1 search), the Keyword Tool's ideas (with 15 months of trend) and the
   Top Listings (competitors' titles, sales and 13 tags).
3. **The shop's own Etsy Stats → Search terms** (the owner's screens, 2026-10-10; `seo.py import-own`, `own`) — the
   strongest evidence: a phrase buyers already reach us by is marked ★ and ranked higher. They showed that
   "<occasion> book" phrases bring 10–100× more visits per search than "<occasion> gift" ones, and that phrases longer
   than 20 characters (only the title can hold them) bring visits — so tags with the item noun count ×1.25.
4. **What is known about Etsy search** — [`seo/knowledge/rules.md`](../../seo/knowledge/rules.md), every rule with
   its evidence level (Etsy / eRank / practitioners / the owner) and source.

**Etsy is opened only as a visitor, never signed in** (since 2026-10-11, [security](../security.md)); the numbers come from eRank.

## Checking the whole shop

`seo.py audit <listings.csv> --sales <order items.csv>...` (Etsy's own exports): every listing's score next to its sales.
On 2026-10-10 the score did **not** predict sales — the sellers are the old listings, the best one has a short title and
tags eRank can't measure — so a listing that sells (≥ 3, `KEEP_SOLD`) is marked to keep and is never rewritten.

## How a tag is judged

- Demand is summed over the phrase's **plural group** (eRank counts `christening gift` and `christening gifts` apart,
  Etsy matches both).
- Score = 45 % demand + 40 % low competition per search + 15 % CTR.
- **No eRank data is not "bad"** (the owner): eRank can't see under 20 searches a month and has never seen a new
  phrase; an exact phrase with few competing listings is judged by its competition (25–60), a phrase eRank has
  never seen gets 45 when it is exactly this book; up to 5 such tags per listing.
- The picker takes the best tag of every facet first, never two of one plural group, never a tag whose words all
  sit inside another chosen tag, at most 5 per facet. The agent then judges the result by hand.
- **The title's check** lists the exact buyer phrases inside it with their demand, and marks a phrase that forms
  **across a comma** (Etsy reads past punctuation) — e.g. "…from Godparent, Gift for…" makes `godparent gift`,
  a buyer looking for a gift *for* a godparent.
- The blocklist (`seo/knowledge/blocklist.tsv`) keeps phrases that would mislead (`angel baby` = baby-loss on Etsy).

## Where in the code

- [seo/seo.py](../../seo/seo.py) — the database and every command: `import-tagreport` (`cmd_import_tagreport()`),
  `import-legacy`, `import-erank` (`parse_compact()`, `import_payload()`), `known` (`evaluate()`, `group_key()`),
  `import-own`, `own` (`cmd_import_own()`), `related`, `competitors`, `pick` (`cmd_pick()`), `lint` (`cmd_lint()`, `title_phrases()`), `block` (`blocked()`),
  `save`, `summary`, `to-drive` (`cmd_to_drive()`, `_numbered()`).
- [.claude/skills/etsy-seo/SKILL.md](../../.claude/skills/etsy-seo/SKILL.md) — the agent's steps: brief → candidates →
  numbers → tags → title → description → save, copy to Google Drive, report.
- Data: `seo/data/seo.sqlite`, `seo/data/inbox/` (what was read from eRank, as text), `seo/data/work/` (a book's
  candidate list) — all local.

## Known limits

- eRank's numbers are Etsy-US 12-month averages. The shop's own search terms come only as screens (Etsy has no export there,
  89 pages — the owner sends the top ones); there is no Etsy Stats period in them, so the ratios compare terms with each other.
- The eRank pages may change (they were redesigned in December 2025): the snippets then need fixing in
  `erank-browser.md`.
- The browser pane blocks a page from sending data to this PC (`ERR_BLOCKED_BY_CLIENT`), so eRank results pass
  through the agent as compact text.
