"""End-to-end flows with the external services replaced by fakes (no network, no real accounts)."""
import json
import re
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

from PIL import Image

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import archive, core, creator, etsy, gelato, httpc, printify, profit, tunnel
from studio.jobs import Job, JobError
from studio.vault import vault


def png(path: Path, size, color):
    Image.new("RGB", size, color).save(path, "PNG")


def journal(name: str) -> dict:
    """One record of the send journal (data/logs/sends)."""
    from studio import sendlog
    return json.loads((sendlog.SENDS / name).read_text(encoding="utf-8"))


class FakePrintify:
    """Minimal in-memory Printify: uploads, products, one read-only Master."""

    def __init__(self, master_cfg):
        self.uploads = {}
        self.created = []
        self.master = {
            "id": master_cfg["productId"], "title": master_cfg["title"], "updated_at": "2026-09-01 10:00:00+00:00",
            "blueprint_id": master_cfg["blueprintId"], "print_provider_id": master_cfg["printProviderId"],
            "visible": True, "print_areas": [{"placeholders": [{"position": "cover", "images": [{"id": "old"}]}]}],
        }
        self.calls = []

    def __call__(self, method, path, body=None, action="", timeout=60, retries=3, params="", order=False):
        printify._check(method, path, order)  # the real allowlist still applies
        self.calls.append((method, path))
        if method == "POST" and path.endswith("/orders.json"):
            self.orders = getattr(self, "orders", []) + [body]
            return {"id": "order-on-hold-1"}
        if method == "POST" and path == "uploads/images.json":
            image_id = f"{len(self.uploads):024x}"
            self.uploads[image_id] = body["file_name"]
            return {"id": image_id, "file_name": body["file_name"]}
        if method == "GET" and path.startswith("uploads/"):
            return {"id": path.split("/")[1].split(".")[0]}
        if method == "POST" and path.endswith("/products.json"):
            pid = f"{900 + len(self.created):024x}"
            self.created.append({"id": pid, **body})
            return {"id": pid}
        if method == "GET" and path.endswith(f"/products/{self.master['id']}.json"):
            return self.master
        if method == "GET" and "/products/" in path:
            pid = path.rsplit("/", 1)[1].split(".")[0]
            product = next(p for p in self.created if p["id"] == pid)
            return {"id": pid, "print_areas": product["print_areas"]}
        raise AssertionError(f"unexpected call {method} {path}")


