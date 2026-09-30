---
title: The interface waves — one plan, every wave, step by step
type: plan
updated: 2026-09-30
code: []
---
# The interface waves — one plan, step by step

> One page for the whole interface work of 2026-09-30: what each wave was for, **how to do it step by step** (files,
> functions, checks), what is done, what is left. The reasons and the audit's evidence are in
> [the redesign](ui-redesign.md) and [decisions](../decisions.md); the owner's rules — [ui-principles](../owner/ui-principles.md);
> the skills used — [design-skills](../dev/design-skills.md). Read this page to **repeat, extend or undo** a wave.

## How to do any step (the routine)

1. Read [ui-principles](../owner/ui-principles.md) and the skill `book-studio-ui-logic` — show, don't tell; a label does what it
   says; nothing redundant; the real state; one loud button; light theme first.
2. `preview_start("book-studio-dev")` (made-up data, port 47890); set the **light** theme: in the page's console
   `fetch('/api/settings/ui', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({theme:'light'})})`
   and reload. The hidden pane does not run animation frames — check the DOM and take screenshots, `resize_window` to 1400×1000
   and back to `desktop` after; `preview_stop` at the end ([preview](../dev/preview.md)).
3. Make the change; syntax-check each changed `.js` by copying it to `x.mjs` and `node --check x.mjs` (a plain `.js` is not
   parsed as a module); an unused import fails the tests.
4. Look at it in the browser: desktop width, a narrow one (900), light first, then dark; read the console for errors.
5. `cd app && python -m unittest discover -s tests` (469 tests); `python app/tools/wiki_check.py --changed` → update the listed
   pages (content, «Where in the code», `updated:`); a decision → [decisions](../decisions.md); a new word → [glossary](../glossary.md);
   a new route → [api-routes](../architecture/api-routes.md); a new file → [code-map](../code-map.md) and a page's `code:`; an entry in
   [log](../log.md); `python app/tools/wiki_check.py` clean.
6. After a change under `app/studio/` the owner restarts Book Studio. Never commit unless he asks.

## The waves

