---
title: Interface — structure and shared helpers
type: architecture
updated: 2026-09-24
code:
  - app/web/index.html
  - app/web/js/app.js
  - app/web/js/info.js
  - app/web/js/lib.js
  - app/web/js/icons.js
  - app/web/js/handoff.js
  - app/web/js/keep.js
  - app/web/js/lightbox.js
  - app/web/css/app.css
---
# Interface

> One HTML page with no build step: ES modules from `app/web/js`, styles in one `app.css`.
> Pages switch by `#hash`, each one its own module with `mount()`. Since 2026-09-24 the window has
> [two modes](../features/modes.md) — Orders and Listings — each with its own rail and ink.

## Shell and routing — `app.js`

- **Two modes** (`MODES`, since 2026-09-24 — [features/modes.md](../features/modes.md)): the brand icon at the
  top of the rail is the switch (a click, Alt+0). **Orders**: Orders `#/orders` (Alt+1), Library `#/library`
  (Alt+2), Order Creator `#/creator` (Alt+3), Order archive `#/archive` (Alt+4, since 2026-09-18), Settings
  `#/settings` (Alt+5). **Listings**: the Workshop `#/workshop` (Alt+1), the Mockups `#/mockups` (Alt+2). The
  mode on screen is the mode of the page's route (`html[data-mode]`, the accent tokens, the title); each mode
  remembers its last page (`last`, `entryOf()`). The start page is `HOME = '#/orders'`: Book Studio always
  starts in Orders. While a dialog or the viewer is open, Alt+1…5 doesn't switch pages; every
  navigation closes any open menu and tooltip (`closeMenu()`, `hideTip()` in `navigate()`) —
  2026-09-19: the book passport's "More" menu used to stay open over another page. At the bottom — the
  theme menu (dark / light / follow Windows, "reduce motion"). The dot on Settings — when some service
  is missing a key or a sign-in. The active item is marked by a "pill" (`.nav-pill`, `placeNavPill()`)
  that glides with a spring animation. While the page changes, the panel stays "alive" over the
  transition (`.vt-running .nav` has its own `view-transition-name`, the old snapshot is hidden): the
  pill travels **under** the icons, and an icon smoothly changes color. As a separate snapshot, the pill
  would be drawn over the icon — it would vanish while the pill traveled (the owner's note, 2026-09-18).
- **Routes** (`ROUTES`, each with its mode): `#/orders[/<receipt number>]` → `pages/orders.js`, `#/library` →
  `library.js`, `#/book/<id>` → `book.js`, `#/creator` → `creator.js`, `#/archive[/<id>]` → `archive.js`,
  `#/settings[/<section>]` → `settings.js` — the orders; `#/workshop` → `workshop.js`, `#/workshop/<id>` →
  `workshop-book.js`, `#/mockups` → `mockups.js` — the listings. **The Profit page isn't in the routes** — it's hidden until
  1 October ([features/profit.md](../features/profit.md)).
- **A page's contract**: `export async function mount(view, params)` builds content in the given
  element and returns `{ shown(), unmount() }` (both optional). `navigate()` builds the new page off
  screen and swaps them with one View Transition — no empty frames.
- `unmount()` must remove every listener (`on()` returns an unsubscribe function) and timer.
- **Saving work on an order** (since 2026-09-18, the owner's wish; `keep.js`): a controller can also
  have `keep()`, `hidden()`, `revive()` and `receiptId`. If `keep()` returns true when leaving the page,
  `navigate()` doesn't tear it down but hides it: it calls `hidden()` (release global listeners, like Esc
  in the card) and stores the view in `keep.js` along with the page's scroll position and any inner
  scrolling (the proof filmstrip, the right column). Returning to the same hash calls `revive()`
  (asynchronously asks whether the order is still new; `false` or an error → the page is rebuilt) and the
  same view comes back as it was: any running file checks or draft creation finish on their own in the
  meantime. A page that `give()` is waiting for is always rebuilt (`waiting()`). This is how a new
  order's card and an Order Creator filled from an order behave; the queue releases everything about
  orders that have left "New" (`settle()`). Memory only — a restart forgets it all.
  **"Finish" (the ×, since 2026-09-20):** `finish(receiptId)` releases every saved page for this order
  and clears the "draft created" mark; the page it was clicked from is no longer kept (its `keep()`
  returns false) — and the owner ends up in the queue.
- The "Orders" icon (and Alt+1) from another tab goes back to where the owner was in "Orders": an open
  card if it's kept, otherwise the queue (`ordersTarget()`, `lastOrders`).
- `refreshInfo()` → `/api/app` (service status, book count) for the panel and the pages — in its own
  `info.js` together with `store`, so pages don't have to import the shell that loads them; the panel
  redraws via `whenInfoChanges()`.
- Theme and "reduce motion" are both taken from the program's settings the same way on launch (the
  browser only remembers the theme for the first frame); a failed save shows a message.

