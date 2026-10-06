"""Text check before print: a local vision model (Gemma in Ollama, on this computer's graphics card)
reads every page of the Canva export, and the program compares what is printed with what must be —
the book's texts from the library with the child's name, the dedication and who the book is from.

Two passes (the scheme that found every planted mistake on the owner's own Canva pages without a false
alarm, 19.09.2026 — wiki/features/text-check.md):
  read   the story pages are copied blind, only their first lines — enough to learn which pages carry
         text and which library text each one is (a Printify book lacks three spreads, a 28-page
         Gelato book one);
  check  every text page, the cover and the first and last page again, now with the text they must
         carry: the model copies the page exactly and judges it, the program compares that copy word by
         word. Names and leftover placeholders are always the program's own call.
A book without texts in the library gets the light check: names, placeholders, other orders' children,
cut-off text. The pictures never leave the computer (Ollama answers on 127.0.0.1 only); a journal of
every check is kept in data/logs/checks/.
The parts: ollama.py (the model on this computer), texts.py (words, the buyer's fields, which page is which
text), rules.py (what the card shows), run.py (one check), journal.py (the journal and the owner's marks),
routes.py. Split out of one 1 400-line file on 27.09.2026 — every rule as it was (textcheck_replay.py --all gives
the same output).
"""
from __future__ import annotations

from ..wording import clean_name, is_default, words
from . import journal, ollama, routes, rules, run, texts  # noqa: F401  (routes: they register themselves)
from .journal import CHECKS, mark, _journal
from .ollama import DEFAULT_MODEL, ModelError, TimedOut, Unavailable, _NO_PROXY, _base, _ready, status, start_ollama
from .routes import _check, _mark, _passport, _save_settings, as_template
from .rules import _all_issues, _vocabulary, book_issues, findings, has_text, page_issues
from .run import LOOKS_PICTURE, LOOKS_TEXT, _Run, _cache, _runs, cancel, check_book, check_order, warm
from .texts import COMMON, assign, diff, fill, personalization, similarity, split_dedication
