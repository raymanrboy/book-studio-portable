"""What this program keeps about Etsy orders on disk (data/profit/): the last sync's snapshot, the owner's manual links
and states, and the print orders it sent itself. Read and written only here; nothing is worked out here — matching
and money are reconcile.py / outcomes.py, the stages stages.py, the Profit view profit.py, the sync sync.py."""
from __future__ import annotations

import threading
from pathlib import Path

from . import core

SNAPSHOT = core.data_path("profit", "snapshot.json")
LINKS = core.data_path("profit", "links.json")          # receipt id -> a print order linked by hand (or "none")
STATES = core.data_path("profit", "states.json")        # receipt id -> manual state (cancel / refund / replacement)
SENDS = core.data_path("profit", "print-orders.json")   # receipt id -> the print orders this program sent
lock = threading.Lock()  # every read-change-write of links, states and sends


def stamp(path: Path) -> tuple | None:
    """A file's identity now: every write_json() puts a new file in place, so its id changes even when two writes
    fall within one tick of the file clock (~16 ms on Windows — the flaky test of 16.09.2026). None — no file."""
    try:
        st = path.stat()
    except FileNotFoundError:
        return None
    return st.st_ino, st.st_mtime_ns, st.st_size


_snapshot = {"key": None, "data": None}
_snapshot_lock = threading.Lock()


def load_snapshot() -> dict:
    """The last sync's orders, parsed once per change of the file (opening one order card used to parse it
    four times — 22.09.2026 audit). Callers only read it: a sync builds a new snapshot and saves that."""
    key = stamp(SNAPSHOT)
    if key is None:
        return {}
    with _snapshot_lock:
        if _snapshot["key"] != key:
            _snapshot.update(key=key, data=core.read_json(SNAPSHOT, {}) or {})
        return _snapshot["data"]


def load_links() -> dict:
    return core.read_json(LINKS, {}) or {}


def load_states() -> dict:
    return core.read_json(STATES, {}) or {}


def load_sends() -> dict:
    return core.read_json(SENDS, {}) or {}


class DataGuard(Exception):
    """A write that would lose what the owner's data holds is refused (the file stays as it is)."""


def _guard(path: Path, data: dict) -> None:
    if path == SENDS:      # what was sent to print is only ever added to: a receipt's sends vanishing would let it be sent twice
        lost = set(core.read_json(SENDS, {}) or {}) - set(data)
        if lost:
            raise DataGuard(f"print-orders.json: {len(lost)} receipts would be lost — the write is refused")
    elif path == SNAPSHOT:  # the shops' snapshot does not shrink to a fraction of itself
        old = len((core.read_json(SNAPSHOT, {}) or {}).get("receipts") or [])
        if old >= 20 and len(data.get("receipts") or []) < old // 2:
            raise DataGuard(f"snapshot.json: {old} receipts would become {len(data.get('receipts') or [])} — the write is refused")


def save(path: Path, data: dict) -> None:
    _guard(path, data)
    core.write_json(path, data)


def has_ref(refs: list, provider: str, order_id) -> bool:
    return any(r.get("provider") == provider and str(r.get("orderId")) == str(order_id) for r in refs or [])


def remember_print_order(receipt_id: str | None, provider: str, order_id: str | None, books: int | None = None) -> bool:
    """What this program itself sent to a printer for a receipt. Books of one order can go in two goes
    (some ready now, the rest later) or to two printers, and then one receipt honestly has two print
    orders. Matching finds one of them by itself; only this record proves the others belong here too —
    a receipt number inside a printer's own text also appears on reprints, so it cannot be trusted for
    money. Reprints are not written here: they are replacements (stages.mark_reprint()). `books` — how many of the
    receipt's books went in this order (since 2026-10-14): an order of two books stays «new» until both are ordered."""
    if not receipt_id or not order_id:
        return False
    with lock:
        sends = load_sends()
        refs = sends.setdefault(str(receipt_id), [])
        if has_ref(refs, provider, order_id):
            return False
        refs.append({"provider": provider, "orderId": str(order_id), "at": core.now_iso(),
                     **({"books": int(books)} if books else {})})
        save(SENDS, sends)
    return True


def add_replacement(receipt_id: str, provider: str, order_id: str) -> bool:
    """A reprint written down as a replacement of its receipt (the check whether it should be is
    stages.mark_reprint()'s). A receipt with another manual state (cancelled, refunded) is left as it is."""
    with lock:
        states = load_states()
        entry = states.get(receipt_id)
        if entry and entry.get("status") not in ("normal", "replacement"):
            return False
        if not entry or entry.get("status") != "replacement":
            entry = {"status": "replacement", "at": core.now_iso(), "replacementOrders": [], "byArchive": True}
        refs = entry.setdefault("replacementOrders", [])
        if not has_ref(refs, provider, order_id):
            refs.append({"provider": provider, "orderId": str(order_id)})
        states[receipt_id] = entry
        save(STATES, states)
    return True


def unmark_reprint(receipt_id: str | None, provider: str, order_id: str | None) -> bool:
    """Undoes a replacement mark for a reprint that never went to print (its draft was deleted or the order
    cancelled): its reference goes, and so does a replacement state the archive made that holds nothing else."""
    if not receipt_id or not order_id:
        return False
    with lock:
        states = load_states()
        entry = states.get(receipt_id)
        refs = (entry or {}).get("replacementOrders") or []
        rest = [r for r in refs if not (r.get("provider") == provider and str(r.get("orderId")) == str(order_id))]
        if not entry or entry.get("status") != "replacement" or len(rest) == len(refs):
            return False
        if not rest and entry.get("byArchive") and not entry.get("replacementCost"):
            states.pop(receipt_id)
        else:
            entry["replacementOrders"] = rest
        save(STATES, states)
    return True
