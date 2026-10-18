# Etsy Children's Book Production — Agent Entry Point

You help produce personalized printed children's books (for sale on Etsy):
30 pages = 14 story-spreads + 2 separate square end pages, the main character is a
baby/toddler, the child's name ({Name}) is inserted into the text, the style is soft watercolor.

Read this file, then — `playbook/README.md` for full navigation.

**Starting a new book:** when the user says "new book" / "let's make a book" — DO NOT dump everything,
but lead them by the hand step-by-step using `playbook/onboarding.md` (one question at a time, warm tone).
If the user provides **the entire brief at once** — use the autonomous `playbook/build-book.md`
(agents 0→5 without questions until story generation; Agent 6 after approved story panoramas; stopping
only for **style** / canonical.png / GO-NO-GO / generation / final wide image).

> **Entry point for book agents.** `AGENTS.md` — the one file, read by any agent
> (Antigravity, Claude Code, Codex…; there is no separate `GEMINI.md` since 2026-10-03). `CLAUDE.md` is a different file on purpose — it is for coding agents
> working on Book Studio's code. This folder is the book pipeline inside Book Studio (the user's program): a clean
> copy of the old `Etsy-Book-Pipeline` (2026-09-26); the old folder is an archive — never write to it. Everything
> outside this folder is Book Studio's code and data — not yours to read or change.

---

## Where you write — one book, one folder

```
books/[number].[slug]/
  agent/        ← YOU write here, and only here: every file of the book
  pictures/     ← the Workshop's (the generated pictures, cut into pages) — never touch
  originals/    ← the Workshop's (the pictures as the generator made them) — never touch
  book.json     ← the Workshop's — never create, read into prompts, change or delete
```

- **Every file you make for a book goes into its `agent/` folder** (flat, no subfolders): `input.md`,
  `formula.md`, `canonical-prompt.md`, `character-card.md`, `canonical.png`, `story-blueprint.md`,
  `book-text.md`, `spread-prompts-json.md`, `endpage-prompts-json.md`, `cover-prompts-json.md`, reports.
  The Workshop reads these files by their names — keep the names exactly.
- **New book naming rule:** a new book is a new folder `books/[number].[slug]/agent/`, with an
  auto-incrementing number prefix. Look into `books/` (`list_dir`) for the highest number and add 1;
  **a book's number is its Etsy listing's number** (the owner, 29.09.2026): 24 is Spooky stories, 25 Sleepy trucks
  bedtime — the next new book is the highest number + 1 (26, …). Never make a folder with just the name.
- **Dynamic lookup rule:** never rely on your memory of book paths. Before reading or writing a book,
  scan `books/` to find its current folder name — the user may rename folders.
- **Can't see `books/`, or can't write there?** The books are kept out of git, and Antigravity hides
  git-ignored files from its agents until the user turns on *Settings → Agent → Agent Gitignore Access*. Tell
  the user exactly that and wait — never write a book anywhere else.
- **The Workshop** (Book Studio → «Лістинги» → «Майстерня», the user's program) shows the book's progress by your files,
  puts each prompt into the clipboard, catches the pictures the user downloads from Gemini, cuts every
  2:1 spread into its two square pages and flips the alternate ones. **Cutting, flipping and filing
  pictures are not your job** — there are no tools for that here.

### Hero variants (Tier H) — only when the user asks for one

```
books/[number].[slug]/agent/variants/<G#_name>/     e.g. G2_brunette (the looks in playbook/knowledge/archetypes.md)
  hero-prompt.md    the edit prompt for canonical.png (one ```json block): change only the swappable attributes
  2.json … 15.json  one swap prompt per story spread, named by the spread's number (2 = pages 2–3 … 15 = 28–29):
                    Image 1 = the original spread, Image 2 = the variant's hero.png; replace only the hero,
                    keep everything else of Image 1 (pose, composition, text-safe area, style) exactly
  hero.png          saved by the Workshop when the user generates the variant's hero — never write it
