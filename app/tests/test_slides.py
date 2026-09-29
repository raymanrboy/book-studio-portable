"""Listing slides: the book cut out of a mockup with its shadow, «Без фону» while Photoshop works, the template and a
book's slides (a stale save refused — the agent's change is never overwritten), «Зробити слайди» with a pretend
browser, the names in the owner's folder, the command line. Made-up pictures only."""
import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
from PIL import Image, ImageDraw

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import mockups
from studio.jobs import UserError
from studio.server import ApiError
from studio.slides import bake, cutout, store, work

SIZE = (300, 200)
BOOK = (100, 50, 200, 150)     # where the pretend template's book is


def pretend_template(path: Path, size):
    """A template's book mask (a rectangle) and one Multiply shadow of grey 0.5 under it, a little down-right."""
    alpha = np.zeros((size[1], size[0]), np.float32)
    x0, y0, x1, y1 = BOOK
    alpha[y0:y1, x0:x1] = 1
    shade = np.zeros_like(alpha)
    shade[y0 + 10:y1 + 10, x0 + 10:x1 + 10] = 0.5
    return alpha, [(0.0, shade)]


def mockup(path: Path, colour=(200, 60, 60)) -> Path:
    """A mockup picture: the grey studio background with a coloured book where the template has it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", SIZE, (150, 150, 150))
    ImageDraw.Draw(im).rectangle([BOOK[0], BOOK[1], BOOK[2] - 1, BOOK[3] - 1], fill=colour)
    im.save(path)
    return path


def quiet_job():
    return SimpleNamespace(progress=lambda *a, **k: None, share=lambda *a: None)


def pretend_browser(calls):
    """Plays headless Edge: writes a 2000² picture where --screenshot says."""
    def run(args, timeout):
        calls.append(args)
        shot = next(a for a in args if a.startswith("--screenshot=")).split("=", 1)[1]
        Image.new("RGB", (2000, 2000), (238, 222, 199)).save(shot)
        profile = Path(next(a for a in args if a.startswith("--user-data-dir=")).split("=", 1)[1])
        profile.mkdir(parents=True, exist_ok=True)
    return run


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._reader = cutout.READER
        cutout.READER = pretend_template
        cutout.forget_templates()
        for folder in (store.ROOT,):
            shutil.rmtree(folder, ignore_errors=True)

    def tearDown(self):
        cutout.READER = self._reader
        cutout.forget_templates()
        shutil.rmtree(store.ROOT, ignore_errors=True)
        self.tmp.cleanup()


class TheCut(Base):
    def test_which_mockups_can_be_cut(self):
        self.assertEqual(cutout.kind_of("2. Open 1 (6-7).png"), "open1")
        self.assertEqual(cutout.kind_of("3. Open 2 (12-13) (2).png"), "open2")
        self.assertEqual(cutout.kind_of("1. Cover 1.png"), "cover1")
        self.assertEqual(cutout.kind_of("4. Dedication.png"), "dedication")
        self.assertIsNone(cutout.kind_of("Cover & Open 1 (20-21).png"))   # a whole scene: no book mask
        self.assertIsNone(cutout.kind_of("All & Open 1 (22-23).png"))
        self.assertIsNone(cutout.kind_of("Listing 1.png"))
        self.assertEqual(cutout.spread_of("2. Open 1 (6-7).png"), 6)

    def test_the_book_is_kept_and_the_grey_shadow_turns_into_a_transparent_one(self):
        png = mockup(self.root / "2. Open 1 (2-3).png")
        book, shadow, info = cutout.cut(png, pretend_template(png, SIZE))
        # cropped to the book and its shadow: 100 + 10 wide, 100 + 10 high
        self.assertEqual(book.size, (110, 110))
        self.assertEqual(book.getpixel((50, 50)), (200, 60, 60, 255))       # the book itself, opaque
        self.assertEqual(book.getpixel((105, 105))[3], 0)                   # outside the book: see-through
        r, g, b, a = shadow.getpixel((105, 105))                             # the shadow: black, half see-through
        self.assertEqual((r, g, b), (0, 0, 0))
        self.assertAlmostEqual(a / 255, (0.5 - cutout.HAZE) / (1 - cutout.HAZE), delta=0.01)
        self.assertEqual(shadow.getpixel((2, 2))[3], 0)                      # no whole-canvas haze
        self.assertAlmostEqual(info["aspect"], 1.0, delta=0.02)
        self.assertAlmostEqual(info["cx"], 0.45, delta=0.02)                 # the book sits left of the pair's middle

    def test_a_mockup_of_another_size_is_refused(self):
        png = self.root / "2. Open 1 (2-3).png"
        Image.new("RGB", (100, 100)).save(png)
        with self.assertRaises(UserError):
            cutout.cut(png, pretend_template(png, SIZE))

    def test_without_background_lands_beside_it_and_is_never_overwritten(self):
        png = mockup(self.root / "out" / "2. Open 1 (2-3).png")
        folder = cutout.ensure(png, self.root)
        target = png.parent / cutout.NO_BG / png.name
        self.assertTrue((folder / "book.png").is_file() and (folder / "shadow.png").is_file())
        with Image.open(target) as im:
            self.assertEqual(im.mode, "RGBA")
            self.assertEqual(im.getpixel((50, 50))[3], 255)
        target.write_bytes(b"the owner's own file")
        cutout.ensure(png, self.root)                                        # cut again: the cache, and no overwrite
        self.assertEqual(target.read_bytes(), b"the owner's own file")

    def test_the_background_cutter_takes_the_pictures_as_photoshop_saves_them(self):
        out = self.root / "out"
        a, b = mockup(out / "2. Open 1 (2-3).png"), mockup(out / "1. Cover 1.png")
        skipped = mockup(out / "Cover & Open 1 (4-5).png")
        c = cutout.Cutter()
        self.assertTrue(c.add(a, self.root))
        self.assertTrue(c.add(b, self.root))
        self.assertFalse(c.add(skipped, self.root))
        for _ in range(100):
            if not c.busy(out):
                break
            time.sleep(0.05)
        self.assertEqual(c.status(out), {a.name: "done", b.name: "done"})
        self.assertTrue((out / cutout.NO_BG / a.name).is_file())
        self.assertFalse((out / cutout.NO_BG / skipped.name).exists())

    def test_the_mockups_hand_every_saved_picture_to_the_cutter(self):
        saved = str(self.root / "2. Open 1 (2-3).png")
        work_ = {"templates": [{"source": str(self.root / "2. Open 1.psd"), "shots": [{"save": saved}]}]}
        with mock.patch.object(mockups.slide_cutout.cutter, "add") as add:
            handed = set()
            mockups._cut_without_background(work_, {"saved": [saved]}, handed)
            mockups._cut_without_background(work_, {"saved": [saved]}, handed)   # the next status: not twice
        add.assert_called_once_with(Path(saved), self.root)


class Scenes(Base):
    def scene(self, **extra):
        return {"id": "slide1", "bg": "#eedec7", "items": [{"type": "text", "x": 10, "y": 20, "text": "Hi", **extra}]}

    def test_the_template_starts_as_first_drawn_and_every_book_starts_as_the_template(self):
        first, version = store.load(store.TEMPLATE, "slide1")
        self.assertEqual(version, "")                                         # not touched yet
        self.assertEqual(first, store.factory("slide1"))
        store.save(store.TEMPLATE, "slide1", self.scene(), "")
        rec = store.new_set("Goose", str(self.root))
        mine, _ = store.load(rec["id"], "slide1")
        self.assertEqual(mine["items"][0]["text"], "Hi")

    def test_a_stale_save_is_refused_with_the_scene_as_it_is_now(self):
        v1 = store.save(store.TEMPLATE, "slide2", self.scene(), "")
        v2 = store.save(store.TEMPLATE, "slide2", self.scene(text="the agent's"), v1)
        with self.assertRaises(ApiError) as caught:
            store.save(store.TEMPLATE, "slide2", self.scene(text="the editor's"), v1)   # made on v1: stale
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(caught.exception.extra["version"], v2)
        self.assertEqual(caught.exception.extra["scene"]["items"][0]["text"], "the agent's")

    def test_a_scene_with_an_unknown_element_or_no_items_is_refused(self):
        for bad in ({"items": [{"type": "video", "x": 1, "y": 1}]}, {"bg": "#fff"}, {"items": [{"type": "text", "x": "a"}]}):
            with self.assertRaises(ApiError):
                store.save(store.TEMPLATE, "slide3", bad, None)

    def test_reset_and_to_template(self):
        rec = store.new_set("Goose", str(self.root))
        store.save(rec["id"], "slide4", self.scene(text="for this book"), None)
        store.to_template(rec["id"], "slide4")
        self.assertEqual(store.template("slide4")["items"][0]["text"], "for this book")
        scene, _ = store.reset(store.TEMPLATE, "slide4")                     # the template back to the first design
        self.assertEqual(scene, store.factory("slide4"))

    def test_the_signature_changes_with_any_scene(self):
        rec = store.new_set("Goose", str(self.root))
        before = store.sig(rec["id"])
        time.sleep(0.02)
        store.save(rec["id"], "slide5", self.scene(), None)
        self.assertNotEqual(store.sig(rec["id"]), before)

    def test_where_is_checked(self):
        for bad in ("../x", "20260101-000000-zzzzzz", ""):
            with self.assertRaises(ApiError):
                store.valid_where(bad if bad else "nope")
        self.assertEqual(store.valid_where("template"), "template")

    def test_the_first_design_uses_slots_and_the_books_numbers(self):
        for slide in store.SLIDES:
            scene = store.factory(slide)
            for it in scene["items"]:
                self.assertNotIn("src", it)                                  # no file names: slots
                if it["type"] == "book":
                    self.assertIn(it["slot"], store.BOOK_SLOTS)
                if it["type"] == "image":
                    self.assertIn(it["slot"], store.PICTURE_SLOTS)
        texts = json.dumps([store.factory(s) for s in store.SLIDES], ensure_ascii=False)
        self.assertIn("{pages}", texts)
        self.assertIn("{poems}", texts)


class MakingThem(Base):
    def folder(self) -> Path:
        out = self.root / "Goose mockups"
        for i, n in enumerate((10, 2, 6, 14)):                              # the picks' order: 10, 2, 6, 14
            mockup(out / f"2. Open 1 ({n}-{n + 1}).png", (40 * i, 90, 90))
        mockup(out / "3. Open 2 (8-9).png")
        mockup(out / "1. Cover 1.png")
        Image.new("RGB", (400, 300), (90, 70, 50)).save(out / "4. Dedication.png")
        mockup(out / "Cover & Open 1 (4-5).png")
        return out

    def test_the_slots_follow_the_owners_picks(self):
        out = self.folder()
        order = [f"2. Open 1 ({n}-{n + 1}).png" for n in (10, 2, 6, 14)]
        slots = work.slots_of(work.mockups_in(out, order))
        self.assertEqual([slots[f"open1:{i}"].name for i in range(1, 5)], order)
        self.assertEqual(slots["open2:1"].name, "3. Open 2 (8-9).png")
        self.assertNotIn("open2:2", slots)
        self.assertEqual(slots["cover"].name, "1. Cover 1.png")
        by_spread = work.slots_of(work.mockups_in(out))                      # no order: by spread
        self.assertEqual(by_spread["open1:1"].name, "2. Open 1 (2-3).png")

    def test_make_cuts_makes_the_set_and_bakes_six_into_the_folder(self):
        out = self.folder()
        page30 = self.root / "30.png"
        Image.new("RGB", (500, 500), "white").save(page30)
        calls = []
        with mock.patch.object(bake, "run_browser", pretend_browser(calls)), \
                mock.patch.object(bake, "browser", lambda: "msedge.exe"):
            res = work.make(quiet_job(), out, "Goose", None, page30, {"pages": 30}, self.root, "http://127.0.0.1:1", "tok")
        self.assertEqual([p["name"] for p in res["pictures"]], [f"Listing {n}.png" for n in range(1, 7)])
        self.assertTrue(all((out / f"Listing {n}.png").is_file() for n in range(1, 7)))
        self.assertEqual(res["missing"], ["Open 2 · 2"])                     # one Open 2 only
        rec = store.read_set(res["set"])
        self.assertEqual(set(rec["books"]), {"open1:1", "open1:2", "open1:3", "open1:4", "open2:1", "cover"})
        self.assertEqual(set(rec["pictures"]), {"dedication", "page30"})
        self.assertEqual(rec["numbers"], {"pages": 30, "poems": 11})
        self.assertTrue((out / cutout.NO_BG / "1. Cover 1.png").is_file())
        self.assertEqual(len(calls), 6)
        args = calls[0]
        self.assertIn("--headless=new", args)
        self.assertTrue(any(a.startswith("--force-device-scale-factor=2") for a in args))
        self.assertTrue(args[-1].startswith("http://127.0.0.1:1/slides/render.html?"))
        profiles = Path(next(a for a in args if a.startswith("--user-data-dir=")).split("=", 1)[1]).parent
        self.assertFalse(profiles.exists())                                  # the browser's profile went
        # baked again after the editor: the same files, nothing new beside them
        with mock.patch.object(bake, "run_browser", pretend_browser([])), mock.patch.object(bake, "browser", lambda: "x"):
            again = work.bake_set(quiet_job(), rec, ["slide2"], "http://127.0.0.1:1", "tok")
        self.assertEqual(len(list(out.glob("Listing*.png"))), 6)
        self.assertEqual(len(again), 6)

    def test_names_never_go_over_the_owners_files(self):
        out = self.root / "out"
        out.mkdir()
        (out / "Listing 1.png").write_bytes(b"another book's")
        rec = {"folder": str(out), "baked": {}}
        names = bake.outputs(rec, ["slide1", "slide2"])
        self.assertEqual(names["slide1"].name, "Listing 1 (2).png")
        self.assertEqual(names["slide2"].name, "Listing 2.png")
        rec["baked"] = {"slide1": str(out / "Listing 1 (2).png")}
        self.assertEqual(bake.outputs(rec, ["slide1"])["slide1"].name, "Listing 1 (2).png")   # its own: replaced

    def test_nothing_to_show_is_said(self):
        empty = self.root / "empty"
        empty.mkdir()
        with self.assertRaises(UserError):
            work.make(quiet_job(), empty, "x", None, None, {}, self.root, "", "")

    def test_a_browser_that_draws_nothing_is_said(self):
        with mock.patch.object(bake, "run_browser", lambda args, timeout: None), mock.patch.object(bake, "browser", lambda: "x"):
            with self.assertRaises(UserError):
                bake.render("template", "slide1", self.root / "a.png", "http://127.0.0.1:1", "t", self.root / "p")


class CommandLine(Base):
    def test_path_writes_out_the_first_design_to_edit(self):
        from tools import slides as cli
        with mock.patch("sys.stdout") as out:
            self.assertEqual(cli.main(["path", "slide6"]), 0)
        printed = "".join(c.args[0] for c in out.write.call_args_list)
        self.assertIn("slide6.json", printed)
        self.assertTrue((store.DESIGN / "slide6.json").is_file())


if __name__ == "__main__":
    unittest.main()
