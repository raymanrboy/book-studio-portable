---
title: The interface the owner wants
type: owner
updated: 2026-10-28
code:
  - app/web/css/app.css
  - app/web/css/library.css
---
# The interface the owner wants

> Minimal, icon-driven, smooth (60 fps), tidy down to the pixel. No unnecessary explanations — only what
> a given action needs.

## The light theme is the main one

The owner uses the **light theme every day** ("all design decisions from now on — by it"). The program still starts dark
until he picks otherwise in the rail's theme menu, but every design choice — contrast, inks, surfaces, icons, shadows — is
made and checked in **light first**, then confirmed in dark.

## Show, don't tell

The owner: "I want the interface to **show**, not tell: a minimum of captions, a maximum of icons and visual language." And, about a row
button that only opened the order: "such silly things are bad UX". The project skill
`.claude/skills/book-studio-ui-logic` ([design-skills](../dev/design-skills.md)) holds the rules:

- **Icons over words.** The rail is icons only (a tooltip names the place and its key; the page's own title says where
  he is — [the rail](../features/modes.md)). The queue's tabs and «Книги»' tabs are icons with counts — only the chosen one shows its word. An order's path
  is a row of pictures (Canva · files · text check · printer · truck), the word in the tooltip. The refresh is an icon.
- **A label does what it says.** A row never says «Позначте в Etsy» when a click merely opens the order; the copyable
  tracking chips are already in the row. No next-step sentences on rows; the truck tab's count takes the ink when it
  holds something (the to-do is *shown*).
- **Nothing redundant**: a printed order's card has no sentence repeating its status chip and path.
- **The real state, not the rule's guess**: a placed order's chip names the printer it went to (`o.provider`); the printer
  rule's answer is shown only before the order exists (a Gelato order said «Printify · 24 стор.»).
- **No search** anywhere: the owner never used it; the pages' own filters stay.

## A question only for what cannot be taken back

An action the program can undo **acts and offers «Скасувати»** (a book removed from the library comes back with one press);
a question is for what is gone for good (sending to print) — and then
**one** review with everything noticed, most serious first, not a string of dialogs. A picture removed from a library book is
set aside, not deleted, so it too comes back with one press An undo is offered only when it really restores.

## Progress is shown only as far as it is known

- The owner disliked step squares and icons «filled to a half». **Where the percent is really known** — an upload, a check page by page, the pictures of a book
  (n of 16) — the indicator fills **in proportion** and moves smoothly. **Where it cannot be known** (waiting for a printer, the model loading, a Windows
  dialog) it is **white / neutral** (an accent edge, a spinner, a sweeping segment) — never half-filled, never a floor of 1–3 %.
- The 170–180 Hz screen: every change has frames between ([frontend → Motion](../architecture/frontend.md)).

## The keyboard

A real Tab walk was made: every stop has a ring; a group of tabs is **one** stop with the arrow keys; after a page change
the focus is on the new page's title; a dialog keeps Tab inside and returns the focus to the control that opened it. A new
control or dialog keeps all four.

## One object, one look

A book is drawn **one way** everywhere: the library's and the Workshop's tiles are the same tile (`book-tile.js`), and progress
is always the same alphabet — **filled = done, half = started, empty = not yet, pale/dashed = not needed, red = something is
wrong** — in an order's path, a Workshop book's eleven steps, the tile's bar. A new place that shows a state uses that
alphabet (`pathStep()`, `segBar()`), not its own shapes or sentences. `×` means *remove* only; «done» is a ✓.

## Understood without hints

The owner: "the functions are scattered as if someone spilled grain… I want to sit down and know at once where to
click, with no labels and hints: everything needed in front of the eyes, everything extra appearing when needed." He
handed the decisions over ("you're the expert, you're the boss") ([decisions](../decisions.md)):

- **Every object has one home and one path.** An order lives in «Замовлення», a book in «Книги»; its path strip on
  top says where it is and what's next, and the next step is the loudest thing on the screen.
- **Tools work on their own too** (the owner's thought): the Order Creator, the print archive, the Mockups, the photo
  mockups, the slides are in «Інструменти»; opened from an object's step they carry that object (its head, its way
  back, its place lit in the rail).
- **The rail is seen, not remembered**: each place has its own icon, its own place for good; the inks follow the area (orders orange,
  books cyan).
- **The queue is a to-do list**: its tabs in words («Позначити в Etsy» is a task, not a filter), each row says what's
  next.
- **One loud button per screen** — the next step; the rest are quiet (a labelled button, an icon with its tooltip).
- **Numbers that mean nothing yet look like nothing**: before the first sale the Profit's zeros are grey, not green.
- **Three widths**: a half screen beside Photoshop keeps the work and the book's structure side by side.

## General

- **A button never ignores a press in silence**: a greyed-out button that does nothing on a
  click reads as "the program doesn't work". Keep it pressable and say what's missing (light up the empty
  fields — `markMissing()`), and show what's being waited for (e.g. a Windows dialog).
