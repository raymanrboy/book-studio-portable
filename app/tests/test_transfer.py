"""Exporting and importing the settings and keys (transfer.py): one file under the backup password."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import __init__  # noqa: F401  (a test file run alone still gets the made-up data folder)
from studio import backup, core, transfer
from studio.server import ApiError
from studio.vault import vault

PASSWORD = "test-password-123"


@unittest.skipUnless(backup.SEVEN_ZIP.exists(), "7za.exe is not in app/bin")
class Transfer(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        vault.set(backup.PASSWORD, PASSWORD)
        vault.set("gelato_api_key", "made-up-gelato-key")
        self.addCleanup(vault.set, backup.PASSWORD, None)
        self.addCleanup(vault.set, "gelato_api_key", None)
        core.settings.update({"gelato": {"defaultFormat": "square-8"},
                              "browser": {"exe": r"D:\old\chrome.exe", "profile": "Profile 6", "hosts": ["gelato.com"]},
                              "workshop": {"upscayl": r"D:\old\upscayl-bin.exe"},
                              "backup": {"last": {"file": "x.7z"}}})
        self.scheme = core.data_path("slides", "schemes", "mine")
        self.scheme.mkdir(parents=True, exist_ok=True)
        (self.scheme / "scheme.json").write_text('{"colour": "green"}', encoding="utf-8")
        self.addCleanup(shutil.rmtree, self.scheme, True)
        self.file = self.tmp / "settings.7z"

    def seven(self, *args):
        return subprocess.run([str(backup.SEVEN_ZIP), *args, f"-p{PASSWORD}", "-sccUTF-8"], capture_output=True,
                              encoding="utf-8")

    def test_the_file_holds_settings_keys_and_schemes_but_nothing_of_this_computer(self):
        done = transfer.export_to(self.file)
        self.assertEqual(done["keys"], 1)
        listing = self.seven("l", "-slt", str(self.file)).stdout
        paths = {line[7:] for line in listing.splitlines() if line.startswith("Path = ")}
        self.assertIn(transfer.SETTINGS_FILE, paths)
        self.assertIn(transfer.KEYS_FILE, paths)
        self.assertIn(r"slides\schemes\mine\scheme.json", paths)
        settings = json.loads(self.seven("e", "-so", str(self.file), transfer.SETTINGS_FILE).stdout)
        self.assertEqual(settings["gelato"]["defaultFormat"], "square-8")
        self.assertNotIn("backup", settings)
        self.assertNotIn("workshop", settings)
        self.assertNotIn("exe", settings["browser"])
        self.assertEqual(settings["browser"]["profile"], "Profile 6")
        keys = json.loads(self.seven("e", "-so", str(self.file), transfer.KEYS_FILE).stdout)
        self.assertEqual(keys["gelato_api_key"], "made-up-gelato-key")
        self.assertNotIn(backup.PASSWORD, keys)
        self.assertEqual(list(self.tmp.glob("*.part")), [])

    def test_the_safety_switches_never_travel_and_an_import_cannot_switch_them_off(self):
        core.settings.update({"security": {"etsyKyivOnly": True}, "printify": {"readOnlyFrom": "2026-10-01"}})
        transfer.export_to(self.file)
        settings = json.loads(self.seven("e", "-so", str(self.file), transfer.SETTINGS_FILE).stdout)
        self.assertNotIn("security", settings)
        self.assertNotIn("readOnlyFrom", settings.get("printify", {}))
        # a file made elsewhere with the switches off (a hand-made one: they are not in what export writes)
        self.assertEqual(transfer._computer_bound({"security": {"etsyKyivOnly": False}, "printify": {"readOnlyFrom": None, "x": 1}}),
                         {"printify": {"x": 1}})
        transfer.import_from(self.file)
        self.assertTrue(core.settings.section("security")["etsyKyivOnly"])
        self.assertEqual(core.settings.section("printify")["readOnlyFrom"], "2026-10-01")

    def test_the_start_sweeps_what_a_crash_left_in_tmp_and_nothing_else(self):
        keep = core.data_path("tmp", "dropped")
        keep.mkdir(parents=True, exist_ok=True)
        junk = [core.data_path("tmp", "upload-1.png"), core.data_path("tmp", "upscale-2.png"), core.data_path("tmp", "listing-3.jpg")]
        for f in junk:
            f.write_bytes(b"x")
        self.assertEqual(core.sweep_tmp(), 3)
        self.assertFalse(any(f.exists() for f in junk))
        self.assertTrue(keep.is_dir())

    def test_a_cut_short_import_leaves_nothing_in_tmp(self):
        stale = core.data_path("tmp", "import-123")
        stale.mkdir(parents=True, exist_ok=True)
        (stale / transfer.KEYS_FILE).write_text("{}", encoding="utf-8")
        transfer.sweep()
        self.assertFalse(stale.exists())

    def test_import_puts_everything_back_and_keeps_what_it_replaced(self):
        transfer.export_to(self.file)
        core.settings.update({"gelato": {"defaultFormat": "changed"}})
        vault.set("gelato_api_key", "another")
        (self.scheme / "scheme.json").write_text('{"colour": "red"}', encoding="utf-8")
        done = transfer.import_from(self.file)
        self.assertEqual(done["keys"], 1)
        self.assertEqual(core.settings.section("gelato")["defaultFormat"], "square-8")
        self.assertEqual(vault.get("gelato_api_key"), "made-up-gelato-key")
        self.assertEqual(json.loads((self.scheme / "scheme.json").read_text(encoding="utf-8"))["colour"], "green")
        self.assertEqual(core.settings.section("workshop")["upscayl"], r"D:\old\upscayl-bin.exe")   # this computer's own stays
        saved = Path(done["saved"])
        self.assertEqual(json.loads((saved / "slides" / "schemes" / "mine" / "scheme.json").read_text(encoding="utf-8"))["colour"], "red")
        self.assertTrue((saved / "settings.json").is_file())

    def test_a_wrong_password_changes_nothing(self):
        transfer.export_to(self.file)
        core.settings.update({"gelato": {"defaultFormat": "changed"}})
        with self.assertRaises(ApiError):
            transfer.import_from(self.file, "not-the-password")
        self.assertEqual(core.settings.section("gelato")["defaultFormat"], "changed")

    def test_the_password_that_opened_the_file_becomes_this_computers_when_it_has_none(self):
        transfer.export_to(self.file)
        vault.set(backup.PASSWORD, None)
        transfer.import_from(self.file, PASSWORD)
        self.assertEqual(vault.get(backup.PASSWORD), PASSWORD)

    def test_no_password_no_file(self):
        vault.set(backup.PASSWORD, None)
        with self.assertRaises(ApiError):
            transfer.export_to(self.file)


if __name__ == "__main__":
    unittest.main()
