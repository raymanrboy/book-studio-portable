"""Photo mockups (the owner, 30.09.2026): the templates by category, the clipboard's order — the template, the book's
reference, the category's JSON prompt — the finished photo caught into the book's etsy/ folder, the «Фото» step; the
same without a book (only the template and the prompt, nothing caught); the Mockups keep the Canva cover. All in the
sandbox: the books, the templates, Downloads and the clipboard are files in the tests' own folder."""
import importlib.util
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from tests import __init__  # noqa: F401  (sets a temporary data folder and the sandbox)
from studio import aside, core, photos
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


def seconds(path: Path) -> float:
    """A video's length, as ffmpeg reads it."""
    out = subprocess.run([photos.ffmpeg(), "-hide_banner", "-i", str(path)], capture_output=True).stderr.decode()
    h, m, s = out.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def video(path: Path, length: float = 5) -> Path:
    """A made-up video with sound (ffmpeg's test pattern) — as Gemini Omni would give one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([photos.ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", f"testsrc=size=180x320:rate=24:duration={length}",
                    "-f", "lavfi", "-i", f"sine=frequency=440:duration={length}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path)], check=True)
    return path


HAS_FFMPEG = bool(shutil.which("ffmpeg"))


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = sample_books.make_books(core.WORKSHOP_BOOKS)
        self.templates = photos.templates_dir()
        shutil.rmtree(self.templates, ignore_errors=True)
        sample_books.make_photo_templates(self.templates)
        for folder in (generate.downloads_folder(), core.data_path("clipboard"), core.data_path("recycle-bin"), core.data_path("aside")):
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
        self.assertEqual([c["key"] for c in cats],
                         ["main", "product", "grandma", "child", "shelf", "video", "size"])
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
        token = photos.remove_template("shelf", "shelf-03.jpg")["undo"]
        self.assertFalse((self.templates / "shelf" / "shelf-03.jpg").exists())
        self.assertNotEqual(photos.signature(), before)
        aside.restore(token)                                                       # «Скасувати»
        self.assertTrue((self.templates / "shelf" / "shelf-03.jpg").is_file())
        photos.remove_template("shelf", "shelf-03.jpg")
        self.assertEqual(aside.flush(0), 1)                                        # minutes later: the Recycle Bin
        self.assertTrue(any(core.data_path("recycle-bin").glob("shelf-03.jpg*")))   # never deleted for good

    def test_only_a_real_template_and_a_real_category(self):
        with self.assertRaises(ApiError):
            photos.template_file("main", "../../secret.png")
        with self.assertRaises(ApiError):
            photos.template_file("trailer", "x.png")
        with self.assertRaises(ApiError):
            photos.add_template("main", core.data_path("tmp", "nothing.png"), "nothing.png")


class ThePrompts(Base):
    def test_one_json_prompt_per_category_that_changes_only_the_book(self):
        for c in photos.PHOTOS:
            p = json.loads(photos.prompt(c["key"]))
            self.assertIn("ONLY the blank white book", p["edit_scope"])
            self.assertIn("no white surface", p["no_blank_left"])
            self.assertIn("never mirrored", " ".join(p["cover_fidelity"]))
        texts = {c["key"]: photos.prompt(c["key"]) for c in photos.PHOTOS}
        self.assertEqual(len(set(texts.values())), 6)                       # each its own scene
        self.assertIn("spine", json.loads(texts["grandma"])["inputs"]["image_2"])   # the flat Canva cover
        self.assertIn("callout", " ".join(json.loads(texts["product"])["book_placement"]))


class InABook(Base):
    def test_the_clipboard_goes_template_then_the_categorys_reference_then_the_prompt(self):
        refs = {"main": "1. Cover 1.png", "child": "1. Cover 1.png", "shelf": "1. Cover 1.png",
                "product": "1. Cover 1.png", "grandma": "canva-cover.png", "video": "1. Cover 1.png",
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
        self.assertTrue((etsy / "03 photo-grandma.png").is_file())   # its number in the listing
        self.assertFalse((self.downloads / "Gemini_Generated.png").exists())   # moved out of Downloads
        self.assertTrue((self.downloads / "old.png").exists())
        self.assertIsNone(self.s.status()["active"])
        self.assertEqual(self.s.status()["last"]["note"], "Фото «Бабуся читає» на місці")
        state = books.detail(H)["photos"]
        card = next(c for c in state["cards"] if c["key"] == "grandma")
        self.assertEqual((card["photo"], card["template"]), ("03 photo-grandma.png", "grandma-02-baby-evening.png"))
        step = next(s for s in books.detail(H)["steps"] if s["key"] == "photos")
        self.assertEqual((step["state"], step["count"], step["total"]), ("part", 1, 7))
        # again: the new one in its place, the old one in .replaced
        self.s.start_photo(H, "grandma", "grandma-01-baby-daylight.png")
        photo(self.downloads / "Gemini_2.jpg", (10, 200, 10))
        self.look()
        self.assertEqual(sorted(p.name for p in etsy.iterdir()), ["03 photo-grandma.jpg"])
        self.assertTrue(any((self.dir / H / ".replaced").glob("*photo-grandma.png")))
        photos.remove(H, "grandma")
        self.assertFalse(list(etsy.iterdir()))
        self.assertEqual(next(s for s in books.detail(H)["steps"] if s["key"] == "photos")["state"], "todo")

    def test_the_step_is_done_with_all_five_or_by_hand(self):
        for c in photos.PHOTOS:
            photos.place(H, c["key"], photo(core.data_path("tmp", "p.png")), "p.png")
        self.assertEqual(next(s for s in books.detail(H)["steps"] if s["key"] == "photos")["state"], "part")
        (self.dir / H / "etsy" / "video-video.mp4").write_bytes(b"a video")   # the video category counts too
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
        self.assertTrue((self.dir / S / "etsy" / "15 photo-shelf.png").is_file())
        drop("canva-cover", "Cover.png")
        self.assertTrue((self.dir / S / "mockups" / "canva-cover.png").is_file())
        self.assertEqual(photos.references(self.dir / S)["canva-cover"], "canva-cover.png")
        self.assertEqual(books.mockups_state(self.dir / S)["mockups"], 0)   # the Canva cover is no mockup
        self.assertIn("etsy/15 photo-shelf.png", books.detail(S)["v"])     # the page redraws when a photo comes


class TheOmniVideo(Base):
    def test_the_owners_video_prompt_goes_in_as_it_is(self):
        text = photos.prompt("video")
        self.assertTrue(text.startswith("Animate this exact scene."))           # plain text, not a JSON object
        self.assertIn("pushes in towards the small book with confident momentum", text)   # the camera comes in
        self.assertIn("A woman's right hand and forearm enter from the right side", text)   # the right hand, from the right
        self.assertIn("grips the small book firmly by its lower right corner", text)        # a corner, not the page edge
        self.assertIn("tilts it back gently, about 10 degrees", text)                      # a little tilt, a number
        self.assertIn("carries the small book out of the frame", text)                     # every second has its motion
        self.assertIn("handheld phone shot", text)                                          # the handheld feel
        for word in ("open", "page", "flip", "turn"):                       # what a generator must not be given the idea of
            self.assertNotIn(word, text.lower())
        self.assertIn("small book", text)
        st = self.s.start_photo(H, "video", "video-01-sofa.png")
        self.assertEqual(st["active"]["items"], ["фото-заготовка", "Cover 1", "промпт"])
        self.assertTrue(st["active"]["catch"] and st["active"]["video"])
        self.s.next_item()
        self.s.next_item()
        self.assertEqual(self.clip(), text)
        self.assertTrue(next(c for c in books.detail(H)["photos"]["cards"] if c["key"] == "video")["omni"])
        with self.assertRaises(ApiError):                                        # a picture is no video
            photos.place(H, "video", photo(core.data_path("tmp", "p.png")), "p.png")

    @unittest.skipUnless(HAS_FFMPEG, "no ffmpeg on this PC")
    def test_the_video_is_caught_its_first_half_second_cut_and_the_uncut_kept(self):
        self.s.start_photo(H, "video", "video-01-sofa.png")
        photo(self.downloads / "Gemini.png")                  # a picture is not what this category waits for
        video(self.downloads / "Gemini_Omni.mp4", length=5)
        self.look()
        etsy, originals = self.dir / H / "etsy", self.dir / H / "originals"
        self.assertTrue((self.downloads / "Gemini.png").exists())
        self.assertFalse((self.downloads / "Gemini_Omni.mp4").exists())          # moved out of Downloads
        self.assertAlmostEqual(seconds(etsy / "02 video-video.mp4"), 4.5, delta=0.2)   # 5 s − the first 0.5
        self.assertAlmostEqual(seconds(originals / "video-video.mp4"), 5, delta=0.2)
        self.assertIsNone(self.s.status()["active"])
        self.assertIn("перші 0,5 с обрізано", self.s.status()["last"]["note"])
        card = next(c for c in books.detail(H)["photos"]["cards"] if c["key"] == "video")
        self.assertEqual((card["photo"], card["template"]), ("02 video-video.mp4", "video-01-sofa.png"))
        self.assertEqual(books.media_file(H, "etsy", "02 video-video.mp4").name, "02 video-video.mp4")
        # again, dropped by hand: the new one in its place, both old ones in .replaced
        photos.place(H, "video", video(core.data_path("tmp", "v.mov"), length=4), "v.mov")
        self.assertEqual(sorted(p.name for p in etsy.iterdir()), ["02 video-video.mp4"])
        self.assertAlmostEqual(seconds(etsy / "02 video-video.mp4"), 3.5, delta=0.2)
        self.assertTrue((originals / "video-video.mov").is_file())
        self.assertEqual(len(list((self.dir / H / ".replaced").glob("*video-video.mp4"))), 2)
        photos.remove(H, "video")
        self.assertFalse(list(etsy.iterdir()))

    @unittest.skipUnless(HAS_FFMPEG, "no ffmpeg on this PC")
    def test_a_video_too_short_to_cut_is_said_and_nothing_changes(self):
        with self.assertRaises(ApiError) as e:
            photos.place(H, "video", video(core.data_path("tmp", "short.mp4"), length=0.3), "short.mp4")
        self.assertIn("0,5 с", str(e.exception))
        self.assertFalse((self.dir / H / "etsy").exists() and list((self.dir / H / "etsy").iterdir()))


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
        self.assertEqual(sorted(p.name for p in etsy.iterdir()), ["04 All & Open 1 (8-9).png", "07 Cover & Open 1 (6-7).png"])
        self.assertTrue((m / "All & Open 1 (8-9).png").is_file())            # copied, the mockup stays
        self.assertEqual(photos.scenes_to_etsy(self.dir / H), [])           # the same ones: nothing again
        import os
        newer = photo(m / "Cover & Open 1 (12-13).png")
        os.utime(newer, (newer.stat().st_mtime + 60,) * 2)
        self.assertEqual(photos.scenes_to_etsy(self.dir / H), ["Cover & Open 1 (12-13).png"])
        self.assertFalse((etsy / "07 Cover & Open 1 (6-7).png").exists())
        self.assertTrue((etsy / "07 Cover & Open 1 (12-13).png").is_file())
        self.assertTrue(any((self.dir / H / ".replaced").glob("*Cover & Open 1 (6-7).png")))
        mockups._to_etsy({"folder": str(core.data_path("somewhere", "mockups"))})   # not a Workshop book: nothing

    def test_the_owners_order_numbers_in_front_and_his_own_files_left_as_they_are(self):
        from studio.slides import store
        book, etsy = self.dir / H, self.dir / H / "etsy"
        m = book / "mockups"
        photo(m / "All & Open 1 (8-9).png")
        photos.scenes_to_etsy(book)                                  # 04 and 06 (Cover & Open 1 (6-7) — sample)
        for n in range(1, 7):                                       # the slides as a bake leaves them, then put in order
            photo(etsy / f"Listing {n}.png")
        for key in ("main", "grandma", "child", "size", "shelf"):
            photos.place(H, key, photo(core.data_path("tmp", "p.png")), "p.png")
        (etsy / "video-video.mp4").write_bytes(b"a video")
        photo(etsy / "my own extra.png")                            # the owner's own: no number, after the rest
        photos.tidy_etsy(book)
        self.assertEqual(sorted(p.name for p in etsy.iterdir()), [
            "01 photo-main.png", "02 video-video.mp4", "03 photo-grandma.png", "04 All & Open 1 (8-9).png",
            "06 Listing 1.png", "07 Cover & Open 1 (6-7).png", "08 Listing 3.png", "09 Listing 4.png",
            "10 photo-child.png", "11 Listing 2.png", "12 photo-size.png", "13 Listing 5.png", "14 Listing 6.png",
            "15 photo-shelf.png", "my own extra.png"])
        self.assertEqual(photos.tidy_etsy(book), [])                # already in order: nothing moves
        self.assertEqual(photos.scenes_to_etsy(book), [])           # a numbered copy is the same one
        self.assertEqual(books.mockups_state(book)["slides"], 6)
        self.assertEqual(store._baked_file(book, "Listing 3.png").name, "08 Listing 3.png")
        # the product demonstration goes last and leaves Cover & Open 1 where it is
        photos.place(H, "product", photo(core.data_path("tmp", "o.png")), "o.png")
        self.assertTrue((etsy / "05 photo-product.png").is_file())
        self.assertTrue((etsy / "07 Cover & Open 1 (6-7).png").is_file())


class TheMockupsKeepTheCanvaCover(Base):
    def test_a_run_for_a_workshop_book_keeps_the_demo_books_cover(self):
        from studio import mockups
        cover = photo(core.data_path("tmp", "cover.png"), size=(1074, 570))
        mockups._keep_canva_cover(S, {"cover": str(cover)})
        self.assertTrue((self.dir / S / "mockups" / "canva-cover.png").is_file())
        mockups._keep_canva_cover(S, {"cover": None})   # no cover in the ZIP: nothing happens

    def test_a_hardcover_with_its_wrap_is_cut_to_the_finished_cover(self):
        # 27.10.2026, the owner: with the wrap the generator draws a wrong book — only what is inside the contour
        gelato = Image.new("RGB", (5409, 2906), (255, 0, 0))              # the wrap red
        gelato.paste((0, 0, 255), (236, 236, 5409 - 236, 2906 - 236))      # the finished cover blue
        src = core.data_path("tmp", "gelato.png")
        src.parent.mkdir(parents=True, exist_ok=True)
        gelato.save(src, dpi=(300, 300))
        photos.set_canva_cover(self.dir / S, src, "Cover.png")
        with Image.open(self.dir / S / "mockups" / "canva-cover.png") as im:
            self.assertEqual(im.size, (4937, 2434))                         # 418×206 mm at 300 dpi
            self.assertEqual(im.getpixel((0, 0)), (0, 0, 255))
            self.assertEqual(im.getpixel((im.width - 1, im.height - 1)), (0, 0, 255))
        self.assertEqual(photos.trim_box((1074, 570)), (45, 45, 1029, 525))  # the Printify template: 16.40×8.00″
        flat = photo(core.data_path("tmp", "flat.png"), size=(1000, 500))
        photos.set_canva_cover(self.dir / S, flat, "flat.png")               # a 2:1 cover has no wrap: kept whole
        with Image.open(self.dir / S / "mockups" / "canva-cover.png") as im:
            self.assertEqual(im.size, (1000, 500))

    def test_a_cover_kept_with_its_wrap_is_cut_when_the_photos_open(self):
        folder = self.dir / S / "mockups"
        folder.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (5409, 2906), (255, 0, 0)).save(folder / "canva-cover.png")
        photos.state(self.dir / S)
        with Image.open(folder / "canva-cover.png") as im:
            self.assertEqual(im.size, (4937, 2434))
        kept = list((self.dir / S / ".replaced").glob("*canva-cover.png"))
        self.assertEqual(len(kept), 1)                                       # the whole one kept, never deleted
        self.assertFalse(photos.trim_kept_cover(self.dir / S))               # once only

    def test_a_held_or_unwritable_cover_stays_as_it_is(self):
        from unittest import mock
        folder = self.dir / S / "mockups"
        folder.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (5409, 2906), (255, 0, 0)).save(folder / "canva-cover.jpg")
        real = photos.os.replace

        def held(src, dst):
            if Path(src).name == "canva-cover.jpg":
                raise PermissionError("held")
            return real(src, dst)
        with mock.patch.object(photos.os, "replace", held):
            self.assertFalse(photos.trim_kept_cover(self.dir / S))           # held: at once, left for the next time
        with mock.patch.object(photos, "_save_trimmed", side_effect=OSError("disk full")):
            photos.state(self.dir / S)                                       # a failed write: the page still opens
        self.assertEqual(sorted(e.name for e in folder.iterdir()), ["canva-cover.jpg"])   # whole, nothing left beside
        with Image.open(folder / "canva-cover.jpg") as im:
            self.assertEqual(im.size, (5409, 2906))
        self.assertTrue(photos.trim_kept_cover(self.dir / S))                # a JPEG cut too
        with Image.open(folder / "canva-cover.jpg") as im:
            self.assertEqual((im.format, im.size), ("JPEG", (4937, 2434)))


if __name__ == "__main__":
    unittest.main()
