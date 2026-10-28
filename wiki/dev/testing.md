---
title: Tests
type: dev
updated: 2026-10-28
code:
  - app/tests/
  - app/tools/ui_smoke.py
---
# Tests

> Tests on the standard `unittest` (how many — the runner says). No real requests or accounts: services are faked, data is
> **always** in a fresh temporary folder, buyers are made up. Run after every change.

## Running them

From the `app` folder:
```
python -m unittest discover -s tests
```
From the repository root:
```
python -m unittest discover -s app/tests -t app
```
The `PYTHONDONTWRITEBYTECODE=1` variable keeps `__pycache__` folders from piling up.
The wiki check is part of the tests (`test_wiki.py`), but it can also be run on its own:
`python app/tools/wiki_check.py`.

**The robot that clicks through the interface** (`tools/ui_smoke.py`, `tests/test_ui_smoke.py`): `dev_server.py --sample` in its own
folder `.tmpsui` on a free port (`BOOK_STUDIO_DEV_PORT`), a hidden Edge (`--headless=new`, a throwaway profile `.tmpsui-edge`) driven over
the DevTools protocol (a small WebSocket client of its own), every page of `PAGES` opened and its tabs pressed. A script error, a
`console.error`, a red toast, an empty page or a 5xx from the program fails it. Skipped without Edge or with `BOOKSTUDIO_SKIP_UI=1`.
Alone: `python app/tools/ui_smoke.py -v`.

## How it's built

- **Tests never reach real data** (the rule is in [data safety](../architecture/data-safety.md)): `tests/__init__.py` sets `BOOK_STUDIO_DATA` to a
  fresh temp folder before any import — **unconditionally**, whatever it was before, because tests clear whole folders — and wipes it after.
  Every test module starts with `from tests import __init__`. The Workshop's tests run in its sandbox (`BOOK_STUDIO_SANDBOX`): made-up books,
  Downloads, clipboard and Recycle Bin. Checked by `TestsNeverRunOnRealData` in `test_orders.py`.
- **On drive D**: Python's temp folder and `TEMP`/`TMP` (for node too) point to `<repository>\.tmp`, not Windows' temp on drive C
  (`test_the_suite_writes_nothing_to_drive_c` in `test_orders.py`); `.tmp` goes when the run ends (unless a preview server's folder lives
  there). The program's log file is closed first (`logging.shutdown()`), since Windows deletes no open file.
- **The day**: `tests/__init__.py` moves `printify.READ_ONLY_FROM` to `date.max`, so the suite checks Printify's work and the printer rule
  whatever day it runs; `GelatoOnly` in `test_orders.py` stands in `printify.retired()` for the Gelato-only days and checks the real date on its own.
- **Printify** is swapped for `FakePrintify` (in memory: uploads, products, Master, orders on hold; one copy in
  `tests/fixtures.py`, with `png()` and `book()` — the made-up print folders) via `mock.patch.object(printify, "call", …)`; the real
  `_check()` still runs underneath — the test catches forbidden paths.
- **The local model** (the text check) — `gemma_answer()` in `test_textcheck.py`: a read gives the page's first dozen words, a check says
  whether the page says what the prompt EXPECTED (one stand-in for every suite).
- **Gelato** — `gelato.call` is swapped; the tunnel — `FileTunnel.start`, `registry.keep`.
- **Etsy** — `etsy.tokens`, `etsy.fetch_all_receipts`, `httpc.request_json` are swapped.
- **Order archive** — time is supplied via the `now` argument to `archive.refresh()`, order facts via swapping `archive._facts`; background
  preview preparation (`_warm_previews`) is turned off so it doesn't hold files open during deletion. A file still open blocks its folder's
  removal on Windows: only the page's check makes previews (`images.check_png(previews=…)`; `PrintifyValidation` keeps it that way).
