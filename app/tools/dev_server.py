"""Book Studio server for looking at the interface during development — never on the real data.

  python app/tools/dev_server.py            empty program on http://127.0.0.1:47890/
  python app/tools/dev_server.py --sample   plus made-up orders, one library book, three Workshop books and the
                                            mockups' made-up templates to click through

The data folder is .tmp\\bsdev in the repository, on drive D (or BOOK_STUDIO_DATA when it is set): no keys
there, so nothing reaches Etsy, Printify or Gelato. The mockups get made-up templates and a pretend Photoshop:
nothing real is opened, and their Windows dialogs answer by themselves. The Workshop is in the sandbox
(studio.core.SANDBOX): its books, its Downloads (a picture put into the "downloads" folder is caught) and its
clipboard (the "clipboard" folder) live in the data folder. Stop it with Ctrl+C (or preview_stop).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
PORT = int(os.environ.get("BOOK_STUDIO_DEV_PORT") or 47890)   # tools/ui_smoke.py runs its own beside the preview


MARK = ".book-studio-sample"    # this folder was made by this tool and may be written over


def claim(data: Path, default: Path) -> str | None:
    """Sample data goes only into this tool's own folder or one it made itself. Any other folder may be
    the owner's real data — a copy, a backup, a moved folder — and refusing one exact path is not enough.
    Returns the reason to stop, or None when the folder may be used (and is marked as ours)."""
    if data == (APP / "data").resolve():
        return "це справжня папка даних програми"
    if (data / "vault.json").exists():
        # Also when a key was typed into this tool's own Settings: a real key never lives in sample data,
        # and the tool does not delete keys by itself — the folder is for the owner to remove.
        return ("у ній лежать ключі (vault.json) — це не тимчасові дані. Якщо ключ зберегли в налаштуваннях "
                "тестового сервера, видаліть цю папку вручну")
    if not (data / MARK).exists() and data != default and data.exists() and any(data.iterdir()):
        return "вона не порожня й не створена цим інструментом"
    data.mkdir(parents=True, exist_ok=True)
    (data / MARK).write_text("Sample data for app/tools/dev_server.py. Delete this folder any time.\n",
                             encoding="utf-8")
    return None


def main(argv: list[str]) -> int:
    # On drive D beside the code, not in Windows' temp folder on drive C (the owner keeps drive C clean).
    default = (APP.parent / ".tmp" / "bsdev").resolve()
    data = Path(os.environ.get("BOOK_STUDIO_DATA") or default).resolve()
    stop = claim(data, default)
    if stop:
        print(f"Не чіпаю {data}: {stop}.\nВиберіть іншу папку в BOOK_STUDIO_DATA або видаліть цю.",
              file=sys.stderr)
        return 1
    os.environ["BOOK_STUDIO_DATA"] = str(data)
    os.environ["BOOK_STUDIO_SAMPLE"] = "1"  # no key is stored or offered here (studio.core.SAMPLE)
    sys.path.insert(0, str(APP))
    if "--sample" in argv:
        from sample_data import seed  # made-up orders, books, mockups (sample_data.py, sample_mockups.py)
        seed(data)
    from studio.main import main as run
    return run(["--no-window", "--port", str(PORT)])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
