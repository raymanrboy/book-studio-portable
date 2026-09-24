---
title: The interface the owner wants
type: owner
updated: 2026-09-24
code:
  - app/web/css/app.css
---
# The interface the owner wants

> Minimal, icon-driven, smooth (60 fps), tidy down to the pixel. No unnecessary explanations — only what
> a given action needs. Gathered from his notes, 2026-09-14 to 16.

## General

- **A button never ignores a press in silence** (2026-09-23): a greyed-out button that does nothing on a
  click reads as "the program doesn't work". Keep it pressable and say what's missing (light up the empty
  fields), and show what's being waited for (e.g. a Windows dialog).
- **A long job says when it's over** (2026-09-23, "is there any message that it's finished?"): the owner
  watches another program meanwhile (Photoshop), so the result card alone isn't enough — the window's
  taskbar button flashes, Windows plays its sound and the title says how it ended. Show the results
  themselves (the saved pictures), not just a count.
- **Two modes, two inks** (2026-09-24): Orders are orange, "like Etsy and Claude"; Listings wear the cyan the
  whole program had before (the owner's swap; magenta for a few hours first); the brand icon at the top of the rail switches them ([modes](../features/modes.md)).
- **The Workshop's rows are of moderate width**, not the full window (2026-09-24): the prompt, the 2:1 frame
  and the text one under another, the frames empty until the pictures are generated
  ([workshop](../features/workshop.md)).
- **A tool of the family looks like Book Studio** (2026-09-23, «Мокапи»: "exactly like Book Studio"):
  numbered step cards, the path field with the folder-and-magnifier button, status badges, the structure
  of the book on the right — the same parts, not look-alikes.
- **A tooltip should be fully visible** — a long one wraps to a second line instead of getting cut off
  (2026-09-19).
- **Icons instead of text buttons** for secondary actions; their meaning lives in the tooltip (`ib()`).
  One icon — one meaning.
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
  color (2026-09-18).
- Dark theme by default; the image viewer follows the program's theme too.
- Service colors: **Printify — lime green**, **Gelato — blue**, Etsy — orange, Canva — purple.

## Specific requirements

- The Order Creator and every form **open empty** — no cached folders, addresses, or drafts.
  **Exception (2026-09-18):** work on a new order — the card and the Order Creator come back exactly as
  they were left (even a successful-creation page), until the order leaves "New".
- **No clickable links to Etsy** (the listing chip is plain text).
- **Canva — a button**, not the full link.
- In Printify/Gelato blocks — only the service name, no technical detail.
- Settings — kept minimal: keys and templates (Printify — a 24-page book; Gelato — three formats, 28 or
  30 pages).
- Anywhere a folder is picked, a **folder or ZIP can be dragged in** without changing how the field looks.
- The order card: **data on the right (sticky), work on the left**; proofing is large; the note's text
  is large and bold; the child's name in personalization is bigger, but not huge; the cover-format field
  has no copy button.
- The page filmstrip is smooth, and reaches all the way to the last spread.
- **Text on one line aligns to the text baseline**, not to the top edge of the blocks; digits shouldn't
  "jump" because of a different font (the "Gelato · 28 or 30 pages" chip, 2026-09-17).
- **Statuses in plain language**, not raw API text: "In transit", not `in_transit` (English is fine,
  2026-09-17).
- **"Back" returns to where it came from**: from the card — to the same queue tab ("Sent", etc.), with
  the same search and scroll position, not to the start (2026-09-19: "it feels inconsistent" otherwise).
- The queue: the child's name — bold, in the gray row after the time; the printer status — on the right;
  the tracking number — in a block colored by printer, the carrier and the number both colored, but kept
  apart (2026-09-17).
- **Equal contrast** for colored text in the same place: the printer's name, the carrier, and the number
  — all one soft shade (the owner picked the softest option, 2026-09-17).
- **Numbers copy on click** — the tracking number and the Etsy order number (without "#").
- The order card: the printer status sits next to the recipient's name, centered (2026-09-17).
- In a book's passport: no notes, no illustration filters.
- The library: "+" sits in the same row as search and the icons.

## Where in the code

- [app/web/css/app.css](../../app/web/css/app.css) — the color tokens and `.lib-toolbar`, `.tint-printify`, `.chip-mono`, `.ord-track`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `statusText()`, `trackChips()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `ib()`, `fadeImages()`, `slide()`, `flip()`, `reducedMotion()`
- [app/web/js/icons.js](../../app/web/js/icons.js) — `icon()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `smoothWheel()`

## Related

- [Interface (structure)](../architecture/frontend.md) · [Working with the owner](working-with-owner.md) · [Decisions](../decisions.md)
