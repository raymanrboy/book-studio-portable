"""Temporary public file link for Gelato (Gelato downloads print files only by URL).

A tiny local HTTP server exposes exactly the files of one draft; a Cloudflare
quick tunnel (bin/cloudflared.exe, no account needed) gives it a temporary
https://*.trycloudflare.com address. Both stop after the keep-alive period or
when the operator closes the tunnel.
"""
from __future__ import annotations

import functools
import os
import re
import shutil
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import core

CLOUDFLARED = core.BIN_DIR / "cloudflared.exe"
_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
CREATE_NO_WINDOW = 0x08000000


class TunnelError(Exception):
    pass


_job = None  # the Windows job every cloudflared of this run belongs to; closed only when Book Studio ends


def _ends_with_us(proc: subprocess.Popen) -> None:
    """cloudflared goes when Book Studio goes, even when Book Studio is killed or crashes (22.09.2026 audit):
    it is put in a Windows job object that closes its processes with the last handle to it — ours. Where
    that cannot be done, stop() and close_all() still end it on a normal exit."""
    global _job
    if os.name != "nt":
        return
    try:
        import ctypes
        from ctypes import wintypes

        class Basic(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class Extended(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", Basic), ("IoInfo", ctypes.c_uint64 * 6),
                        ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        if _job is None:
            job = kernel32.CreateJobObjectW(None, None)
            if not job:
                raise ctypes.WinError(ctypes.get_last_error())
            info = Extended()
            info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not kernel32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):  # extended limits
                raise ctypes.WinError(ctypes.get_last_error())
            _job = job
        if not kernel32.AssignProcessToJobObject(_job, int(proc._handle)):
            raise ctypes.WinError(ctypes.get_last_error())
    except Exception:
        core.log.warning("cloudflared is not tied to Book Studio's lifetime", exc_info=True)


class _FilesOnly(SimpleHTTPRequestHandler):
    allowed: tuple[str, ...] = ()

    def log_message(self, format, *args):
        pass

    def list_directory(self, path):  # never expose a listing
        self.send_error(404)
        return None

    def send_head(self):
        name = self.path.split("?", 1)[0].lstrip("/")
        if name not in self.allowed:
            self.send_error(404)
            return None
        return super().send_head()


class FileTunnel:
    def __init__(self, folder: Path, files: tuple[str, ...]):
        self.folder = Path(folder).resolve()
        self.files = files
        self.public_url: str | None = None
        self.reachable: bool | None = None  # did the file answer from outside before the draft was made
        self._httpd: ThreadingHTTPServer | None = None
        self._proc: subprocess.Popen | None = None

    def start(self, timeout: float = 40.0) -> str:
        if not CLOUDFLARED.exists():
            raise TunnelError(f"Не знайдено {CLOUDFLARED}. Покладіть cloudflared.exe у папку bin програми.")
        handler = functools.partial(type("H", (_FilesOnly,), {"allowed": self.files}), directory=str(self.folder))
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self._httpd.serve_forever, daemon=True).start()
        local = f"http://127.0.0.1:{self._httpd.server_address[1]}"
        self._proc = subprocess.Popen(
            [str(CLOUDFLARED), "tunnel", "--url", local, "--no-autoupdate"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
            creationflags=CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        _ends_with_us(self._proc)
        found = threading.Event()

        def reader() -> None:
            assert self._proc and self._proc.stdout
            for line in self._proc.stdout:
                m = _URL_RE.search(line)
                if m and not self.public_url:
                    self.public_url = m.group(0)
                    found.set()

        threading.Thread(target=reader, daemon=True).start()
        if not found.wait(timeout):
            self.stop()
            raise TunnelError("Cloudflare не видав тимчасову адресу за відведений час. Перевірте інтернет і спробуйте ще раз.")
        # The address is announced slightly before it starts routing — verify it actually serves a file.
        self._wait_reachable()
        return self.public_url

    def _wait_reachable(self) -> None:
        deadline = time.time() + 25
        probe = f"{self.public_url}/{self.files[0]}"
        tries = 0
        while time.time() < deadline:
            tries += 1
            # The home router often has not heard of a brand-new trycloudflare name yet (while Gelato's
            # resolvers have), so from the third try the address is also asked from public DNS.
            if _head_ok(probe) or (tries >= 3 and _head_ok_public_dns(probe)):
                self.reachable = True
                return
            time.sleep(1.5)
        self.reachable = False
        core.log.warning("Tunnel %s not confirmed reachable; continuing", self.public_url)

    def stop(self) -> None:
        if self._proc:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None
        if self._httpd:
            try:
                self._httpd.shutdown()
                self._httpd.server_close()
            except Exception:
                pass
            self._httpd = None


def _head_ok(url: str) -> bool:
    import urllib.request
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "BookStudio"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status == 200
    except Exception:
        return False


def _head_ok_public_dns(url: str) -> bool:
    """The same check with the address taken from Cloudflare's public DNS (1.1.1.1, DNS over HTTPS)."""
    import http.client
    import json
    import socket
    import ssl
    import urllib.parse
    import urllib.request
    parts = urllib.parse.urlsplit(url)
    host = parts.hostname or ""
    try:
        req = urllib.request.Request(f"https://1.1.1.1/dns-query?name={host}&type=A",
                                     headers={"accept": "application/dns-json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            addresses = [a["data"] for a in json.load(resp).get("Answer") or [] if a.get("type") == 1]
        for ip in addresses[:2]:
            raw = socket.create_connection((ip, 443), timeout=8)
            conn = http.client.HTTPSConnection(host, timeout=8)
            conn.sock = ssl.create_default_context().wrap_socket(raw, server_hostname=host)
            try:
                conn.request("HEAD", parts.path or "/", headers={"User-Agent": "BookStudio"})
                if conn.getresponse().status == 200:
                    return True
            finally:
                conn.close()
    except Exception:
        pass
    return False


class TunnelRegistry:
    """Keeps draft tunnels alive for a while so Gelato can fetch the files."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: dict[str, dict] = {}

    def keep(self, key: str, tunnel: FileTunnel, folder: Path, seconds: int) -> None:
        with self._lock:
            self._items[key] = {"tunnel": tunnel, "folder": folder, "until": time.time() + seconds}
        threading.Thread(target=self._expire, args=(key, seconds), daemon=True).start()

    def _expire(self, key: str, seconds: int) -> None:
        time.sleep(seconds)
        self.close(key)

    def close(self, key: str) -> bool:
        with self._lock:
            entry = self._items.pop(key, None)
        if not entry:
            return False
        entry["tunnel"].stop()
        shutil.rmtree(entry["folder"], ignore_errors=True)
        core.log.info("Tunnel for %s closed", key)
        return True

    def active(self) -> list[dict]:
        with self._lock:
            return [{"key": k, "secondsLeft": max(0, int(v["until"] - time.time()))} for k, v in self._items.items()]

    def close_all(self) -> None:
        for key in list(self._items):
            self.close(key)


registry = TunnelRegistry()


def cleanup_stale() -> None:
    root = core.data_path("tmp", "gelato")
    if root.exists():
        for folder in root.iterdir():
            shutil.rmtree(folder, ignore_errors=True)
