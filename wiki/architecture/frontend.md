---
title: Interface — structure and shared helpers
type: architecture
updated: 2026-10-03
code:
  - app/web/index.html
  - app/web/js/app.js
  - app/web/js/places.js
  - app/web/js/palette.js
  - app/web/js/path.js
  - app/web/js/book-tile.js
  - app/web/js/info.js
  - app/web/js/lib.js
  - app/web/js/icons.js
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
  - app/web/css/slides.css
  - app/web/js/slides/engine.js
---
# Interface

> One HTML page with no build step: ES modules from `app/web/js`, styles in `app/web/css/` (`app.css` and a file
> per section, loaded in that order).
> Pages switch by `#hash`, each one its own module with `mount()`. Since 2026-09-30 one labelled
> [rail of places and tools](../features/modes.md) ; the ink follows the area.

## Shell and routing — `app.js`

- **The rail** (`PLACES`, since 2026-09-30 — [features/modes.md](../features/modes.md)): **Замовлення** `#/orders` (Alt+1), **Книги** `#/books` (Alt+2), **Прибуток**
  `#/profit` (Alt+3), **Інструменти** `#/tools` (Alt+4), «Пошук» (Ctrl+K, last of the list), at the bottom Settings
  `#/settings` and the theme menu (dark / light / follow Windows, "reduce motion"). Icons only (tooltips); a click goes back to where the owner
  was under it (`lastIn`, `entryOf()`) — only while that page still belongs to it (`placeAt`: the Mockups opened
  from a book and later as a tool must not keep pulling «Книги» into them), a second click to its start. The ink is the area of the page's route
  (`html[data-mode]`: `orders` orange, `listings` cyan). The start page is `HOME = '#/orders'`. A page serving an
  object claims its place with its controller's `navFor()` (the Order Creator of an order → «Замовлення»). While a
  dialog or the viewer is open, Alt+1…4 doesn't switch pages; every navigation closes any open menu and tooltip
  (`closeMenu()`, `hideTip()` in `navigate()`) — 2026-09-19: the book passport's "More" menu used to stay open over
  another page. The dot on Settings — when some service is missing a key or a sign-in. The active item is marked by a
  "pill" (`.nav-pill`, `placeNavPill()`) that glides with a spring animation. While the page changes, the panel stays
  "alive" over the transition (`.vt-running .nav` has its own `view-transition-name`, the old snapshot is hidden): the
  pill travels **under** the icons, and an icon smoothly changes color (the owner's note, 2026-09-18). The first Tab
  stop is «Перейти до вмісту» (`#skip`). **The keyboard** (a real Tab walk, 2026-09-30, last): every stop has the 2 px ring; a
  segmented control (`.seg`) is **one** stop with ←/→/Home/End inside it (roving `tabindex` in `syncSeg()`, the keys in `lib.js`);
  when the page pressed on is gone (Enter on a queue row) the focus lands on the new page's title (`shown()` in `app.js`);
  a dialog keeps Tab inside and gives the focus back to the control that opened it (`modal()`).
- **Routes** (`ROUTES`, each with its area): `#/orders[/<receipt number>]` → `pages/orders.js`, `#/books[/work|shop|archive]`
  → `books.js` («Книги»: the Workshop's gallery and the library's in one, since 2026-09-30; `ALIASES` lead `#/library` and
  `#/workshop` there), `#/book/<id>` → `book.js`, `#/tools` → `tools.js`, `#/creator` → `creator.js`, `#/archive[/<id>]` → `archive.js`,
  `#/profit` → `profit.js` (since 2026-09-29; counts from 1 October — [features/profit.md](../features/profit.md)),
  `#/settings[/<section>]` → `settings.js` — orange; `#/book/<id>`, `#/workshop/<book folder>` →
  `workshop-book.js`, `#/mockups` → `mockups.js`, `#/photos` → `photos.js`, `#/slides/<set | template>/<1–7>` →
  `slides-editor.js` (the listing slides' editor, since 2026-09-29) — cyan. A route marked `'lazy'` is left out of the pages' warm-up in `boot()`:
  the editor's code loads the first time it is opened (the owner: "a separate module called only when needed").
- **A page's contract**: `export async function mount(view, params)` builds content in the given
  element and returns `{ shown(), unmount() }` (both optional). `navigate()` builds the new page off
  screen and swaps them with one View Transition — no empty frames.
- `unmount()` must remove every listener (`on()` returns an unsubscribe function) and timer.
- **Saving work on an order** (since 2026-09-18, the owner's wish; `keep.js`): a controller can also
  have `keep()`, `hidden()`, `revive()`, `receiptId`, and since 2026-09-30 `canStartOver()` / `belongsToObject()` (a tool opened from
  «Інструменти» is never revived: `startOver()` drops what was kept — except live work, and an order's own Order Creator stays for its order). If `keep()` returns true when leaving the page,
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
- **Where the owner came from** (since 2026-09-30): `store.here` — the page on screen (while the next one is built,
  still the one being left), `store.from` — the one before it (`info.js`). An archive entry opened from its order's card
  goes back to the card; the Mockups opened from a Workshop book show that book and go back to it.
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
| Server | `api()` (token, JSON, `ApiError`), `post(path, body)` — a POST (85 calls read `api(…, { method: 'POST', body })` until 2026-09-27), `media()` (a link with a token), `upload()` (XHR with progress), `runJob()` (4th argument `keepGoing()` — stop polling once the result is no longer needed; `job.partial` in `onProgress` — what the job has already found) |
| External links | `openExternal()` — through the server, in the regular browser (Etsy is blocked) |
| A compact switch | `segHtml(options, active, {compact: true})` — icons with counts; only the chosen one shows its word (`.seg-compact`, `.seg-label`); `countStages()` marks the to-do tab `.has` (its count takes the ink) |
| What's missing | `markMissing(fields)` — a press that can't go on yet lights up the empty fields (an amber edge until typed in) and focuses the first; the button stays pressable and a notice says what's missing (since 2026-09-30) |
| Notices | `backToTools()` (a tool opened on its own: the arrow to the list), `stickyFit()` (a sticky column taller than the window sticks by its bottom), `toast()` (with `{undo: {label, run}}` — a «Скасувати» button, only for an action the program can really take back; 9 s), `modal()`, `confirmBox()` (`extra` — markup under the text, e.g. the texts about to be saved), `confirmChecked()` (a warning and a box to tick before «Продовжити»; `act()` runs before it closes — the Etsy sign-in, the Printify manual approval), `menu()`, `closeMenu()`, `topLayer()` |
| The shell's dot | `tellBusy(detail)` — the `bs:busy` event: what runs (the mockups, the Workshop's generation) and how a run ended while the window was behind |
| Detail pages | `escBack(hash, {fields})` — Esc back to the list when no dialog, viewer or menu (or, with `fields`, a text field) owns the key; returns `listen(yes)` for a kept page; `notFound(view, {back, backLabel, icon, title, text})` — the page that could not open (the order card, the archived book, the passport, the Workshop's book; since 2026-09-27) |
| Segmented switch | `segHtml()`, `syncSeg()`, `setSeg()` |
| Formatting | `money()` («-$5.00» for a minus; the Profit page's own `usd()` merged into it, 2026-09-27), `dateTime()`, `relTime()`, `bytes()`, `plural()`, `highlightTokens()` |
| A page's own preference | `remembered(key, fallback)` / `remember(key, value)` — kept in the window (a filter, a period, the open cards, the mockups' picks); missing or broken it is the fallback, never an error that stops the page (since 2026-09-26) |
| Smoothness | `fadeImages()` (decoding off the main thread; a picture drawn with `data-fade` is hidden by one CSS rule, `img[data-fade]`, and shown at `data-fade="in"` — fifteen pairs of rules until 2026-09-27), `slide()` (height), `glide(el, mutate)` (a block whose content changed glides to its new height), `flip()` (moving cards), `keepFocus()`, `idle()`, `reducedMotion()` |
| Lists and entrances | `enterOnce(node, delay)` — a row new to a list comes in with the page's entrance once (the class goes when it has played, so a later move never replays it); `patch(container, items, redraw)` — `redraw`: keys changed by hand meanwhile (a text being edited) drawn again even with the same markup. The pages with pictures redraw in place with them (the queue and the archive: a search hides rows; the order card's flow; the Order Creator's step cards and structure; the passport; the mockups' templates; since 2026-09-26) |
| Progress | `setProgress(bar, percent)` — a `.progress > i` bar drawn by a transform (`scaleX`), not its width: no layout on every step (since 2026-09-26) |
| Live pages | `patch()` — a keyed redraw in place (the gone parts removed first and the rest moved with `moveBefore()` where the browser has it, so focus and hover stay; since 2026-09-26): an unchanged part stays, a changed one is replaced, a picture already shown is carried over (the Workshop) |

## An object's path — `path.js` (since 2026-09-30)

`pathHtml(steps, {label, active, act})` — the strip of squares (numbers; with `icon` on every step — pictures,
the word in the tooltip) (`.ws-strip`, `.ws-step`: ✓ done, half-filled started, dashed skipped, red ⚠ where something is
wrong, the next one breathing), drawn for any object: an order's «Canva · Файли · Вичитка · Друк · Відправка» in its card
and in the Order Creator of that order, **and a Workshop book's eleven steps** (one step at a time — `pathStep(s, i, steps,
{act, active, tabs})` — so the book page's keyed patching keeps the strip smooth; `thumb` puts a picture in the square).
The strip takes any number of steps (`--steps`).

**One bar for a book's progress** — `book-tile.js`: `bookTile()` is the library's and the Workshop's tile (a square cover,
a title, one quiet line, `segBar()` — four segments in the library, eleven in the Workshop, `.segbar i > b` filled by
`scaleX`; a «next» line only where there is something to say). **The state alphabet** (the same in the strip and the bar):
filled = done, half = started, empty = not yet, pale/dashed = not needed, red = something is wrong.

## The book pages (cyan)

- [The Workshop](../features/workshop.md) (the book console moved in, 2026-09-26) — `pages/workshop.js` (the gallery
  of the pipeline's books) and `pages/workshop-book.js` (the path strip and its panel, the rows — drawn by `pages/workshop-rows.js` —, the
  cover's two stages, hero variants; its own drag-and-drop — one picture per frame). Both are **live**: `workshop-live.js` asks
  the server what changed every 1.5 s while a Workshop page is on screen (every 4 s while a picture is awaited
  elsewhere) and the page redraws only what changed with `patch()`; it also keeps the generation mode's state, draws
  its bar (`genBar()`) and tells the shell through `bs:busy` (the rail's dot, the window's title). «Передати в
  бібліотеку» is `openAddBook()` (add-book.js — the Library page itself isn't loaded) in its passing-on form (`transfer.send` runs the job).
- [The photo mockups](../features/photo-mockups.md) (2026-09-30) — `pages/photos.js` (the templates by category;
  live through `workshop-live.js` `watch({sigUrl})`, the generation bar without a book) and a Workshop book's step
  «Фото» (`photosBody()` in `workshop-book.js`); `startPhoto()` starts both.
- [The listing slides](../features/slides.md) (2026-09-29) — the Mockups' step 4 (`pages/mockups-slides.js`) and the
  editor `pages/slides-editor.js`, which links its own `css/slides.css` when it mounts (`ensureCss()`), widens its view
  (`.se-view`) and draws with `js/slides/engine.js` — the same engine the headless bake uses (`web/slides/render.html`,
  served as a static file with `fonts/` since the static routes took `fonts` and `slides`). The bake page sets
  `bake: true` in the assets: slide 7's empty frames (`hero:N` with no look) leave no mark there, only in the editor.
- [The Mockups](../features/mockups.md) — `pages/mockups.js`, the separate utility's page moved in (its own
  window `mockups.html` + `mockups-shell.js` went). It keeps the usual page contract and adds `keep()`/`revive()`
  so the book, the picks and a run survive stepping away; it tells the rail about a run through the `bs:busy`
  event, and how a run ended while the window was behind Photoshop (`done` — the shell alone writes the window's
  title, and clears those words when the window comes to the front). Laid out with the Order Creator's own parts (`.creator-grid`, `.card` steps with `.step-no`,
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
  mode (an Etsy listing's tag, its brand icon), `workshop` — the Workshop (a hammer and a ruler crossed, the owner's wish of 2026-09-30),
  `mirror` — ⇄, a Workshop spread mirrored left to right (not `swap`, which trades a spread's two pages in the
  passport); since 2026-09-26 `agent` — the book agents in Antigravity (a chat bubble, the agent typing), `hero` — a
  book's hero, `minus` — a step not needed, `guides` — the printer's template lines (a cover with its spine inside
  crop marks). **The magic wand went** (the owner, 2026-09-26): `prompt` — a prompt for the generator (a prompt sign
  `>_` in a window; the prompt files' tabs), `generate` — «Генерувати» (▷: the prompt into the clipboard, a download
  awaited), `regenerate` — «Ще раз» (↻; not `sync`, which refreshes the orders); `original` — the Workshop's
  originals (a picture in four frame corners — the uncropped one; the square `images` there means the cut pages). The
  weakest pictograms were redrawn on 2026-09-30 (late): `pin` is now a slanted push-pin (the old one read as a flask),
  `original` the corners-and-picture, and `video` (a film frame with a play mark) is the Omni video — `motion` (a wave over
  a line) stays the "reduce motion" switch only, so one icon means one thing.
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
  and tracking chips, the printer's chip (`svcChip()`), the receipt number, the proof with its strip
  (`proofHtml()`), the files' badge and notices (`filesBadge()`, `checkNotices()`), the order list's counts and
  empty states (`countStages()`, `emptyOrders()`), the address (`addressHtml()`), the buyer's fields (`fieldsHtml()`) ([features/orders.md](../features/orders.md)),
  [features/archive.md](../features/archive.md)).
- `folder-viewer.js` — `openFolderViewer(book, start, {total, label, sent, again, decorate, changed})`: the viewer of
  a book's print folder with a page replaced by a file from the computer and put back (the order card and the Order
  Creator, each with its own question and next step; one copy since 2026-09-27).
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

The styles are five files since 2026-09-27 (it was one of 1 500 lines), loaded by `index.html` in the order their
rules had, so no rule moved past another that styles the same element (checked on every page, both themes and a
narrow window — the computed styles of every element were the same): `app.css` — the tokens, the shell, the controls
and everything shared (dialogs, the viewer, Settings, the picker lists), the reduced motion; `library.css` — the
Library and the passport; `orders.css` — the Order Creator, the queue and the card, the archive; `profit.css`;
`listings.css` — the Workshop and the mockups. Each file keeps its own narrow-window rules at its end.

- Color tokens on `:root` (the light "proofing booth" theme) and `[data-theme="dark"]` ("graphite"); the
  theme is set before the first frame by a script in `index.html` (the `bs-theme` key in localStorage).
- Fonts: Bahnschrift — the interface and headings, Segoe UI — text, Sitka — book texts, Consolas —
  numbers/codes.
- Accent — **orange for the orders' area** (since 2026-09-24, "like Etsy and Claude": `#bf4f1a` / `#f0874d`,
  contrast 4.8/7.0 with the text on it), **"process cyan" for the books' area** (`[data-mode="listings"]` on the page
  or on a part of it — the tools' groups — redefines `--accent*`; `html[data-mode="listings"] [data-mode="orders"]`
  brings the orange back inside a cyan page). Service colors: `--printify` (lime green), `--gelato` (blue), `--etsy`,
  `--canva`. The Order Creator's Printify mode and the Printify send card (`.tint-printify`) recolor the
  accent to lime green; its Gelato mode (`.creator.mode-gelato`) — to the old blue, the same "process
  cyan" (the owner, 2026-09-25: once Orders turned orange, Gelato in the Order Creator became orange too — "як було").
