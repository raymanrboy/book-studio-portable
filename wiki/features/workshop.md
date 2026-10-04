---
title: The Workshop — books in development, with the book pipeline's agents («Книги» → «Майстерня»)
type: feature
updated: 2026-10-04
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
  - app/web/js/book-tile.js
  - app/web/js/pages/workshop-book.js
  - app/web/js/pages/workshop-rows.js
  - app/web/js/workshop-live.js
  - app/tools/sample_books.py
  - app/web/js/workshop-bits.js
---
# The Workshop (Майстерня)

> Where the owner makes a new book before it goes on sale. A book is a folder of the book pipeline, where the agents
> in Antigravity write its formula, hero, story, text and prompts; the Workshop shows the book's path, puts every prompt
> into the clipboard, **catches the picture the owner downloads from Gemini** into its row — cut, flipped, upscaled,
> the cover laid on the printer's template — and passes the finished book to the library with its Etsy listing. Part
> of [«Книги»](modes.md) — its first tab.

## Where a book lives

```
Book Studio/pipeline/            the book pipeline — Antigravity's project folder (in git: the agents' rules, playbook)
  AGENTS.md                      the book agents' rules (any agent); CLAUDE.md — the fork for coding agents
  check_book.py                  the book check the agents run before GO (the Workshop's own rules, check.py)
  books/                         NOT in git — the Workshop's books:
    25.some-book/
      agent/      the agents' files — the Workshop only reads them (except the hero it catches)
      pictures/   the pages, cut and named: Cover.png, 1.png … 30.png — the set for Canva
      originals/  the pictures as the generator made them, named by their row: page-01.jpg, spread-04-05.jpg …,
                  cover-art.jpg, cover-expanded.png, cover-wrap.jpg, hero.png
      mockups/    the Mockups' pictures, their cut-outs, the Canva cover, the slides' scenes — see [mockups](mockups.md)
      etsy/       what goes into the Etsy listing — see [photo mockups](photo-mockups.md#where-things-are)
      .replaced/  whatever a new picture replaced or a removal took — never deleted
      book.json   the Workshop's state: steps ticked by hand, each row's marks, the cover's layout, the library book,
                  the photo mockups' templates
```

- **A book's id is its folder's name** (`25.some-book`, the page `#/workshop/25.some-book`); **its number is its Etsy
  listing's number** (the owner, 29.09.2026). The agents make the folder themselves — the Workshop finds it.
- **The agents write only into `agent/`** and never touch `book.json` — they can't break a book's state
  ([decisions](../decisions.md)).
- **Antigravity**: the owner turned on *Agent Gitignore Access* once (`books/` is out of git; checked in the program:
  `AllowAgentAccessGitignoreFiles`), and picked a project on `Book Studio\pipeline` for new chats. Antigravity ignores a
  folder given at its start, so the words put into the clipboard carry the full paths (`agent_words()`).

## The gallery («Книги» → «Майстерня», `#/books/work`; `#/workshop` leads there)

- A card per book (`card()`) — **the library's tile** (`book-tile.js`, since the late evening of 2026-09-30; before, a wide
  bordered card of its own): the cover as a square (its front), else the cover's picture, else the first spread, else the
  hero; `№25 Title`, the cover's title from `book-text.md`, **one bar of eleven segments** (the steps), a chevron with the
  next step (and «n/16» for the pictures), the prompts check's GO or «N помилок»; a pulsing mark with pictures on a book a
  picture is awaited for.
- Search (Ctrl+F or `/`), sort (`SORTS`, remembered in `bs-workshop-view`), «У роботі · У бібліотеці», the books
  folder, **«+» (N)** — Antigravity opens, the clipboard holds «Нова книга…» with the paths; the book appears by itself.

## A book (`#/workshop/<folder>`)

