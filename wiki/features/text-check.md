---
title: Text check
type: feature
updated: 2026-11-12
code:
  - app/studio/textcheck/run.py
  - app/studio/textcheck/rules.py
  - app/studio/textcheck/texts.py
  - app/studio/textcheck/ollama.py
  - app/studio/textcheck/journal.py
  - app/studio/textcheck/routes.py
  - app/studio/wording.py
  - app/tools/textcheck_replay.py
  - app/studio/textcheck/__init__.py
---
# Text check

> The "AI validator": after the files from Canva are laid out in the order card, a local Gemma model (Ollama, this PC's graphics card) reads the text pages and the program compares what will be printed with what should be there — the book passport's texts with the child's name, the dedication, the "from whom" from Etsy. The result is the «Вичитка» step of the order card: a badge, a list of problems, marks on the pages. **It never blocks printing — it only asks.** Installing Ollama and the model: [modules.md](modules.md).

## What the owner sees (order card, step «Вичитка»)

- **Starts on its own** after a successful file check. The badge: a spinner with a percentage → "Text matches" (green) / "N errors" (red) / "N questions" (yellow). ↻ checks again.
- **Findings appear while it runs**, then the full list replaces them. A row reads "Page 7 · "Ollivia" instead of "Olivia"" with the model's explanation in Ukrainian; a click opens the viewer on that spread. ✓ «Це не помилка» hides it and is written to the check's journal. New files clear all marks; a replaced page clears its own.
- **Red** (certain): a leftover `{Name}`, a misspelled / lowercase / undiacritic name, another child's name, a passport difference the model also confirmed. **Yellow** (worth a look): seen by only one side, edits on the first or last page, "from whom" or the buyer's own dedication not found, a spread with no text, a greeting or signature printed twice (`_twice()`).
- **«Це не та книга!»**: a big red banner when half the story spreads or more (at least 3) do not look like the ordered book's passport — the pages come from another book's template. It names the book the pages look like, outlines those pages and the print dialog asks «Все одно до друку?». «Це та книга» removes it. While it shows, "Update passport" is never offered.
- Problem pages are outlined in the proof and filmstrip; **T** in the viewer shows what the model read and what should be there.
- **Print dialog:** still running → «Send without waiting?»; red items → «Print anyway?». The dialog itself belongs to [orders](orders.md).
- **«Update passport · N pages»**: pages differing from the passport only in wording become the passport's texts after a confirmation, with `{Name}` restored, and the check runs again. A name becomes `{Name}` only as a whole word and only where the passport had `{Name}` (`as_template()`).
- **A light check** (grey line): no library book, no passport texts or no name — only the program's own rules and the model's eye (cut-off text, stuck words, obvious typos).
- Ollama not running → the program starts it; failing that, or with no model, a yellow «Text not checked: …» with ↻.

## How a check runs

Files: `run.py` (one check: passes, cache, stopping), `rules.py` (what the card shows), `texts.py` (words, which page is which text), `ollama.py` (the model), `journal.py` (journal and marks), `routes.py`.

1. **Warm-up** (`warm()`): when the card takes files, the model loads onto the GPU while the PNGs copy. Silent; repeated within `WARM_AGAIN` (30 s) does nothing.
2. **Readiness** (`_ready()`): Ollama answers (else it is started) and the model is installed.
3. **Quick scan** (`page_kinds()` → `images.text_score()` on small previews): printed text is thin strokes in narrow lines, an illustration is spread evenly. A page is `text` (≥ `LOOKS_TEXT`), `picture` (< `LOOKS_PICTURE`) or `unsure`; the tag alone decides nothing, `unsure` goes to the model. Switch: `prescan`.
4. **Reading** (`READ_PROMPT`, blind, first lines only — `READ_TOKENS`): pages that may have text and the cover's back. `has_text()` throws out refusals and 1–3 word answers.
5. **Which page is which text** (`assign()`): a 30-page book by position (spread *k* = passport spread *k+1*); a 24/28-page book by the best order-preserving match (`MATCH`).
6. **Checking** (`STRICT_PROMPT` with the expected text, `LOOSE_PROMPT` without): the cover's front, page 1, the last page, every page with text. The model transcribes word for word and gives a verdict (`SCHEMA`, `JUDGE_TOKENS`), `PARALLEL` (4) pages at once, pictures at `IMAGE_SIDE`.
7. **Summary** (`page_issues()`, `book_issues()`): the program's own word-for-word `diff()` decides (quotes, dashes, punctuation and design capitals are no difference; diacritics are) plus `findings()`: `{…}`, a misspelled name (1–2 letters, same first letter), a word stuck to the name, another order's child. Remarks that only talk about punctuation, capitals, a line break or "no mistake" are not shown.
8. **Expected text** (`texts.fill()`): `{Name}`, `{Gifter}`; the buyer's own dedication is split into «Dedication:» / «Closing:» (`split_dedication()`); name cleanup and "custom text vs DEFAULT" live in `wording.py`, shared with the order card.
9. **Cache**, in memory by page content (`_digest()`) and prompt: a re-check is instant and only a fixed page is asked again, even from a new folder. A broken answer is not kept; a call that times out (`TimedOut`, 300 s) is not retried. A newer check of the same book stops the old; the card stops its own (`cancel()`) when closed or given other files.
10. **The GPU is freed right after** each check (`_release_model()`); `KEEP_ALIVE` (2 min) is only a fallback.
11. **Journal:** `data/logs/checks/<date>_<receipt>-<book>.json` — what was read, what should have been, the problems and the owner's `notMistakes` marks (`mark()`); the last `KEEP` (400) records; local only.

**Every book of an order is checked separately:** the key is `receipt#book` (`run_key()`).

**Another book's pages** (`_strange()`, `_wrong_book()`): when story spreads unlike the passport reach half or more (at least 3), one red finding (`_one_alarm()`) replaces those rows and `_like_book()` names the book the pages start like. It never teaches the passport; light checks are not guarded (two books may share a story).

## Starting Ollama

- A program-made start is `ollama.exe serve` with `CREATE_NO_WINDOW` (`_ollama_command(hidden=True)`); the tray app `ollama app.exe` is used only for Settings «Запустити» on a PC install. The portable copy starts `runtime/Ollama/ollama.exe serve`.
- Ollama itself starts shortly after the program (`start_quietly()`), the model is requested when the card of a new, unsent order opens, so its slow first read is over while the files are made in Canva. Nothing is read at program start.
- On made-up or test data (`core.SANDBOX`) Ollama is never started (one already running is still used).
- Settings (`textcheck` → `enabled`, `prescan`, `model`, `url`) are in [modules.md](modules.md#the-text-checks-own-settings). The address is 127.0.0.1 only (`_base()`); `PROBE_TIMEOUT` (1 s) caps the "is Ollama there" probe.

## Why

- **Local only:** pages with children's names never leave the computer (a cloud model was rejected for that reason); the address is forced to 127.0.0.1.
- **It never blocks printing:** the model can be wrong; the owner has the last word.
- **Calibration lives in the program's rules, not in Gemma.** Every «Це не помилка» goes to the journal and the rules are tuned on them; every real catch (a line or signature twice, another book's pages, a wrong spread, a misspelt name) must stay. `python app/tools/textcheck_replay.py` (`--all`) shows what today's rules would show for each journaled check next to what was shown.
- **The model is told what should be there, but `diff()` decides**, and the name hint plus blind transcription together avoid the model "correcting" a real name.
- **The quick scan, `has_text()` and `JUDGE_TOKENS` exist** because the model invents text and loops on picture-only pages; a looping answer is cut and the whole copy that came before is kept (`_salvage()`, amber at most, not cached). See [limits](../dev/limits.md).
- **GPU freed after each check:** the card is shared with the window and Upscayl. `PARALLEL = 4` matches `OLLAMA_NUM_PARALLEL=4`.
- **Marks reset with the files:** otherwise a stray click would hide the same finding next time.
- **«Update passport» exists** because passports drift from the Canva templates in wording.

## Where in the code

- [app/studio/textcheck/run.py](../../app/studio/textcheck/run.py) — `check_order()`, `check_book()`, `warm()`, `start_quietly()`, `run_key()`, `cancel()`
- [app/studio/textcheck/rules.py](../../app/studio/textcheck/rules.py) — `findings()`, `page_issues()`, `book_issues()`, `has_text()`, `_wrong_book()`
- [app/studio/textcheck/texts.py](../../app/studio/textcheck/texts.py) — `assign()`, `diff()`, `fill()`, `split_dedication()`
- [app/studio/textcheck/ollama.py](../../app/studio/textcheck/ollama.py) — `_ready()`, `_release_model()`, `_ollama_command()`, `_base()`, `DEFAULT_MODEL`
- [app/studio/textcheck/routes.py](../../app/studio/textcheck/routes.py) — `as_template()`; [journal.py](../../app/studio/textcheck/journal.py) — `mark()`
- [app/studio/wording.py](../../app/studio/wording.py) — name and custom-text helpers; [order-card.js](../../app/web/js/pages/order-card.js) — the badge, the list and the banner
- [app/tools/textcheck_replay.py](../../app/tools/textcheck_replay.py) — the journal through today's rules

## Related

- [Orders](orders.md) · [Modules](modules.md) · [Order to print](../flows/order-to-print.md) · [Library](library.md) · [Known limits](../dev/limits.md) · [Security](../security.md)
