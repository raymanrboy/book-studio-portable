---
title: Known limits and what was not seen live
type: dev
updated: 2026-10-03
code: []
---
# Known limits

> What the program deliberately doesn't do, what its checks can't prove, and what has only been tried against fakes.
> Nothing here is a to-do: each line is how the finished program behaves.

## What the program deliberately doesn't do

- **A receipt's stage comes from one print order.** If one of two books is sent and the other isn't, the receipt is
  already off «Нові»; the «+N in print» chip shows the rest, but there is no «partly sent» stage. For the 10% of orders
  with several books (usually one book for different children) this is right ([order stages](../rules/order-stages.md)).
- **No «receipt → books → print batches» model.** Each book of an order goes through the path separately and they go
  to the printer together as one draft to one address ([orders](../features/orders.md)); a receipt mixing two printers
  is handled by hand.
- **Sends before 2026-09-22 aren't in `profit/print-orders.json`**, so for older receipts accounting sees one print
  order. Accounting counts only sales from 1 October 2026 anyway ([profit](../features/profit.md)).
- **After a successful send each local step can fail on its own** (the journal entry, accounting, the archive); it is a
  warning, the send itself stands ([send journal](../features/send-journal.md)).
- **A book created in Printify without an order doesn't move the receipt.** Printify only reads since 1 October 2026
  ([Printify](../integrations/printify.md)); its code stays in case the owner wants it back.
- **Pages with the buyer's own dedication aren't parsed** — the cases are rare and are settled with the buyer; "With
  love, …" in the «from whom» field isn't removed automatically ([the path to print](../flows/order-to-print.md)).
- **The three spreads that don't fit the 24-page version** (and the one that doesn't fit a 28-page book) are picked by
  hand in Canva; the program only reports which passport spreads a book lacks ([text check](../features/text-check.md)).
- **The window sends the server at most 6 requests at once** (the browser's own limit per host); the first seconds after
  dropping a book's pages queue behind each other.
- **No test clicks through a page in a real browser.** The tests cover the server, the scripts' imports and the Photoshop
  script (run by Node.js against a pretend Photoshop); the interface is checked by hand on the preview server
  ([testing](testing.md), [preview](preview.md)).
- **The `etsy/` folder holds more files than a listing takes** (6 slides, 2 whole-scene mockups, up to 7 photo
  mockups; two of them weigh 16–18 MB). The owner picks which go into the listing; Etsy's current limits were not
  checked from this PC, because Etsy is never opened here ([security](../security.md)).
- **Pasting the next part with Ctrl+V works only in Chrome**; the Workshop's pages are made in Gemini, the photo
  mockups in ChatGPT ([workshop](../features/workshop.md), [photo mockups](../features/photo-mockups.md)).

## Worth watching

- **The text check: the model can loop on a correct page.** Since Ollama 0.35.1, `gemma4` sometimes copies a page's text
  word for word (it matches the passport), then invents «a mistake in the name» and repeats an apology until
  `JUDGE_TOKENS` cuts the answer. The card shows «модель не змогла прочитати сторінку»; ↻ asks again. A known gemma4
  problem with a JSON schema (ollama#15502); it was seen on one page of one book and not in the ~990 pages journaled
  before. If it recurs, the fix is in the program: take the transcript from a cut-off answer and let `diff()` decide
  ([text check](../features/text-check.md#why-this-model-and-this-design)).
- **Drafts could be closed sooner.** Gelato fetches the PDF about a minute after a draft is created, and the program
  waits 15 minutes before letting its temporary link go; the send journal's statistics will show whether that can be
  shorter ([Gelato](../integrations/gelato.md)).

## Tried only against fakes or on made-up data

- **A first real Printify «On hold» order** — not created; that it really waits for «Submit order» and charges nothing
  is unconfirmed. The «Orders in Printify» link (`https://printify.com/app/orders`) hasn't been opened.
- **Dragging from Explorer** (a folder, a ZIP) in a real window — checked with a simulation.
- **How smooth the filmstrip is** in a visible window — checked with simulated frames; the owner is the judge.
- **A live order with several books** — checked with tests and made-up data. The first real one should be checked in
  Printify (one order with two line items) and Gelato (one draft with two products, shipping charged once).
- **A 28-page softcover live** — a test draft covered only a 20×20 hardcover (no offset); the catalog allows 28 for
  softcovers too.
- **The mockups' second script in the real Photoshop** and the taskbar flash — checked against a pretend Photoshop.
- **In Antigravity:** its window and the *Agent Gitignore Access* setting on the owner's PC, a real Gemini download and
  paste, and F8 on real Windows inside Book Studio were not checked by an agent ([workshop](../features/workshop.md)).

## Related

- [Security](../security.md) · [Tests](testing.md) · [Decisions](../decisions.md)
