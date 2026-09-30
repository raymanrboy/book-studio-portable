---
title: Text check (AI validator on a local model)
type: feature
updated: 2026-09-30
code:
  - app/studio/textcheck/
  - app/studio/wording.py
  - app/tests/test_textcheck.py
  - app/tools/textcheck_replay.py
  - app/studio/jobs.py
  - app/studio/images.py
---
# Text check

> The owner's "AI validator": once the files from Canva are laid out in the order card, a local Gemma model (Ollama,
> this PC's graphics card) reads the text pages, and the program checks what was printed against what should be there:
> the book passport's texts with the child's name, the dedication, the "from whom" from Etsy. The result is in the
> «Вичитка» step — a badge, a list of problems, marks on the pages. **It never blocks printing — it only asks.**

## What the owner sees (the order card, step 3 «Вичитка»; «Звірка» until 2026-09-30)

- **Starts on its own** after a successful file check. The badge beside the heading: a spinner with a percentage →
  "Text matches" (green) / "N errors" (red) / "N questions" (yellow); its tooltip — what it was checked against, the
  pages with text, the passport spreads this book lacks (24/28 pages), the seconds. ↻ — "Check the text again".
- **Findings appear while it runs**: each checked page adds its rows and outlines at once; at the end the full list
  replaces them (with the remarks about the whole book).
- **The list**: "Page 7 · "Ollivia" instead of "Olivia"", the model's explanation under it in grey, in Ukrainian. A
  click opens the viewer on that spread; ✓ "Not an error" hides it and **is written into the check's journal** (the
  next calibration is made on his answers). New files clear every mark on the book; a replaced page clears that page's
  (the owner: otherwise a stray click would hide the same finding next time). ↻ on the same files keeps them.
- **Red** — certain: a leftover `{Name}`, a misspelled / lowercase / undiacritic name, another child's name, a difference
  from the passport the model also confirmed. **Yellow** — worth a look: seen by only one side, edits on the first and
  last page, "from whom" or the buyer's own dedication not found, a spread with no text, **a greeting or the signature
  printed twice** on the first or last page.
- **"Це не та книга!"** — a big red banner (the owner: "a guard against a slip") when half the story spreads or more
  don't look like the ordered book's passport: the pages come from another book's template. It names the book the pages
  look like (both covers), outlines those pages, the badge says "Не та книга", and "Print" asks "Все одно до друку?".
  "Це та книга" removes it (journaled). While it shows, "Update passport" is never offered.
- Problem pages are outlined red/yellow in the proof and the filmstrip; **T** in the viewer shows what the model read
  and what should have been there.
- **"Print"**: still running → "Send without waiting?"; red items → "Print anyway?".
- **"Update passport · N pages"** — pages differing from the passport only in wording: after confirming, their texts
  (cover, spreads) become what was printed, the child's name `{Name}` again, and the check runs once more. The window
  shows the texts as they'll be saved (`preview`). A name becomes `{Name}` **only as a whole word, and only where the
  passport had `{Name}`** (`as_template()`): "Eve" never touches "every", "Hope"/"hope" stays a word where it was one.
- **A light check** (a grey line): no library book, no passport texts or no name — only the program's own rules and the
  model's eye (cut-off text, stuck words, obvious typos).
- Ollama not running — the program starts it; failing that, or with no model, a yellow "Text not checked: …" with ↻.

## How it works (`textcheck/`)

`run.py` — one check (passes, cache, stopping), `rules.py` — what the card shows, `texts.py` — words and which page is
which text, `ollama.py` — the model, `journal.py` — the journal and the owner's marks, `routes.py`.

0. **Warm-up** (`warm()`): as soon as the card takes files, `POST /api/textcheck/warm` loads the model onto the GPU
   while the PNGs are still copied. Silent; repeated within `WARM_AGAIN` (30 s) — nothing.
1. **Readiness** (`_ready()`): Ollama answers (else `start_ollama()`), the model is installed and loaded (~4 s from
   memory, ~70 s from disk).
2. **A quick page scan by the program** (`page_kinds()` → `images.text_score()`, on the 360 px previews, ~5 ms a page):
   printed text is thin strokes in a few narrow lines, an illustration is spread evenly. A page is `text`
   (≥ `LOOKS_TEXT`), `picture` (< `LOOKS_PICTURE`) or `unsure` — the tag alone decides nothing; `unsure` goes to the
   model. Switch: `prescan` in Settings.
3. **Reading** (`READ_PROMPT`, blind, the first lines — `READ_TOKENS`): only the pages that may have text, and the back
   of the cover. A spread with one `text` and one `picture` page whose passport text is known isn't read — it goes
   straight to checking. `has_text()` throws out refusals and 1–3 word answers (the model's reaction to decorative
   pseudo-writing). A page sent straight to checking where the model sees no writing → the other half is checked
   (`_second_half()`).
