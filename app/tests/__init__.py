"""Test suite: run with `python -m unittest discover -s tests` from the project folder."""
import atexit
import os
import shutil
import tempfile
from pathlib import Path

# Everything the tests write goes to <repository>/.tmp on drive D instead of Windows' temp folder on drive C (the
# owner keeps drive C clean, 23.09.2026) — the child processes they start (node) included — and goes at the end.
_ROOT = Path(__file__).resolve().parents[2] / ".tmp"
_ROOT.mkdir(exist_ok=True)
tempfile.tempdir = str(_ROOT)
os.environ["TEMP"] = os.environ["TMP"] = str(_ROOT)

# Tests never touch real data: they make their own throw-away folder before any import and take it over,
# whatever BOOK_STUDIO_DATA said. The tests below empty whole folders, so this may not be left to chance.
_folder = tempfile.mkdtemp(prefix="bstests-")
os.environ["BOOK_STUDIO_DATA"] = _folder
# The portable copy's runtime/ is the owner's real programs: no test may find them (test_portable turns it on on a fake one).
os.environ["BOOKSTUDIO_PORTABLE"] = ""
# The Workshop's sandbox: its books, Downloads, clipboard and Recycle Bin are files in that folder too — the owner's
# clipboard, keyboard (F8), Downloads and screen are never touched by a test.
os.environ["BOOK_STUDIO_SANDBOX"] = "1"


def _wipe() -> None:
    import logging
    # The program's log file is still open, and Windows deletes no open file: folders holding a lone
    # logs/app.log piled up in the temp folder until 23.09.2026.
    logging.shutdown()
    shutil.rmtree(_folder, True)
    try:
        _ROOT.rmdir()  # only when nothing else lives there (a preview server's folder may)
    except OSError:
        pass


atexit.register(_wipe)

# The suite checks Printify's work and the printer rule as they were before 1 October 2026, when Printify stopped
# getting new books (printify.retired()) — whatever day it runs on; the tests of that change say so themselves.
from datetime import date  # noqa: E402

from studio import printify as _printify  # noqa: E402

_printify.READ_ONLY_FROM = date.max
