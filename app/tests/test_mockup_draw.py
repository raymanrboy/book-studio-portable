"""Mockups drawn by Book Studio itself (13.10.2026): the baked templates (linear and multiply), the scenes' colours from
the cover, the drawn run, and the crop window's routes."""
import json
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
from PIL import Image, ImageDraw

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core, mockup_colours, mockup_render, mockups
from studio.jobs import Job
from studio.server import ApiError, Response
from tests.test_mockups import PICKS, demo_book

H, W = 8, 10


def _write(key: str, psd: Path, arrays: dict, meta: dict) -> None:
    mockup_render.BAKED.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(mockup_render.BAKED / f"{key}.npz", meta=np.frombuffer(json.dumps(meta).encode(), np.uint8), **arrays)
    stamps = mockup_render._stamps_file()
    stamps[key] = {"stamp": mockup_render.stamp(psd)}
    (mockup_render.BAKED / mockup_render.STAMPS).write_text(json.dumps(stamps), encoding="utf-8")


def _identity_uv(h, w):
    u = np.repeat((np.arange(w) / (w - 1))[None, :], h, 0)
    v = np.repeat((np.arange(h) / (h - 1))[:, None], w, 1)
    return np.stack([u, v], -1)


def linear_asset(psd: Path) -> None:
    """One smart object over the whole canvas, taken pixel for pixel, at full strength, on black."""
    _write("cover1", psd, {"k": np.zeros((H, W, 3), np.uint16),
                           "front_gain": np.full((H, W, 3), round(2 * 32767.5), np.uint16),
                           "front_uv": np.round(_identity_uv(H, W) * 32768 + 16384).astype(np.uint16)},
           {"key": "cover1", "slots": {"front": [0, H, 0, W]}, "colours": {}, "parts": []})


