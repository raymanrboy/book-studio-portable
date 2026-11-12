---
title: Interface principles
type: owner
updated: 2026-11-12
code:
  - app/web/css/app.css
  - app/web/css/library.css
  - app/web/css/orders.css
---
# Interface principles

> The one source of what the owner wants from the interface: minimal, icon-driven, smooth, tidy to the pixel. `.claude/rules/ui.md` holds the short imperative rules; this page holds the cases behind them, the visual tokens, what is kept by decision, and what is still open. The program is light only; every choice (contrast, inks, shadows) is made and checked in light.

## The cases behind the rules
- **Show, don't tell.** The rail is icons only (a tooltip names the place and its key; the page's title says where he is — [rail](../features/rail.md)). The queue's tabs and the books' tabs are icons with counts, only the chosen one shows its word. An order's path is a row of pictures (Canva, files, text check, printer, truck); the word is in the tooltip. A secondary action is an icon (`ib()`); one icon, one meaning.
- **A label does what it says.** A row never says «Позначте в Etsy» when a click merely opens the order; the copyable tracking chips are already in the row. The truck tab's count takes the ink when it holds something (the to-do is shown).
- **Nothing redundant.** A printed order's card has no sentence repeating its status chip and path. Hint lines appear only when something is missing.
- **The real state, not the rule's guess.** A placed order's chip names the printer it went to (`o.provider`); the printer rule's answer shows only before the order exists. The case: a Gelato order whose card said «Printify · 24 стор.».
- **A guard against a slip is loud.** The wrong book being made is a big red banner above everything in the proofing, its own badge and its own question before print ([text check](../features/text-check.md)).
- **No global search.** The Ctrl+K search is gone. The library and the Workshop have their own search box (Ctrl+F or `/`); the pages' filters stay.
- **A button never ignores a press in silence.** A greyed-out button that does nothing reads as "the program is broken": it stays pressable, names what is missing and lights the empty fields (`markMissing()`).
- **A long job says when it is over.** He watches another program meanwhile: the taskbar button flashes, Windows plays its sound, the title says how it ended, and the results themselves (the saved pictures) are shown, not a count.

## A question only for what cannot be taken back
An action the program can undo acts and offers «Скасувати» (a book removed from the library comes back with one press; a Workshop book or a photo template sits on a 2-minute shelf; a picture removed from a library book is set aside, not deleted). A question is for what is gone for good (sending to print), and then **one** review with everything noticed, most serious first, never a string of dialogs. An undo is offered only when it really restores.

## Progress shows only what is known
Where the percent is measured (an upload, a check page by page, the pictures of a book n of 16) the indicator fills in proportion and moves smoothly. Where it cannot be known (waiting for a printer, the model loading, a Windows dialog) it is neutral — an accent edge, a spinner, a sweeping segment — never half-filled, never a floor of 1–3 %. The screen runs at 170–180 Hz, so every change needs frames in between ([frontend](../architecture/frontend.md)); Edge gets no frame-rate flags.

## The keyboard
Every tab stop has a ring; a group of tabs is one stop with the arrow keys; after a page change the focus is on the new page's title; a dialog keeps Tab inside and returns the focus to the control that opened it. A new control or dialog keeps all four.

## One object, one look
- A book is one tile everywhere (`book-tile.js`). Progress is one alphabet: **filled = done, half = started, empty = not yet, pale/dashed = not needed, red = something is wrong** — in an order's path, a Workshop book's steps, the tile's bar. A new place uses `pathStep()` or `segBar()`, not its own shapes or sentences. `×` means remove only; "done" is a ✓.
- Every object has one home and one path: an order in «Замовлення», a book in «Книги». The path strip on top says where it is, and the next step is the loudest thing. Tools (Order Creator, archive, mockups, photo mockups, slides) work alone and, opened from an object's step, carry that object.
- A tool of the family looks like Book Studio: numbered step cards, the path field with the folder-and-magnifier button, status badges, the structure of the book on the right, the header's actions as one icon group. The generation has its own icons (▷ generate, ↻ once more, `>_` a prompt), no magic wand.
- Numbers that mean nothing yet look like nothing: before the first sale Profit's zeros are grey.
- The Workshop's rows are of moderate width; the prompt, the 2:1 frame and the text one under another, the frames empty until the pictures exist.

## Specific requirements
- Forms and the Order Creator open empty. Exception: work on a new order comes back as it was left until the order leaves «Нові».
- No clickable links to Etsy (the listing chip is plain text). Canva is a button, not the full link. Printify/Gelato blocks show the service name only.
- Settings stay minimal: keys, templates, modules.
- Wherever a folder is picked, a folder or ZIP can be dragged in without changing how the field looks.
- The order card: data on the right (sticky), work on the left; proofing is large; the note is large and bold; the child's name is bigger but not huge; the printer status sits next to the recipient's name; the cover-format field has no copy button.
- "Back" returns to where it came from: the same queue tab, search and scroll position.
- The queue row: the child's name bold in the grey line after the time; the printer status on the right; the tracking number in a block coloured by printer (carrier and number in one soft shade, kept apart). Tracking and Etsy order numbers (without «#») copy on click.
- Statuses in plain words, not API text («In transit», not `in_transit`) (`statusText()`, `trackChips()`).
- Text on one line aligns to the baseline, not the block tops; digits do not jump because of another font (the «Gelato · 28 or 30 pages» chip).
- A tooltip is fully visible; a long one wraps. Equal-height toolbar elements; equal weight for equal kinds of data (personalization values bold). Data is structured and collapsed, expanding on click.
- A book's passport has no notes and no illustration filters. The library's «+» sits in the row with search and the icons.
- The filmstrip is smooth and reaches the last spread. Wheel scrolling has in-between frames (`smoothWheel()`). Nothing vanishes and reappears during an animation: the rail's pill travels under the icon, which only changes colour.