| # | Wave | Status |
|---|---|---|
| 0 | The structure: places, objects, tools, the rail, the path strip, search | done (2026-09-30, the day's first part) |
| 1 | Contrast, hands and type | done |
| 2 | An honest «done» (✓, not ×) | done |
| 3 | One book, one look | done |
| 4 | A quiet Workshop page | done |
| 5 | Quiet rooms | done (two items dropped on purpose) |
| 6 | Undo instead of questions, one review before print | done (scoped to what can really be undone) |
| 7 | Creative: «Сьогодні», Ctrl+K that does | done (the drop zone left out) |
| Icons | Three redrawn, one added, the hammer and the ruler | done |
| 8 | The drop anywhere, a picture that comes back, the keyboard | done (three items left to the owner or optional) |

### Wave 0 — the structure (already described in [the redesign](ui-redesign.md))

Goal: an order or a book has one home and one path; tools work alone too. Steps, as built: (1) `places.js` — `PLACES`, `TOOLS`,
`SETTINGS`; (2) `app.js` — `ROUTES` with an area each, `ALIASES`, the icons-only rail `buildSidebar()`, `placeOf()`, `navFor()`;
(3) `path.js` — the path strip; (4) `palette.js` — Ctrl+K; (5) `pages/books.js` (Майстерня · Бібліотека · Архів) and
`pages/tools.js`; (6) the Order Creator and the Mockups as a step of their object (`give()` in `handoff.js`, `store.from` in
`info.js` for «back»). Check: every page has one way in; the rail's place stays lit inside an object's tool.

### Wave 1 — contrast, hands and type

Goal: the light theme passes AA, one system for leading and press, no leftovers of the old look.

1. `css/app.css` `:root` (light): `--text-3` `#6d7076` → `#63666c` (4.6 : 1 on `#e7e7e4`); measure with a script, not by eye.
2. Add tokens in `:root`: `--lh-tight: 1.2`, `--lh: 1.4`, `--lh-read: 1.6`, `--press: .96`, `--press-soft: .992`.
3. Map every `line-height: 1.25/1.18 → var(--lh-tight)`, `1.3/1.35/1.4/1.45 → var(--lh)`, `1.5/1.55/1.6/1.62 → var(--lh-read)` in all
   `css/*.css` (39 places); the fixed `13px` (`listings.css` `.mk-slot-no`) → a unitless value.
4. `:active` scales: `.ib`, `.btn`, `.lb-btn` → `scale(var(--press))`; `.tool-tile`, `.ord-row` → `scale(var(--press-soft))`.
5. Weights 400 / 600 only: `listings.css` (`.ws-tabs button.missing`, `.mk-secs`, `.mk-zones > span small`) and `profit.css` (`.dbox-note`) → 400;
   `orders.css` `.tc-alarm-head` 700 → 600. **Keep** 500 on the soft printer chips and the tooltips (the owner's choice, 2026-09-17).
6. `orders.css` `.proof-note dt`: no capitals, no tracking, `clamp(11px, 1.25cqw, 12px)`, colour `#6a6c66`; `.tc-alarm-book figcaption span` no capitals.
7. `.chip` height 22 → 24 (`app.css`); `.mk-clear` 24; `profit.css` `.date-field input { align-self: stretch }`.
8. `pages/mockups.js`: the make button gets `aria-disabled="true"` and `aria-describedby="mk-left"` while something is missing (and stays pressable).

Check: a script lists any text below 4.5 : 1 (3 : 1 for large) — none on the real pages; `getComputedStyle(documentElement)` shows the tokens.
Not done on purpose: 32 px icon buttons stay (a mouse program; 24 px is the floor).

### Wave 2 — an honest «done»

Goal: `×` means *remove* only.
1. `pages/order-card.js` `renderFinish()`, `pages/creator.js` (`#cr-switch`), `pages/mockups.js` (`data-act="close"`): `ib('x', …)` → `ib('checkCircle', …)`.
2. On «Завершити» in the order card and the Creator: `toast('Роботу над замовленням завершено', 'success')` before `location.hash = '#/orders'`.
3. Wiki: glossary («Завершити роботу над замовленням»), orders, order-creator, mockups pages say ✓.
Check: the tick shows only after a draft exists; the queue opens with the toast.

### Wave 3 — one book, one look

Goal: the library's tile and the Workshop's card are one component; progress is drawn one way.
1. `js/book-tile.js`: `segBar(parts, tip)` (`<span class="segbar"><i><b style="transform:scaleX(v)"></b></i>…`), `bookTile({key,title,number,sub,cover,over,bar,meta,i,enter})`, `tickBadge(tip)`.
2. `css/library.css`: replace `.pips` and `.book-id` with `.book-sub`, `.segbar` (`i.skip`, `i.nogo`), `.book-next`, `.book-go`; the grid is `.lib-grid` for both.
3. `pages/library.js` `card()` → `bookTile` (four segments: cover, illustrations, texts, Canva; `sub` = listing id + shield).
4. `pages/workshop.js` `card()` → `bookTile` (eleven segments: done 1, part .5, skip pale; `sub` = the cover's title in `.serif`; `meta` = a chevron,
   the next step, «n/16» for pictures, the prompts check's GO / «N помилок»; `over` = the waiting mark + the tick). Grid `ws-grid` → `lib-grid`.
5. `css/listings.css`: delete `.ws-grid`, `.ws-card`, `.ws-card-*` (keep `.ws-card-wait`, now a small mark inside the cover).
6. `js/path.js`: split out `pathStep(s, i, steps, {act, active, tabs})` (supports `thumb`); `pathHtml` uses it.
7. `pages/workshop-book.js`: `stepHtml()` calls `pathStep` with an icon per step (`STEP_ICON`: sparkle, hero, spread, text, prompt, images, book, canva, mockup,
   camera, shelf); strip container `ws-strip path-strip path-icons` with `style="--steps:11"`; the count and the check move to the tooltip.
8. `css/orders.css`: `.ws-strip.path-icons { grid-template-columns: repeat(var(--steps), minmax(44px, 1fr)); }` (a plain `.path-icons` loses to `listings.css`).
Check: at 1400 and 900 px the strip does not overflow (`scrollWidth === clientWidth`); a click on a step changes the panel; keyed patching keeps the strip smooth.
The state alphabet (filled = done, half = started, empty = not yet, pale/dashed = not needed, red = wrong) is in [ui-principles](../owner/ui-principles.md).

### Wave 4 — a quiet Workshop page

1. `pages/workshop-book.js` `head()`: the book's folder and the shelf become icons in the tools group; «Передати в бібліотеку» is a labelled
   `btn-primary` only when `ready() && !passed`, a tick icon when passed.
2. `pages/workshop-rows.js` `promptBlock()`: `long` from 3 lines; the link text «Весь промпт»; `css/listings.css` `.ws-mono.clamp { max-height: 4.8em }`.
3. (The page already opens at the step that needs attention — nothing to do.)
Check: the loud button count on the page is one; the JSON prompt shows three lines.

### Wave 5 — quiet rooms

1. `pages/tools.js`: a tile is the icon and the name; the sentence is `data-tip` and `aria-label`; the page's caption is gone.
2. `pages/mockups.js` (the Photoshop card): the paragraph becomes two `.chip`s — `ic('image')` + the number Photoshop saves, `ic('hand')` + the number left open (sentences in
   `data-tip`); a `TEMPLATES` plural; `.mk-plan` becomes a centred flex row; the «Папку спитаю…» hint moves to the make button's `data-tip`.
3. `pages/settings.js`: the page caption removed.
Dropped on purpose: a «services ready» strip (each card's header mark says it) and shortened tracking numbers (the owner checks them by eye, 25.09).

### Wave 6 — undo instead of questions, one review before print

Only for what the program can really take back.
1. Server, `studio/library.py`: `_delete` also answers `"trashName": target.name`; a new `POST /api/library/trash/restore` (`_restore`): `{name}` must be a plain name (no path),
   the folder must exist in `TRASH_DIR`, its `book.json` gives the id, the destination must not exist (409), `shutil.move` back under `_lock`. Tests in
   `tests/test_library_creator.py` (`RestoringABook`: comes back; nothing outside the trash; never covers a book). Add the route to [api-routes](../architecture/api-routes.md).
2. `js/lib.js` `toast(message, type, ms, {undo: {label, run}})`: a «Скасувати» button (`.toast-undo` in `app.css`), 9 s, closes after `run()`.
3. `pages/book.js` `deleteBook()`: no `confirmBox`; `DELETE` → `toast(…, 'success', 9000, {undo})` → the undo `POST`s the restore, then opens `#/book/<id>`; the menu item is «Видалити книгу» (no «…»).
4. `pages/order-card.js` `print()`: collect `notes` (wrong book, mistakes, text still checking, not every book ready) and ask **once** with `confirmBox`
   (title by the most serious, `danger` for wrong/mistakes, confirm «Все одно до друку» / «Відправити готові» / «До друку»); no notes — no question.
Kept asking, on purpose: the Windows-Recycle-Bin deletions of the Workshop and the send itself (a picture's delete got its undo in wave 8).
Check (done on the preview server): delete → toast → «Скасувати» → the book is back. **Not exercised live:** the print review with a real ready order.

### Wave 7 — creative

1. `pages/today.js` + the route `^#/today/?$` (area `orders`) + the brand mark as `<a href="#/today">` in `buildSidebar()` + an entry in `PLACES` (for the search).
   Rows are `.tool-tile.today-row` (a picture, a few words, a chip): new orders; tracking to mark in Etsy (`data-stage="sent"` → `orders.js` `openStage('sent')` then the hash);
   a Workshop book whose prompts check failed (red) or whose pictures and cover are done (green); services missing a key (`store.info.integrations`). Empty: «Усе гаразд». Read-only.
2. `palette.js`: `doers` — for each Workshop book not in the library «Мокапи · №N» (`remember('mk-for-book', {id})` then `#/mockups`) and «Слайди · №N» (`#/slides/<id>/1`); `go()` runs `x.run` when there is one.
Check: "мокапи 41" + Enter opens the Mockups with that book selected.

### Icons

`icons.js`: `pin` (a slanted push-pin), `original` (a picture in frame corners), `video` (a film frame; the Omni video in `photos.js` / `workshop-book.js` — `motion` stays the reduce-motion switch),
`workshop` (**a hammer and a ruler crossed**, the owner's wish: the handle over a broken ruler with ticks). Always look at an icon at 96 px and at 16–20 px before keeping it.
`.book-card:focus-visible .book-frame` has a ring (`library.css`).

## Wave 8 — done, and what is left (2026-09-30, the very last)

Done, with how (repeat or extend):
1. **A real Tab walk** (in the built-in pane, real `Tab`/arrow/`Enter`/`Esc` keys, `document.activeElement` read after each): every stop has a ring. Three faults fixed —
   a. `lib.js` `syncSeg()` gives a `.seg` group **one** Tab stop (roving `tabindex`) and a `keydown` handler moves with ←/→/Home/End and chooses the tab it lands on;
   b. `app.js` `shown()` puts the focus on the new page's `<h1>` (`tabindex=-1`, no ring) when the page pressed on is gone; `css/app.css` hides that ring;
   c. `lib.js` `modal()` remembers the opener and returns the focus on close, and a document `keydown` keeps Tab inside the top dialog.
2. **A drop anywhere**: `js/drop-anywhere.js` `installDropAnywhere()` (called in `app.js` `boot()`): `dragenter/over` accept files when the pointer is not over a `[data-folder-drop]` field and no dialog is on top (a
   `.drop-veil` shows it); on `drop` (not `defaultPrevented`, so a page's own field wins) `dropContents()` is read at once, a `bs:dropped` event goes to `#view` — the Order Creator
   (`dropFolder`) and the Mockups (`takeDrop`) set `detail.handled` — otherwise the dialog «Куди?» (`choose()`) offers the Mockups and the Order Creator and does `give(to, {drop})` + the hash; both pages read it
   with `take()` (the Mockups **after** their first paint — before it the state was wiped). Verified with synthetic drops on the preview server: the veil, the dialog, both hand-overs, a drop on an open Creator taken directly.
3. **A picture that comes back**: `studio/library.py` `_trash_asset()` (the file moved to `data/library/trash-assets/<book>/<stamp>-<file>` with a `.json` note of its slot), `_remove_asset` answers `trashAsset`,
   `POST /api/library/books/<id>/assets/restore` (`_restore_asset`: plain name, empty slot, no name clash); tests in `RemovingAPicture`; `pages/book.js` `removeAsset()` with the undo toast.

Left:
1. **A live run of the print review** (the owner): on the real program with an order whose text check found a mistake, see the single dialog; cancel at it — no send is needed.
2. **A real Explorer drag** (the owner, once): drop a Canva ZIP and a book folder on an orders page; «Куди?» appears; the choice opens the right page and it starts taking the files.
3. **The rail with its words on hover** — only if the owner wants it (he chose icons only).
4. **The Workshop's step strip** is still 11 Tab stops (it has its own arrow handler; its `tabs` have no roving stop because no step may be chosen) — make «no step chosen» keep the first as the stop, then the same roving.
5. **Optional, only when touching them**: split `workshop-book.js`, `mockups.js`, `slides-editor.js` by job, as in [the big cleanup](cleanup.md).
6. Keep [ui-principles](../owner/ui-principles.md) and `.claude/skills/book-studio-ui-logic` in step with any new owner correction — the same day.

## Related

[The redesign](ui-redesign.md) · [Decisions](../decisions.md) · [Design skills](../dev/design-skills.md) · [The interface the owner wants](../owner/ui-principles.md) · [Preview](../dev/preview.md)
