"""Secret storage protected by Windows DPAPI (current Windows user).

Secrets never leave the backend: the UI only learns whether a secret is set
and its last four characters for recognition.
"""
from __future__ import annotations

import base64
import ctypes
import json
import sys
import threading
from ctypes import wintypes
from typing import Any

from . import core
from .jobs import JobError

_IS_WINDOWS = sys.platform == "win32"


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


if _IS_WINDOWS:
    _crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_Blob), wintypes.LPCWSTR, ctypes.POINTER(_Blob),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_Blob),
    ]
    _crypt32.CryptProtectData.restype = wintypes.BOOL
    _crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_Blob), ctypes.c_void_p, ctypes.POINTER(_Blob),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_Blob),
    ]
    _crypt32.CryptUnprotectData.restype = wintypes.BOOL
    _kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    _kernel32.LocalFree.restype = ctypes.c_void_p

_UI_FORBIDDEN = 0x01


def _call(fn, data: bytes, *extra) -> bytes:
    buf = ctypes.create_string_buffer(data, len(data))
    blob_in = _Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    blob_out = _Blob()
    if not fn(ctypes.byref(blob_in), *extra, None, None, None, _UI_FORBIDDEN, ctypes.byref(blob_out)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        _kernel32.LocalFree(ctypes.cast(blob_out.pbData, ctypes.c_void_p))


def protect(data: bytes) -> bytes:
    if not _IS_WINDOWS:
        return data
    return _call(_crypt32.CryptProtectData, data, "Book Studio")


def unprotect(data: bytes) -> bytes:
    if not _IS_WINDOWS:
        return data
    return _call(_crypt32.CryptUnprotectData, data, None)


def unprotect_powershell_securestring(text: str) -> str:
    """Decrypts the hex output of PowerShell `ConvertFrom-SecureString` (no key)."""
    raw = bytes.fromhex(text.strip())
    return unprotect(raw).decode("utf-16-le")


SECRET_NAMES = ("etsy_keystring", "etsy_shared_secret", "printify_token", "gelato_api_key", "gelato_old_api_key",
                "etsy_tokens", "backup_password")


class Vault:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._warned: set[str] = set()
        self._path = core.data_path("vault.json")
        self._cache: dict[str, str] = {}
        self._loaded = False

    def _load(self) -> dict:
        return core.read_json(self._path, {}) or {}

    def get(self, name: str) -> str | None:
        with self._lock:
            if name in self._cache:
                return self._cache[name]
            stored = self._load().get(name)
            if not stored:
                return None
            try:
                value = unprotect(base64.b64decode(stored)).decode("utf-8")
            except (OSError, ValueError):                 # Windows cannot open it for this user, or the stored text is damaged
                if name not in self._warned:           # once per key: every page asks for them
                    self._warned.add(name)
                    core.log.warning("Secret %s cannot be decrypted by this Windows user", name)
                return None
            self._cache[name] = value
            return value

    def set(self, name: str, value: str | None) -> None:
        if core.SAMPLE and value:
            # The preview server must stay unable to reach Etsy, Printify or Gelato (23.09.2026: its Settings
            # offered to import the owner's real keys from the old programs on the Desktop).
            raise JobError("Це тестовий сервер на вигаданих даних — ключі тут не зберігаються.")
        with self._lock:
            data = self._load()
            value = (value or "").strip()
            if value:
                data[name] = base64.b64encode(protect(value.encode("utf-8"))).decode("ascii")
                self._cache[name] = value
            else:
                data.pop(name, None)
                self._cache.pop(name, None)
            core.write_json(self._path, data)

    def get_json(self, name: str) -> Any:
        raw = self.get(name)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def set_json(self, name: str, value: Any) -> None:
        self.set(name, json.dumps(value) if value is not None else None)

    def readable(self) -> dict[str, str]:
        """Every stored secret decrypted — only for the owner's password-protected backup (backup.py, 27.09.2026:
        the vault opens for this Windows user alone, and a restore on another computer needs the keys)."""
        with self._lock:
            return {name: value for name in self._load() if (value := self.get(name))}

    def status(self, name: str) -> dict:
        value = self.get(name)
        if not value:
            return {"configured": False, "hint": ""}
        return {"configured": True, "hint": "…" + value[-4:] if len(value) > 8 else "••••"}


vault = Vault()
