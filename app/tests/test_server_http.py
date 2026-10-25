"""The real HTTP layer (server.py): the protection against other local programs and web pages — token, Host, framing, traversal."""
import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import server
from studio.main import main as _main  # noqa: F401  (imports the entry point; the route modules follow below)
from studio import (archive, backup, creator, drops, etsy, gelato, gelato_accounts, images, library, library_files,  # noqa: F401
                    mockups, modules, orders, printify, profit, sendlog, settings_api, slides, sync, textcheck, transfer,
                    tunnel, workshop)

OPEN = {"/api/ping", "/api/app/bye", "/etsy/callback"}      # the only routes that answer without the session token


class HttpLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.start(0)
        cls.port = cls.httpd.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def get(self, path, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            conn.request("GET", path, headers=headers or {})
            res = conn.getresponse()
            return res.status, dict(res.getheaders()), res.read()
        finally:
            conn.close()

    def test_a_route_without_the_token_is_refused(self):
        status, _, _ = self.get("/api/app")
        self.assertEqual(status, 401)
        status, _, _ = self.get("/api/app", {"X-Studio-Token": "wrong"})
        self.assertEqual(status, 401)

    def test_the_token_opens_it(self):
        status, _, _ = self.get("/api/app", {"X-Studio-Token": server.SESSION_TOKEN})
        self.assertEqual(status, 200)

    def test_pictures_take_their_own_key_that_outlives_a_restart(self):
        """The pictures' key stays the same across launches (the window's cache keeps them); it opens pictures only."""
        picture = "/media/photos/none/none.png?t="
        self.assertEqual(self.get(picture + "wrong")[0], 403)
        self.assertNotEqual(self.get(picture + server.MEDIA_TOKEN)[0], 403)     # let in (then: no such picture)
        self.assertNotEqual(self.get(picture + server.SESSION_TOKEN)[0], 403)
        self.assertEqual(self.get("/api/app", {"X-Studio-Token": server.MEDIA_TOKEN})[0], 401)
        self.assertEqual(server._media_key(), server.MEDIA_TOKEN)              # the next launch reads the same one
        self.assertNotEqual(server.MEDIA_TOKEN, server.SESSION_TOKEN)

    def test_an_error_in_the_page_goes_into_the_log(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        body = json.dumps({"message": "x is undefined", "where": "orders.js:12", "page": "#/orders"})
        with self.assertLogs("studio", "WARNING") as logged:
            conn.request("POST", "/api/app/log", body, {"X-Studio-Token": server.SESSION_TOKEN, "Content-Type": "application/json"})
            self.assertEqual(conn.getresponse().status, 200)
        conn.close()
        self.assertIn("Page error: x is undefined | orders.js:12 | #/orders", logged.output[0])

    def test_another_host_name_is_refused(self):
        """A web page on the internet pointed at 127.0.0.1 by DNS carries its own Host: it must get nothing."""
        status, _, _ = self.get("/api/ping", {"Host": "evil.example"})
        self.assertEqual(status, 403)

    def test_no_other_page_may_frame_the_program(self):
        _, headers, _ = self.get("/api/ping")
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        self.assertIn("frame-ancestors 'none'", headers.get("Content-Security-Policy", ""))

    def test_the_ping_tells_which_data_it_runs_on(self):
        import json
        _, _, body = self.get("/api/ping")
        self.assertTrue(json.loads(body)["data"])

    def test_a_path_cannot_climb_out_of_the_web_folder(self):
        for path in ("/../studio/core.py", "/..%2fstudio/core.py", "/%2e%2e/studio/core.py", "/css/../../studio/core.py"):
            status, _, body = self.get(path)
            self.assertNotEqual(status, 200, path)
            self.assertNotIn(b"APP_NAME", body, path)

    def test_a_media_route_needs_the_token_in_the_address(self):
        media = [p.pattern for m, p, fn, auth in server.ROUTES if auth == "media"]
        self.assertTrue(media)

    def test_every_route_but_three_needs_the_token(self):
        open_routes = {p.pattern for m, p, fn, auth in server.ROUTES if auth == "none"}
        self.assertEqual({r.strip("^$") for r in open_routes}, OPEN)

    def test_scripts_and_styles_are_asked_for_by_an_address_with_the_files_tag_and_kept_for_good(self):
        import re
        _, _, body = self.get("/")
        html = body.decode("utf-8")
        self.assertIn('<script type="importmap">', html)
        self.assertLess(html.index("importmap"), html.index('rel="modulepreload"'))          # the map comes before any module
        css = re.search(r'href="(/css/app\.css\?v=[0-9a-f]+)"', html)
        script = re.search(r'src="(/js/app\.js\?v=[0-9a-f]+)"', html)
        self.assertTrue(css and script)
        status, headers, _ = self.get(script.group(1))
        self.assertEqual(status, 200)
        self.assertIn("immutable", headers["Cache-Control"])
        self.assertIn("no-cache", self.get("/js/app.js")[1]["Cache-Control"])               # without the tag: asked again each time
        imports = json.loads(re.search(r'<script type="importmap">(.*?)</script>', html).group(1))["imports"]
        self.assertTrue(imports["/js/lib.js"].startswith("/js/lib.js?v="))


class StartUp(unittest.TestCase):
    def test_the_program_starts_and_answers(self):
        """The real entry point in a process of its own, on a made-up data folder: a slip in main() (a name used before it is
        imported) once made the whole program refuse to start while every unit test passed."""
        data = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, data, True)
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        app = Path(__file__).resolve().parents[1]
        env = {**os.environ, "BOOK_STUDIO_DATA": data, "BOOKSTUDIO_PORTABLE": "", "BOOK_STUDIO_SAMPLE": "1"}
        code = f"import sys; sys.path.insert(0, {str(app)!r}); from studio.main import main; sys.exit(main(['--no-window', '--port', '{port}']))"
        proc = subprocess.Popen([sys.executable, "-c", code], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self.addCleanup(proc.stderr.close)
        self.addCleanup(proc.kill)
        answer = None
        for _ in range(200):
            if proc.poll() is not None:
                self.fail("The program stopped at start:\n" + proc.stderr.read().decode("utf-8", "replace")[-1500:])
            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
                conn.request("GET", "/api/ping")
                answer = json.loads(conn.getresponse().read())
                break
            except OSError:
                time.sleep(0.1)
        self.assertTrue(answer and answer.get("data"), "no answer from the started program")


class OneCopy(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "a Windows mutex")
    def test_a_second_process_on_the_same_data_sees_the_first(self):
        from studio import main as m
        self.addCleanup(setattr, m, "_mutex", None)
        self.assertFalse(m._another_copy_starting())           # the first takes the lock
        code = ("import sys; sys.path.insert(0, %r); from studio import main as m; sys.exit(7 if m._another_copy_starting() else 0)"
                % str(Path(__file__).resolve().parents[1]))
        run = subprocess.run([sys.executable, "-c", code], env={**os.environ}, capture_output=True)
        self.assertEqual(run.returncode, 7, run.stderr.decode("utf-8", "replace"))
        # a copy that only waits lets the lock go — or the next start would wait for it in turn (24.10.2026: a start made while the
        # old copy was closing left every following start waiting for nobody)
        m._release_lock()
        run = subprocess.run([sys.executable, "-c", code], env={**os.environ}, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr.decode("utf-8", "replace"))


if __name__ == "__main__":
    unittest.main()