## Shared helpers — `lib.js`

| What | Functions |
|---|---|
| Safe templates | `` html`…` `` escapes everything except `raw()`; `setHtml()`, `el()` |
| Icon buttons with a tooltip | `ib(icon, tip, attrs, {cls, kbd})`; the shared tooltip `showTip()` / `hideTip()` (`.tip`: up to 320 px, longer wraps to two lines, never past the panel's edge; 2026-09-19) |
| Server | `api()` (token, JSON, `ApiError`), `media()` (a link with a token), `upload()` (XHR with progress), `runJob()` (4th argument `keepGoing()` — stop polling once the result is no longer needed; `job.partial` in `onProgress` — what the job has already found) |
| External links | `openExternal()` — through the server, in the regular browser (Etsy is blocked) |
| Notices | `toast()`, `modal()`, `confirmBox()` (`extra` — markup under the text, e.g. the texts about to be saved), `menu()`, `closeMenu()`, `topLayer()` |
| Segmented switch | `segHtml()`, `syncSeg()`, `setSeg()` |
| Formatting | `money()`, `dateTime()`, `relTime()`, `bytes()`, `plural()`, `highlightTokens()` |
| Smoothness | `fadeImages()` (decoding off the main thread), `slide()` (height), `flip()` (moving cards), `keepFocus()`, `idle()`, `reducedMotion()` |

## The Listings mode's pages (since 2026-09-24)

- [The Workshop](../features/workshop.md) — `pages/workshop.js` (the gallery, built like the library's) and
  `pages/workshop-book.js` (17 row cards: prompt, 2:1 frame, text; its own drag-and-drop — one picture per
  frame, a `.json` anywhere). «Передати в бібліотеку» is the library's `openAddBook()` in its passing-on form.
- [The Mockups](../features/mockups.md) — `pages/mockups.js`, the separate utility's page moved in (its own
  window `mockups.html` + `mockups-shell.js` went). It keeps the usual page contract and adds `keep()`/`revive()`
  so the book, the picks and a run survive stepping away; it tells the rail about a run through the `bs:busy`
  event. Laid out with the Order Creator's own parts (`.creator-grid`, `.card` steps with `.step-no`,
  `.path-input` + `folderPick`, `.v-badge`, `.structure-cover`, `.spread-grid`, `.result-card`) plus its own
  `.mk-*`; a spread or a slot is dragged with its own data types (`application/x-mk-spread`, `…-slot`), so the
  file-drop highlight (`wireFolderDrop()` — files only) never reacts to it.

## Other modules

