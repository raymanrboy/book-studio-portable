---
title: The big cleanup — every finding of the 2026-09-26 code study, fixed (plan)
type: plan
updated: 2026-09-27
code: []
---
# The big cleanup (plan and progress)

> **Agreed on 2026-09-26.** The owner, after the study: "fix everything you found — I need a flawless app;
> the wiki and GitHub up to date, and above all flawless code without errors". Branch `cleanup`, merged into
> `main` after every phase that passes the tests and the wiki check. The study's report (7 parallel audits:
> Orders pages; library, mockups and Workshop; the text check; orders and money; the Order Creator and the
> printers; the shell and CSS; speed and tests) was published to the owner as a private page; this page
> keeps what is to be done and what is done.

**The study's verdict.** The code is healthy: almost no copy-paste, little dead code, 324 tests pass. The
problem is shape — six or seven big files doing 5–7 jobs each, and the facts about print orders and money
worked out in 3–4 places. The server is already fast (1–27 ms per request, 0.3 s to start); the real waits
are where big pictures are decoded and where the text check's model loads.

**The owner's decisions for this plan (2026-09-26)**: "fix everything you found" — the receipt-matching
order (receipt numbers before names) as recommended; the accounting items deferred on 2026-09-23 are fixed
now, following the 2026-09-18 decision (only a placed and paid order counts); the order card and the Order
Creator may be restructured (the 2026-09-19 go-ahead). **Not done without him:** anything that writes to
Printify, Gelato or Etsy for real — the Gelato link started beside the PDF build needs one real draft, so it
waits.

## Rules for every phase

- Behaviour stays the same unless the item says it changes; every bug fix comes with a test.
- Tests, `python app/tools/wiki_check.py`, the wiki pages of the touched code, a log entry; the interface
  checked on the preview server (`dev_server.py`), never on the real program.
- One commit per phase (or per large step), pushed; `main` fast-forwarded after the phase.

## Phase 1 — bugs (done 2026-09-26)

Money and safety first:
- [x] `httpc.request`: an error while *reading* a reply (`IncompleteRead`, `ssl.SSLError`) escapes the
  "result unknown" handling → catch `http.client.HTTPException` and `OSError`; an unknown result after a
  create says "don't resend".
