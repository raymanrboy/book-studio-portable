"""Test suite: run with `python -m unittest discover -s tests` from the project folder."""
import atexit
import os
import shutil
import tempfile

# Tests never touch real data: point the app at a throw-away folder before any import.
if "BOOK_STUDIO_DATA" not in os.environ:
    _folder = tempfile.mkdtemp(prefix="bstests-")
    os.environ["BOOK_STUDIO_DATA"] = _folder
    atexit.register(shutil.rmtree, _folder, True)
