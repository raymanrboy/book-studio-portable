---
title: Known limits and not verified live
type: dev
updated: 2026-11-12
code:
  - app/studio/textcheck/run.py
---
# Known limits and not verified live

> What the program deliberately does not do, what its checks cannot prove, and what has been tried only against fakes or made-up data.

## Deliberately not done
- **A receipt's stage comes from one print order.** If one of two books is sent and the other is not, the receipt is already off «Нові»; the «+N in print» chip shows the rest, but there is no "partly sent" stage ([order stages](../rules/order-stages.md)).
- **No «receipt → books → print batches» model.** Each book of an order goes through the path separately, and they go to the printer together as one draft to one address ([order creator](../features/order-creator.md)); a receipt mixing two printers is handled by hand.
- **After a send, each local step can fail on its own** (the journal entry, accounting, the archive): a warning, and the send stands ([order creator](../features/order-creator.md)).
- **Pages with the buyer's own dedication are not parsed;** they are rare and settled with the buyer. «With love, …» in the «from whom» field is not removed automatically ([order to print](../flows/order-to-print.md)).
- **The spread a 28-page book drops** is picked by hand in Canva; the program only reports which passport spreads a book lacks ([text check](../features/text-check.md)).
- **The window sends at most 6 requests at once** (the browser's own limit per host); the first seconds after dropping a book's pages queue behind each other.
- **Interface behaviour beyond a smoke pass is checked by hand.** The robot opens every page and presses its tabs; everything else is judged on the [preview](preview.md) ([testing](testing.md)).
- **The `etsy/` folder holds more files than a listing takes** (slides, whole-scene mockups, photo mockups, two of them 16–18 MB). The owner picks; Etsy is never opened from here, so its current upload limits are not checked ([photo mockups](../features/photo-mockups.md)).
- **Pasting the next part with Ctrl+V works only in Chrome;** the Workshop's pictures are made in Gemini, the photo mockups in ChatGPT.

## Worth watching
- **The text check model can loop on a correct page.** `gemma4` sometimes copies a page word for word, then invents "a mistake in the name" and repeats an apology until `JUDGE_TOKENS` cuts the answer (a known problem with a JSON schema, ollama#15502). The transcript that came through whole is taken from the cut answer and the program's own comparison decides (`_salvage()`); «модель не змогла прочитати сторінку» appears only when the copy itself is cut ([text check](../features/text-check.md)).
- **Drafts could be closed sooner.** Gelato fetches the PDF about a minute after a draft is created, and the temporary link lives 15 minutes ([Gelato](../integrations/gelato.md)).

## Tried only against fakes or made-up data
- A drag from Explorer (a folder, a ZIP) in a real window: simulated.
- The smoothness of the filmstrip and of animations in a visible window: simulated frames; the owner is the judge.
- A live order with several books: tests and made-up data. The first real one is to be checked in Gelato (one draft with two products, shipping charged once).
- A 28-page softcover and a several-books order live: not yet seen; a test draft covered only a 20×20 hardcover, and the catalog allows 28 for softcovers.
- The mockups' bake script in the real Photoshop and the taskbar flash: checked against a pretend Photoshop.
- A real Gemini download and paste into the Workshop, inside Book Studio on real Windows.
- Python on a clean Windows without the Visual C++ runtime; a Gelato draft from this copy after the keys are restored with `restore_keys.py` (no real writes without the owner's leave).

## Related
- [Security](../security.md) · [Testing](testing.md) · [Preview](preview.md) · [Decisions](../decisions.md)
