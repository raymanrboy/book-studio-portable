---
title: Decisions
type: decision
updated: 2026-09-24
code: []
---
# Decisions

> What was decided, when, and why. Before "fixing" something odd in the code — check whether it's a
> deliberate choice by the owner. Newest decisions are at the top.

## 2026-09-24 (later) — The inks swapped: Orders orange, Listings cyan

The owner, after the modes were merged: "make the Workshop's colours what the Studio has now, and the Studio's
like Etsy and Claude — orange". So the **Listings mode wears the cyan** the whole program had until now, and
**the Orders mode is orange** (`#bf4f1a` light / `#f0874d` dark; Etsy's own `#F1641E` and Claude's `#D97757` are
too light for white text on a button — 3.2:1 — so a deeper shade of the same orange: 4.8:1 and 7.0:1). The dot
of a mockups run going on elsewhere is cyan now (the Listings' ink). This replaces "The Listings mode is
magenta" below; the orange sits close to the Etsy chips and a little closer to the amber warnings — the owner's
choice, the warnings stay amber.

## 2026-09-24 — Two modes: Orders and Listings; the Workshop; the mockups move into Book Studio

The owner: "Book Studio will have two modes — working with orders and creating listings", switched "by a
click on the main Book Studio icon", the second one "like another program, separated from everything".
The agent's plan was approved without changes ([plan](plans/listings-mode.md), his words in
[raw/](raw/2026-09-24-listings-mode-owner-answers.md)).
- **The Listings mode is magenta** (changed the same day — see above: Orders orange, Listings cyan), its own
  icon and rail items (Майстерня, Мокапи). Reason: the owner picked it; magenta is the logo's second ink, and
  neither the Etsy orange (already a service colour, close to the amber warnings) nor the same cyan would tell
  the modes apart at a glance.
