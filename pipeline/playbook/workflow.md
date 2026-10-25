# Workflow — full pipeline (agents 0–6)

Lean pipeline from listing to finished prompts. Each agent does one thing and writes one
short file. Agents 0–5 prepare story panoramas via `master-prompt.md`; Agent 6 prepares
a separate final wide-image prompt.

---

## Steps

### 0. Formula Router → `agents/0-formula-router.md`
Based on the listing: formula (A–E) + occasion + tone + **Tier (H/S)**. The Tier decides whether to run Agent 1.

### 1. Character (Tier H only) → `agents/1-character.md`
Canonical portrait prompt (→ you generate `canonical.png`) + short `character-card.md`
(≈8–12 fields = CHARACTER block of the master-prompt). Tier S — we skip.

### 2. Story Blueprint → `agents/2-story-blueprint.md`
First, a subtle **visual header** (palette/mood/motif/must-NOT) on top of the global
`visual-world-bible.md` — absorbed the former Visual World step. Then WHAT for each spread +
locations + sequence + **built-in continuity check**. No text, no prompts.

### 3. Book Text → `agents/3-book-text.md`
Text for each spread (formulas + text-rules + audience), immediately following the poetic standard.

### 4. Text Critic → `agents/4-text-critic.md`
Text audit and polish: high-quality simple rhymes (no forced/repetitive ones), rhythm, content,
grammar, **native American English**. This is the final text gate. → polished `book-text.md`.

### 5. Illustration Director → `agents/5-illustration-director.md`
Populates `master-prompt.md` with data from all previous ones → `spread-prompts-json.md` (14 panoramas),
`endpage-prompts-json.md` (2 squares); the Workshop reads them (with `book-text.md`) into its rows.
2:1 story panoramas + 1:1 square end images + text area + safe negatives are mandatory.
At the end — pre-flight GO/NO-GO before generation.
The generator-facing JSON describes only a standalone image: no words like `book/page/spread/cover/front/back/spine`.

### 6. Wraparound Image Director → `agents/6-wraparound-image-director.md`
After story panoramas are approved, creates `cover-prompts-json.md` for the final 2:1 wide image
(the Workshop's cover row takes it). It first **asks the user which mode**: 2:1, or «два квадрати» — two 1:1
prompts (`title-square` with the painted title and room for the name, `quiet-square` with no characters and no
text), which the Workshop lays on Gelato's template and outpaints between.
Internally this is a cover wrap, but in prompt-language it is just one continuous panorama:
main focus on the right, quieter environment continuation on the left, calm zone top right
for future typography. No book/physical trigger words even in negatives.

### Production (order is important)
1. Generate in ONE chat with a reference: **14 story panoramas** (2:1) + **2 square end images**
   (Dedication + Afterword; 1:1, decorative corners/edges, calm rounded zone in the center for text).
   The Workshop puts each prompt in the clipboard and catches each downloaded picture into its row.
2. The Workshop cuts every 2:1 panorama into its two square pages and flips the alternate spreads
   (4–5, 8–9 … 28–29); the pages land in the book's `pictures/` as `1.png`..`30.png`.
3. **Final wide image** you generate LAST via Agent 6 — a separate premium 2:1 panorama
   (main focus right, quieter continuation left, slightly higher contrast). The Workshop then puts it on a
   bigger white canvas and gives an outpaint prompt, so the generator fills the margins → `pictures/Cover.png`.
4. **Upscale** — the Workshop does it by itself: every page and the cover ×2 with the owner's Upscayl, right after
   the picture lands in its row (a book can be left without it — the switch «Апскейл ×2»).
5. **Canva:** the book's `pictures/` folder → Canva (overlaying text from `book-text.md`) → PDF 300 DPI.

### Fulfillment (made to order)
- **Tier S** (goose/animal/anthology/scenic): only {Name} substitution (text in Canva) + PDF assembly — **no generation**.
- **Tier H** (book with a child): {Name} + if necessary **img2img-edit of demo frames, swap ONLY the character** to
  the customer's archetype (composition and `text_safe_area.side` unchanged, so the Canva overlay fits) → PDF assembly.

---

## Sources of truth (higher = stronger)
Formula → Character Lock Card (WHO, Tier H) → Visual World Bible (HOW) → Story Blueprint
(WHAT + continuity) → Book Text → Illustration Director.

## Two tracks
1. Production (once, hard): agents sequentially → demo set of frames.
2. Order fulfillment: Tier S — {Name} + PDF (no generation); Tier H — {Name} + img2img character swap to archetype.

