---
title: The Workshop — books in development, with the book pipeline's agents (the Listings mode)
type: feature
updated: 2026-09-30
code:
  - app/studio/workshop/__init__.py
  - app/studio/workshop/books.py
  - app/studio/workshop/rows.py
  - app/studio/workshop/pictures.py
  - app/studio/workshop/generate.py
  - app/studio/workshop/upscale.py
  - app/studio/workshop/check.py
  - app/studio/workshop/routes.py
  - app/studio/clipboard.py
  - app/web/js/pages/workshop.js
  - app/web/js/pages/workshop-book.js
  - app/web/js/pages/workshop-rows.js
  - app/web/js/workshop-live.js
  - app/tools/sample_books.py
  - app/web/js/workshop-bits.js
---
# The Workshop (Майстерня)

> The owner's place for making a new book before it goes on sale: "a place where I create books before sending
> them to the library with orders" (2026-09-24). **Since 2026-09-26 it is the book console moved in** (the
> prototype «Пульт книги», [the plan](../plans/book-console.md)): a book is a folder of the book pipeline, where the
> agents in Antigravity write its formula, hero, story, text and prompts; the Workshop shows the book's path, puts
> every prompt into the clipboard, **catches the picture the owner downloads from Gemini** into its row — cut,
> flipped, the cover laid on the printer's template — and passes the finished book to the library with its Etsy
> listing. Part of the [Listings mode](modes.md).

## Where a book lives

```
Book Studio/pipeline/            the book pipeline — Antigravity's project folder (in git: the agents' rules, playbook)
  GEMINI.md = AGENTS.md          the book agents' rules; CLAUDE.md — the fork for coding agents
  playbook/ notes/ Listing prompts/
  check_book.py                  the book check the agents run before GO (the Workshop's own rules, check.py)
  books/                         NOT in git — the Workshop's books:
    25.some-book/
      agent/      the agents' files — the Workshop only reads them (except the hero it catches: canonical.png,
                  a variant's hero.png)
      pictures/   the pages, cut and named: Cover.png, 1.png … 30.png — the set for Canva («Сторінки»)
      originals/  the pictures as the generator made them, moved out of Downloads, named by their row:
                  page-01.jpg, spread-04-05.jpg …, cover-art.jpg, cover-expanded.png (made by the Workshop),
                  cover-wrap.jpg, hero.png
      .replaced/  whatever a new picture replaced or a removal took — never deleted
      book.json   the Workshop's state: the steps ticked by hand, each row's marks (mirrored, cut, from, size),
                  the cover's layout on the template, the library book it was passed on as
      mockups/    the Mockups' pictures for this book, no-background/ (their cut-outs), canva-cover.png (the demo
                  book's cover — the photo mockups' reference), slides/ (its listing slides: the scenes, the
                  cut-out books) — since 29.09.2026, written by Book Studio
      etsy/       what goes into the Etsy listing (since 30.09.2026): the slides Listing 1…6.png, copies of Cover & Open 1 and All & Open 1
                  (made by the Mockups) and the photo
                  mockups photo-<category>.png
```

