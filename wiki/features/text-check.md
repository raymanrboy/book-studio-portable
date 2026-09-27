---
title: Text check (AI validator on a local model)
type: feature
updated: 2026-09-27
code:
  - app/studio/textcheck/
  - app/studio/wording.py
  - app/tests/test_textcheck.py
  - app/tools/textcheck_replay.py
  - app/studio/jobs.py
  - app/studio/images.py
---
# Text check

> The owner's "AI validator": as soon as the files from Canva are laid out in the order card, a local
> Gemma model (Ollama, this PC's graphics card) reads the text pages, and the program checks what was
> printed against what should be there: the book passport's texts with the child's name, the dedication,
> and the "from whom" from Etsy. The result shows in the "Proofing" step: a badge, a list of problems,
> marks on the pages. It never blocks printing — it only asks. Built on 2026-09-19.

## What the owner sees (the order card, step 2 "Proofing")

- The check **starts on its own** after a successful file check; proofing keeps working as usual in the
  meantime. A badge to the right of the heading: a spinner with a percentage → "Text matches" (green) /
  "N errors" (red) / "N questions" (yellow).
- **Findings appear while the check runs** (since 2026-09-20): every checked page adds its own rows to
  the list and outlines on the filmstrip right away, without waiting for the rest of the book. The first
  errors show up roughly 3–5 s before the check finishes; at the end the list is replaced with the full
  one (which also adds remarks about the whole book). The badge's tooltip: what it was checked against,
  how many pages have text, which passport spreads this book is missing (for 24- and 28-page books), how
  many seconds it took. Next to it — a ↻ "Check the text again".
- **The list of problems** under the heading: "Page 7 · "Ollivia" instead of "Olivia"" (words in
  quotation marks are bold), and under it, in gray, the model's explanation, in Ukrainian. Clicking a row
  opens the viewer on that spread; ✓ "Not an error" removes it (a deliberate edit; remembered as long as
  the card is kept) and **is written into that check's journal** (since 2026-09-25) — the next
  calibration is made on the owner's own answers ([Calibration](#calibration-2026-09-25)). **New files clear every such mark on this book, and replacing a single page clears
  the marks on that page only** (since 2026-09-20, the owner's request: otherwise a stray click would
  hide the same finding in the next print too). ↻ "Check again" on the same files keeps the marks.
- **Red** — certain: a leftover `{Name}`, a misspelled name / missing a diacritic / lowercase, another
  child's name, a difference from the passport's words that the model also confirmed. **Yellow** — worth
  a look: seen only by the model (a word cut off at the edge) or only by the comparison; edits on the
  first and last page (the owner adjusts those himself); "from whom" words or the buyer's own dedication
  that weren't found; a spread with no text; **a greeting or the "from whom" signature printed twice** on
  the first or last page ("Двічі «Dear Mia»", "Підпис «від кого» двічі" — since 2026-09-25).
- **"Це не та книга!"** (since 2026-09-25, the owner: "a big red message, a guard against a slip") — a
  big red banner at the top of "Proofing" when half the story spreads or more don't look like the ordered
  book's passport: the pages were laid out from another book's Canva template. It names the book the pages
  look like (with both covers: "Замовлено" / "А сторінки схожі на"), outlines every such page red, and the
  badge says "Не та книга". **"Print"** then asks "Це не та книга! Все одно до друку?" (still never
  blocked). "Це та книга" on the banner removes it (and is journaled like "Not an error"). While it's
  shown, "Update passport" is never offered — it would overwrite this book's passport with the other
  book's texts. See [Another book's pages](#another-books-pages-since-2026-09-25).
- Pages with problems are outlined red/yellow — in the big proof and in the filmstrip.
- In the viewer, the **T** key shows what the model read on the spread's pages, and what should have
  been there.
- **"Print"**: the check is still running → "Send without waiting?"; there are red items → "Print
  anyway?". Nothing is ever blocked.
- **"Update passport · N pages"** — when pages differ from the passport only in wording (no name or
  placeholder errors): "if that's really how the Canva template has it — the book passport is out of
  date". After confirming, these pages' texts (cover, spreads; not the dedication or afterword) become
  what was printed, the child's name becomes `{Name}` again, and the check runs once more. Needed
  because passport texts were written separately from the Canva templates — see "Tested on real books".
  - The confirmation window **shows the texts exactly as they'll be saved**, with `{Name}` highlighted
    (the server computes them ahead of time without saving anything — `preview`).
  - A name becomes `{Name}` **only as a whole word**, and only where the passport had `{Name}`
    (`as_template()` compares the print against the old passport text word for word): "Eve" doesn't
    touch "every", "Ian" doesn't touch "giant", and a name that's also an everyday word ("Hope"/"hope",
    "Grace"/"grace") stays a word wherever the passport had that word. In new lines the passport didn't
    know yet, such a name becomes `{Name}` only if it's capitalized. (The 2026-09-22 audit: before this,
    "Every" used to become "{Name}ry" and get saved that way.)
