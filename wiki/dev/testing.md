---
title: Tests
type: dev
updated: 2026-11-12
code:
  - app/tests/
  - app/tools/ui_smoke.py
  - app/tools/wiki_check.py
---
# Tests

> Standard `unittest`. No real requests or accounts: services are faked, data is always in a fresh temporary folder, buyers are made up. Run after every change. The wiki check is one of the tests.

## Running them
From the `app` folder: `python -m unittest discover -s tests`. From the repository root: `python -m unittest discover -s app/tests -t app`. `PYTHONDONTWRITEBYTECODE=1` keeps `__pycache__` folders from piling up. The wiki check alone: `python app/tools/wiki_check.py` (also `--changed`, `--map`, `--routes`).

**The interface robot** (the test is [test_ui_smoke.py](../../app/tests/test_ui_smoke.py), the tool is [ui_smoke.py](../../app/tools/ui_smoke.py) — `PAGES`): `dev_server.py --sample` in its own folder on a free port (`BOOK_STUDIO_DEV_PORT`), a hidden Edge (`--headless=new`, a throwaway profile) driven over the DevTools protocol, every page of `PAGES` opened and its tabs pressed. A script error, a `console.error`, a red toast, an empty page or a 5xx fails it. Skipped without Edge or with `BOOKSTUDIO_SKIP_UI=1`. Alone: `python app/tools/ui_smoke.py -v`.

## How it is built
- **Tests never reach real data** ([data safety](../architecture/data-safety.md)). `tests/__init__.py` sets `BOOK_STUDIO_DATA` to a fresh temp folder before any import, unconditionally (tests clear whole folders), and wipes it after; every test module starts with `from tests import __init__`. The Workshop's tests run in its sandbox (`BOOK_STUDIO_SANDBOX`): made-up books, Downloads, clipboard, Recycle Bin. `TestsNeverRunOnRealData` guards this.
- **Drive D only:** Python's temp folder and `TEMP`/`TMP` point to `<repository>\.tmp`, not Windows' temp on C (`test_the_suite_writes_nothing_to_drive_c`); `.tmp` goes when the run ends unless a preview server's folder lives there. The log file is closed first (`logging.shutdown()`), since Windows deletes no open file.
- **Printify:** `tests/__init__.py` moves `printify.READ_ONLY_FROM` to `date.max`, so its code and the printer rule are exercised whatever day it is; `GelatoOnly` in `test_orders.py` stands in for `printify.retired()` where the Gelato-only behaviour is tested, and `test_etsy_rule.py` checks the real date. Printify itself is `FakePrintify` (in-memory, `tests/fixtures.py`, with `png()` and `book()` — the made-up print folders) swapped in with `mock.patch.object(printify, "call", …)`; the real `_check()` still runs underneath, so a forbidden path is caught.
- **Fakes:** the text-check model is `gemma_answer()` in `test_textcheck.py`; Gelato is `gelato.call`, the tunnel `FileTunnel.start` and `registry.keep`; Etsy is `etsy.tokens`, `etsy.fetch_all_receipts`, `httpc.request_json`; the browser is `mock.patch("webbrowser.open")`.
- **Archive:** time comes in through the `now` argument of `archive.refresh()`, order facts through swapping `archive._facts`; `_warm_previews` is switched off, because an open file blocks its folder's removal on Windows.
- **The scripts of the interface** (`test_scripts.py`): there are no browser tests, so each script is run by Node.js as the ES module it is (`node --check` on a `.js` file does not parse a module; skipped without Node.js), and a small tokenizer (`tests/jstokens.py`) checks that no script uses a name another exports without importing it, imports a name it never uses, or uses an undeclared name that is not the browser's own (`undeclared()`, `GLOBALS`).
- **Photoshop** is never started: `mockups.launch` is swapped for a stand-in that writes the status file, and the Photoshop script (plain old JavaScript) runs under Node.js against a pretend Photoshop (`HARNESS` in `test_mockups.py`). Node reads more than Photoshop 2019's ExtendScript does (a `/` inside a regex's `[...]`), so `test_no_slash_inside_a_regex_class_which_photoshop_cannot_read` reads the script's text for what ExtendScript cannot parse.
- `golden_profit.json`: made-up receipts and orders with the results of the original Profit Calculator (parity to the cent). Images are generated on the fly (Pillow, small).

## Rules
- New behaviour, a new test; its name says the behaviour, in English (`test_dropped_copies_are_moved_not_copied`).
- Only made-up names, addresses and receipt numbers (format `41000000xx`): a real address once leaked into the repository. Real customer data never goes in.
- A test never hits the network; a new external call is faked.
- Test order does not matter; settings are restored in `tearDown`. To reset a state file, delete the file: the `.bak` of a deleted file is not read.
- Send-journal steps are checked as "these steps in this order" (`assert_steps()` in `test_flows.py`), not an exact list. There are almost no real pauses; the record's time is supplied.
- The order of interface layers and preview sizes are checked straight from the page files (`SharedNumbers`); page behaviour is checked by a person on the [preview server](preview.md).

## Where in the code
- [app/tests/__init__.py](../../app/tests/__init__.py) — the temporary data folder, Printify's read-only date moved away
- [app/tests/fixtures.py](../../app/tests/fixtures.py) — `FakePrintify`, `png()`, `book()`
- [app/tests/test_flows.py](../../app/tests/test_flows.py) — `assert_steps()`
- [app/tests/test_textcheck.py](../../app/tests/test_textcheck.py) — `gemma_answer()`
- [app/tests/test_scripts.py](../../app/tests/test_scripts.py) — `undeclared()`, `GLOBALS`
- [app/tools/ui_smoke.py](../../app/tools/ui_smoke.py) — `run()`, `PAGES`, `Socket`, `problems_in()`

## Related
- [Security](../security.md) · [Preview](preview.md) · [Data safety](../architecture/data-safety.md)
