import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core, creator, gelato, library, printify
from studio.server import ApiError


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


class PrintifyValidation(unittest.TestCase):
    def setUp(self):
        self._saved = core.settings.get()
        core.settings.update({"printify": {"coverSize": [60, 30], "pageSize": [40, 40]}})
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        png(self.root / "Cover.png", (60, 30))
        for i in range(1, 25):
            png(self.root / f"{i}.png", (40, 40), (i * 9, 100, 150))
        creator._validation_cache.clear()

    def tearDown(self):
        core.settings.replace_section("printify", self._saved["printify"])
        self.dir.cleanup()

    def test_ok(self):
        res = creator.validate("printify", str(self.root))
        self.assertTrue(res["ok"], res["errors"])
        self.assertEqual(res["found"], 25)

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
        creator._validation_cache.clear()

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
        creator._validation_cache.clear()
        rows = {r["file"]: r for r in creator.validate("printify", str(self.folder), None)["files"]}
        self.assertTrue(rows["7.png"]["replaced"])
        self.assertFalse(rows["8.png"]["replaced"])
        self.assertFalse(rows["Cover.png"]["replaced"])
        creator.restore_page(str(self.folder), "7.png")
        creator._validation_cache.clear()
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
            creator._validation_cache.clear()
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

    def test_gelato_only_drafts(self):
        self.assertTrue(gelato._allowed("POST", f"{gelato.ORDER_API}/orders", {"orderType": "draft"}))
        self.assertFalse(gelato._allowed("POST", f"{gelato.ORDER_API}/orders", {"orderType": "order"}))
        self.assertFalse(gelato._allowed("POST", f"{gelato.ORDER_API}/orders/1:cancel", {}))
        self.assertTrue(gelato._allowed("POST", f"{gelato.ORDER_API}/orders:search", {}))


if __name__ == "__main__":
    unittest.main()
