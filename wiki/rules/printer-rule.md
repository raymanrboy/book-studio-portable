---
title: The printer rule — Printify or Gelato
type: rule
updated: 2026-10-28
code:
  - app/studio/orders.py
  - app/studio/reconcile.py
---
# The printer rule

> **Since 1 October 2026 every book → Gelato, 28 or 30 pages** (the owner, 29.09.2026: "from 1 October I move only
> to Gelato, on my own account"). The earlier rule (a US hardcover → Printify, 24 pages) is still in the code, behind
> `printify.retired()`, and described at the bottom.

## Only Gelato

- `printing()` carries `gelatoOnly` (= `printify.retired()`) and only Gelato's page counts; `plan_for()` then gives
  a hardcover — US too — `provider: "gelato"`, `hardcover_8x8`, no `choice`. The queue's chip is Gelato.
- **The big hardcover, 11×11** (since 2026-10-28, the owner's Gelato template «Hardcover 11x11»): a hardcover whose
  **chosen format variation** says `11.11`, `11x11`, `11" × 11"` or `28 × 28 cm` (`reconcile.LARGE`, `is_large()`) →
  `hardcover_11x11`. Only the format fields count (`chosen_format_text()`: a name with cover / size / format, or a value
  with hardcover / softcover) — never the listing's title (it may list every size) and never the buyer's own words (a
  dedication «born on 11.11»): an 8×8 must never be printed as an 11×11; the Order Creator still lets the owner switch the format. Never Printify's (`choice` only on the 8×8).
  The card's tip names the format: «Hardcover 11×11 · США → Gelato · 28 або 30 стор.» (`planText()`); the queue's
  line says «Hardcover 11×11 книга» (`cover_label()`).
- **A book whose cover type couldn't be read** goes to Gelato too (`format: None`): no Printify/Gelato switch in the
  card; its format is picked in the Order Creator (the header's tip: «Тип обкладинки не визначено → Gelato · 28 або
  30 стор. Формат — в Order Creator»).
- `_files`: `provider: "printify"` is refused; a card opened before 1 October that still sends `"files"` gets
  Gelato's lengths (24 pages → "Потрібно 28 або 30 сторінок").
- Printify itself only reads — [integrations/printify.md](../integrations/printify.md).

## The retired rule (still in the code behind `printify.retired()`)

Before 1 October 2026 a US hardcover went to Printify (24 pages) and every other book to Gelato (28 or 30); for a few weeks the
downloaded files decided a hardcover's printer (24 → Printify, 28/30 → Gelato). The plan then carried `choice`
(`{"printify": [24], "gelato": [28, 30]}`), the card sent `provider: "files"` and `provider_by_pages()` answered with the printer.
Going back would be a small code change — remove the `gelatoOnly` branch in `plan_for()`; there is no Settings switch. Why it
was dropped: the owner moves to his own Gelato account only ([decisions](../decisions-2026-09.md)).

## Formats today

| Order | Printer | Pages | Gelato format |
|---|---|---|---|
| Hardcover | Gelato | 28 / 30 | `hardcover_8x8` |
| Hardcover 11×11 (the chosen variation, see above) | Gelato | 28 / 30 | `hardcover_11x11` |
| Softcover 5.5×5.5 (in the fields — `5" × 5"`, how Etsy labels it for this owner, or "5.5", "5,5", "14 × 14") | Gelato | 28 / 30 | `softcover_5x5` |
| Softcover | Gelato | 28 / 30 | `softcover_8x8` |
| The cover type couldn't be read | Gelato, format picked in the Order Creator | 28 / 30 | — |

The downloaded files decide the length (28 or 30); whether Gelato prints 28 pages in that format is decided by its catalog
([integrations/gelato.md](../integrations/gelato.md)). `plan.pages` is a list: `[28, 30]` (`page_options()`).

## How the cover type is decided

`binding_of()` takes the label from `cover_label()`: first the buyer's variations (hardcover / hard
cover / hardback / тверд…, softcover / soft cover / paperback / м'як…), then the SKU (`hard`, `-hc`,
`soft`, `-sc`, `pb`…), then the product's title. Mixed or unknown → `None` → the owner picks the
printer.

The country comes from `country_iso` in the shipping address on the Etsy receipt.

## Where in the code

- [app/studio/orders.py](../../app/studio/orders.py) — `printing()` (`gelatoOnly`), `plan_for()` (`choice`), `provider_by_pages()`, `binding_of()`, `page_options()`, `PRINTIFY_PAGES`, `_SMALL`, `_files()`
- [app/studio/creator/printfolder.py](../../app/studio/creator/printfolder.py) — `gelato_page_options()`
- [app/studio/reconcile.py](../../app/studio/reconcile.py) — `cover_label()`, `LARGE`, `chosen_format_text()`, `is_large()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `planText()` (the explanation "Hardcover · US → Printify · 24 pages", "… → usually Printify. The files decide…"), `pagesText()`
- [app/web/js/pages/order-card.js](../../app/web/js/pages/order-card.js) — `renderPlan()` (the switch, when the type is unknown), `byFiles()`, `providerOf()`, `arrange()` (`decided`)
- Test: [app/tests/test_orders.py](../../app/tests/test_orders.py) (`PrinterRule`, `GelatoOnly`, `GelatoLength.test_24_pages_of_a_hardcover_go_to_printify`)

## Related

- [Orders](../features/orders.md) · [Printify](../integrations/printify.md) · [Gelato](../integrations/gelato.md) · [Recipes](../recipes.md)
