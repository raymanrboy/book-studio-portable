---
title: Decisions
type: decision
updated: 2026-10-06
code: []
---
# Decisions

> What was decided, when, and why. Before "fixing" something odd in the code — check whether it's a
> deliberate choice by the owner. Newest decisions are at the top. An entry is a record of its day: where it says
> "not built yet", the feature page tells what exists now.

## 2026-10-06 — What not to build next (the owner's answer to «what else could be better»)

- **Not wanted:** order deadlines / Windows notifications, sales analytics «what to make next», a morning summary on the start
  screen, a smarter search (the owner says he does not use search at all).
- **Not now:** the program rendering the personalised pages itself instead of Canva — too much work, and the owner wants to keep
  control; the cover stays in Canva in any case.
- **Liked, then done the same day** ("Все що придумав — роби"): «Скасувати» instead of a question for a Workshop book and a photo
  template — they wait 2 min on the program's shelf (`aside.py`) before the Recycle Bin, so the undo is real (the 2026-09-30 rule «an
  undo the program cannot keep is a lie» still holds: the shelf is what keeps it). Still asking, on purpose: removing a Workshop book's
  Etsy photo (its scenes are rebuilt), keys and Etsy sign-out, a module, re-making slides, putting a scheme over six slides, the send.
- **Search removed from the code** (the owner: "can be removed completely"): Ctrl+K, the magnifier and `palette.js`. The pages' own
  filters stay — they were not asked about.
- **The text check calibrated again** on 71 journaled checks (the owner: "more data has gathered") — see
  [text check](features/text-check.md#why-the-rules-are-what-they-are); the gemma4 loop is handled by keeping the whole transcript.
- **A robot clicks every page** before a change is called done (`tools/ui_smoke.py`, in the test run) — the owner asked what «automatic
  interface checks» are and said do it.

## 2026-10-06 — Progress only as far as it is known; motion on a 170–180 Hz screen

- **The owner** did not like step squares «filled to a half» and has a 170–180 Hz monitor: he wants more intermediate frames, nothing jumping.
- **Decision:** a measured progress fills in proportion, an unmeasured one is neutral (see [ui-principles](owner/ui-principles.md)); `patch()` morphs in place and
  `flip()` animates removals so state changes have frames; shared timing tokens; hidden toggles fade; the slide editor's drags are frame-synchronised.
  The Edge launch gets **no** frame-rate flags (they do not help a vsynced 170 Hz panel — they only tear). Five agents audited the areas in parallel, five implemented.
- **Not done:** `.ws-row` `content-visibility` (clips the waiting ring); the passport upload / export progress toast (needs new UI); the mockup/slides engine
  keeps `left/top` (a drag uses `translate`) so the baked slide output cannot change; server-side «unknown percent» flag for the Gelato/Printify milestone waits.

## 2026-10-05 — Speed audit: what runs only when it is needed, and what runs side by side

- **The owner** asked for a wide research of what could make the program faster, smaller and better, then said to do everything found.
  The measured findings: the code itself is quick (imports 0.26 s, 480 profit rows in 0.08 s) — the losses were elsewhere.
- **Decisions:** (1) the wiki check looks names up in a set of the code's words and never walks `data` (54 s → 2 s); (2) the text check's
  model is **not** read at every start — `warm()` does it when a card takes files (the earlier «prime» of 19.09 is gone); (3) Etsy,
  Printify and Gelato are read side by side in a sync; (4) Edge is told to leave components alone and its leftovers are removed from
  our two profiles when no window holds them; (5) the preview cache is capped at 800 MB (least recently used first); (6) the Workshop's
  and the slide editor's looking for changes slows to every 4 s after 30 quiet seconds; (7) scripts and styles are asked for by a
  versioned address and kept for good.
- **Not done, on purpose:** the 0.7 GB of identical files in the library and the Workshop were not turned into hard links (a page edited in
  place would change both copies — unlike the archive, which is never edited); folder previews keep `max-age=600` (some of their
  addresses carry no version, `immutable` would show a replaced page old); PNG pages are not recompressed (their hashes key the archive and
  Printify's upload cache). **Moving off Edge's `--app` window** (to WebView2, Qt or Electron) was weighed and rejected: same engine, a
  rewrite for no gain — the program never used WebView2.

## 2026-10-04 — The printer's history in the order card: asked for when the card opens, never in bulk

- **The owner** wanted what Gelato's dashboard shows (the status history) in the card's empty right-hand space — a square
  with a scroll — then: "forget what I said, do it as you think", and **"don't scan every order at launch and hide it
  everywhere — do it when I open an order, I can wait a couple of seconds."**
- **Decision:** a card «Історія» beside a placed Gelato order's data ([orders](features/orders.md)); the order is read from Gelato
  (one read-only `GET`) when its card opens, a skeleton meanwhile; nothing at launch, nothing for the queue. No always-open
  "expand" box: the column is free, so a click to open it would only cost.
- **Why not our own journal of status changes** (the alternative): it would have to watch every order at every sync — what the
  owner declined. So when Gelato's own log is empty, the card shows the few dates the order has and the tracking link.
- **Not known yet:** what Gelato's `eventLog` holds for a shipped order (the docs weren't readable, every draft had it empty);
  the card tries the likely field names and `gelato.log` records the real ones. The carrier's own scans (the USPS list in his
  screenshot) aren't in Gelato's API as far as found — the card links to the carrier's tracking page instead. Gelato's webhooks
  need a public address; the program has none.
- Built in the **portable** copy only (the owner, 2026-10-04: "будуй в портативній").

## 2026-10-02 — Listing slide 7: the hero's looks, each in its own frame, on its white background

- **The owner** asked for a new listing slide for the books with appearance variants, on the basis of slide 4 (his
  reference: «7 appearance options», a big G1, the others G2–G7 with their names). Then: "each must have its own place
  (a frame, a «зірочка») — I'll arrange them exactly later", and "it can stay with its white background, no cutting".
- Decided: slide 7 exists only for a Workshop book whose hero has **two looks or more** (`agent/variants/*/hero.png`);
  seven frames `hero:1…7` filled by the looks' numbers, the name from the folder («B2_blond» → «B2»); an empty frame shows
  only in the editor. The big one is a whole-body card, the six — scalloped frames with the head and shoulders. Old
  schemes get slide 7 recoloured from their own slide 4. In `etsy/` it is `15 Listing 7.png` — **last in the numbering**; the owner
  puts it into the listing himself. The texts are defaults he rewrites in the editor.

## 2026-10-03 — The portable Book Studio is back, in its own folder

- **The owner** took the portable copy up again: a folder `Book Studio Portable` on the Desktop with everything inside (Photoshop,
  templates, Python, Antigravity, Ollama, Upscayl, ffmpeg, Cent Browser); keys copied as they are; stage by stage, one stage
  per session (`ROADMAP.md` in its root). The original stays as it is. See [the portable copy](dev/portable.md).

## 2026-10-03 — Text check and upscaling are optional modules