```

---

## Pipeline — agents 0–6 (run sequentially)

Each agent = a role-file in `playbook/agents/`, does ONE thing, writes ONE short file.
Keep it lean — do not overcomplicate. Everything exists to fill `playbook/master-prompt.md`.

```
INPUT (listing + occasion + name + character)
  ▼ [0] Formula Router        playbook/agents/0-formula-router.md   → formula.md (formula + Tier H/S)
  ▼ [1] Character (Tier H)     playbook/agents/1-character.md        → canonical-prompt.md + character-card.md → canonical.png
  ▼ [2] Story Blueprint        playbook/agents/2-story-blueprint.md  → story-blueprint.md (visual header + scenes + continuity)
  ▼ [3] Book Text              playbook/agents/3-book-text.md        → book-text.md
  ▼ [4] Text Critic            playbook/agents/4-text-critic.md      → polished book-text.md (poetry + US-English)
  ▼ [5] Illustration Director  playbook/agents/5-illustration-director.md   → spread-prompts-json.md + endpage-prompts-json.md + pre-flight GO/NO-GO
  ▼ the user generates the story panoramas in Gemini (one chat), the Workshop catches them
  ▼ [6] Wraparound Image       playbook/agents/6-wraparound-image-director.md → cover-prompts-json.md → final wide image
  ▼ Canva (the book's pictures/ folder + the texts) → the Book Studio library
  ▼ FULFILLMENT: Tier S — {Name}+PDF (no generation); Tier H — +img2img character swap to archetype
```

**The book check** (mechanical pre-flight, 0 FAILs before GO):
`python check_book.py "books/[number].[slug]"`

**Tier** is decided by Agent 0:
- **Tier H** — recurring baby hero (birthday, blessing) → Agent 1 WORKS.
- **Tier S** — anthology, figures change every time (Bible) → Agent 1 is SKIPPED,
  consistency is maintained only by style.

**Tier H canonical gate (hard stop):** if the book has a recurring hero, Agent 1 stops
the pipeline at `canonical-prompt.md` + `character-card.md` until the real `canonical.png` is
generated and saved in the book's `agent/` folder. Do not create `story-blueprint.md`, `book-text.md`,
`spread-prompts-json.md`, final wide-image prompt or GO preflight before `canonical.png` appears, unless the user
explicitly requested to `draft ahead`. In draft-ahead mode, mark all downstream files/reports as
`DRAFT - NOT READY`; GO is allowed only after `canonical.png` + a clean book check.

---

## Sacred rules (do not violate)

- **`playbook/master-prompt.md` — our everything for story panoramas.** The only skeleton for story prompts.
  We do not change the structure; agents only FILL its blocks with data (see Agent 5).
  The final wide image is done by Agent 6 following the same image-only language discipline, and since 2026-10-17
  always by its **light-ground formula**: the characters small and low in the right area on a milky cream ground, the whole
  upper right empty for the title, a few small details on the left (the owner's examples: `../wiki/raw/2026-10-17-white-cover-examples/`).
  Why it works: `playbook/master-prompt-anatomy.md`.
- In every generator-facing prompt: **standalone image + text area / overlay area + safe text/style negatives**.
  Do not mention `book/page/spread/cover/front/back/spine/fold/gutter/seam/mockup/product` even in negatives.
- Structure: cover + first page (dedication) + 14 spreads + last page (afterword/wishes);
  first and last — are two separate 1:1 square images with a rounded center-safe text area
  and decorative corners/edges (see `playbook/knowledge/book-anatomy.md`).
  1 scene = 1 spread, ~6 short lines of text of uniform visual length (craft standard: 4-5 words / 7-8 syllables per line forming a neat visual rectangle for Canva; lines 1-2 Image/Action, 3-4 Promise, 5-6 Childward Turn; up to 8 acceptable; formula can dictate its pattern).
- {Name} at least once every 2–3 spreads.
- **Context-sensitive words** about skin/appearance (fair, white, light, dark, pale):
  do not use for skin tone, beauty, purity, "goodness" or comparisons of people; in natural
  descriptions like `morning light`, `dark sky`, `white paper` — allowed.
  `playbook/knowledge/text-rules.md`, `notes/discoveries.md`.
- Style — simplified pastel watercolor, hand-painted, lots of air, simple shapes,
  one clear cute focus. No hyper-detail / 3D / vector / anime / photorealism / AI-look.
- Generate all book spreads in ONE chat with a reference.
- **Never** touch `check_book.py`, another book's folder, or anything outside `books/[number].[slug]/agent/`
  of the book you work on (reading the playbook, notes and `Listing prompts/` is fine).

---

## Project Map

```
AGENTS.md                      ← entry point for book agents (any agent)
CLAUDE.md                      ← for coding agents (Book Studio's code) — not for making books
playbook/
  README.md                    ← navigation
  onboarding.md                ← "lead by the hand" wizard for a new book (drip feed input)
  build-book.md                ← autonomous orchestrator (full brief → ready for generation)
  master-prompt.md             ← ★ skeleton of ALL prompts (filled by agents)
  master-prompt-anatomy.md     ← what exactly works in it (load-bearing blocks)
  visual-world-bible.md        ← ★ global style DNA
  workflow.md                  ← full pipeline step by step
  agents/                      ← 0..6 agent role files
  knowledge/                   ← formulas/, listing-to-formula, text-rules, audience, book-anatomy, archetypes, repetition-gate, media-presets
notes/discoveries.md           ← insights from tests and competitors
Listing prompts/               ← the listing photo prompts (ChatGPT)
books/[number].[slug]/agent/   ← your files for one book
check_book.py                  ← the book check (the same rules the Workshop shows)
```

---

## Two production tracks

1. **Production (once, hard):** agents sequentially → demo set ~15 frames (Tier H — with one
   most popular archetype).
2. **Order fulfillment:**
   - **Tier S** (goose/animal/anthology): only {Name} (text in Canva) + PDF assembly — without generation.
   - **Tier H** (book with a child): {Name} + if necessary **img2img-edit of demo frames, swap ONLY
     the character** to the customer's archetype (composition and text area unchanged) → PDF.

Details of techniques and what works/doesn't: `notes/discoveries.md`, `playbook/workflow.md`.
