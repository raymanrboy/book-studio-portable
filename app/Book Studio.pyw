"""Double-click to start Book Studio (runs without a console window)."""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _message(title: str, text: str, icon: int = 0x10) -> None:
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, title, icon)
    except Exception:
        pass


def _ask(title: str, text: str) -> bool:
    """A Yes/No window; True for Yes."""
    try:
        import ctypes
        return ctypes.windll.user32.MessageBoxW(None, text, title, 0x24) == 6
    except Exception:
        return False


import importlib.util

# Only found, not imported: the PDF packages are read in when a PDF is made (importing them here cost every start ~0.15 s, 04.10.2026).
missing = [package for module, package in (("PIL", "Pillow"), ("img2pdf", "img2pdf"), ("pikepdf", "pikepdf"),
                                           ("cryptography", "cryptography"))
           if importlib.util.find_spec(module) is None]

if missing:
    _message("Book Studio", "Бракує пакетів Python: " + ", ".join(missing) + "\n\nВстановіть їх командою:\n"
             f'python -m pip install -r "{ROOT / "requirements.txt"}"')
    sys.exit(1)

try:
    from studio import portable
    report = portable.startup_report()   # the portable copy: what is missing here, what to log in to (once)
    if report:
        _message("Book Studio — портативна версія", report[0], 0x30 if report[1] else 0x40)
except Exception:
    pass

try:
    from studio import portable
    for need in portable.missing_prerequisites():      # what only Windows can have (Visual C++): offered, installed quietly
        command = portable.install_command(need)
        how = (" ".join(command) if command else f"завантажте з {need['url']} і запустіть: vc_redist.x64.exe /install /quiet /norestart")
        if portable.declined(need):
            continue
        if command and _ask("Book Studio — потрібна системна програма",
                            f"Для {need['needed_by']} потрібна {need['label']}, її немає на цьому комп'ютері.\n\n"
                            "Встановити зараз — тихо, без вікон майстра? Windows попросить дозвіл.\n\n"
                            f"Те саме можна зробити самому в терміналі:\n{how}"):
            text, bad = portable.install_result(portable.install(need))
            _message("Book Studio — системна програма", text, 0x30 if bad else 0x40)
        elif command:
            portable.decline(need)                    # «ні» is remembered for this computer
        elif not command:
            _message("Book Studio — потрібна системна програма",
                     f"Для {need['needed_by']} потрібна {need['label']}. Встановіть її в терміналі:\n{how}", 0x30)
except Exception:
    pass

try:
    from studio.main import main
    sys.exit(main())
except SystemExit:
    raise
except Exception:
    log = ROOT / "data" / "logs" / "startup-error.txt"
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(traceback.format_exc(), encoding="utf-8")
    except Exception:
        pass
    _message("Book Studio — помилка запуску", traceback.format_exc()[-1500:] + f"\n\nПовний текст: {log}")
    sys.exit(1)