- **Type** (since 2026-09-30): five interface sizes with clear steps —
  `--fs-s` 12 (captions, chips, meta) · `--fs` 13 (the base) · `--fs-m` 15 (a card's title) · `--fs-l` 19 (an
  object's or a dialog's title) · `--fs-xl` 25 (a page's title); named exceptions `--fs-book` / `--fs-book-title` (the
  books' own words in Sitka), `--fs-glyph` (a placeholder's letter), `--fs-micro` (keycaps, numbers on thumbnails).
  Every `font-size` in the styles and the pages is a token (the pretend Photoshop dialog and the proof note's paper
  keep their own). Weights 400 / 600 (500 only for the soft printer chips and the tooltips). Section labels in sentence
  case — no tracked capitals (`.eyebrow`, `.section-title`). **Leading in three steps** (late 2026-09-30, was fifteen values):
  `--lh-tight` 1.2, `--lh` 1.4, `--lh-read` 1.6. **Press feedback in two**: `--press` .96 for a control (`.ib`, `.btn`),
  `--press-soft` .992 for a big surface (a queue row, a tool tile). The secondary text colour `--text-3` in light is
  #63666c (4.6 : 1 on the page background; it was 4.0). A chip is 24 px high (the copy chips are click targets; 24 is
  WCAG 2.2's floor).
