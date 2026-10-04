"""Optional modules (modules.py): the text check and upscaling are installed on request, from checked files, into runtime/."""
import hashlib
import io
import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from tests import __init__  # noqa: F401  (a test file run alone still gets the made-up data folder)
from studio import core, modules, portable
from studio.jobs import Job, JobError
from studio.server import ApiError


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Modules(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "portable"
        (self.root / "runtime").mkdir(parents=True)
        patch = mock.patch.dict(os.environ, {"BOOKSTUDIO_PORTABLE": str(self.root)})
        patch.start()
        self.addCleanup(patch.stop)
        self.addCleanup(shutil.rmtree, core.data_path("tmp", "modules"), True)
        # what "the internet" serves: files on disk, reached by file:// URLs
        self.web = self.tmp / "web"
        self.web.mkdir()
        engine = self.web / "engine.zip"
        with zipfile.ZipFile(engine, "w") as z:
            z.writestr("upscayl-bin-1/upscayl-bin.exe", b"exe")
            z.writestr("upscayl-bin-1/LICENSE", b"agpl")
        (self.web / "m.param").write_bytes(b"param")
        (self.web / "m.bin").write_bytes(b"bin")
        self.sources = [mock.patch.object(modules, "UPSCAYL_ENGINE", (engine.as_uri(), sha(engine), "upscayl-bin.exe")),
                        mock.patch.object(modules, "UPSCAYL_MODEL", [((self.web / "m.param").as_uri(), sha(self.web / "m.param")),
                                                                      ((self.web / "m.bin").as_uri(), sha(self.web / "m.bin"))])]
        for p in self.sources:
            p.start()
            self.addCleanup(p.stop)

    def test_the_listing_says_what_each_module_is(self):
        items = {m["id"]: m for m in modules.listing()}
        self.assertEqual(set(items), {"textcheck", "upscale"})
        self.assertTrue(items["upscale"]["canInstall"])
        self.assertIn("ГБ", items["textcheck"]["size"])

    def test_upscale_is_installed_from_the_checked_files(self):
        job = Job("module-upscale")
        with mock.patch("studio.workshop.upscale.available", return_value=True):
            modules._install_upscale(job, None)
        up = self.root / "runtime" / "Upscayl" / "resources"
        self.assertEqual((up / "bin" / "upscayl-bin.exe").read_bytes(), b"exe")
        self.assertEqual((up / "models" / "m.bin").read_bytes(), b"bin")
        self.assertEqual(job.percent, 100)

    def test_a_file_that_does_not_match_its_hash_is_not_installed(self):
        (self.web / "m.bin").write_bytes(b"tampered")
        with mock.patch("studio.workshop.upscale.available", return_value=True), self.assertRaises(JobError):
            modules._install_upscale(Job("module-upscale"), None)
        self.assertFalse((self.root / "runtime" / "Upscayl" / "resources" / "models" / "m.bin").exists())
        self.assertEqual(list((self.root / "runtime").rglob("*.part")), [])

    def test_a_module_package_is_unpacked_into_runtime(self):
        package = self.tmp / "upscale-package.zip"
        with zipfile.ZipFile(package, "w") as z:
            z.writestr("Upscayl/resources/bin/upscayl-bin.exe", b"exe2")
        with mock.patch("studio.workshop.upscale.available", return_value=True):
            modules._install_upscale(Job("module-upscale"), package)
        self.assertEqual((self.root / "runtime" / "Upscayl" / "resources" / "bin" / "upscayl-bin.exe").read_bytes(), b"exe2")

    def test_a_package_that_climbs_out_of_the_folder_is_refused(self):
        evil = self.tmp / "evil.zip"
        with zipfile.ZipFile(evil, "w") as z:
            z.writestr("../outside.txt", b"x")
        with self.assertRaises(JobError):
            modules.unpack(evil, self.root / "runtime")
        self.assertFalse((self.root / "outside.txt").exists())

    def test_removing_a_module_deletes_only_its_folder(self):
        folder = self.root / "runtime" / "Upscayl"
        (folder / "resources").mkdir(parents=True)
        (folder / "resources" / "x.txt").write_text("x")
        other = self.root / "runtime" / "ffmpeg"
        other.mkdir()
        with mock.patch("studio.workshop.upscale.available", return_value=False):
            modules.remove("upscale")
        self.assertFalse(folder.exists())
        self.assertTrue(other.exists())

    def test_nothing_to_remove_is_said_plainly(self):
        with self.assertRaises(ApiError):
            modules.remove("upscale")

    def test_modules_need_the_portable_folder(self):
        with mock.patch.dict(os.environ, {"BOOKSTUDIO_PORTABLE": ""}):
            with self.assertRaises(ApiError):
                modules.start_install("upscale")

    def test_the_text_check_is_not_installed_without_its_model(self):
        ollama = self.root / "runtime" / "Ollama"
        (ollama / "models" / "manifests").mkdir(parents=True)
        (ollama / "ollama.exe").write_bytes(b"")
        self.assertFalse(modules._model_present())
        manifest = ollama / "models" / "manifests" / "registry.ollama.ai" / "library" / "gemma4"
        manifest.mkdir(parents=True)
        (manifest / "12b-it-qat").write_text("{}")
        self.assertTrue(modules._model_present())

    def test_the_start_up_check_does_not_ask_for_the_modules(self):
        with mock.patch("studio.mockups.find_photoshop", return_value={"exe": "x"}):
            said = " ".join(p["what"] for p in portable.check())
        self.assertNotIn("Ollama", said)
        self.assertNotIn("Upscayl", said)


class Isolation(unittest.TestCase):
    """In the portable copy the modules are its own: an Ollama or Upscayl the PC has is never used, counted or written to."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "portable"
        (self.root / "runtime").mkdir(parents=True)
        patch = mock.patch.dict(os.environ, {"BOOKSTUDIO_PORTABLE": str(self.root)})
        patch.start()
        self.addCleanup(patch.stop)

    def test_the_copys_ollama_has_its_own_port_and_models_even_before_it_is_installed(self):
        env = portable.env()
        self.assertEqual(env["OLLAMA_HOST"], "127.0.0.1:11435")
        self.assertEqual(env["OLLAMA_MODELS"], str(self.root / "runtime" / "Ollama" / "models"))
        self.assertEqual(portable.ollama_url(), "http://127.0.0.1:11435")

    def test_the_ollama_that_came_as_a_zip_is_started_by_its_exe_never_the_pcs(self):
        from studio.textcheck import ollama
        self.assertIsNone(ollama._ollama_command())                    # nothing in runtime: the PC's Ollama is not used
        (self.root / "runtime" / "Ollama").mkdir()
        (self.root / "runtime" / "Ollama" / "ollama.exe").write_bytes(b"")
        self.assertEqual(ollama._ollama_command(), [str(self.root / "runtime" / "Ollama" / "ollama.exe"), "serve"])
        self.assertEqual(ollama._base(), "http://127.0.0.1:11435")

    def test_a_pcs_own_ollama_does_not_make_the_module_installed(self):
        with mock.patch("shutil.which", return_value=r"C:\Ollama\ollama.exe"):
            self.assertFalse(modules.installed("textcheck"))
        folder = self.root / "runtime" / "Ollama"
        (folder / "models" / "manifests" / "registry.ollama.ai" / "library" / "gemma4").mkdir(parents=True)
        (folder / "ollama.exe").write_bytes(b"")
        self.assertFalse(modules.installed("textcheck"))               # the exe alone is not enough: the model is missing
        (folder / "models" / "manifests" / "registry.ollama.ai" / "library" / "gemma4" / "12b-it-qat").write_text("{}")
        self.assertTrue(modules.installed("textcheck"))

    def test_a_pcs_own_upscayl_is_not_the_copys(self):
        from studio.workshop import upscale
        with mock.patch.object(upscale.core.settings, "section", return_value={"upscayl": r"D:\Programs\Upscayl\upscayl-bin.exe"}):
            self.assertEqual(list(upscale._candidates()), [])

    def test_the_model_is_pulled_through_the_copys_own_ollama_with_progress(self):
        lines = [b'{"status": "pulling manifest"}\n',
                 b'{"status": "pulling abc", "total": 2097152, "completed": 1048576}\n',
                 b'{"status": "success"}\n']
        response = mock.MagicMock()
        response.__enter__.return_value = lines
        job = Job("module-textcheck")
        with mock.patch("urllib.request.urlopen", return_value=response) as opened, \
                mock.patch("studio.textcheck.ollama.status", return_value={"models": ["gemma4:12b-it-qat"]}):
            modules._pull_model(job, "gemma4:12b-it-qat")
        self.assertEqual(opened.call_args.args[0].full_url, "http://127.0.0.1:11435/api/pull")
        self.assertEqual(round(job.percent), 50)

    def test_an_error_from_ollama_stops_the_install_with_its_words(self):
        response = mock.MagicMock()
        response.__enter__.return_value = [b'{"error": "pull model manifest: file does not exist"}\n']
        with mock.patch("urllib.request.urlopen", return_value=response), self.assertRaises(JobError) as caught:
            modules._pull_model(Job("module-textcheck"), "nope:1")
        self.assertIn("file does not exist", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
