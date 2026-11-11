---
name: book
description: "Make or continue a personalized children's picture book in the Workshop pipeline (pipeline/books/<number>.<slug>/agent/) — a new book from a competitor listing or the owner's brief, or the next step of an existing one: formula, hero, story blueprint, text, text critic, image prompts, the GO check. Use when the owner says «нова книга», «зробимо книгу», «продовжуємо книгу 52», «/book 52», pastes a listing or a brief, or asks for any of those steps. The cover is the book-cover skill; hero variants are book-variant."
argument-hint: "[book number | new]"
---

# Book pipeline

One book = one folder `pipeline/books/<number>.<slug>/`. You write **only** into its `agent/` folder; the Workshop
(Book Studio) owns everything else there and reads your files by their exact names. Paths below are relative to the
repository root (`${CLAUDE_SKILL_DIR}/../../..`); `python` means the portable Python `../runtime/python/python.exe`
from there (the PC may have none of its own).

## 1. Find the book and where it stands

- `new` (or a listing / brief with no number): `python pipeline/scripts/new_book.py <slug>` makes the next numbered
  folder with `agent/` (the number is the Etsy listing's number: highest existing + 1). Write `agent/input.md` from the
  brief ([template](steps/new-book.md#inputmd)).
- A number: find `pipeline/books/<number>.*` (folder names change — never trust memory).
- The state is the files, not the conversation. The next step is the first one whose file is missing:

| Step | Writes (in `agent/`) | Done when |
|---|---|---|
| 0 Formula — [steps/0-formula.md](steps/0-formula.md) | `formula.md` | the file has `Formula:` and `Tier: H` or `Tier: S` |
| 1 Hero, Tier H only — [steps/1-hero.md](steps/1-hero.md) | `canonical-prompt.md`, `character-card.md` | **the owner saved `canonical.png`** and the card matches it |
| 2 Story — [steps/2-blueprint.md](steps/2-blueprint.md) | `story-blueprint.md` | the continuity check passes |
| 3 Text — [steps/3-text.md](steps/3-text.md) | `book-text.md` | self-check passes |
| 4 Critic — the `book-text-critic` subagent | polished `book-text.md`, `text-critic-report.md` | verdict READY or MINOR FIXES (applied) |
| 5 Prompts — [steps/5-prompts.md](steps/5-prompts.md) | `spread-prompts-json.md`, `endpage-prompts-json.md`, `preflight-report.md` | the book check has 0 FAILs → **GO** |
| 6 Cover | `cover-prompts-json.md` | the `book-cover` skill, after the pictures are generated |

Tell the owner in one line where the book is and what comes next («Книга 52: є текст, далі — промпти»), then work.

## 2. Two ways to run

- **The whole brief at once** → run the steps without questions up to the next stop. A missing detail gets the safest
  sensible default, noted in `input.md`.
- **Drip-fed** («нова книга» with little detail) → lead the owner one question at a time: [steps/new-book.md](steps/new-book.md).

Either way, run the steps yourself in this conversation, one at a time — the stops need the owner, and a background
agent cannot ask him. The one exception is the critic: a subagent that only reads and polishes the text and asks
nothing. Keep step names out of what you tell him: he sees plain Ukrainian, not "Agent 3".

## 3. The stops — wait for the owner here

1. **Medium.** No style in `input.md` → ask which preset before step 2 (codes and one-line looks:
   `python pipeline/scripts/preset.py --list`).
2. **Hero (Tier H).** After step 1 the owner generates `canonical.png` (the Workshop's «Герой» step catches it). Steps
   2–6 need it — a hook refuses `story-blueprint.md`, `book-text.md`, the prompt files and `preflight-report.md` of a
   Tier H book without it.
   Only if he explicitly asks to draft ahead: start each of those files with `DRAFT - NOT READY` and give no GO.
3. **GO / NO-GO.** After step 5: `python pipeline/check_book.py "pipeline/books/<folder>"` with 0 FAILs (a hook runs it
   after every write of a book file and shows the FAILs) plus your own gates. Show GO or the fix list.
4. **Generation.** The owner generates the 14 panoramas and 2 squares himself in one Gemini chat from the Workshop rows.
   Nothing to do until he comes back.
5. **Cover.** When the pictures are in, ask for the best frames and use the `book-cover` skill.

## 4. What is always true

- **New books are animal books, Tier S** (the owner, 2026-11-01): the child is a little animal, the family are animals,
  no people, no `canonical.png`; consistency comes from a fixed written description repeated in every prompt. Tier H
  (a human child hero with `canonical.png`) is for the older books and their variants.
- Structure: dedication square + 14 story panoramas (2:1) + afterword square = 30 pages; the cover separately —
  [pipeline/knowledge/book-anatomy.md](../../../pipeline/knowledge/book-anatomy.md). Formula F (ABC) is different:
  [steps/abc.md](steps/abc.md).
- The machine-read formats — `book-text.md` headings, the prompt files' JSON — are in the step files; the Workshop
  breaks if they change.
- Generator-facing prompts describe one standalone picture — the trigger words and why:
  [pipeline/knowledge/master-prompt.md](../../../pipeline/knowledge/master-prompt.md#generator-language).
- Text: [pipeline/knowledge/text-rules.md](../../../pipeline/knowledge/text-rules.md) is the one source; the sensitive-word
  rule there once cost a competitor a 1-star review.
- Lessons from earlier books: [pipeline/knowledge/lessons.md](../../../pipeline/knowledge/lessons.md).
