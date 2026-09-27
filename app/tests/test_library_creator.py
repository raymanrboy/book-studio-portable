import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core, creator, gelato, library, printify
from studio.server import ApiError, Request


def png(path: Path, size=(40, 40), color=(200, 120, 90)):
    Image.new("RGB", size, color).save(path, "PNG")


class TextJson(unittest.TestCase):
    def test_full(self):
        raw = json.dumps({"cover": "{Name}'s Book", "page1": "Dear {Name}", "page30": "The end",
                          "spreads": {str(n): f"Spread {n}" for n in range(2, 16)}})
        text, problems, notes = library.parse_text_json(raw)
        self.assertEqual(len(text), 17)
        self.assertEqual(problems, [])
        self.assertEqual(text["spread15"], "Spread 15")

    def test_partial_and_extra(self):
        text, problems, notes = library.parse_text_json('{"cover": "C", "spreads": {"2": "two", "99": "x"}}')
        self.assertEqual(set(text), {"cover", "spread2"})
        self.assertIn("Немає тексту «page1»", problems)
        self.assertTrue(notes)

    def test_invalid(self):
        with self.assertRaises(ApiError):
            library.parse_text_json("{not json")
        with self.assertRaises(ApiError):
            library.parse_text_json("[1, 2]")


class FolderScan(unittest.TestCase):
    def test_pipeline_layout(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            gen = root / "generated"
            gen.mkdir()
            png(gen / "Cober.png", (80, 40))
            png(gen / "1.png")
            png(gen / "30.png")
            for n in range(2, 16):
                a, b = library.spread_pages(n)
                png(gen / f"{a}-{b}.png", (80, 40))
            png(gen / "notes.png")
            (root / "book-text.json").write_text("{}", encoding="utf-8")
            scan = library.scan_folder(root)
            self.assertEqual(scan["slotsFound"], 16)
            self.assertIn("cover", scan["mapping"])
            self.assertEqual(scan["mapping"]["spread15"]["name"], "28-29.png")
            self.assertEqual(scan["text"]["name"], "book-text.json")
            self.assertEqual(scan["ignored"], ["notes.png"])

    def test_separate_pages(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for i in range(1, 31):
                png(root / f"{i}.png")
            scan = library.scan_folder(root)
            self.assertEqual(scan["slotsFound"], 16)
            self.assertEqual(scan["mapping"]["spread2:left"]["name"], "2.png")
            self.assertEqual(scan["mapping"]["spread2:right"]["name"], "3.png")


class NothingIsLostWhenAWriteFails(unittest.TestCase):
    """A picture is removed from disk only after the book record that stopped pointing at it is saved.
    The other way round, one failed write would take the picture and leave a book pointing at nothing."""

    def setUp(self):
        self.book_id = "e" * 32
        library.save({"id": self.book_id, "schema": 1, "rev": 0, "title": "Failing writes",
                      "listing": {"id": "4100000903"}, "slots": library._empty_slots(),
                      "text": {}, "cover": None, "thumbnail": None})
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        source = Path(self.tmp.name) / "page.png"
        png(source, (80, 40))
        self.asset = library._store_asset(self.book_id, source, "page.png")
        book = library.load(self.book_id)
        library._set_asset(book, "spread2", self.asset)
        library.save(book)
        self.file = library._book_dir(self.book_id) / "assets" / self.asset["file"]
        self.assertTrue(self.file.exists())

    def remove(self):
        """The real «прибрати ілюстрацію» route, as the page calls it."""
        return library._remove_asset(Request(None, "DELETE", "/api/library/books/x/assets",
                                             {"slot": ["spread2"]}, (self.book_id,)))

    def test_the_picture_stays_when_the_record_cannot_be_written(self):
        with mock.patch.object(library, "save", side_effect=OSError("disk full")), self.assertRaises(OSError):
            self.remove()
        self.assertTrue(self.file.exists(), "a failed write must not cost the picture")
        kept = library.load(self.book_id)["slots"]["spread2"]
        self.assertEqual((kept.get("image") or {}).get("file"), self.asset["file"],
                         "and the book still points at it")

    def test_the_picture_goes_once_the_record_is_written(self):
        self.remove()
        self.assertFalse(self.file.exists())
        self.assertIsNone(library.load(self.book_id)["slots"]["spread2"].get("image"))


class DeletingABook(unittest.TestCase):
    def test_a_book_being_imported_is_not_deleted(self):
        """Audit 26.09.2026: deleting a book while its folder import ran left a folder with no book.json, warned
        about on every list."""
        import threading
        from studio.jobs import jobs
        book = library.create_book({"id": "4100000977"}, "4100000077 - Iris")
        release = threading.Event()
        jobs.start("library-import", lambda job: release.wait(5), exclusive=f"library-{book['id']}")
        delete = Request(None, "DELETE", f"/api/library/books/{book['id']}", {}, (book["id"],))
        try:
            with self.assertRaises(ApiError) as caught:
                library._delete(delete)
            self.assertEqual(caught.exception.status, 409)
            self.assertTrue(library._book_dir(book["id"]).exists())
        finally:
            release.set()
        for _ in range(100):
            if not jobs.running(f"library-{book['id']}"):
                break
            time.sleep(0.02)
        self.assertTrue(library._delete(delete)["ok"])


class QueryNumbers(unittest.TestCase):
    def test_a_size_that_is_not_a_number_is_the_default_not_an_error(self):
        """Audit 26.09.2026: «?w=abc» on a picture was a server error with a traceback in the log (4 routes)."""
        def req(**query):
            return Request(None, "GET", "/media/x", {k: [v] for k, v in query.items()}, ())
        self.assertEqual(req(w="abc").int_param("w", 480, 64, 4096), 480)
        self.assertEqual(req().int_param("w", 480, 64, 4096), 480)
        self.assertEqual(req(w="10").int_param("w", 480, 64, 4096), 64)
        self.assertEqual(req(w="99999").int_param("w", 480, 64, 4096), 4096)
        self.assertEqual(req(page="3").int_param("page", 1, 1), 3)


class JsonFiles(unittest.TestCase):
    """22.09.2026 audit: the .bak brought a removed file back; a .bak copy that failed was not said."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "states.json"

    def test_a_damaged_file_is_read_from_its_copy_a_removed_one_is_gone(self):
        core.write_json(self.path, {"n": 1})
        core.write_json(self.path, {"n": 2})
        self.path.write_text("{broken", encoding="utf-8")
        with self.assertLogs("studio", "WARNING"):
            self.assertEqual(core.read_json(self.path, {}), {"n": 1})
        self.path.unlink()
        self.assertEqual(core.read_json(self.path, {}), {})

    def test_a_failed_backup_copy_is_logged_and_the_write_still_happens(self):
        core.write_json(self.path, {"n": 1})
        real = core.replace_file

        def locked(src, dst, copy_only=False):
            if copy_only:
                raise PermissionError("the .bak is held by another program")
            return real(src, dst, copy_only)

        with mock.patch.object(core, "replace_file", locked), self.assertLogs("studio", "WARNING") as logged:
            core.write_json(self.path, {"n": 2})
        self.assertIn("older state", logged.output[0])
        self.assertEqual(core.read_json(self.path), {"n": 2})


class PrintifyValidation(unittest.TestCase):
    def setUp(self):
        self._saved = core.settings.get()
        core.settings.update({"printify": {"coverSize": [60, 30], "pageSize": [40, 40]}})
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        png(self.root / "Cover.png", (60, 30))
        for i in range(1, 25):
            png(self.root / f"{i}.png", (40, 40), (i * 9, 100, 150))

    def tearDown(self):
        core.settings.replace_section("printify", self._saved["printify"])
        self.dir.cleanup()

    def test_ok(self):
        res = creator.validate("printify", str(self.root))
        self.assertTrue(res["ok"], res["errors"])
        self.assertEqual(res["found"], 25)

    def test_a_newer_check_of_the_folder_stops_the_older_one(self):
        """Quick page replacements each start a full check: the older ones stop instead of running side by
        side (22.09.2026 audit). A send's own check is never stopped."""
        from studio import images
        from studio.jobs import Job, JobError
        real, calls = images.check_png, []

        def check(path, previews=()):
            calls.append(path.name)
            if len(calls) == 1:   # the page asks again while this check is on its first file
                creator._validating[("printify", str(self.root.resolve()))] += 1
            return real(path, previews)

        with mock.patch.object(images, "check_png", check), self.assertRaises(JobError):
            creator.validate("printify", str(self.root), Job("t"))
        self.assertLess(len(calls), 25)
        with mock.patch.object(images, "check_png", check):
            self.assertTrue(creator.validate("printify", str(self.root))["ok"])  # no job: a send's check

    def test_only_the_pages_check_makes_the_previews_from_its_own_decode(self):
        """A send's own check (no job) makes no previews: it competed with the PDF, and on Windows a second reader
        kept a page open while a test removed its folder (flaky 1 run in 5, 25.09.2026). The page's check makes
        them from the pixels it has just decoded — the viewer and the strip are ready when it ends (26.09.2026)."""
        from studio import images
        from studio.jobs import Job
        pages = [self.root / "Cover.png"] + [self.root / f"{i}.png" for i in range(1, 25)]
        made = lambda: [p.name for p in pages if all(images._cached(p, p.stat(), s)[1].exists() for s in images.VIEW_SIDES)]
        self.assertTrue(creator.validate("printify", str(self.root))["ok"])
        self.assertEqual(made(), [])
        self.assertTrue(creator.validate("printify", str(self.root), Job("t"))["ok"])
        self.assertEqual(len(made()), 25)

    def test_a_replaced_page_is_the_only_one_read_again(self):
        """Every page was decoded again after one was replaced (4–5 s for a 30-page book, 26.09.2026)."""
        from studio import images
        self.assertTrue(creator.validate("printify", str(self.root))["ok"])
        new = Path(self.dir.name) / "fixed.png"
        png(new, (40, 40), (1, 2, 3))
        creator.replace_page(str(self.root), "7.png", str(new))
        real, read = images._check, []

        def check(path, st, previews):
            read.append(path.name)
            return real(path, st, previews)
        with mock.patch.object(images, "_check", check):
            res = creator.validate("printify", str(self.root))
        self.assertTrue(res["ok"])
        self.assertEqual(read, ["7.png"])

    def test_the_result_is_the_callers_own(self):
        first = creator.validate("printify", str(self.root))
        first["files"].clear()
        self.assertEqual(creator.validate("printify", str(self.root))["found"], 25)

    def test_missing_page_blocks(self):
        (self.root / "17.png").unlink()
        res = creator.validate("printify", str(self.root))
        self.assertFalse(res["ok"])
        self.assertIn("17", res["errors"][0])

    def test_wrong_size_and_fake_png(self):
        png(self.root / "13.png", (41, 40))
        (self.root / "5.png").write_bytes(b"not a png at all")
        res = creator.validate("printify", str(self.root))
        joined = " ".join(res["errors"])
        self.assertIn("13.png", joined)
        self.assertIn("5.png", joined)
        self.assertFalse(res["ok"])

    def test_extra_and_duplicate_warnings(self):
        png(self.root / "25.png")
        png(self.root / "3.png", (40, 40), (4 * 9, 100, 150))  # same pixels as 4.png
        res = creator.validate("printify", str(self.root))
        self.assertTrue(res["ok"])
        self.assertTrue(any("25.png" in w for w in res["warnings"]))
        self.assertTrue(any("однакові" in w for w in res["warnings"]))

    def test_payload_matches_master(self):
        cfg = core.settings.section("printify")
        ids = {e["position"]: f"img-{e['position']}" for e in creator.expected_files("printify")}
        payload = creator.build_printify_payload("4100000001 - Emma", ids, cfg)
        self.assertEqual(payload["blueprint_id"], 2737)
        self.assertEqual(payload["print_provider_id"], 28)
        self.assertEqual([v["id"] for v in payload["variants"]], [149190, 149191, 149192, 149193])
        self.assertEqual([v["is_enabled"] for v in payload["variants"]], [True, True, False, False])
        area = payload["print_areas"][0]
        self.assertEqual(area["background"], "#ffffff")
        self.assertEqual(len(area["placeholders"]), 25)
        cover = area["placeholders"][0]
        self.assertEqual(cover["position"], "cover")
        self.assertEqual(cover["images"][0]["x"], 0.5000000000000001)
        self.assertEqual(cover["images"][0]["y"], 0.4968637346791639)
        self.assertEqual(area["placeholders"][24]["position"], "page_24")
        self.assertNotIn("publish", json.dumps(payload))


class ReplacePage(unittest.TestCase):
    """The owner fixed one page in Canva and downloaded it again: it takes the place of the old one,
    and the old one waits in .replaced for «Повернути» (owner, 20.09.2026)."""

    def setUp(self):
        self._saved = core.settings.get()
        core.settings.update({"printify": {"coverSize": [60, 30], "pageSize": [40, 40]}})
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.folder = self.root / "print"
        self.folder.mkdir()
        png(self.folder / "Cover.png", (60, 30))
        for n in range(1, 25):
            png(self.folder / f"{n}.png", (40, 40), (n * 10, 60, 60))
        self.fresh = self.root / "Lily - 8.png"
        png(self.fresh, (40, 40), (7, 8, 9))

    def tearDown(self):
        core.settings.replace_section("printify", self._saved["printify"])
        self.tmp.cleanup()

    def test_the_page_changes_and_the_old_one_waits(self):
        before = (self.folder / "7.png").read_bytes()
        res = creator.replace_page(str(self.folder), "7.png", str(self.fresh))
        self.assertEqual((res["file"], res["width"], res["height"]), ("7.png", 40, 40))
        self.assertEqual((self.folder / "7.png").read_bytes(), self.fresh.read_bytes())
        kept = list((self.folder / creator.REPLACED).glob("7.png.*"))
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].read_bytes(), before)
        # the pages Printify gets are still exactly the expected ones — the kept copy is not one of them
        check = creator.validate("printify", str(self.folder), None)
        self.assertTrue(check["ok"], check["errors"])
        self.assertEqual(check["found"], 25)
        self.assertEqual(check["warnings"], [])

    def test_the_old_page_comes_back(self):
        before = (self.folder / "7.png").read_bytes()
        creator.replace_page(str(self.folder), "7.png", str(self.fresh))
        res = creator.restore_page(str(self.folder), "7.png")
        self.assertEqual(res["file"], "7.png")
        self.assertEqual((self.folder / "7.png").read_bytes(), before)
        with self.assertRaises(ApiError):
            creator.restore_page(str(self.folder), "7.png")   # nothing left to put back

    def test_the_files_check_says_which_pages_can_be_put_back(self):
        """«Повернути» is offered from what lies on disk, so it is still there after the card is closed,
        reopened or the program restarted — the card itself remembers nothing."""
        creator.replace_page(str(self.folder), "7.png", str(self.fresh))
        rows = {r["file"]: r for r in creator.validate("printify", str(self.folder), None)["files"]}
        self.assertTrue(rows["7.png"]["replaced"])
        self.assertFalse(rows["8.png"]["replaced"])
        self.assertFalse(rows["Cover.png"]["replaced"])
        creator.restore_page(str(self.folder), "7.png")
        rows = {r["file"]: r for r in creator.validate("printify", str(self.folder), None)["files"]}
        self.assertFalse(rows["7.png"]["replaced"])

    def test_two_replacements_keep_both_old_pages(self):
        """Replaced twice within the same second: «Повернути» walks back version by version."""
        first = (self.folder / "7.png").read_bytes()
        creator.replace_page(str(self.folder), "7.png", str(self.fresh))
        second = (self.folder / "7.png").read_bytes()
        other = self.root / "Lily - 8 again.png"
        png(other, (40, 40), (9, 8, 7))
        res = creator.replace_page(str(self.folder), "7.png", str(other))
        self.assertTrue(res["canRestore"])
        self.assertEqual(len(list((self.folder / creator.REPLACED).glob("7.png.*"))), 2)
        back = creator.restore_page(str(self.folder), "7.png")
        self.assertEqual((self.folder / "7.png").read_bytes(), second)
        self.assertTrue(back["canRestore"], "the page before that one is still there")
        back = creator.restore_page(str(self.folder), "7.png")
        self.assertEqual((self.folder / "7.png").read_bytes(), first)
        self.assertFalse(back["canRestore"])

    def test_a_page_cannot_change_under_a_running_send(self):
        """A send checks every PNG, then uploads those same paths, builds the PDF and copies them to the
        archive. If a page could be replaced in between, the printer would get bytes that never passed
        the check — and the upload cache would file the new picture under the old file's hash."""
        with creator._while_sending([str(self.folder)]):
            with self.assertRaises(ApiError) as caught:
                creator.replace_page(str(self.folder), "7.png", str(self.fresh))
            self.assertIn("відправляється", str(caught.exception))
            with self.assertRaises(ApiError):
                creator.restore_page(str(self.folder), "7.png")
            other = self.root / "elsewhere"          # another book's folder is not blocked
            other.mkdir()
            png(other / "7.png", (40, 40))
            self.assertEqual(creator.replace_page(str(other), "7.png", str(self.fresh))["file"], "7.png")
        res = creator.replace_page(str(self.folder), "7.png", str(self.fresh))   # free again once it ends
        self.assertEqual(res["file"], "7.png")

    def test_two_sends_of_one_folder_both_hold_it(self):
        """The same folder sent to Printify and Gelato at once: the first to finish must not free the folder
        while the second still reads it (22.09.2026 audit)."""
        with creator._while_sending([str(self.folder)]):
            with creator._while_sending([str(self.folder)]):
                pass                                   # the quicker send is done…
            with self.assertRaises(ApiError):          # …the other still reads the pages
                creator.replace_page(str(self.folder), "7.png", str(self.fresh))
        self.assertEqual(creator.replace_page(str(self.folder), "7.png", str(self.fresh))["file"], "7.png")
        self.assertEqual(creator._sending, {})

    def test_a_page_of_the_wrong_size_is_caught_by_the_usual_check(self):
        """Printify wants 4000x4000 (here 40x40): a page straight from Canva, without Upscayl, must not
        pass quietly — the file check says so right after the replacement."""
        small = self.root / "small.png"
        png(small, (20, 20))
        creator.replace_page(str(self.folder), "7.png", str(small))
        check = creator.validate("printify", str(self.folder), None)
        self.assertFalse(check["ok"])
        self.assertTrue(any("7.png" in e for e in check["errors"]), check["errors"])

    def test_the_cover_can_be_replaced_too(self):
        wide = self.root / "cover-new.png"
        png(wide, (60, 30), (1, 2, 3))
        creator.replace_page(str(self.folder), "Cover.png", str(wide))
        self.assertEqual((self.folder / "Cover.png").read_bytes(), wide.read_bytes())

    def test_nothing_else_may_be_written(self):
        for bad in ("../secret.png", "7.txt", "25a.png", "book.json", ""):
            with self.subTest(file=bad), self.assertRaises(ApiError):
                creator.replace_page(str(self.folder), bad, str(self.fresh))
        with self.assertRaises(ApiError):   # a page the folder does not have
            creator.replace_page(str(self.folder), "99.png", str(self.fresh))
        with self.assertRaises(ApiError):   # not a picture at all
            text = self.root / "note.png"
            text.write_text("not a png", encoding="utf-8")
            creator.replace_page(str(self.folder), "7.png", str(text))
        with self.assertRaises(ApiError):   # the file already in the folder
            creator.replace_page(str(self.folder), "7.png", str(self.folder / "7.png"))


