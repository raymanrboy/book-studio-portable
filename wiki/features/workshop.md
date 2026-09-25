---
title: The Workshop — books in development (the Listings mode)
type: feature
updated: 2026-09-25
code:
  - app/studio/workshop.py
  - app/web/js/pages/workshop.js
  - app/web/js/pages/workshop-book.js
---
# The Workshop (Майстерня)

> The owner's place for making a new book before it goes on sale: "a place where I create books before sending
> them to the library with orders" (2026-09-24). Every row of a book — the cover, the dedication, spreads 2–15,
> the afterword — holds **a prompt** for its picture, **the 2:1 picture** and **the text**. Prompts and texts
> come first (typed, or one JSON from an agent), the pictures last, dropped one per frame. «Передати в
> бібліотеку» gives the book its Etsy listing and sends it to the orders' library. Part of the
> [Listings mode](modes.md); the agreements — [plans/listings-mode.md](../plans/listings-mode.md).

## The gallery (`#/workshop`)

- Like the [library's](library.md), in the Listings mode's cyan: search by title (Ctrl+F or `/`), sorting
  (recently changed, added, by title, least ready first — remembered in `bs-workshop-view`), the agent's
  instruction (copy / save to a file), "+" (key N).
- **A new book needs only a title** — no Etsy listing yet (the dialog says the listing comes when the book is
  passed on); the new book opens at once.
- A card: the cover, else the first finished spread (`_first_picture()`), else the title's first letter; the
  title; the pictures count (`4/17`) and three strips **Prompts · Texts · Pictures** (a tooltip with the
  numbers); ✓ «Готова до бібліотеки» when every picture and text is there (`ready()`).
- No archive: a book leaves the Workshop by being passed to the library or deleted (to the library's trash).
- Empty: «Майстерня порожня» and a «Нова книга» button.

## A book (`#/workshop/<id>`)

- **Header**: back (Esc), the title edited in place (Enter or leaving the field saves), the readiness —
  prompts, texts, pictures, each `n з 17` in its tooltip; `{ }` — the JSON menu; "More" — open the book's
  folder, delete the book (to the trash, confirmed); the main button **«Передати в бібліотеку»**.
- **17 row cards in one column of moderate width** (`.ws-page`, 820 px, centred — the owner: "not the full
  width"): Обкладинка, Сторінка 1 · присвята, Розворот 2–3 … 28–29, Сторінка 30 · післяслово. A row's header
  has three dots: prompt / picture / text there or not.
- **Every card, top to bottom** (the owner's pick of three layouts):
  1. **Prompt** — the copy button (one click, for pasting into an image generator), the pencil; an empty one
     says «Промпт ще не написано — клацніть, щоб написати».
  2. **The frame, 2:1** — the owner: "at first there are no pictures in the Workshop, only placeholders to
     drag them into one at a time … and it's important that these are 2:1 spreads". Empty: dashed, the fold
     in the middle (broken around the words), the page numbers on its halves, «Перетягніть розворот 2:1 · або
     клацніть, щоб обрати файл». A file dragged over lights the frame up; a drop or a click puts **one**
     picture in (several files → «Одна картинка — в одну рамку»); the upload shows its progress.
     **A spread becomes its two pages at once** (the owner's flipper and slicer from `Etsy-Book-Pipeline`,
     2026-09-24 — [below](#a-spread-becomes-two-pages)): the frame then shows two squares side by side, like
     the passport; view, **⇄ mirror**, replace, remove (confirmed: the Workshop's copies are deleted, the
     owner's file stays). Pages 1 and 30 are single pages: the same 2:1 frame, one half the hatched endpaper,
     the other the page (1:1 expected; a picture that isn't is taken but marked amber «не 1:1 · …», 4 %
     tolerance, `OFF`). The cover is one wide picture (back on the left, front on the right), marked the same
     way when it isn't 2:1.
  3. **Text** — the book-text font, `{Name}`/`{Gifter}` highlighted, copy and edit.
- **Editing** a prompt or a text: a click on it or the pencil; the field grows with the text; saved on
  leaving the field or Ctrl+Enter, Esc gives the old one back. A save uses the book's `rev` (a change from
  another window is refused, as in the library).
- **The viewer**: a click on a picture — every picture of the book in order; T shows the page's text; the
  "original" button opens the file in Windows.

## A spread becomes two pages

The owner (2026-09-24): "when I drop a 2:1 spread, a second later it's already two nice squares, like in the
book's passport — flipped by the logic of my flipper". His tools in `D:\Roman\Desktop\Etsy-Book-Pipeline\tools`
(read, never changed): `mirror-alternate.py` and `slice-spreads.py`; his answers —
[raw/2026-09-24-workshop-flipper-owner-answers.md](../raw/2026-09-24-workshop-flipper-owner-answers.md).

- **Mirrored first, like his flipper**: the spreads whose left page divides by 4 — **4–5, 8–9, 12–13, 16–17,
  20–21, 24–25, 28–29** (`MIRRORED`) — are flipped left to right. An empty frame of such a spread says so
  beforehand («віддзеркалиться»).
- **Cut to 2:1 around the centre**: a wider picture loses its sides (like `slice-spreads.py`), **a narrower one
  its top and bottom** (his answer; the slicer would skip it). The frame then shows an amber «обрізано зверху й
  знизу · 1792×1024» (or «з боків») when the picture was more than 4 % off 2:1.
- **Cut into two squares** as high as the picture — the left and the right page — stored as PNG in the
  spread's `left` / `right` (the passport's own two-page form; a whole picture there goes). **Only the two
  pages are kept**, not the panorama (his answer). The slot notes `mirrored` and `source` (the picture's size).
- **⇄ mirrors any spread by hand** (his answer "automatically + a button"): the right page, mirrored, becomes
  the left one and the other way round — the same as mirroring the whole panorama; pressed again, the pages
  come back pixel for pixel (PNG). The button is lit while the spread is mirrored.
- A notice after the drop says what happened («Розворот 4–5: віддзеркалено — і дві сторінки готові»,
  «…обрізано зверху й знизу…»). The viewer shows a spread's two pages one after the other, like the passport's.
- Passed to the library, the book keeps its spreads as two pages — the passport shows them as it always did.

## Prompts and texts in one JSON

- The `{ }` menu: «Вставити JSON…» (a dialog), «Завантажити JSON-файл…», «Скопіювати промпти й тексти як
  JSON», the agent's instruction (copy / save). A `.json` dropped anywhere on the page is imported too.
- The format — the library's book-text JSON where every value is `{"prompt", "text"}`; the library's old
  text-only form (a plain string) is still read as the text (`parse_book_json()`):
  ```json
  { "cover":  {"prompt": "…", "text": "…"},
    "page1":  {"prompt": "…", "text": "…"},
    "spreads": {"2": {"prompt": "…", "text": "…"}, "15": {"prompt": "…", "text": "…"}},
    "page30": {"prompt": "…", "text": "…"} }
  ```
- **What's already written is only replaced after a question**: a dry run first counts it
  («Замінити 5 промптів і 3 тексти, які вже є?»; the same text isn't counted). Then «Заповнено: 17 промптів,
  17 текстів», and what the JSON lacks is named (a few) or counted (many) — a partial JSON is normal.
- **From the owner's `Etsy-Book-Pipeline`** (2026-09-25): its Agent 5 (and Agent 6 again, for the cover) runs
  `tools/build_workshop_json.py "BOOKS_NEW/<book>"` → `workshop.json` in the book's folder — this exact format:
  every prompt is the pipeline's whole JSON prompt object, pretty-printed, as a string (so the copy button gives
  what the generator gets); the texts come from `book-text.md` (`## Cover` — the cover title, `## Spread 01` —
  page 1, `## Spread 02–15`, `## Afterword` — page 30). It replaced the pipeline's `rendered-prompts.md`.
- **The agent's instruction** (`guide()`, the file `Book Studio — промпти й тексти книги.md`): the book's
  structure, "every spread prompt describes one wide 2:1 illustration over both pages", `{Name}`,
  `{Gifter}`, `\n`, "return only the JSON". The owner adds his own style wishes for the agent. A test keeps its
  example readable by the parser (like the library's [agent guide](library.md#agent-guide)).

## «Передати в бібліотеку»

- The library's «Нова книга» dialog in its passing-on form (`openAddBook(existing, transfer)`): what's
  missing on top (amber: «Бракує картинок — 6–7, 10–11 …; текстів — …. У бібліотеці їх можна докласти
  пізніше», or green «Усі картинки й тексти на місці»), the **Etsy listing link or number** checked read-only
  through the API (without keys — passed unchecked), "take the listing's main photo as the thumbnail",
  «Передати в бібліотеку».
- A listing another library book already has → the dialog says so with «Відкрити ту книгу»; the server
  refuses it too (409 with that book's id).
- Passed: «„Назва“ — у бібліотеці замовлень», back to the Workshop; the book is in the library with every
  picture and text, and orders find it by its listing. **One way** for now; the prompts stay in `book.json`,
  unseen by the library.

## Inside

- A Workshop book is a library book with `"stage": "workshop"` and `"prompts"` ([data](../architecture/data.md),
  [library model](library.md#the-book-model-bookjson)): the library keeps its pictures, previews, `rev` and
  trash; `library.all_books()` leaves it out unless asked for `stage="workshop"`, so the orders, the book
  counter and the text check never see it. Passing it on removes the mark and writes the listing — nothing
  is copied.
- The pictures of the cover and pages 1 and 30 go through the library's own route
  (`/api/library/books/<id>/assets`); a spread through the Workshop's (`/api/workshop/books/<id>/spread`,
  `place_spread()`: mirror, cut, two pages), and ⇄ through `/api/workshop/books/<id>/flip` (`flip_spread()`); a library book opened at `#/workshop/<id>` goes to its passport, a Workshop
  book at `#/book/<id>` comes here.

## Where in the code

- [app/studio/workshop.py](../../app/studio/workshop.py) — `create()`, `_workshop_book()`, `import_json()`, `place_spread()`, `two_squares()`, `flip_spread()`, `_put_pages()`, `MIRRORED`, `to_library()`, `guide()`, `GUIDE_NAME`, `LISTING_FIELDS`
- [app/studio/library.py](../../app/studio/library.py) — `WORKSHOP`, `PROMPT_KEYS`, `is_workshop()`, `all_books()`, `parse_book_json()`, `export_book_json()`, `_first_picture()`, `completeness()`, `summary()`
- [app/web/js/pages/workshop.js](../../app/web/js/pages/workshop.js) — `mount()`, `newBook()`, `progress()`, `ready()`, `guideMenu()`, `copyGuide()`, `saveGuide()`, `SORTS`
- [app/web/js/pages/workshop-book.js](../../app/web/js/pages/workshop-book.js) — `mount()`, `ROWS`, `OFF`, `HUMAN`, `flipped()` (the empty frame's «віддзеркалиться»)
- [app/web/js/pages/library.js](../../app/web/js/pages/library.js) — `openAddBook()` (the passing-on form)
- [app/web/css/app.css](../../app/web/css/app.css) — `.ws-page`, `.ws-row`, `.ws-block`, `.ws-frame`, `.ws-ph`, `.ws-art`, `.ws-pairart`, `.ws-mark`, `.ws-will-flip`
- [app/web/js/icons.js](../../app/web/js/icons.js) — `mirror` (⇄; not `swap`, which trades a spread's two pages in the passport)
- Tests: [app/tests/test_workshop.py](../../app/tests/test_workshop.py) (`ANewBook`, `PromptsAndTexts`, `SpreadsBecomeTwoPages`, `PassingToTheLibrary`)

## Related

- [Two modes](modes.md) · [Library](library.md) · [Book structure](../rules/book-structure.md) ·
  [The plan](../plans/listings-mode.md) · [Decisions](../decisions.md)
