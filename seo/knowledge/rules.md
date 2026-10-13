# Etsy SEO rules for the shop (personalized children's books, US)

Researched 2026-10-09. Every rule carries its evidence level; when two rules disagree, the higher level
wins, and **the shop's own Etsy Stats will beat all of them** once they are collected (not yet — the owner,
2026-10-09).

| Level | Meaning |
|---|---|
| **E** | Etsy said it — read on etsy.com (the Seller Handbook) |
| **R** | eRank's documentation, or eRank's data checked by us |
| **P** | practitioners and tool vendors — opinion, no controlled test |
| **O** | the owner's decision or observation |
| **S** | **the shop's own Etsy Stats** — beats every other level |

## 0. What the shop's own Stats say (S) — 2026-10-10

Etsy Stats → Search terms (pages 1–4, 6–8 of 89; `seo.py own` lists them with eRank's numbers):

| Search term | Our visits | eRank searches/month | Visits per search |
|---|---|---|---|
| baptism book(s) | 24 | 107 | ~22 % |
| flower girl book | 22 | 238 | ~9 % |
| baptism gift girl | 22 | 1,252 | ~1.8 % |
| flower girl proposal | 12 | 1,273 | ~0.9 % |
| first birthday book | 4 | 487 | ~0.8 % |
| baby baptism gift | 5 | 928 | ~0.5 % |
| baptism gift boy | 4 | 1,236 | ~0.3 % |
| baptism gift(s) | 6 | 2,808 | ~0.2 % |

(The period is the one Stats showed; the ratios compare terms with each other, not absolutely.)

1. **"<occasion/theme> book" beats "<occasion> gift" by 10–100× in visits per search.** A buyer typing "book" wants
   exactly our product, and those phrases have far fewer competing listings (7–10 k vs 60–200 k). → Every
   listing needs its "<theme> book" phrases, in the title and the tags; `pick` gives tags with the item noun ×1.25.
2. **Phrases longer than 20 characters bring visits** — `baptism book personalized` 13, `personalized baptism book` 8,
   `personalized first birthday book` 7, `gifts for baby girls christening book` 3. No tag can hold them: they match
   through the **title** (and title + tags together). This supports the owner's long titles, and says block 1 of
   the title should read `Personalized <Theme/Occasion> Book…`.
3. **Terms eRank can't measure bring real visits** (`baptism book girl` 5, `baptism day book` 3, `personalized book
   for 2 year old boy planes` 2) — the owner's rule about unmeasured tags (§3) holds.
4. A big "gift" phrase still brings visits (`baptism gift girl` 22) — keep 2–4 head tags, but they are not where
   most of the traffic per search comes from.

### The shop's sales against the tool (2026-10-10, Aug 1 – Oct 9, 121 books, 31 listings)

The tool's score (made before the sales were compared, the code unchanged) did **not** predict sales: rank
correlation −0.42. Title length −0.49, measured tag demand −0.05, title's exact-phrase demand −0.34; tags with no
eRank numbers +0.30, tags our shop already gets visits from +0.25.

- **Mostly age:** every listing that sold since August is an old one; the high-scoring ones are books 24–33, made
  with this tool in Sept–Oct and days old. So this does not prove long titles or eRank demand hurt — it proves they
  **don't show** in sales yet, and that the score must never be read as "this listing is weak".
- **The best seller** (57 of 121: `Personalized Baptism Storybook: Custom Name Christian Keepsake for Child`, 72
  characters, $28.32) scores only 46: 8 of its tags have no eRank numbers — `baby baptism book`, `baptism storybook`,
  `baptism day book`… exactly the "<occasion> book" phrases §0 found. What sells is the theme (baptism, first birthday
  with a custom character, flower girl, ocean, airplane), its history and its pictures — not the score.
- **Rule: a listing that sells is not rewritten** (`audit --sales` marks every one with ≥ 3 sales). Its tags may get
  1–2 swaps of dead tags at most, one change at a time.
- **Long titles:** the owner's choice for new books stays (the competitors use them) — but the shop's own sales give
  **no support** for it so far. Look again when books 24–37 are 2+ months old (about mid-December 2026).

## 1. How Etsy search works (E)

- Two phases: **query matching**, then **ranking**. Matching takes "a holistic view of your listing —
  including title, tags, attributes, descriptions, first photo, reviews, and more". *How Etsy Search Works,
  26 Aug 2025.*
- "If those keywords are an **exact match** for the query, your listing may be ranked higher." *(same)*
- Ranking also uses: listing quality and **conversion** (views → purchases), customer service (review
  rating, message response, cases — last 3 months), shipping price (US), shop quality (icon, policies),
  Context Specific Ranking (each shopper's own habits). Etsy Ads, Etsy Plus and Star Seller do **not** move
  organic placement. *(same)*
- Recency: a new listing gets a small temporary boost (hours to days), a renewed one a smaller one; renewing
  to chase it "isn't an effective strategy". *(same)*
- Categories and attribute selections **act as tags**; plurals and root words are matched, so singular and
  plural tags are the same tag. *Keywords 101 (summary, not read verbatim).*
- Since Jan 2026 Etsy grades relevance with an LLM trained on human labels: *relevant / partially relevant /
  irrelevant*. Irrelevant keywords can only hurt. *Code as Craft, 16 Jan 2026 (summary).*

## 2. Titles

- **E (27 Apr 2026, "New Guidance for Listing Titles"):** state the item once, key traits first, "consider
  using less than 15 words", no gifting phrases unless essential, no repeated words. The *reason* Etsy
  gives is buyer confidence and scannability. The same article says the title "is still an important part of
  your listing and **can impact both search results** and buyer conversion" — it "doesn't need to do all
  the work". Etsy states **no penalty for length**; only irrelevant keyword stuffing hurts.
- **P:** no public controlled test either way. One sample of 218 real listings (ListifyAI, Aug 2026): median
  title 96 characters, a third longer than 130.
- **O — the shop's rule (2026-10-09): long titles only, 110–140 characters, no A/B tests.** The owner sees
  short titles index and rank worse, and the leading competitors in the niche all use long titles.

**How we write the long title ("phrase blocks")** — this is where the two views meet: every word earns its
place by being part of an *exact buyer phrase* (E: exact matches may rank higher), and nothing irrelevant
goes in (E: stuffing hurts):

1. 4–5 blocks separated by `, ` (commas, not `|`).
2. **Block 1** = what it is + how it's personalized + the main theme: `Personalized Truck Bedtime Book with
   Name`. The item noun (`book`/`storybook`) appears in block 1.
3. Blocks 2–5 = the strongest **exact** phrases buyers type for this book, by demand from the database:
   theme story, recipient (`Baby Boy`, `Toddler`, `Godchild`), occasion (`First Birthday`, `Baptism`,
   `Christmas Eve Box`), keepsake/format.
4. Words may be shared between neighbouring blocks only when that builds another real exact phrase
   (`First Christmas Gift` + `Christmas Eve Box`); otherwise no word twice.
5. Never: price, sale, shipping, "perfect/beautiful", a phrase that is untrue for this book, a blocked phrase.
6. Check: `seo.py lint` lists the exact phrases the title contains and their demand — more known demand
   inside the title is the goal.

## 3. Tags

- **E:** use all 13; up to 20 characters; multi-word phrases beat single words; don't spend tags on
  overlapping variants or on words the category/attributes already cover; plurals are matched (don't add
  both forms); no other languages (Etsy translates); no misspellings.
- **R (eRank):** long-tail phrases convert better; prefer relatively high searches, clicks and CTR and
  relatively low competition. eRank gives **no numeric thresholds** — ours below are our own.
- **Ours (scoring in `seo.py`):** demand = searches summed over the plural group; ratio = competition ÷
  demand; score = 45 % demand + 40 % low ratio + 15 % CTR.
- **O — no eRank data is not "bad" (the owner, 2026-10-09):** eRank shows nothing under 20 searches a month,
  and a phrase it has never seen may simply be new — we may be the first with this product or this
  combination; the shop's books sell on such tags. Many small queries add up (the long tail), and a phrase
  that describes the book exactly with few competing listings is where we can be on page one. So:
  an unmeasured tag (`< 20` / `Unknown`) scores 25–60 by how few listings compete; a phrase eRank has never
  seen scores 45 when it is exactly this book (A); up to **5** such tags go into a listing. Intuitive tags
  are welcome — mark them A in the candidates and say in the report they are unmeasured.
- **Mix:** 3–4 head tags (big demand even if crowded), 4–6 mid tags (demand ≥ ~150 with a good ratio),
  3–5 exact tags that describe this very book (theme words: `sleepy trucks book`, `godparent letter`).
- Cover different **buyer intents** (facets): product+theme, recipient, occasion, giver, keepsake/format.
- **O — each listing keeps its own angle (the owner, 2026-10-11, after weighing sharing tags):** two of the shop's books
  on the same theme don't get the same tag set; a tag that fits a book best may still be shared with one or two others
  (e.g. `christmas eve box`, `stocking stuffer`). P: sellers report Etsy limits how many listings of one shop a search
  page shows — not stated by Etsy, unverified.
- A tag must be true for the book (relevance A or B). Gender: only if the book's hero is that gender, or
  both (`… boy`, `… girl`) when the text is neutral.

## 4. Description

- **E:** the description is part of matching. **R:** put the main keywords at the beginning.
- The first sentence contains block 1 of the title in natural words. Template:
  [description-template.md](description-template.md). **Page count: "30-page"** (30 pages = 14 story
  spreads + dedication + afterword — the owner, 2026-10-04); never take a count from the book's files.

## 5. eRank numbers — how to read them (R, checked on our data)

- Etsy-US only, average per month over the past 12 months.
- `< 20` = eRank can't measure below 20 — **not zero** (we count it as 10). `Unknown` = no data.
- CTR over 100 % is normal (one shopper clicks several listings).
- **Competition** = number of listings matching the phrase.
- **KD** is only competition ÷ searches squeezed onto 0–100 (checked on 181 tags, rank correlation 1.0)
  and it is **100 for everything with a ratio above ~100** — useless at the top; we use the ratio itself.
- **Plurals:** eRank counts each spelling separately (`christening gift` < 20, `christening gifts` 1,387),
  while Etsy matches both — so we **sum the group**, else strong tags get thrown away.
- Google Searches column = Google's US volume, a side signal only.
- RankHero's numbers are on a different scale (for `godson gift` it showed 2,400/month, eRank 197) — never
  mix them with eRank's.

## 6. Seasons (P)

- List seasonal books **~3 months** before the peak (eRank: "Christmas" rises from September); changes
  need **4–8 weeks** to show. Christmas → by early October; Halloween → by July/August; Easter → by January;
  Mother's Day → by February; baptism/christening and first birthday are all-year.
- `seo.py known` shows a phrase's peak months when eRank's monthly history is in the database.

## 7. Never (E/O)

- Etsy is opened only as a visitor, never signed in ([security](../../wiki/security.md)); the demand numbers come from eRank.
- Never a phrase that misleads about the book: see the blocklist (`seo.py summary`, `block`). Reasons are
  kept with each entry (e.g. `angel baby` = baby-loss on Etsy).

## Sources

- How Etsy Search Works — etsy.com/seller-handbook/article/how-etsy-search-works/375461474487 (26 Aug 2025, read 2026-10-09)
- New Guidance for Listing Titles — etsy.com/seller-handbook/article/1399426136697 (27 Apr 2026, read 2026-10-09)
- Keywords 101 — etsy.com/seller-handbook/article/keywords-101-everything-you-need-to-know/382774281517 (summary)
- How Etsy Uses LLMs to Improve Search Relevance — etsy.com/codeascraft (16 Jan 2026, summary)
- eRank help: Tag Report, Bulk Keyword Tool, Listing Audit (hc.erank.com), CTR article (5 Dec 2024),
  tags article (29 Apr 2025), checklist (28 May 2025), holiday tips — help.erank.com/blog
- ListifyAI "State of Etsy SEO 2026" (Aug 2026) — the only title-length sample found
