"""core.write_json / read_json: the atomic write, the .bak copy."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core


class WriteJson(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.path = self.dir / "a.json"

    def test_the_bak_is_the_state_before_the_write(self):
        core.write_json(self.path, {"n": 1})
        core.write_json(self.path, {"n": 2})
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), {"n": 2})
        self.assertEqual(json.loads(self.path.with_name("a.json.bak").read_text(encoding="utf-8")), {"n": 1})
        self.assertEqual([p.name for p in self.dir.iterdir() if p.suffix in (".tmp", ".part")], [])

    def test_a_damaged_main_file_does_not_replace_the_good_bak(self):
        core.write_json(self.path, {"n": 1})
        core.write_json(self.path, {"n": 2})                         # .bak = n 1
        self.path.write_text("{ damaged", encoding="utf-8")
        core.write_json(self.path, {"n": 3})
        self.assertEqual(json.loads(self.path.with_name("a.json.bak").read_text(encoding="utf-8")), {"n": 1})

    def test_a_failed_write_leaves_no_temp_file(self):
        core.write_json(self.path, {"n": 1})
        with mock.patch.object(core, "replace_file", side_effect=OSError("locked")):
            with self.assertRaises(OSError):
                core.write_json(self.path, {"n": 2})
        self.assertEqual([p.name for p in self.dir.iterdir() if p.name.endswith(".tmp")], [])
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), {"n": 1})


if __name__ == "__main__":
    unittest.main()
