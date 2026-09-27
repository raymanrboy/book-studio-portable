"""Paths, atomic JSON persistence, settings and logging shared by every module."""
from __future__ import annotations

import copy
import json
import logging
import os
import threading
import time
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

APP_NAME = "Book Studio"
APP_VERSION = "1.0.0"
DEFAULT_PORT = 47821

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
BIN_DIR = ROOT / "bin"
DATA_DIR = Path(os.environ.get("BOOK_STUDIO_DATA") or (ROOT / "data")).resolve()
# app/tools/dev_server.py: made-up data for looking at the pages — a real key is never stored or offered there.
SAMPLE = os.environ.get("BOOK_STUDIO_SAMPLE") == "1"
# The preview server and the tests: the Workshop touches nothing of the owner's — its clipboard goes into files in
# the data folder, F8 isn't taken from Windows, no window opens, and its Downloads and books are made-up ones there.
SANDBOX = SAMPLE or os.environ.get("BOOK_STUDIO_SANDBOX") == "1"
# The book pipeline (the folder Antigravity opens: the book agents' rules and playbook, in git) and the Workshop's
# books — its folders, where the agents write (pipeline/books, kept out of git).
PIPELINE_DIR = ROOT.parent / "pipeline"
WORKSHOP_BOOKS = DATA_DIR / "workshop-books" if SANDBOX else PIPELINE_DIR / "books"

log = logging.getLogger("studio")


def data_path(*parts: str) -> Path:
    return DATA_DIR.joinpath(*parts)


