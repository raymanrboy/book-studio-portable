"""Windows integration: native folder dialog, Explorer, app window."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from . import core

CREATE_NO_WINDOW = 0x08000000

# The Windows dialog in a process of its own (Tk wants its own main thread): argv = folder|file|zip, title, start folder.
_DIALOG_SCRIPT = r"""
import sys, tkinter as tk
from tkinter import filedialog
kind, title, initial = sys.argv[1], sys.argv[2], sys.argv[3] or None
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)
root.update()
if kind == 'folder':
    path = filedialog.askdirectory(parent=root, title=title, initialdir=initial, mustexist=True)
elif kind == 'zip':
    path = filedialog.askopenfilename(parent=root, title=title, initialdir=initial,
                                      filetypes=[('ZIP-архів', '*.zip')])
else:
    path = filedialog.askopenfilename(parent=root, title=title, initialdir=initial,
                                      filetypes=[('PNG', '*.png'), ('Зображення', '*.png *.jpg *.jpeg *.webp')])
root.destroy()
sys.stdout.write(path or '')
"""


def _console_python() -> str:
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        candidate = exe.with_name("python.exe")
        if candidate.exists():
            return str(candidate)
    return str(exe)


def _dialog(kind: str, title: str, initial: str) -> str | None:
    folder = initial if initial and Path(initial).is_dir() else ""
    result = subprocess.run(
        [_console_python(), "-B", "-c", _DIALOG_SCRIPT, kind, title, folder],  # -B: no .pyc written anywhere
        capture_output=True, text=True, encoding="utf-8",
        creationflags=CREATE_NO_WINDOW if os.name == "nt" else 0,
        timeout=3600,
    )
    path = (result.stdout or "").strip()
    return str(Path(path)) if path else None


def pick_folder(title: str, initial: str = "") -> str | None:
    return _dialog("folder", title, initial)


def pick_file(title: str, initial: str = "") -> str | None:
    """One picture from the computer (a page freshly downloaded from Canva), in the usual Windows dialog."""
    return _dialog("file", title, initial)


def pick_zip(title: str, initial: str = "") -> str | None:
    """A ZIP archive (a demo book exported from Canva), in the usual Windows dialog."""
    return _dialog("zip", title, initial)


def downloads_folder() -> str:
    """Where the browser saves downloads (Canva's ZIP lands there): the ZIP dialog starts there the first time."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
            value = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
        folder = Path(os.path.expandvars(value))
    except (ImportError, OSError):
        folder = Path.home() / "Downloads"
    return str(folder) if folder.is_dir() else ""


def attention(title_part: str) -> bool:
    """A long job finished while its window is behind another one (the owner watches Photoshop): the window's
    taskbar button flashes until he looks at it, and Windows plays its notification sound. Only an Edge/Chrome
    app window whose title carries `title_part` is flashed."""
    if os.name != "nt":
        return False
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    found: list[int] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def each(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            if cls.value == "Chrome_WidgetWin_1":
                size = user32.GetWindowTextLengthW(hwnd)
                text = ctypes.create_unicode_buffer(size + 1)
                user32.GetWindowTextW(hwnd, text, size + 1)
                if title_part in text.value:
                    found.append(hwnd)
        return True

    class FLASHWINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("hwnd", wintypes.HWND), ("dwFlags", wintypes.DWORD),
                    ("uCount", wintypes.UINT), ("dwTimeout", wintypes.DWORD)]

    try:
        user32.EnumWindows(each, 0)
        for hwnd in found:
            info = FLASHWINFO(ctypes.sizeof(FLASHWINFO), hwnd, 0x3 | 0xC, 0, 0)  # FLASHW_ALL | FLASHW_TIMERNOFG
            user32.FlashWindowEx(ctypes.byref(info))
        import winsound
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:  # a nicety: never worth an error
        core.log.exception("Window attention failed")
    return bool(found)


def open_in_explorer(path: Path) -> None:
    path = Path(path)
    if path.is_dir():
        os.startfile(str(path))  # noqa: S606 — folders only
    elif path.is_file():
        subprocess.Popen(["explorer", "/select,", str(path)])
    else:
        raise FileNotFoundError(str(path))


def open_image_file(path: Path) -> None:
    path = Path(path)
    if path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp") or not path.is_file():
        raise FileNotFoundError(str(path))
    os.startfile(str(path))  # noqa: S606 — images only


def find_browser() -> str | None:
    roots = [os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")]
    for rel in (r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe"):
        for root in roots:
            if root and (Path(root) / rel).exists():
                return str(Path(root) / rel)
    return None


def open_app_window(url: str) -> subprocess.Popen | None:
    """Opens the UI as a chromeless app window (Edge/Chrome --app). Falls back to the default browser."""
    browser = find_browser()
    if browser:
        profile = core.data_path("window-profile")
        args = [
            browser,
            f"--app={url}",
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-sync",
            "--disable-features=Translate,msEdgeSidebarV2,msHubApps,EdgeCollections",
            "--window-size=1480,940",
        ]
        try:
            return subprocess.Popen(args, creationflags=CREATE_NO_WINDOW if os.name == "nt" else 0)
        except OSError:
            core.log.exception("Cannot start app window")
    import webbrowser
    webbrowser.open(url)
    return None
