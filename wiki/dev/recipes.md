---
title: Recipes — how to change common things
type: dev
updated: 2026-11-12
code:
  - app/studio/orders.py
  - app/studio/core.py
  - app/studio/profit.py
  - app/studio/printify.py
  - app/studio/stages.py
  - app/studio/mockups.py
  - app/web/js/app.js
  - app/web/js/places.js
  - app/web/js/icons.js
  - app/web/js/order-bits.js
---
# Recipes

> Exactly where to change code for common tasks, and what not to forget. After each one: the tests, `python app/tools/wiki_check.py --changed`, and the pages it lists (rules in `.claude/rules/wiki.md`).

## Change the printer rule
- [app/studio/orders.py](../../app/studio/orders.py) — `plan_for()` (and `binding_of()` if cover recognition changes).
- Test: [test_orders.py](../../app/tests/test_orders.py) — `PrinterRule`. The interface's explanation: [order-bits.js](../../app/web/js/order-bits.js) — `planText()`.
- Wiki: [Gelato](../integrations/gelato.md), [decisions](../decisions.md).

## Add a Gelato format (a new size)
- [app/studio/core.py](../../app/studio/core.py) — `DEFAULT_SETTINGS` (`gelato.formats`: `label`, `productUid`); saved settings are merged with the defaults, so the new key appears by itself.
- [app/studio/orders.py](../../app/studio/orders.py) — `plan_for()`: when the format is picked.
- The Order Creator shows formats from the status: [creator.js](../../app/web/js/pages/creator.js) — `formatCard()`; the page counts come from Gelato's catalog.

## A different Gelato book length (besides 28 and 30)
- [app/studio/core.py](../../app/studio/core.py) — `DEFAULT_SETTINGS` `gelato.pageCounts`. `_merge()` does not change a list already saved in the owner's `settings.json`: write the new list into it (the load only lays the saved file over the defaults).
- Everything else follows the list: [printfolder.py](../../app/studio/creator/printfolder.py) — `gelato_page_options()`, `_gelato_page_count()`; [orders.py](../../app/studio/orders.py) — `page_options()`.
- Check with a test draft with numbered pages (page 0 blank, then 1…N). Wiki: [Gelato](../integrations/gelato.md), [book files](../rules/book-files.md).

## The Profit page's first day
- [app/studio/profit.py](../../app/studio/profit.py) — `ACCOUNTING_FROM`; test: [test_profit.py](../../app/tests/test_profit.py) — `BookkeepingStart`. Wiki: [Profit](../features/profit.md).

## Printify back for new books
- [app/studio/printify.py](../../app/studio/printify.py) — `READ_ONLY_FROM`, `retired()` (a later date, or the latest possible one); the printer rule, the Order Creator's switch and the archive's reprint follow `retired()`. Wiki: [Printify](../integrations/printify.md), [Gelato](../integrations/gelato.md).

## A new interface page
- A file `app/web/js/pages/<name>.js` with `export async function mount(view, params)` → `{ shown?, unmount }` (an example: [profit.js](../../app/web/js/pages/profit.js) — `mount()`).
- [app/web/js/app.js](../../app/web/js/app.js) — `ROUTES` with the page's area (its ink); a place of its own in the rail — `PLACES`; an old address becomes an entry of `ALIASES`. A page that serves an object (an order, a book) gives its controller a `navFor` key naming that place.
- A tool that also works alone: [places.js](../../app/web/js/places.js) — a line in `TOOLS` (it shows in «Інструменти»).
- Styles in [app.css](../../app/web/css/app.css) (tokens and shared parts) or the section's own css file; colours from tokens only ([interface principles](../owner/ui-principles.md)).
- Wiki: a page under `features/` and a row in `index.md`.

