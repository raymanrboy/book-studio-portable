---
title: Recipes — how to change common things
type: recipe
updated: 2026-10-03
code: []
---
# Recipes

> Exactly where to change code for common tasks, and what not to forget. After each one — tests,
> `wiki_check.py`, updated pages, and an entry in the log ([rules](dev/wiki-rules.md)).

## Change the printer rule
- [app/studio/orders.py](../app/studio/orders.py) — `plan_for()` (and `binding_of()`, if cover
  recognition changes)
- Test `PrinterRule` in [app/tests/test_orders.py](../app/tests/test_orders.py).
- The explanation in the interface — [app/web/js/order-bits.js](../app/web/js/order-bits.js) `planText()`.
- Wiki: [rules/printer-rule.md](rules/printer-rule.md), [decisions.md](decisions.md).

## Add a Gelato format (a new size)
- [app/studio/core.py](../app/studio/core.py) — `DEFAULT_SETTINGS` (`gelato.formats`: `label`,
  `productUid`); saved settings are merged with the defaults, so the new key appears on its own.
- [app/studio/orders.py](../app/studio/orders.py) — `plan_for()`: when to pick the format.
- The Order Creator shows formats from status on its own (`formatCard()`); how many pages the new format
  prints, the program will ask Gelato's catalog itself.

## A different Gelato book length (besides 28 and 30)
- [app/studio/core.py](../app/studio/core.py) — `DEFAULT_SETTINGS` `gelato.pageCounts`. But `_merge()`
  doesn't change a list already saved in the owner's `settings.json` — a migration in `_upgrade()` is
  needed.
- Check with a test draft with numbered pages (Page 0 blank, then 1…N).
- The rest is computed from this list: [app/studio/creator/printfolder.py](../app/studio/creator/printfolder.py)
  `gelato_page_options()`, `_gelato_page_count()`; [app/studio/orders.py](../app/studio/orders.py)
  `page_options()`.
- Wiki: [integrations/gelato.md](integrations/gelato.md), [rules/printer-rule.md](rules/printer-rule.md),
  [rules/book-structure.md](rules/book-structure.md).

## The "Profit" page's first day
- Shown since 2026-09-29 (`MODES.orders.nav`, `#/profit` in [app/web/js/app.js](../app/web/js/app.js)).
- The day bookkeeping starts — `ACCOUNTING_FROM` in [app/studio/profit.py](../app/studio/profit.py); the test
  `BookkeepingStart` in `test_profit.py`.
- Wiki: [features/profit.md](features/profit.md).

## Printify back for new books
- `READ_ONLY_FROM` / `retired()` in [app/studio/printify.py](../app/studio/printify.py) (a later date, or `date.max`);
  everything else — the printer rule, the Order Creator's switch, the archive's reprint — follows `retired()`.
- Wiki: [integrations/printify.md](integrations/printify.md), [rules/printer-rule.md](rules/printer-rule.md).

## A new interface page
- File `app/web/js/pages/<name>.js` with `export async function mount(view, params)` → `{ shown?, unmount }`.
- [app/web/js/app.js](../app/web/js/app.js) — `ROUTES` with the page's area (its ink); a place of its own in the rail — `PLACES`. A page that serves an object (an order, a book) gives its controller a navFor() naming that place.
- A tool that also works on its own — a line in [places.js](../app/web/js/places.js) `TOOLS` (it shows in «Інструменти» and the search).
- Styles — in [app/web/css/](../app/web/css/app.css): `app.css` (the tokens and the shared parts) or the section's
  own file (`library.css`, `orders.css`, `profit.css`, `listings.css`); colors from tokens only.
- Wiki: a new page under `features/`, a row in [code-map.md](code-map.md) and `index.md`.

## A new server route
- `@route("METHOD", r"/api/...")` in the right module ([app/studio/server.py](../app/studio/server.py)
  `route()`).
- A new module — add it to the import in [app/studio/main.py](../app/studio/main.py) `main()`, or the
  route won't register.
- A long-running action — through `jobs.start()`, `runJob()` in the interface.
- Wiki: a row in [architecture/api-routes.md](architecture/api-routes.md) (the check requires it).

