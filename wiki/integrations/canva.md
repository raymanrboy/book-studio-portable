---
title: Canva — book templates
type: integration
updated: 2026-10-28
code: []
---
# Canva

> The program doesn't work with Canva through an API: a book's passport only keeps a **link to the
> template** (`canvaUrl`), and the order card opens it with a button. The rest is done by the separate Chrome extension
> ([Canva extension](../features/canva-extension.md), which owns every detail of it) and by the owner's hands.

## How the owner works in Canva

1. Every book has **one template**: a cover + 30 pages. Placeholders `{Name}` (the child's name) sit
   throughout the text; the owner adds "from whom" at the end of the dedication by hand.
   A **new** book's template is filled by the extension from the Workshop book's folder (pictures, the sphere and the text).
2. For an order, the card's «Відкрити шаблон у Canva» opens the template and the extension makes the **copy** named
   «<receipt> - <child>» and deletes the copy's first page.
3. The owner replaces the name by find-and-replace (Ctrl+F) — if the name got replaced in the dedication, it almost certainly got replaced
   everywhere else too. Dedication: if the buyer didn't write their own (the field says `DEFAULT`), the standard one stays. "With love, …" at
   the start of the "from whom" field is removed by hand — a duplicate is visible right away.
4. Downloading — PNG (a ZIP), the owner's own press; the order card takes that book's ZIP from Downloads by itself. **For Gelato** — all 30
   pages, or 28 (without one spread, the owner's choice); the program figures out which version to print from the file count
   ([integrations/gelato.md](gelato.md)). (The old Printify route took specific 24 of the 30 pages; Printify is read-only now —
   [printify](printify.md).)
5. Some templates are already the right quality; some pages get run through **Upscayl** after Canva (the
   program ignores the `_upscayl…` tail in file names).
6. The ZIP lands in the order card (dropped, or caught from Downloads) — then [laying out the pages](../rules/file-naming.md).

This is the riskiest manual step, which is why the card keeps all the buyer's data close by and lets it
be copied instead of retyped ([decisions.md](../decisions.md)).

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
