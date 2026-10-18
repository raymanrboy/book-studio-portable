---
title: Canva — book templates
type: integration
updated: 2026-10-18
code: []
---
# Canva

> The program doesn't work with Canva through an API: a book's passport only keeps a **link to the
> template** (`canvaUrl`), and the order card opens it with a button. Filling a new book's template — the pictures, the
> sphere and the text — is done by the separate Chrome extension ([Canva extension](../features/canva-extension.md), 2026-10-08).

## How the owner works in Canva

1. Every book has **one template**: a cover + 30 pages. Placeholders `{Name}` (the child's name) sit
   throughout the text; the owner adds "from whom" at the end of the dedication by hand.
2. A **copy** of the template is made for each order; the name is filled in with find-and-replace
   (Ctrl+F). If the name got replaced in the dedication, it almost certainly got replaced everywhere
   else too.
3. Dedication: if the buyer didn't write their own (the field says `DEFAULT`), the standard one stays.
   "With love, …" at the start of the "from whom" field is removed by hand — a duplicate is visible
   right away.
4. Downloading — PNG (a ZIP). **For Printify (the US)**, it's not the first 24 pages that get
   downloaded, but **specific** ones: exactly 3 spreads (6 pages) are dropped out of 30 — different ones
   for each book, whichever work least well. **For Gelato** — all 30, or 28 (without one spread, the
   owner's choice); the program figures out which version to print from the file count
   ([integrations/gelato.md](gelato.md)).
5. Some templates are already the right quality; some pages get run through **Upscayl** after Canva (the
   program ignores the `_upscayl…` tail in file names).
6. The ZIP gets dropped into the order card — then [laying out the pages](../rules/file-naming.md).

This is the riskiest manual step, which is why the card keeps all the buyer's data close by and lets it
be copied instead of retyped ([decisions.md](../decisions.md)).

**Since 2026-10-18 the Canva extension does three things of an order** ([canva-extension](../features/canva-extension.md)): makes the
template's copy named «<receipt> - <child>», deletes the copy's first page, and the card takes the ZIP from Downloads by itself. The name
in the pages, the dedication, the cover and the download press stay the owner's.

**A demo book for the listing** (a new book in the shop): the same template with a sample name on the
cover ("Oliver") and a literal `{Name}` in the pages, downloaded as a ZIP; its cover and chosen spreads
go into Photoshop mockups — a Photoshop script fills the templates ([mockups](../features/mockups.md)).

## Where in the code

- The link in a book: `canvaUrl` in [features/library.md](../features/library.md) (the `canvaDialog()`
  dialog in the passport).
- The button in the order card: `renderLeft()` in [features/orders.md](../features/orders.md).
- Opens through the server, in the regular browser — `openExternal()` ([frontend](../architecture/frontend.md)).

## Related

- [The order-to-print path](../flows/order-to-print.md) · [Text check](../features/text-check.md)
