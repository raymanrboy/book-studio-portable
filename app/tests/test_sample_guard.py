"""The made-up data (tools/sample_data.py) never lands in a data folder that is not its own."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import sample_data  # noqa: E402


class SeedGuard(unittest.TestCase):
    def test_a_seed_for_another_folder_than_the_one_studio_works_with_is_refused_and_writes_nothing(self):
        """04.10.2026: a wrapper imported `studio.core` before the made-up folder was named — the made-up orders overwrote the real
        snapshot and send journal. The seed now checks which folder `studio.core` really uses."""
        other = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, other, True)
        before = sorted(p.name for p in core.DATA_DIR.rglob("*"))
        with self.assertRaises(SystemExit):
            sample_data.seed(other)
        self.assertEqual(sorted(p.name for p in core.DATA_DIR.rglob("*")), before)     # nothing written where studio.core points
        self.assertEqual(list(other.iterdir()), [])                                    # nor in the folder it was told about


if __name__ == "__main__":
    unittest.main()
