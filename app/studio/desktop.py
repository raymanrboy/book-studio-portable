"""Windows integration: native file and folder dialogs, Explorer, the Recycle Bin, app window."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from . import core

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0     # a child process without a console window (0 elsewhere)

# The Windows dialog in a process of its own (Tk wants its own main thread):
# argv = folder|file|zip|save, title, start folder[, the file name «Зберегти як» suggests].
_DIALOG_SCRIPT = r"""
import sys, tkinter as tk
from tkinter import filedialog
kind, title, initial = sys.argv[1], sys.argv[2], sys.argv[3] or None
name = sys.argv[4] if len(sys.argv) > 4 else ''
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)
root.update()
if kind == 'folder':
    path = filedialog.askdirectory(parent=root, title=title, initialdir=initial, mustexist=True)
elif kind == 'save':
    ext = name[name.rfind('.'):] if '.' in name else '.png'
    path = filedialog.asksaveasfilename(parent=root, title=title, initialdir=initial, initialfile=name,
                                        defaultextension=ext, filetypes=[('Файл ' + ext, '*' + ext)])
elif kind == '7z':
    path = filedialog.askopenfilename(parent=root, title=title, initialdir=initial,
                                      filetypes=[('Налаштування Book Studio', '*.7z')])
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


def _dialog(kind: str, title: str, initial: str, name: str = "") -> str | None:
    folder = initial if initial and Path(initial).is_dir() else ""
    result = subprocess.run(
        [_console_python(), "-B", "-X", "utf8", "-c", _DIALOG_SCRIPT, kind, title, folder, name],  # -B: no .pyc written anywhere
        capture_output=True, text=True, encoding="utf-8",
        creationflags=CREATE_NO_WINDOW,
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


def pick_7z(title: str, initial: str = "") -> str | None:
    """A 7-Zip file (the exported settings), in the usual Windows dialog."""
    return _dialog("7z", title, initial)


def save_file(title: str, name: str, initial: str = "") -> str | None:
    """Where to save a copy of a file («Зберегти як…»), in the usual Windows dialog; None when it was closed."""
    return _dialog("save", title, initial or str(Path.home() / "Pictures"), name)


def to_recycle_bin(path: Path) -> None:
    """A file or a whole folder into the Windows Recycle Bin — restorable from there until it is emptied: the owner's
    things are never deleted for good. The sandbox (the preview, the tests) moves it into its data folder instead."""
    path = Path(path)
    if core.SANDBOX:
        import shutil
        import time
        folder = core.data_path("recycle-bin")
        folder.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(folder / f"{path.name}-{time.strftime('%Y%m%d-%H%M%S')}"))
        return
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT), ("pFrom", wintypes.LPCWSTR),
                    ("pTo", wintypes.LPCWSTR), ("fFlags", ctypes.c_uint16), ("fAnyOperationsAborted", wintypes.BOOL),
                    ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", wintypes.LPCWSTR)]
    FO_DELETE, FOF_SILENT, FOF_ALLOWUNDO, FOF_NOERRORUI, FOF_WANTNUKEWARNING = 3, 0x4, 0x40, 0x400, 0x4000
    op = SHFILEOPSTRUCTW(None, FO_DELETE, str(path.resolve()) + "\0", None,
                         FOF_ALLOWUNDO | FOF_SILENT | FOF_NOERRORUI | FOF_WANTNUKEWARNING, False, None, None)
    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    if result != 0 or op.fAnyOperationsAborted or path.exists():
        raise OSError(f"Windows не дав перенести «{path.name}» у Кошик (код {result}) — можливо, якийсь файл відкритий "
                      "в іншій програмі. Закрийте його і спробуйте ще раз.")


