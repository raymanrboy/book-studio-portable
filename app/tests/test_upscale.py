"""Upscaling in the Workshop (the owner, 2026-09-27): a picture that lands in its row is upscaled ×2 in the background
— its original, then mirrored and cut as before, the big pages replacing the small ones; the cover and pages 1 and 30
too, and each hero variant's spreads and cover; the hero pictures not; a book can be left without it. In the sandbox the engine is a plain resize —
the owner's Upscayl is never started."""
import os
import tempfile
import time
import unittest
import unittest.mock
from pathlib import Path

from PIL import Image

from tests import __init__  # noqa: F401  (sets a temporary data folder and the sandbox)
from tests.test_workshop import Base, H, request, spread_png
from studio import core
from studio.jobs import jobs
from studio.server import ApiError
from studio.workshop import books, pictures, routes, upscale


class Upscaling(Base):
    def size(self, name):
        with Image.open(self.dir / H / "pictures" / name) as im:
            return im.size

    def marks(self, key):
        return (books.state(self.dir / H).get("rows") or {}).get(key) or {}

    def place(self, key, size=(1024, 512), name="a.png", **kw):
        return pictures.place(H, key, spread_png(self.tmp / name, size), name, **kw)

    def run_queue(self):
        while upscale._upscaler.step():
            pass

    def test_a_placed_spread_is_upscaled_twice_and_cut_as_before(self):
        self.place("spread3")  # one of the flipper's spreads: pages 4–5, mirrored
        self.assertEqual(self.size("4.png"), (512, 512))
        self.assertEqual(upscale.status(H)["queue"], ["spread3"])
        self.assertTrue(upscale._upscaler.step())
        self.assertEqual((self.size("4.png"), self.size("5.png")), ((1024, 1024), (1024, 1024)))
        self.assertEqual(self.pixel(H, "4.png"), (30, 60, 220))  # still mirrored: the blue on the left
        up = self.marks("spread3")["upscaled"]
        self.assertEqual((up["scale"], up["model"], up["size"]), (2, "upscayl-standard-4x", [2048, 1024]))
        with Image.open(self.dir / H / "originals" / "spread-04-05.png") as im:
            self.assertEqual(im.size, (1024, 512))  # the original stays as it came
        self.assertFalse(upscale._upscaler.step())
        self.assertNotIn("spread3", upscale.status(H)["todo"])

    def test_upscayl_gets_a_copy_and_the_books_picture_stays_free(self):
        """28.09.2026: while Upscayl read the book's own original, replacing it failed with «WinError 32»."""
        self.place("spread3")
        given = []
        real = upscale._run_engine

        def watch(source, target, progress):
            given.append(source)
            return real(source, target, progress)
        with unittest.mock.patch.object(upscale, "_run_engine", watch):
            upscale._upscaler.step()
        self.assertEqual(len(given), 1)
        self.assertNotEqual(given[0].parent, self.dir / H / "originals")  # a copy in tmp, not the book's file
        self.assertFalse(given[0].exists())                                # and cleared after
        self.assertTrue(self.marks("spread3")["upscaled"])

    def test_a_cold_look_at_the_sizes_doesnt_unpack_pngs(self):
        """Asking a PNG for its EXIF unpacked the whole picture: book 41 (370 pictures) took 31 s to open."""
        self.place("spread3")
        upscale._sizes.clear()
        with unittest.mock.patch.object(Image.Image, "load", side_effect=AssertionError("unpacked")):
            self.assertIn("spread3", upscale.sides(self.dir / H))

    def test_a_big_picture_is_not_offered(self):
        """The owner, 27.09.2026: "it doesn't recognise big pictures" — a page of 2400 px and more is print-ready."""
        self.place("spread2", (4900, 2450), "big.png")
        self.place("page1", (2400, 2400), "p.png")
        self.place("spread3")
        st = upscale.status(H)
        self.assertEqual(st["queue"], ["spread3"])
        self.assertEqual(st["todo"], ["spread3"])
        self.assertEqual(st["sides"]["spread2"], {"side": 2450, "upscaled": False, "big": True, "recut": False, "original": 2450})
        self.assertTrue(st["sides"]["page1"]["big"])
        upscale._upscaler.step()
        self.assertEqual(upscale.status(H)["sides"]["spread3"],
                         {"side": 1024, "upscaled": True, "big": False, "recut": False, "original": 512})
        with self.assertRaises(ApiError):
            upscale.start(H)  # the big ones aren't «the rest»

    def test_an_original_upscaled_by_hand_only_cuts_its_pages_again(self):
        """Book 41's Boy_2: the originals were upscaled in Upscayl and put back, the pages stayed small — they are
        measured by the pages, and cut again from the big original, without Upscayl."""
        self.place("spread2")
        upscale._upscaler.queue.clear()
        spread_png(self.dir / H / "originals" / "spread-02-03.png", (4800, 2400))  # replaced by hand
        st = upscale.status(H)["sides"]["spread2"]
        self.assertEqual((st["side"], st["big"], st["recut"], st["original"]), (512, False, True, 2400))
        self.assertIn("spread2", upscale.status(H)["todo"])

        def never(*a):
            raise AssertionError("Upscayl isn't needed")
        with unittest.mock.patch.object(upscale, "_run_engine", never):
            upscale.start(H, ["spread2"])
            upscale._upscaler.step()
        self.assertEqual(self.size("2.png"), (2400, 2400))
        self.assertEqual(upscale.status(H)["sides"]["spread2"]["big"], True)
        self.assertNotIn("spread2", upscale.status(H)["todo"])

    def test_a_flip_by_hand_is_kept(self):
        self.place("spread2")
        pictures.flip(H, "spread2")
        upscale._upscaler.step()
        self.assertEqual(self.pixel(H, "2.png"), (30, 60, 220))

    def test_pages_1_and_30_and_the_cover(self):
        self.place("page1", (600, 500), "p.png")
        self.place("cover", (1000, 500), "c.png")
        self.place("cover-wrap", (1100, 580), "w.png")
        self.assertEqual(upscale.status(H)["queue"], ["page1", "cover-wrap"])  # the cover's picture itself isn't
        self.run_queue()
        self.assertEqual(self.size("1.png"), (1000, 1000))
        self.assertEqual(self.size("Cover.png"), (5370, 2850))  # still exactly the printer's template
        self.assertEqual(self.marks("cover-wrap")["upscaled"]["size"], [2200, 1160])

    def test_a_cover_without_margins_is_upscaled_as_it_is(self):
        self.place("cover", (1000, 500), "c.png")
        pictures.skip_margins(H)
        self.assertEqual(upscale.status(H)["queue"], ["cover-wrap"])
        upscale._upscaler.step()
        self.assertEqual(self.size("Cover.png"), (2000, 1000))

    def test_the_variants_are_upscaled_the_hero_pictures_not(self):
        """The owner, 27.09.2026: "there's no upscale in the variants" — their spreads and cover are, like the base's."""
        self.place("hero", (400, 400), "h.png")
        self.place("hero", (400, 400), "vh.png", variant="G2_brunette")
        self.place("spread3", name="v.png", variant="G2_brunette")
        self.place("cover-wrap", (1100, 580), "vc.png", variant="G2_brunette")
        self.assertEqual(upscale.status(H)["queue"], ["G2_brunette/spread3", "G2_brunette/cover-wrap"])
        self.run_queue()
        folder = self.dir / H / "pictures" / "variants" / "G2_brunette"
        with Image.open(folder / "4.png") as im:
            self.assertEqual(im.size, (1024, 1024))
        self.assertEqual(self.pixel(H, "4.png", variant="G2_brunette"), (30, 60, 220))  # mirrored as before
        with Image.open(folder / "Cover.png") as im:
            self.assertEqual(im.size, (5370, 2850))
        self.assertEqual(self.marks("G2_brunette/spread3")["upscaled"]["size"], [2048, 1024])
        self.assertEqual(self.marks("G2_brunette/cover-wrap")["upscaled"]["size"], [2200, 1160])
        self.assertIsNone(self.marks("spread3").get("upscaled"))  # the base row is its own
        with Image.open(self.dir / H / "agent" / "canonical.png") as im:
            self.assertEqual(im.size, (400, 400))

    def test_upscale_the_rest_takes_the_variants_too(self):
        upscale.set_on(H, False)
        self.place("spread2")
        self.place("spread2", name="v.png", variant="G2_brunette")
        upscale.set_on(H, True)
        self.assertEqual(upscale.start(H)["queue"], ["spread2", "G2_brunette/spread2"])
        self.run_queue()
        self.assertEqual(upscale.status(H)["todo"], [])
        with self.assertRaises(ApiError):
            upscale.start(H, ["../spread2"])  # only a real variant's row

    def test_a_book_turned_off_is_left_as_it_is_and_can_be_done_later(self):
        upscale.set_on(H, False)
        self.assertIs(books.state(self.dir / H)["upscale"], False)
        self.place("spread2")
        st = upscale.status(H)
        self.assertEqual((st["on"], st["queue"], st["todo"]), (False, [], ["spread2"]))
        upscale.set_on(H, True)
        self.assertNotIn("upscale", books.state(self.dir / H))  # on is the default: nothing written
        self.assertEqual(upscale.start(H)["queue"], ["spread2"])  # «Апскейлити решту»
        upscale._upscaler.step()
        self.assertEqual(self.size("2.png"), (1024, 1024))
        with self.assertRaises(ApiError):
            upscale.start(H)  # nothing left

    def test_turning_off_empties_the_books_queue(self):
        self.place("spread2")
        upscale.set_on(H, False)
        self.assertFalse(upscale._upscaler.step())
        self.assertEqual(self.size("2.png"), (512, 512))

    def test_a_picture_replaced_meanwhile_wins(self):
        self.place("spread2")
        real = upscale._run_engine

        def and_meanwhile(source, target, progress):
            real(source, target, progress)
            self.place("spread2", (800, 400), "b.png")
        with unittest.mock.patch.object(upscale, "_run_engine", and_meanwhile):
            self.assertIsNone(upscale.upscale_row(H, "spread2"))
        self.assertEqual(self.size("2.png"), (400, 400))
        self.assertIsNone(self.marks("spread2").get("upscaled"))

    def test_a_new_picture_is_not_upscaled_whatever_the_one_before_was(self):
        self.place("spread2")
        upscale._upscaler.step()
        self.place("spread2", (800, 400), "b.png")
        self.assertIsNone(self.marks("spread2")["upscaled"])
        self.assertIn("spread2", upscale.status(H)["todo"])

    def test_a_failure_keeps_the_small_pages_and_says_why(self):
        self.place("spread2")

        def broken(source, target, progress):
            raise ApiError("Upscayl не впорався (код 1)")
        with unittest.mock.patch.object(upscale, "_run_engine", broken):
            upscale._upscaler.step()
        self.assertEqual(upscale.status(H)["errors"], {"spread2": "Upscayl не впорався (код 1)"})
        self.assertEqual(self.size("2.png"), (512, 512))
        upscale.start(H, ["spread2"])  # «Апскейлити ще раз»
        self.assertEqual(upscale.status(H)["errors"], {})
        upscale._upscaler.step()
        self.assertEqual(self.size("2.png"), (1024, 1024))

    def test_a_removed_row_is_passed_by(self):
        self.place("spread2")
        pictures.remove(H, "spread2")
        upscale._upscaler.step()
        self.assertEqual(upscale.status(H)["errors"], {})
        self.assertFalse((self.dir / H / "pictures" / "2.png").exists())

    def test_the_book_page_is_told_and_redraws_while_it_goes(self):
        self.assertTrue(routes._get(request(H))["book"]["upscale"]["on"])
        self.place("spread2")
        before = routes._live(H)["sig"]
        with upscale._upscaler.lock:
            upscale._upscaler.current = {"book": H, "key": "spread2", "pct": 0}
        upscale._upscaler._progress(40)
        self.assertEqual(upscale.status(H)["current"], {"key": "spread2", "pct": 40})
        self.assertNotEqual(routes._live(H)["sig"], before)
        self.assertEqual(routes._live()["sig"].count("-"), 1)  # the gallery doesn't follow it

    def test_the_switch_and_the_buttons_routes(self):
        self.place("spread2")
        self.assertFalse(routes._upscale_on(request(H, {"on": False}))["on"])
        self.assertEqual(routes._upscale_start(request(H, {}))["queue"], ["spread2"])
        self.assertTrue(routes._upscale_on(request(H, {"on": True}))["on"])
        self.assertEqual(routes._upscale_start(request(H, {"key": "spread2"}))["queue"], ["spread2"])