- **Header**: back (Esc), `№25 Title`, the cover's title, the Tier chip (H — a child hero on every spread; S — none);
  on the right a group of icons (the agent — Antigravity and «Продовжуємо книгу …» in the clipboard; the pages; the
  originals; the book's folder — it was a labelled button the owner called "important", an icon since the late evening of
  2026-09-30; «Ще» → delete: the folder into the Recycle Bin) and one more icon, «Передати в бібліотеку» (a shelf; a tick
  «У бібліотеці» after) — which becomes **the one loud, labelled button** only once every picture and the cover are there.
  A row's prompt shows three lines with a «Весь промпт» link (the JSON is for copying — the copy icon — not for reading).
  The Workshop's own glyph (the tab, the palette) is a hammer and a ruler crossed — the owner's wish, 2026-09-30. «Back» and Esc lead to
  «Книги» → «Майстерня».
- **The generation bar** (sticky, `genBar()` drawn by `paintGenBar()`): what is awaited, what's in the clipboard, the
  parts of a several-part paste, «Далі» (F8), «покласти ще раз», «Стоп», the queue's progress. It slides in once when a
  wait begins; the next part only glides its line in (the owner: the bar coming in again "blinks the whole program").
  On another page it names the book that waits, with «Перейти». «Стоп» while a picture is still being cut stays a stop.
