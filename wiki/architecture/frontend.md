---
title: Frontend — shell, page contract, helpers
type: architecture
updated: 2026-11-12
code:
  - app/web/index.html
  - app/web/js/app.js
  - app/web/js/places.js
  - app/web/js/info.js
  - app/web/js/order-bits.js
  - app/web/js/drop.js
  - app/web/js/lib.js
  - app/web/js/icons.js
  - app/web/js/path.js
  - app/web/js/book-tile.js
  - app/web/js/handoff.js
  - app/web/js/keep.js
  - app/web/js/lightbox.js
  - app/web/js/folder-viewer.js
  - app/web/js/workshop-live.js
  - app/web/css/app.css
  - app/web/css/library.css
  - app/web/css/orders.css
  - app/web/css/profit.css
  - app/web/css/listings.css
  - app/web/css/motion-mockups.css
  - app/web/css/motion-settings.css
  - app/web/css/slides.css
  - app/web/js/slides/engine.js
---
# Frontend

> One `index.html`, no build step: ES modules in `app/web/js`, styles in `app/web/css`. Pages switch by `#hash`; each page is a module with `mount()`. The UI is light only. Look and feel rules: [UI principles](../owner/ui-principles.md).

## Files

- Icons: `icons.js` is the only catalogue (`icon()`); one icon, one meaning.
- CSS is loaded by `index.html` in this order (keep it: a rule must not move past another that styles the same element): `app.css` (tokens, shell, controls, dialogs, viewer, Settings, reduced motion), `library.css`, `orders.css`, `profit.css`, `listings.css` (Workshop, mockups), plus `motion-mockups.css` and `motion-settings.css` (overrides). `slides.css` is linked by the slide editor when it mounts (`ensureCss()`). Each file keeps its narrow-window rules at its end.

## Shell and routing — `app.js`

- **Rail** (`PLACES`; [rail](../features/rail.md)): Замовлення `#/orders` (Alt+1), Книги `#/books` (Alt+2), Прибуток `#/profit` (Alt+3), Інструменти `#/tools` (Alt+4); at the bottom Settings `#/settings` (with a dot when a service lacks a key or sign-in) and the "reduce motion" switch (`ui.reduceMotion`, `applyMotion()`). Icons only, with tooltips. The start page is `HOME = '#/orders'`.
- A click on a place goes back to where the owner was under it (`lastIn`, `entryOf()`) — only while that page still belongs to the place (`placeAt`); a second click goes to its start. A page serving an object claims its place with its controller's `navFor()`. "Orders" from another tab returns to an open kept card, else the queue (`ordersTarget()`).
- The ink follows the area of the page's route (`html[data-mode]`: `orders` orange, `listings` cyan); a page may redefine it on a part of itself with `[data-mode]`.
- **Keyboard**: a segmented control (`.seg`) is one Tab stop with ←/→/Home/End inside (`syncSeg()`); focus lands on the new page's title after a navigation; a dialog keeps Tab inside and returns focus to what opened it (`modal()`).
- **Routes** (`ROUTES`, each with its area): `#/orders[/<receipt>]` → `pages/orders.js`; `#/books[/work|shop|archive]` → `books.js` (`ALIASES` send `#/library` and `#/workshop` there); `#/book/<id>` → `book.js`; `#/tools` → `tools.js`; `#/creator` → `creator.js`; `#/archive[/<id>]` → `archive.js`; `#/profit` → `profit.js`; `#/settings[/<section>]` → `settings.js` (orange); `#/workshop/<book folder>` → `workshop-book.js`; `#/mockups`, `#/photos`, `#/slides/<set|template>/<1–7>` → `mockups.js`, `photos.js`, `slides-editor.js` (cyan). A route marked `'lazy'` is left out of the warm-up in `boot()` and loads on first open.
- **Where the owner came from**: `store.here` and `store.from` in `info.js`; `refreshInfo()` asks `/api/app` (service status, book count) for the rail. An archive entry opened from an order's card goes back to the card.
- **«Нагору»**: a floating button on every page once `#main` is scrolled more than a screen (`installToTop()`).

## Page contract