class GelatoValidation(unittest.TestCase):
    def test_gelato_needs_30_pages(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            png(root / "cover.png", (80, 40))
            for i in range(1, 30):
                png(root / f"{i}.png")
            res = creator.validate("gelato", str(root))
            self.assertFalse(res["ok"])
            png(root / "30.png")
            self.assertTrue(creator.validate("gelato", str(root))["ok"])

    def test_gelato_book_is_as_long_as_the_folder(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            png(root / "Cover.png", (80, 40))
            for i in range(1, 28):
                png(root / f"{i}.png")
            res = creator.validate("gelato", str(root))
            self.assertEqual((res["ok"], res["pageCount"]), (False, 28))    # 1–27: page 28 is missing
            self.assertIn("Відсутні файли (1 шт.): 28", res["errors"][0])
            png(root / "28.png")
            res = creator.validate("gelato", str(root))
            self.assertEqual((res["ok"], res["pageCount"], res["found"]), (True, 28, 29))
            png(root / "31.png")                                              # past the longest book: an extra file
            res = creator.validate("gelato", str(root))
            self.assertEqual((res["ok"], res["pageCount"]), (False, 30))

    def test_address(self):
        self.assertTrue(creator.validate_address({"country": "US"}))
        ok = {"firstName": "A", "lastName": "B", "addressLine1": "1 St", "city": "X", "postCode": "1", "country": "DE"}
        self.assertEqual(creator.validate_address(ok), [])
        self.assertTrue(creator.validate_address({**ok, "country": "US"}))  # state required


class SafetyRails(unittest.TestCase):
    def test_printify_allowlist(self):
        printify._check("GET", "shops/1/orders.json")
        printify._check("POST", "uploads/images.json")
        printify._check("POST", "shops/1/products.json")
        for method, path in (("POST", "shops/1/products/abc/publish.json"), ("POST", "shops/1/orders.json"),
                             ("PUT", "shops/1/products/abc.json"), ("DELETE", "shops/1/products/abc.json"),
                             ("POST", "shops/1/orders/abc/send_to_production.json")):
            with self.assertRaises(ApiError, msg=f"{method} {path}"):
                printify._check(method, path)

    def test_a_create_is_never_sent_twice_after_an_unclear_failure(self):
        """A POST that may have reached the printer (timeout, dropped connection, 500/502/504) is not repeated —
        a second one would be a second product, image or order. One that certainly did not arrive (refused
        connection, 503, 429) is; so is every read, and a search sent as a POST."""
        import socket
        import urllib.error
        from studio import httpc

        def attempts(method, failure, **kw):
            calls = []

            def urlopen(req, timeout=None):
                calls.append(req.get_method())
                raise failure
            with mock.patch("urllib.request.urlopen", urlopen), mock.patch("time.sleep"):
                with self.assertRaises(httpc.HttpError) as caught:
                    httpc.request(method, "https://api.example.test/x", json_body={}, retries=3, **kw)
            return len(calls), caught.exception.ambiguous

        def status(code):
            return urllib.error.HTTPError("https://api.example.test/x", code, "x", {}, None)

        self.assertEqual(attempts("POST", socket.timeout("timed out")), (1, True))
        self.assertEqual(attempts("POST", status(500)), (1, True))
        self.assertEqual(attempts("POST", status(504)), (1, True))
        self.assertEqual(attempts("POST", status(503)), (3, False))
        self.assertEqual(attempts("POST", urllib.error.URLError(ConnectionRefusedError())), (3, False))
        self.assertEqual(attempts("GET", socket.timeout("timed out")), (3, True))
        self.assertEqual(attempts("POST", socket.timeout("timed out"), idempotent=True), (3, True))
        # A reply cut short while it was read: the server may have made the product or order all the same.
        import http.client
        import ssl
        self.assertEqual(attempts("POST", http.client.IncompleteRead(b"{", 200)), (1, True))
        self.assertEqual(attempts("POST", ssl.SSLEOFError("EOF occurred in violation of protocol")), (1, True))
        self.assertEqual(attempts("POST", http.client.RemoteDisconnected("closed")), (1, True))
        self.assertEqual(attempts("GET", http.client.IncompleteRead(b"{", 200)), (3, True))

    def test_both_printers_read_a_failure_alike(self):
        from studio import httpc
        for err in (httpc.HttpError("x", status=502, ambiguous=True), httpc.HttpError("x", ambiguous=True)):
            for provider in (printify, gelato):
                with self.subTest(provider=provider.__name__, status=err.status):
                    human = provider._human(err, "Створення")
                    self.assertTrue(human.extra["ambiguous"])
                    self.assertEqual(human.extra["upstream"], err.status)
                    self.assertTrue(creator._unknown_outcome(human))
        refused = gelato._human(httpc.HttpError("x", status=400, body="bad address"), "Створення")
        self.assertFalse(creator._unknown_outcome(refused))
        self.assertIn("bad address", str(refused))

    def test_gelato_only_drafts(self):
        self.assertTrue(gelato._allowed("POST", f"{gelato.ORDER_API}/orders", {"orderType": "draft"}))
        self.assertFalse(gelato._allowed("POST", f"{gelato.ORDER_API}/orders", {"orderType": "order"}))
        self.assertFalse(gelato._allowed("POST", f"{gelato.ORDER_API}/orders/1:cancel", {}))
        self.assertTrue(gelato._allowed("POST", f"{gelato.ORDER_API}/orders:search", {}))


if __name__ == "__main__":
    unittest.main()