- **A book's id is its folder's name** (`25.some-book`; the page's address `#/workshop/25.some-book`). The agents
  make the folder themselves («нова книга» in Antigravity) — the Workshop finds it. **A book's number is its Etsy
  listing's number** (the owner, 29.09.2026: 24 — Spooky stories, 25 — Sleepy trucks bedtime, the next the highest + 1;
  they were 40 and 41 until then, renamed that evening with the library's link — `pipeline/GEMINI.md`).
- **The agents write only into `agent/`** and never touch `book.json` — so they can't break a book, and the
  Workshop's state isn't lost ([decisions](../decisions.md), 2026-09-26).
- **Antigravity hides git-ignored files from its agents** by default: `pipeline/books/` is kept out of git, so the
  owner turns on Antigravity → Settings → Agent → *Agent Gitignore Access* once (checked in the program itself:
  `AllowAgentAccessGitignoreFiles`, `BLOCK_REASON_GITIGNORED`); the agents' rules tell them to say so if they can't
  see `books/`.
- **Antigravity 2 works in projects and ignores a folder given at its start** (the owner's 2.17, checked
  2026-09-26): a new chat runs in the project last picked in it. The prototype's project `Book Console` stayed picked,
  so the first book after the move was written into `D:\Roman\Desktop\Book Console\books`. Hence: **once, by the
  owner** — an Antigravity project on `Book Studio\pipeline` picked for new chats; and **every time** — the words
  «Відкрити агента» / «Нова книга» put into the clipboard carry the full paths (`agent_words()`): the rules
  `…\pipeline\GEMINI.md` and the book's folder `…\pipeline\books\<n>.<slug>`, so the agent is told where to write
  whatever project it runs in.

## The gallery (`#/workshop`)

- A card per book (`card()`): the cover (its front half), else the cover's picture, else the first finished
  spread, else the hero, else the title's letter; `№41 Title` (from the folder's name), the cover's title from
  `book-text.md` (serif, `{Name}` marked), **the path as eleven strips**, «Далі: <step>», «Картинки n/16», the book
  check's GO (green) or «N помилок» (red); a book the Workshop is waiting a picture for says «чекаю картинку».
- Search by title or number (Ctrl+F or `/`), sort (`SORTS`: by number, newest first — the default; recently
  changed; least ready first — remembered in `bs-workshop-view`), **«У роботі · У бібліотеці»** (shown once a book
  has been passed on), the books folder, **«+» (N) — a new book in Antigravity**: Antigravity opens and the
  clipboard holds «Нова книга. Спершу прочитай …\pipeline\GEMINI.md; книгу пиши тільки в …\pipeline\books» to paste
  into the agent's chat; the book appears here by itself once the agent starts it.
- The gallery follows the files by itself (`workshop-live.js`): an agent's new book comes in, a caught picture
  shows, without a reload.

## A book (`#/workshop/<folder>`)

- **Header**: back (Esc), `№41 Title`, the cover's title, the Tier chip (H — a child hero on every spread; S — no
  recurring hero); on the right **«Папка книги»** — a button in the accent colour beside «Передати в бібліотеку»
  (2026-09-30, the owner: "an important button too"; an icon in the group before), and **one group of icons, the
  passport's way** (since 2026-09-26): **the agent**
  (Antigravity, «Продовжуємо книгу …\pipeline\books\41.… (правила — …\GEMINI.md)» in the clipboard), **the pages**
  (square pictures — `pictures/`, the set for Canva), **the originals** (a wide picture — `originals/`, the 2:1
  spreads as the generator made them), «Ще» — **delete** (the whole folder into the Windows Recycle Bin, confirmed); beside it the one text button **«Передати в бібліотеку»** (in the
  accent colour once every picture and the cover are there), then «У бібліотеці» (opens the library book).
- **The generation bar** (sticky on top, `genBar()`, drawn by `paintGenBar()`: it slides in once, when a wait begins; the
  next part going into the clipboard only glides its line in — the owner, 30.09.2026: the whole bar coming in again at
  every part "blinks the whole program"): what is awaited, what's in the clipboard, the parts of a
  several-part paste, «Далі» (F8), «покласти ще раз», «Стоп», the queue's progress («6 з 10», a thin line).
  «Стоп» (or deleting the book, or another row started) while a caught picture is still being cut stays a stop:
  the picture is kept in its row, the old queue never comes back (the 2026-09-26 audit). On
  another book's page or the gallery it names the book that waits, with «Перейти».