def ensure_dirs() -> None:
    for sub in (
        "library/books",
        "library/trash",
        "profit",
        "creator",
        "cache/thumbs",
        "logs",
        "tmp",
    ):
        data_path(sub).mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    data_path("logs").mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    if any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        return
    handler = RotatingFileHandler(data_path("logs", "app.log"), maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def own_temp() -> Path:
    """Windows' temp folder is on drive C, and the programs this one starts write there (the Edge window leaves
    logs and empty folders behind). The owner keeps drive C clean (23.09.2026): this process and everything it
    starts — the window, the Windows dialogs, cloudflared, Photoshop — get a temp folder inside the data folder
    on drive D instead, emptied now and again by clear_own_temp() when the program closes."""
    import shutil
    import tempfile
    folder = data_path("tmp", "system")
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(folder)
    tempfile.tempdir = str(folder)
    return folder


def clear_own_temp() -> None:
    import shutil
    shutil.rmtree(data_path("tmp", "system"), ignore_errors=True)  # a file still held stays till the next start


def new_id() -> str:
    return uuid.uuid4().hex


IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")  # a picture, wherever one is looked for (was written out five times)


def inside(path: Path, folder: Path, or_same: bool = False) -> bool:
    """`path` lies somewhere in `folder` (or is the folder itself, with `or_same`). Both resolved first, so neither a
    `..` nor a link fools it — the one check behind every "only in our own folder" rule."""
    path, folder = Path(path).resolve(), Path(folder).resolve()
    return folder in path.parents or (or_same and path == folder)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z"


# ---------------------------------------------------------------- JSON files

def read_json(path: Path, default: Any = None) -> Any:
    """Reads JSON; falls back to the .bak copy when the main file is damaged. A main file that is not there
    means no data: write_json never leaves it missing, so the .bak of a removed file stays unread (it brought
    back state the program or a test had cleared — 22.09.2026 audit)."""
    for candidate in (path, path.with_name(path.name + ".bak")):
        try:
            with open(candidate, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except FileNotFoundError:
            break
        except (json.JSONDecodeError, UnicodeDecodeError):
            log.warning("Damaged JSON file skipped: %s", candidate)
            continue
    return copy.deepcopy(default)


def write_json(path: Path, obj: Any, backup: bool = True) -> None:
    """Atomic write: temp file in the same folder, fsync, then replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}.tmp")
    data = json.dumps(obj, ensure_ascii=False, indent=2)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    if backup and path.exists():
        try:
            replace_file(path, path.with_name(path.name + ".bak"), copy_only=True)
        except OSError:
            # The write goes on (the new data matters more); the .bak is now older than one write.
            log.warning("Backup copy of %s not made; the .bak keeps an older state", path.name, exc_info=True)
    replace_file(tmp, path)


def replace_file(src: Path, dst: Path, copy_only: bool = False) -> None:
    """`src` moved over `dst` (or copied, `copy_only`). Windows can briefly lock a file (antivirus, the indexer,
    a picture open in a viewer) — tried a few times."""
    last: Exception | None = None
    for attempt in range(8):
        try:
            if copy_only:
                with open(src, "rb") as a, open(dst, "wb") as b:
                    b.write(a.read())
            else:
                os.replace(src, dst)
            return
        except PermissionError as err:
            last = err
            time.sleep(0.05 * (attempt + 1))
    if last:
        raise last


# ---------------------------------------------------------------- settings

def _default_placements(page_count: int) -> dict:
    placements = {"cover": {"x": 0.5000000000000001, "y": 0.4968637346791639, "scale": 1, "angle": 0}}
    for i in range(1, page_count + 1):
        placements[f"page_{i}"] = {"x": 0.5, "y": 0.5, "scale": 1, "angle": 0}
    return placements


DEFAULT_SETTINGS: dict = {
    "ui": {"theme": "dark", "reduceMotion": False},
    "etsy": {
        "redirectUri": "",
        "shopId": None,
        "shopName": None,
    },
    "printify": {
        "shopId": 25329813,
        "shopTitle": "CozyCovenant",
        "coverSize": [4672, 2464],
        "pageSize": [4000, 4000],
        "pageCount": 24,
        "master": {
            "productId": "6a9d873d0c58e23a2a0dd499",
            "title": "Hardcover 8x8 Template",
            "blueprintId": 2737,
            "printProviderId": 28,
            "description": "<p></p>",
            "background": "#ffffff",
            "variants": [
                {"id": 149190, "price": 845, "is_enabled": True, "title": "8x8 / Glossy"},
                {"id": 149191, "price": 845, "is_enabled": True, "title": "8x8 / Matte"},
                {"id": 149192, "price": 1550, "is_enabled": False, "title": "11x8.5 / Glossy"},
                {"id": 149193, "price": 1550, "is_enabled": False, "title": "11x8.5 / Matte"},
            ],
            "printAreaVariantIds": [149190, 149191, 149192, 149193],
            "placements": _default_placements(24),
            "analyzedAt": None,
        },
    },
    "gelato": {
        "pageCounts": [28, 30],  # a book is as long as the Canva export: 30 pages, or 28 without one spread
        "currency": "USD",
        "eurUsdRate": 1.085,
        # Dollars per unit of the other currencies Gelato bills in: the ECB's cross rates of 25.09.2026 (1.1403 USD,
        # 24.345 CZK, 0.86045 GBP, 4.3718 PLN per euro); the euro keeps the Profit Calculator's rate above.
        "czkUsdRate": 0.0468, "gbpUsdRate": 1.325, "plnUsdRate": 0.2608,
        "tunnelKeepAliveSeconds": 900,
        "defaultFormat": "hardcover_8x8",
        "formats": {
            # The metric products the owner orders by hand in Gelato (20×20 cm, 14×14 cm), not the
            # inch-sized ones (203.2 / 139.7 mm) — same books, slightly different sheet sizes.
            "hardcover_8x8": {
                "label": "Hardcover 8×8",
                "productUid": "photobooks-hardcover_pf_200x200-mm-8x8-inch_pt_170-gsm-65lb-coated-silk"
                "_cl_4-4_ccl_4-4_bt_glued-left_ct_matt-lamination_prt_1-0_cpt_130-gsm-65-lb-cover-coated-silk_ver",
            },
            "softcover_8x8": {
                "label": "Softcover 8×8",
                "productUid": "photobooks-softcover_pf_200x200-mm-8x8-inch_pt_170-gsm-65lb-coated-silk"
                "_cl_4-4_ccl_4-4_bt_glued-left_ct_matt-lamination_prt_1-0_cpt_250-gsm-100-lb-cover-coated-silk_ver",
            },
            "softcover_5x5": {
                "label": "Softcover 5.5×5.5",
                "productUid": "photobooks-softcover_pf_140x140-mm-5_5x5_5-inch_pt_170-gsm-65lb-coated-silk"
                "_cl_4-4_ccl_4-4_bt_glued-left_ct_matt-lamination_prt_1-0_cpt_250-gsm-100-lb-cover-coated-silk_ver",
            },
        },
    },
    # Text check before print by a local model in Ollama (textcheck.py); only 127.0.0.1 is accepted.
    "textcheck": {"enabled": True, "model": "gemma4:12b-it-qat", "url": "http://127.0.0.1:11434",
                  "prescan": True},  # a local look first: only pages that may carry text go to the model
}

# Settings saved before 2026-09-17 still name the inch-sized Gelato products.
def _merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in (extra or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


class Settings:
    """Non-secret configuration persisted in data/settings.json."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._path = data_path("settings.json")
        self._data = _merge(DEFAULT_SETTINGS, read_json(self._path, {}) or {})

    def get(self) -> dict:
        with self._lock:
            return copy.deepcopy(self._data)

    def section(self, name: str) -> dict:
        with self._lock:
            return copy.deepcopy(self._data.get(name, {}))

    def update(self, patch: dict) -> dict:
        with self._lock:
            self._data = _merge(self._data, patch)
            write_json(self._path, self._data)
            return copy.deepcopy(self._data)

    def replace_section(self, name: str, value: dict) -> None:
        with self._lock:
            self._data[name] = copy.deepcopy(value)
            write_json(self._path, self._data)

    def drop_section(self, name: str) -> None:
        """Removes a section for good, from the backup copy too."""
        with self._lock:
            if self._data.pop(name, None) is None:
                return
            write_json(self._path, self._data, backup=False)
            bak = self._path.with_name(self._path.name + ".bak")
            old = read_json(bak, None) if bak.exists() else None
            if isinstance(old, dict) and old.pop(name, None) is not None:
                write_json(bak, old, backup=False)


settings = Settings()
