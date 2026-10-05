"""The order archive's same pages kept once: every archived page another book already holds becomes a hard link to that one.

14 of a book's ~31 pages are the same illustrations in every child's order, and Canva signs each export with its own text, so they were
kept again and again (~6 of 13 GB on 04.10.2026). New sends are kept once by `archive.store()`; this tool does it for what is there.

  python app/tools/archive_dedupe.py            what it would save (changes nothing)
  python app/tools/archive_dedupe.py --apply    do it: the replaced files go to the Recycle Bin (the space comes back when it is emptied)

Close Book Studio first. It works on `app/data` of this copy, or on BOOK_STUDIO_DATA when that is set.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
os.environ.setdefault("BOOK_STUDIO_DATA", str(APP / "data"))      # set before `studio` is imported: it fixes its folder then
sys.path.insert(0, str(APP))


def _running() -> bool:
    """Book Studio on this data is open: its one-copy lock exists."""
    if os.name != "nt":
        return False
    import ctypes
    from studio import core
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenMutexW.restype = ctypes.c_void_p
    handle = kernel.OpenMutexW(0x00100000, False, "Local\\BookStudio-" + core.data_id())    # SYNCHRONIZE
    if handle:
        kernel.CloseHandle(ctypes.c_void_p(handle))
    return bool(handle)


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    from studio import archive, core, desktop
    apply = "--apply" in argv
    if apply and _running():
        print("Спершу закрийте Book Studio.")
        return 1
    print(f"Архів: {archive.ROOT}")
    print("Читаю сторінки (уперше — близько хвилини)…", flush=True)
    aside = core.data_path("merge-backup", time.strftime("%Y%m%d-%H%M%S") + "-archive-dedupe")
    done = archive.dedupe(apply=apply, aside=aside)
    gb = done["bytes"] / 1024 ** 3
    if not apply:
        print(f"Можна звільнити {gb:.1f} ГБ: {done['files']} однакових сторінок у {done['books']} книгах. Зробити: додайте --apply")
        return 0
    print(f"Готово: {done['files']} сторінок у {done['books']} книгах тепер одна копія ({gb:.1f} ГБ).")
    for line in done["skipped"]:
        print("  не змінено (файл відкритий):", line)
    if aside.is_dir():
        try:
            desktop.to_recycle_bin(aside)
            print("Старі копії — у Кошику: місце звільниться, коли його очистите.")
        except OSError as err:
            print(f"Старі копії лишились у {aside} ({err}). Видаліть цю папку, коли переконаєтесь, що все гаразд.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