- Spacing steps `--sp-1…8` (4 / 8 / 12 / 16 / 20 / 24 / 32).
- Radii by role: paper is sharp (`--r-art`), small tags `--r-sm`, controls are soft (`--r-ctl`), groups `--r-grp`,
  cards `--r-card` — every radius is one of them.
- **Three widths** (since 2026-09-30): ≥ 1280 as drawn; 961–1279 (half a screen beside Photoshop) two narrower
  columns — the order card, the Order Creator and the Mockups keep the work and the book's structure side by side;
  ≤ 960 one column.
- The faintest grey `--text-4` is for decoration (placeholder letters, empty frames); text that says something uses
  `--text-3` (4.7 : 1) or stronger.
- **60 fps**: only `transform` and `opacity` animate, no blur; `data-motion="reduce"` and
  `prefers-reduced-motion` disable animation the same way (duration, delay and smooth scrolling).
- Preview sizes of 1400 px and up that pages ask for are only the ones the server keeps
  (`images._LARGER`: 1400, 2600, 4096); the `SharedNumbers` test checks the pages against the server.
- Class groups: `.lib-toolbar` (toolbars), `.ord-*` (orders), `.proof*`, `.strip*` (proofing),
  `.creator*`, `.spread-*` (the Order Creator), `.book-*`, `.slot-*` (the library), `.set-*` (settings),
  `.lightbox`, `.lb-*` (the viewer), `.mk-*` (the Mockups: `.mk-tpl`, `.mk-slot`, `.mk-spread`, `.mk-run`, `.mk-ask`, `.mk-turn`, `.mk-ghost`),
  `.ws-*` (the Workshop: `.ws-card-wait`, `.ws-genbar`, `.ws-strip`, `.ws-step`, `.ws-panel`, `.ws-row`, `.ws-block`, `.ws-frame`, `.ws-ph`, `.ws-art`, `.ws-pairart` — a spread's two pages, `.ws-cover`, `.ws-tpl`), `.nav-item` / `.nav-label` (the rail), `.path-strip` (an order's path), `.pal-*` (the search), `.tool-*`
  («Інструменти»), `.fld` (a field with its name above it), `.is-missing`.
