"""Double-click to start «Мокапи» — listing mockups from a Canva demo book (runs without a console window)."""
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
# A data folder of its own: nothing here touches Book Studio's orders, library or keys.
DATA = ROOT / "data" / "mockups"
os.environ["BOOK_STUDIO_DATA"] = str(DATA)


def _message(title: str, text: str) -> None:
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, title, 0x10)
    except Exception:
        pass


try:
    import PIL  # noqa: F401
except ImportError:
    _message("Мокапи", "Бракує пакета Python: Pillow\n\nВстановіть його командою:\n"
             f'python -m pip install -r "{ROOT / "requirements.txt"}"')
    sys.exit(1)

try:
    from studio.mockups_app import main
    sys.exit(main())
except SystemExit:
    raise
except Exception:
    log = DATA / "logs" / "startup-error.txt"
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(traceback.format_exc(), encoding="utf-8")
    except Exception:
        pass
    _message("Мокапи — помилка запуску", traceback.format_exc()[-1500:] + f"\n\nПовний текст: {log}")
    sys.exit(1)