- **The interface's scripts** (`test_scripts.py`): there are no browser tests, so each script is checked by Node.js as the ES module it is
  (`node --check` on a `.js` file doesn't parse it as one; skipped without Node.js); and, read by a small tokenizer (`tests/jstokens.py`), no
  script uses a name another script exports without importing it, none imports a name it never uses, and none uses a name it neither
  declares nor imports and that isn't the browser's own (`undeclared()`, `GLOBALS`).
- Opening the browser — `mock.patch("webbrowser.open")`.
- **Photoshop** — never started by the tests: `mockups.launch` is swapped for a stand-in that writes the status file; the Photoshop script
  itself (ExtendScript is plain old JavaScript) runs under **Node.js** against a small pretend Photoshop (`HARNESS` in `test_mockups.py`).
  Without Node.js these tests are skipped (the portable `runtime/` has no Node). **Node reads more than Photoshop 2019's ExtendScript does**
  (e.g. a `/` inside a regex's `[...]`), so a test reads the script's text for what ExtendScript can't parse
  (`test_no_slash_inside_a_regex_class_which_photoshop_cannot_read`).
- `golden_profit.json` — made-up receipts and orders with the results from the original Profit Calculator (parity to the cent).
- Images are generated on the fly (Pillow, small sizes), Printify sizes are swapped in the tests.

## Rules

- New behavior — a new test; the test's name describes the behavior, in English
  (`test_dropped_copies_are_moved_not_copied`).
- Only made-up names, addresses, receipt numbers (format `41000000xx`). Real customer data never goes into the repository.
- A test must never hit the network; if a new external call shows up, fake it.
- Test order doesn't matter; settings state is restored in `tearDown`. To reset a state file, it's
  enough to delete the file itself: the `.bak` of a deleted file is not read.
- Send-journal steps are checked as "these steps in this order" (`assert_steps()`), not an exact list: a
  new step doesn't break a dozen tests. There are almost no real pauses (`time.sleep` only in a few thread-wait loops); the
  record's time is supplied instead.
- The order of interface layers and preview sizes are checked straight from the page files
  (`SharedNumbers`): a human or an agent checks page behavior on the [preview server](preview.md).

## Suites

One line each; the test names say the rest.

| File | Classes |
|---|---|
| [test_ui_smoke.py](../../app/tests/test_ui_smoke.py) | `EveryPage` — every page in a hidden Edge on made-up data |
| [test_aside.py](../../app/tests/test_aside.py) | `Shelf` — «Скасувати» before the Recycle Bin |
| [test_ledger.py](../../app/tests/test_ledger.py) | `Assign`, `ReceiptCheck`, `Chain`, `Overhead`, `Refresh` — Etsy's ledger, made-up entries |
| [test_profit.py](../../app/tests/test_profit.py) | `ProfitParity`, `FeeRules`, `NameMatching`, `BookkeepingStart` |
| [test_gelato_accounts.py](../../app/tests/test_gelato_accounts.py) | `Accounts`, `OpenOrders` — two made-up Gelato accounts and the switch |
| [test_states.py](../../app/tests/test_states.py) | `NormalOrdersUnchanged`, `EtsyStates`, `LedgerMoney`, `QueueSignals`, `Replacement`, `ProviderCancellations`, `PickerStages`, `SeveralPrintOrdersForOneReceipt`, `SentStage`, `GelatoTracking`, `IncrementalSync`, `StateApi` |
| [test_library_creator.py](../../app/tests/test_library_creator.py) | `TextJson`, `FolderScan`, `PrintifyValidation`, `GelatoValidation`, `ReplacePage`, `NothingIsLostWhenAWriteFails`, `JsonFiles`, `SafetyRails` |
| [test_flows.py](../../app/tests/test_flows.py) | `PrintifyDraftFlow`, `GelatoDraftFlow`, `CreatorStartsEmpty`, `DroppedFolders`, `OpenUrlGuard`, `ProfitSyncFlow`, `EtsyOAuth` |
| [test_orders.py](../../app/tests/test_orders.py) | `PrinterRule`, `GelatoOnly`, `ArrangePages`, `GelatoLength`, `PreparationGuide`, `PartialBookImport`, `SyncOnlyAtStartOrByHand`, `DevToolsKeepOffRealData`, `TestsNeverRunOnRealData`, `SharedNumbers`, `CanvaZipFromDownloads` |
| [test_archive.py](../../app/tests/test_archive.py) | `Storing`, `Removing`, `OnlyWhatWentToPrint`, `ReprintMark`, `PrintifyReprint`, `GelatoReprint`, `PreviewCache` |
| [test_textcheck.py](../../app/tests/test_textcheck.py) | `Words`, `BuyerFields`, `NameRules`, `Assign`, `PageIssues`, `WholeCheck` (the model is faked), `WhileItRuns`, `Prescan`, `Passport`, `BooksOfOneOrder`, `AnotherBookByPosition`, `OwnerMarks`, `Replay`, `OllamaAndRoutes` |
| [test_mockups.py](../../app/tests/test_mockups.py) | `ReadingTheDemoBook`, `Pictures`, `RunPlan`, `Run` (a pretend Photoshop), `SaidInTheLog`, `Cleaning`, `SaveTheOpenOnes`, `Progress`, `PhotoshopScript` — the real `mockups.jsx` run by Node.js |
| [test_photos.py](../../app/tests/test_photos.py) | `TheTemplates`, `ThePrompts`, `InABook`, `TheOmniVideo`, `WithoutABook`, `TheEtsyFolder`, `TheMockupsKeepTheCanvaCover` |
| [test_mockup_draw.py](../../app/tests/test_mockup_draw.py) | `Baked`, `Colours`, `TheFrontsCrop`, `DrawnRun` — the mockups drawn without Photoshop |
| [test_slides.py](../../app/tests/test_slides.py) | `TheCut`, `Scenes`, `WorkshopBooks`, `MakingThem`, `CommandLine` |
| [test_workshop.py](../../app/tests/test_workshop.py) | In the sandbox: `TheSandbox`, `TheBookList`, `ThePathStrip`, `OnlyInsideTheBook`, `TheSignature`, `TheRows`, `TheBookCheck`, `APictureIntoItsRow`, `CoverTool`, `CatchingDownloads`, `CtrlVInTheBrowser`, `PassingToTheLibrary`, `OnePlaceForThePages` |
| [test_canva_extension.py](../../app/tests/test_canva_extension.py) | `BookLogic` — the Canva extension's `book.js` run by Node.js; `Manifest` |
| [test_backup.py](../../app/tests/test_backup.py) | `Rules`, `RealArchive` — a real 7-Zip run on a made-up folder (skipped without `app/bin/7za.exe`) |
| [test_speed.py](../../app/tests/test_speed.py) | `EdgeProfile`, `SideBySide` |
| [test_server_http.py](../../app/tests/test_server_http.py) | `HttpLayer` — the real server on a free port; `OneCopy` — a second process on the same data |
| [test_scripts.py](../../app/tests/test_scripts.py) | `ScriptsParse`, `ScriptsImport` |
| [test_wiki.py](../../app/tests/test_wiki.py) | `WikiMatchesCode`, `NamedInTheRightFile` |

## Where in the code

- [app/tests/__init__.py](../../app/tests/__init__.py) — the temporary data folder, Printify's read-only date moved away
- [app/tests/fixtures.py](../../app/tests/fixtures.py) — `FakePrintify`, `png()`, `book()`
- [app/tests/test_flows.py](../../app/tests/test_flows.py) — `assert_steps()`, `journal()`
- [app/tests/test_textcheck.py](../../app/tests/test_textcheck.py) — `gemma_answer()`
- [app/tools/wiki_check.py](../../app/tools/wiki_check.py) — `check()`
- [app/tools/ui_smoke.py](../../app/tools/ui_smoke.py) — `run()`, `PAGES`, `Socket`, `problems_in()`

## Related

- [Security](../security.md) · [Interface preview](preview.md) · [Wiki rules](wiki-rules.md)
