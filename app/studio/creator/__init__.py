"""Order Creator: Printify unpublished photo-book products and Gelato draft orders.

Printify: folder with Cover.png + 1..N.png (N from the Master, 24) ->
  strict validation -> upload artwork (hash cache) -> new product built from the
  read-only Master configuration -> verification -> Master untouched check.
Gelato: folder with Cover.png + 1..30.png (or 1..28.png) -> light validation -> interior PDF ->
  temporary public link -> draft order (orderType=draft) -> link kept 15 min.
Nothing is ever published, ordered or sent to production.

The parts (a package since 27.09.2026 — it was one 1 300-line file): printfolder.py (the folder, its check, a page
replaced), sending.py (what every send does the same way), printify_send.py, gelato_send.py, photobook.py (the PDF),
routes.py.
"""
from __future__ import annotations

from ..jobs import jobs  # noqa: F401  (the tests stand in for the job runner here)
from . import gelato_send, photobook, printfolder, printify_send, routes, sending  # noqa: F401  (routes register)
from .gelato_send import GELATO_PLACEHOLDER_PHONE, create_gelato_draft, gelato_page_counts, gelato_pages_problem
from .photobook import _one_idat, build_photobook_pdf
from .printfolder import (REPLACED, _sending, _validating, _while_sending, expected_files, gelato_page_options,
                          replace_page, restore_page, validate)
from .printify_send import UPLOAD_CACHE, build_printify_payload, create_printify_draft, create_printify_reprint
from .routes import _create_gelato, _gelato_page_counts, _reprint_printify
from .sending import _unknown_outcome, receipt_for, validate_address