## A new server route
- `@route("METHOD", r"/api/...")` in the right module ([server.py](../../app/studio/server.py) — `route()`); a new module is added to the import in [main.py](../../app/studio/main.py) — `main()`, or the route does not register.
- A long action goes through [jobs.py](../../app/studio/jobs.py) — `Jobs.start()`, with [lib.js](../../app/web/js/lib.js) — `runJob()` in the interface.
- `python app/tools/wiki_check.py --routes` prints the route table; a rule-bearing note (a 403 refusal) goes on the feature's page.

## A new icon
- [app/web/js/icons.js](../../app/web/js/icons.js) — a path in the `P` map (24×24 grid, 1.6 stroke); `icon()` returns it. One icon, one meaning.

## A new order stage
- [app/studio/stages.py](../../app/studio/stages.py) — `order_stage()`; [order-bits.js](../../app/web/js/order-bits.js) — `STAGES`, `STAGE_EMPTY`, `STAGE_LABEL` (the card's and the archive's chip).
- Test: [test_states.py](../../app/tests/test_states.py) — `PickerStages`; wiki [order stages](../rules/order-stages.md).

## What to show in the proof's note
- [order-card.js](../../app/web/js/pages/order-card.js) — `proofCard()` (the notes filter); [order-bits.js](../../app/web/js/order-bits.js) — `isFormatField()`, `isNameField()`; the sizes are the proof-name and proof-note classes in orders.css.

## Filmstrip thumbnail size
- Change **together** [order-bits.js](../../app/web/js/order-bits.js) — `STRIP_THUMB` and [images.py](../../app/studio/images.py) — `VIEW_SIDES`, or the file check prepares the wrong size.

## A new service key
- [vault.py](../../app/studio/vault.py) — `SECRET_NAMES`; [settings_api.py](../../app/studio/settings_api.py) — `EDITABLE_SECRETS`; [settings.js](../../app/web/js/pages/settings.js) — `SECRET_LABELS`.

## A new setting
- [core.py](../../app/studio/core.py) — `DEFAULT_SETTINGS` → a route in [settings_api.py](../../app/studio/settings_api.py) → a field in [settings.js](../../app/web/js/pages/settings.js). Settings stay minimal ([interface principles](../owner/ui-principles.md)).
- A switch that must not travel between computers goes into [transfer.py](../../app/studio/transfer.py) — `_computer_bound()` ([settings](../features/settings.md)).

## Allow a new Printify or Gelato call
- Only with the owner's direct permission and a security review. [printify.py](../../app/studio/printify.py) — `_check()`, `_READ`, `_WRITE`; [gelato.py](../../app/studio/gelato.py) — `_allowed()`.
- Tests: [test_library_creator.py](../../app/tests/test_library_creator.py) — `SafetyRails`; wiki [security](../security.md).

## Find out why a book came out wrong at the printer
- Open the record of the send in `app/data/logs/sends/` (the journal icon in the Order Creator): steps `files`, `catalog`, `pdf`, `link`, `readback`, the request and the response ([order creator](../features/order-creator.md)). Do not change the Gelato PDF layout without a test draft with numbered pages ([Gelato](../integrations/gelato.md)).

## Change the print file check
- [printfolder.py](../../app/studio/creator/printfolder.py) — `expected_files()`, `validate()` read the sizes from settings (`coverSize`, `pageSize`).

## Mockups: a new template, a renamed layer, another number of spreads
- [app/studio/mockups.py](../../app/studio/mockups.py) — `TEMPLATES` (file, slots, each role's layer path, the owner's front cover, size), `RUN_ORDER`, and the smart objects' inner sizes `HARD`, `SOFT` (read them from the template with psd-tools, read-only). A changed template must be baked again ([mockups engine](../features/mockups-engine.md#templates)). The page takes the slots from `/api/mockups/state` by itself.
- Tests: [test_mockups.py](../../app/tests/test_mockups.py) — `trees()`, the pretend layer tree of each template.
- A different crop of the back, spine or rim: [mockups.py](../../app/studio/mockups.py) — `cover_pictures()`.

## Related
- [Testing](testing.md) · [Preview](preview.md) · [Glossary](../glossary.md)
