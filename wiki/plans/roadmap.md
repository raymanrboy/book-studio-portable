---
title: Plans — what's next
type: plan
updated: 2026-09-27
code: []
---
# Plans

> Ideas agreed with the owner, but not yet built. Starting any of them needs his command.

> **Reviewed with the owner on 2026-09-25** (an agent's list of ideas, his answer point by point — what he
> keeps is below, what he turned down is in [decisions](../decisions.md), 2026-09-25).

## The order pipeline

- **Pages from the library instead of Canva.** Every spread has one page with text and one that's just
  a picture. Pages with no text could come from the library (already upscaled); only the personalized
  ones would need downloading from Canva; the file numbers themselves say what's given, and the program
  fills in the rest.
  *Needed:* fill the library with every book.
  **Later — a micro feature** (the owner, 2026-09-25): his storage and internet are fine, so to avoid
  confusion the whole book keeps coming from Canva for now.
- **The ship-by date on a new order's card** (agreed 2026-09-25, not built). Not intrusive — "not small,
  but not loud": a quiet line on the right side of the card, where there is room. Not in the queue's
  rows. *Note:* Etsy gives the date per item (`expected_ship_date` in a receipt's transactions);
  `profit.normalize_receipt()` doesn't keep it yet — it needs adding there (a full re-sync fills it for
  older receipts).
