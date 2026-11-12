---
title: The rail
type: feature
updated: 2026-11-12
code:
  - app/web/js/app.js
  - app/web/js/places.js
  - app/web/js/pages/tools.js
  - app/web/js/pages/books.js
---
# The rail: places and tools

> One rail of **places** (objects with a path: an order, a book) and **tools** (they also work on their own). Two inks follow the area on screen: orange for orders, profit, order tools and Settings; cyan for books and book tools. There is no mode switch on the brand icon.

## The rail, top to bottom
Icons only, no words; a tooltip names the place and its key and the page's title says where the owner is.
- brand mark (only the logo) · **Замовлення** `#/orders` (Alt+1) · **Книги** `#/books` (Alt+2) · **Прибуток** `#/profit` (Alt+3) · a gap · **Інструменти** `#/tools` (Alt+4) · at the bottom **Налаштування** (a dot when a service misses a key or sign-in) and the «Анімації» button ([Settings](settings.md)).
- The first Tab press reaches «Перейти до вмісту», past the rail straight to the page.

## Behaviour
- **A click on a place** returns to where the owner was under it (the order card while kept, the book he had open); a second click on the place he is in goes to its start (the queue, the gallery). **«Інструменти» always opens the list**, never the last tool.
- **Tools:** the list (`TOOLS` in `places.js`, drawn by `pages/tools.js`) is the one home of what exists; a tile is name and picture, its tooltip says what the tool does. Each tool opened on its own has a back arrow to the list (`backToTools()`); opened from an object, back goes to that object.
- **A page serving an object claims its place** (`navFor()`): the Order Creator from an order card, and an archive entry from its order's card, keep the rail on «Замовлення»; the Mockups from a Workshop book, a book's slides, and the cover tool from a book stay on «Книги». `navFor()` is implemented by `archive.js`, `cover.js`, `creator.js`, `mockups.js`, `slides-editor.js`.
- **The ink follows the area:** every route names its area (`'orders'` or `'listings'`, the cyan one), so the address alone says which ink is on screen; the brand square takes it. Book Studio always starts on the orders (`HOME`).
- **No global search.** Each list has its own filter or search box (the queue, the archive, profit, the galleries).
- **Work elsewhere is never missed:** a mockups run puts a cyan dot on «Інструменти», a picture the Workshop waits for puts one on «Книги» (hidden while on that page); the window title names what is awaited, e.g. «● Розворот 10–11 · 6 з 16 — Book Studio», and a notice says when a run ends. Pages send `bs:busy` when a run starts and ends; `workshop-live.js` does it while a picture is awaited; `paintBusy()` draws the dots.

## How it works
- `PLACES` in `app.js`: each place has hash, word, icon, `match`, Alt key and an optional busy dot. `ALIASES` map the gallery addresses `#/library` and `#/workshop` into «Книги» (`#/books/shop`, `#/books/work`).
- `navigate()` → `swap()` sets `html[data-mode]`, asks the page's controller `navFor()`, remembers the address under its place (`lastIn`, `entryOf()`), keeps `store.here` and `store.from` (`info.js`, for the pages' «back»), then `placeNavPill()` glides the pill.

## Why
- Two hidden icon sets were confusing; one labelled-by-tooltip rail with a clear place per object replaces them.
- Icons only: show, don't tell.
- Every tool must work alone as well as inside its object.

## Where in the code
- [app/web/js/app.js](../../app/web/js/app.js) — `PLACES`, `HOME`, `ALIASES`, `entryOf()`, `placeNavPill()`, `paintBusy()`
- [app/web/js/places.js](../../app/web/js/places.js) — `TOOLS`
- [app/web/js/pages/tools.js](../../app/web/js/pages/tools.js) — `mount()`
- [app/web/js/info.js](../../app/web/js/info.js) — `store`

## Related
- [Interface](../architecture/frontend.md) · [Interface principles](../owner/ui-principles.md) · [Library](library.md) · [Workshop](workshop.md) · [Mockups](mockups.md) · [Cover](cover.md)
