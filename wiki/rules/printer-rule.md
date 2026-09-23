---
title: The printer rule — Printify or Gelato
type: rule
updated: 2026-09-18
code:
  - app/studio/orders.py
  - app/studio/reconcile.py
---
# The printer rule

> **A hardcover shipping to the US → Printify, 24 pages. Everything else → Gelato, 28 or 30 pages.**

| Order | Printer | Pages | Gelato format |
|---|---|---|---|
| Hardcover, US | Printify | 24 | — |
| Hardcover, any other country | Gelato | 28 / 30 | `hardcover_8x8` |
| Softcover 5.5×5.5 (in the fields — `5" × 5"`, how Etsy labels it for this owner, or "5.5", "5,5", "14 × 14"), anywhere | Gelato | 28 / 30 | `softcover_5x5` |
| Softcover, anywhere | Gelato | 28 / 30 | `softcover_8x8` |
| The cover type couldn't be read | the owner decides (a switch in the card) | 24 / 28–30 | — |

For Gelato, the downloaded files decide the length (28 or 30), and whether Gelato prints 28 pages in
that format is decided by its catalog ([integrations/gelato.md](../integrations/gelato.md)). In the
server's response, `plan.pages` is a list: `[24]` or `[28, 30]` (`page_options()`).

## Why it's this way (in the owner's words)

- Printify is fast and reliable in the US, and its hardcovers are good; its softcovers are poor.
- Gelato, for some reason, is slow with hardcovers in the US, but on-time and good for other countries
  and for softcovers.
- The page count is just a product type: Printify only makes 24 pages, Gelato makes 30, and since
  2026-09-17 also 28 (without one spread), when the format allows it.

## How the cover type is decided

`binding_of()` takes the label from `cover_label()`: first the buyer's variations (hardcover / hard
cover / hardback / тверд…, softcover / soft cover / paperback / м'як…), then the SKU (`hard`, `-hc`,
`soft`, `-sc`, `pb`…), then the product's title. Mixed or unknown → `None` → the owner picks the
printer.

The country comes from `country_iso` in the shipping address on the Etsy receipt.

## Open question

The rule matches 51 of the last 54 orders. Exceptions: 2 softcovers in the US and 1 hardcover to Canada
were printed in Printify. Whether these are deliberate exceptions, or the rule needs to be broader — see
[open-questions.md](../plans/open-questions.md).

## Where in the code

- [app/studio/orders.py](../../app/studio/orders.py) — `plan_for()`, `binding_of()`, `page_options()`, `PRINTIFY_PAGES`, `_SMALL`
- [app/studio/creator.py](../../app/studio/creator.py) — `gelato_page_options()`
- [app/studio/reconcile.py](../../app/studio/reconcile.py) — `cover_label()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `planText()` (the explanation "Hardcover · US → Printify · 24 pages", "… → Gelato · 28 or 30 pages"), `pagesText()`
- [app/web/js/pages/orders.js](../../app/web/js/pages/orders.js) — `renderPlan()` (the switch, when the type is unknown)
- Test: [app/tests/test_orders.py](../../app/tests/test_orders.py) (`PrinterRule`)

## Related

- [Orders](../features/orders.md) · [Printify](../integrations/printify.md) · [Gelato](../integrations/gelato.md) · [Recipes](../recipes.md)