- `export async function mount(view, params)` builds content into `view` and returns `{ shown(), unmount() }` (both optional). `navigate()` builds the new page off screen and swaps with one View Transition — no empty frames.
- `unmount()` removes every listener (`on()` returns an unsubscribe function) and timer.
- **Keeping work** (`keep.js`): a controller may also have `keep()`, `hidden()`, `revive()`, `receiptId`, `canStartOver()` / `belongsToObject()`. If `keep()` returns true when leaving, `navigate()` does not tear the page down: it calls `hidden()` (release global listeners) and stores the view with its scroll positions via `stash()`. Returning to the same hash calls `revive()` (asks whether the order is still new; `false` or an error rebuilds the page) and the same view returns, running file checks or draft creation continue meanwhile. A page that `give()` is waiting for is always rebuilt. Idle pages are kept up to `IDLE_KEPT`; `settle(orders)` releases everything about orders that left "New"; `finish(receiptId)` (the ✓) releases every saved page of the order and clears the "draft created" mark (`markSent()` / `sentOf()`). A tool opened from «Інструменти» is never revived (`startOver()`), except live work. Memory only: a restart forgets it all.
- `handoff.js`: `give(to, data)` / `take(to)` / `waiting(to)` — a one-time handoff between pages (order card → Order Creator; archive → Order Creator with `reprint`). From a card it carries `books: [{folder, label, title, format}]`, the first book's fields also at the root.
- **A page with several books** (order card, Order Creator): state is an array, one record per book, and `pick` says which one is shown. Async work (copying, file and text checks) is tied to its own record and `seq` counter, so switching books never mixes anything; only the shown book is drawn. A drop zone `[data-folder-drop][data-book]` lands the drop in exactly that book (`wireFolderDrop()`).
- **Live pages**: `workshop-live.js` asks the server what changed every `FAST` (1.5 s) while a Workshop page is on screen, `SLOW` (4 s) when nothing changed for 30 s, `OFFLINE` while the no-connection overlay is up; the page redraws only what changed with `patch()`. It also keeps the generation bar (`genBar()`) and tells the shell through the `bs:busy` event (rail dot, window title).

## Shared helpers — `lib.js`

| Group | What |
|---|---|
| Templates | `` html`…` `` escapes everything except `raw()`; `setHtml()`, `el()`; `attr(name, value)` writes an escaped attribute |
| Server | `api()` (token, JSON, `ApiError`), `post()`, `upload()` (XHR with progress), `media()` (link with the picture key), `recent(path, ms)` (a heavy list fetched moments ago), `runJob()` (4th argument `keepGoing()`; `job.partial` in `onProgress`), `openExternal()` (through the server; Etsy is blocked, [server](server.md)) |
| Notices | `toast()` (`{undo: {label, run}}` gives «Скасувати», only for an action the program can really take back), `modal()`, `confirmBox()`, `confirmChecked()` (a tick before «Продовжити»; `act()` runs before it closes), `menu()`, `topLayer()` |
| Controls | `ib(icon, tip, attrs, {cls, kbd})` icon button with the shared tooltip (`showTip()`/`hideTip()`); `segHtml()`, `syncSeg()`, `setSeg()`; `markMissing(fields)` lights empty fields amber and focuses the first (a press is never ignored silently); `data-press` makes a `role="button"` non-button respond to Enter/Space |
| Keys, format | `typing()`, `galleryKeys()` (by physical key, so the Ukrainian layout works), `money()`, `dateTime()`, `relTime()`, `bytes()`, `plural()` |
| Pages | `escBack(hash, {fields})` (Esc back to the list unless a dialog, viewer, menu or field owns the key); `notFound(view, {...})`; `backToTools()`; `stickyFit()` |
| Page memory | `remembered(key, fallback)` / `remember(key, value)` — kept in the window; missing or broken gives the fallback, never an error |
| Motion | `fadeImages()`, `slide()`, `glide()`, `flip()`, `enterOnce()`, `setProgress()`, `reducedMotion()` |
| Lists | `patch(container, items, redraw)` — keyed in-place redraw: an unchanged part stays, a changed one is updated in place (attributes, text, children; a new picture shows only once decoded), the gone ones are removed first and the rest moved (`moveBefore()` where available) so focus and hover stay; a focused field is never touched; `data-nomorph` or a key in `redraw` forces a replace |

