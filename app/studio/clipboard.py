"""The Windows clipboard, filled by the program itself — so the Workshop's next prompt is there while the owner
stays in Gemini's window — and, while a several-part paste goes on (the hero, then the prompt), two ways to put the
next part in: **Ctrl+V in Chrome itself** (the owner, 2026-09-27: "two pastes in a row") and F8, taken from Windows.

Ctrl+V isn't taken from anyone: the keys' state is only looked at (every 20 ms, and only while such a paste goes on),
nothing is caught or written down, and only a Ctrl+V while Chrome is the window in front counts. The next part goes in
a moment after V is let go — Chrome has read the clipboard by then.

In the sandbox (the preview server, the tests) the clipboard goes into files in the data folder (clipboard.txt,
clipboard.png) and the keys are only pretended: the owner's clipboard and keyboard are never touched.
"""
from __future__ import annotations

import ctypes
import io
import os
import queue
import threading
import time
from ctypes import wintypes
from pathlib import Path

from . import core
from .server import ApiError

CF_UNICODETEXT, CF_DIB = 13, 8
GMEM_MOVEABLE = 0x0002
WM_HOTKEY = 0x0312
VK_F8 = 0x77
MOD_NOREPEAT = 0x4000
HOTKEY_ID = 0xB00C
VK_CONTROL, VK_V = 0x11, 0x56
BROWSERS = ("chrome.exe",)   # where the owner has Gemini open (2026-09-27); Book Studio's own window is Edge
PASTE_SETTLE = 0.35          # seconds after V is let go before the next part goes in


def _api():
    if os.name != "nt":
        raise ApiError("Буфер обміну Windows недоступний.")
    k32, u32 = ctypes.windll.kernel32, ctypes.windll.user32
    k32.GlobalAlloc.restype = wintypes.HGLOBAL
    k32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    k32.GlobalLock.restype = wintypes.LPVOID
    k32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    k32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    k32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    u32.OpenClipboard.argtypes = [wintypes.HWND]
    u32.SetClipboardData.restype = wintypes.HANDLE
    u32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    u32.RegisterClipboardFormatW.restype = wintypes.UINT
    u32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
    return k32, u32


def sandbox_file(name: str) -> Path | None:
    """Where the sandbox's clipboard goes instead (the older one of the two files goes first); None for real."""
    if not core.SANDBOX:
        return None
    folder = core.data_path("clipboard")
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("clipboard.*"):
        old.unlink()
    return folder / name


def _put(formats: list[tuple[int, bytes]]) -> None:
    k32, u32 = _api()
    for _ in range(40):  # another program may hold the clipboard for a moment
        if u32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        raise ApiError("Буфер обміну зайнятий іншою програмою — спробуйте ще раз.")
    try:
        u32.EmptyClipboard()
        for fmt, data in formats:
            handle = k32.GlobalAlloc(GMEM_MOVEABLE, len(data))
            if not handle:
                raise ApiError("Не вдалося покласти в буфер обміну.")
            ctypes.memmove(k32.GlobalLock(handle), data, len(data))
            k32.GlobalUnlock(handle)
            if not u32.SetClipboardData(fmt, handle):
                k32.GlobalFree(handle)
                raise ApiError("Не вдалося покласти в буфер обміну.")
    finally:
        u32.CloseClipboard()


def set_text(text: str) -> None:
    fake = sandbox_file("clipboard.txt")
    if fake:
        fake.write_text(text, encoding="utf-8")
        return
    _put([(CF_UNICODETEXT, (text.replace("\r\n", "\n").replace("\n", "\r\n") + "\0").encode("utf-16-le"))])


def set_image(image) -> None:
    """A picture (a path or a Pillow image) as the two forms browsers paste: the Windows bitmap and PNG."""
    from PIL import Image
    from . import images
    im = image if isinstance(image, Image.Image) else Image.open(image)
    try:
        im.load()
        fake = sandbox_file("clipboard.png")
        if fake:
            im.save(fake, "PNG")
            return
        png = io.BytesIO()
        im.save(png, "PNG", compress_level=1)  # a throwaway copy: ~3× faster than the default, the same pixels
        bmp = io.BytesIO()
        images.flat_rgb(im).save(bmp, "BMP")
    finally:
        if im is not image:
            im.close()
    _, u32 = _api()
    _put([(CF_DIB, bmp.getvalue()[14:]), (u32.RegisterClipboardFormatW("PNG"), png.getvalue())])  # a DIB is a BMP without its file header