4. **Which page is which passport text** (`assign()`): a 30-page book — by position (spread *k* = passport spread
   *k+1*); a 24/28-page book — the best order-preserving match (`similarity()` ≥ `MATCH`), the rest `skipped`.
5. **Checking** (`STRICT_PROMPT` with the expected text, `LOOSE_PROMPT` without): the cover's front, page 1, the last
   page, every page with text; the model transcribes word for word and gives a verdict (`SCHEMA`, `JUDGE_TOKENS`), 4
   pages at once (`PARALLEL`). In a 30-page book a spread is checked as soon as its two pages are read; a shorter book
   needs every reading first (its matching needs the order). Answers come in as ready (`_collect()`) and go to
   `job.share()`.
6. **The summary** (`page_issues()`, `book_issues()`): a word-for-word comparison (`diff()`: quotes, dashes,
   punctuation and design capitals are no difference; diacritics are) and the program's rules (`findings()`): `{…}`, a
   misspelled name (1–2 letters, the same first letter; ordinary and passport words aren't names — `COMMON`,
   `_vocabulary()`), a word stuck to the name, another order's child (`_other_children()`). Not shown: punctuation-only
   remarks (`_only_punctuation()`, the model's own `only_punctuation`), a difference only in capitals of the story's
   words (`_case_only()`), a remark that itself says there's no mistake (`_NO_PROBLEM`) or only talks about a line
   break, "a word missing" on a first/last page when every word of the buyer's message is there (`_buyer_intact()`).
   Searched for: things said twice on the first/last page (`_twice()`). Name cleanup and "custom text vs DEFAULT" live
   in `wording.py`, shared with the order card.
7. **The expected text**: `fill()` — `{Name}`, `{Gifter}` (a "from whom" starting with its own "With love…" drops the
   template's line); `personalization()`, `is_default()`; the buyer's own dedication split into "Dedication:" /
   "Closing:".
8. **The cache** — in memory, by the page's **content** (`_digest()`) and the prompt: a re-check is instant, a fixed page
   is the only one asked again, even from a new folder. The model is loaded only when a question isn't cached
   (`_Run.ready()`). A broken answer isn't kept; a call that timed out (`TimedOut`, 300 s) isn't retried. A newer check
   of the same book stops the previous one; the card stops its own (`cancel()`) when closed, given other files or
   another book. Every call runs inside `_Run` (4 at a time, the percentage, the stop signal).
9. **The GPU is freed right after** (`_release_model()`): the model takes ~9.2 of 12 GB, and Book Studio's window and
   Upscayl share the card. `KEEP_ALIVE` (2 min) is only a fallback.
10. **The journal** — `data/logs/checks/<date>_<receipt>-<book number>.json` (what was read, what should have been, the
   problems, each page's own model answer `model`, `layout`, the owner's `notMistakes` — `mark()`); the last 400; local
   only.

- **Every book of an order is checked separately**: the key is `receipt#book number` (`run_key()`) — a check of the
  second book never interrupts the first; closing the whole card stops every book of that receipt.
- **Another book's pages** (`_strange()`, `_wrong_book()`): story spreads unlike the passport — no passport text found
  (24/28 pages) or "another text altogether" (30 pages) — are half the story spreads or more (at least 3). Then one red
  finding (`kind: "book"`, `_one_alarm()`) replaces those rows; `like` — the book the pages start like (`_like_book()`).
  It comes with the first checked page in a 24/28-page book, at half the spreads in a 30-page one; never teaches the
  passport (`_learnable()`); light checks aren't guarded (two books may share a story).

## Why the rules are what they are

- **The calibration of 25.09.2026** (the owner: calibrate "what to show me and what not" — the program's rules, not
  Gemma), on 30 journaled checks: 103 rows shown → 12, red 69 → 3; all 4 real catches kept (a line twice, a signature
  twice, a book from another's template). The noise was mostly a possessive "'s" on the name and capitals of the
  template's words. **The next calibration**: `python app/tools/textcheck_replay.py` shows what today's rules would show
  for every journaled check beside what was shown, with his "Not an error" marks; `--all` — every check.
- **The quick scan** cut a 30-page book's check from ~40 s to ~24 s with identical findings; a text page scores 2.4–2.6,
  a picture 0.9–1.5.
- **`has_text()` and `JUDGE_TOKENS`** exist because the model invented text and looped on picture-only pages (the first
  run took 11 minutes). **"Update passport"** exists because the passports were written apart from the Canva templates
  and drift from them in words.
- Details and dates — [decisions](../decisions.md), [log](../log.md).

## Settings

The "Text check" block in [Settings](settings.md): a switch, the quick scan (`prescan`), a model (those installed that
see pictures), Ollama's status, "Start", "Check connection". `settings.json` → `textcheck` (`enabled`, `prescan`,
`model`, `url`); the address is **127.0.0.1 only** (`_base()`) — pages with children's names never leave the computer.
A disabled Ollama makes Windows wait 2 s per attempt, so the probe is capped at 1 s (`PROBE_TIMEOUT`).

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
