---
title: The Workshop — books in development (the Listings mode)
type: feature
updated: 2026-09-24
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

- Like the [library's](library.md), in the Listings mode's magenta: search by title (Ctrl+F or `/`), sorting
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
     picture in (several files → «Одна картинка — в одну рамку»); the upload shows its progress; with a
     picture — view, replace, remove (confirmed: the Workshop's copy is deleted, the owner's file stays).
     **A picture that isn't 2:1 is taken, but marked** amber «не 2:1 · 1792×1024» (4 % tolerance, `OFF`), with
     its margins shown instead of a blur, and a notice says so — never refused (decisions, 2026-09-24).
     Pages 1 and 30 are single pages: the same 2:1 frame, one half the hatched endpaper, the other the page
     (1:1 expected). The cover is one wide picture (back on the left, front on the right).
  3. **Text** — the book-text font, `{Name}`/`{Gifter}` highlighted, copy and edit.
- **Editing** a prompt or a text: a click on it or the pencil; the field grows with the text; saved on
  leaving the field or Ctrl+Enter, Esc gives the old one back. A save uses the book's `rev` (a change from
  another window is refused, as in the library).
- **The viewer**: a click on a picture — every picture of the book in order; T shows the page's text; the
  "original" button opens the file in Windows.

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
- The pictures go through the library's own routes (`/api/library/books/<id>/assets`, slot `cover`,
  `page1`, `spread5`, `page30`); a library book opened at `#/workshop/<id>` goes to its passport, a Workshop
  book at `#/book/<id>` comes here.

## Where in the code

- [app/studio/workshop.py](../../app/studio/workshop.py) — `create()`, `_workshop_book()`, `import_json()`, `to_library()`, `guide()`, `GUIDE_NAME`, `LISTING_FIELDS`
- [app/studio/library.py](../../app/studio/library.py) — `WORKSHOP`, `PROMPT_KEYS`, `is_workshop()`, `all_books()`, `parse_book_json()`, `export_book_json()`, `_first_picture()`, `completeness()`, `summary()`
- [app/web/js/pages/workshop.js](../../app/web/js/pages/workshop.js) — `mount()`, `newBook()`, `progress()`, `ready()`, `guideMenu()`, `copyGuide()`, `saveGuide()`, `SORTS`
- [app/web/js/pages/workshop-book.js](../../app/web/js/pages/workshop-book.js) — `mount()`, `ROWS`, `OFF`, `HUMAN`
- [app/web/js/pages/library.js](../../app/web/js/pages/library.js) — `openAddBook()` (the passing-on form)
- [app/web/css/app.css](../../app/web/css/app.css) — `.ws-page`, `.ws-row`, `.ws-block`, `.ws-frame`, `.ws-ph`, `.ws-art`, `.ws-mark`
- Tests: [app/tests/test_workshop.py](../../app/tests/test_workshop.py) (`ANewBook`, `PromptsAndTexts`, `PassingToTheLibrary`)

## Related

- [Two modes](modes.md) · [Library](library.md) · [Book structure](../rules/book-structure.md) ·
  [The plan](../plans/listings-mode.md) · [Decisions](../decisions.md)
