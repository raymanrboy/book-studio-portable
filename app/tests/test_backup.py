"""Backup to Google Drive: which copies stay, when the next one is due, and a real 7-Zip run on a made-up program
folder — the password protects it, the keys and the instruction are inside, what Edge holds open is left out."""
import json
import shutil
import subprocess
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import backup, core
from studio.jobs import Job, JobError
from studio.vault import vault

PASSWORD = "test-password-1"


class Rules(unittest.TestCase):
    def test_keeps_last_seven_and_one_a_month(self):
        start = datetime(2025, 1, 1, 10, 0)
        found = sorted(((start + timedelta(days=3 * i), Path(f"c{i}")) for i in range(200)), reverse=True)
        gone = set(backup.to_remove(found))
        kept = [(w, p) for w, p in found if p not in gone]
        self.assertEqual(kept[:7], found[:7])
        months = {w.strftime("%Y-%m") for w, _ in kept}
        self.assertEqual(len(months), 12)  # a year back, one a month (the newest of it)
        for month in months:
            newest = next(p for w, p in found if w.strftime("%Y-%m") == month)
            self.assertNotIn(newest, gone)
        self.assertLessEqual(len(kept), 7 + 12)

    def test_few_copies_all_stay(self):
        found = [(datetime(2026, 9, d), Path(f"c{d}")) for d in (27, 24, 21)]
        self.assertEqual(backup.to_remove(found), [])

    def test_due_every_three_days(self):
        with mock.patch.object(core.settings, "section", return_value={}):
            self.assertTrue(backup.due())
        at = time.time() - 2 * 86400
        stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(at)) + "Z"
        with mock.patch.object(core.settings, "section", return_value={"last": {"at": stamp}}):
            self.assertFalse(backup.due())
            self.assertTrue(backup.due(now=at + 3 * 86400))
            self.assertTrue(backup.due(now=at + 3 * 86400 - 1800))  # the same time of day three days on

    def test_names_of_copies(self):
        folder = Path(tempfile.mkdtemp())
        try:
            for name in ("Book Studio 2026-09-27 19-40.7z", "Book Studio 2026-09-24 08-00.7z",
                         "Book Studio 2026-09-30 10-00.7z.part", "other.7z"):
                (folder / name).write_bytes(b"x")
            self.assertEqual([p.name for _, p in backup.copies(folder)],
                             ["Book Studio 2026-09-27 19-40.7z", "Book Studio 2026-09-24 08-00.7z"])
        finally:
            shutil.rmtree(folder)

    def test_the_big_program_folder_is_packed_last(self):
        """Every later addition rewrites the archive: the program (with its books) last, so it is written once."""
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        program, templates = root / "Book Studio", root / "Трафарети"
        templates.mkdir()
        with mock.patch("studio.mockups.places", return_value={"templates": templates}), \
                mock.patch.object(backup, "PROGRAM_DIR", program):
            self.assertEqual(backup.sources(), [templates, program])

    def test_never_runs_by_itself_in_the_sandbox(self):
        with mock.patch.object(backup, "start") as start:
            backup.start_if_due()
        start.assert_not_called()


@unittest.skipUnless(backup.SEVEN_ZIP.exists(), "7za.exe is not in app/bin")
class RealArchive(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.program = self.tmp / "Book Studio"
        (self.program / "app" / "data" / "library").mkdir(parents=True)
        (self.program / "app" / "data" / "library" / "book.json").write_text('{"title": "Тест"}', encoding="utf-8")
        (self.program / "app" / "data" / "window-profile").mkdir()
        (self.program / "app" / "data" / "window-profile" / "Cookies").write_bytes(b"edge")
        (self.program / ".tmp").mkdir()
        (self.program / ".tmp" / "junk.txt").write_text("junk")
        self.templates = self.tmp / "Трафарети мастхев"
        self.templates.mkdir()
        (self.templates / "Mockup 1.psd").write_bytes(b"psd" * 100)
        self.drive = self.tmp / "drive"
        vault.set(backup.PASSWORD, PASSWORD)
        vault.set("gelato_api_key", "made-up-gelato-key")
        self.addCleanup(vault.set, backup.PASSWORD, None)
        self.addCleanup(vault.set, "gelato_api_key", None)
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for patch in (mock.patch.object(backup, "PROGRAM_DIR", self.program),
                      mock.patch.object(backup, "sources", lambda: [self.program, self.templates]),
                      mock.patch.object(backup, "target", lambda: self.drive)):
            patch.start()
            self.addCleanup(patch.stop)

    def seven(self, *args):
        return subprocess.run([str(backup.SEVEN_ZIP), *args, f"-p{PASSWORD}", "-sccUTF-8"],
                              capture_output=True, encoding="utf-8")

    def test_whole_copy_with_keys(self):
        result = backup.make(Job("backup"))
        archive = self.drive / result["file"]
        self.assertTrue(archive.exists())
        self.assertEqual(list(self.drive.glob("*.part")), [])
        listing = self.seven("l", "-slt", str(archive)).stdout
        paths = {line[7:] for line in listing.splitlines() if line.startswith("Path = ")} - {str(archive)}
        self.assertIn(backup.KEYS_FILE, paths)
        self.assertIn(backup.README_FILE, paths)
        self.assertIn(r"Book Studio\app\data\library\book.json", paths)
        self.assertIn(r"Трафарети мастхев\Mockup 1.psd", paths)
        self.assertFalse([p for p in paths if "window-profile" in p or ".tmp" in p])
        keys = json.loads(self.seven("e", "-so", str(archive), backup.KEYS_FILE).stdout)
        self.assertEqual(keys["gelato_api_key"], "made-up-gelato-key")
        self.assertNotIn(backup.PASSWORD, keys)
        self.assertEqual(core.settings.section("backup")["last"]["file"], result["file"])

    def test_wrong_password_opens_nothing(self):
        archive = self.drive / backup.make(Job("backup"))["file"]
        run = subprocess.run([str(backup.SEVEN_ZIP), "l", str(archive), "-pwrong-one"], capture_output=True)
        self.assertNotEqual(run.returncode, 0)

    def test_no_password_no_copy(self):
        vault.set(backup.PASSWORD, None)
        with self.assertRaises(JobError):
            backup.make(Job("backup"))


if __name__ == "__main__":
    unittest.main()