- **The program draws the pages itself — "an order comes in, and it's all already filled in"** (the
  owner's idea, 2026-09-19, "off the top of his head"; details — [below](#pages-with-no-canva-idea-2026-09-19)).
  All the owner would need from Canva is placing text on the pages; the most manual work is long
  dedications.
- **A "doesn't fit the 24-page version" mark** on spreads in a book's passport (exactly 3 per book; the
  program would make sure there are exactly three) — then the program could check that exactly the
  right pages for Printify were downloaded from Canva. *Partly there already:* the text check already
  works out which passport spreads are missing from a book (the badge's hint says "missing spreads 5, 9,
  12") — checking that against the marks is what's left.
- ~~Text check~~ — **built on 2026-09-19** on a local model: [features/text-check.md](../features/text-check.md).
  ~~Checking spreads as soon as they're read~~ and ~~warming up the model~~ — **built on 2026-09-20**
  (findings now appear while the check runs; the time saved comes from the warm-up, not the pipeline
  change — see [decisions](../decisions.md)). Next possible steps: a fallback Gemini model (a key
  exists; pages would then go to the cloud — only with the owner's decision); "Update passport" for the
  dedication and afterword (needs the reverse substitution of "from whom" back into `{Gifter}`).
- ~~**Replacing a single page right from the viewer**~~ — **built on 2026-09-20**, as agreed below
  ([features/orders.md](../features/orders.md)). The case: the text check finds a mistake → the owner
  fixes it in the Canva template → downloads **one** page → has to replace it in the already-prepared
  folder without redoing the whole book.
  - **Where:** in the page viewer (`lightbox.js`), in the top row next to "Page text" and "Open the
    original file" (there's already a mechanism for a button that hides when the action isn't
    available). A spread shows two pages, so there are **two** buttons — "Replace 6", "Replace 7" (the
    owner's decision); the cover and outer spreads have one. **Only in the viewer**: there won't be a
    button on a text-check finding's row (also his decision).
  - **Where exactly it's needed:** the order card **and** the Order Creator (the same structure viewer).
    Not in the [order archive](../features/archive.md) or the library (those hold what already went to
    print).
  - **Picking the file** — the native Windows dialog, like `desktop.pick_folder()`, just
    `askopenfilename`: it returns a path, so nothing gets uploaded into the window and the replacement
    is instant.
  - **After replacing:** the old page goes into a hidden subfolder (for "Undo"); the picture in the
    viewer is immediately the new one — **the browser cache has to be bypassed** (`/media/folder` is
    served with `max-age=600`, otherwise the old one shows); the files are re-checked; the text check
    restarts — the model re-checks **only this page** (the cache is keyed to the file, its size, and its
    modified time), ~3–5 s; "not an error" marks on this page are cleared; a message: "Page 7 replaced ·
    Undo".
  - **Printify**: the page has to be exactly 4000×4000, so the fixed one also needs to go through
    Upscayl — the file check's message should explain this. Gelato has no size requirement.
  - If a draft has already been created → warn that it needs to be **sent again** after the
    replacement.
  - **Also fix a trap while at it:** right now, dropping 1–2 files onto a card that already has a
    folder wipes out all the prepared work and fails with "24 pages needed, found 1". It should touch
    nothing, and point to the viewer instead.
- ~~**"Not an error" marks are cleared by new files**~~ — **built on 2026-09-20** (new files clear the
  book's marks, replacing a page clears that page's marks; ↻ keeps them).
  Right now a finding's identifier is computed from the file name and the finding's text, and new files
  don't clear the marks — so the same yellow (or even red) finding would stay hidden, and the badge
  would say "Text matches"; the pre-print question wouldn't count it either. Needed: new files (a drop,
  picking a folder, "take files from an earlier send") clear **this book's** marks; replacing a single
  page clears only **that page's** marks; ↻ "Check again" on the same files keeps them.
  *Still unresolved:* whether to show a "Hidden: N · show" line (to bring back a finding right away,
  without waiting for new files), and whether to mention hidden red findings in the pre-print question.
- ~~**A "product already created in Printify" mark**~~ — **most likely covered already** (checked on
  2026-09-25; the owner to confirm). *Why he wanted it:* a Printify "On hold" order (and a Gelato draft)
  leaves the receipt in "New" until he confirms and pays it — so the same book could be created twice.
  *What covers it now:* in the queue such a receipt carries a printer-status chip `On hold` / `Draft`
  (from the sync at launch and "Refresh", `profit.waiting_order()`), and the card's "Print" step says
  "Draft … created" with "Result in Order Creator" ([features/orders.md](../features/orders.md)).
- ~~**Orders with several books**~~ — **built on 2026-09-20**: each book of an order goes through the
  path separately, and they go to the printer together as one draft to one address
  ([features/orders.md](../features/orders.md), [features/order-creator.md](../features/order-creator.md)).
- **Upscaling for orders — not needed** (the owner, 2026-09-25): his Canva books now hold pages that are
  already upscaled. Upscaling moves to the Workshop — [below](#the-workshop).

Built from this list: 28 pages in Gelato (2026-09-17), the [order archive](../features/archive.md) with
reprints (2026-09-18), a local-model [text check](../features/text-check.md) (2026-09-19), orders with
several books and a faster text check (2026-09-20).

## The text check — the research story (built on 2026-09-19, on a local model)

> How the finished feature works — [features/text-check.md](../features/text-check.md). Below is how it
> got there: a plan with Gemini, model tests, thoughts on the design. Gemini isn't used in the program.

**As first planned:** a "Text check" step after laying out files in the order card.
- Send **only pages with text** (the cover, the dedication, one per spread, the afterword — up to 17),
  shrunk, in one request.
- Along with each — the reference text from the library (`{Name}`, `{Gifter}`), the child's name, the
  dedication, and "from whom" from Etsy.
- The model **transcribes the text word for word**, names every name and any leftover `{…}`, gives a
  verdict of ok / warn / error, and explains it in Ukrainian. **The program compares the exact things**
  (the name, letter for letter, `{`); the model only judges the ambiguous ones (a reasonable stylistic
  edit versus a mistake).
- Green / yellow / red marks — in the proofing filmstrip; adjustable "sensitivity".
- Fallback models: 3.8 Flash → 3.6 → 3.5; all unavailable → "the check isn't available right now". The
  model name — in settings, not in code (Google ships new Flash versions every few weeks).
- Each check is recorded, modeled on the [send journal](../features/send-journal.md).

**Test on 2026-09-17** (3 made-up pages, handwritten Segoe Script font with planted mistakes, REST
`generateContent`, a structured JSON response, `mediaResolution: HIGH`, `thinkingLevel: low`):
- 3.8 Flash and 3.7 Flash — "503: model overloaded" the whole time; 3.6 Flash and 3.5 Flash — **found
  everything**: "Emilly" instead of "Emily" and a forgotten `{Gifter}` → error; "gentle" → "soft" → warn
  (other line-break differences weren't treated as mistakes); another name, "Clara" → error. The text
  was transcribed word for word.
- ~3 s for 3 pages; a page ≈ 1100 tokens → 17 pages ≈ 20K tokens per order.

**The owner's decision:** the key would be the free tier of AI Studio, no subscription
([decisions.md](../decisions.md)). The owner had already saved the key in the program's vault as
`gemini_api_key` (DPAPI); there's still no code that uses it, and no field in Settings either.

**A local model (installed on 2026-09-19, at the owner's request):** Ollama 0.34.2 in
`D:\Programs\Regular\Ollama`, models in `D:\Programs\Regular\Ollama\models` (a user variable
`OLLAMA_MODELS`, set by the owner), model **`qwen3.5:9b`** (6.1 GB). Server —
`http://127.0.0.1:11434` (`/api/chat`, pictures in `images`), starts with Windows (an icon near the
clock). GPU — an RTX 4070 SUPER, 12 GB: the model takes ~7.3 GB, only while working and for ~5 min
after.

**Local-model test, 2026-09-19** (the same 3 pages used for Gemini):
- **If the model is told the correct name, it "corrects" what it read**: it rewrote "Emilly" as "Emily"
  and missed the mistake (with reasoning enabled — the same result). It found the other name "Clara",
  `{Gifter}`, and "gentle" → "soft".
- **Blind transcription** (the model knows neither the name nor the template — "transcribe exactly,
  don't correct anything"), with the program doing the comparing: **3 of 3 pages transcribed word for
  word**, and the program found all 4 mistakes. ~2.5 s per page; the first one after idling — ~80 s (the
  model loads onto the GPU).
- **Conclusion:** for a local model, blind transcription only — the program does all the comparing.

**Gemma 4 12B QAT** (`gemma4:12b-it-qat`, 6.7 GB on D, 7.7 GB on the GPU; installed on 2026-09-19 at the
owner's request — "the best Gemma that fits in 12 GB"): the same test **passed fully both ways** — with
the name as a hint, it didn't "correct" "Emilly" (error, like Gemini); blind transcription 3 of 3. Faster
than Qwen: ~1–3 s per page, ~70 s for the first one after idling. It reads a picture with about half the
tokens (~1300 versus ~2600). **The main candidate** for the local check; Qwen remained a fallback. Bigger
variants (`gemma4:26b-a4b`, 16–19 GB; `31b`, 20 GB) don't fit the GPU fully; `nvfp4`/`mxfp8` compression
is for the RTX 50-series, `mlx` is for Mac; for Gemma, use the `-qat` variant.

**A hard test on 2026-09-19** — 12 pages made by the owner in his real Canva templates (full-page verse,
the brand's own font, illustrated backgrounds, a cover with a curved caption): 5 with mistakes —
"Ollivia", a forgotten `{Name}`, another child's name "Noah" next to the correct "Mason's", "Zoe" with no
diaeresis next to the correct "Zoë's", the word "bit" missing; 7 clean ones, 2 of which were real pages
from someone else's real book that the owner planted himself.

| | Gemma 4 12B QAT | Qwen 3.5 9B |
|---|---|---|
| blind transcription, full size (2000 px) | **5/5, 0 false positives**, ~2.5 s | 5/5, 0 false positives, ~6.5 s |
| blind, shrunk to 1024 / 768 px | **5/5, 0 false positives**, ~1.5 s | 1024: 4/5 (read "Ollivia" as "Olivia") |
| with a hint, full size | 5/5, 0 false positives, ~4 s | 4/5 (missed "Zoe") |
| with a hint, 1024 px | 5/5, 0 false positives, ~3 s | 3/5, and 1 false positive (apostrophe style) |

A repeat run gave the same result (temperature 0). **Conclusion:** Gemma 4 12B QAT, blind transcription,
a 768–1024 px picture, comparison done by the program (words, with quotes/apostrophes/dashes normalized;
case and diacritics checked strictly) — ~1.5 s per page, 17 pages ≈ 25–30 s. Not checked: words stuck
together ("Isabellawalked") and text half cut off — the owner hadn't made these two pages; nor were
other fonts checked.

**Words stuck together (page 13, "Isabellawalked"):** Gemma with blind transcription at 1024 px
**missed** it — it read "Isabella walked" (inserting the space itself); at full size and at 768 px it
found it; with a hint (the model sees what should be there) it found it at every size. **Summary across
13 pages:** Gemma with a hint, plus the program checking its transcribed text — 6/6, 0 false positives at
every size (~3.5–4 s per page, ~20–25 s for a whole book run in parallel). Blind transcription alone —
5/6 at 1024 px. The design chosen for the program: a hint, plus the program's own comparison. The owner
decided to drop Qwen (2026-09-19) — it isn't used.

**Cut-off text** (the owner made two pages: text running off the right edge — "we held y…", "laughte…";
off the left edge — the name "Olivia" disappearing entirely): Gemma found both, in all 6 variants (blind
and with a hint; 2000, 1024, 768 px). With a hint it also explains: "the name is completely missing",
"the word is cut off". Blind transcription sometimes "completes" the cut-off word ("laughte" →
"laughter"), but still flags the page anyway, because of the other losses.

**The GPU (2026-09-19):** both models run 100% on the GPU (CUDA), 90–100% load, ~2.8 GHz, 160–195 W of
220. Gemma writes at ~54 tokens/s — close to the 4070 SUPER's memory-bandwidth limit. Qwen reads a
picture at its native resolution (far more "chunks") — hence slower and louder; Gemma downsizes it to a
fixed size (~512 tokens per page). **Parallel processing:** the owner turned on
`OLLAMA_NUM_PARALLEL=4` (a user variable) — 6 pages went from 11.1 to 4.6 s, the whole test (12 pages, 4
at a time) took 10.3 s with the same 5/5 result and no false positives; Gemma then takes ~9.2 GB. The
program should send pages 4 at a time.

**What's needed before building this:** reference texts in the library (without them — a lighter check:
placeholders, the name, the dedication); an accuracy check against 5–10 real past orders with
deliberately damaged copies.

### What this could look like in the program (an agent's thoughts, 2026-09-19; built that same day — see [text-check.md](../features/text-check.md))

The owner wants a real program feature — a "check button", a strong one — not an agent doing the work.
- **Where:** the order card, step 2, "Proofing". The check starts on its own as soon as the Canva files
  are laid out (in the background, ~15 s per book), plus a "Check again" button.
- **Result:** a summary line above proofing — green "everything matches", red "N mistakes", yellow "N
  questions" (a possible deliberate edit); colored marks on the spread filmstrip; a list of problems in
  Ukrainian ("Page 7: "Ollivia" instead of "Olivia""), a click opens the page in the viewer, next to
  "what was printed / what should have been there" with the difference highlighted; "Not an error" —
  clears a deliberate edit.
- **"Print"** with red mistakes present asks "Print anyway?" — it doesn't block it.
- **Reference:** the book's texts from the passport (`{Name}`, `{Gifter}` from Etsy), the dedication —
  from the Etsy field. As of 2026-09-19, texts existed for 5 of the 9 library books (Flower Girl, First
  Bible Stories, Airplane Bedtime, Baptism Storybook, Ocean Animal); for the rest — a **light check**:
  the name is correct everywhere, no other names or `{…}` remain, the text isn't cut off, the dedication
  matches Etsy. Which page matches which text is worked out by the program itself (it reads every page
  and matches them).
- **Under the hood:** Gemma in Ollama, 4 pages at a time, shrunk copies, the "hint + program comparison"
  design (the hard test above); Ollama not running → "Start Ollama"; a fallback — Gemini (a key exists);
  a checked page isn't checked again until the file changes; a check journal, modeled on the send
  journal; the model and the on/off switch — in Settings.
- **Steps:** 1) a light check with the full interface; 2) a full one with references; 3) fill in the
  texts of the 4 remaining books.
- **Open questions for the owner:** check right away or by button; warn or block printing; does he edit
  the story's text per order (how strictly to check); should the cover be checked too; fill in the
  remaining books' texts, or keep the light check for now.

## Pages without Canva (an idea from 2026-09-19)

- **As envisioned:** once per book, mark in the passport where the text goes on each page (a rectangle,
  font, size, color, a shadow or glow). Then, for every order, the program fills in the name, the
  dedication, and "from whom" from Etsy itself, wraps lines and shrinks the font for long text, and
  draws the pages at full size (sharp text — no upscaling needed). For rare awkward cases — a simple
  editor in the card: drag the text block, resize it. Right after — a Gemma check.
- **Dedications with the local model (the owner's wish):** break a long dedication into lines by
  meaning; **suggest** fixes for the buyer's typos (never change them itself); if the buyer picked
  "DEFAULT" or wrote nothing, offer a few warm dedication options to choose from.
- **Order (the owner's preference):** start as a separate experiment first — an agent suggests a "lab"
  inside Book Studio (using the library and Etsy, but not touching the order card or printing); if it
  goes well, wire it into the pipeline.
- **Tool research (2026-09-19):** Canva runs in a browser and on Linux; auto-filling Canva via API needs
  Canva Enterprise (ruled out); Photopea has "variables" (text layers ← CSV → PNG in one click) and
  scripts; Scribus 1.6 + ScribusGenerator (`%VAR_name%` → PDF/PNG); GIMP 3 and Inkscape have scripts;
  Penpot has an API but no auto-fill; Polotno is a "Canva-like" editor with server-side rendering, paid
  for business use; Affinity is Windows/Mac only. **The agent's recommendation:** a custom renderer
  inside Book Studio (an HTML/SVG template via the built-in browser: any fonts, shadows, glow, a curved
  caption). Fonts: the ones from Google Fonts used in Canva are free; Canva Pro exclusives are only
  usable inside Canva (worth checking which fonts the books actually use). Moving to Linux: Ollama and
  Upscayl both run there; Book Studio itself would need work (the Windows key store, the Edge window,
  the shortcut).

## Etsy listings

- **Mockups for a listing — the "Mockups" utility — BUILT on 2026-09-23** ([features/mockups.md](../features/mockups.md);
  agreed the same day, the idea dates from 2026-09-19; plan and templates — [listing-mockups.md](listing-mockups.md)).
  **Moved into Book Studio on 2026-09-24** — the Listings mode ([plan](listings-mode.md)). Left: the owner
  tries it on a real demo book (the back/spine crop by eye, the file names). Right now, for every new book, the
  owner makes a demo book in Canva (a cover with a sample name, pages with `{Name}`), then fills 6 mockup
  templates in Photoshop by hand (~10 pictures: `2. Open 1` four times and `3. Open 2` twice with
  different spreads).
  - **What was agreed:** a **separate utility** first, with its own window; later it moves into Book
    Studio. The owner drags in the Canva ZIP and clicks 8 "presentable" spreads; the script fills the
    pages, the spine and the back cover everywhere (and the front cover's thin rim in the open-book
    templates), saves 7 pictures as PNG into a folder he picks each time, and leaves the 3 templates with
    a visible front cover open — **he fits the front cover by hand** ("the cover sells").
  - Templates: `D:\Roman\Desktop\Трафарети мастхев` — **read-only** (the owner's rule,
    [security](../security.md)); the script only ever opens copies. Replaces the old sample folder
    `D:\Roman\Desktop\Photoshop demo\Prep`.
  - Photoshop — **CC 2019 (20.0.5), portable**: the launcher `…\Portable Adobe Photoshop\Photoshoр.exe`
    (Cyrillic "р"; the 918 MB `Adobe Photoshop CC 2019 (20.0.5.27259) Portable by XpucT.exe` one level up is
    the package it came in, not a launcher), the program itself
    `…\Portable Adobe Photoshop\App\Photoshop\Photoshop.exe`; ExtendScript scripts
    (`.jsx`). **Checked on 2026-09-23:** a script launched from outside runs (after a "run this
    script?" confirmation), and filling the templates by layer name + saving PNGs works — 11 s for two
    templates; details on the plan page.
  - Not part of it: `Cover.png`, `Shelf.png`, `Size.jpg` from the same folder (the owner's examples for
    a diffusion model).
  - Later, together with "Pages without Canva": the program draws the demo book itself, the utility makes
    the mockups.
- **Two modes and the Workshop — BUILT on 2026-09-24** ([plan and agreements](listings-mode.md),
  [modes](../features/modes.md), [workshop](../features/workshop.md)): the brand icon switches between Orders
  and Listings (cyan; Orders turned orange the same day); the Workshop holds books in development — a prompt, a 2:1 spread and a text per row,
  prompts and texts from one JSON, pictures dropped one per frame — and passes a finished book to the library
  with its Etsy listing. The owner said the Listings mode's library "will be modified a bit" later; next steps
  are his to name (e.g. a way back from the library to the Workshop, the listing's own texts).
- **The listing's texts by the local Gemma — maybe** (2026-09-25: the owner asked whether Gemma can
  cope). *The agent's estimate:* the size is fine — the input is the book's 17 texts plus an example listing
  (a few thousand tokens; Ollama's context has to be raised from its small default), the output — a title,
  13 tags and a description (~600–900 tokens, ~15–20 s at ~54 tokens/s). The weak spot is quality, not
  size: a 12B model knows nothing of Etsy search, and the tag rules (13 tags, ≤20 characters) the program
  would check itself. *Before deciding:* a test on 2–3 existing books against his real listings (read-only).
- **Not wanted** (2026-09-25): a demo book drawn from the Workshop instead of Canva — Canva takes little
  time and needs a human eye for the aesthetics; a check that a character looks the same on every spread —
  he checks the generations himself ([decisions](../decisions.md)).

## The Workshop

- **A dropped spread is cut, flipped and upscaled at once** (the owner, 2026-09-25: "I drop a page, it's
  cut, flipped and upscaled at once" — "a top feature"). Today a drop already cuts and mirrors
  ([workshop](../features/workshop.md#a-spread-becomes-two-pages)); the upscale would be the third step,
  so the library gets print-ready pages. *To work out when it's started:* which Upscayl (its command-line
  engine runs without a window) and model he uses, the target size (4000×4000 per page, like Printify),
  where it runs (in the background after the drop, the frame showing its progress), and the graphics card
  shared with the text check's model.

- **Ideas of 2026-09-25:**
  - ~~A live bridge to `Etsy-Book-Pipeline`, catching downloads~~ — **built on 2026-09-26**:
    [the book console](book-console.md), a prototype first, then moved into the [Workshop](../features/workshop.md)
    on the branch `book-console`.
  - **Tier H orders** — the order card shows the buyer's chosen look and copies a ready hero-swap
    prompt (from the pipeline's archetype blocks); later, with one look per hero, every variant made once
    in the Workshop and the order takes the right set.
  - **Listing photos** — the pipeline's `Listing prompts` (flat lay, shelf, a mother reading) offered
    with the book's cover on the Mockups page, to copy into ChatGPT (it downloads JPEG).
  - **Turned down:** generating through an API ([decisions](../decisions.md)).

## Printers

### The owner's own Gelato account — a smooth switch (agreed 2026-09-27, not built)

> **Until this is built, the Gelato key in Settings is not replaced.** The owner opens his own Gelato account
> about 1 October 2026 (the current one holds other people's orders too); this has to be ready before he switches.

- **Why.** The program knows one Gelato key, and every sync replaces the Gelato list with what that account returns
  (`sync._gelato_part()`). After the key is swapped, the old account's orders are gone from it:
  - the queue: an order printed through the old account and not yet marked shipped on Etsy falls back to «нове»
    and loses its tracking (`stages.order_stage()`);
  - **the archive would delete those books' files**: a print order missing from its printer's list, loaded whole
    `VANISH_DAYS` (2) after sending, is "dropped", and the book goes `DROP_DAYS` (3) later (`archive.standing()`,
    `archive.clock()`);
  - Profit: those sales lose their cost (it matters for October sales printed through the old account).
  Not touched: Etsy, Printify, the library, the Workshop, the mockups, Printify's books in the archive; the orders
  themselves stay in the old account at Gelato.
- **What was agreed** (variant A — the owner: "the smooth switch, it'll be more convenient"):
  1. *A safety net, always on.* A Gelato order the program already knew is never dropped because a list lacks it:
     it is kept with its last status, tracking and cost, marked with its account. The archive never deletes a book
     because its order vanished after an account change.
  2. *Two keys for the transition.* Settings → «Перейти на новий акаунт Gelato»: the owner pastes the new key; the
     program moves the current one into «Старий акаунт (лише читання)» itself, inside the vault (no agent sees
     either key, none goes through the chat). Every sync reads both accounts; each order knows its account; its
     tracking is read from that account. Everything new (the Order Creator's drafts, reprints) goes only to the
     new account; with the old key the program can only read (an allow-list of its own: searches and reads).
     When every old-account order is delivered and its archive days are over (about 3–6 weeks), the program says
     the old account isn't needed any more, and the key can be removed.
- **Checks:** tests with two made-up Gelato accounts — a switch in the middle of work; an old order shipped after
  the switch; the archive keeps its books; the new account unreachable; nothing can be created with the old key;
  the interface on the preview server. The only real step is the owner's: he pastes the new key in Settings.
- **Reminders:** the owner asked to be reminded now and then — a scheduled task «Нагадування: перехід на свій
  Gelato» (Mondays and Thursdays, 10:00; it only reads this page and reminds). Stop it once this is built and the
  switch is done.

## Accounting

- **Turn on "Profit" on 1 October 2026** ([recipe](../recipes.md)).
- **A clean slate on 1 October** (the owner, 2026-09-25: "so that accounting pulls nothing before
  1 October — not even a request for that data; serious work starts then"). *What was found:* accounting
  makes **no requests of its own** — the one sync (Etsy receipts, Printify and Gelato orders) feeds the
  order queue, the tracking and the archive, and has to stay. Accounting's own part is local: the fees,
  matching (`reconcile.match()`), states, `profit/print-orders.json`. So a clean slate means: accounting
  counts only receipts from 1 October on, and nothing before is matched, shown or stored for it (the
  debts in [open questions](open-questions.md#technical-debt) about older receipts then stop mattering).
  To agree with him before building: whether the queue keeps showing older orders as now (it should).
  Confirmed by the owner on 2026-09-27: "it must not include earlier orders at all". Not built yet.

## Infrastructure

- ~~Automatic backup of the whole program to Google Drive~~ — **built on 2026-09-27**: [features/backup.md](../features/backup.md).

- Running tests automatically on GitHub (GitHub Actions) — possibly; the `gh` token already has
  `workflow` permission.

## Related

- [Open questions](open-questions.md) · [Decisions](../decisions.md) · [The order path](../flows/order-to-print.md)
- [Listing mockups](listing-mockups.md)
