"""Listing slides: the book cut out of a mockup with its shadow (Dedication: the desk stays, the floor goes), «Без фону»
while Photoshop works, the schemes (Nature, Night, the owner's own, other books' slides as presets), a Workshop book's
slides in its own folder, a stale save refused (the agent's change is never overwritten), «Зробити слайди» with a
pretend browser, the names in the owner's folder, the cleaning, the command line. Made-up pictures only."""
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
from studio import core, mockups
from studio.workshop import books as workshop
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


def pretend_desk(path: Path, size):
    """Dedication's template: the book, and a desk over the right half; the left half is the floor that goes."""
    alpha, effects = pretend_template(path, size)
    keep = np.zeros_like(alpha)
    keep[:, size[0] // 2:] = 1
    return np.maximum(keep, alpha), effects


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
        self._readers = cutout.READER, cutout.DESK_READER
        cutout.READER, cutout.DESK_READER = pretend_template, pretend_desk
        cutout.forget_templates()
        for folder in (store.ROOT, core.WORKSHOP_BOOKS):
            shutil.rmtree(folder, ignore_errors=True)

    def tearDown(self):
        cutout.READER, cutout.DESK_READER = self._readers
        cutout.forget_templates()
        for folder in (store.ROOT, core.WORKSHOP_BOOKS):
            shutil.rmtree(folder, ignore_errors=True)
        self.tmp.cleanup()

    def workshop_book(self, name="25.sleepy-trucks-bedtime") -> str:
        folder = core.WORKSHOP_BOOKS / name
        (folder / "pictures").mkdir(parents=True, exist_ok=True)
        (folder / "agent").mkdir(exist_ok=True)
        return name


class TheCut(Base):
    def test_which_mockups_can_be_cut(self):
        self.assertEqual(cutout.kind_of("2. Open 1 (6-7).png"), "open1")
        self.assertEqual(cutout.kind_of("3. Open 2 (12-13) (2).png"), "open2")
        self.assertEqual(cutout.kind_of("1. Cover 1.png"), "cover1")
        self.assertEqual(cutout.kind_of("4. Dedication.png"), "dedication")
        self.assertIsNone(cutout.kind_of("Cover & Open 1 (20-21).png"))   # a whole scene: no book mask
        self.assertIsNone(cutout.kind_of("All & Open 1 (22-23).png"))
        self.assertIsNone(cutout.kind_of("Listing 1.png"))
        self.assertIn("dedication", cutout.KINDS)                            # the desk stays, the floor goes
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

    def test_dedication_keeps_the_desk_and_the_book_and_loses_the_floor_but_not_its_shadow(self):
        png = self.root / "out" / "4. Dedication.png"
        png.parent.mkdir(parents=True)
        Image.new("RGB", SIZE, (120, 90, 60)).save(png)
        cutout.ensure(png, self.root)
        with Image.open(png.parent / cutout.NO_BG / png.name) as im:
            self.assertEqual(im.size, SIZE)                                   # its own frame: where the mockup lay
            self.assertEqual(im.getpixel((250, 20))[3], 255)                  # the desk
            self.assertEqual(im.getpixel((120, 60))[3], 255)                  # the book
            self.assertEqual(im.getpixel((10, 190))[3], 0)                    # the floor: gone
            self.assertGreater(im.getpixel((115, 155))[3], 50)                # the book's shadow on it: kept

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

    def test_the_first_scheme_is_nature_and_every_book_starts_as_the_default_scheme(self):
        self.assertEqual([(x["key"], x["name"], x["default"]) for x in store.list_schemes()], [("nature", "Nature", True)])
        first, _ = store.load(store.TEMPLATE, "slide1")
        self.assertEqual(first, store.factory("slide1"))                     # no template before: the first design
        _, v = store.load(store.TEMPLATE, "slide1")
        store.save(store.TEMPLATE, "slide1", self.scene(), v)                # «template» — the default scheme itself
        rec = store.new_set("Goose", str(self.root))
        mine, _ = store.load(rec["id"], "slide1")
        self.assertEqual(mine["items"][0]["text"], "Hi")
        self.assertEqual(rec["scheme"], "nature")

    def test_an_old_template_becomes_nature(self):
        store.DESIGN.mkdir(parents=True)
        for slide in store.SLIDES:
            (store.DESIGN / f"{slide}.json").write_text(json.dumps(self.scene(text=f"old {slide}")), encoding="utf-8")
        self.assertEqual(store.template("slide3")["items"][0]["text"], "old slide3")

    def test_a_stale_save_is_refused_with_the_scene_as_it_is_now(self):
        _, v0 = store.load(store.TEMPLATE, "slide2")
        v1 = store.save(store.TEMPLATE, "slide2", self.scene(), v0)
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

    def test_a_scheme_is_the_whole_six_saved_put_on_and_made_the_default(self):
        rec = store.new_set("Goose", str(self.root))
        for slide in store.SLIDES:
            store.save(rec["id"], slide, self.scene(text=f"night {slide}", color="#555876"), None)
        key = store.save_scheme(rec["id"], "Night")
        self.assertEqual(key, "night")
        self.assertEqual(json.loads((store.SCHEMES / "night" / "slide4.json").read_text(encoding="utf-8"))["items"][0]["text"],
                         "night slide4")
        self.assertEqual(store.save_scheme(rec["id"], "night"), "night")     # the same name: that scheme replaced
        other = store.new_set("Fox", str(self.root))
        self.assertNotEqual(store.load(other["id"], "slide4")[0]["items"][0].get("text"), "night slide4")
        store.apply_preset(other["id"], "night")                             # all six at once
        self.assertEqual(store.load(other["id"], "slide4")[0]["items"][0]["text"], "night slide4")
        self.assertEqual(store.read_set(other["id"])["scheme"], "night")
        store.save(other["id"], "slide4", self.scene(text="touched"), None)
        scene, _ = store.reset(other["id"], "slide4")                        # «Скинути» — back to its scheme
        self.assertEqual(scene["items"][0]["text"], "night slide4")
        store.set_default("night")
        self.assertEqual(store.default_scheme(), "night")
        self.assertEqual(store.new_set("Owl", str(self.root))["scheme"], "night")
        self.assertEqual(sum(x["default"] for x in store.list_schemes()), 1)
        with self.assertRaises(ApiError):
            store.save_scheme(rec["id"], "   ")

    def test_a_scheme_can_be_edited_in_place_by_its_key(self):
        """2026-09-30: the standalone editor picks which scheme it edits (Nature, Night…), not only the default one."""
        rec = store.new_set("Goose", str(self.root))
        for slide in store.SLIDES:
            store.save(rec["id"], slide, self.scene(text=f"night {slide}"), None)
        store.save_scheme(rec["id"], "Night")
        where = "scheme:night"
        self.assertEqual(store.valid_where(where), where)
        self.assertTrue(store.is_plain(where) and store.is_plain("template") and not store.is_plain(rec["id"]))
        self.assertEqual(store.load(where, "slide2")[0]["items"][0]["text"], "night slide2")
        version = store.load(where, "slide2")[1]
        store.save(where, "slide2", self.scene(text="night, touched"), version)
        self.assertEqual(json.loads((store.SCHEMES / "night" / "slide2.json").read_text(encoding="utf-8"))["items"][0]["text"],
                         "night, touched")
        self.assertNotEqual(store.default_scheme(), "night")                 # editing one does not make it the default
        self.assertNotEqual(store.sig(where), store.sig("template"))
        for bad in ("scheme:", "scheme:../x", "scheme:nope", "scheme:NIGHT"):
            with self.assertRaises(ApiError):
                store.valid_where(bad)

    def test_the_signature_changes_with_any_scene(self):
        rec = store.new_set("Goose", str(self.root))
        before = store.sig(rec["id"])
        time.sleep(0.02)
        store.save(rec["id"], "slide5", self.scene(), None)
        self.assertNotEqual(store.sig(rec["id"]), before)

    def test_where_is_checked(self):
        for bad in ("../x", "20260101-000000-zzzzzz", "nope", "99.no-such-book"):
            with self.assertRaises(ApiError):
                store.valid_where(bad)
        self.assertEqual(store.valid_where("template"), "template")

    def test_the_first_design_uses_slots_and_the_books_numbers(self):
        for slide in store.SLIDES:
            scene = store.factory(slide)
            for it in scene["items"]:
                self.assertNotIn("src", it)                                  # no file names: slots
                if it["type"] == "book":
                    self.assertIn(it["slot"], store.BOOK_SLOTS)
                if it["type"] == "image":
                    self.assertIn(it["slot"], store.PICTURE_SLOTS + store.HERO_SLOTS)
        texts = json.dumps([store.factory(s) for s in store.SLIDES], ensure_ascii=False)
        self.assertIn("{pages}", texts)
        self.assertIn("{poems}", texts)
        self.assertIn("{looks}", texts)
        frames = [it["slot"] for it in store.factory(store.LOOKS_SLIDE)["items"] if it["type"] == "image"]
        self.assertEqual(frames, store.HERO_SLOTS)                           # slide 7: a frame for every look


class WorkshopBooks(Base):
    """A book's slides belong to its Workshop book (the owner, 29.09.2026) — in its folder, named by it."""

    def test_the_slides_live_in_the_books_folder_and_keep_the_owners_touches(self):
        book = self.workshop_book()
        rec = store.new_set("x", str(self.root), book=book)
        self.assertTrue((core.WORKSHOP_BOOKS / book / "mockups" / "slides" / "scenes" / "slide1.json").is_file())
        self.assertEqual(store.read_set(book)["name"], "№25 Sleepy trucks bedtime")
        self.assertEqual(store.valid_where(book), book)
        store.save(book, "slide1", {"items": [{"type": "text", "x": 1, "y": 1, "text": "mine"}]}, None)
        store.new_set("x", str(self.root), book=book)                        # the mockups made again: the touches stay
        self.assertEqual(store.load(book, "slide1")[0]["items"][0]["text"], "mine")
        store.new_set("x", str(self.root), book=book, fresh=True)            # «Зробити заново»: from the scheme
        self.assertNotEqual(store.load(book, "slide1")[0]["items"][0].get("text"), "mine")
        self.assertEqual(rec["id"], book)
        self.assertIn(book, [r["id"] for r in store.list_sets()])

    def test_a_done_books_slides_are_a_preset_for_another_book_and_its_cache_goes(self):
        a, b = self.workshop_book("24.spooky-stories"), self.workshop_book("25.sleepy-trucks-bedtime")
        rec = store.new_set("x", str(self.root), book=a)
        (store.set_dir(a) / "books").mkdir()
        (store.set_dir(a) / "books" / "open1-1.png").write_bytes(b"png")
        store.save(a, "slide2", {"items": [{"type": "text", "x": 1, "y": 1, "text": "spooky"}]}, None)
        store.book_done(a)
        self.assertFalse((store.set_dir(a) / "books").exists())               # the cache went
        self.assertTrue((store.set_dir(a) / "scenes" / "slide2.json").is_file())   # the settings stay
        store.new_set("x", str(self.root), book=b)
        keys = [x["key"] for x in store.presets(exclude=b)]
        self.assertIn(f"book:{a}", keys)
        self.assertNotIn(f"book:{b}", keys)
        store.apply_preset(b, f"book:{a}")
        self.assertEqual(store.load(b, "slide2")[0]["items"][0]["text"], "spooky")
        self.assertEqual(rec["id"], a)

    def test_the_mockups_step_ticks_itself_and_counts_whats_there(self):
        book = self.workshop_book()
        mockups._ticked({"saved": ["2. Open 1 (2-3).png"]}, book)
        self.assertTrue(workshop.state(core.WORKSHOP_BOOKS / book)["marks"]["mockups"])
        folder = store.mockups_dir(book)
        for name in ("2. Open 1 (2-3).png", "Listing 1.png", "Listing 2.png"):
            (folder / name).write_bytes(b"png")
        (folder / cutout.NO_BG).mkdir()
        (folder / cutout.NO_BG / "2. Open 1 (2-3).png").write_bytes(b"png")
        self.assertEqual(workshop.mockups_state(core.WORKSHOP_BOOKS / book),
                         {"mockups": 1, "noBg": 1, "slides": 2, "editable": False})
        with self.assertRaises(ApiError):
            store.mockups_dir("99.no-such-book")

    def test_the_quite_temporary_goes(self):
        (cutout.CUTS / "abc").mkdir(parents=True)
        core.data_path("tmp", "slides-browser", "0").mkdir(parents=True)
        store.clean_temporary()
        self.assertFalse(cutout.CUTS.exists())
        self.assertFalse(core.data_path("tmp", "slides-browser").exists())


class MakingThem(Base):
    def folder(self) -> Path:
        out = self.root / "Goose mockups"
        for i, n in enumerate((10, 2, 6, 14)):                              # the picks' order: 10, 2, 6, 14
            mockup(out / f"2. Open 1 ({n}-{n + 1}).png", (40 * i, 90, 90))
        mockup(out / "3. Open 2 (8-9).png")
        mockup(out / "1. Cover 1.png")
        Image.new("RGB", SIZE, (90, 70, 50)).save(out / "4. Dedication.png")
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
        self.assertTrue(rec["pictures"]["dedication"].get("cut"))            # the floor see-through
        self.assertTrue((out / cutout.NO_BG / "4. Dedication.png").is_file())
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

    def test_for_a_workshop_book_the_slides_go_into_its_folder_with_its_own_page_30(self):
        book = self.workshop_book()
        Image.new("RGB", (400, 400), "white").save(core.WORKSHOP_BOOKS / book / "pictures" / "30.png")
        out = store.mockups_dir(book)
        mockup(out / "2. Open 1 (2-3).png")
        with mock.patch.object(bake, "run_browser", pretend_browser([])), mock.patch.object(bake, "browser", lambda: "x"):
            res = work.make(quiet_job(), out, "x", None, None, {}, self.root, "http://127.0.0.1:1", "tok", book=book)
        self.assertEqual(res["set"], book)
        etsy = core.WORKSHOP_BOOKS / book / "etsy"   # a Workshop book's slides: in its etsy/ folder (30.09.2026)
        numbered = ["06 Listing 1.png", "11 Listing 2.png", "08 Listing 3.png", "09 Listing 4.png", "13 Listing 5.png",
                    "14 Listing 6.png"]                     # each with its number in the listing's order
        self.assertEqual(sorted(p.name for p in etsy.glob("*.png")), sorted(numbered))
        self.assertFalse(list(out.glob("Listing*.png")))
        self.assertEqual([p["name"] for p in res["pictures"]], numbered)
        with mock.patch.object(bake, "run_browser", pretend_browser([])), mock.patch.object(bake, "browser", lambda: "x"):
            work.bake_set(quiet_job(), store.read_set(book), ["slide2"], "http://127.0.0.1:1", "tok")
        self.assertEqual(sorted(p.name for p in etsy.glob("*.png")), sorted(numbered))   # baked again: the same files
        self.assertEqual(res["folder"], str(etsy))
        self.assertIn("page30", store.read_set(book)["pictures"])
        self.assertTrue(workshop.state(core.WORKSHOP_BOOKS / book)["marks"]["mockups"])   # the step ticked itself

    def test_one_slide_alone_leaves_the_other_slides_as_they_were(self):
        """The owner, 09.10.2026: only Dedication was redone — only slide 3 is made again; the other five, their mockups
        in the set and the Workshop's «Мокапи» step stay as they are."""
        book = self.workshop_book()
        out = store.mockups_dir(book)
        for n in (2, 6, 10, 14):
            mockup(out / f"2. Open 1 ({n}-{n + 1}).png")
        mockup(out / "1. Cover 1.png")
        mockup(out / "4. Dedication.png", (60, 60, 200))
        Image.new("RGB", (400, 400), "white").save(core.WORKSHOP_BOOKS / book / "pictures" / "30.png")
        with mock.patch.object(bake, "run_browser", pretend_browser([])), mock.patch.object(bake, "browser", lambda: "x"):
            work.make(quiet_job(), out, "x", None, None, {}, self.root, "http://127.0.0.1:1", "tok", book=book)
        etsy = core.WORKSHOP_BOOKS / book / "etsy"
        before = {p.name: p.stat().st_mtime_ns for p in etsy.glob("*.png")}
        self.assertEqual(len(before), 6)
        workshop.set_mark(book, "mockups", False)
        old_books = dict(store.read_set(book)["books"])
        time.sleep(0.05)
        calls = []
        mockup(out / "4. Dedication (2).png", (30, 200, 30))                   # the redone one
        with mock.patch.object(bake, "run_browser", pretend_browser(calls)), mock.patch.object(bake, "browser", lambda: "x"):
            res = work.make(quiet_job(), out, "x", ["4. Dedication (2).png"], None, {}, self.root, "http://127.0.0.1:1",
                            "tok", book=book, only=["slide3"])
        self.assertEqual(len(calls), 1)                                         # one slide drawn
        self.assertTrue(any("s=slide3" in a for a in calls[0]))
        rec = store.read_set(book)
        self.assertEqual(rec["books"], old_books)                               # the other slides' mockups are kept
        self.assertEqual(rec["pictures"]["dedication"]["source"], "4. Dedication (2).png")
        self.assertIn("page30", rec["pictures"])
        after = {p.name: p.stat().st_mtime_ns for p in etsy.glob("*.png")}
        self.assertEqual(set(after), set(before))
        self.assertEqual([n for n in after if after[n] != before[n]], ["08 Listing 3.png"])
        self.assertEqual(len(res["pictures"]), 6)                               # the card still shows all six
        self.assertEqual(res["missing"], [])
        self.assertFalse(workshop.state(core.WORKSHOP_BOOKS / book)["marks"].get("mockups"))   # a partial run ticks nothing
        with self.assertRaises(UserError):                                      # nothing for slide 5 in the folder
            work.make(quiet_job(), out, "x", None, None, {}, self.root, "http://127.0.0.1:1", "tok", book=book,
                      only=["slide5"])

    def test_the_books_folder_is_read_as_it_is_whatever_the_page_ran(self):
        """The owner, 11.10.2026: "the mockups are made, but the program says there are none"; "I redo one mockup — the
        whole session goes". The Mockups page reads the Workshop book's folder: its mockups in the templates' order, its
        slides with the ones not made yet («Доробити»)."""
        book = self.workshop_book()
        self.assertEqual(mockups.existing(book), {"folder": str(core.WORKSHOP_BOOKS / book / "mockups"), "files": [],
                                                  "slides": None})
        self.assertFalse((core.WORKSHOP_BOOKS / book / "mockups").exists())   # reading makes no folder
        out = store.mockups_dir(book)
        for name in ("1. Cover 1.png", "2. Open 1 (6-7).png", "2. Open 1 (2-3).png", "4. Dedication.png",
                     "4. Dedication (2).png", "All & Open 1 (16-17).png", "3. Open 2 (8-9).png"):
            mockup(out / name)
        mockup(out / "canva-cover.png")                                         # not a mockup
        found = mockups.existing(book)
        self.assertEqual([f["name"] for f in found["files"]],
                         ["2. Open 1 (2-3).png", "2. Open 1 (6-7).png", "3. Open 2 (8-9).png", "All & Open 1 (16-17).png",
                          "4. Dedication (2).png", "4. Dedication.png", "1. Cover 1.png"])
        self.assertEqual(found["files"][0]["template"], "open1")
        with mock.patch.object(bake, "run_browser", pretend_browser([])), mock.patch.object(bake, "browser", lambda: "x"):
            res = work.make(quiet_job(), out, "x", None, None, {"pages": 30}, self.root, "http://127.0.0.1:1", "tok",
                            book=book, only=["slide3"])
        self.assertEqual(res["todo"], ["slide1", "slide2", "slide4", "slide5", "slide6"])
        slides = mockups.existing(book)["slides"]
        self.assertEqual([p["slide"] for p in slides["pictures"]], ["slide3"])
        self.assertEqual(slides["todo"], res["todo"])
        self.assertEqual(slides["numbers"]["pages"], 30)
        self.assertEqual(slides["folder"], str(core.WORKSHOP_BOOKS / book / "etsy"))
        with mock.patch.object(bake, "run_browser", pretend_browser([])), mock.patch.object(bake, "browser", lambda: "x"):
            rest = work.make(quiet_job(), out, "x", None, None, {}, self.root, "http://127.0.0.1:1", "tok", book=book,
                             only=res["todo"])                                 # «Доробити»
        self.assertEqual(rest["todo"], [])
        self.assertEqual(len(rest["pictures"]), 6)
        for wrong in ("../x.png", "canva-cover.png", "2. Open 1 (9-10).png", ""):
            with self.assertRaises(ApiError):
                mockups._existing_file(book, wrong)
        self.assertEqual(mockups._existing_file(book, "1. Cover 1.png"), out / "1. Cover 1.png")

    def test_slide_7_alone_is_made_from_the_looks_and_an_older_copy_of_a_redone_mockup_is_left_out(self):
        """«Доробити слайд 7» — the looks came after the six were made: no mockup is needed for it. And a mockup redone
        another day lies beside the old one: slides made from the folder take the newest of each spread, once."""
        book = self.workshop_book()
        out = store.mockups_dir(book)
        for n in (2, 6):
            mockup(out / f"2. Open 1 ({n}-{n + 1}).png")
        time.sleep(0.05)
        mockup(out / "2. Open 1 (2-3) (2).png", (30, 200, 30))                  # spread 2 redone
        slots = work.slots_of(work.mockups_in(out))
        self.assertEqual([slots[f"open1:{i}"].name for i in (1, 2)], ["2. Open 1 (2-3) (2).png", "2. Open 1 (6-7).png"])
        self.assertNotIn("open1:3", slots)
        with mock.patch.object(bake, "run_browser", pretend_browser([])), mock.patch.object(bake, "browser", lambda: "x"):
            work.make(quiet_job(), out, "x", None, None, {}, self.root, "http://127.0.0.1:1", "tok", book=book)
        self.looks(book, "B1_brunette", "B2_blond")
        work.sync_heroes(book)
        self.assertEqual(mockups.existing(book)["slides"]["todo"], ["slide7"])
        calls = []
        with mock.patch.object(bake, "run_browser", pretend_browser(calls)), mock.patch.object(bake, "browser", lambda: "x"):
            res = work.make(quiet_job(), out, "x", None, None, {}, self.root, "http://127.0.0.1:1", "tok", book=book,
                            only=["slide7"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(res["todo"], [])

    def test_the_editor_lists_the_workshops_books_with_what_they_have(self):
        from studio.slides import routes
        bare = self.workshop_book("24.spooky-stories")
        made = self.workshop_book()
        mockup(store.mockups_dir(made) / "2. Open 1 (2-3).png")
        mockup(store.mockups_dir(made) / "Cover & Open 1 (4-5).png")             # not on the slides
        books = routes._books(None)["books"]
        self.assertEqual([(b["id"], b["slides"], b["mockups"]) for b in books], [(made, False, 1), (bare, False, 0)])
        self.assertTrue(books[0]["name"].startswith("№25"))

    def looks(self, book: str, *names: str) -> None:
        for i, name in enumerate(names):
            hero = core.WORKSHOP_BOOKS / book / "agent" / "variants" / name / "hero.png"
            hero.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (200, 300), (250, 250, 250 - i)).save(hero)

    def test_a_book_whose_hero_has_looks_gets_slide_7_with_each_look_in_its_frame(self):
        """The owner, 2026-10-02: a slide for the books with appearance variants — each in its own frame, the name
        under it; the pictures keep their white background."""
        book = self.workshop_book()
        self.looks(book, "B10_extra", "B2_blond", "B1_brunette", "B3_east_asian")
        (core.WORKSHOP_BOOKS / book / "agent" / "variants" / "B4_afro").mkdir()   # no hero.png yet: not a look
        out = store.mockups_dir(book)
        mockup(out / "2. Open 1 (2-3).png")
        calls = []
        with mock.patch.object(bake, "run_browser", pretend_browser(calls)), mock.patch.object(bake, "browser", lambda: "x"):
            res = work.make(quiet_job(), out, "x", None, None, {}, self.root, "http://127.0.0.1:1", "tok", book=book)
        self.assertEqual(len(calls), 7)
        self.assertEqual(res["pictures"][-1]["name"], "16 Listing 7.png")      # the listing's place: last for now
        rec = store.read_set(book)
        self.assertEqual([rec["pictures"][s]["label"] for s in store.HERO_SLOTS if s in rec["pictures"]],
                         ["B1", "B2", "B3", "B10"])                            # by their numbers
        self.assertEqual(rec["pictures"]["hero:1"]["aspect"], 1.5)
        self.assertTrue((store.set_dir(book) / "pictures" / "hero-1.png").is_file())
        with Image.open(store.set_dir(book) / "pictures" / "hero-1.png") as im:
            self.assertEqual(im.getpixel((0, 0))[:3], (250, 250, 248))         # B1's own, its white background kept
        self.assertEqual(store.shown(book), store.SLIDES)
        self.assertEqual(res["missing"], [m for m in res["missing"] if not m.startswith("Герой")])

    def test_slide_7_only_with_two_looks_and_it_takes_looks_made_later(self):
        book = self.workshop_book()
        self.looks(book, "G1_base")
        rec = store.new_set("x", str(self.root), book=book)
        self.assertTrue(work.put_heroes(rec, book))
        store.write_set(rec)
        self.assertNotIn(store.LOOKS_SLIDE, store.shown(book))                 # one look: nothing to choose from
        self.assertFalse(work.put_heroes(store.read_set(book), book))          # nothing changed: nothing done
        self.looks(book, "G1_base", "G2_brunette")                             # the Workshop made another one
        work.sync_heroes(book)
        self.assertEqual(store.shown(book)[-1], store.LOOKS_SLIDE)
        self.assertEqual(store.read_set(book)["pictures"]["hero:2"]["label"], "G2")
        self.assertEqual(store.shown(store.TEMPLATE), store.SLIDES)            # a scheme has all seven to edit

    def test_a_scheme_made_before_slide_7_gets_it_in_its_own_colours(self):
        store.ensure_schemes()
        night = store.SCHEMES / "night"
        night.mkdir()
        for slide in store.SLIDES[:6]:
            scene = store.factory(slide)
            if slide == "slide4":
                scene["bg"] = "#555876"
                for e in scene["items"]:
                    if e.get("name") == "Оливкова смуга":
                        e["color"] = "#5c7d88"
            core.write_json(night / f"{slide}.json", scene, backup=False)
        core.write_json(night / "scheme.json", {"name": "Night", "default": False}, backup=False)
        store.list_schemes()
        seven = json.loads((night / "slide7.json").read_text(encoding="utf-8"))
        self.assertEqual(seven["bg"], "#555876")
        self.assertIn("#5c7d88", [e.get("color") for e in seven["items"]])    # slide 4's olive, Night's blue here
        self.assertTrue((store.SCHEMES / "nature" / "slide7.json").is_file())

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
    def test_path_gives_the_default_schemes_file_to_edit(self):
        from tools import slides as cli
        with mock.patch("sys.stdout") as out:
            self.assertEqual(cli.main(["path", "slide6"]), 0)
        printed = "".join(c.args[0] for c in out.write.call_args_list)
        self.assertIn("slide6.json", printed)
        self.assertTrue((store.SCHEMES / "nature" / "slide6.json").is_file())


if __name__ == "__main__":
    unittest.main()
