"""Creates (or refreshes) the desktop shortcut "Book Studio" (the mockups live inside it since 24.09.2026).

Run:  python tools\\make_shortcut.py
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# name on the desktop, the script it starts, its icon, the tooltip. Windows' shortcut maker (WScript) keeps
# only the ANSI code page: a Cyrillic tooltip or path turns into "?????" — the tooltips are Latin, the scripts
# have Latin names, and a Cyrillic shortcut name is given by renaming the saved file.
SHORTCUTS = [
    ("Book Studio", "Book Studio.pyw", "icon.ico", "Book Studio - orders and listings: library, Workshop, mockups"),
]
if (ROOT.parent.parent / "runtime").is_dir():    # the portable copy: its own shortcut, the original's is left alone
    SHORTCUTS = [("Book Studio Portable", script, icon, note) for _, script, icon, note in SHORTCUTS]


HELPERS = ("Start Book Studio.bat", "Start with console.bat", "Make desktop shortcut.bat", "ПРОЧИТАЙ.md", "ROADMAP.md")


def tidy(root: Path) -> list[str]:
    """The portable folder shows only `Book Studio.lnk`, `Book Studio/` and `runtime/`: the launchers and the notes in its root get
    the Hidden attribute (Explorer → View → Hidden items shows them). Returns the names hidden. Nothing is moved or deleted."""
    done = []
    for name in HELPERS:
        path = root / name
        if path.is_file():
            subprocess.run(["attrib", "+h", str(path)], check=False)
            done.append(name)
    return done


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
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
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "[Console]::OutputEncoding=[Text.Encoding]::UTF8; [Environment]::GetFolderPath('Desktop')"],
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()   # a Cyrillic user name survives
        if out:
            desktop = Path(out)
    except Exception:
        pass
    ps = (
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:BS_LINK);"
        "$s.TargetPath=$env:BS_TARGET;"
        "$s.Arguments='\"'+$env:BS_SCRIPT+'\"';"
        "$s.WorkingDirectory=$env:BS_ROOT;"
        "$s.IconLocation=$env:BS_ICON+',0';"
        "$s.Description=$env:BS_NOTE;"
        "$s.Save()"
    )
    places = [desktop]
    if (ROOT.parent.parent / "runtime").is_dir():    # the portable copy: also one inside its own folder, the only thing the owner opens
        places.append(ROOT.parent.parent)
    for place, (name, script, icon, note) in ((w, s) for w in places for s in SHORTCUTS):
        link = place / ("Book Studio.lnk" if place != desktop else f"{name}.lnk")
        saved = link if link.name.isascii() else place / "book-studio-shortcut.lnk"
        env = {**os.environ, "BS_LINK": str(saved), "BS_TARGET": str(pythonw), "BS_SCRIPT": str(ROOT / script),
               "BS_ROOT": str(ROOT), "BS_ICON": str(ROOT / "web" / "img" / icon), "BS_NOTE": note}
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, env=env)
        if saved != link:
            os.replace(saved, link)
        print(f"Ярлик створено: {link}")
    root = ROOT.parent.parent
    if "--tidy" in argv and (root / "runtime").is_dir() and (root / "Book Studio.lnk").is_file():     # first start: the shortcut is there, the rest hides
        print("Сховано службові файли: " + ", ".join(tidy(root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
