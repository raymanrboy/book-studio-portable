"""Order pipeline: which printer an order goes to, and turning a Canva export into Cover.png + 1..N.png."""
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from PIL import Image

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from tests.fixtures import png
from studio import drops, library_files, orders, printify
from studio.server import ApiError

REAL_RETIRED = printify.retired  # GelatoOnly stands in for it; its own test checks the real one


def item(cover="8\" × 8\" Hardcover", title="Personalized book"):
    return {"title": title, "quantity": 1, "variations": [{"name": "Cover Type & Size", "value": cover}]}


class PrinterRule(unittest.TestCase):
    def test_owner_rule(self):
        us = orders.plan_for(item(), "US")                                                 # hardcover to the US
        self.assertEqual(us["provider"], "printify")                                       # the suggestion the queue shows
        uk = orders.plan_for(item(), "GB")                                                 # hardcover elsewhere
        self.assertEqual((uk["provider"], uk["format"]), ("gelato", "hardcover_8x8"))
        soft = orders.plan_for(item("8\" × 8\" Softcover"), "US")                           # softcover anywhere
        self.assertEqual((soft["provider"], soft["format"], soft["pages"]), ("gelato", "softcover_8x8", [28, 30]))
        self.assertNotIn("choice", soft)                                                   # softcovers are only Gelato's

    def test_for_now_a_hardcover_goes_where_its_files_say(self):
        """Owner, 25.09.2026: Printify prints faulty books — every hardcover, wherever it goes, is decided by
        the pages he downloads: 24 → Printify, 28 or 30 → Gelato."""
        for country in ("US", "GB"):
            with self.subTest(country=country):
                plan = orders.plan_for(item(), country)
                self.assertEqual(plan["choice"], {"printify": [24], "gelato": [28, 30]})
                self.assertEqual((plan["pages"], plan["format"]), ([24, 28, 30], "hardcover_8x8"))
        self.assertEqual([orders.provider_by_pages(n) for n in (24, 28, 30)], ["printify", "gelato", "gelato"])
        small = orders.plan_for(item("5.5\" × 5.5\" Softcover"), "CA")
        self.assertEqual(small["format"], "softcover_5x5")
        for label in ('5" × 5" Softcover', "5&quot; × 5&quot; Softcover", "Softcover 14 x 14 cm"):  # as Etsy names it
            with self.subTest(label=label):
                self.assertEqual(orders.plan_for(item(label), "US")["format"], "softcover_5x5")
        self.assertEqual(orders.plan_for(item("8&quot; × 8&quot; Softcover"), "US")["format"], "softcover_8x8")

    def test_unknown_cover_leaves_the_choice_to_the_owner(self):
        self.assertIsNone(orders.plan_for(item(cover="Blue", title="Book"), "US")["provider"])


