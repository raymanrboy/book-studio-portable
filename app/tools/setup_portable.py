"""Lays out a portable Book Studio folder from a clone of this repository — so the repository alone is enough to start one.

The repository is the `Book Studio/` folder. Next to it a portable folder has the launchers and `runtime/` (the programs the
program runs on: Python, ffmpeg, Photoshop, the mockup templates, Antigravity — too big and not ours to keep in git). This script:

  1. puts the launchers (`portable/*.bat`, `ПРОЧИТАЙ.md`) beside the repository and makes an empty `runtime/` with its
     sub-folders and a note on what goes into each;
  2. with `--python`: copies the Python that runs it into `runtime/python` and installs `app/requirements.txt` there (the
     only step that uses the internet: pip);
  3. with `--shortcut`: makes the «Book Studio» shortcut (tools/make_shortcut.py);
  4. says what is still missing in `runtime/`.

Run (from the repository folder):  python app/tools/setup_portable.py [--target FOLDER] [--python] [--shortcut]
Without `--target` the folder above the repository is used. Nothing here deletes or overwrites the owner's data: the launchers are
refreshed, `ПРОЧИТАЙ.md` and the notes are written only when missing.
"""
from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LAUNCHERS = REPO / "portable"
REFRESHED = ("Start Book Studio.bat", "Start with console.bat", "Make desktop shortcut.bat")   # always as the repository has them
KEPT = ("ПРОЧИТАЙ.md",)                                                                         # written only when missing
RUNTIME_FOLDERS = ("Photoshop", "Templates", "Antigravity", "ffmpeg", "Installers")
RUNTIME_NOTE = """runtime/ — the programs Book Studio runs on. They are not in the repository (too big, and some are licensed).

python/        Python 3.14 (x64) with the packages of app/requirements.txt
               → python app/tools/setup_portable.py --python   (copies the Python that runs it, then pip installs the packages)
ffmpeg/        an ffmpeg build for Windows: some folder in here must hold ffmpeg.exe (the photo mockups' video)
Photoshop/     a portable Photoshop of your own: App/Photoshop/Photoshop.exe (the mockups) — see wiki/features/mockups.md
Templates/     your mockup templates (.psd) — read-only, the program only works on copies
Antigravity/   app/Antigravity.exe — the agents that write new books; data/ and home/ are made by the program
Installers/    vc_redist.x64.exe (optional): the program offers to install the Visual C++ runtime quietly from it
Ollama/        } optional modules: the program installs them itself (Settings → Модулі),
Upscayl/       } do not put anything here by hand

What is still missing is shown by the window at the program's start, and by:  python app/tools/setup_portable.py
Everything about it: wiki/dev/portable-setup.md
"""
PYTHON_SKIP = {"__pycache__", "idlelib", "turtledemo", "Doc"}     # not needed in a copy
PYTHON_SKIP_IN_LIB = {"test", "site-packages"}                  # Python's own tests; the packages are installed afresh


def _put(src: Path, dst: Path) -> None:
    """`src` over `dst`. The owner hides the launchers (Windows refuses to write over a hidden file): the flag is lifted for the copy and
    put back."""
    hidden = os.name == "nt" and dst.exists() and bool(dst.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)
    if hidden:
        subprocess.run(["attrib", "-h", str(dst)], check=False)
    try:
        shutil.copyfile(src, dst)
    finally:
        if hidden:
            subprocess.run(["attrib", "+h", str(dst)], check=False)


def layout(target: Path) -> list[str]:
    """The launchers and an empty `runtime/` skeleton in `target`. Returns what was written."""
    done: list[str] = []
    target.mkdir(parents=True, exist_ok=True)
    for name in REFRESHED:
        src, dst = LAUNCHERS / name, target / name
        if src.is_file() and (not dst.is_file() or dst.read_bytes() != src.read_bytes()):
            _put(src, dst)
            done.append(name)
    for name in KEPT:
        src, dst = LAUNCHERS / name, target / name
        if src.is_file() and not dst.exists():
            shutil.copyfile(src, dst)
            done.append(name)
    runtime = target / "runtime"
    runtime.mkdir(exist_ok=True)
    for name in RUNTIME_FOLDERS:
        (runtime / name).mkdir(exist_ok=True)
    note = runtime / "README.txt"
    if not note.exists():
        note.write_text(RUNTIME_NOTE, encoding="utf-8")
        done.append("runtime/README.txt")
    return done


