"""Windows integration: native folder dialog, Explorer, app window."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from . import core

CREATE_NO_WINDOW = 0x08000000

# The Windows dialog in a process of its own (Tk wants its own main thread): argv = folder|file, title, start folder.
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
        [_console_python(), "-c", _DIALOG_SCRIPT, kind, title, folder],
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