- **The owner:** «давай зробимо ці штучки як модулі»: by default the program has neither Ollama (+ the model, ≈ 9 GB) nor Upscayl; the interface
  offers to install them where they would be used and the program installs them itself (quietly, from checked official files). A light PC
  (the colleague's) gets a program of ≈ 3 GB instead of 15. Also decided: Python is shipped with only the packages the program needs, ffmpeg
  with only `ffmpeg.exe`, Upscayl with its one model. See [optional modules](features/modules.md).

## 2026-10-03 — A copy for a colleague: the owner's rules become settings

- **The owner:** the program should be fit to hand to a colleague who owns a similar business (his own Etsy shop, Printify and Gelato; the
  Printify shop and defaults in the code are from his print shops the owner once worked on). The Kyiv option stays «only for me»; the
  colleague connects Etsy directly. Decided: `security.etsyKyivOnly` (default on) and `printify.readOnlyFrom` (default 2026-10-01,
  null = never) are settings; `make_colleague_copy.py` builds a copy without his data/keys/books/history with both switched off, **with**
  Photoshop and the mockup templates (the colleague paid for the mockups too; not commercial use).

## 2026-10-03 — Export/import of settings and keys, in both Book Studios

- **The owner:** a function in the ordinary and the portable program alike to move the settings and keys between computers/versions.
  Decided: only the settings, the keys and the slides' schemes (not books, orders or pictures); one 7-Zip file under the backup
  password, taken automatically. See [moving the settings](features/settings-transfer.md).

## 2026-10-03 — Edge instead of Cent Browser, and `AGENTS.md` only (the portable copy)

- **The owner:** the portable copy opens Gelato/Canva in the Edge that every Windows has, not in a carried Cent Browser;
  and the book pipeline's rules file is `AGENTS.md` alone, not a `GEMINI.md` twin, so any agent can use it. Antigravity's own
  data (`.gemini`) travels in the folder.

## 2026-10-03 — Keys in the portable copy: restored from the backup

- **The owner:** the keys do not travel in `vault.json` (Windows encrypts them for one user); on another PC they are brought back
  from the password-protected backup (`app/tools/restore_keys.py`), not by a new password vault. The start-up check says so.

## 2026-10-02 — The portable Book Studio is set aside

- **The owner:** «від портативки поки відмовися». The fully portable copy started on 2026-09-30 (its own folder on
  the Desktop, local git, no GitHub) is no longer there; the original `Book Studio` stays the only one. Not to be
  restarted without his word.

## 2026-10-01 (later) — a Gelato draft's card stays in the order card while its link lives

- **The owner**: the green card with all of a draft's details vanished once he left the Order Creator; he wants it to stay
  **while the temporary link lives**. He also wanted the yellow notice kept («Лиши»). Decided: the order card's print step
  shows the same card (`gelato-result.js`) until the link closes, then the short line. The button became «Замовлення в
  Gelato» (like «Замовлення в Printify»), one row with the copy and journal icons. The notice's text became true:
  Gelato fetches the files on its own within a minute (checked 17.09 and 30.09.2026), it does not wait for the draft to be
  opened. A first try with a small timer in the corner, without the yellow notice, was undone the same day: it was a
  misreading of a message typed without a Ukrainian keyboard.

## 2026-10-01 — Gelato and Canva open in the browser profile «Work»

- **The owner** asked that the «Gelato Dashboard» button open Gelato's orders list (`dashboard.gelato.com/orders/list`),
  not its home page, and that Gelato and Canva links open in one profile of his browser. The default browser on
  the Wrocław PC is Cent Browser (portable, Chromium); the profile he picked is «Work», which is the folder `Profile 6`.
- Decided: the settings' `browser` section (`exe`, `profile`, `hosts: gelato.com, canva.com`) is written once in
  `settings.json` and isn't shown in the interface, like other technical values. `_open_in_profile()` starts that
  browser with `--profile-directory`. If another site is opened, the section is empty, or the browser isn't found, the
  default browser opens the link as before. The Etsy block comes first and is unchanged.

## 2026-09-30 (later) — «Сьогодні» removed; tools open clean

- **The owner**: «"Сьогодні" можна повністю видалити як функцію» — done: the page, its route, the brand mark's link, its search entry and the helper
  that opened the queue on a tab are deleted; the brand mark is only the logo. (The earlier decision below is history.)
- **The owner**: a tool opened from «Інструменти» must open **clean every time**. Decided: entering a tool from the list drops what was kept of it
  (`keep.js` `startOver()`), except live work — a Photoshop run or templates waiting for his save (`canStartOver()` in the Mockups), a send in progress;
  an order's own Order Creator stays kept for that order and the tool opens a clean one beside it (`belongsToObject()`).

## 2026-09-30 (the answer about the presets) — schemes inside the editor and before the six are made

- **The owner**: "Night or Nature must be inside the editor, so that for a new listing I can pick the scheme at once." **Decided**: (1) a scheme is edited
  in place by its key (`where = scheme:<key>`; 27 slides tests + a new one) and the standalone editor's «Схема» button picks which one; (2) the Mockups'
  step 4 gets the same choice before «Зробити слайди» (the server already took `scheme`). The default scheme and `template` stay as they were.

## 2026-09-30 (after the owner's first look at the real data) — the tools on their own, the slide reset, a column that trapped the wheel

- **The owner**: the wheel did not scroll the page over the order card's white cards; a tool opened from «Інструменти» had no way back and the rail's
  «Інструменти» went to the tool last used; the slides' back arrow paged through the slides' history; «Скинути слайд» went to a months-old
  default; the Mockups always showed a «Книга» selector. **Decided**: the data column is never a scroller (bottom-sticky when taller than the
  window); «Інструменти» always opens the list and a tool opened on its own has an arrow to it; the slides' back goes to where the owner came
  from and the reset returns the slide **to how it was when the editor was opened** (no question, Ctrl+Z); the Mockups take a book only when it is
  a book's step or asked for with an icon — otherwise they ask for a folder.
- **Not done yet — a question to the owner**: a «presets» selector in the standalone slides editor; and a slower start could not be reproduced
  (the server starts in 2.40 s both before and after; the page's requests are the same on made-up data); **the owner later said it went away by itself** —
  most likely the first launch after an update (nothing cached yet); if it comes back, note where it waits (the window, the first screen, the orders).

## 2026-09-30 (the very last) — Wave 8: a drop anywhere, a picture that comes back, a keyboard that works

- **The owner**: "do wave eight." **Decided**: (1) a file dropped outside a page's own field is accepted over the whole window and
  asks **«Куди?»** (the Mockups or the Order Creator) — the program never chooses, nothing is copied before the choice, the
  page that is open takes it itself; (2) removing a picture from a library book **sets the file aside** (`data/library/trash-assets/`,
  never deleted by the program) and offers «Скасувати» — this also makes the old "file deleted for good" safer, in line with
  "never permanently delete the owner's data"; (3) the real Tab walk found three faults, fixed: a group of tabs was four stops
  without arrows, the focus was lost after a page change, a dialog did not give the focus back nor keep Tab inside.
- **Left**: the live run of the print review (the owner), the rail unfolding its words on hover (the owner chose icons only).

## 2026-09-30 (last) — The final waves: undo for what can be undone, one review before print, «Сьогодні», Ctrl+K that does

- **The owner**: "the final waves". **Decided**: removing a library book acts at once and offers «Скасувати» (a real restore
  from `data/library/trash`, a new route); a picture's delete, the Windows-Recycle-Bin deletions of the Workshop and the
  print send keep their question, because an undo the program cannot keep is a lie; the send's up-to-four dialogs are one
  review; the brand mark opens «Сьогодні» (a read-only to-do across the places — the program still *starts* in the orders);
  Ctrl+K gets verbs for a Workshop book («Мокапи · №41», «Слайди · №41»).
- **Not done, on purpose**: a «services ready» strip in Settings (each card's header already carries the green/amber mark —
  a second one would say the same); shortening tracking numbers (the owner pastes them into Etsy's two fields and checks
  them by eye, 25.09); a **drop zone for the whole window** that recognises a Canva ZIP — the real Explorer drag can't be tested
  from here and a wrong guess would put files in the wrong place.

## 2026-09-30 (night) — One book, one look: a shared tile, one bar, the Workshop's steps as pictures

- **The owner**: "do the third and the fourth." The library's square tile and the Workshop's wide bordered card were two
  components for the same object, and progress was drawn three ways (a bar of 11, four squares, a strip of squares).
- **Decided**: one tile (`book-tile.js`, the library's "book on a shelf" look), one bar (`segBar()`), one state alphabet; the
  Workshop's eleven steps use the order path's component (`pathStep()`), pictures with the word in the tooltip. *Lost on
  purpose:* the step's written count under the dot («5/16», «14 помилок» in red text) — the dot is red with ⚠ and the tooltip
  and the panel carry the numbers. The Workshop's two views of the same picture set (the gallery panel and the rows) stay:
  one is the overview, the other the work.

## 2026-09-30 (late) — The third pass: a hammer and a ruler, a tick for «done», quieter Workshop, tokens for leading and press

- **The owner** asked for a full analysis with every design skill, the weakest icons redrawn, and — his own wish — **the
  Workshop's glyph as a hammer and a ruler crossed**. Findings and the waves are in the log of 2026-09-30.
- **Decided (by the agent, "do as you see fit")**: `×` means *remove* only; finishing work on an order is a ✓ (and says so in
  a toast); the Workshop header keeps one labelled button — «Передати в бібліотеку», only once the book is ready — the folder
  and the shelf become icons; a prompt shows three lines; leading in three tokens, press feedback in two, `--text-3` in
  light darkened to reach AA. *Not done on purpose:* the 500 weight on the soft printer chips (the owner's choice of
  2026-09-17) and on tooltips; 32 px icon buttons (a mouse-driven Windows program; 24 px is the floor, 32 the norm).

## 2026-09-30 — The interface redesign: objects with their path, tools on their own, one labelled rail

- **The owner** (after a UI/UX audit): "the design isn't intuitive… the functions are scattered as if someone spilled
  grain… even I get lost" — and he handed the decisions over: "I trust you completely, do it as you know; be
  creative". His thought, "not a requirement": the program is a set of tools glued together, and he'd like to use each
  on its own. The audits and waves are in the log of 2026-09-30.
- **Decided (by the agent, with his leave)**, revising earlier decisions where named:
  - **One labelled rail** — Замовлення · Книги · Прибуток | Інструменти, Пошук on top, Settings at the bottom — replaces
    the two modes switched by the brand icon (2026-09-24). The inks stay and follow the area.
  - **«Книги»** — the Workshop's gallery and the library's as the tabs «Майстерня · Бібліотека · Архів» (his own words;
    "у магазині" was tried and dropped the same day: his vocabulary wins). The passport turns cyan with the books.
  - **«Інструменти»** — the Order Creator and the print archive leave the rail (the archive was "a separate menu on the
    left" since 2026-09-18); with the Mockups, the photo mockups and the slides' scheme they work on their own from
    there, and inside their object from its step.
  - **An order is one place**: its path in the card; «Друк» opens the Order Creator as that order's print step; a
    printed order's card shows what went to print and leads to the reprint.
  - **Search everywhere** (Ctrl+K).
  - **Type**: five sizes 12 / 13 / 15 / 19 / 25 replace the seven of 2026-09-26 (five within 2 px); section labels in
    sentence case.
  - **One loud button per screen**: the Workshop book's «Папка книги» stays labelled but not in the ink (it was, at
    the owner's word "an important button", 2026-09-26) — two ink buttons side by side read as two next steps.
  - The queue's tabs in words; the address fields labelled; no silent grey buttons left (`markMissing()`).
- **Revised the same day by the owner** ("show, don't tell — a minimum of captions, a maximum of icons"): the rail
  is **icons only** (tooltips, the page's title), search moved to the **end** of the list, the queue's tabs and the
  books' tabs are icons with counts (only the chosen one shows its word), an order's path is a row of icons, the rows'
  next-step sentences went (a «Позначте в Etsy» that only opened the order was a lie), the refresh is an icon. **Fixed
  a bug**: a placed order's card showed the printer rule's printer («Printify · 24 стор.» on a Gelato order) — it
  shows `o.provider` now. Rules — `book-studio-ui-logic`, [ui-principles](owner/ui-principles.md). The owner's
  **light theme** is the main one: judged first.
- **Why**: recognition over recall — places and tabs seen in words; one object, one home, its next step visible; the
  tools' own pages kept for work without an object, as he asked.

## 2026-09-30 — No «Слайди для лістингу» button in the Mockups' header

- **The owner** didn't see why it was there, and asked to remove it. A book's slides open from the book (the
  Workshop's «Мокапи» step → «Редагувати слайди»); the design new books start from is chosen in any book's editor
  («Схема ▾» → «Нові книги — зі схеми …», or «Зберегти ці слайди як схему» with its tick). The route
  `/api/slides/sets` went with it. The default scheme's own page (`#/slides/template/…`) stays, reached by its
  address; the agent changes it through `/listing-slides`.

## 2026-09-30 — The etsy/ folder in the listing's order

- **The owner:** the files of a book's `etsy/` stand in the order they go into the Etsy listing: 01 photo-main, 02 the
  Omni video (`video-hands`, always second), 03 photo-grandma, 04 All & Open 1, 05 Listing 1, 06 Cover & Open 1, 07
  Listing 3, 08 Listing 4, 09 photo-child, 10 Listing 2, 11 photo-size, 12 Listing 5, 13 Listing 6, 14 photo-shelf.
  Anything else — no number, at the end.
- **The open-book photo, when made, takes Cover & Open 1's place (06)**; that mockup then stays in `mockups/` only.
- **A number belongs to its file**: a missing one leaves a gap (his "так"). The form «01 photo-main.png».
- How it works — [photo mockups](features/photo-mockups.md#where-things-are). Book 25's folder was put in order once.

## 2026-09-30 — «Книга в руках у людини»: a video category with the owner's own Omni prompt

- **The owner:** remember the prompt that worked in Gemini Omni and add his photos «Книга в руках у людини» as the
  seventh category of the photo mockups.
- **Kept word for word** (`photos.OMNI_PROMPTS`), plain text: it was tuned over several tries in Omni (a prompt that
  describes only the motion; one that described the whole scene made Omni redraw the frames; "small book" everywhere
  stopped the book growing). Not turned into the photo categories' JSON frame.
- **The video is caught, its first 2 seconds cut off** (the owner, the same day): into `etsy/video-hands.mp4`, by
  ffmpeg, encoded again so the cut is exact; the download as it came kept in `originals/`. The category counts in the
  step like the others (`n/8`).

## 2026-09-30 — Photo mockups: a step of the Workshop and a page of their own; `etsy/`; English inside

- **The owner:** lifestyle photos with a blank white book (a grandmother reading, a child holding it, a shelf, an open
  book, the main flat lay) — one per category, **categories may be skipped**; the generator swaps the book for ours.
  In a book: **template → the book's cover → the prompt**, Ctrl+V after Ctrl+V; the photo caught into the book. **A
  page of its own** as well: only the template and the prompt ("I'll add the pictures myself") — nothing caught.
- **Which cover goes second:** Cover 1 (main, child, shelf); **Cover & Open 1** for the open book; for the grandmother
  **the flat cover from the Canva ZIP** — the owner: simpler than explaining which part of «All & Open 1» to take ("I did
  it that way already"). The Mockups keep it in the book (`mockups/canva-cover.*`).
- **The prompts are JSON** (the Workshop's own format), one per category; **no white of the blank book may stay** — the
  spine and edges are our book too (the owner: "no white parts — our book").
- **`etsy/` in every book** for what goes into the listing, as the owner laid out book 25's by hand: the six slides
  (`Listing 1.png … Listing 6.png`), the photos (`photo-<category>.png`) and copies of the two whole-scene mockups
  (`Cover & Open 1 (…)`, `All & Open 1 (…)` — copied when the Mockups save them, the originals stay in `mockups/`). **Every name inside Book Studio in English** (folders, files, categories; «Без фону» →
  `no-background`), the interface in Ukrainian.
- **The templates live inside Book Studio** (`app/data/photo-mockups`, copied from his desktop, English names), not on
  the desktop. The sixth category «Для відео» (three 9:16 phone photos of the book lying, no people) — the same
  evening, and «Розмір» (the softcover and the hardcover side by side — one template, from `Size.jpg`).
  «Папка книги» — a blue button beside «Передати в бібліотеку». The rail's icon — a camera
  ([photo mockups](features/photo-mockups.md)).

## 2026-09-29 — Listing slides: schemes, the Workshop book's folder, locked by default

- **The owner (the evening):** a **scheme** is "not only the colours but the settings of the whole mockup" — the six
  scenes, named: his blue slides saved as **Night**, the template as **Nature** (the default); picked and saved in the
  editor; a done book's slides are **presets** for other books ("e.g. another bedtime book") — never erased.
- **A book's slides belong to its Workshop book** ("not to a session"): the Mockups save into its folder `mockups\`
  without asking; its «Мокапи» step ticks itself and leads back to the mockups and the slides at any time.
- **Cleaning:** the quite temporary goes when the program starts and closes; a book's cache when it is passed to the
  library; everything in the program's folder.
- **Every element locked against moving by default** (a click selects it); the background a layer of its own; the
  colours of the other slides offered; «Який мокап» without the file name; Dedication without its floor (the desk
  and the shadows kept). **Books numbered as his Etsy listings** (24, 25, …).
- The template's «Зробити шаблоном» went — «Зберегти як схему» and the default scheme replace it
  ([slides](features/slides.md)).

## 2026-09-29 — Listing slides move into Book Studio

- **Decision (the owner, the same evening):** "integrate it into our program at once" — the slide tool becomes a
  **separate module of Book Studio's Listings mode, called only when needed**, with the editor in Book Studio's
  style, plus a **skill** for working on the slides through an agent ("sometimes it will be easier for me to work
  through an LLM"). Built phase by phase the same evening. Replaces
  "outside Book Studio for now" below.
- **How (the owner, then the defaults of the plan):** no page in the rail — the slides are the Mockups' next steps
  ("after the Photoshop script the Mockups page offers the next step; I press it and they are made by themselves;
  then a button offers the editor"); the Mockups save every picture **without background** too (`Без фону\`, only
  Open 1, Open 2, Cover 1 can be cut); **one template** for every book — a book gets its own copy, «Зробити
  шаблоном» carries a slide back; the files `Listing 1…6.png` in the mockups' folder; an agent's change in the
  files shows up in the open editor, a save made on an old version is refused, never overwriting it
  ([features/slides.md](features/slides.md)).

## 2026-09-29 — Listing slides: our own tool, outside Book Studio for now

- **Decision (the owner):** the six Etsy listing pictures he makes in Canva are made by a tool of our own —
  no Canva, no Canva connector ("create an entirely new tool of your own"). His layout, reproduced closely,
  with torn-paper edges, a die-cut sticker, sparkles and faint leaf shadows; the final touches he makes by hand
  in a small Canva-like editor, then the agent bakes them. **It stays an external tool for now** — "don't
  integrate it into Book Studio yet" — in `D:\Roman\Desktop\moсkup studio\Slide Editor\` (moved in the same evening, see above).
- **How the book is cut out** (the agent): the templates' Multiply/Screen shadow layers turned into
  transparent black/white, the outline from `BOOK/OBJECT`'s mask — nothing to change in Photoshop or the
  templates (only read).

## 2026-09-29 — From 1 October only Gelato, on his own account; Profit turned on

- **Decision (the owner):** "from 1 October I move only to Gelato, on my own account"; his "alternative printer" is
  that own Gelato account, nothing third. Printify gets **no new books** from 1 October 2026, US hardcovers included;
  it is only read while its earlier orders finish (the owner picked this over "keep as now" and "turn it off
  entirely"). **How (the agent):** a date in the code (`printify.READ_ONLY_FROM`), not a switch in Settings — the
  owner doesn't want switches for this (2026-09-25), and on that day the program changes by itself; Printify's code
  stays whole, so going back is one date ([recipe](recipes.md)). An archived Printify book gets no reprint button:
  24 pages don't fit Gelato.
- **The smooth switch as agreed on 2026-09-27**, with two engineering choices: an order's account is a hash of its
  key (never the key); the old key is needed only until none of his orders there waits, prints or travels — not
  until the archive days are over — because the safety net keeps every known order anyway.
- **Profit in the rail now, counting from 1 October** (the owner picked "at once, counts from 1 October" over
  "appears by itself on 1 October"): empty until the first October sale. The day is midnight on this computer's
  clock.

## 2026-09-28 — Printify "Fulfilled" reads as In transit / Delivered

- **Decision (the owner):** the status chip no longer shows Printify's "Fulfilled" beside Gelato's "Delivered". **Why:**
  it looked inconsistent. "Fulfilled" only means the printer handed it to the carrier, so a plain rename to
  "Delivered" would lie about fresh parcels: it shows **In transit**, and **Delivered** once the carrier's
  `delivered_at` is on every parcel. The stages (the truck, the box) still go by Printify's real status.
  [Stages](rules/order-stages.md).

## 2026-09-27 — A picture 2400 px a side is big enough: not offered for upscaling

- The owner: "it doesn't recognise big pictures … if the picture is already the size it is in the book, or close, don't
  offer the upscaler again". **Decision (the agent's):** one threshold — a page of 2400 px (8″ at 300 dpi, what print
  needs) or more is big; the pages in the book are measured, not the original alone; a row whose original is big
  already (upscaled by hand) is only cut again, without Upscayl. Every picture shows its page's size.

## 2026-09-27 — No «Генерувати варіант»: a variant's spreads one by one

- The owner: the button that queued all of a variant's spreads is not needed — "I do them one by one, it's handier".
  Removed from the variant's tab; the base book keeps «Генерувати всю книгу».

## 2026-09-27 — Pictures put into originals/ by hand: picked up on a press, not by themselves

- The owner put variants' spreads into `originals/variants/<name>/` with the right names and expected the Workshop to
  take them. **Decision:** a button «Підхопити з папки (N)» (the agent offered it, the owner: "go ahead") rather than
  the Workshop watching the folder — a file put there by chance overwrites nothing until he presses.
- Details — [features/workshop.md](features/workshop.md#a-picture-into-its-row).

## 2026-09-27 — Upscaling in the Workshop: ×2 by his Upscayl, right after a picture lands, a book can skip it

- **Decision (the owner):** upscaling becomes a step of the Workshop, with a way to skip it — **for the whole book**
  (a switch «Апскейл ×2»), **on by default**. "Just 2×, whatever size the picture comes in — I use different
  generators, their sizes differ": no target size (not 4000 px), the model he picked in Upscayl himself
  (upscayl-standard-4x, output ×2).
- **What is upscaled:** the spreads, pages 1 and 30 (the dedication, the afterword) and the cover — and, the same
  evening ("there's no upscale in the variants"), every hero variant's spreads and cover. **Not** the hero pictures
  themselves ("the hero — no"). Listing photos aren't the Workshop's ("we only work with the spreads and
  the cover").
- **How (the agent's choice):** his own Upscayl's command-line engine, no window; the row's original is upscaled
  before it is cut (the two halves stay alike), then mirrored and cut as before; in the background, one at a time
  (the graphics card is shared with the text check's model); a failure leaves the small pages and says so.
- Details — [features/workshop.md](features/workshop.md#upscaling).

## 2026-09-27 — Every spread gets the hero with its prompt; Ctrl+V in Chrome turns to the next part; a cover per variant

- **The owner:** in the one Gemini chat he attaches the reference to **every** prompt — so a spread of a book with a
  hero gives the hero, then the prompt; **pages 1 and 30 — the prompt alone**. He picked "two pastes in a row"
  (Ctrl+V → Ctrl+V → Enter) over Ctrl+V → F8 → Ctrl+V. Gemini is open in **Chrome**.
- **How:** the keys' state is **looked at** (every 20 ms, only while a several-part paste goes on), not caught with a
  keyboard hook: nothing is taken from Windows, typing elsewhere can't be slowed, nothing is recorded. Only a Ctrl+V
  while Chrome is in front counts — Book Studio's own window (Edge) and other programs are left out. The next part
  goes in 0.35 s after V is let go (Chrome has read the clipboard by then). One clipboard with a picture and a text at
  once was not used: the site takes one of the two, which one isn't sure. «Далі» and F8 stay for a miss.
- **A cover per hero variant** (the owner): no two stages, one frame for the expanded (finished wide) cover at once,
  no prompt — brought to the printer's template like the base cover.
- Details — [features/workshop.md](features/workshop.md#the-generation-mode).

## 2026-09-27 — One place for a Workshop book's pages: its folder

- **Decision (the owner):** "the Workshop and the library keep the same files — one place, no doubles". A book
  passed on from the Workshop takes its cover and pages from the Workshop book's `pictures/`; the library keeps no
  copy (`"pagesFrom": "workshop"`, [features/library.md](features/library.md)). A page replaced or added in the
  Workshop is the library's at once.
- **Such pages are changed in the Workshop only**: it mirrors and cuts a spread the way the book needs; a picture
  put in through the passport would skip that. The passport shows them and leads to the Workshop («Змінити в
  Майстерні»); its thumbnail stays its own.
- **The texts stay in both places** (the owner: "they can be edited here and there, two places is fine"): copied
  once on passing; the passport's are the text check's reference, the Workshop's are the agents'. They don't follow
  each other — the owner was told, and whether they should is his call.
- **Nothing is lost:** deleting the Workshop book first copies its pages into the library book; the one book passed on
  earlier (31 of 31 pages the same byte for byte) moves onto the Workshop's pages at start-up, its copies (≈0.3 GB)
  to the Recycle Bin; a book whose copy differs keeps its own.

## 2026-09-27 — A backup of the whole program to Google Drive, the keys inside

- **Decision (the owner):** Google Drive for desktop on this PC (he has 5 TB); every 2–3 days (made: 3, on launch)
  **the whole program folder, everything**; the mockup templates too — backed up where they are, not copied into
  the program (two copies would drift); a password on the archive; **the keys inside, readable** ("everything is
  under a password") — so a restore on another PC needs no re-entering (the vault opens only for this Windows
  user). `.secrets.txt` goes along with the folder, by the same decision.
- **How:** 7-Zip (`app/bin/7za.exe`), AES-256 with hidden names, stored uncompressed; the Drive app uploads it;
  the last 7 copies and one a month for a year stay. Left out only what can't or needn't be read: Edge's profile,
  the temp folders. Drive's cache moved to drive D (he keeps C clean). [features/backup.md](features/backup.md).

## 2026-09-27 — Profit from 1 October only; the Gelato account's currencies; a smooth switch to his own Gelato

- **Decision (the owner):** accounting starts on 1 October 2026 and does not include earlier orders at all. Built on 2026-09-29
  (`profit.ACCOUNTING_FROM`).
- **Why the program asks the printers now:** it is the queue's sync, not the accounting's — the order's stage, the
  printer's status, the tracking number, the archive's 14 days all come from it (its old names — the job
  `profit-sync`, `/api/profit/sync`, `data/profit/` — are from the time it lived in `profit.py`). The Profit page
  itself asks nothing: it reads the same snapshot.
- **Currencies:** the owner's Gelato orders are paid in dollars; the euros and crowns in the account are mostly
  other people's orders (he plans an account of his own). The euro's rate stays; nothing to decide.
- **His own Gelato account — a smooth switch** (the owner chose it over a frozen copy of the old orders): the old
  account's orders are never forgotten, and for the transition the program reads both accounts — the old key only
  reads, everything new goes to the new account. Built on 2026-09-29 ([gelato](integrations/gelato.md)); the old key
  stays until none of its orders waits, prints or travels.

## 2026-09-27 — The big cleanup, phase 6: big files cut by job

- **A page keeps its state and its actions in `mount()`**; what only draws (a row, a panel, a result) or a dialog of
  its own goes to a module of its own and gets what it needs passed in (`book()`, an id, a callback) — it never
  reaches into the page. The order card's text check and the Order Creator's steps stay in their pages: they live
  on one order's state.
- **The server's big files are packages by job** (`textcheck/`, `creator/`), the library's files and guide apart
  from its model; the styles by section; the preview server by job.
- **The wiki names a function where it is defined.** A line that links a file names only what that file defines;
  `wiki_check.py` fails otherwise (since this phase: an import or a call used to pass).

## 2026-09-27 — The big cleanup, phase 5: one copy of everything

- **One-time migrations go once they have done their work** on the owner's PC (checked in his data: no old
  settings, no old Gelato product names, no old mockups folders left): the Order Creator's old form, the separate
  «Мокапи»'s leftovers, the inch-sized Gelato products, the single page count. The code keeps no upgrade path for
  data that no longer exists.
- **The Order Creator's «Замовлення Etsy» lists the queue's orders** (`/api/orders`) — its own route
  `/api/creator/etsy-orders` gave the same orders and went.
- **Shared pieces instead of copies** (not to be copied back): the folder viewer with a page replaced
  (`folder-viewer.js`), the proof with its strip, the buyer's fields, the address, the printer's chip, the files'
  badge and notices, the order list's counts and empty states (`order-bits.js`); a detail page's Esc and "could
  not open", the dialog with a box to tick, `post()`, `glide()`, `tellBusy()` (`lib.js`); on the server — the picture
  suffixes and "inside our folder" (`core.py`), see-through parts on white (`images.flat_rgb()`), the child's name
  (`wording.py`). One CSS rule fades every picture in (`img[data-fade]`).
- **Left as they are, on purpose:** the ~130 one-off inline styles (an inline style wins over any rule — moving
  them into classes changes which rule wins, one by one, for no gain the owner would see); the notice markup
  (short and explicit); the Printify / Gelato send frame — it moves with the Order Creator's split (phase 6).

## 2026-09-26 — The big cleanup, phase 2: matching and money

- **Changed on purpose** (the owner: "fix everything you found"; not to be "fixed" back):
  - **Receipt numbers before names**: Printify by number, Gelato by number, then Printify by name, Gelato by name.
    A receipt whose own Gelato order carried its number was taken by a Printify order with a similar name and
    showed its status and tracking.
  - **Only a placed and paid print order costs money** — the 2026-09-18 decision, now in the money too: an order
    on hold or awaiting payment costs nothing yet and the sale shows no profit until it is paid.
  - **Every currency converted**: crowns, pounds, zlotys at the ECB's rates of 25.09.2026 (settings'
    `czkUsdRate`, `gbpUsdRate`, `plnUsdRate`); a currency without a rate is never counted as dollars. The euro keeps
    the Profit Calculator's 1.085 (2026-09-27: the owner's own Gelato orders are billed in dollars — only two early
    ones in euros; the crowns are other people's orders in the account — open questions).
  - **The cover type only from the buyer's choice**, never from letters of a Gelato order's name.
  - A cancelled first print order no longer wipes the cost of the sale's other print orders.
- **How:** one reading of a print order (`printorders.py`), matching one receipt at a time (`reconcile.py`), the
  money once (`outcomes.py`); `profit.py` split into `sync.py`, `records.py`, `stages.py` and the Profit view — the
  archive ↔ profit import cycle is gone. The Profit page brought to the owner's interface rules, ready for
  1 October. Details — [rules/reconciliation.md](rules/reconciliation.md).

## 2026-09-26 — The big cleanup: every finding of the code study is fixed

- **Decision (the owner):** "fix everything you found — I need a flawless app; the wiki and GitHub up to date".
  The work went phase by phase (bugs, money, speed, no blinking, duplicates, big files cut by job); `main` was updated after each.
- **Changed on purpose in phase 1** (not to be "fixed" back):
  - Printify: **every book's pictures go up before any book is made**; the steps after a book or a draft exists
    (reading it back, the Master's check) only warn — they never fail the send, or a retry would make it twice.
  - Gelato: the PDF link belongs to the registry as soon as the draft exists.
  - A reply cut short while it is read counts as "result unknown" (don't resend), like a timeout.
  - The text check keeps no broken answer and never asks a timed-out page twice.
  - A dropped folder stays until a day unused (each check of it is a use), not 2 hours from the drop.
  - A library book is not deleted while its folder import runs.
- **Why:** each was a real way to lose work or money (a second order, a draft without its files, a card losing its
  folder), found by reading the code; every one now has its own test.

## 2026-09-26 — Mockups: Dedication stays open for its colours

- **The owner:** "Dedication has to be left open too, because there I pick the colour of the background and the
  table."
- **Decision:** Dedication is filled as before (page 1, the back, the spine, the rim) and left open instead of saved
  (`"keep": "colours"`); «Зберегти відкриті» saves it as `4. Dedication.png` with his colours. So a run saves 6
  pictures by itself and leaves 4 templates open; no automatic Dedication picture in the default colours.

## 2026-09-26 — Mockups: the book's cover opens in Photoshop too; «×» finishes the page

- **The owner:** "I want the script to open and leave not only the PSDs but also the Cover image in Photoshop, so I
  can work with it at once. And a cross on the Mockups page, to finish the creation."
- **Decision (the agent's, on that ask):** the cover opened is the demo book's own cover (the wide picture of the
  Canva export), a copy in the run's folder named `Cover.png`, opened only when templates are left open, the first
  template still in front; «Зберегти відкриті» closes it only if unchanged. «×» clears the page and the unpacked
  book; a run still waiting in Photoshop is asked about first and then no longer offered — Photoshop itself is never
  touched by it. Where — [features/mockups.md](features/mockups.md).

## 2026-09-26 — The Workshop in Book Studio's own style; no magic wand

- **The owner:** "the icons, fonts and text look like some other style than Book Studio… go over the typography…
  redraw the icons, especially the magic wand — replace it with something else".
- **Decision (the agent's, on that ask):** the Workshop takes the program's parts instead of its own look-alikes —
  the header's secondary actions as one `.tools` group of icons (the passport), the rows under a `.section-title`
  heading, the passport's `.drop-ico` drop zone and eyebrow-only block heads, the Order Creator's square step numbers
  for the path and the cover's stages, the dotted endpaper of the Order Creator's empty cover; font sizes only from
  the program's scale; the three status dots on a row went (the row shows the same by itself). Icons redrawn:
  `agent` (a chat, typing), `workshop`, `mirror`, `guides` (crop marks); the wand `prompt` became `>_`, with new
  `generate` (▷) and `regenerate` (↻) for the buttons. Where — [features/workshop.md](features/workshop.md),
  [architecture/frontend.md](architecture/frontend.md).

## 2026-09-26 — The agent is told the pipeline's full paths (Antigravity 2 picks the folder by its project)

- **Found:** after the move the agent wrote the new book into the prototype's `D:\Roman\Desktop\Book Console\books`.
  Antigravity 2.17 ignores the folder `Antigravity.exe` is started with; a new chat runs in the project last picked
  in it (`Book Console`), and reads that folder's `GEMINI.md`.
- **Decision (the agent's, on the owner's "fix it"):** Book Studio only starts Antigravity; the clipboard's words
  name the rules (`…\pipeline\GEMINI.md`) and the book's folder in full (`books.agent_words()`), so a chat in a wrong
  project is still told where to write. **The owner, once:** an Antigravity project on `Book Studio\pipeline`,
  picked for new chats. *Not done:* Book Studio doesn't edit Antigravity's own settings (another program's).

## 2026-09-26 — The book console moves into the Workshop; the pipeline moves into Book Studio

- **Decision (the owner):** "create a new branch on GitHub and integrate the console into the Workshop" — branch
  `book-console`. The Workshop *is* the console now: its gallery is the console's book list, a book's page is the
  console's page, in Book Studio's own parts ([features/workshop.md](features/workshop.md)).
- **A Workshop book is the pipeline's folder** (`pipeline/books/<n>.<slug>/`), not a library book marked
  `"stage": "workshop"` any more (the agent's call; 0 such books existed): the agents write into its `agent/`, and
  that folder has to be inside the one Antigravity opens. **The agents' files are the one source of the prompts and
  texts** — the old Workshop's typing, its JSON `{ }` and its agent instruction went.
- **«Передати в бібліотеку» makes a library book** from the book's pages, texts and listing (copied, as a job); the
  Workshop's book stays with its folder (originals, variants) and moves to «У бібліотеці».
- **The pipeline (rules, playbook, notes, listing prompts) is in git** at `pipeline/`; **the books are not** (every
  picture). *Why this place:* Antigravity keeps its agents inside the opened folder and hides git-ignored files
  unless *Agent Gitignore Access* is on (checked in the program, 2026-09-26) — one setting for the owner, instead of
  opening all of his disk to the agents (*Non-Workspace File Access*).
- **The sandbox** (`core.SANDBOX`): the preview and the tests never touch the owner's clipboard, keyboard, Downloads,
  books or screen.
- Details — [workshop](features/workshop.md).

## 2026-09-26 — The cover's margins follow the printer's template; a deleted book goes to the Recycle Bin

- **The cover's margins are the printer's template** (the 8×8 hardcover the owner gave: 17.90″×9.50″, finished
  16.40″×8.00″), by default and without a name of its own ("just make it the default"): the picture's width is
  the finished width; the result is 5370×2850 px, 300 dpi.
- **«Видалити книгу» sends the book's folder to the Windows Recycle Bin**, not away for good — the owner asked for
  "the book and all its files deleted"; the project never deletes his data irreversibly, and the Recycle Bin keeps
  it restorable until he empties it.

## 2026-09-26 — The console moves a download into the book; no listing photos; the cover gets margins

- **After the first real book, the owner changed it:** a caught download is **moved** out of Downloads into the
  book's `originals/`, named by its row ("it should live in the program") — before, it was only copied. The cut,
  named pages stay in `pictures/`; both folders open from the page; every picture can be saved anywhere
  («Зберегти як…»).
- **The listing photos, the cover's mockup and reference are gone** from the console ("redundant", "they only
  confuse me").
- **The cover has two stages:** the picture, then its margins outpainted by the generator (white margins of 8 %
  of its height, adjustable) → Cover.png — the owner's own step, shown on his example screenshot.
- Details — [workshop](features/workshop.md).

## 2026-09-26 — The book console's generation mode: the clipboard by the program, F8 for the next part

- **The program fills the Windows clipboard itself** (not the page), so the next prompt is there while the owner
  stays in Gemini; the work (watching Downloads, catching, the next prompt) is the server's and goes on when the
  window is behind.
- **A paste of several parts** (the cover: mockup, reference, prompt; a listing photo; a variant's spread) gives
  them one by one — the first at once, the next by «Далі» or **F8**, a key taken from Windows only while such a
  paste goes on (a picture and a text can't reliably go into one paste). *Why not detect the paste:* Windows
  says nothing when the clipboard is read, and the clipboard history reads it at once.
- **Nothing the console replaces is deleted** — it goes to the book's `.replaced/`; Downloads is only read.
- **The cover's mockup and reference are chosen once for every book**; a listing photo's mockup once per book
  (the agent's choice at the step, 2026-09-26 — the owner may change it).
- Details — [workshop](features/workshop.md).

## 2026-09-26 — The book console prototype: its own folder, no SEO guide, no git until the move

- **Decision (the owner):** the prototype lives in `D:\Roman\Desktop\Book Console`; the pipeline's
  `seo-intelligence` is **not** taken into it ("it goes separately"); the prototype keeps **no git history**
  until it moves into Book Studio.
- **The agents write only into a book's `agent/` folder** (the agent's proposal, accepted with «роби»): the
  console owns `pictures/`, `listing/` and `book.json`, so an agent can't break a book or lose the owner's
  edits. The old validator became the console's `check_book.py` (same rules).
- Details — [workshop](features/workshop.md).

## 2026-09-25 — Pictures are generated on the websites (Gemini, ChatGPT), never through a paid API

- **Decision (the owner):** he generates in the websites' chats on his subscriptions; **no image-generation API
  is connected** (it costs money per picture). So no "Generate" button in the Workshop. Anything that helps
  generation works *around* the website chat: prompts to copy, files he downloads.
- **Where what is made:** the book's spreads — **Gemini** (downloads as PNG to Downloads); the listing's
  lifestyle pictures — **ChatGPT** (JPEG); the cover — a Photoshop cover mockup put into the chat as context
  plus one of his existing listings as a reference, asking to replace the picture.
- **Tier H books (a child hero):** for now he swaps the hero to the buyer's look **per order**, in the same
  chat. Pre-generating every look is too costly — look, clothing colour and eye colour multiply. If it ever comes, one
  look per hero would let every variant be made once.

## 2026-09-25 — Ideas reviewed: what the owner keeps and what he turns down

An agent offered ten ideas for the whole pipeline; the owner answered each one. **Turned down, and why:**
- **Upscaling for orders** — his Canva books already hold upscaled pages. (Upscaling in the **Workshop**,
  right after a drop — kept.)
- **Pages from the library instead of Canva** — not now: storage and internet are fine, and a mixed
  source would confuse; "a micro feature for later".
- **A demo book from the Workshop without Canva** — Canva takes little time and needs a human eye for the
  aesthetics; Photoshop's interface doesn't suit this work either.
- **Checking that a character looks the same across the generated pictures** — "I'm very picky, I don't
  need a checker here".
- **A print-quality journal (reprints by printer)** and **profit by book** — no statistics wanted here; he
  keeps such a metric separately.

## 2026-09-25 — For now a hardcover's printer is decided by its files, not by the country

- **Decision (the owner):** Printify started printing faulty books, so for a while he wants the choice
  between Printify and Gelato himself. For a **hardcover** (any country) the printer follows the files he
  gives the program: **24 pages → Printify, 28 or 30 → Gelato**. **Softcovers, the small one included,
  stay only Gelato's.** In the queue a US hardcover is still marked green "Printify", as usual — as a hint;
  he decides.
- **No switch in Settings** (the owner): when Printify is fine again, bringing back the rule is a small
  code change (`choice` in `orders.plan_for()`).
- The owner: an order with books going to different printers "will never happen" — nothing is built for it.
- Details — [rules/printer-rule.md](rules/printer-rule.md).

## 2026-09-25 — The text check calibrated on its journal; another book's pages — a loud guard

The owner: calibrate "the machine validator that decides what to show me in errors and what not" (not Gemma),
now that there are cases; then "do as you see fit — only if I make the wrong book, as happened once, it must be
not just a message but a big red one that's noticeable, a guard against a slip".
- **Decided on the journal** (30 checks, 10 orders): 4 real catches, the rest noise with 5 causes — the full
  story in [features/text-check.md](features/text-check.md#why-the-rules-are-what-they-are).
- **Not shown any more**: a difference only in the capitals of the story's own words (the template's; a child's
  name in small letters stays red); a model remark that says itself there's no mistake; a remark only about
  where a line breaks (like commas and quotes — the owner lays out page 1 himself); the model's "a word is
  missing" when the program finds every word of the buyer's message on the page.
- **The name**: "Leo's" in the name field is the name "Leo" everywhere (the card, the print order title
  too) — covers say "{Name}'s" themselves.
- **New program rule**: a greeting or the "from whom" signature printed twice on the first/last page — yellow.
- **Another book's pages**: half the story spreads or more unlike the passport → one red finding shown as a big
  red banner (both books' covers), outlined pages, its own badge and print question; the passport can't be
  "updated" from such pages. Still never blocks printing (as decided on 2026-09-19): a question, not a lock.
  Not for light checks — Boys/Girls books may share a story.
- **For the next calibration**: the journal keeps the model's own verdicts and the owner's "Not an error";
  `app/tools/textcheck_replay.py` replays every check through the current rules.
- The First Bible Stories passport's three drifted words were fixed to match Canva (they were red on every
  order of that book).

## 2026-09-24 (evening) — A spread dropped in the Workshop becomes its two pages, flipped like his flipper

The owner: "when I drop a 2:1 spread, a second later it's two nice squares like in the passport, flipped by the
logic of my flipper" (his tools `mirror-alternate.py`, `slice-spreads.py` in `Etsy-Book-Pipeline`; his answers —
[raw/](raw/2026-09-24-workshop-flipper-owner-answers.md)).
- **The flipper's rule, automatically**: 4–5, 8–9 … 28–29 (the left page divides by 4) are mirrored on the drop;
  **⇄ on the frame** mirrors any spread by hand (his pick of three).
- **A narrower picture is cut top and bottom** to make the two squares (his answer; his slicer skips it, and the
  Workshop used to take it whole with a mark). A wider one loses its sides, like his slicer.
- **Only the two pages are kept, not the panorama** (his answer). They are PNG, so ⇄ twice gives back the same
  pixels; ⇄ mirrors the pages and trades them, which is exactly mirroring the whole spread.
- This replaces "a picture that isn't 2:1 is taken whole and marked" for spreads; the cover and pages 1 and 30
  keep it.

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
The agent's plan was approved without changes (his words in
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
(plan, sources in [raw/](raw/2026-09-23-mockups-owner-answers.md)). Nothing
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
disappears when the first one is cancelled (`outcomes.apply()`, the `further_orders` it keeps); three
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
  problem sooner. To be honest: the "5–10 s" savings promised at the time didn't materialize — the
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
  pipeline best, and go for it"). Answers to the open questions of the time:
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

- **Decision (the owner):** deferred. No paid subscription — the key is the AI Studio free tier. **Why:** the pages only have the book's
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

- [How to work with the owner](owner/working-with-owner.md) · [Known limits](dev/limits.md) · [Log](log.md)

## The safety switches stay on the computer (2026-10-04)

`security.etsyKyivOnly` and Printify's `readOnlyFrom` / `manualApprovalConfirmedAt` never go into an exported settings file and are ignored on import. Why: a file made on a colleague's copy (where they are off) must not switch the owner's rules off. How to apply: new rules of that kind are added to `transfer._computer_bound()`.

## The portable copy has its own private repository (2026-10-04)

The owner: «створи окремий приватний репозиторій, там веди тільки мою версію». `raymanrboy/book-studio-portable` (private, branch `main`, remote `origin`) holds only this copy; the ordinary Book Studio keeps `raymanrboy/book-studio`. Why: the copy has been changed in dozens of ways that must not reach the original, and the history was shared only up to 2026-10-04. How to apply: push only here and only when the owner asks; never add the original's remote; `app/data`, `app/bin`, `pipeline/books`, `.secrets.txt` stay out (`.gitignore`). The colleague build is a different thing — one neutral commit, no remote.

## The repository is self-sufficient (2026-10-04)

The owner: the plan, the launchers and the wiki must live in the repository, so that it alone is enough. `ROADMAP.md` and `portable/` (the three `.bat` and `ПРОЧИТАЙ.md`) are in the repository root; the files in the portable root are copies laid out by `app/tools/setup_portable.py`, which also builds a new portable folder from a clone (launchers, an empty `runtime/` with a note, a copy of the PC's Python with pip, the shortcut) and names what is still missing. `runtime/` itself (Python, ffmpeg, Photoshop, templates, Antigravity) and the owner's data stay out of git — size, licences, privacy; [how to restore them](dev/portable-setup.md). How to apply: change a launcher or the note in `portable/`, then run the script; the colleague build takes the launchers from `portable/` and writes its own note and no roadmap.

## Nothing the owner's data holds is lost by one bad write (2026-10-04)

The owner, after the accident with the made-up data: precautions so that data is not overwritten and what is deleted goes only to the Recycle Bin, so that it can always
be restored. Done as layers ([data safety](architecture/data-safety.md)): a history of every write of the important files, a daily snapshot, a guard that keeps the send
journal add-only, tests and the preview unable to reach the real data, the owner's slide sets to the Recycle Bin, and `tools/data_history.py` to put a version back. How to apply:
a new file that holds the owner's work gets a rule in `core.HISTORY_RULES`; a new deletion of something he made uses `desktop.to_recycle_bin()`.

## Pictures keep the same address across restarts (2026-10-04)

The owner: the listing covers never change, so the program must not fetch them again after every restart — keep them. Done with a key of the pictures' own
(`server.MEDIA_TOKEN`, kept in `app/data/media-key.txt`) instead of the per-launch session token in `/media/` addresses: the window's cache keeps what it has shown
(the library's pictures are `immutable`; the Workshop's revalidate with an ETag). The key opens pictures only, never the API. How to apply: a new picture route is `auth="media"`
and its links come from `media()` in the page or `MEDIA_TOKEN` on the server.

## Logs: collected by default, kept a week (2026-10-04)

The owner, after the program closed under an open window: collect logs by default and clean them every 7 days, so bugs are caught. `app.log`, `gelato.log` and
`printify.log` start a new file every day and keep the last 7 (`core.LOG_DAYS`); the window's life (why it counted as closed, gaps between pings) and the page's
uncaught errors go into `app.log`. The send journal (`logs/sends`) and the text-check journal (`logs/checks`) are records of what was done, not logs: never cleaned by this.

## The order archive keeps the same page once (2026-10-04)

The owner, after the research into duplicate files: store only the pages that are needed. The archive holds each picture once — the same illustration in many
children's books is one file with a name in each entry (a hard link). A page counts as the same by its picture, not its bytes: Canva writes its own text into every
export, which is not printed and not kept for the later copies. Each entry stays whole and on its own (its `entry.json`, its file names; removing it leaves the others).
How to apply: anything that puts files into the archive goes through `archive.store()`; never edit an archived file in place (all its books would change).

- **2026-10-05 — ads and new-listing fees are counted into the Profit totals as a flat $1.38 a day, with no card of their own** (the owner: count it, but keep it out of the main view). Constant `OVERHEAD_PER_DAY` in `app/web/js/pages/profit.js`. Etsy's ledger (read since the same day, scope `transactions_r` the program already has) checks it — the decision below.

- **2026-10-05 — the Profit page checks itself against Etsy's payment ledger** (the owner: "if it all matches, our sums are right"). The
  first card showed the Etsy balance («Доступно до виводу») with the program's expected sum under it — **taken off on 2026-10-06** (the
  owner: "remove it completely, return it as it was": the first card is the period's «На руки (Etsy Net)» again) — and a row whose real Etsy money
  differs gets a mark (stays). The formula stays the source of the numbers until the owner has compared; the ledger only checks it. Read only,
  with the scope the program already has (`transactions_r`). [features/profit.md](features/profit.md)
- **2026-10-05 — the Printify token is optional**: no warning, no mark, no Printify in the Profit header without it — every order goes
  through Gelato.
