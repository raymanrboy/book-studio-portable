---
title: Decisions
type: decision
updated: 2026-10-28
code: []
---
# Decisions

This page holds the current decisions (from 11 October, and the 4 October safety ones). Earlier ones: [September](decisions-2026-09.md) and [1–10 October](decisions-2026-10-early.md) — `grep` them before changing a behavior that is not covered here.

## 2026-10-28 — A third size: Hardcover 11×11, by the buyer's chosen variation only

- **The owner:** a new option, the 11×11 hardcover, on his Gelato template «Hardcover 11x11»; the same Canva files as the
  8×8 and 5×5 ("нічого не змінюється"), the orders must go to the right Gelato product, and the size must be named
  correctly everywhere. The Etsy variation will likely be «11.11 Hardcover».
- **Decision:** a fourth Gelato format `hardcover_11x11` (the template's product, read from Gelato). An order is the 11×11
  only when its **chosen variation** says so — never by the listing's title, which may list every size: printing an 8×8
  order as an 11×11 costs more than the owner switching the format in the Order Creator. Never Printify's.
- [Printer rule](rules/printer-rule.md), [Gelato](integrations/gelato.md).

## 2026-10-28 — Listing descriptions: hardcovers are matte only

- **The owner:** there is no choice between glossy and matte — every book is matte.
- **Decision:** the description template's 8×8 hardcover line now says "with a soft matte finish"; the saved `listing-seo.md` of
  books 34–45 changed too. The published listings are changed by the owner on Etsy.

## 2026-10-27 (later) — Back to 2:1 and the outpaint; «Два квадрати» taken out; the 2:1 picture gets a layout guide

- The owner tested one more way on book 44 (`Cover Squares Test/prompts/44-santas-workshop-wide.md`): one 2:1 picture
  **filled with the scene edge to edge** (no cream ground, no light patch), the title painted in its right area and a
  big empty room left for the name, with a **2:1 layout guide** attached (where the title and the name's room go). He
  chose it: "переходимо на цей підхід з OutPaint… Прибирай цей інструмент [квадрати]".
- **«Два квадрати» taken out** of the tool, the server and Agent 6 (the owner's answers: only the squares, the tool
  «Обкладинка» stays with 2:1; Agent 6 — only 2:1, no question). The full-scene squares of earlier today and their guides
  are gone with it. A Cover.png made of squares stays its book's until a new one.
- The cover tool's «Генерувати» pastes the reference, the guide (picked by the title: «{Name}'s …» → the name's room
  above the title), then the prompt with the guide's words; the margins are outpainted as before.

How to apply: Agent 6 writes one 2:1 prompt by its full-scene formula and no `layout_guide` (the tool adds it).
[features/cover.md](features/cover.md), `pipeline/playbook/agents/6-wraparound-image-director.md`.

## 2026-10-27 — The grandmother's reference is the finished cover, without the wrap

The owner: the photo mockups must take the cover as it is inside the contour, not with the margins that fold round
the hardcover's boards — otherwise the generator draws a wrong book. The Canva cover is cut to its finished size when
it comes into `mockups/`; one kept before is cut once, the whole file to `.replaced/`.

How to apply: a picture of the book for a generator shows only what the reader sees.
[features/photo-mockups.md](features/photo-mockups.md)

## 2026-10-27 — All & Open 1: the back cropped as the front is

Since the two squares the back is a full scene of its own, so the owner wants to frame it in the «All & Open» mockup the
way he frames the front. The crop window gets a second frame over the back where the back shows (only All & Open 1 of
the three); each side is moved by itself, ↶ resets both, «Зберегти» keeps both.

How to apply: a side shown in a mockup gets its own window; a picture saved without one draws exactly as before.
[features/mockups.md](features/mockups.md#drawn-without-photoshop-since-13102026)

## 2026-10-24…27 — «Два квадрати» tried and dropped (superseded by the 2:1 decision above)

- **Tried:** the back and front as two squares (Gelato's 8×8 template: 458×246 mm, 20 mm wrap, spine 226–232), the title painted into the front, an empty room left for the name (never painted — the owner sets it in Canva), Book Studio filling the spine from the squares' edges, a layout-guide picture with each prompt. Why it was wanted: a square centres the title by itself and the spine needs no outpaint.
- **Kept from it:** the cover is a step of its own, the tool «Обкладинка» (`#/cover/<book>`); layout guides with the prompt (the owner: "значно більше контролю"); the tool generates from itself (reference, guide, prompt).
- **Dropped 2026-10-27:** the owner chose the 2:1 full-scene picture with outpaint; the squares code and guides were removed.

## 2026-10-27 — Girl archetypes G4 and G6 dropped; the numbers stay

The owner does not use the olive/Mediterranean (G4) and South Asian (G6) girls — removed from `pipeline/playbook/knowledge/archetypes.md`.
He asked why the numbers skip and chose to keep them (a number means the same child in every book; book 41's variants are G1, G2, G3,
G5, G7). The boys' B1–B7 are unchanged.

## 2026-10-27 — No metadata in the pictures and videos of a book's etsy/

- The owner: Etsy now checks the photos' metadata; nothing in it should draw its attention. Every picture and video put
  into `etsy/` loses all of it — C2PA, XMP, EXIF, ICC, text chunks, comments, a video's tags and dates. Only what comes in
  from now on: the files the books already have stay untouched (the owner: "ті фото книжок що вже є в нас, їх думаю
  можна не чіпати").
- Cut out chunk by chunk, not re-encoded, so no quality is lost and a clean file is never touched again; re-encoded only
  where the look would change otherwise (a rotation, a non-sRGB profile). SynthID-style watermarks live in the pixels and
  stay — this is metadata only.

## 2026-10-21 — Profit gets a second page: the owner's whiteboard calendar

The owner keeps a month calendar on a whiteboard, a red dot for each sale, the week's sum at the end of each row, the month's
beside it, and wanted it in the program: "a second desktop in Profit, I click an arrow and switch to it, just a visual dashboard;
hovering a day shows what I earned and how many sales". Then: "the dots red, as on my board; cuter, smoother, cosy — circles,
not squares; the hover card not so brutal".
- **The sum is the profit** (his board's 208 $ for ~40 sales of October is the profit, not the money in) and the cards' own:
  `kpi()` with that day's ads, so the month equals «Цей місяць».
- **Calendar weeks** Mon–Sun as on the board — not the payout weeks of «Цей тиждень».
- **Red dots** here although red elsewhere means a loss: they are his board's marker; the calendar alone is styled softer.
- [features/profit.md](features/profit.md).

## 2026-10-19 — The text check calibrated a third time, against the print archive

The owner: "a bit more data has gathered on the proofreading, calibrate — dig well, pull the pages from the archive to compare;
there were a few exceptions where clients asked for edits in private messages, I don't remember which orders, but it's obvious".
- **Done on** 103 journaled checks; every finding the rules still showed was looked at on the archived print files.
- **The exceptions found** (edits asked in Etsy messages): Eloise 4206086560 (dedication rewritten) and James 4197201764 (the reprint
  with «James'»). Their rows are **not** turned into rules — they stay shown, as they should for an ordinary order.
- **Left red on purpose**: a misspelt name read by the model on a correct page (Eliana, p. 23) — rare, and a misspelt name is the
  check's main catch. A second, closer look at such a page is a possible next step.
- **A passport, not a rule**: the Sleepy Trucks passport's cover («Good Night, Little Trucks») differed from Canva — on the owner's word
  it is now «Sweet Dreams {Name}» (`library.update_texts()`, as «Оновити паспорт» does; the old `book.json` kept in
  `data/merge-backup/2026-10-19-sleepy-trucks-cover/` and in the history).
- The rules — [text check](features/text-check.md#why-the-rules-are-what-they-are).

## 2026-10-19 — Ollama starts with the program, hidden; the model is asked for when a new order is opened

- **The owner** remembered the old start-up warm-up (removed 05.10 in the speed audit) and chose two of three offered options: «1 + 2 — роби».
- **Decision:** (1) 8 s after the start Ollama itself is started — **without the model**, so the graphics card stays free
  (`textcheck.run.start_quietly()`); (2) the model is asked for as soon as the card of a new, not yet sent order opens
  (`warmModel()`), not only when it takes files — its first read off the disk (~70 s) happens while the files are made in
  Canva. The model still goes off the card after a check (and 2 min after a warm-up with no check).
- **Nothing of it may be seen** (the owner, same day: «нічого з цього я не маю бачити, все в фоні»): every start the
  program makes by itself is `ollama.exe serve` with `CREATE_NO_WINDOW` — never the PC's tray app `ollama app.exe` (its
  icon and its helpers' black windows). Only Settings → «Запустити» still opens the tray app on a PC install.
- **Made-up or test data never starts Ollama** (`core.SANDBOX`, checked in `start_ollama()` itself, so every path obeys): the
  first version of this change started the PC's own Ollama from the test run (the UI smoke test opens a new order's card).

## 2026-10-18 — Etsy titles: the first blocks split by « | »

- **The owner** showed his own title — `Personalized Christmas with Grandma Book with Name | Grandma Christmas Gift from Grandchild |
  Little Bear Story, Cookies & Cocoa Keepsake` — and asked for every title like it: one or two ` | `, then commas.
- **Decision:** `seo/knowledge/rules.md` §2 and `/etsy-seo` say so; `seo.py lint` gives an error for any other count of `|`
  (before, the rule was commas only).

## 2026-10-18 — A reprint with new files is a reprint; it is «in progress» while made; a tab per print

**The case:** a buyer complained about the possessive on the cover («…'s» → «…'»); the owner sent the fixed book to Gelato from the order's
card. The program took that send for a normal order: the newest Gelato order of the receipt's name became «the» print, the first
one the extra; the order stayed among the shipped; the card showed one print; the replacement picker hid the reprint, so the
costs came out under swapped labels (the total was right: $10.47 the first print with Gelato+'s free shipping of 1–8 October,
$18.30 the reprint).
**The owner decided:**
- **«Передрук» tick in the Order Creator, set by itself** for an order already printed; he takes it off when it is not a reprint
  (asked: ask every time, or tick by itself — «б»).
- **While the reprint is made the order is «Друкується»** with a «передрук» mark, then back to its stage. *Revises* 2026-09-18
  («a reprint doesn't change the stage»).
- **A tab per print** on the order's page (asked: tabs or a list inside — «вкладки»), the newest open.
**The agent decided (engineering):** the earliest order naming a receipt is its own (not the newest); the replacement picker
offers every order, the current first print marked; a reprint with new files keeps `reprint: true` in the archive (14 days from
its own shipping). That order's records put right by hand (backup copies kept outside the data folder). Pages: [order-stages](rules/order-stages.md),
[order-creator](features/order-creator.md), [orders](features/orders.md), [archive](features/archive.md).

## 2026-10-17 — Every book's outer picture: the characters low on a milky cream ground, the title space above them

The owner sent five competitor covers as the format for all our next ones: the picture sits on a clean white, light ground with plenty of
empty space for the title. Agent 6 now makes every wide image by this **light-ground formula** (the characters large and close in the
lower right, a small vignette dissolving into white or the characters alone on white, the upper right plain white, the left area almost all
white); the full-scene and solid-color grounds (books 38–45) stay only on request. First tests: three versions for book 40
(`cover-white-tests.md`). **After the first test the owner corrected it:** the ground milky cream, not white; the characters much lower
and smaller with real empty space above their heads (in round 1 the heads nearly touched the top); the left area with a minimal but
present sprinkle of small details, not empty. Round 2 of the tests has these, and **the owner approved it** ("I like this approach") — its three pictures are saved next to the examples. **It applies from book 46 on**;
older books keep their outer images unless he asks. A soft colored ground instead of cream is allowed on his request (book 42: a muted red). [The examples and their analysis](raw/2026-10-17-white-cover-examples/SOURCE.md) · the rule —
`pipeline/playbook/agents/6-wraparound-image-director.md`

## 2026-10-16 — Antigravity is given up: Book Studio starts no IDE, only puts the agent's words into the clipboard

The owner decided to abandon that IDE. «+» and «Відкрити агента» now only copy the words (`agent_words()`) and the owner pastes them into
any agent or harness; the `antigravity()` finder and the window start are gone from the Workshop. The words with full paths stay (they
were made for an agent that picks its own folder). *Left in place, unused by the Workshop:* `portable.antigravity()` / `antigravity_launch()` and the
`runtime/Antigravity` check of the portable copy — to be removed if the owner wants the program fully clean. Supersedes the start-only
decision of 2026-09-26 below. [features/workshop.md](features/workshop.md)

## 2026-10-15…18 — The Canva extension does not do orders; it only makes books (mostly)

- **15.10:** the extension edited the owner's template in place for an order (copy "<receipt> - <child>", `{Name}` → the child, PNG download, Book Studio took the ZIP). The dedication, «від кого» and the cover's name stayed the owner's (buyers write them messily; an AI tidy was weighed and dropped).
- **18.10:** the order mode was removed whole (`early.js`, `order.js`, the panel steps, the ZIP route). Then three steps came back (extension 0.4.0): the template's copy made and renamed by itself, the copy's first page deleted, the downloaded archive caught by the card. The name replace, the dedication fields and the download press stay gone.
- [features/canva-extension.md](features/canva-extension.md)

## 2026-10-14 — After the audit of the program's functions: the queue warns, orders refresh hourly

Three agents read every feature page and the decisions; the owner said yes or no to each finding.
- **Yes:** Etsy's ship-by date in the queue (red once past); a refused Gelato payment in red and a draft forgotten for 12 h
  in amber; an order of several books is listed under «Нові» until all are ordered (open since 22.09; its stage is kept); the period's sales and profit
  by listing on the Profit page (instead of Etsy's CSV); the backup checked every 6 hours, not only on launch; the
  period's Offsite Ads under «На руки» (he keeps Offsite Ads on); **orders refresh quietly every hour** — this replaces the
  rule of 2026-09-15 (launch + button only).
- **No:** archive files kept longer than 14 days; fixed costs (Gelato+, Payoneer, the FOP tax) in Profit; the September
  orders' October refunds; any Etsy automation (marking shipped, draft listings — Etsy stays read-only); several books on one
  listing; automating the Canva step for now (he asked for a worked-out proposal first).
- **Not needed:** the receipt number in Gelato's references — all 31 sales since 1.10 already match by it.
- The listing slides' numbers are **30 pages / 14 poems** (were 24 / 11).
[rules/order-stages.md](rules/order-stages.md) · [rules/sync-policy.md](rules/sync-policy.md) · [features/profit.md](features/profit.md)

## 2026-10-13 — The Mockups are drawn by Book Studio; Photoshop only bakes a template once

The owner asked whether Photoshop could go from the Mockups ("just a discussion"), then "let's try". A pilot baked the six
templates (calibration renders in Photoshop) and drew real books equal to Photoshop by eye — the sheet of six was shown.
- **A run draws every baked template itself** (`mockup_render.py`): no "run this script?", nothing left open, ~30 s for ten
  pictures with their cut-outs; the PNGs are named and sized as before, so the slides, the cut-outs and `etsy/` go on unchanged.
- **The owner's touch moves into the program** (the owner: "a mini editor just for cropping, like the Canva one, but only
  cropping — the program already puts the right half of the 2:1 picture where it belongs; if it looks right I edit nothing"):
  a crop window on Cover 1, Cover & Open 1 and All & Open 1, the crop per template.
- **Colours** (the owner): the open book's edges take the cover's edge colours "as with an eyedropper"; the background he
  picks himself — only in the two softcover scenes ("the blue background, the two with long names"); "an automatic best
  pastel would be nice" → pastel suggestions from the cover's hues, the first used by a run; **one background for both
  scenes** (my suggestion, he agreed — the listing looks one set). **Dedication needs no colours**: its desk colour is fixed
  in the template, its floor is cut away.
- **Open 1, Open 2 and Dedication are kept only without their background** (the owner: "if the ones with the background
  aren't needed, don't save them"); Cover 1 keeps both (the photo mockups' reference — the owner agreed), the scenes stay
  whole.
- **Photoshop stays** for a template not baked or changed since (the stamp), and to bake: `app/tools/mockup_bake/`.
- The owner allowed installing any tools; an agent may answer Photoshop's "run this script?" by itself while he is away
  (13.10.2026) — `WarnRunningScripts` is still his alone.

How to apply: a new or changed template is baked (`bake.py`) before it is drawn; the owner's choices in the crop window
belong to that run's pictures only.
[features/mockups.md](features/mockups.md#drawn-without-photoshop-since-13102026)

## 2026-10-13 — Etsy's ledger is the source of the Etsy money; the formula only forecasts

The owner, on learning the page computed what Etsy's ledger already says: «навіщо ми рахуємо самі, коли є точні цифри».
Research on his data (14.09–13.10.2026, 761 entries): the chain of entries whole (no number missing, every balance follows),
every sale in the ledger, 760 of 761 entries tied to their receipt by Etsy's own reference (one by the moment — 4 cents,
18.09), a sale posted 5–7 seconds after it (the longest 29 minutes), the ads charged once a day ~07:40 for the day before.
- **A row's Etsy Net is the ledger's** (Offsite Ads, a state's fee, refunds and cancellations as Etsy made them); until Etsy posts
  the sale it is the formula's **forecast** — faint, with a clock (the owner's "buffer"). The formula's sum is kept beside it.
- **The ads and new listings come from the ledger by day** instead of the flat $1.38 (on 11.10 the owner raised the ads budget (now
  $5 a day, the owner 13.10): Etsy charged $4.96 + 20% VAT = $5.95 for that day, the flat sum knew nothing of it). The days Etsy hasn't charged yet are forecast with
  the last charged day's ads. Still no card of its own (the decision of 2026-10-05 below).
- **A day without sales still pays for the ads** (the owner, 13.10: «роби»): until then the page took them off only when the period
  had a sale, so «Сьогодні» with no orders showed $0 though the ads had cost ~$6. Now the profit is that loss, in red.
- **The Profit periods follow the payouts** (the owner, 13.10): on view «Сьогодні · Вчора · Цей тиждень · Цей місяць · Увесь час»,
  the rest behind «Ще» («Минулий тиждень», «Минулий місяць», «30 днів», «Свій період»). A week runs from one Payoneer payout to
  the next — the owner's real rhythm of money; it shows what was earned between payouts, not the payout itself (the balance
  carries some over — the «Доступно до виводу» card stays off).
- **The ledger checks itself**: a break in the chain is a warning on the page, and the next sync reads the ledger from the start.
- Not now (the owner: «це ще рано»): the payout to the card, bank fees, taxes in Ukraine. Gelato's cost is exact already.

How to apply: a number Etsy (or a printer) reports is shown as reported; a rule of ours only stands in until it comes.
[features/profit.md](features/profit.md) · [rules/reconciliation.md](rules/reconciliation.md)

## 2026-10-11 — Etsy SEO: the book's listing photos go to Google Drive

- **The owner:** at the SEO step, make the book's folder on his Google Drive and put the listing photos from the Etsy folder in it.
- **Decision:** `/etsy-seo` step 7 runs `seo.py to-drive <n>`: `pipeline/books/<n>.<slug>/etsy/` → `G:\My Drive\MoonMeadowStories\<n>.<slug>\`.
  It **copies** instead of moving — the Workshop counts the listing slides in `etsy/`, so moving would make a finished book look
  unfinished. Never overwrites or deletes; an existing Drive folder of the same number is used.

## 2026-10-11 — Etsy SEO: each listing keeps its own angle (sharing tags was weighed and dropped)

- **The owner** first objected: "the more of my books one search shows, the better" — then, told that the "own angle"
  comes from sellers' advice (Etsy may show only a few listings of one shop per search page; unverified), said "go back,
  do it the way you did".
- **Decision:** `/etsy-seo` keeps giving each listing its own angle (`seo/knowledge/rules.md` §3); a best-fitting tag may
  still be shared by a few listings. Books 39 and 40 stay as made. Don't re-ask unless the shop's own Stats show
  otherwise.

## 2026-10-11 — The Mockups follow the book's folder, not the page's session; the slides' editor picks a book

- **The owner:** "the mockups for Christmas with Grandma are made, but the program shows there are none"; "I redo one mockup —
  the whole session goes and I can't get to the next step even when everything is done"; "in the listing slides I can't even
  choose the book to make the slides from".
- **Decided:** with a Workshop book chosen, the Mockups read its `mockups\` as it is and show it; step 4 «Слайди для лістингу» is
  there whenever that folder has mockups for the slides (no demo book, no run on the page needed), and slides already made show
  as made with «Доробити» for the rest. The slides' editor got «Книга ▾»: a book with slides opens them, one without goes to the
  Mockups for it. **Not changed:** what a run makes, the run's own result card, a partial run not ticking the «Мокапи» step.
  Pages: [mockups](features/mockups.md), [slides](features/slides.md).

## 2026-10-11 — Agents may browse Etsy as a visitor (never signed in)

- **The owner:** "you may open Etsy from this computer; you just must not log in to My Account. Using Etsy to search listings
  or shops and to do analysis is allowed." (He wanted competitor shops researched for new listing ideas — see
  [book ideas](owner/book-ideas.md).)
- **Why the old rule (never open Etsy from Wrocław) existed:** a foreign IP signing in to the shop's account could get the shop
  blocked. A signed-out visit has no account to block, so the risk it guarded against isn't there.
- **Kept:** no sign-in to the owner's Etsy from here (sign-in only on the Kyiv PC); Etsy stays read-only; no clicks that change
  anything; a CAPTCHA or bot check is never bypassed. **Unchanged:** the program's own `security.etsyKyivOnly` setting and
  `_open_url()` guard — they govern the program, not agents. Pages updated: [security](security.md), `AGENTS.md`, `/etsy-seo`,
  `seo/knowledge/rules.md`, [overview](overview.md).

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

## Early October additions (2026-10-05)

- **2026-10-05 — ads and new-listing fees are counted into the Profit totals as a flat $1.38 a day, with no card of their own** (the owner: count it, but keep it out of the main view). Constant `OVERHEAD_PER_DAY` in `app/web/js/pages/profit.js`. Etsy's ledger (read since the same day, scope `transactions_r` the program already has) checks it — the decision below.

- **2026-10-05 — the Profit page checks itself against Etsy's payment ledger** (the owner: "if it all matches, our sums are right"). The
  first card showed the Etsy balance («Доступно до виводу») with the program's expected sum under it — **taken off on 2026-10-06** (the
  owner: "remove it completely, return it as it was": the first card is the period's «На руки (Etsy Net)» again) — and a row whose real Etsy money
  differs gets a mark (stays). The formula stays the source of the numbers until the owner has compared; the ledger only checks it. Read only,
  with the scope the program already has (`transactions_r`). [features/profit.md](features/profit.md)
- **2026-10-05 — the Printify token is optional**: no warning, no mark, no Printify in the Profit header without it — every order goes
  through Gelato.

## Related

- [How to work with the owner](owner/working-with-owner.md) · [Known limits](dev/limits.md) · [Log](log.md)