def multiply_asset(psd: Path) -> None:
    """A softcover scene: the book over the left half (its tone curve plain: out = the picture), a grey background on
    the right with the burn fill over it, at the vendor's colour (200, 200, 200)."""
    k = np.zeros((H, W, 3), np.uint16)
    k[:, W // 2:] = round(0.5 * 65535)
    alphas = np.zeros((1, H, W), np.uint16)
    alphas[0, :, : W // 2] = 65535
    rise = np.zeros((8, H, W, 3), np.uint8)
    for i in range(8):
        rise[i, :, : W // 2] = round((i + 1) / 8 * 255)
    mask = np.zeros((H, W), np.uint8)
    mask[:, W // 2:] = 255
    _write("coverOpen", psd, {"k": k, "rise": rise, "alphas": alphas,
                              "uv": np.round(_identity_uv(H, W)[None] * 32768 + 16384).astype(np.uint16), "fill0": mask},
           {"key": "coverOpen", "box": [0, H, 0, W], "slots": ["front"], "interp": {}, "prescale": {},
            "fills": [["Change Color", "linear_burn", [200, 200, 200]]]})


class Baked(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.psd = Path(self.tmp.name) / "1. Cover 1.psd"
        self.psd.write_bytes(b"template" * 100)
        mockup_render.forget()

    def tearDown(self):
        mockup_render.forget()
        shutil.rmtree(mockup_render.BAKED, ignore_errors=True)
        self.tmp.cleanup()

    def picture(self, seed=1):
        rng = np.random.default_rng(seed)
        return Image.fromarray(rng.integers(0, 255, (H, W, 3), dtype=np.uint8), "RGB")

    def test_a_template_counts_as_baked_only_while_it_is_the_very_file(self):
        self.assertFalse(mockup_render.ready("cover1", self.psd))
        linear_asset(self.psd)
        self.assertTrue(mockup_render.ready("cover1", self.psd))
        self.psd.write_bytes(b"resaved by someone" * 100)        # another file: the Photoshop way again
        self.assertFalse(mockup_render.ready("cover1", self.psd))

    def test_a_linear_template_takes_the_picture_where_its_map_says(self):
        linear_asset(self.psd)
        pic = self.picture()
        out = np.asarray(mockup_render.render("cover1", {"front": pic}))
        self.assertLessEqual(np.abs(out.astype(int) - np.asarray(pic, int)).max(), 1)

    def test_a_softcover_scene_keeps_its_book_and_takes_another_background(self):
        multiply_asset(self.psd)
        pic = self.picture(2)
        out = np.asarray(mockup_render.render("coverOpen", {"front": pic})).astype(int)
        self.assertLessEqual(np.abs(out[:, : W // 2] - np.asarray(pic, int)[:, : W // 2]).max(), 1)   # the book
        self.assertTrue(np.all(np.abs(out[:, W // 2:] - 128) <= 1))                                     # the background
        lighter = np.asarray(mockup_render.render("coverOpen", {"front": pic}, {"Change Color": (250, 230, 200)})).astype(int)
        self.assertLessEqual(np.abs(lighter[:, : W // 2] - out[:, : W // 2]).max(), 0)                  # the book stays
        self.assertTrue(np.all(np.abs(lighter[0, -1] - (178, 158, 128)) <= 1))                           # + (50, 30, 0)
        self.assertEqual(mockup_render.fills("coverOpen"), {"Change Color": (200, 200, 200)})


class Colours(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cover = Path(self.tmp.name) / "cover.png"
        im = Image.new("RGB", (400, 200), (40, 70, 160))                  # a blue back
        ImageDraw.Draw(im).rectangle([200, 0, 399, 199], fill=(230, 120, 40))   # an orange front
        ImageDraw.Draw(im).rectangle([260, 60, 340, 140], fill=(250, 250, 250))  # its middle — not its edge
        im.save(self.cover)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_edges_come_from_each_halfs_outer_edges(self):
        self.assertEqual(mockup_colours.edges(self.cover), {"front": "#e67828", "back": "#2846a0"})

    def test_pastels_are_light_soft_shades_of_the_covers_own_hues_and_a_warm_white(self):
        shades = mockup_colours.pastels(self.cover)
        self.assertGreaterEqual(len(shades), 3)
        rgbs = [mockup_colours.rgb_of(h) for h in shades]
        self.assertTrue(all(min(c) >= 180 for c in rgbs), shades)        # light
        self.assertTrue(all(max(c) - min(c) <= 60 for c in rgbs), shades)  # soft
        self.assertTrue([c for c in rgbs[:-1] if c[0] > c[2] + 20])         # the orange front's hue
        self.assertTrue([c for c in rgbs[:-1] if c[2] > c[0] + 20])         # the blue back's
        self.assertEqual(shades[-1], mockup_colours._pastel(*mockup_colours.NEUTRAL))

    def test_colours_travel_as_hex(self):
        self.assertEqual(mockup_colours.rgb_of("#0a10ff"), (10, 16, 255))
        self.assertIsNone(mockup_colours.rgb_of("red"))
        self.assertEqual(mockup_colours.hex_of((10.4, 16, 300)), "#0a10ff")


class TheFrontsCrop(unittest.TestCase):
    def test_the_owners_crop_moves_the_front_over_the_whole_cover(self):
        # 13.10.2026, the owner: "the whole picture's spare — moving left and right is what happens most"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cover.png"
            im = Image.new("RGB", (200, 100), (0, 0, 255))                        # a blue back
            ImageDraw.Draw(im).rectangle([100, 0, 199, 99], fill=(0, 0, 0))       # a black front
            ImageDraw.Draw(im).rectangle([100, 0, 149, 49], fill=(255, 0, 0))     # its top-left quarter red
            im.save(path)
            size = {"board": (40, 40), "spine": (4, 40)}
            plain = mockups.cover_pictures(path, size)
            self.assertEqual(plain["front"].getpixel((5, 5)), (255, 0, 0))
            self.assertEqual(plain["front"].getpixel((35, 35)), (0, 0, 0))
            same = mockups.cover_pictures(path, size, {"x": mockups.FRONT_X, "y": 0.5, "zoom": 1})
            self.assertEqual(same["front"].tobytes(), plain["front"].tobytes())     # the program's own place
            near = mockups.cover_pictures(path, size, {"x": 0.625, "y": 0.25, "zoom": 2})
            self.assertEqual(near["front"].getpixel((35, 35)), (255, 0, 0))        # only the red quarter now
            left = mockups.cover_pictures(path, size, {"x": 0.5, "y": 0.5, "zoom": 1})
            self.assertEqual(left["front"].getpixel((5, 20)), (0, 0, 255))         # over the spine: the back shows
            self.assertEqual(left["front"].getpixel((35, 30)), (0, 0, 0))
            self.assertEqual(left["back"].tobytes(), plain["back"].tobytes())       # the back stays as it was
            far = mockups.cover_pictures(path, size, {"x": 0.75, "y": 0.5, "zoom": 0.2})
            self.assertEqual(far["front"].size, (40, 40))                           # never bigger than the cover lets
            self.assertEqual(far["front"].tobytes(), plain["front"].tobytes())
            self.assertEqual(mockups._crop_values({"x": "nan", "y": 7, "zoom": 99}), (mockups.FRONT_X, 1.0, mockups.MAX_ZOOM))
            self.assertEqual(mockups.min_zoom((200, 100), (40, 40)), 1.0)
            self.assertEqual(mockups.min_zoom((400, 100), (40, 40)), 1.0)
            self.assertAlmostEqual(mockups.min_zoom((200, 100), (30, 40)), 1.0)


class Req(SimpleNamespace):
    def param(self, name, default=None):
        return self.query.get(name, default)

    def int_param(self, name, default, lo=None, hi=None):
        return int(self.query.get(name, default))


class DrawnRun(unittest.TestCase):
    """A run with every template baked: no Photoshop, pictures saved at once, the crop window redraws them."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.templates = self.root / "Трафарети мастхев"
        self.templates.mkdir()
        for t in mockups.TEMPLATES:
            (self.templates / t["file"]).write_bytes(t["file"].encode() * 100)
        self.out = self.root / "Мокапи"
        self.out.mkdir()
        self.book = mockups.read_book(demo_book(self.root / "Goose"))
        self.drawn, self.cut, self.cut_only = [], [], []

        def cut_drawn(im, target, templates, kind):
            self.cut_only.append(target.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            im.save(target, dpi=(300, 300))

        def render(key, pictures, colours=None):
            self.drawn.append((key, sorted(pictures), colours))
            colour = (colours or {}).get("Change Color") or (90, 90, 90)
            im = Image.new("RGB", (30, 20), tuple(round(v) for v in colour))
            im.paste(pictures["front"].resize((10, 10)) if "front" in pictures else pictures[sorted(pictures)[0]].resize((10, 10)), (0, 0))
            return im

        slots = {"open1": ["left", "right", "front", "back", "spine"], "open2": ["left", "right", "front", "back", "spine"],
                 "cover1": ["front"], "dedication": ["page1", "front", "back", "spine"], "coverOpen": ["left", "right", "front"],
                 "allOpen": ["left", "right", "front", "back", "spine"]}
        patches = [
            mock.patch.object(mockups, "places", lambda: {"templates": self.templates, "photoshop": self.root, "lastOut": ""}),
            mock.patch.object(mockups, "WORK", self.root / "work"),
            mock.patch.object(mockups, "mockup_render", SimpleNamespace(ready=lambda key, psd: True, slots=slots.get,
                                                                         render=render, forget=lambda: None)),
            mock.patch.object(mockups, "launch", lambda script: self.fail("Photoshop must not be asked")),
            mock.patch.object(mockups.slide_cutout.cutter, "add", lambda png, folder, again=False: self.cut.append((Path(png).name, again))),
            mock.patch.object(mockups.slide_cutout, "cut_drawn", cut_drawn),
            mock.patch.object(mockups, "_to_etsy", lambda result: result),
            mock.patch.dict(mockups.HARD, {"page": (40, 40), "board": (44, 46), "spine": (4, 46)}),
            mock.patch.dict(mockups.SOFT, {"page": (40, 40), "board": (40, 40), "spine": (6, 40)}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def run_it(self, only=None):
        job = Job("mockups")
        return job, mockups.make(job, self.book, PICKS, self.out, threading.Event(), only)

    def test_every_picture_is_drawn_saved_and_cut_without_photoshop(self):
        job, res = self.run_it()
        self.assertTrue(res["drawn"])
        self.assertEqual(len(res["saved"]), 10)          # 4 + 2 + 1 + 1 + Dedication + Cover 1: nothing left open
        self.assertEqual(res["open"], [])
        self.assertEqual(res["run"], "")                 # no «Зберегти відкриті» for the page to offer
        nobg = self.out / mockups.slide_cutout.NO_BG
        for name in res["saved"]:
            with Image.open(self.out / name if (self.out / name).exists() else nobg / name) as im:
                self.assertEqual(tuple(round(v) for v in im.info.get("dpi")), (300, 300))
        # Open 1, Open 2, Dedication only without their background (the owner, 13.10.2026), cut at once
        self.assertEqual(sorted(p.name for p in self.out.glob("*.png")),
                         ["1. Cover 1.png", "All & Open 1 (16-17).png", "Cover & Open 1 (4-5).png"])
        self.assertEqual(len(self.cut_only), 7)
        self.assertTrue((nobg / "2. Open 1 (2-3).png").is_file() and (nobg / "4. Dedication.png").is_file())
        self.assertIn(("1. Cover 1.png", False), self.cut)              # Cover 1 keeps both: the photo mockups' reference
        self.assertFalse([n for n, _ in self.cut if "Open 1 (" in n and "&" not in n or "Dedication" in n])
        again = mockups.draw_plan(self.book, PICKS, self.out)            # a second run never lands on them
        self.assertEqual(again[0]["save"], str(self.out / "2. Open 1 (2-3) (2).png"))
        self.assertEqual(res["edits"], {"1. Cover 1.png": "cover1", "Cover & Open 1 (4-5).png": "coverOpen",
                                        "All & Open 1 (16-17).png": "allOpen"})
        scenes = [c for k, _, c in self.drawn if k in mockups.SCENES]
        self.assertTrue(all(set(c) == {"Change Color", "Front Color", "Back Color"} for c in scenes))   # from the cover
        self.assertTrue(all(c is None for k, _, c in self.drawn if k not in mockups.SCENES))

    def test_a_template_that_is_not_baked_sends_the_run_to_photoshop(self):
        mockups.mockup_render.ready = lambda key, psd: key != "dedication"
        with mock.patch.object(mockups, "find_photoshop", lambda base: None):
            with self.assertRaises(Exception) as caught:
                self.run_it()
        self.assertIn("Photoshop", str(caught.exception))
        _, res = self.run_it(only=["open1", "cover1"])      # without it, drawn here
        self.assertEqual(len(res["saved"]), 5)

    def test_the_crop_window_redraws_the_picture_over_itself(self):
        job, res = self.run_it()
        cover = self.out / "1. Cover 1.png"
        before = cover.read_bytes()
        state = mockups._edit_state(Req(query={"job": job.id, "key": "cover1"}))
        self.assertEqual(state["crop"], {"x": mockups.FRONT_X, "y": 0.5, "zoom": 1.0})
        self.assertFalse(state["scene"])
        preview = mockups._edit_preview(Req(query={"job": job.id, "key": "cover1", "x": "0", "y": "0", "zoom": "2", "w": "300"}))
        self.assertIsInstance(preview, Response)
        self.assertEqual(preview.content_type, "image/jpeg")
        self.assertEqual(cover.read_bytes(), before)                     # a preview saves nothing
        self.cut.clear()
        saved = mockups._edit_save(Req(json={"job": job.id, "key": "cover1", "crop": {"x": 0, "y": 0, "zoom": 2}}))
        self.assertEqual(saved["saved"], ["1. Cover 1.png"])
        self.assertNotEqual(cover.read_bytes(), before)
        self.assertEqual(self.cut, [("1. Cover 1.png", True)])           # its «Без фону» made again
        self.assertEqual(mockups._edit_state(Req(query={"job": job.id, "key": "cover1"}))["crop"], {"x": 0.0, "y": 0.0, "zoom": 2.0})
        with self.assertRaises(ApiError):
            mockups._edit_state(Req(query={"job": job.id, "key": "open1"}))   # no front cover to move there

    def test_a_new_background_redraws_both_scenes(self):
        job, _ = self.run_it()
        state = mockups._edit_state(Req(query={"job": job.id, "key": "coverOpen"}))
        self.assertTrue(state["scene"])
        self.assertEqual(state["others"], ["All & Open 1"])
        self.assertEqual(state["colours"]["background"], state["suggest"]["background"][0])
        self.drawn.clear()
        res = mockups._edit_save(Req(json={"job": job.id, "key": "coverOpen", "background": "#ffeedd"}))
        self.assertEqual(res["saved"], ["Cover & Open 1 (4-5).png", "All & Open 1 (16-17).png"])
        self.assertTrue(all(c["Change Color"] == (255, 238, 221) for _, _, c in self.drawn))
        self.drawn.clear()
        res = mockups._edit_save(Req(json={"job": job.id, "key": "coverOpen", "crop": {"zoom": 1.5}}))
        self.assertEqual(res["saved"], ["Cover & Open 1 (4-5).png"])      # the colours as they were: this one only

    def test_a_save_that_failed_halfway_is_made_good_by_the_next(self):
        job, _ = self.run_it()
        real = mockups._save_drawn

        def flaky(im, path):
            if path.name.startswith("All & Open 1"):
                raise OSError("busy")
            real(im, path)
        with mock.patch.object(mockups, "_save_drawn", flaky):
            with self.assertRaises(OSError):
                mockups._edit_save(Req(json={"job": job.id, "key": "coverOpen", "background": "#ffeedd"}))
        self.assertFalse(list(self.out.glob("*.part.png")))
        self.drawn.clear()
        res = mockups._edit_save(Req(json={"job": job.id, "key": "coverOpen", "background": "#ffeedd"}))
        self.assertEqual(res["saved"], ["Cover & Open 1 (4-5).png", "All & Open 1 (16-17).png"])   # the other one too

    def test_the_window_needs_the_book_still_open(self):
        job, _ = self.run_it()
        mockups.close()
        with self.assertRaises(ApiError) as caught:
            mockups._edit_state(Req(query={"job": job.id, "key": "cover1"}))
        self.assertIn("закрито", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
