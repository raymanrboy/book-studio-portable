---
title: The rail — places, tools and search (the two modes until 2026-09-30)
type: feature
updated: 2026-09-30
code:
  - app/web/js/app.js
  - app/web/js/places.js
  - app/web/js/palette.js
  - app/web/js/pages/tools.js
  - app/web/js/pages/today.js
  - app/web/js/pages/books.js
---
# The rail: places, tools and search

> Since 2026-09-30 ([the redesign](../plans/ui-redesign.md)) one labelled rail replaces the two modes (Orders and
> Listings, switched by the brand icon since 2026-09-24): the owner got lost among unlabelled icons in two hidden
> sets. **Places** hold the objects — an order, a book — each with its path; **tools** also work on their own. The
> two inks stay and now follow the area on screen.

## How the owner uses it

- **The rail, top to bottom** (**icons only** since the evening of 2026-09-30 — the owner: "show, don't tell"; the
  words under the icons were tried for a few hours): the brand mark (opens «Сьогодні») · **Замовлення** (Alt+1) ·
  **Книги** (Alt+2) · **Прибуток** (Alt+3) · a gap · **Інструменти** (Alt+4) · a gap · **Пошук** (Ctrl+K — the *last* of the
  list, the owner's wish) · at the bottom **Налаштування** (the dot when a service misses a key or a sign-in) and the
  theme. A tooltip names the place and its key; the page's title says where he is.
- **A click on a place** goes back to where the owner was under it (the order card while it's kept, the book he
  had open); a second click on the place he is in goes to its start (the queue, the gallery, the tools).
- **The ink follows the area**: orange for the orders, the profit, the order tools and Settings; cyan for the books
  and the book tools (the Mockups, the photo mockups, the slides). The brand square takes the ink of where he is.
  Book Studio always starts in the orders.
- **A page that serves an object claims its place** (`navFor()`): the Order Creator opened from an order's card is
  that order's print step — the rail stays on «Замовлення»; the Mockups opened from a Workshop book, and a book's
  slides, stay on «Книги»; an archive entry opened from its order's card, on «Замовлення».
- **«Інструменти»** (`#/tools`; a tile is the name and the picture — what the tool does is its tooltip): every tool that works on its own, in the ink of what it serves — «Для замовлень»:
  the Order Creator, the print archive; «Для книг»: the Mockups, the photo mockups, the listing slides (the scheme for
  new books). The owner's thought: "sometimes I'd like to use each tool on its own".
- **Search everywhere** (Ctrl+K or the magnifier): an order by the buyer, the child or the receipt, a book by its title or
  number (the Workshop's and the library's), a place, a tool, a Settings block; ↑ ↓, Enter, Esc. Empty, it shows the
  new orders and the places. The lists are read when it opens — the orders from the last sync (it never starts one).
  **It also does** (since 2026-09-30, night): «Мокапи · №41», «Слайди · №41» for every book still in the Workshop — the
  verb and the object in a few letters ("мокапи 41" → Enter: the Mockups open with that book chosen). Only ways in: nothing
  is sent, changed or written from here.
- **«Сьогодні»** (`#/today`, the brand mark): what needs the owner now, across every place, as a short list of rows (a
  picture, a few words, a count) — new orders, the tracking numbers to mark in Etsy (opens that tab), a Workshop book whose
  prompts check found mistakes (red) or which is ready for the library, services missing a key. Nothing listed that doesn't
  need him; empty, it says all is well. It only reads — it never starts a sync.
- **The first Tab** is «Перейти до вмісту»: past the rail straight to the page (15 presses to the first order before).
- **Work going on elsewhere is never missed**: a mockups run in Photoshop puts a cyan dot on «Інструменти», a picture
  the Workshop waits for — on «Книги» (hidden while he is on that page); the window's title says what is awaited
  («● Розворот 10–11 · 6 з 16 — Book Studio»), and a notice says when a run ends.

## How it works

- `PLACES` in `app.js` — the rail's places (hash, word, icon, `match`, Alt key, the busy dot); every route in `ROUTES`
  names its area (`'orders'` or `'listings'` — the cyan keeps its old name so the styles keep theirs): the address
  alone says which ink is on screen. `ALIASES` — the galleries' old addresses (`#/library`, `#/workshop`) lead into
  «Книги».
- `navigate()` → `swap()`: sets `html[data-mode]`, asks the page's controller `navFor()`, remembers the address under
  its place (`lastIn`, `entryOf()`), keeps `store.here` / `store.from` (info.js — where the owner came from, for the
  pages' «back»), then `placeNavPill()` glides the pill.
- `places.js` — `PLACES` (for the search), `TOOLS`, `SETTINGS`: one list for the tools page and the search.
- `palette.js` — `openPalette()` (a `modal()` of its own size, `modal-palette`).
- The busy dots: the Mockups page sends `bs:busy` when a run starts and ends, `workshop-live.js` — while a picture is
  awaited; `paintBusy()` shows them and writes the title.

## Before 2026-09-30

Two modes, "like another program, separated from everything" (the owner, 24.09.2026): Orders (the queue, the
library, the Order Creator, the archive, Profit, Settings) and Listings (the Workshop, the Mockups, the photo
mockups), switched by the brand icon (Alt+0); each mode its rail and ink. The inks stayed; the switch went — see
[decisions](../decisions.md).

## Where in the code

- [app/web/js/app.js](../../app/web/js/app.js) — `PLACES`, `HOME`, `ROUTES`, `ALIASES`, `buildSidebar()`, `entryOf()`, `placeOf()`, `placeNavPill()`, `paintBusy()`, `navigate()`, `openSearch`
- [app/web/js/places.js](../../app/web/js/places.js) — `PLACES`, `TOOLS`, `SETTINGS`
- [app/web/js/palette.js](../../app/web/js/palette.js) — `openPalette()`
- [app/web/js/pages/tools.js](../../app/web/js/pages/tools.js) — `mount()`
- [app/web/js/pages/today.js](../../app/web/js/pages/today.js) — `mount()`
- [app/web/js/pages/books.js](../../app/web/js/pages/books.js) — «Книги» ([library](library.md), [workshop](workshop.md))
- [app/web/js/info.js](../../app/web/js/info.js) — `store` (`here`, `from`)
- [app/web/css/app.css](../../app/web/css/app.css) — `.nav-item`, `.nav-label`, `.skip-link`, `[data-mode="listings"]` tokens, `.pal-*`, `.tool-*`

## Related

- [Interface](../architecture/frontend.md) · [Workshop](workshop.md) · [Mockups](mockups.md) ·
  [The interface the owner wants](../owner/ui-principles.md) · [The redesign](../plans/ui-redesign.md) ·
  [The plan of 24.09](../plans/listings-mode.md)