- **The path strip** (`STEPS`): Формула → Герой → Історія → Текст → Промпти · GO → Картинки `n/16` → Обкладинка →
  Canva → Мокапи → Фото `n/7` → Бібліотека. Each a rounded square, the Order Creator's step number (since 2026-09-26; circles
  before) — ✓ done, half-filled started, dashed skipped (a Tier S book's hero), a number not yet; the next one is
  outlined in the ink with a breathing ring, the line after a done step lights up, a step that has just become done
  pops; the hero's square is its photo. **Ticked by the files that exist** (`steps()`): `formula.md`,
  `canonical.png` (the prompt or the card alone — started), `story-blueprint.md`, `book-text.md`, both prompt files
  (one — started), the rows whose every page is in `pictures/`, `Cover.png`; **Canva is ticked by hand**; **Мокапи
  ticks itself** when the mockups are made for this book (since 2026-09-29; by hand too, for ones made elsewhere); **Фото**
  — when all seven photo mockups are in `etsy/`, or by hand (a category may be skipped); **Бібліотека ticks itself** when the book has
  been passed on (and unticks if that library book went to the trash).
- **The step's panel** (a click on a step or ← →; a second click or × folds it): the step's file — text with its
  headings and code blocks, a picture (a click — large), tabs when a step has several files, a missing file named
  with the agent who writes it, «Відкрити файл у Windows»; the Hero's panel — «Генерувати героя», «Героя в
  буфер», «Обрати файл»; Промпти — the **book check**'s tab (GO / «Не готово — N помилок», the errors, the
  warnings, how many checks passed — the old pipeline validator's rules, `check.py`); Картинки — the 16 rows as small
  frames (a click scrolls to the row); Canva — «Зроблено» / «Зняти позначку»; **Мокапи** — what the book's `mockups\`
  holds (mockups, «Без фону», slides) and **«Зробити / Редагувати мокапи»** (the Mockups for this book — the owner: "back to
  editing the mockups even when everything is saved"), **«Редагувати слайди»** (the slides' editor), **«Відкрити папку
  мокапів»**, «Відкрити папку Etsy» (the slides), «Позначити зробленим» / «Зняти позначку» (`mockupsBody()`, `books.mockups_state()`);
  **Фото** — the [photo mockups](photo-mockups.md): the book's references, a card per category, the chosen category's
  templates (`photosBody()`); Бібліотека — what's missing and
  «Передати в бібліотеку».
- **The rows** (one column of 820 px, the owner: "not the full width") under the passport's section heading
  «СТОРІНКИ КНИГИ n/16»: page 1, spreads 2–3 … 28–29, page 30 — and **the cover last** (it's generated last, by
  Agent 6). Every card: the row's name, «Генерувати» (▷, or «Ще раз» ↻, or «чекаю картинку»); **the prompt** — the whole JSON object pretty-printed,
  what the generator gets (long ones folded, «Показати весь промпт»; copy); **the 2:1 frame** (empty — the
  passport's drop zone; a single page's other half — the dotted endpaper); **the text** in the
  book's font, `{Name}`/`{Gifter}` marked (copy). A short or broken prompt file is named above the rows («3 промпти
  замість 14», «блок 4: JSON не читається»).
- **A picture dragged from the page is never taken in** (the owner, 2026-09-26: a spread dragged a little and let go
  on itself replaced itself with a cut square — the browser hands a dragged picture over as a file, its shown
  preview): a drag that starts in Book Studio's window is shut out of every drop zone (`app.js`, see
  [dragging files](../flows/dropped-files.md)); dragging a picture out to another program still works.
