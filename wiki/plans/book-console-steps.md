---
title: The book console prototype — steps (temporary)
type: plan
updated: 2026-09-26
code: []
---
# The book console prototype — steps

> **A temporary page** — it lives only while the [book console](book-console.md) is a prototype apart from
> Book Studio. When the prototype moves into Book Studio, what was learned goes into
> [book-console.md](book-console.md) and the feature pages, and this page is removed.
> Each step is small and checked by the owner; ✓ = done by the agent (his check is the note after it).
> **Nothing is built before the owner's «роби»** (2026-09-26).

## What the prototype is (the agent's proposal, 2026-09-26)

- **One folder on D:** `D:\Roman\Desktop\Book Console` (the owner said yes, 2026-09-26; a Latin name because
  the agents run shell commands in it, and Cyrillic paths break those more often than they break Python). The window's own name
  is «Пульт книги». Book Studio's code is not touched; the old `Etsy-Book-Pipeline` is only read.
- **Inside:**
  ```
  Book Console/
    GEMINI.md, AGENTS.md    the book agents' rules (Antigravity) — the pipeline's entry point, cleaned;
                            two identical copies, changed together by hand
    CLAUDE.md               a fork: "making a book → GEMINI.md; the console's code → console/"
    playbook/               agents 0–6, master prompt, visual world bible, knowledge (a clean copy)
    notes/discoveries.md
    Listing prompts/        the 3 JSON prompts and the README (without the old generated pictures)
    books/
      40.<slug>/            one book — one folder (numbers go on from BOOKS_NEW, the last is 39)
        agent/              ONLY the agents write here: formula, character card, canonical prompt,
                            canonical.png, story blueprint, book-text.md, the prompt files
        pictures/           ONLY the console writes here: Cover.png, 1.png … 30.png — the Canva set
        listing/            the listing photos (JPEG from ChatGPT)
        book.json           the console's own state; agents never touch it
    console/                the program: a small Python server + one page, a desktop shortcut;
                            check_book.py — the book check (since step 2)
  ```