- The owner's appearance requirements — [owner/ui-principles.md](../owner/ui-principles.md).

## Where in the code

- [app/web/index.html](../../app/web/index.html) — the `__STUDIO_TOKEN__` token, the theme before the first frame
- [app/web/js/app.js](../../app/web/js/app.js) — `PLACES`, `HOME`, `ROUTES`, `ALIASES`, `navigate()`, `ordersTarget()`, `entryOf()`, `placeOf()`, `unmountSafely()`, `placeNavPill()`, `buildSidebar()`, `paintBusy()`, `applyTheme()`, `applyMotion()`, `openThemeMenu()`
- [app/web/js/path.js](../../app/web/js/path.js) — `pathHtml()`, `pathStep()`
- [app/web/js/book-tile.js](../../app/web/js/book-tile.js) — `bookTile()`, `segBar()`, `tickBadge()`
- [app/web/js/places.js](../../app/web/js/places.js) — `TOOLS`; [app/web/js/palette.js](../../app/web/js/palette.js) — `openPalette()`
- [app/web/js/info.js](../../app/web/js/info.js) — `store`, `refreshInfo()`, `whenInfoChanges()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `markMissing()`, `html()`, `raw()`, `ib()`, `showTip()`, `api()`, `media()`, `upload()`, `runJob()`, `openExternal()`, `post()`, `tellBusy()`, `glide()`, `money()`, `modal()`, `confirmBox()`, `confirmChecked()`, `escBack()`, `notFound()`, `topLayer()`, `menu()`, `segHtml()`, `flip()`, `slide()`, `fadeImages()`, `patch()`, `enterOnce()`, `setProgress()`, `remembered()`, `remember()`
- [app/web/js/workshop-live.js](../../app/web/js/workshop-live.js) — `watch()`, `refresh()`, `wake()`, `genBar()`, `paintGenBar()`, `startPhoto()`
- [app/web/js/icons.js](../../app/web/js/icons.js) — `icon()`
- [app/web/js/handoff.js](../../app/web/js/handoff.js) — `give()`, `take()`, `waiting()`
- [app/web/js/keep.js](../../app/web/js/keep.js) — `stash()`, `unstash()`, `release()`, `isKept()`, `keptOrder()`, `settle()`, `markSent()`, `sentOf()`, `finish()`
- [app/web/js/lightbox.js](../../app/web/js/lightbox.js) — `openLightbox()`, `TAU`, `MAX_ZOOM`
- [app/web/js/folder-viewer.js](../../app/web/js/folder-viewer.js) — `openFolderViewer()`
- [app/web/css/app.css](../../app/web/css/app.css) — color tokens at the top of the file; `.lightbox`, `.modal-root`, `.menu`, `.toasts` (layers)
- [app/web/css/listings.css](../../app/web/css/listings.css) — `.mk-shell`, `.mk-slot`
- [app/web/css/library.css](../../app/web/css/library.css), [orders.css](../../app/web/css/orders.css), [profit.css](../../app/web/css/profit.css) — the sections' own styles

## Related

- [The rail](../features/modes.md) · [Code map](../code-map.md) · [Interface principles](../owner/ui-principles.md) · [Recipes](../recipes.md)