## A new icon
- [app/web/js/icons.js](../app/web/js/icons.js) — add a path to the `P` map (24×24 grid, 1.6 stroke);
  `icon()` will return it.
- Rule: one icon — one meaning; don't reuse an existing one for something else.

## A new order stage
- [app/studio/stages.py](../app/studio/stages.py) — `order_stage()`
- [app/web/js/order-bits.js](../app/web/js/order-bits.js) — `STAGES`, `STAGE_EMPTY`, `STAGE_LABEL` (the card's and the archive's stage chip)
- Test `PickerStages` in [app/tests/test_states.py](../app/tests/test_states.py); wiki
  [rules/order-stages.md](rules/order-stages.md).

## What to show in the proof's note
- [app/web/js/pages/order-card.js](../app/web/js/pages/order-card.js) — `proofCard()` (the `notes` filter),
  `isFormatField()`, `isNameField()`; sizes — `.proof-name`, `.proof-note` in orders.css.

## Filmstrip thumbnail size
- Change **together**: [app/web/js/order-bits.js](../app/web/js/order-bits.js) `STRIP_THUMB` (the order card's and
  the archive's strip) and
  [app/studio/images.py](../app/studio/images.py) `VIEW_SIDES` (otherwise the file check will prepare the wrong
  size).

## A new service key
- [app/studio/vault.py](../app/studio/vault.py) `SECRET_NAMES`;
  [app/studio/settings_api.py](../app/studio/settings_api.py) `EDITABLE_SECRETS`;
  [app/web/js/pages/settings.js](../app/web/js/pages/settings.js) `SECRET_LABELS`.

## A new setting
- [app/studio/core.py](../app/studio/core.py) `DEFAULT_SETTINGS` → a route in
  [app/studio/settings_api.py](../app/studio/settings_api.py) → a field in
  [app/web/js/pages/settings.js](../app/web/js/pages/settings.js) `mount()`.
- Remember: the owner wants Settings kept minimal ([owner/ui-principles.md](owner/ui-principles.md)).

## Allow a new Printify or Gelato call
- **Only with the owner's direct permission** and a security review.
- [app/studio/printify.py](../app/studio/printify.py) `_check()` (the `_READ`, `_WRITE` lists);
  [app/studio/gelato.py](../app/studio/gelato.py) `_allowed()`.
- Tests `SafetyRails` in [app/tests/test_library_creator.py](../app/tests/test_library_creator.py);
  wiki [security.md](security.md).

## Figure out why a book came out wrong in Printify/Gelato
- Open the record in `app/data/logs/sends/` (the "Send journal" icon in the Order Creator): steps
  `files`, `catalog`, `pdf`, `link`, `readback`, the request body and the response —
  [features/send-journal.md](features/send-journal.md).
- Don't change the Gelato PDF layout without a test draft with numbered pages
  ([integrations/gelato.md](integrations/gelato.md)).

## Change the Printify/Gelato file check
- [app/studio/creator/printfolder.py](../app/studio/creator/printfolder.py) — `expected_files()`, `validate()`
  are in settings (`coverSize`, `pageSize`) from the Master analysis.

## Mockups: a new template, a renamed layer, another number of spreads
- [app/studio/mockups.py](../app/studio/mockups.py) — `TEMPLATES` (file, `slots`, the layer path of each
  role, `hand` for the owner's front cover, `size`), `RUN_ORDER`; the smart objects' inner sizes — `HARD`,
  `SOFT` (read them from the template with psd-tools, read-only: [the templates](features/mockups.md#the-templates)).
- The page takes the slots from `/api/mockups/state` on its own.
- Tests: `trees()` in [app/tests/test_mockups.py](../app/tests/test_mockups.py) — the pretend layer tree of
  each template. Wiki: [features/mockups.md](features/mockups.md).

## Mockups: a different crop of the back, spine or rim
- [app/studio/mockups.py](../app/studio/mockups.py) — `cover_pictures()` (and `_fill()`); test `Pictures`.

## Related

- [Code map](code-map.md) · [Glossary](glossary.md)