- **Prompts and texts are the agents'** (read, never written by the page): to change one, the owner asks the agent
  (or opens the file from the step's panel).
- **Hero variants** (Tier H, only when the agent made one): tabs «Основна · G2_brunette 3/14»; a variant's tab —
  its hero card (generate: the base `canonical.png`, «Далі», the edit prompt → `hero.png`) and its spreads (generate:
  the base spread as Gemini made it, un-mirrored, «Далі», the variant's hero, «Далі», the swap prompt → the pages
  into `pictures/variants/<name>/`) — one by one, «Генерувати» on each row (no «Генерувати варіант» for all of them:
  removed 2026-09-27, the owner: "I do them one by one, it's handier"). **Every variant has its own cover**
  (2026-09-27, the owner: "each variant has its own cover — no two stages, a place for the expanded one at once, no
  prompt"): the last card of the tab, one frame for the finished wide cover — dropped, picked or caught from
  Downloads, brought to the printer's template like the base cover's second stage (`fit_template()`, «обрізано під
  шаблон» when it had to be cut) → `pictures/variants/<name>/Cover.png`. «Генерувати» there puts the base cover and
  the variant's hero into the clipboard (what of them there is) and waits.
- **The viewer**: a click on a page — every page of the book in order (a spread's two pages one after the other,
  the cover), T for the text, the "original" button opens the file in Windows. On a hero variant's tab — the
  variant's own spreads and its cover (before 2026-09-27 a variant's page opened the base book's, and its cover didn't
  open at all).

## A picture into its row

`pictures.place()` — the owner's flipper and slicer (then the [upscaling](#upscaling)) (`Etsy-Book-Pipeline`'s `mirror-alternate.py`,
`slice-spreads.py`; his answers — [raw/2026-09-24-workshop-flipper-owner-answers.md](../raw/2026-09-24-workshop-flipper-owner-answers.md)):

- **A spread**: mirrored first when it's one of the flipper's — **4–5, 8–9 … 28–29** (`MIRRORED`; an empty frame
  says «віддзеркалиться»), cut to 2:1 around the centre (a wider picture loses its sides, a narrower one its top
  and bottom — the amber mark «обрізано …»), cut into **two square pages** `pictures/<n>.png`. ⇄ mirrors any spread
  by hand; twice gives back the same pages, pixel for pixel.
- **Pages 1 and 30**: cut to a square when more than 4 % off (`OFF`).
- **The cover, in two stages** (`cover_state()`): ① the picture from Agent 6's prompt, kept as
  `originals/cover-art.*` and laid on **the printer's template** (`TEMPLATE`, the owner's 8×8 hardcover: 17.90″×9.50″
  with the wrap, finished 16.40″×8.00″ — the picture's width is the finished width, `template_layout()`), white all
  round → `originals/cover-expanded.png`; the card slides to ② **Поля**: the picture with its margins and the
  **outpaint prompt** (fill only the white margin, change nothing inside — `outpaint_prompt()`), the template's lines
  (an icon toggle, crop marks: the finished edge, the spine, the safety zones); the outpainted result becomes `pictures/Cover.png` at exactly
  5370×2850 px, 300 dpi (`fit_template()`). «Без полів» takes the picture as it is.