def file_holders(path: Path) -> list[str]:
    """Which programs have this file open right now — Windows' Restart Manager tells (the names it shows, e.g.
    «Провідник Windows», «Google Chrome»); empty when nobody or it can't tell. Nothing is closed or changed."""
    if os.name != "nt":
        return []
    import ctypes
    from ctypes import wintypes

    class _Unique(ctypes.Structure):
        _fields_ = [("pid", wintypes.DWORD), ("start", wintypes.FILETIME)]

    class _Info(ctypes.Structure):
        _fields_ = [("process", _Unique), ("app", ctypes.c_wchar * 256), ("service", ctypes.c_wchar * 64),
                    ("type", ctypes.c_int), ("status", wintypes.ULONG), ("session", wintypes.DWORD),
                    ("restartable", wintypes.BOOL)]

    rm = ctypes.WinDLL("rstrtmgr")
    handle, key = wintypes.DWORD(), ctypes.create_unicode_buffer(33)
    if rm.RmStartSession(ctypes.byref(handle), 0, key):
        return []
    try:
        files = (wintypes.LPCWSTR * 1)(str(path))
        if rm.RmRegisterResources(handle, 1, files, 0, None, 0, None):
            return []
        needed, count, reasons = ctypes.c_uint(), ctypes.c_uint(0), wintypes.DWORD()
        infos = None
        for _ in range(3):  # the list may grow between asking its size and taking it
            infos = (_Info * max(count.value, 1))()
            res = rm.RmGetList(handle, ctypes.byref(needed), ctypes.byref(count), infos, ctypes.byref(reasons))
            if res == 0:
                break
            if res != 234:  # ERROR_MORE_DATA
                return []
            count.value = needed.value
        else:
            return []
        names = []
        for info in infos[:count.value]:
            name = info.app or f"процес {info.process.pid}"
            if info.process.pid == os.getpid():
                name = f"{name} (сама Book Studio)"
            if name not in names:
                names.append(name)
        return names
    except OSError:
        return []
    finally:
        rm.RmEndSession(handle)


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
    if path.suffix.lower() not in core.IMAGE_EXTS or not path.is_file():
        raise FileNotFoundError(str(path))
    os.startfile(str(path))  # noqa: S606 — images only


def find_browser() -> str | None:
    roots = [os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")]
    for rel in (r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe"):
        for root in roots:
            if root and (Path(root) / rel).exists():
                return str(Path(root) / rel)
    return None


# Edge keeps downloading and storing things the program has no use for: component updates, its shopping, wallet and entity models
# (~400 MB in each of the two profiles by 05.10.2026). Not asked for any more, and what is already there goes when no window holds the profile.
QUIET_EDGE = ["--disable-component-update", "--disable-background-networking"]
_EDGE_JUNK = ("component_crx_cache", "ProvenanceData", "Edge Entity Extraction", "Edge Shopping", "Edge Wallet")


def trim_profile(profile: Path) -> int:
    """Removes what Edge stored in a profile of ours that only it needs (it makes it again when it wants it). Only while no window
    holds the profile (Edge keeps `lockfile` there then). Returns how many folders went. Never raises."""
    import shutil
    removed = 0
    try:
        if (profile / "lockfile").exists():
            return 0
        for name in _EDGE_JUNK:
            if (profile / name).is_dir():
                shutil.rmtree(profile / name, ignore_errors=True)
                removed += 1
    except OSError:
        core.log.warning("Edge profile not trimmed", exc_info=True)
    return removed


def open_app_window(url: str) -> subprocess.Popen | None:
    """Opens the UI as a chromeless app window (Edge/Chrome --app). Falls back to the default browser."""
    browser = find_browser()
    if browser:
        profile = core.data_path("window-profile")
        trim_profile(profile)
        args = [
            browser,
            f"--app={url}",
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-sync",
            *QUIET_EDGE,
            # No throttling of a window that another program covers or that is in the background: its page's heartbeat (every 20 s)
            # must keep coming, or the program takes a covered window for a closed one and shuts down (04.10.2026).
            "--disable-features=Translate,msEdgeSidebarV2,msHubApps,EdgeCollections,CalculateNativeWinOcclusion",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--window-size=1480,940",
        ]
        try:
            return subprocess.Popen(args, creationflags=CREATE_NO_WINDOW)
        except OSError:
            core.log.exception("Cannot start app window")
    import webbrowser
    webbrowser.open(url)
    return None
