"""Test suite: run with `python -m unittest discover -s tests` from the project folder."""
import os
import tempfile

# Tests never touch real data: point the app at a throw-away folder before any import.
os.environ.setdefault("BOOK_STUDIO_DATA", tempfile.mkdtemp(prefix="bstests-"))
