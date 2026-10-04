"""A redirect to another host does not carry the keys along (httpc._SafeRedirects)."""
import http.server
import threading
import unittest

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import httpc


class Redirects(unittest.TestCase):
    def test_the_keys_stay_at_home_when_a_reply_sends_the_request_elsewhere(self):
        seen = {}

        class Start(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                self.send_response(302)
                self.send_header("Location", f"http://localhost:{end.server_port}/end")
                self.end_headers()

        class End(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                seen["auth"], seen["key"] = self.headers.get("Authorization"), self.headers.get("x-api-key")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"{}")

        start = http.server.HTTPServer(("127.0.0.1", 0), Start)
        end = http.server.HTTPServer(("127.0.0.1", 0), End)
        for server in (start, end):
            threading.Thread(target=server.serve_forever, daemon=True).start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
        status, _ = httpc.request("GET", f"http://127.0.0.1:{start.server_port}/start",
                                  headers={"Authorization": "Bearer made-up", "x-api-key": "made-up"})
        self.assertEqual(status, 200)
        self.assertEqual(seen, {"auth": None, "key": None})


if __name__ == "__main__":
    unittest.main()
