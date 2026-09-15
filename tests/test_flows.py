"""End-to-end flows with the external services replaced by fakes (no network, no real accounts)."""
import json
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

from PIL import Image

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core, creator, etsy, gelato, httpc, printify, profit, tunnel
from studio.jobs import Job, JobError
from studio.vault import vault


def png(path: Path, size, color):
    Image.new("RGB", size, color).save(path, "PNG")


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

    def __call__(self, method, path, body=None, action="", timeout=60, retries=3, params=""):
        printify._check(method, path)  # the real allowlist still applies
        self.calls.append((method, path))
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
            res = creator.create_printify_draft(str(self.root), "4174712220 - Caleb", Job("t"))
            self.assertEqual(res["total"], 25)
            self.assertEqual(res["uploaded"], 25)
            self.assertTrue(res["verified"])
            self.assertTrue(res["masterSafe"])
            payload = self.fake.created[0]
            self.assertEqual(payload["title"], "4174712220 - Caleb")
            positions = [p["position"] for p in payload["print_areas"][0]["placeholders"]]
            self.assertEqual(positions, ["cover"] + [f"page_{i}" for i in range(1, 25)])
            # page_7 must carry exactly the image uploaded from 7.png
            page7 = payload["print_areas"][0]["placeholders"][7]["images"][0]["id"]
            self.assertEqual(self.fake.uploads[page7], "7.png")
            # A second book from the same folder re-uses every uploaded image.
            res2 = creator.create_printify_draft(str(self.root), "Second", Job("t"))
            self.assertEqual(res2["uploaded"], 0)
            self.assertEqual(res2["reused"], 25)
        self.assertFalse(any(m == "POST" and "publish" in p for m, p in self.fake.calls))

    def test_invalid_folder_uploads_nothing(self):
        (self.root / "12.png").unlink()
        with mock.patch.object(printify, "call", self.fake):
            with self.assertRaises(JobError):
                creator.create_printify_draft(str(self.root), "X", Job("t"))
        self.assertEqual(self.fake.uploads, {})
        self.assertEqual(self.fake.created, [])

    def test_upload_failure_creates_no_product(self):
        def flaky(method, path, *a, **kw):
            if method == "POST" and path == "uploads/images.json" and len(self.fake.uploads) == 20:
                raise printify.PrintifyError("Завантаження: Printify повернув помилку 500.", 502, {"upstream": 500})
            return self.fake(method, path, *a, **kw)
        with mock.patch.object(printify, "call", flaky):
            with self.assertRaises(JobError) as ctx:
                creator.create_printify_draft(str(self.root), "X", Job("t"))
        self.assertIn("повторний запуск продовжить", str(ctx.exception))
        self.assertEqual(self.fake.created, [])

    def test_ambiguous_create_is_not_retried(self):
        def timeout_on_create(method, path, *a, **kw):
            if method == "POST" and path.endswith("/products.json"):
                raise printify.PrintifyError("немає з'єднання", 502, {"ambiguous": True, "upstream": None})
            return self.fake(method, path, *a, **kw)
        with mock.patch.object(printify, "call", timeout_on_create):
            with self.assertRaises(JobError) as ctx:
                creator.create_printify_draft(str(self.root), "X", Job("t"))
        self.assertIn("НЕ запускайте повторно", str(ctx.exception))


class GelatoDraftFlow(unittest.TestCase):
    def test_draft_payload(self):
        vault.set("gelato_api_key", "fake-gelato-key")
        sent = {}

        def fake_call(method, url, body=None, **kw):
            self.assertTrue(gelato._allowed(method, url, body))
            sent.update(body)
            return {"id": "gelato-order-1", "orderType": "draft", "fulfillmentStatus": "draft"}

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            png(root / "Cover.png", (80, 40), (1, 2, 3))
            for i in range(1, 31):
                png(root / f"{i}.png", (40, 40), (i, i, i))
            creator._validation_cache.clear()
            address = {"firstName": "Ann", "lastName": "Lee", "addressLine1": "1 Main St", "city": "Austin",
                       "postCode": "73301", "country": "us", "state": "TX"}
            with mock.patch.object(gelato, "call", fake_call), \
                    mock.patch.object(tunnel.FileTunnel, "start", lambda self: "https://fake.trycloudflare.com"), \
                    mock.patch.object(tunnel.registry, "keep", lambda *a, **kw: None):
                res = creator.create_gelato_draft(str(root), "Book", "hardcover_8x8", address, Job("t"))
        vault.set("gelato_api_key", None)
        self.assertEqual(res["orderId"], "gelato-order-1")
        self.assertEqual(sent["orderType"], "draft")
        item = sent["items"][0]
        self.assertEqual(item["pageCount"], 30)
        self.assertEqual(item["files"], [{"type": "default", "url": "https://fake.trycloudflare.com/cover.png"},
                                         {"type": "inside", "url": "https://fake.trycloudflare.com/interior.pdf"}])
        self.assertEqual(sent["shippingAddress"]["country"], "US")
        self.assertEqual(sent["metadata"][0], {"key": "title", "value": "Book"})


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
