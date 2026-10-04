"""The portable copy's path layer: programs found in runtime/ next to the repository, saved paths taken into it."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import __init__  # noqa: F401  (a test file run alone still gets the made-up data folder)
from studio import core, mockups, portable


def _runtime(root: Path) -> None:
    for rel in ("Photoshop", "Templates", "Upscayl/resources/bin", "ffmpeg/bin", "Ollama/models",
                "Antigravity/app"):
        (root / "runtime" / rel).mkdir(parents=True)
    for rel in ("Upscayl/resources/bin/upscayl-bin.exe", "ffmpeg/bin/ffmpeg.exe",
                "Antigravity/app/Antigravity.exe"):
        (root / "runtime" / rel).write_bytes(b"")


class Portable(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        _runtime(self.root)
        patch = mock.patch.dict(os.environ, {"BOOKSTUDIO_PORTABLE": str(self.root)})
        patch.start()
        self.addCleanup(patch.stop)
        self.addCleanup(self.dir.cleanup)

    def test_programs_are_found_in_runtime(self):
        rt = self.root / "runtime"
        self.assertEqual(portable.antigravity(), rt / "Antigravity" / "app" / "Antigravity.exe")
        self.assertEqual(portable.ffmpeg(), rt / "ffmpeg" / "bin" / "ffmpeg.exe")
        self.assertEqual(portable.upscayl_exe(), rt / "Upscayl" / "resources" / "bin" / "upscayl-bin.exe")

    def test_ollama_keeps_its_models_in_the_portable_folder_and_ffmpeg_goes_on_path(self):
        env = portable.env()
        self.assertEqual(env["OLLAMA_MODELS"], str(self.root / "runtime" / "Ollama" / "models"))
        self.assertTrue(env["PATH"].startswith(str(self.root / "runtime" / "ffmpeg" / "bin")))

    def test_saved_paths_of_a_moved_copy_are_taken_into_runtime(self):
        moved = portable.relocate(r"E:\somewhere\runtime\Upscayl\resources\bin\upscayl-bin.exe")
        self.assertEqual(moved, self.root / "runtime" / "Upscayl" / "resources" / "bin" / "upscayl-bin.exe")

    def test_a_path_that_is_not_ours_stays_as_it_was(self):
        self.assertEqual(portable.relocate(r"G:\My Drive\backups"), Path(r"G:\My Drive\backups"))
        self.assertIsNone(portable.relocate(""))

    def test_the_mockups_take_runtime_when_nothing_is_saved(self):
        with mock.patch.object(mockups.core, "read_json", return_value={}):
            places = mockups.places()
        self.assertEqual(places["photoshop"], self.root / "runtime" / "Photoshop")
        self.assertEqual(places["templates"], self.root / "runtime" / "Templates")

    def test_without_runtime_everything_is_as_it_was(self):
        with mock.patch.dict(os.environ, {"BOOKSTUDIO_PORTABLE": ""}):
            self.assertIsNone(portable.root())
            self.assertIsNone(portable.antigravity())
            self.assertEqual(portable.env(), {})
            self.assertEqual(portable.relocate(r"D:\x"), Path(r"D:\x"))

    def test_the_check_names_what_is_missing_and_says_what_to_do(self):
        (self.root / "runtime" / "ffmpeg" / "bin" / "ffmpeg.exe").unlink()
        with mock.patch.object(mockups, "find_photoshop", return_value=None):
            problems = portable.check()
        said = " ".join(p["what"] for p in problems)
        self.assertIn("ffmpeg", said)
        self.assertIn("Photoshop", said)
        self.assertNotIn("Ollama", said)                 # the text check is an optional module now
        self.assertTrue(all(p["fix"] for p in problems))

    def test_keys_that_this_windows_user_cannot_open_are_reported(self):
        from studio.vault import vault
        with mock.patch.object(vault, "_load", return_value={"gelato_api_key": "x"}), \
                mock.patch.object(vault, "get", return_value=None):
            self.assertIn("Ключі", portable._keys_problem()[0]["what"])
        with mock.patch.object(vault, "_load", return_value={}):
            self.assertEqual(portable._keys_problem(), [])

    def test_the_first_run_notes_come_once_per_computer(self):
        with mock.patch.dict(os.environ, {"COMPUTERNAME": "PC-A"}):
            self.assertTrue(portable.first_run_notes())
            self.assertEqual(portable.first_run_notes(), [])
        with mock.patch.dict(os.environ, {"COMPUTERNAME": "PC-B"}):
            self.assertTrue(portable.first_run_notes())
        with mock.patch.dict(os.environ, {"COMPUTERNAME": "PC-A"}):          # a stick that came back to A: A is still known
            self.assertEqual(portable.first_run_notes(), [])

    def test_a_no_to_an_install_is_remembered_for_that_computer_only(self):
        need = {"id": "vcredist"}
        with mock.patch.dict(os.environ, {"COMPUTERNAME": "PC-A"}):
            self.assertFalse(portable.declined(need))
            portable.decline(need)
            self.assertTrue(portable.declined(need))
        with mock.patch.dict(os.environ, {"COMPUTERNAME": "PC-B"}):
            self.assertFalse(portable.declined(need))

    def test_the_install_result_is_said_in_words(self):
        self.assertFalse(portable.install_result(0)[1])
        self.assertIn("перезавантажити", portable.install_result(3010)[0])
        text, bad = portable.install_result(1602)
        self.assertTrue(bad)
        self.assertIn("1602", text)

    def test_an_apostrophe_in_the_installers_path_does_not_break_the_command(self):
        with mock.patch("subprocess.run") as run:
            run.return_value.returncode = 0
            portable.install({"installer": r"D:\O'Brienc_redist.x64.exe"})
        script = run.call_args[0][0][-1]
        self.assertIn("O''Brien", script)

    def test_nothing_is_checked_in_the_ordinary_install(self):
        with mock.patch.dict(os.environ, {"BOOKSTUDIO_PORTABLE": ""}):
            self.assertEqual(portable.check(), [])
            self.assertIsNone(portable.startup_report())

    def test_antigravity_starts_with_its_own_profile_and_home(self):
        args, env = portable.antigravity_launch()
        base = self.root / "runtime" / "Antigravity"
        self.assertEqual(args[0], str(base / "app" / "Antigravity.exe"))
        self.assertEqual(args[1], f"--user-data-dir={base / 'data' / 'user-data'}")
        self.assertEqual(env["USERPROFILE"], str(base / "home"))
        self.assertTrue((base / "home").is_dir())

    def test_gelato_and_canva_open_in_edge_with_a_profile_of_the_copy(self):
        from studio import settings_api
        with mock.patch.object(settings_api.core.settings, "section", return_value={"hosts": ["gelato.com"]}), \
                mock.patch.object(settings_api.desktop, "find_browser", return_value=r"C:\edge\msedge.exe"), \
                mock.patch("subprocess.Popen") as launched:
            self.assertTrue(settings_api._open_in_profile("https://dashboard.gelato.com/orders/list", "dashboard.gelato.com"))
            self.assertFalse(settings_api._open_in_profile("https://example.com/", "example.com"))
        args = launched.call_args.args[0]
        self.assertEqual(args[0], r"C:\edge\msedge.exe")
        self.assertTrue(any(a.startswith("--user-data-dir=") and a.endswith("work-browser") for a in args))

    def test_a_fresh_install_opens_gelato_and_canva_in_the_programs_own_profile(self):
        from studio import settings_api
        self.assertEqual(core.DEFAULT_SETTINGS["browser"]["hosts"], ["gelato.com", "canva.com"])
        with mock.patch.object(settings_api.core.settings, "section", return_value=core.DEFAULT_SETTINGS["browser"]), \
                mock.patch.object(settings_api.desktop, "find_browser", return_value=r"C:\edge\msedge.exe"), \
                mock.patch("subprocess.Popen") as launched:
            self.assertTrue(settings_api._open_in_profile("https://www.canva.com/design/x", "www.canva.com"))
        self.assertTrue(any(a.startswith("--user-data-dir=") for a in launched.call_args.args[0]))


if __name__ == "__main__":
    unittest.main()
