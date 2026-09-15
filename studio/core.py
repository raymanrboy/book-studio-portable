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
    ensure_dirs()
    root = logging.getLogger()
    if any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        return
    handler = RotatingFileHandler(data_path("logs", "app.log"), maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def new_id() -> str:
    return uuid.uuid4().hex


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z"


# ---------------------------------------------------------------- JSON files

def read_json(path: Path, default: Any = None) -> Any:
    """Reads JSON; falls back to the .bak copy when the main file is damaged."""
    for candidate in (path, path.with_name(path.name + ".bak")):
        try:
            with open(candidate, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except FileNotFoundError:
            continue
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
            _replace(path, path.with_name(path.name + ".bak"), copy_only=True)
        except OSError:
            pass
    _replace(tmp, path)


def _replace(src: Path, dst: Path, copy_only: bool = False) -> None:
    # Windows can briefly lock files (antivirus, indexer) — retry a few times.
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
        "pageCount": 30,
        "currency": "USD",
        "eurUsdRate": 1.085,
        "tunnelKeepAliveSeconds": 900,
        "defaultFormat": "hardcover_8x8",
        "formats": {
            "hardcover_8x8": {
                "label": "Hardcover 8×8",
                "productUid": "photobooks-hardcover_pf_8x8-inch-200x200-mm_pt_170-gsm-65lb-coated-silk"
                "_cl_4-4_ccl_4-4_bt_glued-left_ct_matt-lamination_prt_1-0_cpt_130-gsm-65-lb-cover-coated-silk_ver",
            },
            "softcover_8x8": {
                "label": "Softcover 8×8",
                "productUid": "photobooks-softcover_pf_8x8-inch-200x200-mm_pt_170-gsm-65lb-coated-silk"
                "_cl_4-4_ccl_4-4_bt_glued-left_ct_matt-lamination_prt_1-0_cpt_250-gsm-100-lb-cover-coated-silk_ver",
            },
            "softcover_5x5": {
                "label": "Softcover 5.5×5.5",
                "productUid": "photobooks-softcover_pf_5_5x5_5-inch-140x140-mm_pt_170-gsm-65lb-coated-silk"
                "_cl_4-4_ccl_4-4_bt_glued-left_ct_matt-lamination_prt_1-0_cpt_250-gsm-100-lb-cover-coated-silk_ver",
            },
        },
    },
    "creator": {
        "mode": "printify",
        "printifyFolder": "",
        "gelatoFolder": "",
        "gelatoFormat": "hardcover_8x8",
        "gelatoAddress": {
            "firstName": "", "lastName": "", "addressLine1": "", "addressLine2": "",
            "city": "", "state": "", "postCode": "", "country": "US", "phone": "",
        },
    },
}


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


settings = Settings()
