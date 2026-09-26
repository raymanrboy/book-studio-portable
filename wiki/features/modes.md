---
title: Two modes — Orders and Listings
type: feature
updated: 2026-09-26
code:
  - app/web/js/app.js
---
# Two modes: Orders and Listings

> Since 2026-09-24 Book Studio is two programs in one window (the owner: "working with orders, and creating
> listings … like another program, separated from everything"). **Orders** — the queue, the library, the
> Order Creator, the archive, Settings, in orange ("like Etsy and Claude"). **Listings** — the
> [Workshop](workshop.md) and the [Mockups](mockups.md), in cyan (the whole program's colour until then). A click on the brand icon at the top of the rail switches. The
> agreements — [plans/listings-mode.md](../plans/listings-mode.md).

## How the owner uses it

- **The brand icon is the switch**: a click (or **Alt+0**) goes to the other mode; its tooltip says where —
  «Перейти до лістингів» / «Перейти до замовлень». It lifts a little under the mouse.
- **Orders** — **orange**, "like Etsy and Claude" (the owner, 2026-09-24): a deeper shade than Etsy's own, so
  white text on a button stays readable; the spread icon on the dark square, five rail items (Alt+1…5).
- **Listings** — **cyan**, the colour the whole program had before (the owner swapped them the same day; for a
  few hours it was magenta): the icon becomes an Etsy listing's tag on a cyan square, two rail items —
  **Майстерня** (Alt+1) and **Мокапи** (Alt+2); the theme button stays at the bottom. Every button, focus ring, switch and chip in the accent colour follows the mode; the window's title
  says «Book Studio · Лістинги».
- **The switch is animated** (transform/opacity only): one mode's rail slides up and fades, the other's slides
  in, the brand icon turns over into its new ink, the page cross-fades like any page change. "Minimum
  animations" turns it off like every other animation.
- **Each mode remembers where the owner was** until a restart: back from the listings to the order card left
  (while it's kept — [keep.js](../architecture/frontend.md)), else the queue; back to the listings — the same
  Workshop book or the Mockups. **Book Studio always starts in Orders** (the owner's answer).
- **A mockups run is never lost**: the Mockups page is kept when the owner leaves it; while Photoshop works
  and the owner is in the orders, a small cyan dot breathes on the brand icon (and on «Мокапи» when he is
  elsewhere in the listings); when it ends, a notice says «Мокапи: готово · 7 картинок».
- **A picture the Workshop waits for is never missed** (since 2026-09-26): while the generation mode waits and the
  owner is elsewhere, the same dot shows (on the brand icon in the orders, on «Майстерня» in the listings), the
  window's title says what is awaited («● Розворот 10–11 · 6 з 16 — Book Studio», seen on the taskbar while he is in
  Gemini), and a notice comes for every picture caught.

## How it works

- `MODES` in `app.js` — per mode: the title, the brand icon, the tooltip, the rail items. Every route in
  `ROUTES` names its mode, so **the address alone says which mode is on screen** (back/forward just work, a
  reload stays where it was).
- `navigate()` → `swap()`: when the page's mode differs from the one on screen, `buildNav()` rebuilds the rail,
  sets `html[data-mode]` (the CSS tokens `--accent*`: orange by default, cyan for `[data-mode="listings"]`, light
  and dark; contrast with the text on them 4.8–7.0) and the title; the transition gets the class `vt-mode` (its own keyframes `vt-rail-out`, `vt-rail-in`,
  `vt-flip-out`, `vt-flip-in`; the brand gets its own `view-transition-name` only then).
- `last` keeps each mode's last address; `entryOf()` is where a mode is entered (an order card only while it's
  kept — `ordersTarget()` stays for the «Замовлення» item itself).
- The dot: the Mockups page sends the `bs:busy` event when a run starts and ends, `workshop-live.js` — while a
  picture is awaited (with what, for the title); `paintBusy()` shows the dots and writes the title (`BUSY_NAV`).

## Where in the code

- [app/web/js/app.js](../../app/web/js/app.js) — `MODES`, `HOME`, `ROUTES`, `buildSidebar()`, `buildNav()`, `entryOf()`, `switchMode()`, `paintBusy()`, `placeNavPill()`, `navigate()`
- [app/web/css/app.css](../../app/web/css/app.css) — `[data-mode="listings"]` tokens, `.brand-mark`, `.brand-busy`, `.vt-mode`
- [app/web/js/icons.js](../../app/web/js/icons.js) — `listing`, `workshop`, `prompt`
- [app/web/js/pages/mockups.js](../../app/web/js/pages/mockups.js) — `keep`, `revive`, the `bs:busy` event

## Related

- [Interface](../architecture/frontend.md) · [Workshop](workshop.md) · [Mockups](mockups.md) ·
  [The interface the owner wants](../owner/ui-principles.md) · [The plan](../plans/listings-mode.md)
