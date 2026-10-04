"""app/tools/setup_portable.py: a portable folder laid out from a clone of the repository."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests import __init__  # noqa: F401  (sets a temporary data folder)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import setup_portable as sp  # noqa: E402


class Layout(unittest.TestCase):
    def setUp(self):
        self.target = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.target, True)

    def test_the_launchers_the_skeleton_and_the_note_are_laid_out(self):
        done = sp.layout(self.target)
        for name in sp.REFRESHED + sp.KEPT:
            self.assertTrue((self.target / name).is_file(), name)
            self.assertIn(name, done)
        for folder in sp.RUNTIME_FOLDERS:
            self.assertTrue((self.target / "runtime" / folder).is_dir(), folder)
        self.assertIn("python app/tools/setup_portable.py --python", (self.target / "runtime" / "README.txt").read_text(encoding="utf-8"))

    def test_a_second_run_changes_nothing_but_a_refreshed_launcher(self):
        sp.layout(self.target)
        (self.target / "ПРОЧИТАЙ.md").write_text("my own words", encoding="utf-8")          # the owner's edit stays
        (self.target / "Start Book Studio.bat").write_text("old", encoding="utf-8")         # a launcher is refreshed
        done = sp.layout(self.target)
        self.assertEqual(done, ["Start Book Studio.bat"])
        self.assertEqual((self.target / "ПРОЧИТАЙ.md").read_text(encoding="utf-8"), "my own words")

    @unittest.skipUnless(sys.platform == "win32", "the hidden flag is Windows's")
    def test_a_hidden_launcher_is_refreshed_and_stays_hidden(self):
        import stat
        import subprocess
        sp.layout(self.target)
        bat = self.target / "Start Book Studio.bat"
        bat.write_text("old", encoding="utf-8")
        subprocess.run(["attrib", "+h", str(bat)], check=True)
        self.assertEqual(sp.layout(self.target), ["Start Book Studio.bat"])
        self.assertNotEqual(bat.read_text(encoding="utf-8"), "old")
        self.assertTrue(bat.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)

    def test_the_launchers_in_the_repository_start_the_runtime_python(self):
        text = (sp.LAUNCHERS / "Start Book Studio.bat").read_text(encoding="utf-8")
        self.assertIn(r"runtime\python\pythonw.exe", text)
        self.assertIn("Book Studio.pyw", text)

    def test_what_is_missing_is_named_until_it_is_there(self):
        sp.layout(self.target)
        lacking = sp.missing(self.target)
        self.assertEqual(len(lacking), 5)
        runtime = self.target / "runtime"
        (runtime / "python").mkdir()
        (runtime / "python" / "python.exe").write_bytes(b"")
        (runtime / "ffmpeg" / "bin").mkdir()
        (runtime / "ffmpeg" / "bin" / "ffmpeg.exe").write_bytes(b"")
        (runtime / "Photoshop" / "App" / "Photoshop").mkdir(parents=True)
        (runtime / "Photoshop" / "App" / "Photoshop" / "Photoshop.exe").write_bytes(b"")
        (runtime / "Templates" / "a.psd").write_bytes(b"")
        (runtime / "Antigravity" / "app").mkdir()
        (runtime / "Antigravity" / "app" / "Antigravity.exe").write_bytes(b"")
        self.assertEqual(sp.missing(self.target), [])

    def test_a_python_copy_leaves_out_the_tests_and_the_packages_and_keeps_the_rest(self):
        fake = self.target / "fake-python"
        for path in ("python.exe", "Lib/os.py", "Lib/test/x.py", "Lib/site-packages/pkg/a.py", "Lib/idlelib/i.py",
                     "Lib/json/tool.py", "DLLs/a.dll", "tcl/tcl8.6/init.tcl", "Lib/json/__pycache__/x.pyc"):
            (fake / path).parent.mkdir(parents=True, exist_ok=True)
            (fake / path).write_bytes(b"x")
        target = self.target / "out"
        dest = sp.copy_python(target, fake)
        kept = {p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file()}
        self.assertEqual(kept, {"python.exe", "Lib/os.py", "Lib/json/tool.py", "DLLs/a.dll", "tcl/tcl8.6/init.tcl"})
        self.assertTrue((dest / "Lib" / "site-packages").is_dir())
        self.assertEqual(sp.copy_python(target, fake), dest)                    # already there: left alone

    def test_a_folder_that_is_no_python_is_refused(self):
        with self.assertRaises(SystemExit):
            sp.copy_python(self.target, self.target / "nothing")


if __name__ == "__main__":
    unittest.main()