- **The hero**: `agent/canonical.png` (a variant's: `hero.png`).
- A picture dropped (or picked) is copied; **a caught download is moved** out of Downloads into `originals/`, named
  by its row.
- **`originals/` is the Workshop's store, not a way in**: a file put there by hand is not noticed by itself. When some
  are there with the right names (`spread-04-05.png`, `page-01.png`, `cover-art.*`, `cover-wrap.*`, `hero.png`; a
  variant's — in `originals/variants/<name>/`) and their rows have no pages yet, the rows' heading (the base tab or the
  variant's) shows **«Підхопити з папки (N)»** (the owner, 2026-09-27: "I put the spreads into the folder and the
  program doesn't pick them up"): each goes the usual way — cut, flipped, the cover laid on the template, then
  upscaled — as if dropped onto its row; the file stays where it is (`left_behind()`, `adopt()`, a job with its
  progress in the heading). A row that already has its pages is left alone. **Whatever a new picture replaces, or a removal takes, goes to the book's `.replaced/`** — never deleted.
  When another program holds the old picture open (Explorer with the file selected and its preview, a picture viewer,
  Chrome with the file dragged into it, an antivirus), the Workshop waits ~5 s, then says **which program** holds it —
  Windows' Restart Manager tells (`desktop.file_holders()`) — and that nothing was changed (2026-09-28: the owner's
  «WinError 32» as an internal error, over and over, on book 41). **It was Book Studio's own window** (Edge): the owner
  dragged pictures into the frames straight out of the book's `originals/`, and the window held the very file to be
  moved. Now **a picture byte for byte the row's original already** replaces nothing — its pages are only cut again
  (`_same_as_original()`); if the window still holds an old one, the error says to reopen Book Studio.
- Every picture can be saved anywhere: a page's corner — «Зберегти як…» (the Windows dialog, the folder remembered —
  `settings.json` → `workshop.saveDir`); the frame's tools — «Копіювати картинку» (a spread as Gemini made it — e.g.
  for Agent 6's "best frame"), «Зберегти оригінал як…».

## Upscaling

The owner, 2026-09-27: upscaling is a step of the Workshop, "just 2×, whatever size the picture comes in", with a way
to skip it for the whole book ([decisions](../decisions.md)). `upscale.py`:

- **What**: the spreads, pages 1 and 30 and the cover (its outpainted picture, or the picture itself after «Без
  полів»), and **every hero variant's spreads and cover** (the owner, the same evening: "there's no upscale in the
  variants") — every time a picture lands in its row (caught, dropped, picked). **Not** the hero pictures themselves
  (`canonical.png`, a variant's `hero.png`). A row is named by its slot, as in `book.json`: `spread3`, or
  `G2_brunette/spread3` in a variant.
- **How**: his own **Upscayl**'s command-line engine (`upscayl-bin.exe`, no window), the model **upscayl-standard-4x**,
  output **×2** (Upscayl's own "2×" — what he used by hand). Found by itself: the path remembered in `settings.json`
  (`workshop.upscayl`), else the one Upscayl's own log names (`%APPDATA%\Upscayl\logs`, "UPSCAYL EXEC PATH" — his is
  on drive D), else its usual installs. **The row's original** is upscaled (the spread before it is cut — the halves
  stay alike), then mirrored as the row is now (⇄ by hand counts) and cut as before; the big pages replace the small
  ones in `pictures/`, the original stays as it came. The cover's upscaled picture is brought to the template as
  before — `Cover.png` stays exactly 5370×2850. **Upscayl gets a copy** of the original (in `tmp/`, 2026-09-28): the
  book's own file is never held while it works, so replacing the picture meanwhile can't fail.
- **The pictures' sizes are read from their headers only** — a PNG's EXIF is asked for only when it comes before the
  picture: asking for it unpacked every picture, and the owner's book 41 (8 hero variants, 370 pictures) took **31 s**
  to open; now 0.14 s (2026-09-28, `_size()`).
- **In the background, one at a time** (`Upscaler`, the graphics card is shared with the text check's model): the small
  pages are there at once, the big ones replace them ~8 s later (his RTX 4070 SUPER: 16 spreads in about 2 minutes).
  A picture replaced, flipped or removed meanwhile wins (`pictures.WRITING`, the row's `pic` mark) — nothing old is
  written over it.
- **On the page**: in the rows' heading (the base tab and every variant's) the switch **«Апскейл ×2»** (on by default; off — `book.json` `"upscale":
  false`, the book's queue dropped; disabled with a tip when Upscayl isn't found), «апскейл · ще N» while it works,
  **«Апскейлити решту (N)»** for the pages not upscaled yet, the variants' too (a book made before, or turned on again). Over a picture a
  chip: «апскейл 45%», «чекає апскейлу», amber «не апскейлено» (the tip says why), or «×2» (the tip — the model and
  the size); among a picture's tools ✦ «Апскейлити ×2» / «Апскейлити ще раз» (from the original). The cover shows it
  beside its size. «Передати в бібліотеку» names the pages not upscaled yet (it doesn't stop).
- **A big picture isn't offered** (the owner, 2026-09-27: "it doesn't recognise big pictures"): a page of **2400 px**
  a side or more (`BIG` — 8″ at 300 dpi, print-ready; the cover — its picture's height) is left as it is, and isn't
  queued when it lands. **The pages themselves are measured** (`sides()`), not only the original: in book 41 the
  owner had upscaled Boy_2's originals in Upscayl and put them back, while its pages stayed cut from the small ones.
  Such a row (a big original, small pages) is **only cut again** from its original, without Upscayl — the button
  **«Перерізати з великих оригіналів (N)»** beside «Апскейлити решту (N)»; both count the open tab's rows only (the base
  book's, or the variant's).
- **Every picture says how big its page is** (a chip over it): «✦ ×2 | 2880 px» — upscaled here; «✓ 2880 px» — big
  already; «1440 px» (dim) — not upscaled yet; «1440 px | оригінал 2880» — to be cut again. The tips say it in words.
- A failure (Upscayl missing, the graphics card busy) leaves the small pages and says so; nothing waits on it.
- **The sandbox** (the preview, the tests): a plain ×2 resize instead of Upscayl — the owner's program is never
  started; the tests turn the queue by hand.

## The generation mode

The main win (`generate.Session`): **«Генерувати»** on a row puts its prompt into the **Windows clipboard, by the
program itself** (`clipboard.py` — so the next prompt is there while the owner stays in Gemini's window), the row
lights up «чекаю картинку», and the Workshop looks into **Downloads** every 0.6 s: **the first new PNG/JPEG/WEBP that
appears after the press and has finished downloading** (a `.crdownload` is waited out, the size must stay put) is
caught into the row — moved, cut, flipped — with a short Windows sound. Files that were there before don't count;
nothing else in Downloads is touched.

- **«Генерувати всю книгу»** (then «…решту»): the rows with a prompt and no picture, in the pipeline's order —
  spreads 2–3 … 28–29, then pages 1 and 30 (`SERIES_ORDER`); after each catch **the next row's prompt is already in
  the clipboard**, and the page follows to the next row when the last one was on screen. When the queue is done,
  the taskbar button flashes with Windows' sound.
- **A spread of a book with a hero** (the agent's `canonical.png`) gives **the hero, then the prompt** — the owner
  attaches the reference to every prompt in the one Gemini chat (2026-09-27). Pages 1 and 30 and a book without a
  hero (Tier S) — the prompt alone. After each catch the next spread's hero is already in the clipboard.
- **A paste of several parts** (that spread; the cover's margins: the picture, then the prompt; a variant's spread:
  the base spread, the variant's hero, the prompt) goes one by one — the first at once, the next **by Ctrl+V in
  Chrome itself**: the owner pastes, and a moment after V is let go the next part is in the clipboard — "two pastes
  in a row" (2026-09-27; `PasteWatch`). Only a Ctrl+V while **Chrome** is the window in front counts (Book Studio's
  own window is Edge); the keys' state is only looked at, every 20 ms and only while such a paste goes on — nothing
  is caught or written down. **«Далі» or F8 anywhere** do the same (F8 is taken from Windows only while such a paste
  goes on, `Hotkey`) — for a Ctrl+V that didn't count. The bar says «У буфері: герой — вставте в Chrome (Ctrl+V) —
  одразу за ним у буфер ляже промпт».
- The cover's picture, once caught (or dropped), goes on to wait for its margins by itself.
- **The work is the server's**: it goes on while the window is behind Gemini or the owner is elsewhere in Book
  Studio — then a notice per caught picture, a dot on the rail (the brand icon in Orders, «Майстерня» in Listings)
  and the window's title «● Розворот 10–11 · 6 з 16 — Book Studio» (`workshop-live.js` → `bs:busy`).

## «Передати в бібліотеку»

The library's «Нова книга» dialog in its passing-on form (`openAddBook(existing, transfer)`): what's missing on top
(amber, or green «Усі картинки й тексти на місці»), the **Etsy listing link or number** checked read-only (without
keys — passed unchecked), "take the listing's main photo as the thumbnail". Then `books.to_library()`: **a library
book is made** from the book's pages (`Cover.png`, `1…30.png` — a spread's two pages as its left and right), its
texts (`book-text.md`, the reference for the [text check](text-check.md)) and the listing, titled like the
Workshop's book and noting it (`"workshop": "<folder>"`). **Its cover and pages are not copied** (since 2026-09-27;
the owner: "one place, no doubles"): the library book takes them from this folder's `pictures/` (`"pagesFrom":
"workshop"`, [library](library.md)) — a page replaced or added here is the library's at once, and the passport
only shows them («Змінити в Майстерні»). The job makes the pages' previews, with its progress on the button. **The
Workshop's book stays** — its folder, originals and variants untouched; it moves to «У бібліотеці» and its last
step is ticked (its panel: «Обкладинку й сторінки бібліотека бере звідси: заміните тут — зміниться й там»).
Deleting such a book («Ще» → «Видалити книгу») first copies its cover and pages into the library book
(`library.keep_pages()`; the dialog says so), then the folder goes to the Recycle Bin. A listing another library book already has is refused (409 with that book's id, «Відкрити
ту книгу»); a book already passed on opens its library book instead.

## Live, and smooth

- A Workshop page asks `/api/workshop/sig` every 1.5 s while it's on screen (a book's page — only its own book's
  files, read with `os.scandir`, 7–8× faster than looking at each file, since 2026-09-26); away from the Workshop,
  while a picture is awaited, only `/api/workshop/gen` is asked (no book is walked), and the generation mode (the
  Downloads watcher, F8's thread) starts only when first used — `generate.status()` answers "idle" without starting
  it. A book's page works its parts out once (the strip and the pictures' versions were twice); an open text step is
fetched again only when its file's version changed; the one-shot animations (a step just done pops, the cover's pane
glides) go on after the redraw instead of into the markup, so the next redraw doesn't draw those parts again. When something
  changed the page fetches and **redraws in place** (`patch()` in `lib.js`): each part is keyed,
  an unchanged one stays as it is (its pictures, hover, focus), a changed one is replaced, and a picture the old part
  already showed is carried over — nothing reloads or blinks; the scroll, an opened prompt, the chosen step stay.
- Every picture's address carries its version (`?v=`): the browser keeps it for good; a replaced picture gets a new
  address.
- The page remembers each book's open step, tabs, variant, opened prompts and the cover's stage until a restart.

## In the preview and the tests (the sandbox)

`core.SANDBOX` (the preview server's `--sample`, and the tests): the books are made-up ones in the data folder
(`tools/sample_books.py`: 40 — Tier H with a hero and a variant; 41 — Tier S, prompts and 5 rows of pictures; 42 —
just started), Downloads is the data folder's `downloads\` (a picture put there is caught), the clipboard goes into
`clipboard\clipboard.txt|png`, F8 isn't taken, no window opens (Antigravity, Explorer, «Зберегти як»), and a deleted
book goes to `recycle-bin\`. The owner's clipboard, keyboard, Downloads and screen are never touched.

## Where in the code

- [app/studio/workshop/books.py](../../app/studio/workshop/books.py) — `AREAS`, `ETSY`, `books_dir()`, `book_path()`, `book_ids()`, `STEPS`, `MANUAL`, `ROWS`, `steps()`, `summary()`, `detail()`, `all_books()`, `library_book()`, `set_mark()`, `versions()`, `signature()`, `display_name()`, `mockups_state()`, `MOCKUPS`, `media_file()`, `agent_text()`, `open_in_windows()`, `agent_words()`, `open_agent()`, `antigravity()`, `delete_book()`, `to_library()`, `update_state()`
- [app/studio/workshop/rows.py](../../app/studio/workshop/rows.py) — `row_list()`, `MIRRORED`, `text_sections()`, `book_texts()`, `prompt_objects()`, `as_prompt()`, `book_rows()`, `cover_state()`, `outpaint_prompt()`, `TEMPLATE`, `template_layout()`, `template_guides()`, `variants()`, `book_check()`, `original_stem()`
- [app/studio/workshop/pictures.py](../../app/studio/workshop/pictures.py) — `WRITING`, `place()`, `left_behind()`, `adopt()`, `two_squares()`, `square()`, `OFF`, `build_expanded()`, `fit_template()`, `skip_margins()`, `flip()`, `remove()`, `spread_panorama()`, `picture_for_clipboard()`, `_retire()`
- [app/studio/workshop/generate.py](../../app/studio/workshop/generate.py) — `Session` (`start_photo()`, `_open()`), `session()`, `downloads_folder()`, `SERIES_ORDER`, `_items()`, `_hero()`
- [app/studio/workshop/upscale.py](../../app/studio/workshop/upscale.py) — `MODEL`, `SCALE`, `KEYS`, `BIG`, `sides()`, `side()`, `slots()`, `split()`, `engine()`, `upscale_row()`, `todo()`, `Upscaler`, `status()`, `after_place()`, `set_on()`, `start()`, `forget()`
- [app/studio/workshop/check.py](../../app/studio/workshop/check.py) — `run()`, `RULES`, `main()`
- [app/studio/workshop/routes.py](../../app/studio/workshop/routes.py) — the routes ([api-routes](../architecture/api-routes.md))
- [app/studio/clipboard.py](../../app/studio/clipboard.py) — `set_text()`, `set_image()`, `Hotkey`, `PasteWatch`, `BROWSERS`, `PASTE_SETTLE`, `sandbox_file()`
- [app/studio/desktop.py](../../app/studio/desktop.py) — `save_file()`, `to_recycle_bin()`, `attention()`
- [app/studio/library.py](../../app/studio/library.py) — `create_book()`, `listing_of()`, `follow()`, `keep_pages()`, `take_listing_image()`, `PAGES_FROM_WORKSHOP`
- [app/web/js/pages/workshop.js](../../app/web/js/pages/workshop.js) — `mount()`, `SORTS`
- [app/web/js/workshop-bits.js](../../app/web/js/workshop-bits.js) — `picture()`, `checkWord()`, `STATE_WORDS`, `STATE_TEXT`, `ERRORS`
- [app/web/js/pages/workshop-book.js](../../app/web/js/pages/workshop-book.js) — `mount()`, `WHO`, `photosBody()`
- [app/web/js/pages/workshop-rows.js](../../app/web/js/pages/workshop-rows.js) — `rowTemplates()` (a row: its prompt, its frame, its text), `waitChip()`
- [app/web/js/workshop-live.js](../../app/web/js/workshop-live.js) — `watch()`, `refresh()`, `wake()`, `act()`, `startGen()`, `startPhoto()`, `genAction()`, `genBar()`, `paintGenBar()`, `waitingFor()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `patch()`
- [app/web/css/listings.css](../../app/web/css/listings.css) — `.ws-card`, `.ws-genbar`, `.ws-strip`, `.ws-step`, `.ws-panel`, `.ws-row`, `.ws-frame`, `.ws-ph`, `.ws-art`, `.ws-cover`, `.ws-tpl`
- [pipeline/GEMINI.md](../../pipeline/GEMINI.md) — the book agents' rules; [pipeline/check_book.py](../../pipeline/check_book.py) — their start of the check
- [app/tools/sample_books.py](../../app/tools/sample_books.py) — `make_books()`
- Tests: [app/tests/test_workshop.py](../../app/tests/test_workshop.py) (`TheSandbox`, `TheBookList`, `ThePathStrip`, `OnlyInsideTheBook`, `TheSignature`, `TheRows`, `TheBookCheck`, `APictureIntoItsRow`, `CatchingDownloads`, `PassingToTheLibrary`)

## Related

- [The plan and its history](../plans/book-console.md) · [Two modes](modes.md) · [Library](library.md) · [Photo mockups](photo-mockups.md) ·
  [Mockups](mockups.md) · [Book structure](../rules/book-structure.md) · [Decisions](../decisions.md)