## Objects' path and tiles

- `path.js`: `pathHtml(steps, {label, active, act})` draws the strip of squares for any object — an order's «Canva · Файли · Вичитка · Друк · Відправка» (card and Order Creator) and a Workshop book's steps; `pathStep()` draws one step so keyed patching stays smooth.
- `order-bits.js` (shared by Orders, archive, Order Creator): chips (`svcChip()`), `proofHtml()`, `filesBadge()`, `checkNotices()`, `countStages()`, `emptyOrders()`.
- `book-tile.js`: `bookTile()` is the one tile of the library and the Workshop (square cover, title, one quiet line, `segBar()`).
- The state alphabet is the same in strip and bar: filled = done, half = started, empty = not yet, pale/dashed = not needed, red = something is wrong.

## Viewers and layers

- `lightbox.js`: `openLightbox(items, start)` returns `{close, refresh}`; an item has `src`, `full`, `title`, `sub`, `text`, `onOriginal`, `files`, `actions`. When a page is replaced, the opener rebuilds the items in place and calls `refresh()`. Wheel, inertia drag, ← →, Esc.
- `folder-viewer.js`: `openFolderViewer(book, start, {...})` shows a print folder and lets a page be replaced by a file from the computer and put back (order card and Order Creator, each with its own next step). `folderViewerItems()` (in `order-bits.js`) adds a version `v` to the image address after each replace, since previews are cached in the browser.
- Layers: viewer and dialogs share `z-index` 950, menus 965, notices 970, tooltips 1200. Only the top layer handles Esc and arrows (`topLayer()`): Esc closes a dialog first, then the viewer. The `SharedNumbers` test keeps this order.
- A preview size the pages ask for above 1400 px must be one of `images._LARGER` (1400, 2600, 4096); `SharedNumbers` checks it.

## Motion mechanics

- Only `transform` and `opacity` animate, no blur; `data-motion="reduce"`, `prefers-reduced-motion` and `ui.reduceMotion` disable animation alike. No `transition: all`.
- Progress fills only where the percent is really known (`setProgress()`); otherwise the indicator is neutral (`.progress.indet`, a spinner).
- Drags that start inside the window are ignored by the file-drop zones ([intake](../flows/intake.md)).

## Why
- Pages never import the shell (`info.js` holds shared state) to avoid import cycles.
- `patch()` keeps style attributes of morphed elements; an element that loses its `style` keeps its old aspect-ratio (no general fix).

## Where in the code
- [app/web/js/app.js](../../app/web/js/app.js) — `PLACES`, `HOME`, `ROUTES`, `ALIASES`, `navigate()`, `ordersTarget()`, `entryOf()`, `placeNavPill()`, `applyMotion()`, `installToTop()`
- [app/web/js/info.js](../../app/web/js/info.js) — `store`, `refreshInfo()`, `whenInfoChanges()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `api()`, `runJob()`, `html()`, `patch()`, `modal()`, `toast()`, `markMissing()`, `escBack()`
- [app/web/js/keep.js](../../app/web/js/keep.js) — `stash()`, `unstash()`, `release()`, `settle()`, `finish()`, `IDLE_KEPT`
- [app/web/js/handoff.js](../../app/web/js/handoff.js) — `give()`, `take()`, `waiting()`
- [app/web/js/workshop-live.js](../../app/web/js/workshop-live.js) — `watch()`, `genBar()`, `FAST`, `SLOW`, `OFFLINE`
- [app/web/js/path.js](../../app/web/js/path.js) — `pathHtml()`, `pathStep()`
- [app/web/js/book-tile.js](../../app/web/js/book-tile.js) — `bookTile()`, `segBar()`
- [app/web/js/lightbox.js](../../app/web/js/lightbox.js) — `openLightbox()`
- [app/web/js/folder-viewer.js](../../app/web/js/folder-viewer.js) — `openFolderViewer()`
- [app/web/js/icons.js](../../app/web/js/icons.js) — `icon()`

## Related
- [Rail](../features/rail.md) · [UI principles](../owner/ui-principles.md) · [Server](server.md) · [Orders](../features/orders.md) · [Archive](../features/archive.md)