def copy_python(target: Path, source: Path | None = None) -> Path:
    """The Python that runs this script, copied into `runtime/python` (a relocatable install: python.exe, the DLLs, Lib, tcl for the
    Windows dialogs). A Microsoft Store Python cannot be moved: use the one from python.org."""
    source = Path(source or sys.base_prefix)          # a virtual environment's base is the real install: fine
    if not (source / "python.exe").is_file() or not (source / "Lib").is_dir():
        raise SystemExit(f"{source} is not a Python installation (no python.exe and Lib) — use the one from python.org.")
    dest = target / "runtime" / "python"
    if (dest / "python.exe").is_file():
        return dest

    def skip(folder: str, names: list[str]) -> list[str]:
        out = [n for n in names if n in PYTHON_SKIP]
        if Path(folder).name == "Lib":
            out += [n for n in names if n in PYTHON_SKIP_IN_LIB]
        return out

    shutil.copytree(source, dest, ignore=skip, dirs_exist_ok=True)
    (dest / "Lib" / "site-packages").mkdir(parents=True, exist_ok=True)
    return dest


def install_packages(python_dir: Path) -> None:
    """`app/requirements.txt` into that Python (pip; needs the internet)."""
    exe = python_dir / "python.exe"
    if subprocess.run([str(exe), "-m", "pip", "--version"], capture_output=True).returncode != 0:      # the copy has no packages: pip itself
        subprocess.run([str(exe), "-m", "ensurepip", "--upgrade"], check=True)                         # comes from Python's own bundled wheels
    subprocess.run([str(exe), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(REPO / "app" / "requirements.txt")],
                   check=True)


def missing(target: Path) -> list[str]:
    """What `runtime/` still lacks, in words (files only — the same places `studio/portable.py` looks)."""
    runtime = target / "runtime"
    out = []
    if not (runtime / "python" / "python.exe").is_file():
        out.append("runtime/python — Python 3.14 з пакетами: python app/tools/setup_portable.py --python")
    ffmpeg = runtime / "ffmpeg"
    if not (ffmpeg.is_dir() and next(ffmpeg.rglob("ffmpeg.exe"), None)):
        out.append("runtime/ffmpeg — збірка ffmpeg для Windows (ffmpeg.exe всередині)")
    if not any((runtime / "Photoshop").rglob("Photoshop.exe")):
        out.append("runtime/Photoshop — портативний Photoshop (App/Photoshop/Photoshop.exe)")
    templates = runtime / "Templates"
    if not (templates.is_dir() and any(templates.iterdir())):
        out.append("runtime/Templates — ваші трафарети макапів (.psd)")
    if not (runtime / "Antigravity" / "app" / "Antigravity.exe").is_file():
        out.append("runtime/Antigravity — програма агентів (app/Antigravity.exe)")
    return out


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Lays out a portable Book Studio folder from this repository.")
    parser.add_argument("--target", type=Path, default=REPO.parent, help="the portable folder (default: the folder above the repository)")
    parser.add_argument("--python", action="store_true", help="copy this Python into runtime/python and install the packages")
    parser.add_argument("--no-packages", action="store_true", help="with --python: only copy, do not run pip")
    parser.add_argument("--shortcut", action="store_true", help="make the Book Studio shortcut")
    args = parser.parse_args(argv)
    target = args.target.resolve()
    for name in layout(target):
        print(f"Записано: {target / name}")
    if args.python:
        python_dir = copy_python(target)
        print(f"Python: {python_dir}")
        if not args.no_packages:
            install_packages(python_dir)
    if args.shortcut:
        exe = target / "runtime" / "python" / "python.exe"
        subprocess.run([str(exe if exe.is_file() else sys.executable), str(REPO / "app" / "tools" / "make_shortcut.py")], check=True)
    lacking = missing(target)
    if lacking:
        print("\nЩе бракує в runtime/ (програма покаже це й у своєму вікні при старті):")
        for line in lacking:
            print(f"  •  {line}")
        return 1
    print("\nУсе на місці. Запуск: Book Studio.lnk або «Start Book Studio.bat».")
    return 0


if __name__ == "__main__":
    sys.exit(main())
