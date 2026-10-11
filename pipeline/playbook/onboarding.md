# Onboarding — Lead the user by the hand

When the user says "new book" / "let's make a book" — the agent enters this
wizard and guides them step by step. This is the "dummy-proof" mode: one question at a time, at the right
moment, without jargon.

## Guiding Principles
- **Strict linear process.** Move step-by-step from numbers 1 → 11. Skipping or jumping over steps is strictly prohibited (for example, creating story scenes or book text for Tier H before `canonical.png` is generated and approved is forbidden).
- **One question/task at a time.** Do not dump everything on the user. Ask or suggest the next action only when the previous step is completely finished and approved.
- **Confirmation and consent (Hard Gates).** After each step, show the intermediate result in a simple form and ask for approval (e.g.: "Does everything look good? Shall we move to the next step?"). Move forward only after clear user consent.
- **Always offer the easy path.** "Don't have it? — no problem, I'll suggest / come up with it myself / we'll pick a character archetype."
- **Agent work — under the hood.** The user does not see the names of AI agents (e.g., "Agent 3" or "Agent 4"). They only see simple and clear explanations of actions from you. Internally, you strictly follow the pipeline `agents/0→6`.
- **Tone:** warm, simple, friendly, and confident. Explain each step in simple language without complex technical terms. Emojis — moderately.

---