- **A long job says when it's over** ("is there any message that it's finished?"): the owner
  watches another program meanwhile (Photoshop), so the result card alone isn't enough — the window's
  taskbar button flashes, Windows plays its sound and the title says how it ended. Show the results
  themselves (the saved pictures), not just a count.
- **Two inks**: the orders are orange, "like Etsy and Claude"; the books wear cyan; one rail, the ink following the area
  ([the rail](../features/modes.md)).
- **The Workshop's rows are of moderate width**, not the full window: the prompt, the 2:1 frame
  and the text one under another, the frames empty until the pictures are generated
  ([workshop](../features/workshop.md)).
- **A tool of the family looks like Book Studio** («Мокапи»: "exactly like Book Studio"):
  numbered step cards, the path field with the folder-and-magnifier button, status badges, the structure
  of the book on the right — the same parts, not look-alikes. The same for the Workshop ("the icons, fonts
  and text look like some other style… everything neat and crisp, everywhere"): the
  header's actions as one group of icons, the passport's section headings, drop zones and text blocks, the Order
  Creator's square step numbers, font sizes only from the program's scale (five sizes with clear
  steps; section labels in sentence case, not tracked capitals — [frontend](../architecture/frontend.md));
  **no magic wand** — the generation has its own icons (▷ generate, ↻ once more, `>_` a prompt).
- **A tooltip should be fully visible** — a long one wraps to a second line instead of getting cut off.
- **Icons instead of text buttons** for secondary actions; their meaning lives in the tooltip (`ib()`).
  One icon — one meaning. The queue's tabs carry words (a task, not a filter).
- **No explanatory text** in blocks ("unnecessary explanations" were removed several times). A hint line
  appears only when something is missing.
- **Equal height** for elements in toolbars (the "+" button = the sort control's height, a bit wider).
- **Equal text weight** for equal kinds of data (never mix bold and regular); personalization values in
  the card are bold.
- **Data is structured and collapsed**, expanding on click (personalization in the order picker).
- A small icon instead of a labeled button (the "clear address" eraser).
- **Smoothness**: only `transform`/`opacity` animate, no blur; mouse-wheel scrolling has in-between
  frames, no "snapping" ([smoothWheel](../features/orders.md)). Nothing should vanish and reappear
  during an animation: the pill in the sidebar menu travels under the icon, which only smoothly changes
  color.
- Dark theme by default; the image viewer follows the program's theme too.
- Service colors: **Printify — lime green**, **Gelato — blue**, Etsy — orange, Canva — purple.

- **A guard against a slip is loud** ("not just a message — a big red one, a guard against a
  slip"): when the program sees the wrong book being made, it's a big red banner above everything in
  "Proofing", its own badge and its own question before print — not one more row in a list
  ([text check](../features/text-check.md)).

## Specific requirements

- The Order Creator and every form **open empty** — no cached folders, addresses, or drafts.
  **Exception:** work on a new order — the card and the Order Creator come back exactly as
  they were left (even a successful-creation page), until the order leaves "New".
- **No clickable links to Etsy** (the listing chip is plain text).
- **Canva — a button**, not the full link.
- In Printify/Gelato blocks — only the service name, no technical detail.
- Settings — kept minimal: keys and templates.
- Anywhere a folder is picked, a **folder or ZIP can be dragged in** without changing how the field looks.
- The order card: **data on the right (sticky), work on the left**; proofing is large; the note's text
  is large and bold; the child's name in personalization is bigger, but not huge; the cover-format field
  has no copy button.
- The page filmstrip is smooth, and reaches all the way to the last spread.
- **Text on one line aligns to the text baseline**, not to the top edge of the blocks; digits shouldn't
  "jump" because of a different font (the "Gelato · 28 or 30 pages" chip).
- **Statuses in plain language**, not raw API text: "In transit", not `in_transit` (English is fine).
- **"Back" returns to where it came from**: from the card — to the same queue tab ("Sent", etc.), with
  the same search and scroll position, not to the start ("it feels inconsistent" otherwise).
- The queue: the child's name — bold, in the gray row after the time; the printer status — on the right;
  the tracking number — in a block colored by printer, the carrier and the number both colored, but kept
  apart.
- **Equal contrast** for colored text in the same place: the printer's name, the carrier, and the number
  — all one soft shade (the owner picked the softest option).
- **Numbers copy on click** — the tracking number and the Etsy order number (without "#").
- The order card: the printer status sits next to the recipient's name, centered.
- In a book's passport: no notes, no illustration filters.
- The library: "+" sits in the same row as search and the icons.

## Where in the code

- [app/web/css/app.css](../../app/web/css/app.css) — the color tokens and `.chip-mono`
- [app/web/css/library.css](../../app/web/css/library.css) — `.lib-toolbar`
- [app/web/css/orders.css](../../app/web/css/orders.css) — `.tint-printify`, `.ord-track`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `statusText()`, `trackChips()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `ib()`, `fadeImages()`, `slide()`, `flip()`, `reducedMotion()`
- [app/web/js/icons.js](../../app/web/js/icons.js) — `icon()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `smoothWheel()`

## Related

- [Interface (structure)](../architecture/frontend.md) · [Working with the owner](working-with-owner.md) · [Decisions](../decisions.md)
