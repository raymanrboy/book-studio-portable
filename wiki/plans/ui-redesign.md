---
title: The interface redesign — one system, and a program you understand without hints (plan)
type: plan
updated: 2026-09-30
code: []
---
# The interface redesign (plan)

> **Agreed on 2026-09-30**; part B decided by the agent the same day at the owner's word ("do it as you know").
> **Built on 2026-09-30** — see «Progress» below; the decision — [decisions](../decisions.md). The owner asked for a professional UI/UX pass with eight design skills (installed into `.claude/skills/`:
> `uxcraft`, `planning`, `product-design`, `ui-design`, `frontend-design`, `frontend-design-v2`, `ui-verification`,
> `typography-audit` — texts only, not in git). The audit: every page on made-up data (`dev_server.py --sample`) at
> 1440, 1024, 900 and 800 px, dark theme; the styles measured; the flows read from this wiki.

## The owner's words (2026-09-30)

After the first report he agreed with part A, then named the real pain: "the design isn't intuitive… the functions
are scattered over the interface as if someone spilled grain — there's no shared structure, and above all no work
of an interface designer who knows where each thing belongs, where most clicks will be, what must be in front of the
eyes and what can hide… It's convenient for me because I built it, yet even I get confused and lost. I want to sit
down and know at once where to click, with no labels and hints: everything needed in front of the eyes, everything
extra appearing when needed." He wants the most time and effort put into this part (B).

## Part A — one system (agreed)

**Found** (2026-09-30):
- The type drifted: the agreed scale is 7 sizes (11.5 / 12 / 12.5 / 13 / 13.5 / 15 / 25 — [ui-principles](../owner/ui-principles.md)),
  the styles hold 24; 6 font weights. ~80 radii written as numbers beside the 4 radius tokens; 38 colours outside
  the token blocks (23 in `listings.css`); 139 `style="…"` in the pages' markup.
- Every page's header is built differently (the Order Creator's title is «Printify»; the passport's back arrow sits
  alone above its title; the Workshop book has 6 header actions with «Папка книги» the loudest; Profit's actions in
  the header, other pages' in the toolbar).
- A half-screen window (beside Photoshop): at 1024–1100 px the Order Creator and the Mockups fall into one column
  and the book's structure — the drop zone — goes below the screen; four different breakpoints (700 / 900 / 1100 /
  1280 px).
- `--text-4` (the faintest grey) is text 43 times at 2.6 : 1 (AA needs 4.5).
- The Order Creator's address fields are labelled only by their placeholder (a filled form can't tell «Місто» from
  «Штат»); Settings shows a filled orange ✓ beside every empty key.
- Silent disabled buttons left: «Нова книга → Створити», the import dialog's «Імпортувати» — against the owner's
  rule of 2026-09-23.
- States: a new order's card is one step and emptiness; Profit shows «$0.00» / «0%» in colour before 1 October;
  the orange accent (it means *an action* in the Orders mode) paints a number.
- Technical words on screen (`endpage-prompts-json.md: …`); the library cards' four status squares explain nothing.
- `outline: none` on the library cards, the Mockups' spreads and the passport's fields — focus to be checked.
- The flows' safety is strong and stays: the guards before print, the Recycle Bin, `.replaced/`, «Повернути»,
  Ctrl+Z in the editor, confirmations named by their verb.