## Step 1 — Greeting + brief (one message)
> Hello! 👋 Let's make a new book. To choose the right formula, briefly tell me:
> • What is the **occasion**? (1st birthday / christening / etc.)
> • Is there a **competitor listing title** or your own idea?
>
> *(Note: Do not ask for the child's name. We will use the `{Name}` placeholder for the Canva template).*
>
> The best way is to dump everything at once. Missing something? No problem, I'll help.

→ Internally: `agents/0-formula-router` → formula + **Tier (H/S)**.

## Step 2 — Confirm direction
> Okay: this is **[Formula]**, occasion **[...]**, tone **[...]**.
>
> *[If Agent 0 determined this is a Formula Exception (e.g., Formula F - Alphabet or Formula D - Anthology with custom stories):]*
> > This is a unique format! Because we don't use hardcoded examples for this formula, I need to understand your exact vision before we start. 
> > Please answer these 5-7 questions so I can build the perfect book for you:
> > 1. Will we have a **recurring baby hero** (Tier H) on every page, or an anthology with different subjects / scenic nature (Tier S)?
> > 2. What is the core theme or setting (e.g., specific animals, space, garden, scenic landscapes)?
> > 3. Are there any specific things you absolutely want to include or exclude?
> > 4. What is the exact tone you are aiming for (e.g., funny, educational, spiritual)?
> > 5. [Add 1-3 more specific questions tailored to the user's initial prompt to gather all necessary details to invent the custom scenes.]
>
> *[If this is a regular format (Formulas A-C, E):]*
> > [Tier H:] A book with a recurring baby hero — so first we'll make the main character. Agree?
> > [Tier S:] This is an anthology or scenic book (figures change every time or pure scenery) — there is no recurring hero, we'll start straight with the story.
>
> > What are we painting with? **rich watercolor (RW, default)** / **pastel watercolor (W)** / **gouache (G)** / **glowing watercolor (GW)** / **luminous oil (LO)** / **high-fidelity realism (HR, scenic/sacred keepsake)** / **cozy glow (CG)** / **festive gouache (FG)** — choose the art style
> (`knowledge/media-presets.md`). We will lock it for ALL frames of the book.

*(Note on folder structure: when a new book is initialized, create only `books/[number].[slug]/agent/` and write
every file there — the numbering rule is in `AGENTS.md`. The Workshop makes the rest.)*

## Step 3 — Hero (Tier H only): reference
> Send a **character reference** — a photo or any picture of the baby. I will prepare the hero's design for
> our watercolor style.
> Don't have a reference? — either describe them with words (hair, eyes, skin, clothes) or choose a ready-made **archetype**
> from the library (there are 14: different skin tones, Asian/Black, redheads, boys and girls).

→ Internally: `agents/1-character` + `knowledge/archetypes.md`.

## Step 4 — Canonical prompt
> Done — here is the JSON prompt of the main character (3:4):
> ```json
> [filled canonical-prompt.md]
> ```
> Generate it and save the picture as `canonical.png` in the book's `agent/` folder (the Workshop's
> Hero step can catch it from Downloads for you). Tell me when it's there.
> Want options (different hair/eye color/clothes, or a girl) — say so, I'll throw in presets.

## Step 5 — Receiving canonical
> Super, saved as `canonical.png` ✅. This is our appearance "bible" — all spreads will feature exactly them.

→ Internally: write/update `agent/character-card.md` with the `swappable_attributes` of this baby.
**Hard gate:** for Tier H, do not proceed to story/text/prompts before this step. `canonical.png`
must actually exist in the book folder. If the user explicitly asked to draft ahead, mark
all subsequent files/reports as `DRAFT - NOT READY` and do not give GO until canonical is saved.

## Step 6 — Story
> Now the story. Do you have **references, wishes, or a competitor listing title**? I can come up with it myself
> according to the formula, but the best way is to give everything at once: tone, important moments ("first tooth", "christening"),
> who to mention (grandma / dad / godparents).

→ Internally: `agents/2-story-blueprint` → 15 scenes + continuity check. Show a short outline
(spread titles) for confirmation.

## Step 7 — Text
> Here is the text of all 15 spreads (with `{Name}`). Read it — if you want to change the mood or words anywhere, tell me.
> I have already checked context-sensitive words, meter, and name placement.

→ Internally: `agents/3-book-text` → `book-text.md`.
**Enforce hard text gates from `knowledge/text-rules.md`:**
- **Standard length:** 6 short lines per spread (4-5 words per line; Lines 1-2 Image/Action, 3-4 Promise, 5-6 Childward Turn; up to 8 acceptable).
- **CRITICAL HARD GATE — NEVER RHYME ON {Name}:** `{Name}` MUST NEVER be placed at the end of a rhyming line. Always place it at the start or embedded in the middle.
- **CRITICAL HARD GATE — DIVERSIFY {Name} PLACEMENT & ROLES:** Vary line numbers (Line 2, Line 3, Line 5, Line 6) and grammatical roles (observer/possessive, subject, object/receiver of care), not just direct vocatives.
- **Sensitive words context rule:** `fair/white/light/dark/pale` never for skin, beauty, purity, or human appearance; normal scenery use is allowed.

## Step 8 — Text check (critic)
> Ran the text through the critic-editor: rhymes are simple and high-quality (no forced/repetitive ones),
> rhythm reads easily and bounces smoothly, content is lively, grammar is clean, language is natural **American English**
> (our target audience is native speakers). If I tweaked anything — I will show what exactly and why.

→ Internally: `agents/4-text-critic` → polished `book-text.md` (final text gate).
Enforce no filler words ("And", "So", "Then") starting consecutive lines, flawless read-aloud meter, and US spelling.

## Step 9 — Image prompts
> Assembling prompts (`spread-prompts-json.md` and `endpage-prompts-json.md`, JSON). Done ✅.
> Generate in ONE chat with the attached `canonical.png`: first **14 spreads** (2:1 panoramas),
> and then two separate 1:1 images — Dedication and Afterword. Generate them in one chat with the same reference.
> **We leave the cover for the very end** — a separate premium generation.
> If a frame is ~80% there — don't regenerate, tell me what to fix, I'll fix it in the same chat.

→ Internally: `agents/5-illustration-director` → `spread-prompts-json.md`, `endpage-prompts-json.md`.
> The prompts and texts are in the Workshop — press «Генерувати» there and paste each prompt into Gemini.
Before saying GO, you must run `python check_book.py "books/[number].[slug]"`.
If Tier H prompts refer to `canonical.png`, and the file is missing, the validator will FAIL — this is not a GO.

## Step 10 — Cover (at the very end)
> Are you ready to create the cover?
> Please select the **best, most beautiful frame** out of all the spreads we just generated and send it to me. I will use it as the visual foundation to create a premium wraparound cover prompt (2:1, front=right, back=left, continuous).

→ Internally: `agents/6-wraparound-image-director` → `cover-prompts-json.md`, then rerun the book check;
the cover prompt appears in the Workshop's cover row.

## Helper tools
- **Book check:** `python check_book.py "books/[number].[slug]"` — deterministic pre-flight checks (the old validator's rules);
  0 FAILs before GO. The Workshop shows the same result.
- Cutting, flipping and filing the generated pictures — the Workshop does it, not the agents.

---

## Branches and hints
- **User provided everything at once** → do not ask again; summarize (Step 2) and move on.
- **User has nothing** → suggest: take an archetype (hero) + invent a story according to the formula.
- **User wants several hero options** → give 2–3 presets with `swappable_attributes`.
- **Tier S (anthology)** → skip Steps 3–5; straight to Step 6.
- **Formula F branch (Alphabet)** → this is a super exception:
  - The process is extremely plastic. The number of spreads is fixed (28 squares: 1 dedication, 26 A-Z letters, 1 afterword).
  - At Step 1 we collect wishes regarding the theme (animals, toys, etc.) and Tier choice.
  - If **Tier H** (recurring baby hero) is chosen → follow the standard process (Steps 3-5 create hero, then Steps 6-8 story/text, Step 9 generate 28 squares via `abc-prompts-json.md`).
  - If **Tier S** (no hero) is chosen → skip Steps 3-5, immediately develop a story for letters (Steps 6-8) and generate square images (Step 9).
  - Step 10 (Cover) is completely skipped (it is not needed for the alphabet).
- You can always go back a step and redo one file without touching the rest.
