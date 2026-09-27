"""The Windows clipboard, filled by the program itself — so the Workshop's next prompt is there while the owner
stays in Gemini's window — and F8, taken from Windows only while a several-part paste goes on (a picture, then the
prompt), to put the next part in.

In the sandbox (the preview server, the tests) the clipboard goes into files in the data folder (clipboard.txt,
clipboard.png) and F8 is only pretended: the owner's clipboard and keyboard are never touched.
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


class Hotkey:
    """F8 registered for the whole of Windows only while wanted; a press calls `on_press` in this thread.
    RegisterHotKey wants the same thread for registering, unregistering and its messages."""

    def __init__(self, on_press):
        self.on_press = on_press
        self.commands: queue.Queue = queue.Queue()
        self.active = False
        self.failed = False      # another program holds F8
        self.fake = core.SANDBOX or os.name != "nt"
        if not self.fake:
            threading.Thread(target=self._run, name="hotkey", daemon=True).start()

    def want(self, on: bool) -> None:
        if self.fake:
            self.active = on
        else:
            self.commands.put(on)

    def _run(self) -> None:
        u32 = ctypes.windll.user32
        msg = wintypes.MSG()
        while True:
            try:
                while True:
                    on = self.commands.get_nowait()
                    if on and not self.active:
                        self.active = bool(u32.RegisterHotKey(None, HOTKEY_ID, MOD_NOREPEAT, VK_F8))
                        self.failed = not self.active
                    elif not on and self.active:
                        u32.UnregisterHotKey(None, HOTKEY_ID)
                        self.active = False
            except queue.Empty:
                pass
            while u32.PeekMessageW(ctypes.byref(msg), None, WM_HOTKEY, WM_HOTKEY, 1):  # PM_REMOVE
                if msg.wParam == HOTKEY_ID:
                    try:
                        self.on_press()
                    except Exception:  # a press must never stop the thread
                        core.log.exception("F8 failed")
            time.sleep(0.05)
