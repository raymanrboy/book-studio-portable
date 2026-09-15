"""Creates (or refreshes) the "Book Studio" shortcut on the Windows desktop.

Run:  python tools\\make_shortcut.py
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    if not pythonw.exists():
        pythonw = Path(sys.executable)
    desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    # The user's Desktop may be redirected (e.g. to D:\...\Desktop); ask Windows for the real one.
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"],
                             capture_output=True, text=True, check=True).stdout.strip()
        if out:
            desktop = Path(out)
    except Exception:
        pass
    link = desktop / "Book Studio.lnk"
    script = ROOT / "Book Studio.pyw"
    icon = ROOT / "web" / "img" / "icon.ico"
    ps = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:BS_LINK);"
        "$s.TargetPath=$env:BS_TARGET;"
        "$s.Arguments='\"'+$env:BS_SCRIPT+'\"';"
        "$s.WorkingDirectory=$env:BS_ROOT;"
        "$s.IconLocation=$env:BS_ICON+',0';"
        "$s.Description='Book Studio - бібліотека книг, прибуток і Order Creator';"
        "$s.Save()"
    )
    env = {**os.environ, "BS_LINK": str(link), "BS_TARGET": str(pythonw), "BS_SCRIPT": str(script),
           "BS_ROOT": str(ROOT), "BS_ICON": str(icon)}
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, env=env)
    print(f"Ярлик створено: {link}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
