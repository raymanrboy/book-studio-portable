---
name: etsy-seo
description: Make the Etsy SEO of a Workshop book — the long title, 13 tags and the description — from the book's own files, the shop's keyword database (seo/) and live eRank numbers read in the browser pane. Use when the owner asks for SEO, tags, a title or a description for a book or listing («зроби SEO», «теги для 34», «назва лістингу», «опис лістингу», «/etsy-seo 35»), or to add competitor data / eRank exports to the SEO database.
---

# Etsy SEO for a book

Reply to the owner in Ukrainian, plain words. The listing itself (title, tags, description) is in English.
Run Python from the repository root: `../runtime/python/python.exe seo/seo.py …` with `PYTHONIOENCODING=utf-8`.

**Read first (once per session):** [`seo/knowledge/rules.md`](../../../seo/knowledge/rules.md) — what is
known, with evidence levels. The browser steps: [`seo/knowledge/erank-browser.md`](../../../seo/knowledge/erank-browser.md).

**Hard limits:**
- **Etsy: visitor only** — etsy.com may be opened (not signed in) to look at listings and shops; never sign in to the owner's
  Etsy ([wiki/security.md](../../../wiki/security.md)). The numbers still come from eRank; in eRank never sign in/out, change
  its settings or press «Sync Listings».
- eRank budget: the owner allows the whole daily limit (Pro, 200 searches; a Bulk batch of 20 phrases costs 1).
  Say in the report how many were used.
- The page count in a **new** book's description is always **30-page**; never a count taken from the book's files.
  An **existing** listing keeps the count its current description says (books 1–23 are 24-page) — the owner never
  wants a listing's page count changed.
- Titles are **long** (110–140 characters, phrase blocks) — the owner's rule, no short-title tests.
- Nothing untrue about the book; nothing from the blocklist.

## 1. The brief

Find the book: `ls pipeline/books` → the folder whose number/name the owner gave. Read
`agent/input.md` and `agent/book-text.md` (stop at "Text Critic Report"). Write down:

- **What it is** — the item noun buyers use (`book`, `storybook`, `bedtime book`, `prayer book`).
- **Theme and motifs** — the words a buyer would search (trucks, ships, dinosaurs, nativity, angel…) and the
  concrete things in it (a fire truck, a T-rex, the star of Bethlehem).
