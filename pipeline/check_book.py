"""The book check — run it before GO, from this folder:

    python check_book.py "books/40.some-book"

The rules live in Book Studio (app/studio/workshop/check.py): the Workshop shows the same result on the book's strip
(«Промпти · GO»). Exit code = the number of FAILs (0 = mechanically ready).
"""
import importlib.util
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ left in Book Studio's code by a book agent's run
sys.stdout.reconfigure(errors="replace")  # a console that can't show a character never stops the report
RULES = Path(__file__).resolve().parents[1] / "app" / "studio" / "workshop" / "check.py"
spec = importlib.util.spec_from_file_location("book_check", RULES)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)
sys.exit(check.main(sys.argv))
