"""Double-click to start Book Studio (runs without a console window)."""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _message(title: str, text: str) -> None:
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, title, 0x10)
    except Exception:
        pass


missing = []
for module, package in (("PIL", "Pillow"), ("img2pdf", "img2pdf"), ("cryptography", "cryptography")):
    try:
        __import__(module)
    except ImportError:
        missing.append(package)

if missing:
    _message("Book Studio", "Бракує пакетів Python: " + ", ".join(missing) + "\n\nВстановіть їх командою:\n"
             f'python -m pip install -r "{ROOT / "requirements.txt"}"')
    sys.exit(1)

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