class PrintifyDraftFlow(unittest.TestCase):
    def setUp(self):
        self._saved = core.settings.get()
        core.settings.update({"printify": {"coverSize": [60, 30], "pageSize": [40, 40]}})
        vault.set("printify_token", "fake-token-for-tests")
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        png(self.root / "Cover.png", (60, 30), (10, 20, 30))
        for i in range(1, 25):
            png(self.root / f"{i}.png", (40, 40), (i * 10, 50, 90))
        creator._validation_cache.clear()
        creator.UPLOAD_CACHE.unlink(missing_ok=True)
        self.fake = FakePrintify(core.settings.section("printify")["master"])

    def tearDown(self):
        core.settings.replace_section("printify", self._saved["printify"])
        vault.set("printify_token", None)
        self.dir.cleanup()

    def test_create_then_retry_reuses_uploads(self):
        with mock.patch.object(printify, "call", self.fake):
            res = creator.create_printify_draft([{"folder": str(self.root), "title": "4100000001 - Emma"}], Job("t"))
            self.assertEqual(res["total"], 25)
            self.assertEqual(res["uploaded"], 25)
            self.assertTrue(res["verified"])
            self.assertTrue(res["masterSafe"])
            payload = self.fake.created[0]
            self.assertEqual(payload["title"], "4100000001 - Emma")
            positions = [p["position"] for p in payload["print_areas"][0]["placeholders"]]
            self.assertEqual(positions, ["cover"] + [f"page_{i}" for i in range(1, 25)])
            # page_7 must carry exactly the image uploaded from 7.png
            page7 = payload["print_areas"][0]["placeholders"][7]["images"][0]["id"]
            self.assertEqual(self.fake.uploads[page7], "7.png")
            # A second book from the same folder re-uses every uploaded image.
            res2 = creator.create_printify_draft([{"folder": str(self.root), "title": "Second"}], Job("t"))
            self.assertEqual(res2["uploaded"], 0)
            self.assertEqual(res2["reused"], 25)
        self.assertFalse(any(m == "POST" and "publish" in p for m, p in self.fake.calls))

    ADDRESS = {"firstName": "Jane", "lastName": "Doe", "addressLine1": "12 Example St", "addressLine2": "",
               "city": "Springfield", "state": "IL", "postCode": "62701-0001", "country": "us"}

    def test_with_an_address_the_book_also_gets_an_order_on_hold(self):
        core.settings.update({"printify": {"manualApprovalConfirmedAt": "2026-09-15T20:00:00Z"}})
        with mock.patch.object(printify, "call", self.fake):
            res = creator.create_printify_draft([{"folder": str(self.root), "title": "4100000002 - Noah"}], Job("t"), self.ADDRESS)
        self.assertEqual(res["order"], {"id": "order-on-hold-1", "variant": "8x8 / Matte", "books": 1})
        self.assertIsNone(res["orderError"])
        sent = self.fake.orders[0]
        self.assertEqual(sent["line_items"], [{"product_id": res["productId"], "variant_id": 149191, "quantity": 1}])  # matte
        self.assertFalse(sent["is_printify_express"])
        self.assertFalse(sent["send_shipping_notification"])
        self.assertTrue(sent["external_id"].startswith("4100000002-"))
        self.assertEqual(sent["address_to"], {"first_name": "Jane", "last_name": "Doe", "address1": "12 Example St",
                                              "address2": "", "city": "Springfield", "region": "IL", "zip": "62701-0001",
                                              "country": "US"})
        self.assertFalse(any("send_to_production" in p for _, p in self.fake.calls))
        # Everything that went to Printify is in the send journal, without the token.
        record = journal(res["sendLog"])
        self.assertEqual((record["provider"], record["kind"], record["ok"]), ("printify", "book+order", True))
        self.assertEqual(record["request"]["title"], "4100000002 - Noah")
        self.assertEqual(record["orderRequest"], sent)
        self.assertEqual(record["orderResponse"], {"id": "order-on-hold-1"})
        self.assertEqual([s["step"] for s in record["steps"]],
                         ["files", "master", "uploads", "product", "verify", "masterSafe",
                          "printOrderRemembered", "archive"])
        # …and exactly the files that went to Printify are in the order archive.
        kept = archive.get(res["archiveId"])
        self.assertEqual((kept["provider"], kept["receiptId"], kept["productId"], kept["orderId"], kept["sendLog"]),
                         ("printify", "4100000002", res["productId"], "order-on-hold-1", res["sendLog"]))
        self.assertEqual([f["file"] for f in kept["files"]], ["Cover.png"] + [f"{i}.png" for i in range(1, 25)])
        self.assertEqual((kept["pageCount"], kept["reprintOf"], kept["keep"]), (24, None, False))
        self.assertEqual(len(record["steps"][0]["files"]), 25)
        self.assertNotIn("fake-token-for-tests", json.dumps(record))

    def test_two_books_of_one_order_share_a_single_order(self):
        """An Etsy receipt with two books (owner, 20.09.2026): a product each, one order "On hold" with two
        line items to one address, and an archive entry per book pointing at that same order."""
        core.settings.update({"printify": {"manualApprovalConfirmedAt": "2026-09-15T20:00:00Z"}})
        second = Path(self.dir.name) / "liam"
        second.mkdir()
        png(second / "Cover.png", (60, 30), (30, 20, 10))
        for i in range(1, 25):
            png(second / f"{i}.png", (40, 40), (5, i * 10, 200))
        with mock.patch.object(printify, "call", self.fake):
            res = creator.create_printify_draft([{"folder": str(self.root), "title": "4100000001 - Emma"},
                                                 {"folder": str(second), "title": "4100000001 - Liam"}],
                                                Job("t"), self.ADDRESS)
        ids = [b["productId"] for b in res["books"]]
        self.assertEqual([b["title"] for b in res["books"]], ["4100000001 - Emma", "4100000001 - Liam"])
        self.assertEqual(len(set(ids)), 2)                      # two unpublished books
        self.assertEqual(len(self.fake.orders), 1)              # one order for them both
        self.assertEqual(self.fake.orders[0]["line_items"],
                         [{"product_id": pid, "variant_id": 149191, "quantity": 1} for pid in ids])
        self.assertEqual(self.fake.orders[0]["label"], "4100000001 - Emma, Liam")
        self.assertTrue(self.fake.orders[0]["external_id"].startswith("4100000001-"))
        self.assertEqual((res["total"], res["uploaded"], res["order"]["books"]), (50, 50, 2))
        kept = [archive.get(b["archiveId"]) for b in res["books"]]
        self.assertEqual([k["title"] for k in kept], ["4100000001 - Emma", "4100000001 - Liam"])
        self.assertEqual({k["orderId"] for k in kept}, {"order-on-hold-1"})
        self.assertEqual({k["sendLog"] for k in kept}, {res["sendLog"]})
        record = journal(res["sendLog"])
        self.assertEqual([s["step"] for s in record["steps"]],
                         ["files", "files", "master", "uploads", "product", "verify",
                          "uploads", "product", "verify", "masterSafe", "printOrderRemembered",
                          "archive", "archive"])
        self.assertEqual([s["book"] for s in record["steps"] if s["step"] == "product"],
                         ["4100000001 - Emma", "4100000001 - Liam"])

    def test_no_order_without_the_manual_approval_confirmation(self):
        core.settings.update({"printify": {"manualApprovalConfirmedAt": None}})
        with mock.patch.object(printify, "call", self.fake):
            with self.assertRaises(JobError) as ctx:
                creator.create_printify_draft([{"folder": str(self.root), "title": "4100000002 - Noah"}], Job("t"), self.ADDRESS)
        self.assertIn("ручне затвердження", str(ctx.exception))
        self.assertEqual(self.fake.uploads, {})                       # stopped before anything was uploaded
        with self.assertRaises(printify.PrintifySecurityError):
            printify.create_order_on_hold(1, {"line_items": []})

    def test_order_paths_stay_locked(self):
        with self.assertRaises(printify.PrintifySecurityError):
            printify._check("POST", "shops/1/orders.json")                        # only via create_order_on_hold
        printify._check("POST", "shops/1/orders.json", order=True)
        for path in ("shops/1/orders/abc/send_to_production.json", "shops/1/orders/abc/cancel.json",
                     "shops/1/orders/express.json", "shops/1/products/abc/publish.json"):
            with self.subTest(path=path), self.assertRaises(printify.PrintifySecurityError):
                printify._check("POST", path, order=True)

    def test_invalid_folder_uploads_nothing(self):
        from studio import sendlog
        (self.root / "12.png").unlink()
        before = set(sendlog.SENDS.glob("*.json"))
        with mock.patch.object(printify, "call", self.fake):
            with self.assertRaises(JobError):
                creator.create_printify_draft([{"folder": str(self.root), "title": "4100000003 - Failed"}], Job("t"))
        self.assertEqual(self.fake.uploads, {})
        self.assertEqual(self.fake.created, [])
        new = sorted(set(sendlog.SENDS.glob("*.json")) - before)           # a failed attempt is journaled too
        self.assertEqual(len(new), 1)
        record = journal(new[0].name)
        self.assertFalse(record["ok"])
        self.assertIn("Відсутні файли", record["error"])
        self.assertNotIn("request", record)                                  # nothing was sent

    def test_upload_failure_creates_no_product(self):
        def flaky(method, path, *a, **kw):
            if method == "POST" and path == "uploads/images.json" and len(self.fake.uploads) == 20:
                raise printify.PrintifyError("Завантаження: Printify повернув помилку 500.", 502, {"upstream": 500})
            return self.fake(method, path, *a, **kw)
        with mock.patch.object(printify, "call", flaky):
            with self.assertRaises(JobError) as ctx:
                creator.create_printify_draft([{"folder": str(self.root), "title": "X"}], Job("t"))
        self.assertIn("повторний запуск продовжить", str(ctx.exception))
        self.assertEqual(self.fake.created, [])

    def test_ambiguous_create_is_not_retried(self):
        def timeout_on_create(method, path, *a, **kw):
            if method == "POST" and path.endswith("/products.json"):
                raise printify.PrintifyError("немає з'єднання", 502, {"ambiguous": True, "upstream": None})
            return self.fake(method, path, *a, **kw)
        with mock.patch.object(printify, "call", timeout_on_create):
            with self.assertRaises(JobError) as ctx:
                creator.create_printify_draft([{"folder": str(self.root), "title": "X"}], Job("t"))
        self.assertIn("НЕ запускайте повторно", str(ctx.exception))