**The system**: the same "Prepress" look, made strict — 7 interface sizes (+ the books' own), 3 weights; spacing
4/8/12/16/20/24/32; radii and colours only from tokens; **one page header** (back · title · subtitle · actions on the
right, the one main action last); one field with a visible label; shared empty / loading / error blocks; no silent
grey buttons; three widths (≥ 1280 as now; 1024–1279 two columns with a narrower right one; < 1024 one column with
the structure still at hand).

**Kept**: the modes' inks and the theme, the fonts, the routes and flows, the owner's layouts (the card's data on the
right, the Workshop's moderate width, step cards), every guard and confirmation text, the slides' canvas, the server.

## Part B — a program you understand without hints (research, 2026-09-30)

**Two jobs** (from [the order path](../flows/order-to-print.md) and [the Workshop](../features/workshop.md)):
1. **Fulfil an order** — daily, many times a day: order → Canva → files → proofing → print → the printer ships → mark
   shipped on Etsy → (rarely) reprint.
2. **Make a book and its listing** — a project of days: formula … pictures → cover → Canva → mockups → photos →
   slides → library.
Rarely: Profit (weekly), Settings.

**Why it feels like spilled grain** — the program is laid out by *how it was built* (a page per tool), not by *how
the owner works* (an object and its path):
1. **One order lives on three rail items.** The queue and card (Orders) → «Друк» jumps to the Order Creator (another
   rail item, another layout, the address shown again) → once printed, its files and «Передрук» are in the Order
   archive (a third item), while its card only says "print again only for a reprint".
2. **One book lives in two modes and five places.** The Workshop book (Listings); its steps «Мокапи» and «Фото» send
   the owner to the Mockups and Фотомокапи pages (other rail items), where the book is chosen again; the slides'
   editor; then the library passport (Orders mode), which says "change it in the Workshop".
3. **The rail's weight doesn't follow use.** Six equal unlabelled icons in Orders: the queue (all day) beside the Order
   Creator (now mostly reached from the card), the archive (occasional), Profit and Settings (rare). A printer = the
   Order Creator, a sheet with a clock = the archive — meanings to remember, not to see.
4. **The mode switch is hidden** in the brand icon (an affordance nothing shows).
5. **Rare and frequent actions look equal.** Rows of unlabelled icons in the headers (the passport: 4 + 4, the
   Workshop book: 4 + 2 buttons); the one next step isn't the loudest thing on the screen.
6. **The path is shown only in the Workshop.** The order card shows its first step only — not «Canva → Файли →
   Вичитка → Друк → Відправка»; the queue doesn't say what each order needs next; its tabs are four icons, and the
   truck tab — a *to-do* (mark shipped on Etsy) — looks like a filter.

**The proposed structure** (to be decided point by point):
- **Every object has one home and one path strip** — the Workshop book's strip, reused for an order: where it is and
  what's next, the next step the loudest button.
- **An order is one place**: the print step happens inside the card (format, title, address prefilled, «Створити
  чернетку», the result); once printed, the card *is* the archive card (what went to print, «Передрук»). The Order
  Creator stays for orders without an Etsy receipt, off the main rail.
- **A book is one place**: the Mockups, the photos and the slides open as the book's own steps, inside the book; the
  standalone pages stay only for work without a book (the templates).
- **The rail follows use**: the everyday places first, labelled (a word under each icon); the rare ones lower;
  the mode switch visible.
- **The queue as a to-do list**: tabs in words («Нові · Друкуються · Позначити в Etsy · Відправлені»), each row with
  its next step.
- **Actions by frequency**: the next step — a labelled accent button where the eye ends; frequent — icon + word;
  rare — in «…».

**Open decisions** (asked one at a time): the order as one place (the Order Creator and the archive folded into the
card); the book as one place (the Mockups, photos and slides inside the book; later maybe the library and the Workshop
as one «Книги»); labels in the rail; a visible mode switch; the queue's tabs in words. Each revises a decision in
[decisions](../decisions.md) (2026-09-15, 2026-09-18, 2026-09-24) — the owner's answer is recorded there.

## The owner hands the decisions over (2026-09-30, later)

"I trust you completely. Do it as you know… run one more audit with all those skills, exactly on my pains." And a
thought, "not a requirement": the program is really a set of tools glued into one, and sometimes he'd like to use each
tool on its own. "You're the expert, you're the boss. Be creative, go beyond the frame, make something beautiful."
So part B's open decisions are **decided by the agent** — below, recorded in [decisions](../decisions.md).

## The second audit — on the owner's pains (2026-09-30)

- **uxcraft** (heuristics: recognition over recall, consistency, visibility of status): the rail is recall — 6 + 3
  unlabelled icons in two hidden sets; an order and a book are each spread over several rail items; the queue's
  to-do (the truck) is shaped as a filter; nothing shows "what's next" outside the Workshop.
- **product-design** (`rule/preserve-mental-model`, `rule/one-primary-action`, `rule/navigation-vs-action`): «Друк»
  in the card *navigates* to another section instead of continuing the order; a sent order's card says "reprint only"
  but its «Передрук» lives in another section; the Workshop's «Мокапи» step leaves the book. The safeguards
  (`rule/irreversible-action-safeguard`, `rule/destructive-names-action`) pass: the guards before print, the Recycle
  Bin, `.replaced/`, verbs on confirmations.
- **ui-design, audit** (`a11y-icon-controls-labeled` — named, but still recall; `slop-token-drift`): icon-only vs
  labelled controls per page — the passport 24 : 1, Settings 24 : 7, the Workshop book 19 : 30, the Order Creator
  14 : 5, the Mockups 12 : 3; no way to search the whole program; 38 colours and ~80 radii off the tokens.
- **frontend-design** (art direction): the identity is the program's own and stays; the generated tells here are
  the tracked ALL-CAPS labels over sections («ОБКЛАДИНКА», «РОЗВОРОТИ», «СТОРІНКИ КНИГИ», «ГОЛОВНЕ ФОТО») and the
  same card box for everything. Boldness goes to **one** thing: the path strip, drawn as a printer's control strip.
- **frontend-design-v2** (product workspace): clear regions — the rail (where), the object header (what and
  what's next), the work area; cards only where they group.
- **typography-audit** (`hierarchy-size-contrast`, `hierarchy-weight-contrast`): the agreed scale puts 5 of 7 sizes
  within 2 px (11.5–13.5) and weight 600 is used 84 times — titles, data and buttons alike, so the eye can't rank
  anything. **This is a direct cause of "I can't see what matters".**
- **ui-verification** (the built-in browser, made-up data): 15 Tab presses from the window's start to the first order
  (no skip link); no interactive target under 24 px; the focus shows everywhere checked (the cards' crop marks
  replace the ring on purpose); notices are a polite live region; `lang="uk"`.

## The new structure (decided 2026-09-30)

**Objects and tools.** Book Studio holds two kinds of things, and the new shell says which is which:
- **Objects** — an **order** and a **book**. Each has one home and one **path strip** in its header (where it is,
  what's next); the next step is the loudest button.
- **Tools** — the Order Creator, the Mockups, the photo mockups, the listing slides, the print archive. Every tool
  works **on its own** (opened from «Інструменти» or the search, nothing loaded) and **inside its object** (opened from
  the object's step with the object loaded, the object's header on top, back to the object). One module, two ways in —
  the owner's thought about separate tools, built in.

**The rail** (one rail, labelled, no hidden mode switch): **Замовлення** · **Книги** (the Workshop and the library
together) · **Прибуток** — a gap — **Інструменти** — at the bottom **Пошук** (Ctrl+K), **Налаштування**, the theme. The
inks stay and now follow the area: orders, profit and the order tools orange; books and the book tools cyan — the brand
square takes the ink of where you are. Alt+1…4 as before for the four places.

**Search everywhere (Ctrl+K)**: orders by buyer or receipt, books by title or number, every tool and place, a few
actions («Оновити замовлення», «Нова книга»). Enter opens.

**The order**: the queue's tabs in words with their counts, the truck tab named as the to-do it is («Позначити в
Etsy»); each row says its next step. The card's header carries the order's path — Canva · Файли · Вичитка · Друк ·
Відправка. «Друк» continues the order: the Order Creator opens *as the order's print step* (its header, its path, the
rail stays on Замовлення). A printed order's card shows **what went to print** and «Передрук» (from the print archive).

**The book**: one gallery «Книги» — «Створюю» (the Workshop's books) · «У магазині» (the library) · «Архів». A book's
pages keep their path strip; the Mockups opened from a book show the book's header and go back to it.

**Type** (replaces the scale of 2026-09-26): five sizes with clear steps — **12** (captions, chips, meta) · **13** (the
base: text, controls, lists) · **15** (a card's or section's title, key values) · **19** (an object's title, a
dialog's title) · **25** (a page's title); the books' own display sizes (Sitka titles, big page numbers) stay as named
exceptions. Weights: 400 for text and data, 600 for titles and the few values that must stand out.
Section labels in sentence case, not tracked capitals.

## Order of work

0. A guard: a test that the styles use only the scale and the tokens; screenshots of every page (both themes, three
   widths) as "before".
1. Part B's decisions with the owner → the new map of places (a wireframe of each changed screen before code).
2. Tokens (part A) → shared parts (the header, the path strip, fields, states, buttons).
3. The pages by object: the order (queue, card, print, archive) → the book (Workshop, Mockups, photos, slides,
   passport) → Profit and Settings → the slides' editor last.
4. Widths 1440 / 1280 / 1024 / 900.
5. QA: `ui-verification` (focus, keyboard, hit targets, overflow, themes, failed requests), `typography-audit`, a
   second `uxcraft` / `product-design` review; fixes and re-checks.

## Success

- Only the 7 sizes and the tokens in the styles (a test keeps it); one header on every page; one main action per
  screen; at 1024×768 the work and the book's structure both visible; every filled field labelled; no button ignores a
  press; Tab reaches everything with a visible ring; text ≥ 4.5 : 1 in both themes; tests pass, no console errors.
- **Part B**: every everyday task starts from the place its object lives and needs no page jump; the owner can say,
  from any screen, where he is and what's next; the everyday tasks take no more clicks than now (counted before and
  after for: an order from «Нові» to a draft; marking shipped; a reprint; a book's mockups → photos → slides).

## Progress (2026-09-30)

Built and checked on made-up data (the built-in browser and headless Edge; 1440, 1024 and 900 px; dark and light):
- **Tokens**: 241 font sizes, 77 radii and 13 heavy weights moved onto tokens; informational faint text lifted to
  4.7 : 1; section labels in sentence case.
- **The shell**: the labelled rail, «Інструменти», search (Ctrl+K), the skip link (2 presses to the queue instead of
  15), the ink by area, `navFor()` for pages that serve an object.
- **The order**: the queue's tabs in words and each row's next step; the path in the card and in the Order Creator of
  that order; a printed order's card with what went to print; the card's step numbers matching the path.
- **The book**: «Книги» with its tabs; the Mockups opened from a book show it and go back to it; «back» everywhere to
  the right tab.
- **Forms and states**: labelled address fields; the silent grey buttons answer (`markMissing()`); Settings' ✓ quiet
  until a key is pasted; the Profit's grey zeros.
- **Widths**: 961–1279 px keeps two columns (the card, the Order Creator, the Mockups).
- **QA**: `ui-verification` probes (no unnamed control, no target under 24 px except inline links and labelled
  switches, no horizontal overflow, the Tab walk), `typography-audit` (5 sizes + named exceptions; weight 600 kept for
  titles, buttons and the owner's bold values), a second `uxcraft` / `product-design` pass (the everyday tasks take the
  same clicks, without page jumps).

**Not checked**: a real drag of a ZIP from Explorer into the new card, a real send to Gelato, Photoshop — the flows
underneath did not change. **For later**: the passport's and the Workshop book's rows of icons could carry words for
the frequent ones; a real screen reader pass.

## Evening of 2026-09-30 — the owner's corrections

"More captions now… I want it to show, not tell" — the rail icons only, search last; the queue's tabs and the books'
tabs compact; the order's path as icons; the row's «Позначте в Etsy» (only opened the order) gone with every next-step
sentence; a real bug fixed (a Gelato order's card said Printify). **The light theme is the main one** — a light pass was
made on every page (screenshots of the pages in light: the card, the queue, «Книги», the Order Creator, Profit). The rules
are now an agent skill of their own (`book-studio-ui-logic`) — [design-skills](../dev/design-skills.md).

## The third pass — every page, every skill (evening of 2026-09-30, late)

The owner: "a full analysis with every skill, from all sides; be creative; think big; you're the captain" and "redraw the
least successful icons (I like ours — no over-engineering, only where needed)". **How it was done** — every page in the
**light** theme (screenshots), all 111 pictograms at 96 px and at 16–20 px, contrast / hit areas / type sizes measured by
script, the code read (long functions, every confirmation dialog, startup cost), then each skill's checklist **opened and
applied in its own format**: `ux-heuristics` (Nielsen + Krug, scored), `cognitive-load-audit`, `laws-of-ux`,
`product-design` (review mode, rule IDs, P0–P3), `typography-audit`, `make-interfaces-feel-better`, `icon-design`,
`book-studio-ui-logic`. *An honest note: the first quick pass the same evening used only four of them, loosely, and three of
its claims were wrong (colours in the Mockups — the pretend Photoshop, on purpose; «Скасувати» "written differently" — it is
the same word on all the dialogs; "six loud buttons on Settings" — they are six small ✓ save icons).* **Not verified:** a real
Tab walk (the in-app browser pane does not advance the focus), a real screen reader, Photoshop and the print flows, dragging
from Explorer; the first-open time of «Інструменти» (405–950 ms in the hidden pane, which does not run the animation frames
faithfully — to be measured in headless Edge).

### Done in this pass (the first two waves, 2026-09-30 late)

- **Wave 1** — `--text-3` in light to AA; leading in three tokens; one press scale (`--press`); weights 500/700 cleaned (the soft
  printer chips and the tooltips keep 500 on purpose); the proof note's labels out of tracked capitals and 9 px; a chip 24 px;
  `aria-disabled` on the waiting make button. *Not done on purpose:* 32 px icon buttons stay (a mouse program; 24 px is the
  floor), the `.prov` and alarm-card caps are not touched beyond the alarm caption.
- **Wave 2** — «Завершити» is a ✓ with a toast (the order card, the Order Creator, the Mockups).
- **Part of waves 4–5** — the Workshop header's folder/shelf as icons with one labelled button when the book is ready, a prompt
  shows three lines; the Tools tiles lose their sentences; the Mockups' Photoshop paragraph is two counting chips. (The
  Workshop already opens at the step that needs attention — that finding was wrong.)
- **The owner's wish** — the Workshop's glyph is a hammer and a ruler crossed.
- **Waves 3–4 done (night)** — one book tile and one bar for the library and the Workshop, the Workshop's eleven steps as
  pictures through the order path's component, the state alphabet in ui-principles.
- **Final waves done (2026-09-30, last)** — undo for a removed library book, one review before a print send, «Сьогодні»,
  Ctrl+K verbs. Left out on purpose: a Settings strip, shortened tracking numbers, a whole-window drop zone ([decisions](../decisions.md)).

- Icons: the set is consistent (1.6 stroke, round, one grid) and stays. Three fixed: `pin` (read as a laboratory flask →
  a slanted push-pin), `original` (→ a picture in frame corners), `video` added so the Omni video no longer shares `motion`
  (the reduce-motion switch) — one icon, one meaning.
- A library/Workshop book card had no visible keyboard focus; its frame takes the ring now.

### Findings, by skill (evidence measured or read; P0 none — nothing blocks a task or loses data)

**`product-design` review** (decision altitude)

| P | Finding | Rule | Where |
|---|---|---|---|
| P1 | **The order's «Завершити» is an `×`** — the same glyph that means *remove*/*clear* in the Mockups, the Creator's book rows and the chips; it is also silent (no question, no undo) and drops the card's kept files/address and the «draft created» mark. The icon says "cancel", the action is "I'm done" | `rule/name-object-scope-consequence`, icons.js's own "one meaning per glyph" | `order-card.js:447`, `creator.js:112`, `mockups.js:160`, `keep.js:43` |
| P2 | **Five recoverable deletions block on "are you sure?"** (a library picture, a library book → `data/library/trash` restored only by hand, a Workshop book / photo blank → the Windows Recycle Bin, Mockups' finish) | `rule/destructive-proportional`, `rule/undo-only-when-honest` | `book.js:327,443`, `workshop-book.js:695,729`, `photos.js:112` |
| P2 | **Up to four dialogs in a row before a print send** (not all books ready → the text still checking → wrong book → mistakes) — one review step would do | `rule/irreversible-action-safeguard`, `rule/inline-before-modal` | `order-card.js:609–618` |
| P2 | Two checkbox-gated dialogs end in a bare «Підтвердити» | `rule/no-confirm-ok-labels`, `rule/destructive-names-action` | `creator.js:520`, `settings-dialogs.js:11` |
| ✓ | Well done: the wrong-book and error dialogs name the object and the way out («Все одно до друку» / «Повернутись»); the passport update *shows* the new text before it is kept; deleted Workshop books say "the folder is in the Recycle Bin"; «Ще: демо-книга» keeps the make button pressable and says what is missing | | |

**`ux-heuristics`** — score **≈ 8 / 10** (Quick Diagnostic: two rows fail). The gap to 10: *(1) "huh?" moments* — the `×`
above, the unlabeled rail (mystery-meat navigation by the rule of thumb, accepted on purpose: the owner's "show, don't
tell", softened by a tooltip with the key and the page title; an option is a rail that unfolds its words on hover/focus —
the owner's call), the Workshop book page; *(2) undo and exits* — the silent finish, the blocking deletions. Passes: the
page always says what it is (Trunk Test), search is reachable (Ctrl+K), status is visible (busy dots, the window title,
«Оновлено N хв тому»), errors say what to do («Сесію не підтверджено. Перезапустіть програму.»), every interactive element
has a name (measured: 0 unnamed).

**`cognitive-load-audit`**

1. *Extraneous load:* the Workshop book page — **45 controls and ~790 words in the first screen**, the raw JSON prompt
   shown in full on every row (a non-programmer cannot read it; it is for copying), the picture gallery **and** the rows
   saying the same; the Mockups' paragraphs; the Tools tiles' sentences; 47-character tracking numbers that outweigh the
   print-archive row's name.
2. *Mental-model gaps:* `×` = done; «Order Creator» (the only English place name in the rail's world); **the same fact is
   drawn three ways** — the Workshop's 11-segment bar, the library's four squares, the path strip's ticks.
3. *Offloading:* open the Workshop at the step that needs attention (the strip already flags «Промпти · 14 помилок» in red
   — the page could start there); shorten a tracking number to its last digits with a copy click; a prompt as one line + a copy icon.
4. *Top 5:* the Workshop book page's first screen; one state alphabet; the `×`; the prompt as a one-liner; the archive row.

**`laws-of-ux`** (only the laws that bite) — *Hick / Miller:* the Workshop book page (45). *Similarity / Common region:* two
book-tile components (`.ws-card` 16:9 bordered vs `.book-card` square, `workshop.js:73`, `library.js:79`). *Von Restorff:*
one loud button is kept (a cyan «Генерувати решту» on the Workshop page, one orange action on the card). *Goal-gradient /
Zeigarnik:* kept — the path strip and the 11-segment bar. *Fitts:* the rail is 44 px, Profit's and the Archive's controls
28–30 px. *Peak-end:* finishing an order ends on a silent `×` — no moment of "done". *Jakob:* rail left, Ctrl+K — matches.
*Doherty:* routes render in 12–42 ms (measured).

**`typography-audit`** (light theme; fonts are the Windows system faces — no `@font-face`, so no loading cost)

- `[HIGH]` `size-line-height`: **15 different line-heights** (1.05 … 1.62) and one fixed `13px` (`listings.css:353`) — no system;
  three tokens (tight 1.25 / UI 1.45 / reading 1.6) would replace them.
- `[HIGH]` `hierarchy-weights`: the agreed weights are 400 / 600; found 500 ×6 and 700 ×2 (`app.css:330`, `listings.css:128,404,431`,
  `orders.css:108,197`, `profit.css:96`).
- `[HIGH]` `brand-color` + `size-min`: `.proof-note dt` (the proofing labels) — 9–12 px fluid, tracked capitals, a raw `#8b8d87`
  (≈ 3.3 : 1 on white) — a leftover of the old system (`orders.css:161`); three more tracked-capital labels
  (`profit.css:40`, `orders.css:204`).
- `[MEDIUM]` `brand-color` on the page background: `--text-3` #6d7076 = **4.0 : 1** on #e7e7e4 (AA 4.5) — the subtitles, ids,
  counts on every page; ~#63666c gives 4.6.
- ✓ pass: the type scale (five sizes; `.mono`'s 11.04 px is the monospace face's optical correction, 52 px a named token),
  `text-wrap: balance` on headings, `tabular-nums` on the money.

**`make-interfaces-feel-better`** — Typography ✓ (antialiased, balance, tabular) · Surfaces: concentric radii ✓ (a row's 12 =
a thumb's 2 + 10 padding); the cover has no outline — *rejected*: its book-like shadow is deliberate · Animations: no
`transition: all`, only `transform`/`opacity`; **press scale has four values** (.93 / .97 / .99 / .996, guide: one .96) ·
Icons ✓ one stroke, `currentColor` · Performance ✓ four `will-change`. Hit areas: **28–30 px** controls beside the 44 px rail.

**`icon-design`** — reviewed at 96 px and 16–20 px: three redrawn (above). Kept and watched: the service letters
(E · C · P · G in squares — told apart by colour and letter only), `tools` (generic four squares — it works as the set of
tools), `motion` (obscure alone, it only appears as a switch with its word).

**`book-studio-ui-logic`** — rule 1 (show): Mockups' paragraphs, Tools' sentences, the raw JSON prompt; rule 2 (a label does
what it says): the `×`; rule 3 (nothing redundant): the Workshop gallery and rows; rule 4 (real state): ✓ after the Gelato fix;
rule 5 (one loud button): ✓; rule 7 (a button never ignores a press): ✓ («Ще: демо-книга»); rule 8 (light first): this pass.

### Checked and fine (not to be "fixed")

Settings is already accordions with a summary line each (the wall of text is the cards that miss a key, opened on purpose);
animation only on `transform`/`opacity`; a global 2 px focus ring; the code is healthy — the longest function 66 lines, six
page files of 690–840 lines (a split is optional), 34 ms to DOMContentLoaded, 28 KB over 44 local requests. The Mockups'
raw colours are the pretend Photoshop, on purpose.

### The next waves (proposed — the owner picks)

1. **Quick and safe — contrast, hands and type**: `--text-3`, hit areas to 40 px through a pseudo-element, one press scale,
   the `.proof-note` leftover, three line-height tokens, weights 500/700 → 400/600, a real Tab walk in headless Edge,
   `aria-disabled` on "waiting" buttons.
2. **Honest "done"**: the order's «Завершити» becomes a ✓ (`checkCircle`, the glyph for *done*), a short "finished" moment
   and a real way back; `×` stays for remove only.
3. **One book, one language**: one book tile for the Workshop and the library; **one state alphabet** (○ new · ◐ in
   progress · ● done · ▲ needs you) for orders, steps, services, books and the Mockups' slots — the bar, the squares and the
   ticks become one thing.
4. **A quiet Workshop page**: open at the step that needs attention; a prompt as one line + a copy icon (the JSON on
   demand); the gallery and the rows stop saying the same thing; the header's two text buttons become icons.
5. **Quiet rooms**: the Mockups and the Photo mockups say less, the Tools tiles lose their sentences, Settings shows a
   "services ready" strip on top, a tracking number shortened with a copy click.
6. **Undo instead of questions**: a real Undo toast for the recoverable deletions (the server restores from the library's
   trash — a restart), one review step instead of the print send's four dialogs, the questions kept for the irreversible.
7. **Creative**: a «Сьогодні» home (the brand mark) — one line per thing that needs the owner across every place; Ctrl+K as a
   doer ("make the mockups for №41"), not only a finder; one drop zone for the whole window that recognises a Canva ZIP and
   offers where it belongs; the rail that unfolds its words on hover (only if the owner wants it).
8. Optional, only when touching them: split `workshop-book.js`, `mockups.js`, `slides-editor.js` by job.

## Related

- [The interface the owner wants](../owner/ui-principles.md) · [Interface](../architecture/frontend.md) ·
  [Two modes](../features/modes.md) · [Decisions](../decisions.md) · [The order path](../flows/order-to-print.md)
