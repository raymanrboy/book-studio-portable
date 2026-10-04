"""The data folder's history: what versions of its files are kept, and putting one back.

Every write of an important file (the send journal, the settings, the keys' store, a book, an archive entry …) first keeps the file as it
was in `app/data/history/<path>/<time>.json` (the last 20), and once a day the whole set is copied to `app/data/history/daily/<date>/`
(the last 14 days) — `studio/core.py` `keep_history()` and `daily_snapshot()`. This tool reads that history and restores from it.

  python app/tools/data_history.py list                      every file with versions, and the daily snapshots
  python app/tools/data_history.py list print-orders         only paths containing that text
  python app/tools/data_history.py restore profit/print-orders.json                 the newest kept version
  python app/tools/data_history.py restore profit/print-orders.json --version 20261004-132145-512     a chosen one (a name from `list`)
  python app/tools/data_history.py restore profit/print-orders.json --daily 2026-10-03               the file as the daily snapshot has it

A restore never overwrites without keeping: the current file is first put into the history as a version of its own. Close Book Studio first
(a running program may write the file again). Run it with the data folder of the program in question: `BOOK_STUDIO_DATA=<folder>` or,
by default, `app/data` of this copy.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

APP = Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    return Path(os.environ.get("BOOK_STUDIO_DATA") or APP / "data").resolve()


def versions(data: Path) -> dict[str, list[Path]]:
    """path (relative to the data folder) -> its kept versions, oldest first."""
    out: dict[str, list[Path]] = {}
    base = data / "history"
    if not base.is_dir():
        return out
    for folder in sorted(p for p in base.rglob("*") if p.is_dir()):
        files = sorted(f for f in folder.glob("*.json") if f.is_file())
        if files and "daily" not in folder.relative_to(base).parts:
            out[folder.relative_to(base).as_posix()] = files
    return out


def dailies(data: Path) -> list[str]:
    base = data / "history" / "daily"
    return sorted(p.name for p in base.iterdir() if p.is_dir()) if base.is_dir() else []


def keep_current(data: Path, rel: str) -> Path | None:
    """The file as it is now goes into the history before anything replaces it."""
    current = data / rel
    if not current.is_file():
        return None
    folder = data / "history" / rel
    folder.mkdir(parents=True, exist_ok=True)
    kept = folder / (time.strftime("%Y%m%d-%H%M%S") + "-before-restore.json")
    shutil.copy2(current, kept)
    return kept


def restore(data: Path, rel: str, version: str | None = None, daily: str | None = None) -> str:
    if daily:
        source = data / "history" / "daily" / daily / rel
        if not source.is_file():
            raise SystemExit(f"Немає {rel} у знімку за {daily}. Дні: {', '.join(dailies(data)) or '—'}")
    else:
        have = versions(data).get(rel) or []
        if not have:
            raise SystemExit(f"Історії для {rel} немає. Подивіться: data_history.py list")
        if version:
            match = [p for p in have if p.stem == version or p.name == version]
            if not match:
                raise SystemExit(f"Немає версії {version}. Є: {', '.join(p.stem for p in have)}")
            source = match[0]
        else:
            source = have[-1]
    aside = keep_current(data, rel)
    target = data / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return f"Повернуто {rel} ← {source.relative_to(data / 'history').as_posix()}" + (f" (поточний файл збережено: {aside.name})" if aside else "")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Історія файлів даних Book Studio.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("text", nargs="?", default="")
    rs = sub.add_parser("restore")
    rs.add_argument("path")
    rs.add_argument("--version")
    rs.add_argument("--daily")
    args = parser.parse_args(argv)
    data = data_dir()
    if args.cmd == "list":
        found = versions(data)
        shown = 0
        for rel, files in found.items():
            if args.text in rel:
                shown += 1
                print(f"{rel}: {len(files)} версій — {files[0].stem} … {files[-1].stem}")
        days = dailies(data)
        print(f"\nЩоденні знімки ({len(days)}): {', '.join(days) or '—'}")
        if not shown:
            print("Історії файлів поки немає (вона з'являється, коли програма щось записує).")
        return 0
    print(restore(data, args.path.replace("\\", "/"), args.version, args.daily))
    return 0


if __name__ == "__main__":
    sys.exit(main())
