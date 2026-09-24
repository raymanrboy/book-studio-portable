---
title: Two modes — Orders and Listings (the Workshop, the mockups inside Book Studio)
type: plan
updated: 2026-09-24
code: []
---
# Two modes: Orders and Listings (plan and agreements)

> **Agreed on 2026-09-24** (the owner approved the agent's plan without changes; his words —
> [raw/2026-09-24-listings-mode-owner-answers.md](../raw/2026-09-24-listings-mode-owner-answers.md)).
> Book Studio gets a second mode, **Listings**, switched by a click on the brand icon at the top of the
> rail. It is "another program, separated from everything": the **Workshop** (books in development —
> a prompt, a 2:1 spread and a text for every spread) and the **Mockups** (the Photoshop utility, working
> exactly as before, now inside Book Studio). **Built the same day** on the branch `photoshop-module` —
> how it works now: [two modes](../features/modes.md), [the Workshop](../features/workshop.md),
> [the Mockups](../features/mockups.md). This page keeps the agreements.

## The two modes

- **Orders** — everything as it is: cyan accent, the spread icon, five rail items (Alt+1…5).
- **Listings** — its own "ink": **magenta** (the second colour of the CMYK strip in the logo; the owner's
  pick over Etsy orange and "same colour"). Its own icon at the top, two rail items: **Майстерня**
  (Alt+1) and **Мокапи** (Alt+2); the theme button at the bottom as in Orders.
- **The switch:** a click on the brand icon (or **Alt+0**) goes to the other mode. The switch is animated
  (transform/opacity only): the rail items of one mode slide out, the other's slide in, the icon turns
  over into the new colour, the page cross-fades like any page change.
- The accent colour of the whole window follows the mode (the `--accent*` tokens, both themes).
- The window title: "Book Studio" / "Book Studio · Лістинги".
- **Each mode remembers where the owner was** until a restart (an order's card stays kept by the usual
  rules). **Book Studio always starts in Orders** (the owner's answer).
- While Photoshop works and the owner is in Orders, a small magenta dot sits on the brand icon; a notice
  says when the mockups are ready.
- The mode is decided by the page's address (every route belongs to one mode), not by a separate flag.

## The Mockups inside Book Studio

- **The work doesn't change** (the owner: "Ні, як зараз" — not tied to library books): the four steps, the
  same templates, one "Yes", «Зберегти відкриті й закрити», the taskbar flash and sound.
- The page is kept when the owner leaves it (another page, the other mode): the book, the picks, a running
  Photoshop job and the result wait for him.
- Its settings and runs stay where they were on disk (`app/data/mockups/places.json`, `work/`), so the
  template/Photoshop folders, the last output folder and templates still open carry over.
- **The demo book lives in its own folder** (`app/data/mockups/book/`), not among the files dropped for
  orders: the separate utility wiped all dropped files when a new demo book came in, which inside Book
  Studio would remove the files just dropped into an order's card.
- The separate utility goes (its `.pyw`, window, shortcut, preview server); the old utility's own temp,
  cache and window profile in `app/data/mockups/` (~300 MB) are removed once, on the first launch.

## The Workshop

**What it is** (the owner): "a workshop for making a book — a place where I create books before sending
them to the library with orders; it holds the books that are in development". Not the library: its own
structure.

- **Gallery** (`#/workshop`): like the library's, in magenta — search by title, sort (recent / added /
  by title / least ready), the agent's instruction, "+" (N). **A new book needs only a title** — no Etsy
  listing yet. A card: the cover (else the first spread, else a letter), the title, three readiness strips
  **Prompts · Texts · Pictures**, ✓ when every picture and text is there. No archive: a book leaves by being
  passed to the library or deleted (to the trash).
- **A book** (`#/workshop/<id>`): the header (back — Esc, the title edited in place, the strips, the JSON
  menu `{ }`, "More": the book's folder, delete; the main button **«Передати в бібліотеку»**), then
  **17 row cards in one column of moderate width** (~820 px, centred — the owner: "not the full width"):
  the cover, page 1 (dedication), spreads 2–3 … 28–29, page 30 (afterword).
- **Every card is three rows, top to bottom** (the owner's layout): **the prompt** (copy in one click,
  edit), **the 2:1 frame**, **the text** (the book-text font, `{Name}`/`{Gifter}` highlighted, copy, edit).
- **At first there are no pictures** — only placeholders; the owner fills in prompts and texts, generates
  the pictures elsewhere and drops them in **one at a time**. The frames are **2:1 spreads** (the owner:
  "important"): a dashed frame with the fold in the middle and the page numbers on its halves; a drop or a
  click puts one picture in; upload progress shows; with a picture — zoom, replace, remove (confirmed).
  A picture that isn't 2:1 is taken but marked amber («не 2:1 · 1792×1024») — seen at once, never refused
  (the agent's call). Pages 1 and 30 are single pages: the same 2:1 frame with the endpaper half empty and
  hatched. The cover is one wide picture over the whole frame.
- **Editing**: the field grows with the text; saved on leaving the field or Ctrl+Enter, Esc cancels.
- **Prompts and texts in one JSON** (the owner chose this): paste, load a file or drop a `.json` onto the
  page; copy the book's prompts and texts as JSON. Replacing what's already written is asked first
  ("Замінити 5 промптів і 3 тексти?"). The library's old text-only JSON is accepted too.

  ```json
  { "cover":  {"prompt": "…", "text": "…"},
    "page1":  {"prompt": "…", "text": "…"},
    "spreads": {"2": {"prompt": "…", "text": "…"}, "15": {"prompt": "…", "text": "…"}},
    "page30": {"prompt": "…", "text": "…"} }
  ```
- **The agent's instruction** is written by the program: the book's structure, "every spread prompt
  describes one wide 2:1 illustration over both pages", `{Name}`, `{Gifter}`, `\n`, "return only the JSON".
  The owner adds his style wishes to the agent himself. A test keeps the example readable by the parser.
- Not wanted (the owner's answers): a book-wide style prompt, a Canva link in the Workshop.

## «Передати в бібліотеку»

- A dialog: what's ready and what's missing (amber: "missing spreads 6–7, 10–11 — can be added in the
  library later"), the **Etsy listing link or number** checked through the API like «Нова книга» (read
  only; without keys it can be passed unchecked), "take the listing's main photo as the thumbnail".
- After it the book leaves the Workshop and is in the library at once, with every picture and text;
  orders find it by the listing. A listing already tied to another library book → refused, with a button to
  open that book.
- **One way** for now (no return to the Workshop). The prompts stay inside the book, unseen in the library,
  so a return can be added later without losses. The library's passport doesn't change.

## Data

- A Workshop book is an ordinary library book (`app/data/library/books/<id>/book.json`) with
  `"stage": "workshop"` and a new field `"prompts"` (the same 17 keys as `text`). The listing is empty
  until it is passed on.
- Passing it on = removing the mark and writing the listing: nothing is copied or moved, so everything the
  library already does (pictures, previews, `rev`, the trash) works for the Workshop too.
- **Workshop books never reach the orders**: the library's book list returns library books only unless
  the Workshop asks for its own — the order matching, the book counter and the text check's vocabulary
  stay as they are.

## Related

- [Two modes](../features/modes.md) · [Workshop](../features/workshop.md) · [Mockups](../features/mockups.md) ·
  [Listing mockups](listing-mockups.md) · [Library](../features/library.md) ·
  [Interface](../architecture/frontend.md) · [Decisions](../decisions.md) · [Plans](roadmap.md)