- **Book Studio always starts in Orders** (the owner's answer); each mode remembers its last page until a
  restart. The mode comes from the page's address, so back/forward just work.
- **The Workshop, not a second library**: "a place where I create books before sending them to the library
  with orders". A book there is a row of cards — prompt, 2:1 spread, text — of moderate width; pictures come
  last, one at a time into placeholders. Reason: the owner's own words and layout choice.
- **A Workshop book is a library book with `"stage": "workshop"`**, and passing it to the library only
  removes the mark and writes the listing. Reason: nothing is copied (hundreds of MB), the library's tested
  machinery serves both, and the order side never sees Workshop books because the book list excludes them by
  default.
- **Passing a book on needs its Etsy listing** (checked read-only through the API; unchecked without keys) —
  the owner's answer: the library is what orders match against. One way for now; the prompts stay in the book
  so a way back can be added later.
- **A picture that isn't 2:1 is taken and marked**, not refused (the agent's call: the owner said 2:1 is
  important; a mark shows a mistake at once, while an intended other shape isn't thrown away).
- **The mockups stay as they are** ("Ні, як зараз" — not tied to library books) and move inside Book Studio;
  the separate utility and its shortcut go. **Its demo book gets a folder of its own**: the utility wiped all
  dropped files when a new book came in — inside Book Studio that would remove an order's dropped files.

## 2026-09-23 (evening) — Drive C stays clean; «Мокапи» cleans up after itself and looks like Book Studio

The owner, after his first real run: "are there many temporary files, is there a message when it's done?",
"make the drop zone exactly like Book Studio's, with the search; improve the UX, be creative", and "it's
very important to keep drive C clean — any temporary file must be removed when the work is done".
- **Nothing of the programs' goes to drive C.** Book Studio and «Мокапи» set `TEMP`/`TMP` for themselves and
  everything they start to `<data folder>\tmp\system` on D and empty it on launch and close
  (`core.own_temp()`); a Photoshop started by «Мокапи» gets `tmp\photoshop`, emptied once Photoshop is
  closed. Reason: the Edge window left its logs in `%TEMP%`. The tests and the preview servers moved from
  `%TEMP%` to `.tmp\` in the repository; the tests' wipe was fixed (an open log file blocked it — 177
  leftover folders were removed from `%TEMP%`, with the agents' own leftovers there).
- **A run's leftovers go as soon as nothing can need them**, not "after a day": the prepared pictures right
  after the script, the copies of the templates left open — after «Зберегти відкриті», or at once when
  Photoshop is closed (checked on launch, before a run, on close); a day is only the limit while
  Photoshop stays open. **Exception:** a copy the owner saved himself (Ctrl+S lands in the run folder) is
  kept a week — his work is never deleted quietly. One demo book at a time (the one before goes when
  another comes in, and on close).
- **«Зберегти відкриті й закрити»** — the "save the open ones" script offered earlier, now built as an
  optional button: after fitting the front cover, one press saves the three as PNG next to the rest
  (same naming, never overwriting) and closes them without saving the copies. A second "Yes" in Photoshop
  (one per script). Saving them by hand still works. Reason: it ends the workflow in one place and lets the
  copies go at once.
- **"It's done"**: when a run ends while the window is behind (the owner watches Photoshop), its taskbar
  button flashes, Windows plays its notification sound, and the title says «Готово · 7 картинок». Not a
  Photoshop pop-up: a modal message there would block the second script.
- **The look of the Order Creator**: four numbered steps on the left (book — the path field with the
  folder button and a status badge, the drop anywhere on the window; spreads in templates — with each
  template's own preview read from its PSD; where to save; Photoshop), the book's structure on the right.
  Clicks fill slots in order; dragging a spread onto a slot, and slot onto slot, works too. The book comes
  in either by drop or by the Windows dialog for a ZIP (unpacked straight from Downloads, only read).
- **The output folder is still picked for every book** (the owner's rule): a new book starts with it empty;
  «Та сама, що минулого разу» takes the last one in one click. The picks of a book are remembered by the
  window (the last 12 books) and come back when the same book is dropped again.

## 2026-09-23 — The «Мокапи» utility built: how, and what was chosen along the way

The owner said "build it" ([features/mockups.md](features/mockups.md)). Choices made while building —
not asked of the owner, easy to change if he wants otherwise:
- **A program of its own with its own data folder** (`app/data/mockups`, port 47831, shortcut «Мокапи»):
  it loads only the mockups and the dropped files, so it never touches keys, orders or the library, and
  Book Studio's launch never wipes a book dropped into it. Moving it into Book Studio later is a route
  and an import (the page already has the usual `mount()`).
- **The dropped-files code moved into its own module `drops.py`** (with Canva's naming rules:
  `export_files()`, `page_number()`, `COVER_NAME`), and the routes became `/api/drop/*` instead of
  `/api/creator/drop/*`. Reason: the utility needed them without the Order Creator and everything it
  imports. Book Studio's behaviour is unchanged (its tests pass as before).
- **File names** `2. Open 1 (6-7).png`, `4. Dedication.png` — the template's own name (the owner's
  numbering sorts them) + the pages; never overwriting an existing file (` (2)`). The owner hasn't
  confirmed the names.
- **All six templates are copied on every run** (the agreed "a copy, even for an accidental Ctrl+S"); it
  costs <1 s on this PC. The copies of the automatic ones are deleted right after the run; the three left
  open stay a day (in case he saves the fitted cover there), then go.
- **One script per run → one "Yes"** in Photoshop; turning the question off stays the owner's choice.
- **Stop is safe at any moment**: a stop mark the script reads first, so a late "Yes" does nothing.
- **"Fill and centre"** for the back, the rim and the spine, as planned — to be tuned on the first real
  demo book.
- Output starts in the folder picked last time (only the dialog's starting point; he still picks every
  time).

## 2026-09-23 — Listing mockups: a separate utility, the front cover stays manual

The owner described how he makes listing mockups in Photoshop and answered the agent's questions
([plan](plans/listing-mockups.md), sources in [raw/](raw/2026-09-23-mockups-owner-answers.md)). Nothing
was built yet (built the same day — the entry above).
- **A separate utility first**, with its own window; it moves into Book Studio later. Reason: the owner
  wants to try it on its own before it goes into the main program.
- **The front cover is fitted by hand** in the three templates where it's visible (`1. Cover 1`,
  `Cover & Open 1`, `All & Open 1`). Reason, his words: he's "pixel-perfect", "the cover sells". Don't
  "improve" this with auto-fitting unless he asks.
- **Automatic:** the spread pages, the spine (the middle strip of the wide cover) and the back cover (its
  left half) in every template; in the open-book templates also the front cover's thin rim (agreed — a
  white left rim next to a colored right one would look wrong).
- **The spreads are picked by the owner every time** (Open 1 ×4, Open 2 ×2 — different spreads), not a
  fixed table.
- **Output — PNG, a folder picked every time.**
- **The templates folder `D:\Roman\Desktop\Трафарети мастхев` is read-only** — the owner's rule
  ([security](security.md)); the script works on copies.
- `Cover.png`, `Shelf.png`, `Size.jpg` in the same folder are out of scope (the owner's examples for a
  diffusion model).

## 2026-09-23 — Own audit of the `audit-fixes` branch: everything fixed except accounting

After his own audit of the branch (42 findings; the report lives outside the repository), the owner
decided: **accounting (the "Profit" page) — later, fix everything else**.

**Changed behavior that shouldn't be "fixed" back:**
- **"Update passport"**: the child's name becomes `{Name}` only as a whole word, and only where the old
  passport had `{Name}`; before saving, the owner sees the text exactly as it will be saved. Reason:
  "Eve" turned "Every" into "{Name}ry", and a broken passport went on hiding the same mistake in new
  books.
- **The archive only deletes a book that "never became an order" based on a fresh list from its own
  printer** (`loaded` in the snapshot). Auto-deletion (decision 2026-09-18) stays; only what the program
  trusts has changed. Reason: 5 days of Gelato failing while Printify stayed up wiped the files of a
  book that had already gone to print.
- **An unknown result when creating at the printer ≠ a failure**: for Gelato — "don't resend, check
  Drafts", the PDF link stays valid for 15 minutes (as for a successfully created draft).
- **A POST that might have gone through is not retried** (a timeout, a dropped connection, 500/502/504)
  — including uploading an image to Printify. This **changes** the 2026-09-22 decision "kept the upload
  retry": the retry now stays only for cases where the request definitely didn't go through (a rejected
  connection, 429, 503) — there are no duplicates in the media library, and on a bad connection the
  upload still survives drops before sending.
- **The receipt number is its own field on the book**, not just the start of its name; a name with a
  **different** number is rejected at upload.
- **The preview server takes no keys** (doesn't show keys from old programs, doesn't save new ones).
- Dialogs and messages sit **above** the page viewer; library import — one set of rules for the button,
  a folder, a ZIP, and files; the card and the text check read "own text" and the child's name the same
  way.
- Also did what was deferred on 2026-09-22 as "not noticeable": a closed page stops polling jobs; the
  queue refresh is one function shared by Orders and the Order Creator.

**Deferred together with accounting (the owner's decision):** the cost of a second print order
disappears when the first one is cancelled (`outcomes.apply()` after `_further_orders()`); three
functions rewrite the same money fields in turn; Gelato orders in CZK are counted as USD (there are 5 of
them in the data); the cover type in the "Profit" table is guessed from letters in `orderReferenceId`;
four different sets of rules decide "live / placed order", and the accounting still counts "on hold" and
unpaid ones, against the 2026-09-18 decision.

**Deliberately left as is:** a folder import saves the book after every picture (so each one appears
right away, and a failure doesn't lose what was already imported); `Image.MAX_IMAGE_PIXELS` is raised for
the whole process (large, but the owner's own files); settings are read when the module starts; routes
are declared next to their section's code. There are no browser tests: interface layers and preview
sizes are checked by a test that reads the page files directly; the rest of the interface — by preview
on the test server.

## 2026-09-22 — What exactly to fix from the external code audit

The owner's colleague sent over a large code audit (17 findings) and separate interface recommendations.
The findings were checked against the code one by one — confirmed. Fixed what affects the owner's work
or money; the rest was deliberately **not** touched.

**Done:** the text check belongs to the book, not the receipt; "Undo" reads state from disk; tests and
the preview server can't reach real data; an accounting error after a successful send is no longer
silent; the book is recorded before its file is deleted; a receipt can have several print orders, and
all of them are counted; a page can't be swapped out during a send; the wiki check catches stale
numbers.

**Deliberately not done:**
- **Rebuilding the "receipt → books → print batches" model**, which the interface document recommended.
  Too costly for the owner's reality: orders with several books are 10%, and it's usually the same book
  for different children — one printer, one draft, where the current model is correct. A narrow
  accounting fix was chosen instead.
- **Kept the Printify image-upload retry** (`retries=3`): a duplicate image in Printify is almost
  harmless, and on 4000-pixel files the retry helps. Creating the product and the order, where a
  duplicate is costly, still has no retries, as before.
- **Polling jobs after a page is closed, duplicated code between Orders and the Order Creator, clearing
  old jobs from memory** — not noticeable in a local, single-user program.

**An order's stage** (`order_stage()`) is still computed from a single, first print order: if one book
of a receipt is sent and the other isn't, the receipt is already off "New". The "+N in print" chip
shows this, but doesn't change the stage itself — left for discussion with the owner.

## 2026-09-20 — A fixed page is replaced from the viewer, not by dragging

- **The owner's task:** the check found a mistake, he fixed it in Canva, downloaded one page — and
  wants to replace just that one, without redoing the whole book. Dragging the file onto the "Files from
  Canva" row was the first idea discussed.
- **The owner's decision:** do it **in the viewer** — open the page, press a button, pick a file.
  **Why this is better:** with dragging, the program would have to **guess** which page the file
  replaces (a number from the file name; the "Canva number → print number" offset, which is uneven for
  Printify because not every page in sequence gets downloaded; comparing pictures; plus a confirmation
  dialog). In the viewer, the page is defined by what the owner is looking at — nothing to guess.
- **Details he chose:** two buttons per spread (one per page), not one with a question; there won't be
  such a button on a text-check finding's row; it's needed both in the order card and in the Order
  Creator.
- **Built the same day** — [features/orders.md](features/orders.md). The old page goes into a hidden
  `.replaced` folder (that's where "Undo" pulls from), the picture's address gets a new number (previews
  are cached for 10 minutes), the files are re-checked, the text check re-asks the model only about this
  page, and its "not an error" marks are forgotten.

## 2026-09-20 — The model is only shown pages that might have text

- **Noticed by the owner:** "we're loading every picture into the model — why? we only have text on 16
  pages." True: the model was reading all 28 pages of a story just to work out where the text was.
- **Decision:** before the model runs, the program itself looks at every page (the 360 px preview
  already made for the filmstrip) and measures how much "ink" is gathered into rows: text is thin
  strokes in a few narrow rows, a picture is spread evenly across the whole page. Three marks: `text`,
  `picture`, `unsure`.
- **The mark never decides on its own:** `unsure` still goes to the model, as before; a spread that
  looks entirely empty is still read by the model; and if a page sent straight to comparison turned up
  no writing at all in the model's eyes, the other half of the spread is checked too. A switch lives in
  Settings.
- **Measured on real books** (all 5 from the archive): text 2.4–2.6, picture 0.9–1.5; on two books with
  a check journal, the list of pages matched exactly what the model itself found. Time: 39.7 → 24.4 s
  (30 pages), 44.8 → 33.6 s (24 pages), 40.3 → 30.9 s (a complex book) — the same problems found either
  way.
- **Why not guess from the layout** (text-picture alternating by page): in a 24-page book some spreads
  are missing, and the alternation breaks down; the mark looks at the page itself and doesn't depend on
  that.
- **Fixed along the way:** a bug introduced that same morning together with the reading pipeline:
  `setdefault()` created an extra request to the model every time, before checking whether the page was
  already being read — a book was read almost twice (56 requests instead of 29). Because of this, the
  check had temporarily become ~40% longer.

## 2026-09-20 — Several books in one receipt — one draft to one address

- **Requested by the owner** ("so several books in one order go into a draft for one address"). He has
  7 orders like this out of 69 (2–5 books; usually the same book for different children, always the
  same cover type, i.e. one printer). Before this, the program could only handle one book at a time —
  the owner had to place two orders at the printer, meaning **two deliveries**, and the accounting only
  ever saw the first of them.
- **How:** Printify — one product per book (they differ: a different name on the pages) and **one**
  "On hold" order with a line item for each; Gelato — **one** draft with an `item` for each book, each
  with its own PDF on a shared temporary link. The shared order's name is `<receipt> - Emma, Liam` (the
  receipt number first, so sync can find the receipt).
- **In the card, each book goes through the path separately** (folder, comparison, text check); the
  switcher just shows a different one. "To print" takes every ready book from the same printer; if not
  all of them are ready, it asks rather than blocking (the rest can be sent later as a separate order).
- **Why not mix printers:** the cover type decides the printer, and orders at different printers are
  different shipments. If a receipt has mixed types, the books go as two orders, and the "Print" step
  says so.

## 2026-09-20 — Text check: findings as the check runs, and warming up the model

- **Requested by the owner** together with the previous item ("do the first and the second").
- **Findings appear in the card as soon as a page is checked** (`Job.share()` → `partial` in the job
  snapshot), and a spread goes to comparison right after its two pages are read — in a book where
  spreads match the passport (30 pages). A shorter book (24/28) is missing some spreads, and matching
  needs all the readings — there, comparison still starts after reading finishes, as before.
- **What this gets:** the first mistakes are visible ~3–5 s before the check finishes; the check's total
  time barely changed (the model still does the same work) — the point is that the owner sees the
  problem sooner. To be honest: the "5–10 s" savings promised in the plans didn't materialize — the
  queue to the model was already full.
- **Warm-up:** as soon as the card takes in the files, the program asks Ollama to load the model onto
  the graphics card while the server copies and checks the PNGs. This is the real saving: usually 4 s,
  up to ~70 s if the model isn't yet in the computer's memory. The model still gives up the graphics
  card right after the check (decision 2026-09-19).

## 2026-09-19 — Smoothness: the graphics card, kept cards, the preview cache

- **Assigned to the agent** after a code review (the owner: "stopped feeling as smooth… go ahead and
  fix it").
- **The model frees the graphics card right after a check**, not after 5 min: it holds ~9.2 of 12 GB,
  and the Book Studio window is drawn by the same card. Reloading from memory takes ~4 s (measured), so
  the cost is small.
- **The check stops** when the card is closed, its files are replaced, or another book is picked; a
  hidden card (another tab) does not stop it — its work has to run to completion (the owner's wish,
  2026-09-18).
- **Idle cards** (no files, no draft) are kept for only the three most recent; cards with work in
  progress stay as before, until the order leaves "New".
- **The preview cache** is cleared on startup: anything not needed for 21 days is deleted (it isn't the
  owner's data — previews are made again when needed).
- **Not changed:** walking a card's elements on exit (`swap()`) and reading `scrollLeft` in
  `smoothWheel()` — these cost fractions of a millisecond; larger rewrites (`creator.py`,
  `reconcile.match()`, the order card) — only after discussing with the owner.

## 2026-09-19 — Text check with a local model: where it sits in the pipeline

- **Assigned to the agent** (the owner: "think it through properly… work out the feature that fits the
  pipeline best, and go for it"). Answers to the open questions from the [plans](plans/roadmap.md):
  - **Right away, not by button**: the check starts on its own after the file check — the owner watches
    the comparison for those 20–50 s anyway; ↻ — check again.
  - **Warn, don't block**: "To print" asks "Anyway?" if there are red findings or the check is still
    running. The model can be wrong — the last word is the owner's.
  - **How strict:** the cover and spreads — word for word against the passport; the dedication and
    afterword — looser (the owner adjusts these, differences are yellow); the child's name and `{…}` —
    always red. The buyer's own dedication — the model checks it against the buyer's words, in yellow.
  - **The cover** is checked (the front half — strictly, the back — if it has text).
  - **Books with no reference texts** — a light check automatically; the full one — where texts exist.
- **Local model only** (`gemma4:12b-it-qat`), no Gemini: free, no limits or "503"s, pages with
  children's names never leave the PC (Ollama's address is 127.0.0.1 only). Qwen isn't used (the
  owner's decision that same day).
- **The program starts Ollama itself** if it isn't running; the model frees the graphics card after 5
  min — so Upscayl gets its memory back.
- **"Update passport"** — because on 2 of 3 real books the passport had drifted from the Canva template
  (headings, a different cover, verses in a different order), and without this it would show red on
  every single order. Only on the owner's click, only the cover and spreads, name → `{Name}`.
- The model's answers are cached only in memory (a restart forgets them); "Not an error" lives only in
  the card. The check journal — like the send journal (`data/logs/checks/`).

## 2026-09-18 — Gelato: order name, a made-up phone number, the 5" × 5" format

- **The Gelato order name (the owner):** `receipt number - name`, like the book's name and how the
  owner names his own manual orders (was `<receipt>-<session>`).
- **Phone number (the owner):** Gelato won't let an order be placed without one, and Etsy doesn't
  provide it — a made-up `+1 555 555 0100` is used; this is standard practice. Printify wasn't changed
  (it works fine without a phone number there).
- **Format:** in Etsy the small softcover is called `5" × 5" Softcover`, and the rule was looking for
  "5.5" — so the Order Creator was offering Softcover 8×8. Now `5" × 5"`, "5.5", "14 × 14" all →
  Softcover 5.5×5.5.

## 2026-09-18 — Only a placed and paid printer order is counted

- **Decision (the owner):** a draft, an unpaid, or a cancelled order in Printify / Gelato **counts
  nowhere**: it doesn't move an Etsy order to "In progress", doesn't put the book in the order archive,
  doesn't make the next send a reprint. **Why:** the program was treating a cancelled order as already
  printed, and a new send became a "reprint".
- **How (the agent):** `profit.is_placed()` — Printify: not `on-hold` / `pending` /
  `payment-not-received` / cancelled; Gelato: `orderType: order`, paid, not cancelled. A draft leaves
  the receipt in "New" with a printer-status chip, so it isn't sent twice. The archive saves the files
  at the moment of sending, but only shows the book once it's paid; a cancelled or deleted draft is
  removed after 3 days, and until then its files can be picked up in the order card ("Take files from
  the last send") — it's treated as a regular order. A reprint is only made from a book that was really
  printed; a reprint that never became an order clears the "replacement" mark.

## 2026-09-18 — Gelato: Page 0 stays; blank pages at 300 dpi

- **The owner's question:** why does a Book Studio order have a blank "Page 0" that the "correct" order
  5d72fd05 (2026-09-15) doesn't — should the blank pages be removed from the PDF?
- **Found out:** the "correct" one was made by the old Order Creator, but the book went through Gelato's
  own editor (`designId`, the product was rebuilt, Gelato made the PDF itself). The printed PDF has the
  same structure as ours (cover · blank · pages · blank); Page 0 is the white inside of the cover.
  Without the blank pages the book shifts (checked 2026-09-17) — **don't remove them**. The owner
  checked the old method (cover and pages as separate files) with a test draft on 2026-09-18: Gelato put
  the cover on every page. **Decision:** keep one PDF; Page 0 is normal.
- **Fixed:** the blank pages were 16×16 px pictures, and Gelato judged the whole book's print quality at
  3 dpi. Now they're a white 300 dpi picture, like in Gelato's own PDF
  ([integrations/gelato.md](integrations/gelato.md)).
- **A reprint of an order cancelled at the printer** is not marked as a replacement: it's now the only
  live print order, it's matched normally, and the receipt moves off "New"
  ([features/archive.md](features/archive.md)).

## 2026-09-18 — Work on a new order is remembered until it leaves "New"

- **Decision (the owner):** if you switch to another tab while working on an order and come back, the
  program shows the same step — files, comparison, a filled-in Order Creator, even the success screen —
  until the order leaves "New" (shows up at the printer). **Why:** work shouldn't be lost to an
  accidental tab switch; after success the card says "draft created", so it isn't sent twice.
- **Limits:** memory only (a restart forgets it, like the files' temporary copies); an Order Creator
  opened by hand with no order attached still starts empty every time (the 2026-09-15 decision stays
  for that case).
- **Technically:** pages aren't rebuilt from scratch — they're hidden and brought back (`keep.js`,
  [architecture/frontend.md](architecture/frontend.md)).

## 2026-09-18 — Order archive: files auto-delete; the program runs only on the Wrocław PC

- **Decision (the owner):** a book's files in the [order archive](features/archive.md) are deleted
  **automatically 14 days after the order became "Sent"**. This is a deliberate exception to the "never
  permanently delete the owner's data" rule — not something to "fix". A book marked "Don't delete"
  lives on until the mark is removed. The menu is named "Order archive". New orders only; the archive
  lives in the program's own folder, not in git.
- **Why 14 days from "Sent", not from printing:** a buyer notices a mistake once they get the book —
  often 14–20 days after it went to print.
- **Engineering decisions (the owner assigned to the agent):** a Printify reprint is a new "On hold"
  order for the same book (no re-upload; if the book was deleted, it's rebuilt from the archive);
  Gelato — a new draft from the archived files. A reprint is marked as a receipt replacement (accounting
  is frozen — don't tie it in any deeper). A reprint counts its own 14 days from when the reprint itself
  was sent by the printer; a book whose order the program can't trace gets 30 days from when it was sent
  to print. The archive copies the actual files (not a link to the owner's folder), so the archive stays
  a record of what really went to print.
- **Book Studio only runs on the Wrocław PC** — the owner doesn't run the program on the Kyiv one (just
  a browser with Etsy there). The archive, keys, and data live only here; no need to sync between PCs.

## 2026-09-17 — Text check via Gemini: deferred, free tier

- **Decision (the owner):** the idea is recorded in the [plans](plans/roadmap.md), to be built later.
  No paid subscription — the key is the AI Studio free tier. **Why:** the pages only have the book's
  character names and dedications; only pages with text (up to 17) need checking, so the free tier's
  limits (requests per minute / per day) aren't a problem.
- **Worth knowing:** the Gemini API terms forbid sending personal data on the free tier, **but** for
  users in the EEA, Switzerland, and the UK, the paid tier's terms apply even on the free tier (data
  isn't used to improve Google's products). The program only runs on the Wrocław PC (in the EEA)
  ([terms](https://ai.google.dev/gemini-api/terms)).
- **A known risk:** during peak hours the free tier gets "503 — overloaded" more often (2026-09-17 —
  3.8 and 3.7 Flash), so fallback models are needed.

## 2026-09-17 — The "truck" tab, printer status, and the tracking number in the queue

- **Decision (the owner):** a fourth tab between "In progress" and "Sent": the printer has shipped it
  (a tracking number or an "shipped" status), but it isn't marked in Etsy yet. **Why:** always see
  what's already safe to mark shipped in Etsy; once marked in Etsy, the order moves to "Sent" (the box)
  on its own. A `delivered` status from the printer does not move it off the truck. [Stages](rules/order-stages.md).
- **The status shown on the right instead of the child's name** — the printer's own word, in English,
  untranslated, but in a human form ("In transit", not `in_transit`); no separate marks are needed for
  drafts. The child's name — bold, in the grey row after the time.
- **The tracking number** — a chip after the printer's chip, in its color; the carrier and the number
  are both colored, separated by a dash; clicking copies the number. The printer name, the carrier, and
  the number are all one soft tone (the owner: "same contrast, I like the grey version best"). The Etsy
  order number also copies on click. In the card, the status sits next to the recipient's name.
- **Technically:** Printify returns tracking numbers in the order list; Gelato only in the full order,
  so shipped ones are read one at a time, once each (`attach_shipments()`) — read-only.

## 2026-09-17 — A Gelato key from chat doesn't get rotated

- **Decision (the owner):** the Gelato key he pasted into chat stays valid — no need to remind him to
  rotate it. The agent never used it (the program takes its key from its own store) and never wrote it
  down anywhere.

## 2026-09-17 — Gelato: standards from real orders, the send journal

- **Products (the owner):** the program uses the same metric Gelato products the owner picks by hand
  (20×20 cm, 14×14 cm), not the "inch" 203.2 / 139.7 mm ones — those were different products with
  different sizes.
- **The PDF stays "cover · blank · pages · blank".** An attempt to remove the blank pages (the agent
  wrongly assumed Gelato adds them itself) shifted a test book: "1" became Page 0, Page 28 went blank.
  A blank Page 0 in a draft is the endpaper — that's how it should be. Don't remove it.
- **Cover (the owner):** a small amount of trim on the Canva cover is always expected — warn only past
  10 mm, log the rest.
- **Send journal (the owner):** every send to Printify/Gelato is its own JSON file in
  `data/logs/sends/`, to help perfect the mechanism ([features/send-journal.md](features/send-journal.md)).
- **Checking the link** — also over public DNS: the home router didn't know the new trycloudflare
  addresses, and the program was wrongly writing "not confirmed reachable".
- Checked against orders `00cd5172…` (manual, 28 pages) and `5d72fd05…` (via API, 30 pages, printed) and
  two test drafts — [integrations/gelato.md](integrations/gelato.md).

## 2026-09-17 — Gelato: 28 or 30 pages, however many were downloaded

- **Decision (the owner):** there's no separate switch. Download the cover + 28 pages from Canva and the
  book is 28 pages; 30, and it's 30 pages. The owner picks which spread to drop (one, different per
  book) in Canva himself, the same as picking the three spreads for Printify; the program just
  renumbers.
- **Why 28 is even possible:** Gelato's catalog (`validPageCounts`) allows 28–200 for all three formats
  (checked 2026-09-17), even though Gelato's public docs say "from 30". The program doesn't guess — it
  asks the catalog (read-only) and won't let through a book Gelato can't print — in the card, in the
  Order Creator, and before creating a draft.
- **Deliberately not done:** checking that a *whole* spread was removed — Canva numbers files
  differently from book to book (the cover is sometimes first, sometimes last), so automating this would
  give false alarms.
- Details — [integrations/gelato.md](integrations/gelato.md).

## 2026-09-17 — Keys in Book Studio, Etsy OS disconnected

- **Decision (the owner):** the key file `.secrets.txt` lives in the Book Studio root (git ignores it),
  and the Etsy OS folder is no longer connected to work with the agent.
- **Why:** Etsy OS had its `.gitignore` deleted, and the "Commit changes" button in the Claude app could
  have saved the keys into git history; on top of that, Etsy OS's unsaved changes kept hanging around in
  the interface.
- Rules for handling the file — [security.md](security.md).

## 2026-09-17 — The wiki, `app/`, GitHub

- **Decision:** the program moved into `app/`; alongside it, `wiki/` (this knowledge base), and
  `AGENTS.md`/`CLAUDE.md` at the root; a wiki check — a script and a test. A private repository,
  `raymanrboy/book-studio`, branch `main`.
- **Why:** a new agent needs to get up to speed without reading the whole codebase; agreements
  shouldn't get lost between conversations and computers (the agent's memory only lives on one PC).
- **Consequences:** the path to the old programs in `settings_api.py` is computed from `app/`; the
  shortcut was rebuilt; the preview cache is rebuilt once.

## 2026-09-17 — Only made-up buyer data in the repository

- Before the first push, a test turned out to have a real buyer address — replaced with a made-up one.
  Examples in the code and tests — `41000000xx - Emma`, and so on.

## 2026-09-16 — The order card: data on the right, work on the left

- **Decision (the owner):** the data (the book, personalization, shipping) sits on the right and stays
  on screen; the files, comparison, and printing sit on the left. Comparison — the cover and the first
  spread at full width, one above the other. The note — large bold text, no "Cover Type & Size" line.
- **Why:** the data needs to stay in view while comparing; the note's text was nearly unreadable.

## 2026-09-16 — The page filmstrip without "snapping"

- **Decision:** removed `scroll-snap`; a custom smooth wheel-scroll with its own position; 360 px
  thumbnails are prepared by the server right after the file check (from the large 1400 preview).
- **Why:** snap was fighting the programmatic scroll and bouncing back from the end (the filmstrip "got
  stuck at 22–23"); thumbnails were generated on the fly — stutter.

## 2026-09-16 — Accounting cache keyed to a write counter

- **Decision:** the `cached_view()` cache key includes the save counter `_writes`.
- **Why:** two writes within the same Windows clock "tick" had the same modified time — the cache was
  handing back stale data (found through a flaky test).

## 2026-09-15 — Printify: a draft with an address = an On hold order

- **Decision (the owner):** in Printify, as in Gelato, a "full draft" can be created: the book plus an
  order with an address, waiting as "On hold". The finish is always matte. Before the first order — a
  one-time confirmation that the shop has manual approval (Manual) set.
- **Why:** with automatic approval, Printify would send the order into production itself and charge for
  it. The owner's shop is set to Manual (a screenshot).
- **Limits:** sending to production, cancelling, and Express are blocked; with no address, only the book
  is created.

## 2026-09-15 — Orders refresh only on launch and by button

- **Decision (the owner):** one automatic sync when the program starts; after that, only the button.
  Pages don't sync on their own — they only wait for one already running.

## 2026-09-15 — The "Orders" page and the pipeline

- **Decision:** the start screen is the order queue; the card leads through Canva → files → comparison
  → print; the Order Creator stays for manual cases. The printer rule —
  [rules/printer-rule.md](rules/printer-rule.md).
- **Why (from the Etsy OS experience):** there it was "bad at every stage": locking, revisions,
  generations of files. Here — one screen, state from facts, nothing kept in reserve
  ([flows/order-to-print.md](flows/order-to-print.md)).
- Files from Canva are renumbered in order (for the US, 3 spreads are removed → numbers with gaps);
  originals aren't renamed.

## 2026-09-15 — Stages from print orders

- **Decision:** "new" = no order for this receipt yet in Printify/Gelato; "in progress" = there is one.
- **Why:** the Etsy API doesn't return the seller's own "In Production" tab.

## 2026-09-15 — Library: partial import and instructions for an agent

- Any incomplete set of files finds its place. Instructions (file names + text JSON) can be saved or
  copied for an agent; they're built from the import rules, so they never drift from them.

## 2026-09-15 — A minimal interface (the owner's notes)

- The Order Creator starts empty every time (no cache of folders, addresses, or the draft list).
- The Etsy listing is not a link (so Etsy is never opened from Wrocław); Canva is a button.
- Removed: notes and illustration filters in the passport, technical fields in Settings, explanatory
  text.
- Printify — light green, Gelato — blue; the viewer follows the program's theme; "+" in the library
  panel.
- Personalization in the order picker is structured and collapsed; an eraser for the address; dragging
  folders and ZIPs.
- Details — [owner/ui-principles.md](owner/ui-principles.md).

## 2026-09-15 — The server doesn't open Etsy pages

- `_open_url()` blocks etsy.com, except for the login page, which only opens after confirming "I'm on
  the Kyiv PC".

## Before 2026-09-15 — Gelato: one PDF of type `default`

- **Before:** the photo book's files were sent as `inside` — Gelato filled every page with the cover.
- **Decision:** one PDF, "cover, endpaper, pages, endpaper", of type `default`, sized from the catalog.

## 2026-09-14 — Book Studio as one local program

- **Decision:** instead of the Etsy Profit Calculator and the Printify Order Creator, one program: a
  Python server on the standard library + build-free HTML/JS in an Edge window. Profit formulas carried
  over one to one and checked against tests. Keys — DPAPI; Etsy — read-only; Printify/Gelato —
  allow-listed actions.
- **Profit is hidden** until October 1, 2026 (when accounting begins).

## Related

- [How to work with the owner](owner/working-with-owner.md) · [Plans](plans/roadmap.md) · [Log](log.md)