class GelatoDraftFlow(unittest.TestCase):
    # Real catalog answers for the 20×20 cm hardcover with 30 inner pages (Gelato product API, 17.09.2026).
    PRODUCT = {"validPageCounts": list(range(28, 202, 2)),
               "dimensions": {"Text block total width": {"value": "206", "measureUnit": "mm"},
                              "Text block total height": {"value": "206", "measureUnit": "mm"}}}
    COVER = {"pagesCount": 34, "measureUnit": "mm",
             "wraparoundInsideSize": {"width": 458.0, "height": 246.0, "left": 0, "top": 0},
             "contentBackSize": {"width": 198.0, "height": 206.0, "left": 20, "top": 20},
             "contentFrontSize": {"width": 198.0, "height": 206.0, "left": 240.0, "top": 20}}
    # A white endpaper at 300 dpi on the 206 mm page — the same 2434 px as in the PDFs Gelato makes itself.
    BLANK = 2434

    def test_one_pdf_with_cover_blank_pages_blank(self):
        """Regressions: without the blank endpapers Gelato put page 1 in the endpaper's place ("Page 0")
        and left the last page empty (test draft, 17.09.2026); earlier the cover was the only 'default'
        file and was printed on every page; a 16-pixel blank made Gelato rate the whole book 3 dpi."""
        vault.set("gelato_api_key", "fake-gelato-key")
        gelato._geometry.clear()
        gelato._products.clear()
        sent = {}

        def fake_call(method, url, body=None, **kw):
            self.assertTrue(gelato._allowed(method, url, body))
            if method == "GET" and "/cover-dimensions" in url:
                self.assertIn("pageCount=30", url)
                return self.COVER
            if method == "GET" and url.endswith("/orders/gelato-order-1"):  # read back right after creating
                session = sent["customerReferenceId"].removeprefix("local-review-")
                size = core.data_path("tmp", "gelato", session, "book.pdf").stat().st_size
                return {"items": [{"productUid": "p", "pageCount": 30, "fulfillmentStatus": "draft",
                                   "files": [{"type": "default", "mimeType": "application/pdf", "sizeBytes": size}]}]}
            if method == "GET":
                return self.PRODUCT
            sent.update(body)
            return {"id": "gelato-order-1", "orderType": "draft", "fulfillmentStatus": "draft"}

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            png(root / "Cover.png", (466, 250), (1, 2, 3))
            for i in range(1, 31):  # every page gets its own width, so the PDF order can be read back
                png(root / f"{i}.png", (100 + i, 100 + i), (i, i, i))
            creator._validation_cache.clear()
            address = {"firstName": "Ann", "lastName": "Lee", "addressLine1": "1 Main St", "city": "Austin",
                       "postCode": "73301", "country": "us", "state": "TX"}
            with mock.patch.object(gelato, "call", fake_call), \
                    mock.patch.object(tunnel.FileTunnel, "start", lambda self: "https://fake.trycloudflare.com"), \
                    mock.patch.object(tunnel.registry, "keep", lambda *a, **kw: None):
                res = creator.create_gelato_draft([{"folder": str(root), "title": "Book", "format": "hardcover_8x8"}], address, Job("t"))
        vault.set("gelato_api_key", None)
        self.assertEqual(res["orderId"], "gelato-order-1")
        self.assertEqual(res["warnings"], [])
        self.assertEqual(sent["orderType"], "draft")
        item = sent["items"][0]
        self.assertEqual(item["pageCount"], 30)
        self.assertEqual(item["files"], [{"type": "default", "url": "https://fake.trycloudflare.com/book.pdf"}])
        self.assertEqual(sent["shippingAddress"]["country"], "US")
        self.assertEqual(sent["shippingAddress"]["phone"], creator.GELATO_PLACEHOLDER_PHONE)  # none from Etsy
        self.assertEqual(sent["orderReferenceId"], "Book")                  # named like the book, as the owner does
        self.assertEqual(sent["metadata"][0], {"key": "title", "value": "Book"})

        session = sent["customerReferenceId"].removeprefix("local-review-")
        pdf = core.data_path("tmp", "gelato", session, "book.pdf").read_bytes().decode("latin-1")
        boxes = [(float(w), float(h)) for w, h in re.findall(r"/MediaBox \[ ?0 0 ([\d.]+) ([\d.]+) ?\]", pdf)]
        widths = [int(w) for w in re.findall(r"/Width (\d+)", pdf)]
        self.assertEqual(len(boxes), 33)                                 # cover, blank, 30 pages, blank
        self.assertEqual(widths, [466, self.BLANK] + [100 + i for i in range(1, 31)] + [self.BLANK])
        self.assertEqual(res["pdfPages"], 33)
        pt = 72 / 25.4
        self.assertAlmostEqual(boxes[0][0], 458 * pt, places=1)         # cover sheet at Gelato's size
        self.assertAlmostEqual(boxes[0][1], 246 * pt, places=1)
        for w, h in boxes[1:]:
            self.assertAlmostEqual(w, 206 * pt, places=1)               # inner pages with bleed
            self.assertAlmostEqual(h, 206 * pt, places=1)

        # The send journal keeps what was sent and what came back — never the key.
        record = journal(res["sendLog"])
        self.assertEqual((record["provider"], record["kind"], record["ok"], record["format"]), ("gelato", "draft", True, "hardcover_8x8"))
        self.assertEqual(record["request"], sent)
        self.assertEqual(record["response"]["id"], "gelato-order-1")
        steps = {s["step"]: s for s in record["steps"]}
        self.assertEqual(list(steps), ["files", "catalog", "pdf", "link", "readback",
                                       "printOrderRemembered", "archive"])
        kept = archive.get(res["archiveId"])
        self.assertEqual((kept["provider"], kept["orderId"], kept["format"], kept["pageCount"], kept["sendLog"]),
                         ("gelato", "gelato-order-1", "hardcover_8x8", 30, res["sendLog"]))
        self.assertEqual(len(kept["files"]), 31)
        self.assertTrue(steps["readback"]["fileFetched"])                # Gelato already has our PDF
        self.assertEqual(steps["readback"]["pageCount"], 30)
        self.assertEqual(steps["files"]["pageCount"], 30)
        self.assertEqual(steps["catalog"]["geometry"]["coverMm"], [458.0, 246.0])
        self.assertEqual((steps["pdf"]["pdfPages"], steps["pdf"]["coverPx"]), (33, [466, 250]))
        self.assertLess(steps["pdf"]["coverTrimMm"], 10)
        self.assertEqual(steps["link"]["urls"], ["https://fake.trycloudflare.com/book.pdf"])
        self.assertNotIn("fake-gelato-key", json.dumps(record))

    def test_two_books_travel_as_items_of_one_draft(self):
        """Two books of one Etsy order (owner, 20.09.2026): one draft, one address, an item and a PDF of its
        own for each — a 30-page book and a 28-page one keep their own lengths."""
        vault.set("gelato_api_key", "fake-gelato-key")
        gelato._geometry.clear()
        gelato._products.clear()
        sent = {}

        def fake_call(method, url, body=None, **kw):
            self.assertTrue(gelato._allowed(method, url, body))
            if method == "GET" and "/cover-dimensions" in url:
                return self.COVER
            if method == "GET" and url.endswith("/orders/gelato-order-1"):
                session = sent["customerReferenceId"].removeprefix("local-review-")
                folder = core.data_path("tmp", "gelato", session)
                return {"items": [{"productUid": "p", "pageCount": 30, "fulfillmentStatus": "draft",
                                   "files": [{"type": "default", "mimeType": "application/pdf",
                                              "sizeBytes": (folder / name).stat().st_size}]}
                                  for name in ("book-1.pdf", "book-2.pdf")]}
            if method == "GET":
                return self.PRODUCT
            sent.update(body)
            return {"id": "gelato-order-1", "orderType": "draft", "fulfillmentStatus": "draft"}

        with tempfile.TemporaryDirectory() as d:
            emma, liam = Path(d) / "emma", Path(d) / "liam"
            for folder, pages in ((emma, 30), (liam, 28)):
                folder.mkdir()
                png(folder / "Cover.png", (466, 250), (1, 2, 3))
                for i in range(1, pages + 1):
                    png(folder / f"{i}.png", (100 + i, 100 + i), (i, i, i))
            creator._validation_cache.clear()
            address = {"firstName": "Ann", "lastName": "Lee", "addressLine1": "1 Main St", "city": "Austin",
                       "postCode": "73301", "country": "us", "state": "TX"}
            with mock.patch.object(gelato, "call", fake_call), \
                    mock.patch.object(tunnel.FileTunnel, "start", lambda self: "https://fake.trycloudflare.com"), \
                    mock.patch.object(tunnel.registry, "keep", lambda *a, **kw: None):
                res = creator.create_gelato_draft([{"folder": str(emma), "title": "4100000001 - Emma", "format": "hardcover_8x8"},
                                                   {"folder": str(liam), "title": "4100000001 - Liam", "format": "hardcover_8x8"}],
                                                  address, Job("t"))
        vault.set("gelato_api_key", None)
        self.assertEqual(sent["orderReferenceId"], "4100000001 - Emma, Liam")   # the receipt number stays in front
        self.assertEqual([i["pageCount"] for i in sent["items"]], [30, 28])
        self.assertEqual([i["files"][0]["url"] for i in sent["items"]],
                         ["https://fake.trycloudflare.com/book-1.pdf", "https://fake.trycloudflare.com/book-2.pdf"])
        self.assertEqual(len({i["itemReferenceId"] for i in sent["items"]}), 2)
        self.assertEqual([b["pageCount"] for b in res["books"]], [30, 28])
        self.assertEqual([b["pdfPages"] for b in res["books"]], [33, 31])
        kept = [archive.get(b["archiveId"]) for b in res["books"]]
        self.assertEqual([(k["orderId"], k["pageCount"]) for k in kept],
                         [("gelato-order-1", 30), ("gelato-order-1", 28)])
        record = journal(res["sendLog"])
        self.assertEqual([s["step"] for s in record["steps"]],
                         ["files", "catalog", "files", "catalog", "pdf", "pdf", "link", "readback", "readback",
                          "printOrderRemembered", "archive", "archive"])
        self.assertEqual([s["urls"] for s in record["steps"] if s["step"] == "link"],
                         [["https://fake.trycloudflare.com/book-1.pdf", "https://fake.trycloudflare.com/book-2.pdf"]])
        self.assertNotIn("fake-gelato-key", json.dumps(record))

    ADDRESS = {"firstName": "Ann", "lastName": "Lee", "addressLine1": "1 Main St", "city": "Berlin",
               "postCode": "10115", "country": "DE"}

    def test_28_pages_when_28_were_downloaded(self):
        """A book without one spread: Gelato is asked for 28 inner pages (and a cover sized for them)."""
        vault.set("gelato_api_key", "fake-gelato-key")
        gelato._geometry.clear()
        gelato._products.clear()
        sent, asked = {}, []

        def fake_call(method, url, body=None, **kw):
            self.assertTrue(gelato._allowed(method, url, body))
            asked.append(url)
            if method == "GET":
                return self.COVER if "/cover-dimensions" in url else self.PRODUCT
            sent.update(body)
            return {"id": "gelato-order-28", "orderType": "draft", "fulfillmentStatus": "draft"}

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            png(root / "Cover.png", (466, 250), (1, 2, 3))
            for i in range(1, 29):
                png(root / f"{i}.png", (100 + i, 100 + i), (i, i, i))
            creator._validation_cache.clear()
            checked = creator.validate("gelato", str(root))
            with mock.patch.object(gelato, "call", fake_call), \
                    mock.patch.object(tunnel.FileTunnel, "start", lambda self: "https://fake.trycloudflare.com"), \
                    mock.patch.object(tunnel.registry, "keep", lambda *a, **kw: None):
                res = creator.create_gelato_draft([{"folder": str(root), "title": "Book", "format": "hardcover_8x8"}], self.ADDRESS, Job("t"))
        vault.set("gelato_api_key", None)
        self.assertEqual((checked["ok"], checked["pageCount"], checked["expected"]), (True, 28, 29))
        self.assertEqual(sent["items"][0]["pageCount"], 28)
        self.assertTrue(any(u.endswith("cover-dimensions?pageCount=28") for u in asked))
        self.assertEqual((res["pdfPages"], res["pageCount"]), (31, 28))
        session = sent["customerReferenceId"].removeprefix("local-review-")
        pdf = core.data_path("tmp", "gelato", session, "book.pdf").read_bytes().decode("latin-1")
        widths = [int(w) for w in re.findall(r"/Width (\d+)", pdf)]
        self.assertEqual(widths, [466, self.BLANK] + [100 + i for i in range(1, 29)] + [self.BLANK])  # cover, blank, 28, blank

    def test_length_gelato_does_not_print_stops_before_anything_is_made(self):
        from studio import sendlog
        before = set(sendlog.SENDS.glob("*.json"))
        vault.set("gelato_api_key", "fake-gelato-key")
        gelato._geometry.clear()
        gelato._products.clear()
        calls = []

        def fake_call(method, url, body=None, **kw):  # a made-up format that starts at 30 pages
            calls.append(method)
            return {**self.PRODUCT, "validPageCounts": list(range(30, 202, 2))}

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            png(root / "Cover.png", (466, 250), (1, 2, 3))
            for i in range(1, 29):
                png(root / f"{i}.png", (40, 40), (i, i, i))
            creator._validation_cache.clear()
            with mock.patch.object(gelato, "call", fake_call), \
                    mock.patch.object(tunnel.FileTunnel, "start", side_effect=AssertionError("no link")):
                with self.assertRaises(JobError) as ctx:
                    creator.create_gelato_draft([{"folder": str(root), "title": "Book", "format": "softcover_8x8"}], self.ADDRESS, Job("t"))
        vault.set("gelato_api_key", None)
        gelato._products.clear()
        self.assertIn("Gelato не друкує Softcover 8×8 на 28 сторінках (можна від 30)", str(ctx.exception))
        self.assertEqual(calls, ["GET"])  # only the catalog was read: no PDF link, no draft
        new = sorted(set(sendlog.SENDS.glob("*.json")) - before)
        record = journal(new[0].name)
        self.assertEqual((len(new), record["ok"], record["format"]), (1, False, "softcover_8x8"))
        self.assertIn("на 28 сторінках", record["error"])
        self.assertEqual([s["step"] for s in record["steps"]], ["files"])

    def test_link_confirmed_through_public_dns_when_the_router_does_not_know_it_yet(self):
        link = tunnel.FileTunnel(Path("."), ("book.pdf",))
        link.public_url = "https://brand-new.trycloudflare.com"
        asked = []
        with mock.patch.object(tunnel, "_head_ok", lambda url: asked.append(url) or False), \
                mock.patch.object(tunnel, "_head_ok_public_dns", lambda url: len(asked) >= 3), \
                mock.patch.object(tunnel.time, "sleep", lambda s: None):
            link._wait_reachable()
        self.assertTrue(link.reachable)
        self.assertEqual(asked[0], "https://brand-new.trycloudflare.com/book.pdf")

    def test_journal_button_shows_the_newest_record(self):
        from types import SimpleNamespace
        from studio import desktop, sendlog
        import os
        import time
        newest = sendlog.write({"provider": "gelato", "title": "Newer", "steps": []})
        first = sendlog.write({"provider": "printify", "title": "Older", "steps": []})
        past = time.time() - 3600
        os.utime(first, (past, past))                                        # written an hour earlier
        with mock.patch.object(desktop, "open_in_explorer") as shown:
            sendlog._open(SimpleNamespace(json={}))                           # header icon: no record named
            sendlog._open(SimpleNamespace(json={"file": first.name}))          # result card: its own record
            sendlog._open(SimpleNamespace(json={"file": "..\\vault.json"}))    # anything else: the newest
        self.assertEqual([c.args[0] for c in shown.call_args_list], [newest, first, newest])

    def test_drafts_are_asked_for_in_the_order_search(self):
        bodies = []
        with mock.patch.object(gelato, "call", lambda method, url, body=None, **kw: bodies.append(body) or {"orders": []}):
            gelato.all_orders()
        self.assertEqual(bodies[0]["orderTypes"], ["order", "draft"])

    def test_saved_inch_products_become_the_metric_ones(self):
        old = {"gelato": {"formats": {
            "hardcover_8x8": {"label": "Hardcover 8×8", "productUid": "photobooks-hardcover_pf_8x8-inch-200x200-mm_pt_170-gsm-65lb-coated-silk_cl_4-4_ccl_4-4_bt_glued-left_ct_matt-lamination_prt_1-0_cpt_130-gsm-65-lb-cover-coated-silk_ver"},
            "softcover_5x5": {"label": "Softcover 5.5×5.5", "productUid": "photobooks-softcover_pf_5_5x5_5-inch-140x140-mm_pt_170-gsm-65lb-coated-silk_cl_4-4_ccl_4-4_bt_glued-left_ct_matt-lamination_prt_1-0_cpt_250-gsm-100-lb-cover-coated-silk_ver"},
        }}}
        with mock.patch.object(core, "read_json", lambda *a, **kw: old):
            saved = core.Settings().section("gelato")["formats"]
        self.assertEqual(saved, core.DEFAULT_SETTINGS["gelato"]["formats"])
        self.assertIn("_pf_200x200-mm-8x8-inch_", saved["hardcover_8x8"]["productUid"])
        self.assertIn("_pf_140x140-mm-5_5x5_5-inch_", saved["softcover_5x5"]["productUid"])

    def test_page_counts_of_every_format(self):
        gelato._products.clear()

        def fake_call(method, url, body=None, **kw):
            self.assertEqual(method, "GET")
            if "5_5x5_5" in url:
                raise gelato.GelatoError("немає з'єднання з Gelato", 502)
            return {"validPageCounts": [32, 28, 30]}

        with mock.patch.object(gelato, "call", fake_call):
            counts = creator.gelato_page_counts()
        gelato._products.clear()
        self.assertEqual(counts, {"hardcover_8x8": [28, 30, 32], "softcover_8x8": [28, 30, 32], "softcover_5x5": None})

    def test_canva_style_png_is_joined_without_touching_pixels(self):
        import struct
        import zlib
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "page.png"
            Image.new("RGB", (64, 48), (10, 120, 200)).save(src)
            data = src.read_bytes()
            # Re-chunk the pixel data into many tiny IDAT chunks, the way Canva writes (8 KB each there).
            pos, head, idat, tail = 8, [], b"", []
            while pos < len(data):
                ln, kind = struct.unpack(">I4s", data[pos:pos + 8])
                raw = data[pos:pos + 12 + ln]
                if kind == b"IDAT":
                    idat += data[pos + 8:pos + 8 + ln]
                elif idat:
                    tail.append(raw)
                else:
                    head.append(raw)
                pos += 12 + ln
            small = [idat[i:i + 7] for i in range(0, len(idat), 7)]
            chunked = [struct.pack(">I", len(c)) + b"IDAT" + c + struct.pack(">I", zlib.crc32(b"IDAT" + c) & 0xFFFFFFFF) for c in small]
            src.write_bytes(data[:8] + b"".join(head) + b"".join(chunked) + b"".join(tail))
            joined = creator._one_idat(src, root / "joined.png")
            self.assertEqual(joined.read_bytes().count(b"IDAT"), 1)
            with Image.open(src) as a, Image.open(joined) as b:
                self.assertEqual(a.tobytes(), b.tobytes())

    def test_only_a_really_wrong_cover_is_flagged(self):
        """The owner's Canva cover (4672×2464) always loses a few mm on Gelato — that is planned for and
        only journaled; a picture of a different shape altogether is still pointed out."""
        geo = {"coverMm": [408.72, 206.0], "pageMm": [206.0, 206.0], "marginMm": 3}  # 20×20 softcover, 28 pages
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            png(root / "Cover.png", (4672 // 20, 2464 // 20), (9, 9, 9))  # the usual Canva cover (1.896:1)
            png(root / "Square.png", (100, 100), (9, 9, 9))
            png(root / "1.png", (40, 40), (1, 1, 1))
            usual = creator.build_photobook_pdf(root / "Cover.png", [root / "1.png"], root / "a.pdf", geo)
            square = creator.build_photobook_pdf(root / "Square.png", [root / "1.png"], root / "b.pdf", geo)
        self.assertEqual(usual["warnings"], [])
        self.assertAlmostEqual(usual["coverTrimMm"], 4.8, delta=0.3)
        self.assertEqual((usual["pdfPages"], usual["coverPx"]), (4, [233, 123]))   # cover, blank, page, blank
        self.assertEqual(len(square["warnings"]), 1)
        self.assertIn("обріжуться", square["warnings"][0])


class CreatorStartsEmpty(unittest.TestCase):
    def test_old_folders_address_and_draft_list_are_forgotten(self):
        core.settings.update({"creator": {"printifyFolder": "D:\\old", "gelatoAddress": {"firstName": "Ann"}}})
        core.settings.update({"creator": {"gelatoFolder": "D:\\older"}})  # now the backup copy holds it too
        history = core.data_path("creator", "history.json")
        core.write_json(history, [{"title": "1 - Ann"}])
        core.write_json(history, [{"title": "2 - Bo"}])
        creator.forget_old_form()
        self.assertNotIn("creator", core.settings.get())
        self.assertNotIn("creator", core.read_json(core.data_path("settings.json"), {}))
        self.assertNotIn("creator", core.read_json(core.data_path("settings.json.bak"), {}))
        self.assertFalse(history.exists())
        self.assertFalse(history.with_name("history.json.bak").exists())
        status = creator._status(None)
        self.assertNotIn("history", status)
        self.assertNotIn("creator", status)
        creator.forget_old_form()  # nothing left to do the second time


class DroppedFolders(unittest.TestCase):
    def test_zip_is_unpacked_to_the_folder_with_the_cover(self):
        import zipfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = root / "book.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("Madelynn/Cover.png", b"png")
                zf.writestr("Madelynn/1.png", b"png")
                zf.writestr("Madelynn/notes.txt", b"skip")        # not a picture
                zf.writestr("__MACOSX/Madelynn/._Cover.png", b"x")  # macOS litter
                zf.writestr("../evil.png", b"x")                    # must never leave the folder
            target = root / "out" / "book"
            self.assertEqual(creator.extract_zip(archive, target), 2)
            self.assertEqual(creator.dropped_folder(root / "out"), target / "Madelynn")
            self.assertFalse((root / "out" / "evil.png").exists())
            self.assertFalse((root / "evil.png").exists())
            self.assertEqual(sorted(p.name for p in (target / "Madelynn").iterdir()), ["1.png", "Cover.png"])

    def test_only_pictures_inside_the_session_folder_are_accepted(self):
        self.assertEqual(creator._drop_rel("Madelynn/Cover.png"), Path("Madelynn", "Cover.png"))
        for bad in ("../x.png", "C:/Windows/x.png", "a/../../x.png", "book/run.exe", "", "._Cover.png"):
            with self.subTest(name=bad):
                self.assertIsNone(creator._drop_rel(bad))
        with self.assertRaises(Exception):
            creator._drop_root("../../etc")

    def test_etsy_text_arrives_readable(self):
        r = {"receipt_id": 1, "create_timestamp": 1757000000, "name": "Tom &amp; Ann", "transactions": [{
            "title": "Book 8&quot; &amp; more", "variations": [
                {"formatted_name": "Cover Type &amp; Size", "formatted_value": "8&quot; × 8&quot; Hardcover"}]}]}
        n = profit.normalize_receipt(r)
        self.assertEqual(n["customer_shipping_name"], "Tom & Ann")
        self.assertEqual(n["items"][0]["title"], 'Book 8" & more')
        self.assertEqual(n["items"][0]["variations"][0], {"name": "Cover Type & Size", "value": '8" × 8" Hardcover'})


class OpenUrlGuard(unittest.TestCase):
    def test_etsy_pages_never_open_on_this_computer(self):
        from types import SimpleNamespace
        from studio import settings_api
        from studio.server import ApiError
        open_url = lambda url: settings_api._open_url(SimpleNamespace(json={"url": url}))
        with mock.patch("webbrowser.open") as opened:
            for url in ("https://www.etsy.com/listing/4542179572", "https://ETSY.com/your/orders/sold",
                        "https://www.etsy.com/oauth/connect/../listing/1"):
                with self.subTest(url=url), self.assertRaises(ApiError):
                    open_url(url)
            open_url("https://www.canva.com/design/abc/edit")
            open_url("https://www.etsy.com/oauth/connect?response_type=code")  # sign-in, after the Kyiv check
        self.assertEqual(opened.call_count, 2)


class ProfitSyncFlow(unittest.TestCase):
    def test_sync_builds_snapshot(self):
        vault.set("printify_token", "fake")
        m = lambda v: {"amount": int(v * 100), "divisor": 100, "currency_code": "USD"}
        receipt = {"receipt_id": 111, "create_timestamp": 1757000000, "name": "Ann Lee", "grandtotal": m(40),
                   "subtotal": m(34), "total_price": m(34), "total_shipping_cost": m(6), "transactions": [{}]}
        porder = {"id": "a" * 24, "total_price": 1500, "total_shipping": 700, "total_tax": 0,
                  "created_at": "2025-09-04 12:00:00+00:00", "metadata": {"shop_order_id": "111"},
                  "address_to": {"first_name": "Ann", "last_name": "Lee"}, "line_items": []}
        with mock.patch.object(etsy, "tokens", lambda: {"access_token": "1.x"}), \
                mock.patch.object(etsy, "fetch_all_receipts", lambda progress=None, min_last_modified=None: ([receipt], 1, "Shop")), \
                mock.patch.object(printify, "shops", lambda: [{"id": 5, "title": "PShop"}]), \
                mock.patch.object(printify, "all_orders", lambda shop, progress=None: [porder]):
            result = profit._sync(Job("t"))
        vault.set("printify_token", None)
        self.assertEqual(result["receipts"], 1)
        self.assertEqual(result["matched"], 1)
        row = profit.build_view()["rows"][0]
        self.assertEqual(row["pod_total_cost"], 22.0)
        self.assertAlmostEqual(row["profit"], round(row["etsy_net"] - 22.0, 2))


class EtsyOAuth(unittest.TestCase):
    def test_pkce_url_and_code_exchange(self):
        vault.set("etsy_keystring", "keystring123")
        vault.set("etsy_shared_secret", "secret456")
        start = etsy.start_oauth()
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(start["authUrl"]).query)
        self.assertEqual(q["client_id"], ["keystring123"])
        self.assertEqual(q["scope"], ["shops_r transactions_r"])
        self.assertEqual(q["code_challenge_method"], ["S256"])

        def fake_json(method, url, **kw):
            if url == etsy.TOKEN_URL:
                self.assertEqual(kw["form"]["grant_type"], "authorization_code")
                self.assertTrue(kw["form"]["code_verifier"])
                return {"access_token": "777.abc", "refresh_token": "777.ref", "expires_in": 3600}
            self.assertEqual(kw["headers"]["x-api-key"], "keystring123:secret456")
            self.assertEqual(kw["headers"]["Authorization"], "Bearer 777.abc")
            if url.endswith("/users/me"):
                return {"user_id": 777, "shop_id": 63208655}
            if url.endswith("/shops/63208655"):
                return {"shop_id": 63208655, "shop_name": "MoonMeadowStories"}
            raise AssertionError(url)

        with mock.patch.object(httpc, "request_json", fake_json):
            status = etsy.complete_oauth("the-code", start["state"])
        self.assertTrue(status["connected"])
        self.assertEqual(status["shopName"], "MoonMeadowStories")
        with self.assertRaises(etsy.EtsyError):  # the same state cannot be used twice
            etsy.complete_oauth("the-code", start["state"])

        # A refresh token already used by another app: Etsy answers 400 with an empty body.
        tokens = etsy.tokens()
        tokens["expires_at"] = 0
        etsy.save_tokens(tokens)

        def revoked(method, url, **kw):
            raise httpc.HttpError("HTTP 400", status=400, body="", url=url)

        with mock.patch.object(httpc, "request_json", revoked):
            with self.assertRaises(etsy.EtsyError) as ctx:
                etsy.refresh_tokens()
        self.assertEqual(ctx.exception.extra.get("code"), "etsy_auth")
        etsy.disconnect()
        for name in ("etsy_keystring", "etsy_shared_secret"):
            vault.set(name, None)


if __name__ == "__main__":
    unittest.main()