class PickingUpFromTheFolder(Base):
    """«Підхопити з папки» (the owner, 27.09.2026: "I put the spreads into the folder with the right names and the
    program doesn't pick them up"): what was put into originals/ by hand goes the usual way on a press."""

    def put(self, rel, size=(1024, 512)):
        return spread_png(self.dir / H / "originals" / rel, size)

    def test_a_variants_spreads_and_cover_put_by_hand_are_cut_flipped_and_upscaled(self):
        v = "G2_brunette"
        self.put(f"variants/{v}/spread-04-05.png")
        self.put(f"variants/{v}/cover-wrap.png", (1100, 580))
        self.put(f"variants/{v}/hero.png", (400, 400))
        self.assertEqual(pictures.left_behind(H), {v: ["spread3", "cover-wrap", "hero"]})
        r = pictures.adopt(H, v)
        self.assertEqual((r["done"], r["failed"]), (["spread3", "cover-wrap", "hero"], []))
        folder = self.dir / H / "pictures" / "variants" / v
        self.assertEqual(self.pixel(H, "4.png", variant=v), (30, 60, 220))  # mirrored
        self.assertTrue((folder / "Cover.png").is_file())
        self.assertTrue((self.dir / H / "agent" / "variants" / v / "hero.png").is_file())
        # the files stay where they were put, nothing went to .replaced
        self.assertEqual(sorted(p.name for p in (self.dir / H / "originals" / "variants" / v).iterdir()),
                         ["cover-wrap.png", "hero.png", "spread-04-05.png"])
        self.assertFalse((self.dir / H / ".replaced").exists())
        self.assertEqual(upscale.status(H)["queue"], [f"{v}/spread3", f"{v}/cover-wrap"])  # the hero isn't
        while upscale._upscaler.step():
            pass
        with Image.open(folder / "4.png") as im:
            self.assertEqual(im.size, (1024, 1024))
        self.assertEqual(pictures.left_behind(H), {})

    def test_the_base_book_and_rows_that_have_pages_are_left_alone(self):
        pictures.place(H, "spread2", spread_png(self.tmp / "a.png"), "a.png")
        before = (self.dir / H / "pictures" / "2.png").stat().st_mtime_ns
        self.put("page-01.png", (600, 600))
        self.put("cover-art.png", (1000, 500))
        self.assertEqual(pictures.left_behind(H), {"": ["page1", "cover"]})
        pictures.adopt(H, None)
        self.assertTrue((self.dir / H / "pictures" / "1.png").is_file())
        self.assertTrue((self.dir / H / "originals" / "cover-expanded.png").is_file())  # on to its margins
        self.assertEqual((self.dir / H / "pictures" / "2.png").stat().st_mtime_ns, before)

    def test_the_route_is_a_job_and_says_when_there_is_nothing(self):
        with self.assertRaises(ApiError):
            routes._adopt(request(H, {"variant": "G2_brunette"}))
        self.put("variants/G2_brunette/spread-02-03.png")
        job = jobs.get(routes._adopt(request(H, {"variant": "G2_brunette"}))["jobId"])
        for _ in range(200):
            if job.status != "running":
                break
            time.sleep(0.05)
        self.assertEqual((job.status, job.result["done"]), ("done", ["spread2"]), job.error)
        self.assertIn("leftBehind", routes._get(request(H))["book"])