class PasteWatch:
    """Ctrl+V pressed in the browser and let go → `step()` says when the next part may go in. Only the keys' state
    goes in (no Windows here), so the tests can play presses through it."""

    def __init__(self, settle: float = PASTE_SETTLE):
        self.settle = settle
        self.reset()

    def reset(self) -> None:
        self.v_down = False
        self.armed = False     # V went down with Ctrl held, in the browser
        self.due = 0.0         # when the next part goes in (0 — not due)

    def step(self, ctrl: bool, v: bool, browser: bool, now: float) -> bool:
        if v and not self.v_down and ctrl and browser:
            self.armed = True
        elif not v and self.v_down and self.armed:
            self.armed, self.due = False, now + self.settle
        self.v_down = v
        if self.due and now >= self.due:
            self.due = 0.0
            return True
        return False


def _browser_in_front(u32, k32) -> bool:
    """Is the window in front one of `BROWSERS`? (Its program's file name — nothing else about it is read.)"""
    pid = wintypes.DWORD()
    u32.GetWindowThreadProcessId(u32.GetForegroundWindow(), ctypes.byref(pid))
    handle = k32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return False
    try:
        buf, size = ctypes.create_unicode_buffer(520), wintypes.DWORD(520)
        if not k32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return False
        return Path(buf.value).name.lower() in BROWSERS
    finally:
        k32.CloseHandle(handle)


class Hotkey:
    """While wanted (a several-part paste goes on): F8 registered for the whole of Windows, and Ctrl+V in the browser
    watched (`PasteWatch`); either calls `on_press` in this thread. RegisterHotKey wants the same thread for
    registering, unregistering and its messages."""

    def __init__(self, on_press):
        self.on_press = on_press
        self.commands: queue.Queue = queue.Queue()
        self.active = False      # F8 is ours
        self.failed = False      # another program holds F8
        self.paste = False       # Ctrl+V in the browser is watched
        self.fake = core.SANDBOX or os.name != "nt"
        if not self.fake:
            threading.Thread(target=self._run, name="hotkey", daemon=True).start()

    def want(self, on: bool) -> None:
        if self.fake:
            self.active = self.paste = on
        else:
            self.commands.put(on)

    def _press(self) -> None:
        try:
            self.on_press()
        except Exception:  # a press must never stop the thread
            core.log.exception("The next part of a paste failed")

    def _run(self) -> None:
        u32, k32 = ctypes.windll.user32, ctypes.windll.kernel32
        u32.GetAsyncKeyState.restype = ctypes.c_short
        u32.GetForegroundWindow.restype = wintypes.HWND
        u32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                   ctypes.POINTER(wintypes.DWORD)]
        k32.CloseHandle.argtypes = [wintypes.HANDLE]
        msg = wintypes.MSG()
        watch = PasteWatch()
        while True:
            try:
                while True:
                    on = self.commands.get_nowait()
                    if on and not self.paste:
                        self.active = bool(u32.RegisterHotKey(None, HOTKEY_ID, MOD_NOREPEAT, VK_F8))
                        self.failed = not self.active
                        self.paste = True
                        watch.reset()
                    elif not on and self.paste:
                        if self.active:
                            u32.UnregisterHotKey(None, HOTKEY_ID)
                        self.active = self.paste = False
            except queue.Empty:
                pass
            while u32.PeekMessageW(ctypes.byref(msg), None, WM_HOTKEY, WM_HOTKEY, 1):  # PM_REMOVE
                if msg.wParam == HOTKEY_ID:
                    self._press()
            if self.paste:
                v = u32.GetAsyncKeyState(VK_V) < 0
                ctrl = u32.GetAsyncKeyState(VK_CONTROL) < 0
                browser = v and ctrl and not watch.v_down and _browser_in_front(u32, k32)
                if watch.step(ctrl, v, browser, time.monotonic()):
                    self._press()
                time.sleep(0.02)
            else:
                time.sleep(0.05)