class GelatoOnly(unittest.TestCase):
    """From 1 October 2026 every new book is Gelato's (owner, 29.09.2026); Printify only reads."""

    def setUp(self):
        self.printify = printify
        patcher = mock.patch.object(printify, "retired", lambda today=None: True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_day_itself(self):
        from datetime import date
        with mock.patch.object(printify, "READ_ONLY_FROM", date(2026, 10, 1)):  # the suite runs as before that day
            self.assertFalse(REAL_RETIRED(date(2026, 9, 30)))
            self.assertTrue(REAL_RETIRED(date(2026, 10, 1)))

    def test_every_book_goes_to_gelato(self):
        us = orders.plan_for(item(), "US")
        self.assertEqual((us["provider"], us["format"], us["pages"]), ("gelato", "hardcover_8x8", [28, 30]))
        self.assertNotIn("choice", us)
        unknown = orders.plan_for(item(cover="Blue", title="Book"), "US")
        self.assertEqual((unknown["provider"], unknown["format"], unknown["pages"]), ("gelato", None, [28, 30]))
        self.assertNotIn("printify", orders.printing()["pages"])

    def test_24_pages_are_refused_and_a_card_opened_before_is_led_to_gelato(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "Emma"
            d.mkdir()
            for n in list(range(1, 29)):
                png(d / f"{n}.png")
            png(d / "Cover.png", (96, 50))
            from studio import gelato
            with mock.patch.object(drops, "DROPS", Path(tmp) / "drops"), \
                    mock.patch.object(gelato, "page_counts", lambda uid: [28, 30]):
                got = orders._files(SimpleNamespace(json={"folder": str(d), "provider": "files", "format": "hardcover_8x8"}))
                self.assertEqual((got["pageCount"], got["provider"]), (28, "gelato"))
                with self.assertRaises(ApiError):
                    orders._files(SimpleNamespace(json={"folder": str(d), "provider": "printify"}))

    def test_nothing_is_written_to_printify(self):
        from studio import httpc
        with mock.patch.object(httpc, "request_json", side_effect=AssertionError("must not be sent")):
            for path in ("uploads/images.json", "shops/1/products.json"):
                with self.assertRaises(self.printify.PrintifySecurityError):
                    self.printify.call("POST", path, {})
            with self.assertRaises(self.printify.PrintifySecurityError):
                self.printify.call("POST", "shops/1/orders.json", {}, order=True)
        from studio.creator import routes
        for route in (routes._create_printify, routes._reprint_printify):
            with self.assertRaises(ApiError):
                route(SimpleNamespace(json={}))


class ArrangePages(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def folder(self, names, cover=None):
        d = self.root / "Madelynn"
        d.mkdir()
        for n in names:
            png(d / n)
        if cover:
            png(d / cover, (96, 50))
        return d

    def test_page_numbers_and_ranges(self):
        self.assertEqual(drops.page_number("12"), 12)
        self.assertEqual(drops.page_number("Madelynn - 12"), 12)
        self.assertEqual(drops.page_number("12_upscayl_4x_ultrasharp-4x"), 12)
        self.assertIsNone(drops.page_number("cover"))
        self.assertEqual(orders.ranges([1, 2, 3, 5, 7, 8]), "1–3, 5, 7–8")

    def test_already_in_order_is_used_as_is(self):
        d = self.folder([f"{i}.png" for i in range(1, 25)], cover="Cover.png")
        res = orders.arrange_pages(d, 24)
        self.assertEqual((res["path"], res["renumbered"]), (str(d), False))

    def test_canva_numbers_are_put_in_order_without_touching_the_originals(self):
        # Canva keeps the design's page numbers: 24 chosen pages out of 30, the cover recognised by its shape.
        chosen = [1, 2, 3, 6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 19, 22, 23, 24, 25, 26, 27, 28, 29, 30]
        d = self.folder([f"{n}.png" for n in chosen], cover="31.png")
        with mock.patch.object(drops, "DROPS", self.root / "drops"):
            res = orders.arrange_pages(d, 24)
        out = Path(res["path"])
        self.assertNotEqual(out, d)
        self.assertEqual(sorted(p.name for p in out.iterdir()), sorted(["Cover.png"] + [f"{i}.png" for i in range(1, 25)]))
        self.assertTrue((d / "6.png").exists())                                    # the user's own files stay put
        with Image.open(out / "Cover.png") as cover:
            self.assertEqual(cover.size, (96, 50))
        self.assertIn("1–3, 6–11, 14–19, 22–30 → 1–24", res["note"])

    def test_upscayl_names(self):
        d = self.folder([f"{i}_upscayl_4x_ultrasharp-4x.png" for i in range(2, 26)], cover="Cover_upscayl_4x_ultrasharp-4x.png")
        with mock.patch.object(drops, "DROPS", self.root / "drops"):
            res = orders.arrange_pages(d, 24)
        self.assertTrue((Path(res["path"]) / "24.png").exists())
        self.assertIn("2–25 → 1–24", res["note"])

    def test_a_cover_named_in_ukrainian_is_the_cover_here_too(self):
        """The library took «Обкладинка.png» as the cover and the print folder did not (22.09.2026 audit)."""
        d = self.folder([f"{i}.png" for i in range(1, 25)], cover="Обкладинка.png")
        with mock.patch.object(drops, "DROPS", self.root / "drops"):
            res = orders.arrange_pages(d, 24)
        self.assertIn("обкладинка — Обкладинка.png", res["note"])
        self.assertTrue((Path(res["path"]) / "Cover.png").exists())

    def test_wrong_count_says_what_is_there(self):
        d = self.folder([f"{i}.png" for i in range(1, 23)], cover="Cover.png")
        with self.assertRaises(ApiError) as caught:
            orders.arrange_pages(d, 24)
        self.assertIn("Потрібно 24 сторінки, а тут 22", str(caught.exception))

    def test_no_cover_and_duplicates_are_reported(self):
        d = self.folder([f"{i}.png" for i in range(1, 25)])
        with self.assertRaises(ApiError) as caught:
            orders.arrange_pages(d, 24)
        self.assertIn("обкладинку", str(caught.exception))
        (d / "copy of 5.png").write_bytes((d / "5.png").read_bytes())
        png(d / "Cover.png", (96, 50))
        with self.assertRaises(ApiError) as caught:
            orders.arrange_pages(d, 24)
        self.assertIn("5 є двічі", str(caught.exception))

    def test_dropped_copies_are_moved_not_copied(self):
        scratch = self.root / "drops"
        d = scratch / "abc" / "Madelynn"
        d.mkdir(parents=True)
        for i in range(3, 27):
            png(d / f"{i}.png")
        png(d / "Cover.png", (96, 50))
        with mock.patch.object(drops, "DROPS", scratch):
            res = orders.arrange_pages(d, 24)
        self.assertFalse(any(d.iterdir()))
        self.assertEqual(len(list(Path(res["path"]).iterdir())), 25)


    def test_a_refusal_before_the_move_leaves_the_dropped_files_where_they_were(self):
        """Gelato's length check used to come after the move: the card kept the old path and the files were gone from it."""
        scratch = self.root / "drops"
        d = scratch / "abc" / "Madelynn"
        d.mkdir(parents=True)
        for i in range(3, 27):
            png(d / f"{i}.png")
        png(d / "Cover.png", (96, 50))
        with mock.patch.object(drops, "DROPS", scratch):
            with self.assertRaises(ApiError) as caught:
                orders.arrange_pages(d, 24, precheck=lambda count: "Gelato не друкує таку довжину")
        self.assertIn("Gelato не друкує", str(caught.exception))
        self.assertEqual(len(list(d.iterdir())), 25)


class GelatoLength(unittest.TestCase):
    """A Gelato book is as long as the Canva export: 30 pages, or 28 when one spread was left out."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def folder(self, numbers):
        d = self.root / "Emma"
        d.mkdir()
        for n in numbers:
            png(d / f"{n}.png")
        png(d / "Cover.png", (96, 50))
        return d

    def test_28_or_30_pages_as_downloaded(self):
        d = self.folder([n for n in range(1, 31) if n not in (8, 9)])       # spread 8–9 left out in Canva
        with mock.patch.object(drops, "DROPS", self.root / "drops"):
            res = orders.arrange_pages(d, orders.page_options("gelato"))
        self.assertEqual(res["pageCount"], 28)
        self.assertIn("1–7, 10–30 → 1–28", res["note"])
        self.assertEqual(len(list(Path(res["path"]).iterdir())), 29)
        (d / "8.png").write_bytes((d / "7.png").read_bytes())               # one page too many: neither 28 nor 30
        with self.assertRaises(ApiError) as caught:
            orders.arrange_pages(d, [28, 30])
        self.assertIn("Потрібно 28 або 30 сторінок, а тут 29", str(caught.exception))

    def test_card_is_told_at_once_when_gelato_does_not_print_that_length(self):
        from types import SimpleNamespace
        from studio import gelato
        d = self.folder(range(1, 29))

        def catalog(uid):  # made-up answers: whatever Gelato really says, the program follows it
            if "5_5x5_5" in uid:
                raise gelato.GelatoError("немає з'єднання", 502)
            return [30, 32] if "softcover" in uid else [28, 30, 32]

        def files(provider, fmt):
            return orders._files(SimpleNamespace(json={"folder": str(d), "provider": provider, "format": fmt}))

        with mock.patch.object(gelato, "page_counts", catalog):
            with self.assertRaises(ApiError) as caught:
                files("gelato", "softcover_8x8")
            self.assertIn("Gelato не друкує Softcover 8×8 на 28 сторінках (можна від 30)", str(caught.exception))
            self.assertIn("Скачайте з Canva 30 сторінок", str(caught.exception))
            self.assertEqual(files("gelato", "hardcover_8x8")["pageCount"], 28)
            self.assertEqual(files("gelato", "softcover_5x5")["pageCount"], 28)  # catalog not reachable: checked again at the draft
            self.assertEqual(files("gelato", None)["pageCount"], 28)             # printer picked by hand, format not known yet
            got = files("files", "hardcover_8x8")                                 # a hardcover the files decide
            self.assertEqual((got["pageCount"], got["provider"]), (28, "gelato"))

    def test_24_pages_of_a_hardcover_go_to_printify(self):
        from types import SimpleNamespace
        d = self.folder(range(1, 25))
        with mock.patch.object(drops, "DROPS", self.root / "drops"):
            got = orders._files(SimpleNamespace(json={"folder": str(d), "provider": "files", "format": "hardcover_8x8"}))
        self.assertEqual((got["pageCount"], got["provider"]), (24, "printify"))
        (d / "25.png").write_bytes((d / "24.png").read_bytes())                   # 25: no printer takes it
        with self.assertRaises(ApiError) as caught:
            orders._files(SimpleNamespace(json={"folder": str(d), "provider": "files", "format": "hardcover_8x8"}))
        self.assertIn("Потрібно 24, 28 або 30 сторінок, а тут 25", str(caught.exception))


class PreparationGuide(unittest.TestCase):
    """The instruction handed to whoever prepares a book must match what the importer really accepts."""

    def test_names_and_json_in_the_guide_are_what_the_importer_reads(self):
        import json
        import re
        from studio import library
        guide = library_files.agent_guide()
        block = re.search(r"```json\n(\{.*?\n\})\n```", guide, re.S).group(1)
        text, problems, _ = library_files.parse_text_json(block)     # the template itself imports without a problem
        self.assertEqual(problems, [])
        self.assertEqual(len(text), len(library.TEXT_KEYS))
        self.assertEqual(sorted(json.loads(block)["spreads"]), sorted(str(n) for n in library.SPREAD_NUMBERS))
        names = re.findall(r"`(\d+(?:-\d+)?\.png|Cover\.png|Thumbnail\.png)`", guide)
        with tempfile.TemporaryDirectory() as d:
            for name in set(names):
                png(Path(d) / name)
            scan = library_files.scan_folder(Path(d))
        self.assertEqual(scan["slotsFound"], scan["slotsTotal"])  # every slot of the book is filled
        self.assertIn("cover", scan["mapping"])
        self.assertIn("thumbnail", scan["mapping"])
        self.assertIn("{Name}", guide)
        self.assertIn("{Gifter}", guide)

    def test_saved_as_a_file_in_the_chosen_folder(self):
        from types import SimpleNamespace
        from studio import desktop, library
        with tempfile.TemporaryDirectory() as d, mock.patch.object(desktop, "open_in_explorer") as shown:
            res = library_files._guide_save(SimpleNamespace(json={"folder": d}))
            saved = Path(res["path"])
            self.assertEqual(saved.parent, Path(d))
            self.assertEqual(saved.read_text(encoding="utf-8"), library_files.agent_guide())
            shown.assert_called_once_with(saved)


class PartialBookImport(unittest.TestCase):
    """The book passport takes any subset: what is there goes to its place, the rest stays empty."""

    def test_only_some_pictures_without_text(self):
        from studio import library
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ("3_upscayl_4x_ultrasharp-4x.png", "4.png", "9.png", "30.png"):   # single illustration pages
                png(root / name)
            scan = library_files.scan_folder(root)
        # spread N holds pages 2N−2 and 2N−1: page 3 → spread 2 right, 4 → spread 3 left, 9 → spread 5 right
        self.assertEqual(sorted(scan["mapping"]), ["page30", "spread2:right", "spread3:left", "spread5:right"])
        self.assertEqual(scan["issues"], [])           # a single page of a spread is not a problem
        self.assertIsNone(scan["text"])
        self.assertEqual(scan["ignored"], [])

    def test_zip_for_the_library_keeps_the_text(self):
        import zipfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = root / "book.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("Book/5.png", b"png")
                zf.writestr("Book/book-text.json", b'{"page1": "Dear {Name}"}')
            self.assertEqual(drops.extract_zip(archive, root / "out", with_text=True), 2)
            self.assertTrue((root / "out" / "Book" / "book-text.json").exists())
            self.assertEqual(drops.extract_zip(archive, root / "out2"), 1)   # the Order Creator takes pictures only


class CanvaZipFromDownloads(unittest.TestCase):
    """The order card takes this order's Canva ZIP from Downloads by itself — the extension named the copy
    «<receipt> - <child>», and Canva names the ZIP after the design."""

    def setUp(self):
        import os, time, zipfile
        self.os, self.time, self.zipfile = os, time, zipfile
        self.dl = Path(tempfile.mkdtemp())
        orders._zip_sizes.clear()

    def zip(self, name, mtime=None):
        path = self.dl / name
        import io

        def picture(size):
            buf = io.BytesIO()
            Image.new("RGB", size, (200, 180, 160)).save(buf, "PNG")
            return buf.getvalue()
        with self.zipfile.ZipFile(path, "w") as z:
            z.writestr("Cover.png", picture((64, 32)))
            for n in range(1, 31):
                z.writestr(f"{n}.png", picture((32, 32)))
        if mtime:
            self.os.utime(path, (mtime, mtime))
        return path

    def test_only_this_orders_finished_zip_after_the_press(self):
        now = self.time.time()
        self.zip("4202433342 - Margot.zip", mtime=now - 3600)          # an older download of the same order
        self.zip("4100000001 - Emma.zip")                              # another order's
        self.assertIsNone(orders.find_canva_zip("4202433342", now, self.dl))
        self.zip("4202433342 - Margot (1).zip")
        self.assertIsNone(orders.find_canva_zip("4202433342", now, self.dl))   # seen once: its size must hold
        found = orders.find_canva_zip("4202433342", now, self.dl)
        self.assertEqual(found.name, "4202433342 - Margot (1).zip")

    def test_each_book_takes_only_its_own_zip(self):
        """Two books of one order: «R - Emma» and «R - Max» — Emma's ZIP never goes into Max's book."""
        now = self.time.time()
        self.zip("4202433342 - Emma.zip")
        self.assertIsNone(orders.find_canva_zip("4202433342", now, self.dl, "4202433342 - Max"))
        self.assertIsNone(orders.find_canva_zip("4202433342", now, self.dl, "4202433342 - Max"))
        self.zip("4202433342 - Max (1).zip")                            # the browser's own «(1)» of a second download
        orders.find_canva_zip("4202433342", now, self.dl, "4202433342 - Max")
        self.assertEqual(orders.find_canva_zip("4202433342", now, self.dl, "4202433342 - Max").name, "4202433342 - Max (1).zip")
        self.assertIsNone(orders.find_canva_zip("4202433342", now, self.dl, "4202433342 - Emma #2"))

    def test_a_broken_zip_is_said_once(self):
        (self.dl / "4202433342 - Margot.zip").write_bytes(b"not a zip at all")
        req = SimpleNamespace(groups=("4202433342",), param=lambda k: {"since": "0", "title": "4202433342 - Margot"}.get(k))
        with mock.patch.object(orders, "canva_downloads", lambda: self.dl):
            orders._canva_zip(req)
            self.assertIn("error", orders._canva_zip(req))

    def test_the_route_unpacks_it_like_a_dropped_zip(self):
        self.zip("4202433342 - Margot.zip")
        req = SimpleNamespace(groups=("4202433342",), param=lambda k: "0" if k == "since" else None)
        with mock.patch.object(orders, "canva_downloads", lambda: self.dl):
            self.assertEqual(orders._canva_zip(req), {})                # the first look only notes its size
            res = orders._canva_zip(req)
        folder = Path(res["path"])
        self.assertTrue((folder / "Cover.png").exists())
        self.assertEqual(res["name"], "4202433342 - Margot.zip")
        self.assertTrue((self.dl / "4202433342 - Margot.zip").exists())  # the download itself stays


class SyncAtStartHourlyOrByHand(unittest.TestCase):
    """Orders are pulled when the program starts, quietly every hour (a thread, not in the tests' sandbox — 2026-10-14)
    and by the refresh button."""

    def test_start_up_sync_runs_once_and_pages_can_follow_it(self):
        import threading
        import time
        from studio import etsy, sync
        from studio.jobs import jobs
        gate = threading.Event()
        with mock.patch.object(etsy, "tokens", lambda: {"access_token": "1.x"}), \
                mock.patch.object(sync, "_sync", lambda job, full=False: gate.wait(5) and {}):
            sync.startup_sync()
            running = sync._sync_state(None)["jobId"]
            self.assertIsNotNone(running)                            # a page opened now follows this one
            sync.startup_sync()
            self.assertEqual(sync._sync_state(None)["jobId"], running)  # never a second one alongside
            gate.set()
            for _ in range(500):  # the job ends at once; the long limit only keeps a busy machine from failing the test
                if not jobs.running("profit-sync"):
                    break
                time.sleep(0.02)
        self.assertIsNone(sync._sync_state(None)["jobId"])          # afterwards nothing runs by itself

    def test_nothing_starts_without_connections(self):
        from studio import etsy, sync
        with mock.patch.object(etsy, "tokens", lambda: None):
            sync.startup_sync()
        self.assertIsNone(sync._sync_state(None)["jobId"])


class DevToolsKeepOffRealData(unittest.TestCase):
    """The sample server writes its own orders and books into the data folder it is given. It must refuse
    anything that could be the owner's real data — not only the one exact path of the real folder."""

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "dev_server", Path(__file__).resolve().parents[1] / "tools" / "dev_server.py")
        self.dev = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.dev)
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_it_refuses_a_folder_that_is_not_its_own(self):
        looks_real = self.root / "backup"
        looks_real.mkdir()
        (looks_real / "settings.json").write_text("{}", encoding="utf-8")
        self.assertIsNotNone(self.dev.claim(looks_real, self.root / "bsdev"))
        self.assertFalse((looks_real / self.dev.MARK).exists())

    def test_it_refuses_a_folder_with_keys(self):
        keys = self.root / "copy"
        keys.mkdir()
        (keys / "vault.json").write_text("{}", encoding="utf-8")
        self.assertIsNotNone(self.dev.claim(keys, keys))

    def test_it_refuses_the_real_data_folder(self):
        self.assertIsNotNone(self.dev.claim((self.dev.APP / "data").resolve(), self.root / "bsdev"))

    def test_an_empty_folder_becomes_its_own_and_stays_usable(self):
        mine = self.root / "bsdev"
        self.assertIsNone(self.dev.claim(mine, mine))
        self.assertTrue((mine / self.dev.MARK).exists())
        (mine / "settings.json").write_text("{}", encoding="utf-8")
        self.assertIsNone(self.dev.claim(mine, self.root / "elsewhere"))   # marked once, used again

    def test_the_sample_server_neither_offers_nor_keeps_a_real_key(self):
        """23.09.2026: its Settings offered to import the owner's real keys from the old programs on the Desktop
        — and a preview server holding them could reach Etsy, Printify and Gelato."""
        from studio import core, settings_api
        from studio.jobs import JobError
        from studio.vault import vault
        with mock.patch.object(core, "SAMPLE", True):
            self.assertEqual(settings_api.legacy_sources()["items"], [])
            with self.assertRaises(JobError):
                vault.set("printify_token", "real-looking-token")
            vault.set("printify_token", None)                                 # clearing is always allowed
        self.assertIn('os.environ["BOOK_STUDIO_SAMPLE"] = "1"', (self.dev.APP / "tools" / "dev_server.py").read_text(encoding="utf-8"))


class TestsNeverRunOnRealData(unittest.TestCase):
    def test_the_data_folder_is_a_throw_away_one(self):
        """Whatever BOOK_STUDIO_DATA said before, the suite took a fresh temporary folder: tests below
        empty whole folders, so this may not depend on how the program was started."""
        import os
        from studio import core
        self.assertIn("bstests-", os.environ["BOOK_STUDIO_DATA"])
        self.assertTrue(Path(os.environ["BOOK_STUDIO_DATA"]).is_absolute())
        self.assertEqual(core.DATA_DIR, Path(os.environ["BOOK_STUDIO_DATA"]))

    def test_the_suite_writes_nothing_to_drive_c(self):
        """Windows' temp folder is on drive C, which the owner keeps clean (23.09.2026): the suite's files — and
        those of whatever it starts — live in <repository>/.tmp and go when it ends."""
        import os
        import tempfile
        repo_tmp = Path(__file__).resolve().parents[2] / ".tmp"
        self.assertEqual(Path(tempfile.gettempdir()), repo_tmp)
        self.assertEqual(Path(os.environ["TEMP"]), repo_tmp)
        self.assertEqual(Path(os.environ["BOOK_STUDIO_DATA"]).parent, repo_tmp)


class SharedNumbers(unittest.TestCase):
    """Numbers the pages and the server must agree on, read from the page files themselves."""
    WEB = Path(__file__).resolve().parents[1] / "web"

    def js(self) -> str:
        return "\n".join(p.read_text(encoding="utf-8") for p in sorted((self.WEB / "js").rglob("*.js")))

    def test_the_pages_ask_for_the_preview_sizes_the_server_keeps(self):
        """22.09.2026 audit: the viewer asked for 2400 px — a fourth file per picture, decoded from the original."""
        from studio import images
        asked = {int(n) for n in re.findall(r"assetUrl\([^,()]+, (\d+)\)|[{,]\s*w: (\d+)", self.js()) for n in n if n}
        self.assertTrue(asked)
        self.assertEqual(sorted(n for n in asked if n >= 1400 and n not in images._LARGER), [])

    def test_a_dialog_opened_from_the_page_viewer_shows_over_it(self):
        """22.09.2026 audit: «Чернетку вже створено» and every error of a page replacement opened under the viewer."""
        css = (self.WEB / "css" / "app.css").read_text(encoding="utf-8")
        z = {name: int(re.search(rf"^\.{name} \{{[^}}]*z-index: (\d+)", css, re.M).group(1))
             for name in ("lightbox", "modal-root", "menu", "toasts")}
        self.assertEqual(z["modal-root"], z["lightbox"])   # the one opened later is on top
        self.assertGreater(z["menu"], z["modal-root"])
        self.assertGreater(z["toasts"], z["menu"])


if __name__ == "__main__":
    unittest.main()
