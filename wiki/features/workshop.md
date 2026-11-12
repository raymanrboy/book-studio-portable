---
title: The Workshop
type: feature
updated: 2026-11-12
code:
  - app/studio/workshop/books.py
  - app/studio/workshop/rows.py
  - app/studio/workshop/pictures.py
  - app/studio/workshop/generate.py
  - app/studio/workshop/upscale.py
  - app/studio/workshop/check.py
  - app/studio/clipboard.py
  - app/web/js/pages/workshop.js
  - app/web/js/pages/workshop-book.js
  - app/web/js/workshop-live.js
  - app/studio/workshop/__init__.py
  - app/studio/workshop/routes.py
  - app/web/js/pages/workshop-rows.js
  - app/web/js/workshop-bits.js
---
# The Workshop (Майстерня)

> Where a new book is made before it goes on sale: «Книги» → «Майстерня» (`#/books/work`), a book at `#/workshop/<folder>`. A book is a folder of the book pipeline in which Claude Code agents write the formula, hero, story, text and prompts. The Workshop shows the book's path, puts every prompt into the clipboard, **catches the picture the owner downloads from Gemini** into its row (cut, flipped, upscaled), and passes the finished book to the [library](library.md) with its Etsy listing.

## Where a book lives
```
pipeline/                  the book pipeline (in git): knowledge/, scripts/, check_book.py
  books/<n>.<slug>/        NOT in git
    agent/      the agents' files; the Workshop only reads them (except the hero it catches)
    pictures/   the pages, cut and named: Cover.png, 1.png … 30.png — the set for Canva
    originals/  pictures as the generator made them: page-01.jpg, spread-04-05.jpg, cover-art.jpg, hero.png …
    mockups/    mockup pictures, cut-outs, the Canva cover, slides' scenes (mockups.md, slides.md)
    etsy/       what goes into the listing (photo-mockups.md)
    .replaced/  whatever a new picture replaced or a removal took; never deleted
    book.json   the Workshop's state: hand-ticked steps, row marks, cover layout, library book, photo templates
```
- **The folder name is the book's id; the number is its Etsy listing number.** Agents create the folder; the Workshop finds it.
- **Agents write only into `agent/`** and never touch `book.json`, so they cannot break a book's state.
- No IDE is started. «+» and the agent icon put the command for Claude Code's `book` skill into the clipboard (`agent_words()`, `open_agent()`): `/book new` with the books' folder, or `/book <n>` with the book's full path.

