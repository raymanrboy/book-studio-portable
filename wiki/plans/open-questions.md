---
title: Open questions and technical debt
type: plan
updated: 2026-09-30
code: []
---
# Open questions

## External code audit 2026-09-22 — what remains

The owner's colleague sent over a code audit (17 findings) and interface recommendations. What was
fixed and what was deliberately left alone — [decisions.md](../decisions.md), entry 2026-09-22. Still
to discuss:

- **A receipt's stage is computed from a single print order.** One book is sent, the other isn't — the
  receipt is already off "New". The "+N in print" chip shows this, but doesn't change the stage. Is a
  "partly sent" stage needed?
- **A "receipt → books → print batches" model** (the interface document's main recommendation).
  Deliberately deferred: for the 10% of orders with several books, where it's usually the same book for
  different children, the current model is correct. Revisit if mixed receipts (two printers) become
  noticeably more common.
- **Sends before 2026-09-22 aren't recorded** in `profit/print-orders.json`, so for old receipts the
  accounting still sees one print order, as before.
- **Fully finishing the local work after a successful send** (the journal entry, the accounting, the
  archive) — right now each step can fail on its own, and it's only a warning. The audit recommends
  showing a list of steps.
- **No automated interface tests** (no test brings up the HTTP server and clicks through a page) — every
  new defect the audit found lived exactly at these seams.

## Questions for the owner

- **(2026-09-30, the wiki review) The `etsy/` folder and Etsy's own limits.** A book's `etsy/` now gathers 6 slides,
  2 whole-scene mockups and up to 7 photo mockups — 15 files, more than a listing may hold, and Cover & Open 1 / All &
  Open 1 weigh 16–18 MB each. Which of them go into the listing, in what order, and does Etsy take files that big?
  (Etsy's current limits were not checked from this PC — no Etsy here.) Could be a numbered order in `etsy/`.
- **(2026-09-30) Which generator for which step?** The Workshop's pages are made in Gemini, book 25's photo mockups in
  ChatGPT. Ctrl+V → the next part counts only in **Chrome** — is ChatGPT open in Chrome too?

- **Exceptions to the printer rule.** The rule matches 51 of the last 54 orders; 2 softcovers in the US
  and 1 hardcover to Canada were printed in Printify. Deliberate exceptions (then the rule stays as is)
  or does the rule need to be broader? ([rules/printer-rule.md](../rules/printer-rule.md))

- **Listing mockups** (2026-09-23): output file names; the back/spine/rim crop rule on the first real
  book; a "save the open ones" script; Photoshop's "run this script?" dialog — one click per batch, or
  the owner turns it off himself — details in [listing-mockups.md](listing-mockups.md#open-questions).

## Not tested live

- **A first real Printify "On hold" order** — not yet created; check that it really is waiting for
  "Submit order" and nothing has been charged.
- **The "Orders in Printify" link** (`https://printify.com/app/orders`) — not checked.
- **Dragging from Explorer** (a folder, a ZIP) in a real window — checked only with a simulation.
- **How smooth the filmstrip is** in a visible window — checked with simulated frames; the owner is the
  judge.
- **A live order with several books** (since 2026-09-20): checked only with simulated tests and on
  made-up data. The first real order like this is worth doing carefully — and confirming that in
  Printify it's **one** order with two line items (not two), and in Gelato — one draft with two
  products, with shipping charged once.
- **A 28-page softcover live** — a test draft checked only a 20×20 hardcover (no offset, 2026-09-17);
  the catalog allows 28 for softcovers too. The first real 28-page book hasn't been printed yet.
- **Drafts might be closeable sooner**: Gelato fetches the PDF itself, about a minute after the draft is
  created; the 15-minute wait is probably more than needed — decide once the send journal has built up
  some statistics.

## Code review 2026-09-19 (the owner: "stopped feeling as smooth")

Analysis with no code changes; measurements on a copy of the data. **The server isn't at fault**: the
longest response — the order card, 34 ms (`/api/orders` 25 ms, `/api/app` 3 ms, the archive 12 ms); no
event-listener leaks; no errors in the real program's log. The owner's text check wasn't running today.

**Likely causes (in order):**
1. **The model occupies the graphics card** — during a check, 90–100% and 9.2 of 12 GB, and for another
   5 min after (`KEEP_ALIVE`); the Book Studio window is drawn by the same card. On 2026-09-19, the
   model held memory until ~21:46 after the agent's tests, and the owner started the program at 21:43.
2. **New-order cards all stay in memory**, even doing nothing (`keep.js`, `keep()` in the card).
   *Clarified after checking:* the browser itself frees the unpacked pictures of hidden cards, so each
   one only costs a few MB — a safeguard, not the main cause.
3. **Right after dropping files**, the server unpacks the 4000-pixel pages into thumbnails (3 at a
   time), and the window sends the program no more than 6 requests at once — the rest wait. The text
   check, in those same seconds, asks for those same previews plus a large cover (2600 px) on its own.

**Findings in the text check (2026-09-19):**
- closing the card, new files, or another book don't stop the check — the model keeps working for
  nothing, and the card keeps polling its state;
- "Not an error" redraws the whole list — the rows "slide in" again (flicker);
- `JUDGE_TOKENS` = 700 can cut off the answer on a long page with several problems;
- Ollama turned off: on Windows every connection attempt waits 2 s (measured) — the block in Settings
  shows up late;
- `check_book()` — 168 lines; uses the private `creator._files_by_lower`, `library._lock`.

**The rest of the program:**
- the preview cache `data/cache/thumbs` is never cleared: 152 MB / 1527 files after 5 days, including
  previews of temporary copies that no longer exist;
- zooming a spread in the viewer (`compose_spread()`, height 2400) unpacks both full pages every time —
  there's no ready-made larger preview at size 2400;
- `images._key_locks` grows without bound (one lock per preview per session);
- minor: leaving a card walks all of its elements for scrolling's sake (`swap()` in app.js);
  `smoothWheel()` reads `scrollLeft` right after writing it; unused imports (`HTTPStatus` in server.py,
  `json` in dev_server.py) and exports (`onInfo`, `perFrame`).

**Code quality (for discussion, not touched):** the longest functions — `reconcile.match()` 196 lines,
`creator._printify_draft()` 171, `textcheck.check_book()` 168, `creator._gelato_draft()` 111,
`outcomes.apply()` 107; `creator.py` (1100 lines) mixes file checking, Printify, Gelato, PDF, and
drag-and-drop; the order card is one function ~430 lines long; recognizing the buyer's fields (name /
dedication / "from whom") is written three times (order-bits.js, `guess_child_name()` — in `wording.py` since
2026-09-27, `textcheck.personalization()`); no automated interface tests.

**Fixed the same day** ([decisions](../decisions.md)): the graphics card is freed right after a check;
a check stops once it's no longer needed; idle cards — no more than three; the preview cache is cleared
(21 days); preview locks no longer accumulate; the spread zoom uses the 2600 preview; the cover for the
model comes from the 1400 preview; `JUDGE_TOKENS` = 1000; the "is Ollama alive" check — 1 s, the
Settings block appears right away; the problem list no longer flickers; `check_book()` split into
parts, the private `creator`/`library` fields are no longer needed; unused imports removed. **Still
open** — "Code quality" above (for discussion) and the window's 6-concurrent-request limit (needs a
different server).

## Technical debt

- ~~`pages/profit.js` isn't wired into the routes~~ — in the rail since 2026-09-29.
- ~~**Profit counts only sales from 1 October 2026**~~ — built 2026-09-29 (`profit.ACCOUNTING_FROM`).
- ~~**The owner's own Gelato account**~~ — the smooth switch built 2026-09-29
  ([gelato](../integrations/gelato.md)); the key is now replaced only through «Перейти на новий акаунт Gelato».
- **Printify's code stays** after 1 October (read-only): the sending, the Master, the reprint. When every Printify
  order is delivered and its archive days are over, it could be cut down to the reading — only with the owner's
  word (he may want Printify back).
- ~~**Accounting — before October 1**~~ (deferred by the owner on 2026-09-23) — **fixed on 2026-09-26** in the
  [big cleanup](cleanup.md): one money step, a cancelled first order keeps the second one's cost, every currency
  converted, the cover from the buyer's choice, only placed and paid orders counted
  ([rules/reconciliation.md](../rules/reconciliation.md)).
- ~~**The euro's rate**~~ — closed on 2026-09-27: nothing to change. The Gelato account holds 568 orders, most of
  them not the owner's (531 in euros, 5 in crowns); of his 30 sales printed at Gelato 28 are billed in dollars
  (the owner: "all my orders are paid in dollars") and 2 — both on 5 August, before the account's first dollar
  order on 12 August — in euros (€35.85; at 1.085 or the ECB's 1.1403 the difference is about $2). The rates stay
  as a safety net.

## Related

- [Plans](roadmap.md) · [Decisions](../decisions.md)