- **The path strip** (`STEPS`): Формула → Герой → Історія → Текст → Промпти · GO → Картинки `n/16` → Обкладинка →
  Canva → Мокапи → Фото `n/8` → Бібліотека — **a picture per step** (since the late evening of 2026-09-30, the order path's
  way — `pathStep()`; the word, the count and the check in the tooltip; the hero's own thumbnail still shows in its square), ✓ done,
  half-filled started, dashed skipped (a Tier S book's hero), red with ⚠ where the check found mistakes; the next one breathes. **Ticked by the files** (`steps()`): the agents' files, the rows whose
  pages are all in `pictures/`, `Cover.png`. **Canva** — by hand; **Мокапи** — by itself when made for this book (or by
  hand); **Фото** — every photo mockup category (the Omni video too), or by hand; **Бібліотека** — when passed on (unticks if that library book
  went to the trash).
- **The step's panel** (a click or ← →; × folds): the step's file (text, a picture, tabs, the agent who writes a
  missing one, «Відкрити файл у Windows»); Герой — generate, «Героя в буфер», «Обрати файл»; Промпти — the **book
  check** (GO / errors / warnings, `check.py`); Картинки — the 16 rows small; Canva — «Зроблено»; **Мокапи** — what the
  book holds, «Зробити / Редагувати мокапи», «Редагувати слайди», the folders (`mockupsBody()`, `mockups_state()`);
  **Фото** — the [photo mockups](photo-mockups.md) (`photosBody()`); Бібліотека — what's missing, «Передати».
- **The rows** (one column of 820 px — the owner: "not the full width"): page 1, spreads 2–3 … 28–29, page 30, **the
  cover last**. Each: its name, «Генерувати» / «Ще раз» / «чекаю картинку»; **the prompt** (the JSON as the generator
  gets it, long ones folded, copy); **the 2:1 frame** (empty — a drop zone); **the text** in the book's font. A short or
  broken prompt file is named above the rows.
- **Prompts and texts are the agents'** — the page never writes them; the owner asks the agent.
- **A picture dragged out of the page is never taken back in** (the browser hands it over as a file): a drag that starts
  in Book Studio's window is shut out of every drop zone ([dragging files](../flows/dropped-files.md)).
- **Hero variants** (Tier H, when the agent made one): tabs «Основна · G2_brunette 3/14». A variant's tab: its hero
  (generate: the base `canonical.png` → «Далі» → the edit prompt → `hero.png`), its spreads one by one (the base spread
  un-mirrored → the variant's hero → the swap prompt → `pictures/variants/<name>/`), and **its own cover** — one frame
  for the finished wide cover, brought to the template (`fit_template()`); «Генерувати» there puts the base cover and
  the variant's hero into the clipboard.
- **The viewer**: every page in order (a variant's tab — the variant's), T for the text, "original" opens the file.

## A picture into its row

`pictures.place()` — the owner's flipper and slicer ([his answers](../raw/2026-09-24-workshop-flipper-owner-answers.md)),
then the [upscaling](#upscaling):

- **A spread**: mirrored when it's one of **4–5, 8–9 … 28–29** (`MIRRORED`; an empty frame says «віддзеркалиться»), cut
  to 2:1 around the centre (the amber «обрізано …»), cut into **two square pages**. ⇄ mirrors by hand; twice gives back
  the same pages. **Pages 1 and 30**: cut to a square when more than 4 % off (`OFF`).
- **The cover, in two stages** (`cover_state()`): ① the picture from Agent 6's prompt → `originals/cover-art.*`, laid on
  **the printer's template** (`TEMPLATE`: 8×8 hardcover, 17.90″×9.50″ with the wrap, finished 16.40″×8.00″;
  `template_layout()`) with white all round → `cover-expanded.png`; ② **Поля**: that picture and the **outpaint prompt**
  (`outpaint_prompt()`), the template's lines as a toggle; the result → `pictures/Cover.png`, exactly 5370×2850 px,
  300 dpi (`fit_template()`). «Без полів» takes the picture as it is.
- **The hero**: `agent/canonical.png` (a variant's `hero.png`).
- A dropped picture is copied; **a caught download is moved** into `originals/`, named by its row. A picture byte for
  byte the row's original replaces nothing — its pages are only cut again (`_same_as_original()`).
- **`originals/` is a store, not a way in**: files put there by hand with the right names show «Підхопити з папки (N)»
  above the rows (`left_behind()`, `adopt()`) — each goes the usual way.
- **«Прибрати» acts at once and offers «Скасувати»** (2026-10-04, the owner's rule of 2026-09-30: a question only for what cannot be taken back): `pictures.remove()` hands back `undo` — where each file waits in `.replaced/`, where it belongs and the row's marks as they were; `pictures.restore()` (`POST …/restore`) puts them back, never over a picture put there meanwhile (409), only from `.replaced/`, only inside the book. The book photo's «Прибрати» (`photos.remove`) still asks: its removal also re-places the scenes in `etsy/`.
- **Whatever is replaced or removed goes to `.replaced/`** (`_retire()`). When another program holds the old file, the
  Workshop waits ~5 s and names that program (`desktop.file_holders()`); nothing is changed.
- «Зберегти як…» on any picture (the folder remembered in `workshop.saveDir`), «Копіювати картинку», «Зберегти
  оригінал як…».

## Upscaling

The owner: "just 2×, whatever size the picture comes in", with a switch for the whole book ([decisions](../decisions.md)).
`upscale.py`:

- **What**: the spreads, pages 1 and 30, the cover, every hero variant's spreads and cover — whenever a picture lands.
  Not the hero pictures. A row is named by its slot: `spread3`, `G2_brunette/spread3`.
- **How**: his **Upscayl**'s command-line engine (`upscayl-bin.exe`), model **upscayl-standard-4x**, output **×2**; found
  in `workshop.upscayl`, else in Upscayl's own log, else its usual installs. **The row's original** is upscaled (a copy
  in `tmp/`), then mirrored and cut as the row is; `Cover.png` stays 5370×2850.
- **In the background, one at a time** (`Upscaler` — the graphics card is shared with the text check): the small pages
  are there at once, the big ones replace them seconds later. A picture replaced meanwhile wins (`WRITING`, the `pic`
  mark).
- **A page of 2400 px or more** (`BIG`, print-ready) isn't upscaled. **The pages themselves are measured** (`sides()`):
  a big original with small pages is only cut again — «Перерізати з великих оригіналів (N)».
- **On the page**: the switch **«Апскейл ×2»** (on by default; off — `"upscale": false` in `book.json`), «Апскейлити
  решту (N)», a chip over each picture («✦ ×2 | 2880 px», «✓ 2880 px», «1440 px», «апскейл 45%», «не апскейлено»), ✦
  among a picture's tools. «Передати в бібліотеку» names the pages not upscaled yet. A failure leaves the small pages.
- Sizes are read from the pictures' headers only (`_size()`) — a book of 370 pictures opens at once.

## The generation mode

`generate.Session`: **«Генерувати»** puts the row's prompt into the **Windows clipboard, by the program itself**
(`clipboard.py`), the row says «чекаю картинку», and the Workshop looks into **Downloads** every 0.6 s: **the first new
PNG/JPEG/WEBP that appears after the press and has finished downloading** is caught into the row — moved, cut,
flipped — with a short sound. Nothing else in Downloads is touched.

- **«Генерувати всю книгу»** («…решту»): the rows with a prompt and no picture — spreads 2–3 … 28–29, then pages 1 and 30
  (`SERIES_ORDER`); after each catch the next prompt is already in the clipboard and the page follows. At the end the
  taskbar button flashes.
- **A spread of a book with a hero** gives **the hero, then the prompt** (the owner attaches the reference every time).
  Pages 1 and 30 and a Tier S book — the prompt alone.
- **A paste of several parts** (a spread with its hero; the cover's margins: the picture, then the prompt; a variant's
  spread; a [photo mockup](photo-mockups.md)) goes one by one: the next part goes in **a moment after Ctrl+V in Chrome**
  (`PasteWatch` — only while Chrome is in front; the keys are only looked at, every 20 ms, only during such a paste).
  **«Далі» or F8 anywhere** do the same (F8 is taken from Windows only then, `Hotkey`).
- The cover's picture, once in, goes on to wait for its margins by itself.
- **The work is the server's**: it goes on while the window is behind Gemini — a notice per catch, a dot on «Книги» in the rail,
  the window's title «● Розворот 10–11 · 6 з 16 — Book Studio» (`bs:busy`).

## «Передати в бібліотеку»

The library's «Нова книга» dialog in its passing-on form (`openAddBook(existing, transfer)`): what's missing, the
**Etsy listing** checked read-only, "take the listing's main photo as the thumbnail". Then `books.to_library()`: **a
library book** with the texts (`book-text.md` — the [text check](text-check.md)'s reference) and the listing. **Its cover
and pages are not copied** (the owner: "one place, no doubles"): the library takes them from this folder's `pictures/`
(`"pagesFrom": "workshop"`, [library](library.md)). The Workshop's book stays and moves to «У бібліотеці». Deleting it
first copies its pages into the library book (`library.keep_pages()`). A listing another book has is refused (409).

## Live, and smooth

- A Workshop page asks `/api/workshop/sig` every 1.5 s while on screen (a book's page — only its own files, `os.scandir`);
  elsewhere, while a picture is awaited, only `/api/workshop/gen`. The generation mode starts only when first used.
- A change redraws **in place** (`patch()` in `lib.js`): unchanged parts stay, a picture already shown is carried over —
  nothing reloads or blinks; one-shot animations run after the redraw.
- Every picture's address carries its version (`?v=`); the browser keeps it for good.
- The page remembers each book's open step, tabs, variant, opened prompts and the cover's stage until a restart.
- **The sandbox** (preview, tests — [preview](../dev/preview.md)): made-up books, Downloads and clipboard as files, no
  window opens, a plain ×2 resize instead of Upscayl.

## Where in the code

- [app/studio/workshop/books.py](../../app/studio/workshop/books.py) — `AREAS`, `ETSY`, `books_dir()`, `book_path()`, `book_ids()`, `STEPS`, `MANUAL`, `ROWS`, `steps()`, `summary()`, `detail()`, `all_books()`, `library_book()`, `set_mark()`, `versions()`, `signature()`, `display_name()`, `mockups_state()`, `MOCKUPS`, `media_file()`, `agent_text()`, `open_in_windows()`, `agent_words()`, `open_agent()`, `antigravity()`, `delete_book()`, `to_library()`, `update_state()`
- [app/studio/workshop/rows.py](../../app/studio/workshop/rows.py) — `row_list()`, `MIRRORED`, `text_sections()`, `book_texts()`, `prompt_objects()`, `as_prompt()`, `book_rows()`, `cover_state()`, `outpaint_prompt()`, `TEMPLATE`, `template_layout()`, `template_guides()`, `variants()`, `book_check()`, `original_stem()`
- [app/studio/workshop/pictures.py](../../app/studio/workshop/pictures.py) — `WRITING`, `place()`, `left_behind()`, `adopt()`, `two_squares()`, `square()`, `OFF`, `build_expanded()`, `fit_template()`, `skip_margins()`, `flip()`, `remove()`, `restore()`, `spread_panorama()`, `picture_for_clipboard()`, `_retire()`, `_same_as_original()`
- [app/studio/workshop/generate.py](../../app/studio/workshop/generate.py) — `Session` (`start_photo()`, `_open()`), `session()`, `downloads_folder()`, `SERIES_ORDER`, `_items()`, `_hero()`
- [app/studio/workshop/upscale.py](../../app/studio/workshop/upscale.py) — `MODEL`, `SCALE`, `KEYS`, `BIG`, `sides()`, `side()`, `slots()`, `split()`, `engine()`, `upscale_row()`, `todo()`, `Upscaler`, `status()`, `after_place()`, `set_on()`, `start()`, `forget()`, `_size()`
- [app/studio/workshop/check.py](../../app/studio/workshop/check.py) — `run()`, `RULES`, `main()`
- [app/studio/workshop/routes.py](../../app/studio/workshop/routes.py) — the routes ([api-routes](../architecture/api-routes.md))
- [app/studio/clipboard.py](../../app/studio/clipboard.py) — `set_text()`, `set_image()`, `Hotkey`, `PasteWatch`, `BROWSERS`, `PASTE_SETTLE`, `sandbox_file()`
- [app/studio/desktop.py](../../app/studio/desktop.py) — `save_file()`, `to_recycle_bin()`, `attention()`, `file_holders()`
- [app/studio/library.py](../../app/studio/library.py) — `create_book()`, `listing_of()`, `follow()`, `keep_pages()`, `take_listing_image()`, `PAGES_FROM_WORKSHOP`
- [app/web/js/pages/workshop.js](../../app/web/js/pages/workshop.js) — `mount()` (`embedded` in «Книги»), `SORTS`
- [app/web/js/workshop-bits.js](../../app/web/js/workshop-bits.js) — `picture()`, `checkWord()`, `STATE_WORDS`, `STATE_TEXT`, `ERRORS`
- [app/web/js/pages/workshop-book.js](../../app/web/js/pages/workshop-book.js) — `mount()`, `WHO`, `photosBody()`
- [app/web/js/pages/workshop-rows.js](../../app/web/js/pages/workshop-rows.js) — `rowTemplates()` (a row: its prompt, its frame, its text), `waitChip()`
- [app/web/js/workshop-live.js](../../app/web/js/workshop-live.js) — `watch()`, `refresh()`, `wake()`, `act()`, `startGen()`, `startPhoto()`, `genAction()`, `genBar()`, `paintGenBar()`, `waitingFor()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `patch()`
- [app/web/js/book-tile.js](../../app/web/js/book-tile.js) — `bookTile()`, `segBar()`, `tickBadge()`
- [app/web/css/listings.css](../../app/web/css/listings.css) — `.ws-card-wait`, `.ws-genbar`, `.ws-strip`, `.ws-step`, `.ws-panel`, `.ws-row`, `.ws-frame`, `.ws-ph`, `.ws-art`, `.ws-cover`, `.ws-tpl`
- [pipeline/AGENTS.md](../../pipeline/AGENTS.md) — the book agents' rules; [pipeline/check_book.py](../../pipeline/check_book.py) — their start of the check
- [app/tools/sample_books.py](../../app/tools/sample_books.py) — `make_books()`
- Tests: [app/tests/test_workshop.py](../../app/tests/test_workshop.py) (`TheSandbox`, `TheBookList`, `ThePathStrip`, `OnlyInsideTheBook`, `TheSignature`, `TheRows`, `TheBookCheck`, `APictureIntoItsRow`, `CatchingDownloads`, `PassingToTheLibrary`)

## Related

- [The rail](modes.md) · [Library](library.md) · [Photo mockups](photo-mockups.md) ·
  [Mockups](mockups.md) · [Book structure](../rules/book-structure.md) · [Decisions](../decisions.md)