## Gallery
- A card per book (the library's tile, `book-tile.js`): square cover, else the cover picture, else the first spread, else the hero; `№25 Title`, one bar of segments (the steps), the next step, the prompts check's GO or «N помилок», a pulsing mark while a picture is awaited.
- Search (Ctrl+F or `/`), sort (`SORTS`, remembered; default most ready first), «У роботі · У бібліотеці», the books folder, «+» (N).

## A book page
- **Header**: back (Esc), `№25 Title`, the Tier chip (H — a child hero on every spread; S — none), icons: agent, pages, originals, folder, «Ще» → delete (at once, «Скасувати»; the folder waits 2 min on the program's shelf, then goes to the Recycle Bin), and «Передати в бібліотеку», which becomes the one loud labelled button once every picture and the cover are there.
- **Generation bar** (sticky, `genBar()`): what is awaited, what is in the clipboard, the parts of a several-part paste, «Далі», «покласти ще раз», «Стоп», queue progress. On another page it names the book that waits, with «Перейти».
- **Path strip** (`STEPS`): Формула → Герой → Історія → Текст → Промпти · GO → Картинки → Обкладинка → Canva → Мокапи → Фото → Бібліотека. A picture per step; tooltip has word, count, check. ✓ done, half-filled started, dashed skipped (a Tier S hero), red ⚠ where the book check found errors, the next one breathes.
- **Steps are ticked by the files** (`steps()`): agents' files, rows whose pages are all in `pictures/`, `Cover.png`. By hand (`MANUAL`): **Canva**, **Мокапи** (also ticks itself when mockups are made for the book), **Фото** (also ticks when every category has a result). **Бібліотека** ticks when passed on and unticks if that library book goes to the trash.
- **Step panel** (click or ← →): the step's file and the agent that writes a missing one, «Відкрити файл у Windows». Герой — generate, «Героя в буфер», «Обрати файл». Промпти — the **book check** (`check.py`, run by `pipeline/check_book.py`). Картинки — the rows small. Обкладинка — [cover](cover.md). Мокапи — what the book holds, «Зробити / Редагувати мокапи», «Редагувати слайди» ([mockups](mockups.md), [slides](slides.md)). Фото — [photo mockups](photo-mockups.md). Бібліотека — what is missing, «Передати».
- **Rows** (one narrow column): page 1, spreads 2–3 … 28–29, page 30, the cover last. Each has its name, «Генерувати» / «Ще раз», the prompt (JSON as the generator gets it; copy it, do not read it), a 2:1 frame (a drop zone) and the text.
- **Prompts and texts belong to the agents**; the page never writes them.
- **Hero variants** (Tier H): tabs per variant. A variant's tab has its hero (base `canonical.png` → edit prompt → `hero.png`), its spreads one by one (`pictures/variants/<name>/`), and its own cover fitted to the template.
- **Viewer**: every page in order (a variant's tab shows its own); `T` the text; «original» opens the file.
- A picture dragged out of the page is never taken back in: a drag that starts in the window shuts out every drop zone ([frontend](../architecture/frontend.md)).

## A picture into its row (`pictures.place()`)
- **A spread**: mirrored when it is one of **4–5, 8–9 … 28–29** (`MIRRORED`), cut to 2:1 around the centre, cut into **two square pages**. ⇄ mirrors by hand; twice gives back the same pages. **Pages 1 and 30** are cut square when more than 4 % off (`OFF`).
- **The cover** has its own tool: [cover](cover.md). **The hero** is `agent/canonical.png` (a variant's `hero.png`).
- A dropped picture is copied; **a caught download is moved** into `originals/`, named by its row. A picture byte-for-byte the row's original replaces nothing; its pages are only cut again.
- `originals/` is a store, not a way in: files put there with the right names show «Підхопити з папки (N)» (`left_behind()`, `adopt()`).
- **«Прибрати» acts at once with «Скасувати»** (`pictures.remove()` / `restore()`); undo never overwrites a picture put there meanwhile (409). The book photo's «Прибрати» still asks, because it re-places scenes in `etsy/`.
- Whatever is replaced or removed goes to `.replaced/`. When another program holds the old file, the Workshop waits ~5 s, names that program and changes nothing.

## Upscaling (`upscale.py`)
- Spreads, pages 1 and 30, the cover and every variant's spreads and cover are upscaled **×2** when a picture lands; hero pictures never.
- Engine: Upscayl's command line `upscayl-bin.exe`, model `upscayl-standard-4x` output ×2 (`MODEL`, `SCALE`), installed by [modules](modules.md); found via `workshop.upscayl`, else Upscayl's own log, else usual installs. The portable copy uses only its own module.
- The row's **original** is upscaled (a copy in `tmp/`), then mirrored and cut as the row is. `Cover.png` stays 5370×2850.
- In the background, one at a time (`Upscaler`; the GPU is shared with the text check): small pages are there at once, big ones replace them seconds later. A picture replaced meanwhile wins. A failure leaves the small pages.
- A page of 2400 px or more (`BIG`) is not upscaled. Pages are measured: a big original with small pages is only cut again («Перерізати з великих оригіналів»).
- The switch **«Апскейл ×2»** is on by default (off = `"upscale": false` in `book.json`); «Апскейлити решту», a chip over each picture, «Передати в бібліотеку» names pages not upscaled yet.
- Upscayl gets a copy of the file so it never holds the book's file; a page held by another program fails with «WinError 32».

## Generation (`generate.Session`)
- **«Генерувати»** puts the row's prompt into the Windows clipboard (`clipboard.py`); the row says «чекаю картинку»; the server looks into Downloads every 0.6 s and catches **the first new PNG/JPEG/WEBP that has finished downloading** into the row, with a short sound. Nothing else in Downloads is touched.
- **«Генерувати всю книгу»**: rows with a prompt and no picture, spreads 2–3 … 28–29, then pages 1 and 30 (`SERIES_ORDER`); after each catch the next prompt is already in the clipboard.
- A spread of a hero book gives **the hero, then the prompt**; pages 1 and 30 and Tier S books give the prompt alone.
- A **several-part paste** (spread with hero, cover margins, variant spread, [photo mockup](photo-mockups.md)) goes one part at a time: the next part goes in after Ctrl+V in Chrome (`PasteWatch`, only while Chrome is in front), or after «Далі» / F8 anywhere (`Hotkey`).
- The work is the server's: it continues while the window is behind Gemini — a notice per catch, a dot on «Книги», the window title `● …` (`bs:busy`).

## «Передати в бібліотеку»
`books.to_library()` makes a library book with the texts (`book-text.md`, the [text check](text-check.md) reference) and the listing (checked read-only). Its cover and pages stay in this folder (`pagesFrom: "workshop"`); the Workshop book moves to «У бібліотеці». A listing another book already has is refused (409). Details of what the library does with it: [library](library.md).

## Live and smooth
- A Workshop page asks `/api/workshop/sig` every 1.5 s while shown (4 s after 30 quiet seconds); elsewhere, while a picture is awaited, only `/api/workshop/gen`. A change redraws in place (`patch()`); picture addresses carry `?v=`.
- The sandbox ([preview](../dev/preview.md)) has made-up books, Downloads and the clipboard as files, a plain ×2 resize, no window.

## Why
- Pictures live once: the library reads `pictures/`.
- Upscaling is just ×2 with one switch; no per-image options.
- Generation is the server's job so it continues while another window is in front; pictures are made on websites with the owner's subscriptions, never through a paid image API.
- «Прибрати» acts with undo; a question is for what cannot be taken back.
- A book's id is its folder, so agents and the Workshop never disagree about which book.

## Where in the code
- [app/studio/workshop/books.py](../../app/studio/workshop/books.py) — `STEPS`, `MANUAL`, `steps()`, `agent_words()`, `open_agent()`, `to_library()`, `delete_book()`
- [app/studio/workshop/rows.py](../../app/studio/workshop/rows.py) — `MIRRORED`, `text_sections()`, `as_prompt()`
- [app/studio/workshop/pictures.py](../../app/studio/workshop/pictures.py) — `place()`, `remove()`, `restore()`, `left_behind()`, `adopt()`, `OFF`
- [app/studio/workshop/generate.py](../../app/studio/workshop/generate.py) — `Session`, `SERIES_ORDER`
- [app/studio/workshop/upscale.py](../../app/studio/workshop/upscale.py) — `Upscaler`, `MODEL`, `SCALE`, `BIG`
- [app/studio/clipboard.py](../../app/studio/clipboard.py) — `PasteWatch`, `Hotkey`
- [app/web/js/pages/workshop-book.js](../../app/web/js/pages/workshop-book.js) — the book page; [workshop-live.js](../../app/web/js/workshop-live.js) — `genBar()`

## Related
- [Library](library.md) · [Cover](cover.md) · [Photo mockups](photo-mockups.md) · [Mockups](mockups.md) · [Slides](slides.md) · [Rail](rail.md) · [Book files](../rules/book-files.md) · [Workshop books](../owner/workshop-books.md)
