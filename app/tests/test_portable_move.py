"""The portable copy keeps working when its folder moves: paths inside the data follow it; Windows prerequisites are offered quietly."""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import __init__  # noqa: F401  (a test file run alone still gets the made-up data folder)
from studio import core, portable


class Rebase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "runtime").mkdir()
        patch = mock.patch.dict(os.environ, {"BOOKSTUDIO_PORTABLE": str(self.root)})
        patch.start()
        self.addCleanup(patch.stop)
        self.addCleanup(shutil.rmtree, self.root, True)
        self.data = core.DATA_DIR
        self.addCleanup(shutil.rmtree, self.data / "slides" / "sets" / "move-test", True)
        self.addCleanup(shutil.rmtree, self.data / "rebase-backup", True)
        self.addCleanup(lambda: (self.data / "portable-state.json").unlink(missing_ok=True))
        (self.data / "portable-state.json").unlink(missing_ok=True)
        self.here = str(core.ROOT.parent)
        folder = self.data / "slides" / "sets" / "move-test"
        folder.mkdir(parents=True, exist_ok=True)
        self.file = folder / "set.json"
        self.file.write_text(json.dumps({"folder": r"D:\Old Place\Book Studio\pipeline\books\41.x\mockups",
                                        "data": r"E:\other\Book Studio Portable\Book Studio\app\data\slides",
                                        "elsewhere": r"G:\My Drive\backups"}), encoding="utf-8")
        (self.data / "logs").mkdir(exist_ok=True)
        self.log = self.data / "logs" / "move-test.json"
        self.log.write_text(json.dumps({"folder": r"D:\Old Place\Book Studio\pipeline\books\41.x"}), encoding="utf-8")
        self.addCleanup(lambda: self.log.unlink(missing_ok=True))

    def test_paths_into_the_repository_follow_the_folder(self):
        self.assertEqual(portable.rebase_paths() >= 1, True)
        got = json.loads(self.file.read_text(encoding="utf-8"))
        self.assertEqual(got["folder"], self.here + r"\pipeline\books\41.x\mockups")
        self.assertEqual(got["data"], self.here + r"\app\data\slides")
        self.assertEqual(got["elsewhere"], r"G:\My Drive\backups")          # not ours: left alone

    def test_the_old_file_is_kept_and_the_logs_are_not_touched(self):
        portable.rebase_paths()
        saved = list((self.data / "rebase-backup").rglob("set.json"))
        self.assertTrue(saved)
        self.assertIn("Old Place", saved[0].read_text(encoding="utf-8"))
        self.assertIn("Old Place", self.log.read_text(encoding="utf-8"))     # history stays as it was

    def test_it_runs_once_per_place(self):
        portable.rebase_paths()
        self.assertEqual(portable.rebase_paths(), 0)
        self.assertEqual(json.loads((self.data / "portable-state.json").read_text(encoding="utf-8"))["repo"], self.here)

    def test_nothing_happens_in_the_ordinary_install(self):
        with mock.patch.dict(os.environ, {"BOOKSTUDIO_PORTABLE": ""}):
            self.assertEqual(portable.rebase_paths(), 0)
        self.assertIn("Old Place", self.file.read_text(encoding="utf-8"))


class Prerequisites(unittest.TestCase):
    def test_a_bundled_installer_is_run_quietly(self):
        item = {"installer": r"C:\x\vc_redist.x64.exe", "winget": "Microsoft.VCRedist.2015+.x64"}
        self.assertEqual(portable.install_command(item), [r"C:\x\vc_redist.x64.exe", "/install", "/quiet", "/norestart"])

    def test_winget_is_the_way_when_nothing_is_bundled(self):
        item = {"installer": None, "winget": "Microsoft.VCRedist.2015+.x64"}
        with mock.patch("shutil.which", return_value="winget.exe"):
            command = portable.install_command(item)
        self.assertEqual(command[:3], ["winget", "install", "--id"])
        self.assertIn("--silent", command)

    def test_nothing_to_install_with_says_none(self):
        with mock.patch("shutil.which", return_value=None):
            self.assertIsNone(portable.install_command({"installer": None, "winget": "x"}))
            self.assertIsNone(portable.install({"installer": None, "winget": "x"}))

    def test_only_what_is_missing_is_listed(self):
        with mock.patch.object(portable, "vcredist_present", return_value=False):
            self.assertEqual([p["id"] for p in portable.missing_prerequisites()], ["vcredist"])
        with mock.patch.object(portable, "vcredist_present", return_value=True):
            self.assertEqual(portable.missing_prerequisites(), [])


if __name__ == "__main__":
    unittest.main()
