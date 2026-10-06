"""Every page opened in a hidden Edge on made-up data, its tabs pressed (tools/ui_smoke.py, 06.10.2026): a script
error, a red message, an empty page or a server error fails the suite. Skipped where there is no Edge or when
BOOKSTUDIO_SKIP_UI=1 (≈25 s)."""
import importlib.util
import os
import unittest
from pathlib import Path

from tests import __init__  # noqa: F401  (sets a temporary data folder)

_spec = importlib.util.spec_from_file_location("ui_smoke", Path(__file__).resolve().parents[1] / "tools" / "ui_smoke.py")
ui_smoke = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ui_smoke)


@unittest.skipIf(os.environ.get("BOOKSTUDIO_SKIP_UI") == "1", "BOOKSTUDIO_SKIP_UI=1")
@unittest.skipUnless(os.name == "nt" and ui_smoke.find_edge(), "no Edge on this computer")
class EveryPage(unittest.TestCase):
    def test_every_page_opens_without_an_error(self):
        self.assertEqual(ui_smoke.run(), [])


if __name__ == "__main__":
    unittest.main()
