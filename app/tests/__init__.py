"""Test suite: run with `python -m unittest discover -s tests` from the project folder."""
import atexit
import os
import shutil
import tempfile

# Tests never touch real data: they make their own throw-away folder before any import and take it over,
# whatever BOOK_STUDIO_DATA said. The tests below empty whole folders, so this may not be left to chance.
_folder = tempfile.mkdtemp(prefix="bstests-")
os.environ["BOOK_STUDIO_DATA"] = _folder
atexit.register(shutil.rmtree, _folder, True)