## Visual tokens
Defined in [app.css](../../app/web/css/app.css); every value below is a token, not a literal.
- **Fonts:** Bahnschrift (UI, headings), Segoe UI (text), Sitka (book texts and book titles only), Consolas (numbers, codes).
- **Inks:** orange for the orders area (`#bf4f1a` on its text, contrast 4.8); "process cyan" for the books area (`[data-mode="listings"]` redefines `--accent*`; `html[data-mode="listings"] [data-mode="orders"]` restores orange). Orange or cyan never paints a number. Services: `--etsy` orange, `--canva` purple, `--gelato` blue, `--printify` lime (old Printify orders still show it). The Gelato send mode (`.creator.mode-gelato`) tints the accent cyan; a Printify card (`.tint-printify`) lime.
- **Type:** five sizes `--fs-s` 12, `--fs` 13, `--fs-m` 15, `--fs-l` 19, `--fs-xl` 25; exceptions `--fs-book`, `--fs-book-title`, `--fs-glyph`, `--fs-micro`. Every `font-size` is a token. Weights 400/600 (500 only for soft printer chips and tooltips). Section labels in sentence case, no tracked capitals. Leading `--lh-tight` 1.2, `--lh` 1.4, `--lh-read` 1.6.
- **Text colour:** `--text-3` (`#63666c`, 4.6:1) for text that says something; `--text-4` is decoration only.
- **Space and shape:** `--sp-1…8` (4/8/12/16/20/24/32 px); radii by role `--r-art` (paper, sharp), `--r-sm`, `--r-ctl`, `--r-grp`, `--r-card`. A chip is 24 px high (the WCAG 2.2 floor); `.chip-mono` sits 2 px lower to line up.
- **Press feedback:** `--press` .96 (a control), `--press-soft` .992 (a big surface).
- **Widths:** ≥1280 full; 961–1279 two narrower columns (order card, Order Creator and Mockups keep work and structure side by side); ≤960 one column.
- **Motion:** `--d-1` 120, `--d-2` 200, `--d-3` 320, `--d-4` 480 ms, `--d-out` 150 ms, `--ease-out`, `--ease-in`. Enters 200–320 ms, exits 120–170, hover ≥120; only `transform` and `opacity`, no blur; stagger capped near 240 ms; a reduce-motion switch (`reducedMotion()`).
- **Progress:** `.progress.live` glides 700 ms.
- **Icons:** one icon, one meaning: `truck` = printer shipped, `package` = shipped on Etsy; `orderArchive` is not `archive`; `motion` only for reduce-motion.
- **Layers:** z-index 950 viewer and dialogs, 965 menus, 970 notices, 1200 tooltips.

## Kept by the owner's decision
Someone may be tempted to "fix" these:
- Smooth entrances and transitions of 420–700 ms (his 170 Hz screen).
- The step squares: their fill is the state.
- Sitka only for book titles and book text.
- Purple chips: replacement, bundle, archived book — each a meaning.
- Three switch styles — `switch` (Settings), `check` (lists), `seg` (modes) — one role each.

## Open
- Spacing is partly off the 4 px grid (6, 10, 14, 18, 22 px gaps and paddings remain); wanted: a few gaps and two or three card paddings, everything mapped onto them.
- Some sizes come from `em` multiplications and miss the scale (about 11.96, 13.34, 20.2 px); the slide editor has its own 29 and 44 px.
- Some line heights sit outside 1.2/1.4/1.6 (1.05–1.2 and 0 to check); mono is used for some meta lines beyond codes.
- Too many sentences on the Workshop book page, the book passport and Settings; the empty frames repeat the same caption.
- At about 800 px Profit's «Не оплачено» pill touches the card edge.

## Where in the code
- [app/web/css/app.css](../../app/web/css/app.css) — the tokens above, `.chip-mono`
- [app/web/css/library.css](../../app/web/css/library.css) — `.lib-toolbar`
- [app/web/css/orders.css](../../app/web/css/orders.css) — `.tint-printify`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `ib()`, `markMissing()`, `fadeImages()`, `reducedMotion()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `statusText()`, `trackChips()`, `smoothWheel()`
- [app/web/js/path.js](../../app/web/js/path.js) — `pathStep()`; [app/web/js/book-tile.js](../../app/web/js/book-tile.js) — `segBar()`

## Related
- [Frontend](../architecture/frontend.md) · [Working with the owner](working-with-owner.md) · [Rail](../features/rail.md) · [Decisions](../decisions.md)
