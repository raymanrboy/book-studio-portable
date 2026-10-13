---
title: The rail — places and tools
type: feature
updated: 2026-10-11
code:
  - app/web/js/app.js
  - app/web/js/places.js
  - app/web/js/pages/tools.js
  - app/web/js/pages/books.js
---
# The rail: places and tools

> One rail of **places** and **tools** (the owner got lost among two hidden sets of icons, so the two modes — Orders and
> Listings, switched by the brand icon — were replaced on 2026-09-30, [decisions](../decisions.md)). **Places** hold the
> objects — an order, a book — each with its path; **tools** also work on their own. The two inks (orange, cyan)
> follow the area on screen.

## How the owner uses it

- **The rail, top to bottom** (**icons only** since the evening of 2026-09-30 — the owner: "show, don't tell"; the
  words under the icons were tried for a few hours): the brand mark (only the logo) · **Замовлення** (Alt+1) ·
  **Книги** (Alt+2) · **Прибуток** (Alt+3) · a gap · **Інструменти** (Alt+4) · at the bottom **Налаштування** (the dot when a service misses a key or a sign-in) and the
  theme. A tooltip names the place and its key; the page's title says where he is.
- **A click on a place** goes back to where the owner was under it (the order card while it's kept, the book he
  had open); a second click on the place he is in goes to its start (the queue, the gallery); **«Інструменти» always opens the list**, never the tool last
  used (2026-09-30). A tool opened on its own has a back arrow to the list (`backToTools()`); opened from an object — to that object.
- **The ink follows the area**: orange for the orders, the profit, the order tools and Settings; cyan for the books
  and the book tools (the Mockups, the photo mockups, the slides). The brand square takes the ink of where he is.
  Book Studio always starts in the orders.
- **A page that serves an object claims its place** (`navFor()`): the Order Creator opened from an order's card is
  that order's print step — the rail stays on «Замовлення»; the Mockups opened from a Workshop book, and a book's
  slides, stay on «Книги»; an archive entry opened from its order's card, on «Замовлення».
- **«Інструменти»** (`#/tools`; a tile is the name and the picture — what the tool does is its tooltip): every tool that works on its own, in the ink of what it serves — «Для замовлень»:
  the Order Creator, the print archive; «Для книг»: the Mockups, the photo mockups, the listing slides (the scheme for
  new books). The owner's thought: "sometimes I'd like to use each tool on its own".
- **No search everywhere** (removed 2026-10-06, the owner: "I don't need search at all"): Ctrl+K and the magnifier
  are gone with `palette.js`. The pages' own filters (the queue, the galleries, the archive, profit) stay.
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
- `places.js` — `TOOLS`: the tools page's list (a tile's tooltip — what it does; «Слайди лістингу»: «Слайди книги з Майстерні · схема для нових книг» since 11.10.2026).
- The busy dots: the Mockups page sends `bs:busy` when a run starts and ends, `workshop-live.js` — while a picture is
  awaited; `paintBusy()` shows them and writes the title.

## Where in the code

- [app/web/js/app.js](../../app/web/js/app.js) — `PLACES`, `HOME`, `ROUTES`, `ALIASES`, `buildSidebar()`, `entryOf()`, `placeOf()`, `placeNavPill()`, `paintBusy()`, `navigate()`
- [app/web/js/places.js](../../app/web/js/places.js) — `TOOLS`
- [app/web/js/pages/tools.js](../../app/web/js/pages/tools.js) — `mount()`
- [app/web/js/pages/books.js](../../app/web/js/pages/books.js) — «Книги» ([library](library.md), [workshop](workshop.md))
- [app/web/js/info.js](../../app/web/js/info.js) — `store` (`here`, `from`)
- [app/web/css/app.css](../../app/web/css/app.css) — `.nav-item`, `.nav-label`, `.skip-link`, `[data-mode="listings"]` tokens, `.pal-*`, `.tool-*`

## Related

- [Interface](../architecture/frontend.md) · [Workshop](workshop.md) · [Mockups](mockups.md) ·
  [The interface the owner wants](../owner/ui-principles.md) · [Decisions](../decisions.md)
