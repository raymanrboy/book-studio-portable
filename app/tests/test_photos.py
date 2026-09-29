"""Photo mockups (the owner, 30.09.2026): the templates by category, the clipboard's order — the template, the book's
reference, the category's JSON prompt — the finished photo caught into the book's etsy/ folder, the «Фото» step; the
same without a book (only the template and the prompt, nothing caught); the Mockups keep the Canva cover. All in the
sandbox: the books, the templates, Downloads and the clipboard are files in the tests' own folder."""
import importlib.util
import json
import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from tests import __init__  # noqa: F401  (sets a temporary data folder and the sandbox)
from studio import core, photos
from studio.server import ApiError
from studio.workshop import books, generate, routes

TOOLS = Path(__file__).resolve().parents[1] / "tools"
_spec = importlib.util.spec_from_file_location("sample_books", TOOLS / "sample_books.py")
sample_books = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sample_books)

H, S = "40.moonlit-garden-lullaby", "41.little-lamb-prayers"   # 40 has the references, 41 none


def photo(path: Path, color=(120, 90, 60), size=(600, 600)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)
    return path


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = sample_books.make_books(core.WORKSHOP_BOOKS)
        self.templates = photos.templates_dir()
        shutil.rmtree(self.templates, ignore_errors=True)
        sample_books.make_photo_templates(self.templates)
        for folder in (generate.downloads_folder(), core.data_path("clipboard"), core.data_path("recycle-bin")):
            shutil.rmtree(folder, ignore_errors=True)
        self.downloads = generate.downloads_folder()
        self.downloads.mkdir(parents=True)
        self.s = generate.Session(watch=False)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        shutil.rmtree(self.templates, ignore_errors=True)

    def clip(self):
        txt, png = core.data_path("clipboard", "clipboard.txt"), core.data_path("clipboard", "clipboard.png")
        return txt.read_text(encoding="utf-8") if txt.exists() else ("<image>" if png.exists() else None)

    def look(self):
        self.s.look()  # the first look sees the size, the second takes the picture
        self.s.look()


class TheTemplates(Base):
    def test_five_categories_in_the_pages_order_with_their_templates(self):
        cats = photos.templates()
        self.assertEqual([c["key"] for c in cats], ["main", "open-book", "grandma", "child", "shelf", "video", "size"])
        self.assertEqual([t["name"] for t in cats[0]["templates"]],
                         ["main-01-pink-roses.png", "main-02-leaf-shadows.png", "main-03-fairy-lights.png"])
        (self.templates / "main" / "notes.txt").write_text("x")   # only pictures count
        self.assertEqual(len(photos.templates()[0]["templates"]), 3)

    def test_a_dropped_photo_gets_the_categorys_next_number_and_a_removed_one_goes_to_the_bin(self):
        src = photo(core.data_path("tmp", "any name.JPEG"))
        res = photos.add_template("shelf", src, "any name.JPEG")
        self.assertEqual(res["name"], "shelf-03.jpg")
        self.assertTrue((self.templates / "shelf" / "shelf-03.jpg").is_file())
        before = photos.signature()
        photos.remove_template("shelf", "shelf-03.jpg")
        self.assertFalse((self.templates / "shelf" / "shelf-03.jpg").exists())
        self.assertTrue(any(core.data_path("recycle-bin").glob("shelf-03.jpg*")))   # never deleted for good
        self.assertNotEqual(photos.signature(), before)

    def test_only_a_real_template_and_a_real_category(self):
        with self.assertRaises(ApiError):
            photos.template_file("main", "../../secret.png")
        with self.assertRaises(ApiError):
            photos.template_file("trailer", "x.png")
        with self.assertRaises(ApiError):
            photos.add_template("main", core.data_path("tmp", "nothing.png"), "nothing.png")


class ThePrompts(Base):
    def test_one_json_prompt_per_category_that_changes_only_the_book(self):
        for c in photos.CATEGORIES:
            p = json.loads(photos.prompt(c["key"]))
            self.assertIn("ONLY the blank white book", p["edit_scope"])
            self.assertIn("no white surface", p["no_blank_left"])
            self.assertIn("never mirrored", " ".join(p["cover_fidelity"]))
        texts = {c["key"]: photos.prompt(c["key"]) for c in photos.CATEGORIES}
        self.assertEqual(len(set(texts.values())), 7)                       # each its own scene
        self.assertIn("spine", json.loads(texts["grandma"])["inputs"]["image_2"])   # the flat Canva cover
        self.assertIn("open spread", " ".join(json.loads(texts["open-book"])["book_placement"]))