- [x] `etsy._oauth_callback`: the page puts query text into HTML unescaped → `html.escape`.
- [x] `creator._gelato_draft`: a failed read-back after the draft exists stops the link and deletes the PDFs →
  hand the link to the registry as soon as the order id is known; steps after an irreversible create never
  fail the send (also Printify's product verify and the Master-after read).
- [x] `creator._printify_draft`: two books — book 2's failed uploads make a retry create book 1 again →
  upload every book's pictures first, then create the products.
- [x] `profit._sync`: a full read can store a receipt twice → `merge_receipts([], fresh)`.

The rest:
- [x] Workshop book page: Esc that closes a dialog also leaves the page (`e.defaultPrevented`).
- [x] Mockups: «Готово · N картинок» in the window title is overwritten at once → app.js alone writes the title.
- [x] `generate._catch`: Stop / delete / another row while a picture is placed gets undone → re-check the
  active wait after placing.
- [x] `pictures`: `variant` from the request goes into paths unchecked → validate once at the top.
- [x] `rows._agent_key` ignores `agent/_work/` → hash all of `agent/`.
- [x] `pictures._save`: a page open in a viewer leaves `N.png.tmp` → one write helper with cleanup and retries.
- [x] `int(req.param("w"))` unguarded in 4 places → `Request.int_param()`.
- [x] Library: deleting a book while its folder import runs leaves a broken folder → refuse while the job runs.
- [x] Order Creator: two books' progress lands in book 1's badge → a badge per book.
- [x] Order Creator: Enter during a send starts it again and re-enables «Створити» → a running guard.
- [x] Order Creator: `validateSoon` not cancelled on leaving the page.
- [x] Passport: a ZIP or folder dropped on a picture slot is refused → it opens the import.
- [x] Text check: a broken model answer is cached → cache only answers that parse; no retry after a timeout.
- [x] Profit page: unguarded `localStorage` parse; the sync poll outlives the page.
- [x] Dropped folders cleared after 2 hours while a card may still use one → check and fix.

## Phase 2 — orders and money (done 2026-09-26)

- [x] One module for a print order's facts (cost, dead, placed, name, label, tracking), used by matching,
  money, stages and the archive.
- [x] Receipt matching as a rule pipeline: manual → Printify number → Gelato number → Printify name → Gelato
  name (the rule order changes on purpose).
- [x] Money worked out once: a cancelled first order no longer wipes the second's cost; CZK converted, not
  counted as USD; the cover type from the order's own data, not letters of its reference; only placed and
  paid orders count (2026-09-18).
- [x] `profit.py` split (sync, records, stages, the Profit view) — the archive ↔ profit import cycle goes.
- [x] The stage of every receipt worked out once per view; the order card in one pass.
- [x] Dead fields dropped (the buyer's e-mail kept for nothing among them); `plain()` applied once.
- [x] New focused tests for matching and money (today most tests share one fixture).
- [x] The Profit page follows the owner's UI rules (tips, no emoji, Ukrainian labels, no inline styles).

## Phase 3 — speed (done 2026-09-27)

- [x] Text check: the model loads only when a question is really asked (a cached re-check: −4…70 s); the
  model warmed after a page is replaced; answers keyed by the file's content, not its folder.
- [x] Order Creator: a page decoded once — the check makes the previews; a replaced page re-checks only
  itself (4–5 s → ~0.5 s); the archive copies the previews instead of decoding every page again.
- [x] Gelato PDF streamed to the file (≈2 GB less memory, no temporary copies, the same bytes — compared on a
  30-page book); the PDF engine pinned in `requirements.txt`. Printify uploads without five copies of each file in memory.
- [x] Workshop: one read of a book per request, `os.scandir`, the background poll without walking every
  book, the Downloads watcher and F8 started only when needed; the clipboard picture saved faster.
- [x] Library uploads stored outside the library lock; the settings read once per queue load.
- [x] Interface: module preload hints; smoother lightbox, `flip()` and `patch()`; progress bars by transform.

- [ ] **Waits for the owner:** the Gelato link started beside the PDF build (3–8 s per send) — it needs one real
  draft to be checked on, so it isn't done without his yes.

## Phase 4 — no blinking (done 2026-09-27)

- [x] A replaced page reloads only itself (per-file versions), the strip keeps its place.
- [x] Queue and archive search, the Order Creator's structure and step cards, the passport's texts, the text
  check's end, the mockups' templates: redrawn in place (`patch()`), no replayed entrances.

- Not done, on purpose: drawing the queue at once from memory on "back" — the server answers in a few ms now
  (phase 2), so there is nothing to hide.

## Phase 5 — duplicates and dead code

- [ ] Shared order modules (the page viewer's replace/restore, the proof strip, address, badges, one order
  list for the queue and the picker — the `etsy-orders` route goes).
- [ ] Printify and Gelato share one send frame; small duplicates (image suffixes ×5, flatten ×3, "inside
  the folder" ×4) become one each.
- [ ] Dead code (~110 lines), one-time migrations, unused icons and exports; CSS repeats (the image fade ×15),
  needless `!important`.
- [ ] Tests: one fake model for the text check, one set of fixtures instead of seven PNG helpers.

## Phase 6 — big files cut by job

- [ ] `textcheck.py` → a package (checked with `textcheck_replay.py --all`: the same output).
- [ ] `creator.py` → routes, the print folder, the shared send, Printify, Gelato, the photobook PDF.
- [ ] `library.py` → the model and its files; the agent guide as its own Markdown file.
- [ ] Interface pages (order card, Order Creator, passport, settings, mockups, Workshop book, Profit) →
  state + templates + actions; CSS by section; `dev_server.py` by job.

## Left as it is (on purpose)

The printers' guards, "result unknown", the send journal and the folder lock; the text check's calibrated
rules; the archive and order-stage rules; navigation, kept pages and live polling; `core.write_json`; the
Photoshop script; the Profit Calculator's rounding; start-up imports and static-file serving.

## Related

- [Open questions and technical debt](open-questions.md) · [Decisions](../decisions.md) ·
  [Code map](../code-map.md)