- `icons.js` — 24×24 icons, 1.6 stroke. **One icon — one meaning.** There are service logos: `etsy`,
  `canva`, `printify`, `gelato`; `sendLog` — the send journal; `orderArchive` — the order archive (a
  sheet with a clock; not `archive`, which means the library's archive); `pin` — "Keep"; `textScan` —
  the text check (lines of text with a magnifying glass; the icon in "Proof", the block in Settings);
  `truck` — "the printer has shipped it" (the tab and the tracking chip; since 2026-09-17 its own
  picture, not an alias for the `package` box icon, which means "shipped on Etsy"); `plus` — "another
  book" in the Order Creator; `mockup` — the Mockups (a book in a picture frame); `hand` — "the
  owner fits this by hand" (the front cover in a mockup template); since 2026-09-24 `listing` — the Listings
  mode (an Etsy listing's tag, its brand icon), `workshop` — the Workshop (a book with a pencil), `prompt` — a
  picture's prompt (a wand; not `sparkle`, which means a new order), `mirror` — ⇄, a Workshop spread mirrored left
  to right (not `swap`, which trades a spread's two pages in the passport).
- Chips (`.chip`): a chip's text is one font (`.chip .num` doesn't switch fonts), `.chip-mono` sits 2 px
  lower so Consolas lines up with the text of other chips.
- `keep.js` — saved pages (`stash()`, `unstash()`, `release()`, `isKept()`, `keptOrder()`); pages with
  no work (the controller says `idle()`) are kept up to `IDLE_KEPT` = 3 — older ones are released (code
  review, 2026-09-19); `settle(orders)` — release anything about orders that are no longer new;
  `markSent()` / `sentOf()` — the Order Creator tells the card that a draft for the order has been
  created; `finish(rid)` — the owner finished work on the order (the ×).
- `handoff.js` — `give(to, data)` / `take(to)` / `waiting(to)`: a one-time handoff between pages, memory
  only (the order card → the Order Creator; the order archive → the Order Creator with `reprint`). A
  handoff from the card carries `books: [{folder, label, title, format}]` — every ready book of the
  order (since 2026-09-20); the first book's fields also sit at the root, so an old single-book form
  still reads as before.
- **A page with several books** (the order card and the Order Creator, since 2026-09-20): state is an
  array, one record per book (`work[]` in the card, `books[]` in the Order Creator), and `pick` says
  which one is shown. Async work (copying, file checking, text checking) is tied to **its own** record
  and its own `seq` counter, so switching books never interrupts or mixes anything; only what's on
  screen gets drawn (`showing()`). `wireFolderDrop()` passes the drop zone into `onDrop` too
  (`[data-folder-drop][data-book]`) — so a drop lands in exactly the book it was dropped on.
- `order-bits.js` — shared by Orders, the order archive and the Order Creator: stages, printer-status
  and tracking chips, the receipt number, the buyer's fields ([features/orders.md](../features/orders.md)),
  [features/archive.md](../features/archive.md)).
- `lightbox.js` — `openLightbox(items, start)`; an item: `src`, `full` (a sharper version when zoomed),
  `title`, `sub`, `text` (the T key), `onOriginal`, `files` (which files are shown), and `actions` —
  buttons at the top (`{icon, label, tip, on, run(lb)}`). Returns `{close, refresh}`: when a page is
  replaced, whoever opened the viewer rebuilds the item array **in place** and calls `refresh()`, and
  the viewer draws the new picture. Mouse wheel, drag with inertia, ← →, Esc.
- **Layers over the page** (since 2026-09-23): the viewer and dialogs share one layer (`z-index` 950),
  so a dialog opened from the viewer ("a draft already exists") sits above it; menus 965, notices 970,
  tooltips 1200. Keys (Esc, ← →) are only handled by the top one (`topLayer()`): Esc closes a dialog
  first, then the viewer. Before this, dialogs and notices used to appear **under** the viewer, with
  focus landing on a hidden button (the 2026-09-22 audit). The `SharedNumbers` test in `test_orders.py`
  keeps this order in place.
- `folderViewerItems(folder, total, sub, v)` — viewer items for a print folder; `v` grows with every
  replaced page and lands in the image address, since previews are cached in the browser for 10 minutes.

## Visual system — `app.css` ("Prepress")

- Color tokens on `:root` (the light "proofing booth" theme) and `[data-theme="dark"]` ("graphite"); the
  theme is set before the first frame by a script in `index.html` (the `bs-theme` key in localStorage).
- Fonts: Bahnschrift — the interface and headings, Segoe UI — text, Sitka — book texts, Consolas —
  numbers/codes.
- Accent — **orange in the Orders mode** (since 2026-09-24, "like Etsy and Claude": `#bf4f1a` / `#f0874d`,
  contrast 4.8/7.0 with the text on it), **"process cyan" in the Listings mode** (`[data-mode="listings"]` and
  `[data-theme="dark"][data-mode="listings"]` redefine `--accent*`; the whole program's colour until then). Service colors: `--printify` (lime green), `--gelato` (blue), `--etsy`,
  `--canva`. The Order Creator's Printify mode and the Printify send card (`.tint-printify`) recolor the
  accent to lime green; its Gelato mode (`.creator.mode-gelato`) — to the old blue, the same "process
  cyan" (the owner, 2026-09-25: once Orders turned orange, Gelato in the Order Creator became orange too — "як було").
- Radii by role: paper is sharp (`--r-art`), controls are soft (`--r-ctl`).
- **60 fps**: only `transform` and `opacity` animate, no blur; `data-motion="reduce"` and
  `prefers-reduced-motion` disable animation the same way (duration, delay and smooth scrolling).
- Preview sizes of 1400 px and up that pages ask for are only the ones the server keeps
  (`images._LARGER`: 1400, 2600, 4096); the `SharedNumbers` test checks the pages against the server.
- Class groups: `.lib-toolbar` (toolbars), `.ord-*` (orders), `.proof*`, `.strip*` (proofing),
  `.creator*`, `.spread-*` (the Order Creator), `.book-*`, `.slot-*` (the library), `.set-*` (settings),
  `.lightbox`, `.lb-*` (the viewer), `.mk-*` (the Mockups: `.mk-tpl`, `.mk-slot`, `.mk-spread`, `.mk-run`, `.mk-ask`, `.mk-turn`, `.mk-ghost`),
  `.ws-*` (the Workshop: `.ws-row`, `.ws-block`, `.ws-frame`, `.ws-ph`, `.ws-art`, `.ws-pairart` — a spread's two pages, `.ws-mark`), `.brand-busy`
  and `.vt-mode` (the mode switch).
- The owner's appearance requirements — [owner/ui-principles.md](../owner/ui-principles.md).

## Where in the code

- [app/web/index.html](../../app/web/index.html) — the `__STUDIO_TOKEN__` token, the theme before the first frame
- [app/web/js/app.js](../../app/web/js/app.js) — `MODES`, `HOME`, `ROUTES`, `navigate()`, `ordersTarget()`, `entryOf()`, `switchMode()`, `unmountSafely()`, `placeNavPill()`, `buildSidebar()`, `buildNav()`, `paintBusy()`, `applyTheme()`, `applyMotion()`, `openThemeMenu()`
- [app/web/js/info.js](../../app/web/js/info.js) — `store`, `refreshInfo()`, `whenInfoChanges()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `html()`, `raw()`, `ib()`, `showTip()`, `api()`, `media()`, `upload()`, `runJob()`, `openExternal()`, `modal()`, `confirmBox()`, `topLayer()`, `menu()`, `segHtml()`, `flip()`, `slide()`, `fadeImages()`
- [app/web/js/icons.js](../../app/web/js/icons.js) — `icon()`
- [app/web/js/handoff.js](../../app/web/js/handoff.js) — `give()`, `take()`, `waiting()`
- [app/web/js/keep.js](../../app/web/js/keep.js) — `stash()`, `unstash()`, `release()`, `isKept()`, `keptOrder()`, `settle()`, `markSent()`, `sentOf()`, `finish()`
- [app/web/js/lightbox.js](../../app/web/js/lightbox.js) — `openLightbox()`, `TAU`, `MAX_ZOOM`
- [app/web/css/app.css](../../app/web/css/app.css) — color tokens at the top of the file; `.lightbox`, `.modal-root`, `.menu`, `.toasts` (layers); `.mk-shell`, `.mk-slot`

## Related

- [Two modes](../features/modes.md) · [Code map](../code-map.md) · [Interface principles](../owner/ui-principles.md) · [Recipes](../recipes.md)