- **A light check** (a gray line under the list): the book isn't in the library, the passport has no
  texts, or the child's name wasn't found. Then it's only the program's own rules (placeholders, the
  name, other children's names) and the model's eye (cut-off text, stuck-together words, obvious typos).
- Ollama isn't running — the program starts it itself (as if from the Start menu); it fails, or the
  model is missing — a yellow banner "Text not checked: …" with a ↻.

## How it works (`textcheck/`)

The code is a package since 2026-09-27 (it was one 1 400-line file): `run.py` — one check (the passes, the cache,
stopping), `rules.py` — what the card shows, `texts.py` — words and which page is which text, `ollama.py` — the
model on this computer, `journal.py` — the journal and the owner's marks, `routes.py`. Every rule stayed as it was:
`textcheck_replay.py --all` gave the same output before and after.

0. **Warm-up** (`warm()`, since 2026-09-20): as soon as the card takes files (a drop, picking a folder,
   "take files from an earlier send"), the window asks `POST /api/textcheck/warm` — and the model
   loads onto the GPU while the server is still copying and checking the PNGs. The check that follows no
   longer waits for it to load (~4 s from memory, ~70 s from disk). Silent: warm-up errors show nowhere
   — the check itself will report them. Repeated requests within `WARM_AGAIN` (30 s), and requests made
   during a check, do nothing.
1. **Readiness** (`_ready()`): Ollama answers (otherwise `start_ollama()`), the model is installed, the
   model is loaded onto the GPU (the step "Loading the model…": ~4 s from the computer's memory, ~70 s
   from disk).
2. **A quick page scan by the program** (`page_kinds()` → `images.text_score()`, since 2026-09-20):
   before bothering the model, the program looks at every page's history itself — in the 360 px preview
   already made for the spread filmstrip, so it's ~5 ms per page. The signal is simple: **printed text
   is thin strokes gathered into a few narrow lines, while an illustration is spread evenly across the
   whole page** (`text_score()` = how unevenly the "ink" sits across the page's rows). A page gets one of
   three tags: `text` (≥ `LOOKS_TEXT` 2.2), `picture` (< `LOOKS_PICTURE` 1.6), or `unsure` — and **this
   tag alone decides nothing**: `unsure` still goes to the model, as before. The switch lives in Settings
   (`prescan`); turned off, the check runs exactly as it did before 2026-09-20.
3. **Reading** (`READ_PROMPT`, blind, only the first lines — `READ_TOKENS`): **only the pages that might
   have text**, and the back of the cover. A spread where exactly one page is tagged `text` and the
   other `picture`, and for which the book passport says what should be there, **isn't read at all** —
   it goes straight to checking against the ready-made reference (in a 30-page book where the spreads
   line up with the passport, reading disappears entirely). A spread that looks completely blank is
   still read by the model — so that "no text" is the model's own verdict, not the tag's. `has_text()`
   throws out "I'm sorry, I cannot transcribe…" and 1–3 word answers — this is how the model reacts to
   decorative "pseudo-writing" in illustrations (where it also tends to invent text and loop).
   **If the tag was wrong** and the model saw no writing at all on a page sent straight to checking, the
   other half of the spread is checked instead (`_second_half()`), and that's what goes into the result.
4. **Which page is which passport text** (`assign()`): in a full book (30 pages) — by position: spread
   *k* = passport spread *k+1*, on whichever page carries the text (the one more similar to the
   passport's text). In 24/28-page books some spreads are missing, but the order stays the same — the
   best order-preserving match (first lines' `similarity()` ≥ `MATCH`); anything not found is `skipped`.
5. **Checking** (`STRICT_PROMPT` with the expected text; `LOOSE_PROMPT` without it): the cover (right,
   front half), page 1, the last page, every page with text. The model transcribes the page word for
   word and gives a verdict (JSON `SCHEMA`, no longer than `JUDGE_TOKENS`); 4 pages at once (`PARALLEL`).
   **A spread goes to checking as soon as its two pages have been read** (since 2026-09-20): in a book
   as long as or longer than the passport (30 pages), every spread stands on its own, so nothing else
   needs to be known. A shorter book (24 or 28 pages) is missing some spreads and only keeps their
   order, so its matching (`assign()`) needs every reading first — there, checking still starts only
   after reading finishes, as before. The reading queue is kept short (`PARALLEL + 2` pages ahead), or
   checking would wait behind the whole book. Answers are collected as they're ready (`_collect()`), and
   each one adds its findings to `job.share()` — that's where the card picks them up.
6. **The summary** (`page_issues()`, `book_issues()`): a word-for-word comparison (`diff()`: quotes,
   dashes, punctuation — not a difference; design capitals (`OLIVIA`) — not a difference; diacritics —
   strict) and the program's own rules (`findings()`): `{…}`, a misspelled name (1–2 letters off, the
   same first letter; ordinary words and passport words aren't a name, `COMMON`, `_vocabulary()`), a
   word stuck to the name, another order's child's name (`_other_children()`). Model remarks about
   punctuation only are dropped (`_only_punctuation()`): the model answers `only_punctuation` itself (in
   `SCHEMA`), and the wording of its explanation is only read when that answer is missing; a cut-off or
   stuck-together word always shows. Tested on Gemma 4 12B on made-up pages, 2026-09-23: a comma and
   quotes → `true`, a line cut off at the edge → `false`. The "custom text vs. DEFAULT" rule and name
   cleanup (`"Leo."` → `Leo`, `Leo's` → `Leo` since 2026-09-25) live in `wording.py`, shared with
   the order card.
   **Since the 2026-09-25 calibration** also: a difference only in capitals of the story's own words
   (`love`/`Love`, `Savior`/`savior`) isn't shown (`_case_only()`; the child's name in small letters is
   still the red rule — before, the name filled into the expected text counted as "a word of the page"
   and fell to the comparison's yellow); a model remark that itself says there's no mistake
   (`_NO_PROBLEM`) or only talks about where a line breaks isn't shown; on the first/last page with the
   buyer's own message, when the program finds every word of it on the page (`_buyer_intact()`), the
   model's "a word is missing / changed" isn't shown (it "corrected" a Bible verse quoted the buyer's
   way) — a cut-off or repeated line still is; the first/last page is searched for things said twice
   (`_twice()`).
7. The expected text: `fill()` — `{Name}` → the name, `{Gifter}` → "from whom"; if "from whom" starts
   with its own "With love…", the template's "With love," line before it is dropped.
   `personalization()`: a name without a trailing period ("Leo & Mila."), "from whom" without quotes or
   a space before the comma; `DEFAULT` in any spelling (`is_default()`); the buyer's own dedication is
   split into "Dedication:" / "Closing:".
8. The model's answers are cached in memory by the page's **content** (`_digest()`) and the prompt: re-checking
   the same files is instant; after fixing one page, only that page is re-checked — also when the book is dropped
   again into a new folder (since 2026-09-26; the key was the file's place, and every drop is a new place). The
   model is loaded only when a question isn't in the cache (`_Run.ready()`): a re-check answered from memory needs
   no model at all (it used to load 9 GB into the graphics card, ~4 s or ~70 s, for nothing). A page read and then
   judged is made into a JPEG once (`_Run.picture()`). The card warms the model after a page is replaced too
   (`revalidate()`). A broken answer (cut off, not JSON)
   is not kept, so ↻ asks that page again; a call that timed out (`TimedOut`, 300 s) is not tried a second time
   — one hung page held a whole check ~10 minutes (both since the 2026-09-26 audit). A newer check of the same
   order stops the previous one; the card stops its own check (`cancel()`) when it's closed, other files
   are dropped, or another book is picked (since 2026-09-19). A hidden card (switched to another tab)
   doesn't stop it. Every call to the model runs inside `_Run` (4 at a time, a counter for the
   percentage, and a stop signal).
9. **The GPU is freed right away** after the last check finishes (`_release_model()`): the model takes
   ~9.2 GB of 12, and Book Studio's own window is drawn by the same card (code review, 2026-09-19 —
   [open-questions](../plans/open-questions.md)). The next check loads it again in ~4 s. `KEEP_ALIVE`
   (2 min) is only a fallback. A smaller `num_ctx` (4096) didn't save memory — left unchanged. The cover
   for the model comes from the same 1400 px preview proofing uses (no separate 4000 px decode).
10. **Journal** — `data/logs/checks/<date>_<receipt>-<book number>.json` (what the model read, what
   should have been there, problems; the last 400). The book number is in the file name so two books of
   one receipt that finish their check within the same second don't write to the same file. Local only,
   never goes into git. Since 2026-09-25 each page also keeps the model's own answer (`model`: verdict,
   problems, `onlyPunctuation` — before the program chose what to show, `_raw()`), plus `layout` (unmatched
   and blank spreads) and `notMistakes` — what the owner marked "Not an error" (`mark()`, route
   `POST /api/textcheck/mark`; the card sends the journal's name it got in the result, `journal`).

### Every book of an order is checked separately (since 2026-09-22)

A check belongs to the **book**, not the receipt: the key is `receipt#book number` (`run_key()`).
Starting a check on the second book no longer breaks the first one with "Check interrupted" — that's
exactly the promise the card makes ("a hidden book's text check keeps finishing on its own"), and the
code used to do the opposite before 2026-09-22 (found by the audit). A new check of **the same** book
still cancels the previous one, as before; closing the whole card (`cancel()` with no job number) stops
every book of that receipt.

### Another book's pages (since 2026-09-25)

On 2026-09-21 the owner laid out one child's book from the Canva template of the **other book of the same
order**; the check caught it, but as eleven yellow "text like no passport text" rows plus the model's
"another name — Jacob" (biblical characters). The owner asked for a guard nobody can miss.
- **When**: the story spreads unlike the passport — no passport text found on them (`unmatched`, 24/28-page
  books), or "another text altogether" on a page matched by position (30-page books) — are **half of the
  book's story spreads or more** (at least 3) (`_strange()`, `_wrong_book()`). A drifted passport differs in
  a word or a line, not in whole pages.
- **What**: one red finding (`kind: "book"`, `_one_alarm()`) instead of those pages' rows; the program's own
  name rules on them stay (another child's name is still worth its row). `like` — the library book the
  pages start like (`_like_book()`: the pages' first words against every other book's passport).
- **At once**: in a 24/28-page book the unmatched spreads are known after the read pass, so the alarm comes
  with the first checked page (`_collect()` applies it to what it shares); in a 30-page book — as soon as
  half the spreads are checked.
- **Never teaches the passport** (`_learnable()` returns nothing while it's there).
- The card: the banner (`wrongBook()`), the badge, all such pages outlined, the print question.
- Light checks (no passport texts) aren't guarded: two library books may share a story (the Boys/Girls
  versions), and a match to another book's passport would say nothing.

## Calibration (2026-09-25)

> The owner (2026-09-25): once there are more cases, calibrate "the machine validator that decides what
> to show me in errors and what not" — the program's rules, not Gemma.

- **The data**: the check journal — 30 checks, 10 different orders (the rest re-checks of the same
  files), 103 rows shown, 69 red. "Not an error" clicks weren't recorded then, so who was right was
  read from what the owner fixed between re-checks.
- **Real catches — 4, all fixed by the owner afterwards**: "With love," printed twice (one order);
  "Dear <name>" twice and the signature twice (another); a book laid out from the other book's template
  (a third).
- **The noise**: a buyer typed the name with a possessive "'s" — every page red "<name> instead of <name>'s", 52 of
  the 69 red rows; capitals of the template's words; the model contradicting itself ("no mistake, full
  match") on a cover; the model "correcting" a Bible verse the buyer quoted their way; eleven rows plus
  biblical names for the wrong-template book; a remark about a line break. And the First Bible Stories
  passport had drifted from Canva in three words ("Noah **to** build", "David was…" without "Young",
  "Savior") — red on every order of that book; updated that day by the agent (the owner's "do as you see
  fit"; the three words only, a copy of the old `book.json` kept as its `.bak`).
- **What changed** — see step 6 above, [Another book's pages](#another-books-pages-since-2026-09-25), the
  journal (step 10). One catch the model had missed (the signature kept twice, on that order's second check) is now
  the program's own rule.
- **Result on the same 30 checks** (`app/tools/textcheck_replay.py`): 103 rows → 12, red 69 → 3 — the three
  are the real wrong-template book. All 4 real catches stay. Of the 12, four are the model's old words
  about the name with "'s" that it wouldn't say with the right name in its prompt.
- **Next calibration**: `python app/tools/textcheck_replay.py` shows what the current rules would show
  for every journaled check, next to what was shown then, with the owner's "Not an error" marks; `--all`
  — every check. The model isn't asked again; journals before 2026-09-25 keep only what was shown of its
  verdicts.

## Settings

The "Text check" block in [Settings](settings.md): a switch, a **quick page-scan switch** (`prescan`), a
model (from those installed in Ollama that can see pictures), Ollama's status, "Start", "Check
connection". In `settings.json` — a `textcheck` section (`enabled`, `prescan`, `model`, `url`); the
address is **127.0.0.1 only** (`_base()`), so pages with children's names never leave the computer. The
model frees the GPU right after a check — for both Book Studio's own window and Upscayl. A disabled
Ollama: every connection attempt waits 2 s on Windows, so the "is it alive" check is capped at 1 s
(`PROBE_TIMEOUT`), and the block in Settings is drawn right away, with the status caught up afterward.

## The quick page scan — measured (2026-09-20)

**How well the signal tells text apart from a picture.** Run against all five real books in the archive
(4 different books, 30 and 24 pages): a page with text scores **2.4–2.6**, a picture-only page scores
**0.9–1.5**. On two books with a check journal (so it's known what the model itself found), the list of
text pages **matched exactly**. On one book (with chapter headings on "picture" pages), the signal was
more cautious: 7 pages landed in `unsure` and went to the model, as before.

**What this gains** (the real Gemma, the same books, before and after):

| Book | Before | After | Page reads |
|---|---|---|---|
| 30 pages, plain | 39.7 s | **24.4 s** | 29 → 1 (only the back of the cover) |
| 30 pages, complex (headings) | 40.3 s | **30.9 s** | 29 → 15 |
| 24 pages, Printify | 44.8 s | **33.6 s** | 27 → 12 |

The problems found in all three books are **identical before and after** (in the 24-page book — the same
4).

## Tested on real books (2026-09-19, gemma4:12b-it-qat, RTX 4070 SUPER)

The order archive — three books already sent to print (Gelato, 30 pages, 4000 px):
- **Baptism Storybook** (dedication DEFAULT): all 14 spreads found, **0 problems**, ~39 s.
- **Airplane Bedtime**: the only red one — the cover: Canva says "Sweet Dreams dear {Name}", the
  passport says "Sweet Dreams, Little Planes for {Name}". A real mismatch between the passport and the
  template.
- **First Bible Stories**: the passport has chapter headings ("Genesis 1"…) that aren't on the pages; a
  few words ("to build", "Savior"); the last two spreads are in a different order in Canva than in the
  passport. All of it is a passport mismatch, not an order mistake. This is why the "Update passport"
  button exists.
- After "Update passport" (on a data copy): First Bible Stories — 0 red items, the re-check took 23 s;
  Airplane — clean in 1.5 s (only the changed page is re-read from the cache).
- **Planted mistakes**: a 24-page book was assembled from Baptism Storybook (without spreads 5, 9, 12,
  as for Printify), three text pages were rewritten over a blurred copy of the real illustration: a name
  with an extra letter, the word "calm" missing, a forgotten `{Name}`, and one with no mistakes at all.
  Result: the missing spreads 5, 9, 12 were identified correctly, **all three mistakes were flagged
  red**, and across the 20 other real pages and the rewritten clean one — **not a single false alarm**,
  34 s.
- The first run took 11 minutes: on picture-only pages the model kept inventing text and looping. This
  is why `has_text()` exists, why the full check only compares passport pages, and why `JUDGE_TOKENS`
  exists.

## Where in the code

- [app/studio/textcheck/rules.py](../../app/studio/textcheck/rules.py) — calibration and the wrong-book guard: `_case_only()`, `_buyer_intact()`, `_twice()`, `_strange()`, `_wrong_book()`, `_one_alarm()`, `_like_book()`, `WRONG_BOOK`, `_NO_PROBLEM`, `_CLAIM`, `_SEEN`
- [app/studio/textcheck/run.py](../../app/studio/textcheck/run.py) — `check_order()`, `check_book()`, `_passes()`, `page_kinds()`, `_page_score()`, `_second_half()`, `_collect()`, `_targets()`, `_print_files()`, `_Run`, `run_key()`, `cancel()`, `warm()`, `picture()`, `_other_children()`, `READ_PROMPT`, `STRICT_PROMPT`, `LOOSE_PROMPT`, `SCHEMA`, `PARALLEL`, `IMAGE_SIDE`, `READ_TOKENS`, `JUDGE_TOKENS`, `WARM_AGAIN`, `LOOKS_TEXT`, `LOOKS_PICTURE`
- [app/studio/textcheck/rules.py](../../app/studio/textcheck/rules.py) — `_saw_nothing()`, `_ordered()`, `_all_issues()`, `_learnable()`, `findings()`, `page_issues()`, `book_issues()`, `has_text()`, `_vocabulary()`, `_only_punctuation()`
- [app/studio/textcheck/ollama.py](../../app/studio/textcheck/ollama.py) — `_release_model()`, `status()`, `start_ollama()`, `_ready()`, `_names()`, `_has()`, `_chat()`, `TimedOut`, `_base()`, `KEEP_ALIVE`, `DEFAULT_MODEL`, `PROBE_TIMEOUT`
- [app/studio/textcheck/routes.py](../../app/studio/textcheck/routes.py) — `_cancel()`, `_warm()`, `as_template()`, `_passport()`, `_passport_texts()`, `_passport_words()`, `_check()`, `_mark()`
- [app/studio/textcheck/texts.py](../../app/studio/textcheck/texts.py) — `assign()`, `similarity()`, `diff()`, `personalization()`, `fill()`, `MATCH`, `COMMON`
- [app/studio/textcheck/journal.py](../../app/studio/textcheck/journal.py) — `_journal()`, `CHECKS`, `_raw()`, `mark()` (the owner's «це не помилка» marks)
- [app/studio/wording.py](../../app/studio/wording.py) — `words()`, `is_default()`, `clean_name()`, `custom_text()`, `alike()`, `guess_child_name()`, `DEDICATION`, `META`, `_POSSESSIVE`
- [app/tools/textcheck_replay.py](../../app/tools/textcheck_replay.py) — `replay()`, `rebuild()`, `main()` (the journal through today's rules)
- [app/studio/images.py](../../app/studio/images.py) — `text_score()`, `_percentile()`, `TEXT_SIDE`
- [app/studio/jobs.py](../../app/studio/jobs.py) — `Job.share()` (findings ready before the whole check is)
- [app/web/js/pages/order-card.js](../../app/web/js/pages/order-card.js) — `startCheck()`, `warmModel()`, `checkBadge()`, `checkBody()`, `issueRow()`, `checkTip()`, `markPages()`, `paintCheck()`, `readings()`, `learnable()`, `learnPassport()`, `dropCheck()`, `print()`, `alarmOf()`, `wrongBook()`, `findingsHtml()`, `keepMark()`, `LEVEL_WORDS`, `LIGHT_TIP`
- [app/web/js/pages/settings.js](../../app/web/js/pages/settings.js) — `textcheckCard()`, `loadTextcheck()`, `saveTextcheck()`
- [app/web/css/orders.css](../../app/web/css/orders.css) — `.tc-list`, `.tc-issue`, `.tc-where`, `.tc-note`, `.tc-light`, `.tc-error`, `.tc-warn`, `.v-badge.warn`, `.tc-passport`, `.tc-slot`, `.tc-alarm`, `.tc-alarm-head`, `.tc-alarm-books`, `.tc-alarm-book`, `.tc-alarm-dismiss`
- [app/studio/core.py](../../app/studio/core.py) — `DEFAULT_SETTINGS` (`textcheck`)
- Tests: [app/tests/test_textcheck.py](../../app/tests/test_textcheck.py) — the model is faked; the real Ollama isn't needed

## Related

- [Orders](orders.md) · [The path to print](../flows/order-to-print.md) · [Library](library.md) · [Settings](settings.md)
- [Model research and tests](../plans/roadmap.md) · [Decisions](../decisions.md) · [Security](../security.md)