- **Occasion(s)** the book is made for — from the dedication's default wording first (`On your very first
  birthday` → first birthday), then input.md.
- **Recipient and gender** — Tier H with a boy hero → boy; Tier S / neutral text → boy and girl.
- **Giver** — godparents, grandparents… when the book is made for them (a godparent book).
- **Season** — Christmas, Halloween, Easter, or none; check today's date against rules.md §6 and say if it's late.
- **Cover** — does the cover title hold `{Name}`? (decides "on the cover" in the description.)

## 2. Candidates (40–70 phrases)

1. What the database already knows:
   ```
   seo.py own                             the shop's own search terms (★ = buyers already reach us by them)
   seo.py related <theme word>            e.g. related truck · related bedtime · related godparent
   seo.py related book <occasion word>    e.g. related book christmas
   seo.py competitors <theme word>        competitor titles + their tags, weighted by daily views
   ```
2. eRank, in the browser pane (procedure and snippets — erank-browser.md):
   - **Keyword Tool → Ideas** for 2–4 seeds: `<theme> book`, `<occasion> gift`, `<recipient> gift`
     (e.g. `dinosaur book`, `godparent gift`). Save each JSON to `seo/data/inbox/`, `import-erank` it.
   - **Top Listings** for the 1–2 seeds closest to the product, `import-erank`, then `competitors` again.
3. Write `seo/data/work/<book-folder>.tsv` — one phrase per line: `phrase<TAB>A|B|C<TAB>facet`
   - relevance: **A** = exactly this book, **B** = true but broader, **C** = untrue/misleading (kept only as a
     record of what was rejected);
   - facet: `product`, `theme`, `recipient`, `occasion`, `giver`, `keepsake`, `season`;
   - phrases up to 20 characters can be tags; longer ones are title material only (keep them, mark `title`).
   - Add the plural spelling next to every strong singular (and the other way round): eRank counts them
     apart, Etsy matches both — the database sums them.

## 3. Numbers for everything

```
seo.py known --file seo/data/work/<book>.tsv
```
It prints the numbers it has and a **NEED eRank lookup** list already cut into batches of 20. Run each
batch through the **Bulk Keyword Tool**, save, `import-erank`, and run `known` again until the list is
empty (or only phrases eRank answered `Unknown` remain).

## 4. Tags

```
seo.py pick seo/data/work/<book>.tsv
```
It takes the best tag of every facet, then fills to 13 by score, never two of one plural group, never
two near-duplicates, at most 3 tags without measured demand. **Then judge it yourself**: swap a pick when a
"next best" phrase says the book better, keep 3–4 head tags, 6–7 mid, 2–3 exact-niche (rules.md §3).

## 5. Title

Build 2–3 phrase-block titles (rules.md §2) from the strongest A-phrases — including those longer than 20
characters — and compare:
```
seo.py lint --title "<title>" --tags "<13 tags, comma separated>"
```
Prefer the one with more known demand under "Exact buyer phrases inside the title", then the one that
reads better. It must end **READY** (no errors). Warnings about length < 110 mean: add a block.

## 6. Description

Fill [`seo/knowledge/description-template.md`](../../../seo/knowledge/description-template.md): change only
the `{…}` parts, from the book's text and input.md. "30-page". First sentence = title block 1 in natural words.

## 7. Save and report

1. Write `pipeline/books/<n>.<slug>/agent/listing-seo.md` (the agent's folder — the Workshop never reads it):
   ```
   # SEO — <book>   (date)
   ## Title            (one code block)
   ## Tags             (one code block, comma separated — ready to paste)
   ## Description      (one code block)
   ## Why              table: tag · demand · competition · ratio · facet; the title's exact phrases
   ## Notes            season timing, what was not measured, eRank searches used
   ```
2. `seo.py save <n>.<slug> --title "…" --tags "…"` — the database remembers what went into the listing.
3. `seo.py to-drive <n>` — the owner's rule (2026-10-11): the book's listing photos and video go into his Google Drive,
   `G:\My Drive\MoonMeadowStories\<n>.<slug>\` (made if missing; an existing folder of that number is used). It
   **copies** `pipeline/books/<n>.<slug>/etsy/` — never moves (the Workshop counts the slides there), never overwrites or
   deletes; a file of the same name with a different size is left as is and named in the output — tell the owner.
   If `etsy/` is empty (mockups and slides not made yet), say so and skip it. Say in the report how many were copied.
4. Reply in Ukrainian: the title, the tags, the description (each in its own code block, ready to paste),
   then 3–6 short lines of why, what could not be measured, and the eRank searches used.

## Checking the whole shop

`seo.py audit <EtsyListingsDownload.csv> --sales <EtsySoldOrderItems…csv>...` — every listing with its score and sold
count; `--missing` first lists the tags to look up in eRank. **A listing marked SELLING is never rewritten** — the
score is not a verdict on it (rules.md §0: the best seller scores low). Etsy's export writes tags with `_` for spaces;
the audit reads them right. The sales files hold buyers' names and addresses: read them only through `audit`,
never copy them anywhere.

## Reworking an old listing

Only one that does **not** sell (`audit --sales`; never a SELLING one). Its book lives in
`G:\My Drive\MoonMeadowStories\<n>.<slug>\` (images only; the folder № = the order the listings were made); read what
it is from its current description in the listings CSV. Give it its **own angle** — not the tags of a selling listing
of the same theme (they then compete for the same searches; on 2026-10-10 the «Nature & Animals» baptism listing had the
best seller's tags word for word). Change the title and tags; leave the description (its page count) unless the owner
asks. `save old-<n>-<slug> … --note "old: <old title>"` keeps the date of the change for the check 4–6 weeks later.

## Adding data the owner sends

- **The shop's own Etsy Stats → Search terms** (screens; the owner copies them on the Kyiv PC): type them into a TSV
  `term<TAB>visits` in `seo/data/inbox/`, then `seo.py import-own <file> --period "<as shown>"`. `seo.py own` lists them
  with eRank's numbers; `known`, `pick` and `lint` mark every phrase our shop already gets visits from (★) and
  `pick` ranks it higher. This is the strongest evidence there is (rules.md §0).

- eRank «Shop tags» CSV exports (any shop, duplicates are skipped by content):
  `seo.py import-tagreport "<path>"... --date YYYY-MM-DD`
- Screenshots of eRank tables: don't type numbers by eye — look the same phrases up with the Bulk tool.
- A phrase that must never be used: `seo.py block "<phrase>" --reason "<why>"` (`--contains` for every
  phrase holding it); lasting ones also go into `seo/knowledge/blocklist.tsv`.
- A new finding about how Etsy/eRank work → `seo/knowledge/rules.md`, with its evidence level, source and date.