class FindingUpscayl(unittest.TestCase):
    def test_the_engine_is_found_by_upscayls_own_log_and_remembered(self):
        saved = core.settings.section("workshop").get("upscayl", "")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "Up" / "resources" / "bin" / "upscayl-bin.exe"
            models = exe.parent.parent / "models"
            exe.parent.mkdir(parents=True)
            models.mkdir()
            exe.write_bytes(b"")
            (models / "upscayl-standard-4x.param").write_text("")
            (models / "upscayl-standard-4x.bin").write_text("")
            logs = root / "appdata" / "Upscayl" / "logs"
            logs.mkdir(parents=True)
            (logs / "main.log").write_text(f"[info]  UPSCAYL EXEC PATH:  {exe.with_suffix('')}\n", encoding="utf-8")
            env = {"APPDATA": str(root / "appdata"), "LOCALAPPDATA": str(root / "x"), "ProgramFiles": str(root / "y")}
            try:
                core.settings.update({"workshop": {"upscayl": ""}})
                upscale._missing_until = 0
                with unittest.mock.patch.dict(os.environ, env):
                    self.assertEqual(upscale.engine(), (exe, models))
                self.assertEqual(core.settings.section("workshop")["upscayl"], str(exe))
            finally:
                core.settings.update({"workshop": {"upscayl": saved}})
                upscale._missing_until = 0


if __name__ == "__main__":
    unittest.main()