class InABook(Base):
    def test_the_clipboard_goes_template_then_the_categorys_reference_then_the_prompt(self):
        refs = {"main": "1. Cover 1.png", "child": "1. Cover 1.png", "shelf": "1. Cover 1.png",
                "open-book": "Cover & Open 1 (6-7).png", "grandma": "canva-cover.png", "video": "1. Cover 1.png",
                "size": "1. Cover 1.png"}
        for c in photos.CATEGORIES:
            template = photos.templates()[[x["key"] for x in photos.CATEGORIES].index(c["key"])]["templates"][0]["name"]
            label, items = photos.items(H, c["key"], template)
            self.assertEqual([i["kind"] for i in items], ["image", "image", "text"])
            self.assertEqual(Path(items[0]["path"]).name, template)
            self.assertEqual(Path(items[1]["path"]).name, refs[c["key"]])
            self.assertEqual(items[2]["text"], photos.prompt(c["key"]))

    def test_the_newest_cover_and_open_is_taken_and_a_missing_reference_is_said(self):
        m = self.dir / H / "mockups"
        newer = photo(m / "Cover & Open 1 (6-7) (2).png")
        import os
        os.utime(newer, (newer.stat().st_mtime + 60,) * 2)
        self.assertEqual(photos.references(self.dir / H)["cover-open"], "Cover & Open 1 (6-7) (2).png")
        with self.assertRaises(ApiError) as e:
            photos.items(S, "main", "main-01-pink-roses.png")
        self.assertIn("Cover 1", str(e.exception))
        with self.assertRaises(ApiError) as e:
            photos.items(S, "grandma", "grandma-01-baby-daylight.png")
        self.assertIn("Canva", str(e.exception))

    def test_a_caught_photo_lands_in_etsy_the_one_before_is_kept_and_the_step_counts(self):
        (self.downloads / "old.png").write_bytes(b"there before")
        st = self.s.start_photo(H, "grandma", "grandma-02-baby-evening.png")
        self.assertEqual(st["active"]["items"], ["фото-заготовка", "Обкладинка з Canva", "промпт"])
        self.assertEqual(st["active"]["key"], "photo:grandma")
        self.assertEqual(self.clip(), "<image>")                   # the template first
        self.s.next_item()
        self.s.next_item()
        self.assertIn('"task"', self.clip())                        # then the prompt
        self.assertIsNotNone(self.s.status()["active"])             # still waiting for the photo
        photo(self.downloads / "Gemini_Generated.png")
        self.look()
        etsy = self.dir / H / "etsy"
        self.assertTrue((etsy / "photo-grandma.png").is_file())
        self.assertFalse((self.downloads / "Gemini_Generated.png").exists())   # moved out of Downloads
        self.assertTrue((self.downloads / "old.png").exists())
        self.assertIsNone(self.s.status()["active"])
        self.assertEqual(self.s.status()["last"]["note"], "Фото «Бабуся читає» на місці")
        state = books.detail(H)["photos"]
        card = next(c for c in state["cards"] if c["key"] == "grandma")
        self.assertEqual((card["photo"], card["template"]), ("photo-grandma.png", "grandma-02-baby-evening.png"))
        step = next(s for s in books.detail(H)["steps"] if s["key"] == "photos")
        self.assertEqual((step["state"], step["count"], step["total"]), ("part", 1, 7))
        # again: the new one in its place, the old one in .replaced
        self.s.start_photo(H, "grandma", "grandma-01-baby-daylight.png")
        photo(self.downloads / "Gemini_2.jpg", (10, 200, 10))
        self.look()
        self.assertEqual(sorted(p.name for p in etsy.iterdir()), ["photo-grandma.jpg"])
        self.assertTrue(any((self.dir / H / ".replaced").glob("*photo-grandma.png")))
        photos.remove(H, "grandma")
        self.assertFalse(list(etsy.iterdir()))
        self.assertEqual(next(s for s in books.detail(H)["steps"] if s["key"] == "photos")["state"], "todo")

    def test_the_step_is_done_with_all_five_or_by_hand(self):
        for c in photos.CATEGORIES:
            photos.place(H, c["key"], photo(core.data_path("tmp", "p.png")), "p.png")
        self.assertEqual(next(s for s in books.detail(H)["steps"] if s["key"] == "photos")["state"], "done")
        books.set_mark(S, "photos", True)                           # a category skipped: ticked by hand
        self.assertEqual(next(s for s in books.detail(S)["steps"] if s["key"] == "photos")["state"], "done")
        self.assertEqual([s["key"] for s in books.detail(S)["steps"]][-3:], ["mockups", "photos", "library"])

    def test_a_photo_and_the_canva_cover_dropped_on_their_frames(self):
        src = photo(core.data_path("tmp", "drop.png"))

        def drop(key, name="drop.png"):
            req = SimpleNamespace(groups=[S], param=lambda n: {"key": key, "name": name}.get(n),
                                  body_to_file=lambda tmp, limit: shutil.copyfile(src, tmp))
            return routes._place(req)
        self.assertEqual(drop("photo:shelf")["note"], "Фото «На полиці» на місці")
        self.assertTrue((self.dir / S / "etsy" / "photo-shelf.png").is_file())
        drop("canva-cover", "Cover.png")
        self.assertTrue((self.dir / S / "mockups" / "canva-cover.png").is_file())
        self.assertEqual(photos.references(self.dir / S)["canva-cover"], "canva-cover.png")
        self.assertEqual(books.mockups_state(self.dir / S)["mockups"], 0)   # the Canva cover is no mockup
        self.assertIn("etsy/photo-shelf.png", books.detail(S)["v"])     # the page redraws when a photo comes