- **The look:** the Workshop's book page on its own small server, in Book Studio's style (dark, the Listings
  cyan, the same row cards: prompt · 2:1 frame · text), opened in its own Edge window like Book Studio, with a
  desktop shortcut. The [path strip](book-console.md#the-three-parts) sits on top of a book's page; a short
  list of books is the start page. No internet at all, no keys, no API; its own port; temporary files on D.
- **Catching downloads:** `D:\Roman\Downloads` (this PC's Downloads, checked 2026-09-26) is looked at only while
  a row waits: the first new PNG/JPEG/WEBP that appears after «Генерувати» and has finished downloading. **Since
  2026-09-26 (after the first real book) it is moved into the book** — `originals/`, named by its row — the owner:
  "it should move out of Downloads and live in the program"; nothing else in Downloads is touched.
- **The clipboard** is filled by the program itself (Windows), so the next prompt is there even while the
  owner stays in Gemini's window: Ctrl+V → wait → download → Ctrl+V the next one.
- **Cutting and flipping** — the same rules as the [Workshop](../features/workshop.md#a-spread-becomes-two-pages)
  (the logic copied, not shared): cut to 2:1 around the centre, the spreads 4–5, 8–9 … 28–29 mirrored, two
  square pages; ⇄ by hand. No upscaling in the prototype.
- **Checked before the owner sees a step:** the agent tries each step on a made-up book (invented text,
  test pictures) and with small tests; the real check is the owner's new book.
- **The owner can start the real book at step 2**, while the console is still being built: the console
  reads whatever the agents have already written.

## Steps

### A. The folder and the agents

- [x] **0. This plan** (2026-09-26). *You see:* this page, linked from [book-console.md](book-console.md).
- [x] **1. The folder and a clean copy** (2026-09-26). `Book Console` with the playbook, `notes/discoveries.md`
  and the listing prompts (the three JSON and the README) copied from the old pipeline; nothing else — not
  `seo-intelligence` (the owner: it goes separately), not the old tools, not the old generated pictures.
  *You see:* the folder with only those files; the old `Etsy-Book-Pipeline` unchanged (checked: all 4443
  files with the same sizes and times before and after).
- [x] **2. The agents' rules for the new folder** (2026-09-26). `GEMINI.md` = `AGENTS.md` (Antigravity may
  read either); `CLAUDE.md` is the fork for coding agents. Books go into `books/<n>.<slug>/agent/` (flat —
  the old `_work/` is gone), the numbering goes on from 40, Agent 0 writes its own `formula.md`, agents never
  touch `book.json`, `pictures/`, `listing/` or `console/`. Removed from the agents' instructions: building
  `workshop.json` (the console reads the files itself), cutting, flipping, splitting the cover. The old
  validator became `console/check_book.py` — the same rules, reading `agent/`; the agents run it before GO
  (checked on a copy of book 39: the same report as the old validator; without `canonical.png` it fails).
  The upscale before Canva stays the owner's own step. Stale links to pictures that no longer exist in the
  old pipeline (book 3's contact sheet) were turned into plain mentions.
  *You see:* in Antigravity, opened on the folder, «нова книга» starts the usual questions and the agent's
  files appear in `books/40.<slug>/agent/`. **From here the real book can start.** *Not checked by the
  agent:* Antigravity itself (it would open a window) — the owner's check.

### B. The console window

- [x] **3. The window and the book list** (2026-09-26). The desktop shortcut «Пульт книги» (its own icon:
  an open book with a tick, the CMYK strip) → `console/Book Console.pyw` → a server on `127.0.0.1:47850` and
  its own Edge window, closed like Book Studio's; launched again while open — one more window. The rail with
  the brand mark in cyan, a light/dark switch (dark by default). The start page «Книги»: the books from
  `books/` as cards in number order — `№40 Title` (the folder's name), the cover's title from `book-text.md`,
  a thumbnail (the cover, else the first finished spread, else the hero), a thin bar of the 10 steps, «Далі:
  <step>» and «Картинки n/16»; a button opens the books folder. No books → «Книг ще немає» with a hint to say
  «нова книга» in Antigravity.
  *You see:* the shortcut on the desktop; your book's card. *Checked by the agent:* on made-up books
  (`console/dev_server.py --sample`), the real launcher without a window (it answers); the window on the real
  screen — not opened by the agent, the owner's check.
- [x] **4. The path strip** (2026-09-26). On a book's page: Формула → Герой → Історія → Текст → Промпти →
  Картинки `n/16` → Обкладинка → Canva → Мокапи → Бібліотека, each a circle — ✓ done, half-filled started,
  dashed skipped, a number not yet; the next one to do has a breathing ring; the line between two steps lights
  up after a done one. Ticked by the files: `formula.md`; the hero by `canonical.png` (its photo in the circle;
  the prompt or the card alone — started; Tier S — skipped, the tier read from `formula.md`, else the
  blueprint); `story-blueprint.md`; `book-text.md`; both prompt files (one — started); pictures — the rows whose
  every page is in `pictures/`; the cover — `Cover.png` (its prompt alone — started). Canva, Mockups, Library —
  ticked by hand («Зроблено» / «Зняти позначку», into `book.json`, a hand on the circle). **Pictures count 16
  rows and the cover is its own step right after** (not `n/17` as first written — so the cover isn't counted
  twice). A click on a step (or ← →) shows its panel: the file as text (headings, JSON blocks), the hero's
  picture, tabs when a step has several files, a missing file named with who writes it; «Відкрити файл у
  Windows». The Pictures panel shows the 16 rows as small frames with their pages. The page asks every 1.5 s
  whether a file changed and redraws itself; a step that has just become done pops. The tier as a chip by the
  title.
  *You see:* the ticks match what the agents wrote; a new file ticks its step within a couple of seconds,
  without reloading. *Checked by the agent:* made-up files written while the page was open — «Промпти» turned
  «почато», then done, in under 2.5 s; 15 tests (`console/tests`).
- [x] **5. The book's rows** (2026-09-26). Under the strip, «Рядки книги» (counts: prompts, texts, pictures
  `n/17`) and 17 row cards in one column of 820 px, like the Workshop's: the row's name and three dots; the
  **prompt** (the whole JSON object, pretty-printed — what the generator gets; long ones folded with «Показати
  весь промпт»; a copy button); the **2:1 frame** (empty: dashed, the fold, the page numbers, «віддзеркалиться»
  on 4–5, 8–9 … 28–29; pages 1 and 30 — half endpaper, half page; the cover — «задня · передня»; the pages
  from `pictures/` when they're there); the **text** in the book's font with `{Name}` / `{Gifter}` marked, a copy
  button. Read like the old `build_workshop_json.py`: `## Cover`, `## Spread 01` (page 1), `## Spread 02–15`,
  `## Afterword` (page 30); another heading (a critic's report) ends a section; 14 spread prompts in order, the
  two end prompts, the cover's first. A short or broken prompt file is named above the rows («3 промпти замість
  14», «блок 4: JSON не читається») and what parses still shows. The step's panel now folds (× or a second click
  on the step) so the rows come up.
  *You see:* your book's prompts and texts in 17 rows; an agent's fix shows up in its row within a couple of
  seconds, the page keeping its place. *Checked by the agent:* made-up text added while the page was open —
  in the row in under 2.5 s, the scroll kept.
- [x] **6. The book check (GO) in the window** (2026-09-26). Once any prompt file is there, the console runs
  `check_book.py`'s rules itself (again only when an agent's file changed): under «Промпти» on the strip —
  green **GO** or red «N помилок» (the circle red); on the book's card — the same. The step's panel opens on its
  «Перевірка» tab: GO (green) or «Не готово — N помилок» (red), the errors, the warnings, how many checks passed.
  The messages are the old validator's own (English). *You see:* GO or the problems, the same as the old
  validator would say. *Checked by the agent:* the same report as the old validator on a copy of book 39 (GO,
  one warning — shown green in the window); a made-up book with 10 errors shown red; 25 tests (`console/tests`).
- [x] **7. «Відкрити агента»** (2026-09-26; the owner: "the rest in a row, without steps" — steps 7–15 built
  together). A button on a book's page (and «Нова книга в Antigravity» on the list) opens
  `%LOCALAPPDATA%\Programs\antigravity\Antigravity.exe` on the console's **root** folder (where `GEMINI.md`
  is — a book's own folder has no rules) and puts «Продовжуємо книгу books/<id>» (or «нова книга») into the
  clipboard to paste into the agent's chat. *Not checked by the agent:* the Antigravity window itself (it would
  open on the owner's screen) — that the program is there was checked.

### C. The generation mode — the main win

- [x] **8. A picture into a row by hand** (2026-09-26). Drag a PNG/JPEG/WEBP onto a frame, or click an empty
  one for the Windows dialog: a spread is mirrored when it's one of the flipper's (4–5, 8–9 … 28–29), cut to 2:1
  around the centre and into two square pages (`pictures/<n>.png`); pages 1 and 30 are cut to a square when more
  than 4 % off; the cover is kept whole as `Cover.png` (marked «не 2:1» when it isn't). On a filled frame: ⇄
  (twice gives back the same pages), «Замінити файлом», «Прибрати» (confirmed). Chips on the frame say
  «віддзеркалено», «обрізано зверху й знизу». **What a picture replaces or a removal takes goes to the book's
  `.replaced/` folder**, never away (the downloaded original stays in Downloads anyway).
- [x] **9. «Генерувати» on one row** (2026-09-26). The row's prompt goes into the **Windows clipboard, put there
  by the program itself**; the row lights up «чекаю картинку», a bar sticks to the top: «Чекаю картинку ·
  Розворот 10–11 · У буфері: промпт» with «Стоп» and «покласти ще раз». The console looks into Downloads
  (`D:\Roman\Downloads`, from Windows) every 0.6 s: the first new PNG/JPEG/WEBP after the press that has
  finished downloading (a `.crdownload` is waited out, the size must stay put) is **copied** into the row, cut
  and flipped; a short Windows sound; a notice «Розворот 10–11: віддзеркалено — і дві сторінки готові». Nothing
  in Downloads is moved, renamed or deleted; files that were there before don't count. «Ще раз» on a filled
  row generates it again (the new picture replaces the old one, which goes to `.replaced/`).
- [x] **10. The whole book in a row** (2026-09-26). «Генерувати всю книгу»: the rows with a prompt and no
  picture, in the pipeline's order — spreads 2–3 … 28–29, then pages 1 and 30 (the cover is its own, after Agent
  6); after each catch **the next row's prompt is already in the clipboard** («ще 9 у черзі»); the window's
  title shows «● … Картинки 6/17». The work is the server's: it goes on while the window is behind Gemini.
- [x] **11. The hero** (2026-09-26). The Hero step's panel: «Генерувати героя» (the JSON from
  `canonical-prompt.md` into the clipboard; the downloaded picture becomes `agent/canonical.png` — the old one
  to `.replaced/`), «Героя в буфер» (`canonical.png` as a picture, for a new chat; also a button over the rows
  of a Tier H book), «Обрати файл».
- [x] **12. The cover** (2026-09-26). The cover row's «Генерувати» gives, one by one: the **cover mockup**, the
  **reference listing**, then the prompt — the first at once, the next with **«Далі» in the window or F8
  anywhere** (F8 is taken from Windows only while such a paste goes on, and given back after the last thing);
  the caught picture becomes `Cover.png`. *Settled by the agent (the owner can change it):* the mockup and the
  reference are **chosen once for every book** (under the cover's prompt: «обрати / змінити», the Windows
  dialog; kept in `console/data/settings.json`); not chosen — just the prompt.
- [x] ~~**13. Listing photos**~~ (2026-09-26) — **removed the same day** after the first real book (the owner:
  "this whole block is redundant"; the cover's mockup and reference — "they only confuse me"). What was built: «Фото для лістингу» under the rows: the three prompts from
  `Listing prompts/` (as their README says: the book's mockup first, then the JSON prompt → ChatGPT). The
  book's own mockup (from the Mockups) is **picked once per book** (in its `book.json`); each card: «Генерувати»
  → the mockup, «Далі»/F8 → the prompt → ChatGPT's JPEG is caught as it is into `listing/<prompt>.jpg`; a copy
  button, drop or pick a file by hand, remove.

### D. Out of the console

- [x] **14. For Canva and for Book Studio** (2026-09-26). Over the rows: «Папка для Canva» opens `pictures/`
  (`Cover.png`, `1.png` … `30.png`); `{ }` puts the prompts and texts as **the Workshop's JSON** into the clipboard
  (to paste in Book Studio's Workshop: `{ }` → «Вставити JSON…») and saves it as the book's `workshop.json`. The
  upscale before Canva stays the owner's own step.
- [x] **15. Hero variants** (2026-09-26). The agents' rules (`GEMINI.md`) now say where a variant lives:
  `agent/variants/<G2_brunette>/` — `hero-prompt.md` (the canonical's edit), `2.json` … `15.json` (a swap prompt
  per spread number), `hero.png` (caught by the console). On the book's page — tabs «Основна · G2_brunette 3/14»;
  a variant's tab: its hero card (generate: the base `canonical.png`, «Далі», the prompt → `hero.png`) and its
  spreads (generate: **the base spread put together again as Gemini made it** (un-mirrored), «Далі», the
  variant's hero, «Далі», the swap prompt → the pages into `pictures/variants/<name>/`, cut and flipped like the
  base); «Генерувати варіант» for all of them. A spread without its base picture, or before the variant's hero,
  is refused with the reason.
- [ ] **16. What the prototype taught.** On the owner's real book: what worked and what didn't — into
  [book-console.md](book-console.md); the owner decides on the separate branch of Book Studio. *To watch:*
  whether Gemini's download is caught every time (its file names, a picture saved twice); whether pasting the
  picture from the console's clipboard works in Gemini and ChatGPT (a bitmap + PNG are put there); F8 vs the
  window's «Далі»; whether Antigravity reads `GEMINI.md` when opened on the root; the page redrawing itself (a
  window behind Gemini catches up when it's looked at).

## After the first real book (2026-09-26)

The owner made his first book in the console (`40.first-halloween`: 29 pictures caught, Gemini's JPEGs
5824×2880 and 4096×4096) — "it all works really great, really convenient"; then asked:

- [x] **Polish the interface and think the flow through** — the page redrawn without blinking (every picture's
  address carries its version, the browser keeps it), the generation bar shows the queue («6 з 10», a thin
  progress line) and the parts of a several-part paste; a book waiting for a picture says so on its card; the
  Pictures panel's small frames scroll to their row; after a catch the page follows to the next waiting row
  when the last one was on screen; a finished queue says «Готово»; buttons wait (no double press); tooltips
  hide on scroll; the light theme checked.
- [x] **Remove the listing photos, the cover's mockup and reference** — gone from the page and the program.
- [x] **A download moves into the program**; «Сторінки» (the page head) opens `pictures/` — the cut and named pages
  with Cover.png; the images icon opens `originals/`.
- [x] **Every picture can be saved anywhere** — a button in a page's corner («Зберегти як…», the Windows dialog;
  the folder is remembered; a page is suggested as «40.first-halloween — 5.png»); the frame's tools add
  «Копіювати картинку» (a spread as Gemini made it — e.g. for Agent 6's "best frame") and «Зберегти оригінал».
- [x] **The cover — the last card, two stages** (the owner: "drop the picture, outcrop, flip over, the outpaint
  prompt and waiting for the file with the outpaint"): ① **Картинка** — Agent 6's prompt, the picture caught
  (kept as `originals/cover-art.*`); the console at once puts it in the middle of a bigger white canvas —
  margins of **8 % of its height** on every side (the owner's example screenshot; − / + from 2 to 25 %) — and the
  card slides to ② **Поля**: the expanded picture (the picture's own area outlined, the margins tinted), the
  **outpaint prompt** (fill only the white margin, change nothing inside, no visible join, the same size and
  proportions — in the pipeline's image-only language), and it is already waiting: the picture with margins in
  the clipboard, «Далі»/F8 — the prompt, the downloaded result becomes `pictures/Cover.png`. «Без полів» takes
  the picture as it is. A book from before (its Cover.png was the picture itself) has it moved to the first
  stage when it's opened.

- [x] **The printer's template for the cover's margins** (the owner gave the 8×8 hardcover's template, Printify
  SKU 11688-12031: 17.90″×9.50″ with the wrap, finished 16.40″×8.00″, spine 0.40″, safety zones, 5370×2850 px at
  300 dpi; "no special mode — just make it the default"). The picture's width becomes the finished width, so all
  that shows on the book is the picture itself; the margins are what wraps (Gemini's 5824×2880 → 266 px at the
  sides, 247 at the top and bottom — the old 8 % was ~36 and ~17 px short). The outpainted result is brought to
  exactly 5370×2850 px, 300 dpi. The template's lines over the cover («Лінії шаблону»: the finished edge, the
  spine, the safety zones «задня / передня»). The − / + control is gone; a book's old 8 % margins are made again.
- [x] **Deleting a book** (the owner: "the book and all its files — from the library and from the files"; the
  first book didn't please him). A trash button on the book's page → a question in the console's own look → the
  book leaves the console, its whole folder goes to the **Windows Recycle Bin** (restorable until it's emptied —
  never deleted for good, [security](../security.md)); a wait for its picture stops. Checked on the real Windows
  with a made-up folder (it lands in the Recycle Bin with its place), in the sandbox on made-up books. The owner
  deletes his book himself.

*Checked by the agent:* the sandbox preview in both themes (the cover's two stages end to end — a JPEG moved out
of the made-up Downloads, the margins built, the prompt, the result as Cover.png; the hover tools; the list);
43 tests. *Not checked:* how Gemini really outpaints the margins — the prompt is the agent's first version; the
owner's real book in the window (it will move its old Cover.png into the first stage when opened).

**Checked by the agent for 7–15** (the sandbox: made-up books, a made-up Downloads, the clipboard into files,
F8 not taken — the owner's clipboard, Downloads and screen untouched): the whole book caught row after row in the
preview (a `.crdownload` waited out, 12–13 mirrored and cut from 1792×1024 to two 896 squares, the originals
left in Downloads), a listing photo (mockup → «Далі» → prompt → JPEG), a variant's hero and swap (the base spread
back in the clipboard un-mirrored); 39 tests (`console/tests`). **On the real Windows** (briefly, the owner's
clipboard text kept and put back): text and a picture (bitmap + PNG) into the clipboard, F8 taken and given back.
**Found and fixed on the way:** two replacements of one picture in the same second overwrote the kept copy in
`.replaced/`; a variant's spread without its base started with an error instead of refusing. **Not checked:** a
real Gemini/ChatGPT download and paste, the Antigravity window, the window on the owner's screen.

## Answered (2026-09-26)

- The folder — `Book Console`, yes.
- `seo-intelligence` — **not taken**: "it goes separately".
- A git history for the prototype — **none until the move** into Book Studio.

## Related

- [The book console — the plan](book-console.md) · [Workshop](../features/workshop.md) ·
  [Plans](roadmap.md) · [Security](../security.md)
