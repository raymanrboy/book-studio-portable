---
title: Tests
type: dev
updated: 2026-09-26
code:
  - app/tests/
---
# Tests

> 336 tests on the standard `unittest`. No real requests or accounts: services are faked, data is
> **always** in a fresh temporary folder (the test suite takes `BOOK_STUDIO_DATA` over for itself,
> whatever it was before) in `.tmp\` of the repository on drive D, wiped at the end; buyers are made up. The
> Workshop's tests run in its sandbox (`BOOK_STUDIO_SANDBOX`): made-up books, Downloads, clipboard and Recycle Bin
> in that folder — the owner's are never touched.
> Run after every change.

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

## How it's built

- `tests/__init__.py` sets `BOOK_STUDIO_DATA` to a fresh temp folder before any import, and wipes it
  after the tests — the real `app/data` is never touched. Every test module starts with
  `from tests import __init__`.
  **On drive D** (since 2026-09-23): Python's temp folder and `TEMP`/`TMP` (for node too) point to
  `<repository>\.tmp`, not Windows' temp folder on drive C, which the owner keeps clean; `.tmp` goes when
  the run ends (unless a preview server's folder lives there). Before that, the wipe also failed quietly:
  the program's log file was still open and Windows deletes no open file, so 177 `bstests-*` folders with a
  lone `logs\app.log` piled up in `%TEMP%` — now the log is closed first (`logging.shutdown()`). Checked by
  `test_the_suite_writes_nothing_to_drive_c` in `test_orders.py`.
  **Unconditionally** (since 2026-09-22): tests used to accept an already-set `BOOK_STUDIO_DATA` as-is
  — and they clear whole folders (`shutil.rmtree(archive.ROOT)`), so running from a configured shell
  could wipe the real archive. Found by the audit; checked by `TestsNeverRunOnRealData` in
  `test_orders.py`.
- **Printify** is swapped for `FakePrintify` (in memory: uploads, products, Master, orders) via
  `mock.patch.object(printify, "call", …)`; the real `_check()` still runs underneath — the test catches
  forbidden paths.
- **Gelato** — `gelato.call` is swapped; the tunnel — `FileTunnel.start`, `registry.keep`.
- **Etsy** — `etsy.tokens`, `etsy.fetch_all_receipts`, `httpc.request_json` are swapped.
- **Order archive** — time is supplied via the `now` argument to `archive.refresh()`, order facts via
  swapping `archive._facts`; background preview preparation (`_warm_previews`) is turned off so it
  doesn't hold files open during deletion.
- **A file still open blocks its folder's removal on Windows**: a test that leaves a background thread reading
  its temporary folder fails now and then with `PermissionError … being used by another process` and leaves
  a `.tmp\tmpXXXX` folder behind. That was `GelatoDraftFlow.test_an_unclear_draft_keeps_its_files_reachable`
  (1 run in 5, until 2026-09-25): a send's own folder check started the preview warm-up. Now only the page's
  check warms previews (`creator._warm_in_background()`); `PrintifyValidation` keeps it that way.
- Opening the browser — `mock.patch("webbrowser.open")`.
- **Photoshop** — never started by the tests: `mockups.launch` is swapped for a stand-in that writes the
  status file; the Photoshop script itself (ExtendScript is plain old JavaScript) runs under **Node.js**
  against a small pretend Photoshop — layers, visibility, "Replace Contents", saving that takes the active
  document (`HARNESS` in `test_mockups.py`). Node.js is on the Wrocław PC; without it these tests are skipped.
  **Node reads more than Photoshop 2019's ExtendScript does**: `/^.*[\\/]/` ran in Node but stopped the real
  script at once ("Error 25: Expected: )", 2026-09-26) — so a test reads the script's text for what ExtendScript
  can't parse (a `/` inside a regex's `[...]`; `test_no_slash_inside_a_regex_class_which_photoshop_cannot_read`).
- `golden_profit.json` — made-up receipts and orders with the results from the original Profit
  Calculator (parity to the cent).
- Images are generated on the fly (Pillow, small sizes), Printify sizes are swapped in the tests.

## Rules

- New behavior — a new test; the test's name describes the behavior, in English
  (`test_dropped_copies_are_moved_not_copied`).
- Only made-up names, addresses, receipt numbers (format `41000000xx`). Real customer data never goes
  into the repository (a real address was found once and replaced before the first push).
- A test must never hit the network; if a new external call shows up, fake it.
- Test order doesn't matter; settings state is restored in `tearDown`. To reset a state file, it's
  enough to delete the file itself: the `.bak` of a deleted file is no longer read (since 2026-09-23).
- Send-journal steps are checked as "these steps in this order" (`assert_steps()`), not an exact list: a
  new step doesn't break a dozen tests. There are no real pauses (`time.sleep`) for timing — the
  record's time is supplied instead.
- The order of interface layers and preview sizes are checked straight from the page files
  (`SharedNumbers`): there are no browser tests, so a human or an agent checks page behavior on the
  [preview server](preview.md).

## Suites

| File | Classes |
|---|---|
| [test_profit.py](../../app/tests/test_profit.py) | `ProfitParity`, `FeeRules`, `NameMatching` |
| [test_states.py](../../app/tests/test_states.py) | `NormalOrdersUnchanged`, `EtsyStates`, `Replacement`, `ProviderCancellations`, `PickerStages`, `SeveralPrintOrdersForOneReceipt` (a receipt with two print orders), `SentStage`, `GelatoTracking`, `IncrementalSync`, `StateApi` |
| [test_library_creator.py](../../app/tests/test_library_creator.py) | `TextJson`, `FolderScan`, `PrintifyValidation` (including: a newer folder check stops an older one; only the page's check warms the previews), `GelatoValidation`, `ReplacePage` (replacing a single page, "Undo" after a restart, two replacements within a second, replacement blocked during a send — and when a folder is sent to two printers at once, exactly what's allowed to be written), `NothingIsLostWhenAWriteFails`, `JsonFiles` (`.bak` and a deleted file), `SafetyRails` (including: a POST that may have gone through is not retried; both printers read errors the same way) |
| [test_flows.py](../../app/tests/test_flows.py) | `PrintifyDraftFlow` (including: two books — one order with two line items; the receipt number as its own field; an unrecorded cost — a warning), `GelatoDraftFlow` (including: two books — one draft with two items; an unclear result keeps the link; one shared length-problem text), `CreatorStartsEmpty`, `DroppedFolders` (including: a folder for the library, each book its own child), `OpenUrlGuard`, `ProfitSyncFlow`, `EtsyOAuth` |
| [test_orders.py](../../app/tests/test_orders.py) | `PrinterRule`, `ArrangePages`, `GelatoLength`, `PreparationGuide`, `PartialBookImport`, `SyncOnlyAtStartOrByHand`, `DevToolsKeepOffRealData` (the preview server doesn't write to the real folder and doesn't take keys), `TestsNeverRunOnRealData` (and nothing on drive C), `SharedNumbers` (interface layers, preview sizes) |
| [test_archive.py](../../app/tests/test_archive.py) | `Storing`, `Removing` (including: a stale printer list proves nothing), `OnlyWhatWentToPrint` (including: "already at the printer" after a restart), `ReprintMark`, `PrintifyReprint`, `GelatoReprint` (including: a warning when the printer accepted it but the accounting wasn't recorded), `PreviewCache` (cache cleanup, locks, zoom) |
| [test_textcheck.py](../../app/tests/test_textcheck.py) | `Words`, `BuyerFields`, `NameRules`, `Assign`, `PageIssues`, `WholeCheck` (the model is faked: it "reads" what the test "printed"), `WhileItRuns` (a spread goes to checking without waiting for the last read; findings are handed over while the check runs), `Prescan` (a quick page scan: drawn text vs. a drawn illustration, picture-only pages never reach the model, a false positive — the second half of the spread is checked), `Passport` (a name only as a whole word, and only where the passport had `{Name}`; a preview before saving), `BooksOfOneOrder` (two books of one receipt don't block each other's checks), `AnotherBookByPosition` and `WholeCheck.test_another_books_pages_raise_one_alarm` (another book's pages — one alarm), `OwnerMarks` ("Not an error" into the journal), `Replay` (`app/tools/textcheck_replay.py`), `OllamaAndRoutes` |
| [test_mockups.py](../../app/tests/test_mockups.py) | `ReadingTheDemoBook`, `Pictures` (the back/front/spine cuts by colour, sizes, 300 dpi), `RunPlan` (every layer, the front cover never touched, names never overwrite, wrong picks, nothing points into the templates folder), `Run` (a pretend Photoshop: the templates untouched, the prepared pictures gone after it, stop, Photoshop closing, a script error), `SaidInTheLog` (the folder dialog and a failed run in the log), `Cleaning` (earlier runs with Photoshop closed / open, a copy the owner saved, Photoshop's temp folder, one demo book at a time in its own folder — an order's dropped files untouched both ways, a picked ZIP only read, the old utility's leftovers, the program's own temp folder on D), `SaveTheOpenOnes` («Зберегти відкриті»: names, offered after a reload, the run gone, a template the owner closed, Photoshop closed), `Progress` (every template's row), `PhotoshopScript` — **the real `mockups.jsx` run by Node.js against a pretend Photoshop**, the second script («Зберегти відкриті») too (skipped without `node`) |
| [test_workshop.py](../../app/tests/test_workshop.py) | In the sandbox, on made-up books: `TheSandbox` (the owner's books, clipboard and Downloads never reached; «Відкрити агента» puts the words with the pipeline's full paths — the rules and the books' folder — into the fake clipboard, since Antigravity 2 ignores the folder it is started with), `TheBookList`, `ThePathStrip`, `OnlyInsideTheBook`, `TheSignature`, `TheRows`, `TheBookCheck`, `APictureIntoItsRow`, `CatchingDownloads`, `PassingToTheLibrary` |
| [test_wiki.py](../../app/tests/test_wiki.py) | `WikiMatchesCode` |

## Where in the code

- [app/tests/__init__.py](../../app/tests/__init__.py) — the temporary data folder
- [app/tests/test_flows.py](../../app/tests/test_flows.py) — `FakePrintify`, `png()`, `assert_steps()`
- [app/tools/wiki_check.py](../../app/tools/wiki_check.py) — `check()`

## Related

- [Security](../security.md) · [Interface preview](preview.md) · [Wiki rules](wiki-rules.md)
