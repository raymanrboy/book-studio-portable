# Build Book — autonomous orchestrator (full brief → ready-to-generate)

Use this when the user gives the WHOLE brief at once and wants the book taken to the edge of
generation with **no hand-holding**. For drip-fed input, use `onboarding.md` instead — same agents,
interactive, one question at a time.

## Input
A filled `books/[number].[slug]/agent/input.md` (listing/concept, occasion, gender, {Name}, character source, notes).
(Every file the agents write — `input.md`, `formula.md`, the character card, `canonical*.png`,
`story-blueprint.md`, `book-text.md`, the prompt files, reports — lives in `books/[number].[slug]/agent/`.
The book's other folders and `book.json` belong to the Workshop: never create or touch them.)
If something is missing, pick the safest sensible default and note it — do NOT stop to ask.

## Run 0 → 5 with NO questions
**Exception — Style/Medium:** if not specified in `input.md`, STOP and ask the user which preset to use before Agent 2. Show the options from `knowledge/media-presets.md` (RW / W / G / GW / LO / HR / CP / CG / FG / WP). This is the only pre-Agent-2 stop in autonomous mode.

**Format exception — Formula F / ABC Alphabet:** if Agent 0 routes to Formula F, use the ABC square
workflow instead of the standard panorama workflow: Tier S by default, no Agent 1, no `canonical.png`,
2 dedication square images + 26 A-Z square images, `abc-prompts-json.md`, no slicing, and no Agent 6
unless the user separately asks for an outer image.

**Hard sequencing rule — Tier H canonical gate:** STOP 1 is a real stop. For any Tier H / recurring-hero book, do **not** run Agents 2–5 until the generated `canonical.png` exists in the book's `agent/` folder and `agent/character-card.md` has been checked against it. The only exception is when the user explicitly asks for a "draft ahead / storyboard draft before canonical"; then clearly mark every downstream artifact and preflight as **DRAFT - NOT READY**, and never present GO until `canonical.png` exists and `python check_book.py "books/[number].[slug]"` passes.

- **0. Formula Router** (`agents/0-formula-router.md`) → formula + Tier into the blueprint header.
- **1. Character** (`agents/1-character.md`) — Tier H only → canonical prompt + `character-card.md`; human generates `canonical.png`; agent saves/ verifies it. → **STOP 1**.
- **2. Story Blueprint** (`agents/2-story-blueprint.md`) → visual header + 14 story panoramas + 2 square end images + continuity.
- **3. Book Text** (`agents/3-book-text.md`) → `book-text.md` (incl. Afterword).
- **4. Text Critic** (`agents/4-text-critic.md`) → polished `book-text.md` + repetition gate on text/blueprint.
- **5. Illustration Director** (`agents/5-illustration-director.md`) → `spread-prompts-json.md` (14 panoramas) + `endpage-prompts-json.md` (2 squares) (the Workshop shows them in its rows) + repetition gate on the storyboard → **pre-flight GO/NO-GO**.

Agent 6 is not part of the pre-generation story prompt run. It happens after the story panoramas are
generated and approved, because it creates the final wide-image prompt with a different composition
contract.

## The natural stops
1. **STOP 1 — canonical.png (Tier H):** output the canonical JSON prompt; the human generates the
   image outside the chat and returns it; save as the book's canonical reference. Then update/check
   `agent/character-card.md` against the actual image before continuing. Tier S skips this.
   No `story-blueprint.md`, `book-text.md`, `spread-prompts-json.md`, final wide-image prompt, or GO
   preflight should be produced for a Tier H book before this point unless explicitly marked DRAFT.
2. **STOP 2 — GO / NO-GO:** after `python check_book.py "books/[number].[slug]"` (0 FAILs) + the LLM
   gates. Present **GO**, or a precise fix list and loop until GO. No tokens spent yet.
3. **STOP 3 — generation:** on the human's "go", generate the **14 story panoramas + 2 square end
   images** in ONE chat with the reference attached. Tokens are spent here, so only after GO.
4. **STOP 4 — final wide image:** after story panoramas are generated and approved, ask the user: "Are you ready to create the cover? Please send me the best frame from the generated spreads." Once the user provides the chosen frame, run `agents/6-wraparound-image-director.md` using that frame for the characters and the look, placed by its light-ground formula (milky cream ground, the characters low, the title space above them) → `cover-prompts-json.md`, rerun the book check, then generate that one final 2:1 image only after a clean mechanical gate.

## After generation
Agent 6 final wide image (2:1 panorama) → Canva text overlay → PDF. Internally
this asset is used for the outer wrap, but the generator-facing prompt must call it only a standalone
panoramic illustration. Fulfillment per tier (`workflow.md`): **Tier S** = {Name} only (no generation);
**Tier H** = {Name} + img2img character swap of the demo spreads under the customer's archetype.

*(Note: the Workshop catches every downloaded picture, cuts each 2:1 spread into its two square
pages and flips the alternate spreads — no slicing tools for the agents.)*

Formula F / ABC exception: The 28 generated square images go directly to Canva, where
the large A-Z characters, `{Name}`, and short stanza text are overlaid.