class WithoutABook(Base):
    def test_only_the_template_and_the_prompt_and_nothing_is_caught(self):
        st = self.s.start_photo(None, "main", "main-01-pink-roses.png")
        self.assertEqual(st["active"]["items"], ["фото-заготовка", "промпт"])
        self.assertFalse(st["active"]["catch"])
        self.assertEqual(self.clip(), "<image>")
        st = self.s.next_item()                       # Ctrl+V in Chrome: the prompt goes in, and that is all
        self.assertIn('"task"', self.clip())
        self.assertIsNone(st["active"])
        self.assertIn("промпт у буфері", st["last"]["note"])
        photo(self.downloads / "Gemini.png")
        self.look()
        self.assertTrue((self.downloads / "Gemini.png").exists())   # nothing caught


class TheEtsyFolder(Base):
    def test_the_whole_scene_mockups_go_into_etsy_once_and_a_new_spread_replaces_the_old(self):
        from studio import mockups
        m, etsy = self.dir / H / "mockups", self.dir / H / "etsy"
        photo(m / "All & Open 1 (8-9).png")
        mockups._to_etsy({"folder": str(m)})
        self.assertEqual(sorted(p.name for p in etsy.iterdir()), ["All & Open 1 (8-9).png", "Cover & Open 1 (6-7).png"])
        self.assertTrue((m / "All & Open 1 (8-9).png").is_file())            # copied, the mockup stays
        self.assertEqual(photos.scenes_to_etsy(self.dir / H), [])           # the same ones: nothing again
        import os
        newer = photo(m / "Cover & Open 1 (12-13).png")
        os.utime(newer, (newer.stat().st_mtime + 60,) * 2)
        self.assertEqual(photos.scenes_to_etsy(self.dir / H), ["Cover & Open 1 (12-13).png"])
        self.assertFalse((etsy / "Cover & Open 1 (6-7).png").exists())
        self.assertTrue(any((self.dir / H / ".replaced").glob("*Cover & Open 1 (6-7).png")))
        mockups._to_etsy({"folder": str(core.data_path("somewhere", "mockups"))})   # not a Workshop book: nothing


class TheMockupsKeepTheCanvaCover(Base):
    def test_a_run_for_a_workshop_book_keeps_the_demo_books_cover(self):
        from studio import mockups
        cover = photo(core.data_path("tmp", "cover.png"), size=(1074, 570))
        mockups._keep_canva_cover(S, {"cover": str(cover)})
        self.assertTrue((self.dir / S / "mockups" / "canva-cover.png").is_file())
        mockups._keep_canva_cover(S, {"cover": None})   # no cover in the ZIP: nothing happens


if __name__ == "__main__":
    unittest.main()
