"""The interface's scripts parse as the ES modules they are. There are no browser tests; this catches a script that
would not even load (an identifier declared twice made the Order Creator a blank page, 27.09.2026). `node --check` on
a .js file doesn't parse it as a module, so each is checked as a copy named .mjs. Skipped where Node.js isn't installed."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import __init__  # noqa: F401  (sets a temporary data folder)

WEB = Path(__file__).resolve().parents[1] / "web" / "js"


@unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
class ScriptsParse(unittest.TestCase):
    def test_every_script_is_a_valid_module(self):
        scripts = sorted(WEB.rglob("*.js"))
        self.assertGreater(len(scripts), 10)
        with tempfile.TemporaryDirectory() as d:
            for script in scripts:
                copy = Path(d) / f"{script.stem}.mjs"
                shutil.copyfile(script, copy)
                result = subprocess.run(["node", "--check", str(copy)], capture_output=True, text=True, timeout=60)
                with self.subTest(script=script.relative_to(WEB).as_posix()):
                    self.assertEqual(result.returncode, 0, result.stderr.strip()[-600:])


if __name__ == "__main__":
    unittest.main()
