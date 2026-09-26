"""Listing mockups: reading the Canva demo book, the pictures for the smart objects, the run plan, following
Photoshop — and the Photoshop script itself, run by Node.js against a pretend Photoshop."""
import json
import re
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from PIL import Image, ImageDraw

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core, drops, mockups
from studio.jobs import Job, UserError
from studio.server import ApiError

GREEN, DARK, YELLOW = (60, 170, 80), (20, 30, 60), (240, 210, 80)
# Every template with one spread each where there are slots — the shape of what the page sends.
PICKS = {"open1": [2, 6, 10, 14], "open2": [8, 12], "coverOpen": [4], "allOpen": [16]}


def cover(path: Path, size=(1000, 500)):
    """A wide Canva cover: a green back, a yellow front, a dark spine strip in the exact middle."""
    im = Image.new("RGB", size, GREEN)
    d = ImageDraw.Draw(im)
    d.rectangle([size[0] // 2, 0, size[0], size[1]], fill=YELLOW)
    d.rectangle([size[0] // 2 - 10, 0, size[0] // 2 + 9, size[1]], fill=DARK)
    im.save(path)


def demo_book(folder: Path, pages: int = 30) -> Path:
    """Canva's own names: 1.png is the wide cover, 2..N+1 the pages."""
    folder.mkdir(parents=True, exist_ok=True)
    cover(folder / "1.png")
    for n in range(2, pages + 2):
        Image.new("RGB", (60, 60), (n * 7 % 255, 120, 200)).save(folder / f"{n}.png")
    return folder


def book(pages: int = 30) -> dict:
    return {"id": "0" * 16, "name": "Goose", "cover": Path("cover.png"),
            "pages": {n: Path(f"{n}.png") for n in range(1, pages + 1)}}


class ReadingTheDemoBook(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_canva_zip_gives_the_cover_and_the_spreads(self):
        found = mockups.read_book(demo_book(self.root / "Goose"))
        self.assertEqual(found["cover"].name, "1.png")                     # the one wide picture
        self.assertEqual(found["pages"][1].name, "2.png")                  # Canva's page 2 is the book's page 1
        self.assertEqual(found["pages"][30].name, "31.png")
        view = mockups.book_view(found)
        self.assertEqual(view["spreads"][0], [2, 3])
        self.assertEqual(view["spreads"][-1], [28, 29])                    # page 30, the afterword, is alone
        self.assertEqual(len(view["spreads"]), 14)

    def test_a_book_without_a_cover_is_refused(self):
        folder = self.root / "Goose"
        folder.mkdir()
        for n in range(1, 6):
            Image.new("RGB", (60, 60)).save(folder / f"{n}.png")
        with self.assertRaises(ApiError) as caught:
            mockups.read_book(folder)
        self.assertIn("обкладинку", str(caught.exception))

    def test_only_what_was_dropped_into_the_window_is_read(self):
        with self.assertRaises(ApiError):
            mockups._open_book(SimpleNamespace(json={"path": str(demo_book(self.root / "Goose"))}))
        inside = demo_book(drops.DROPS / ("a" * 32) / "Goose")
        try:
            self.assertEqual(mockups._open_book(SimpleNamespace(json={"path": str(inside)}))["pageCount"], 30)
            # The dropped book moved into the mockups' own folder: Book Studio's cleaning of dropped files (an
            # order's card) can't take it away mid-run, and its own cleaning never reaches an order's files.
            self.assertFalse((drops.DROPS / ("a" * 32)).exists())
            self.assertTrue((mockups.BOOKS / ("a" * 32) / "Goose" / "1.png").is_file())
        finally:
            mockups.clear_books()

    def test_a_dropped_folder_that_is_no_book_is_not_kept(self):
        folder = drops.DROPS / ("d" * 32) / "Holiday"
        folder.mkdir(parents=True)
        Image.new("RGB", (60, 60)).save(folder / "1.png")
        try:
            with self.assertRaises(ApiError):
                mockups._open_book(SimpleNamespace(json={"path": str(folder)}))
            self.assertFalse((mockups.BOOKS / ("d" * 32)).exists())
        finally:
            shutil.rmtree(drops.DROPS / ("d" * 32), ignore_errors=True)
            mockups.clear_books()


class Pictures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_cover_is_cut_into_back_front_and_spine(self):
        """The back is the left half, the front the right half, the spine the strip from the exact middle."""
        cover(self.root / "cover.png")
        for size in (mockups.HARD, mockups.SOFT):
            with self.subTest(board=size["board"]):
                parts = mockups.cover_pictures(self.root / "cover.png", size)
                self.assertEqual(parts["back"].size, size["board"])
                self.assertEqual(parts["front"].size, size["board"])
                self.assertEqual(parts["spine"].size, size["spine"])
                w, h = size["board"]
                self.assertEqual(parts["back"].getpixel((w // 3, h // 2)), GREEN)
                self.assertEqual(parts["front"].getpixel((2 * w // 3, h // 2)), YELLOW)
                sw, sh = size["spine"]
                self.assertEqual(parts["spine"].getpixel((sw // 2, sh // 2)), DARK)

    def test_pages_fill_their_square_and_keep_300_dpi(self):
        Image.new("RGB", (300, 200), (10, 20, 30)).save(self.root / "p.png")   # not square: the sides go
        page = mockups.page_picture(self.root / "p.png", mockups.HARD["page"])
        self.assertEqual(page.size, (1900, 1900))
        mockups._save_png(page, self.root / "out.png")
        with Image.open(self.root / "out.png") as im:
            self.assertAlmostEqual(im.info["dpi"][0], 300, places=1)          # a smart object's size stays

    def test_a_see_through_page_lies_on_white(self):
        Image.new("RGBA", (50, 50), (0, 0, 0, 0)).save(self.root / "p.png")
        self.assertEqual(mockups.page_picture(self.root / "p.png", (40, 40)).getpixel((20, 20)), (255, 255, 255))


class RunPlan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.templates = self.root / "Трафарети"
        self.out = self.root / "out"
        self.out.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self, picks=PICKS):
        return mockups.plan(book(), picks, self.out, self.root / "run", self.templates)

    def test_every_template_gets_its_pictures_and_the_front_cover_is_left_alone(self):
        work = self.plan()
        by = {t["key"]: t for t in work["templates"]}
        self.assertEqual([t["key"] for t in work["templates"]], list(mockups.RUN_ORDER))
        self.assertEqual(len(by["open1"]["shots"]), 4)
        self.assertEqual(len(by["open2"]["shots"]), 2)
        self.assertEqual([f["layer"] for f in by["open1"]["shots"][1]["fills"]], [["Main", "Left"], ["Main", "Right"]])
        self.assertTrue(by["open1"]["shots"][1]["fills"][0]["image"].endswith("hard-page-6.png"))
        self.assertTrue(by["open1"]["shots"][1]["fills"][1]["image"].endswith("hard-page-7.png"))
        # back, spine and the front cover's rim in the open books; page 1 in the dedication
        self.assertEqual([f["layer"][-1] for f in by["open2"]["fills"]], ["Cover", "Back Cover", "Rige"])
        self.assertEqual(by["dedication"]["fills"][-1]["layer"], ["Main", "Page 1"])
        self.assertTrue(by["dedication"]["fills"][-1]["image"].endswith("hard-page-1.png"))
        self.assertEqual(len(by["dedication"]["shots"]), 1)
        # the three where the front cover shows: filled, left open, nothing saved, the front never touched
        for key in ("cover1", "coverOpen", "allOpen"):
            with self.subTest(template=key):
                t = by[key]
                self.assertTrue(t["keepOpen"])
                self.assertEqual(t["shots"], [])
                hand = list(next(x for x in mockups.TEMPLATES if x["key"] == key)["hand"])
                self.assertNotIn(hand, [f["layer"] for f in t["fills"]])
        self.assertEqual([f["layer"] for f in by["allOpen"]["fills"]], [["Back Cover"], ["Spine"], ["Left"], ["Right"]])
        self.assertTrue(by["allOpen"]["fills"][0]["image"].endswith("soft-back.png"))   # the square softcover's size
        self.assertNotIn("soft-front.png", work["pictures"])

    def test_pictures_are_named_by_template_and_pages_and_never_overwrite(self):
        (self.out / "2. Open 1 (2-3).png").write_bytes(b"an earlier one")
        work = self.plan({**PICKS, "open1": [2, 2, 10, 14]})
        saves = [Path(s["save"]).name for t in work["templates"] for s in t["shots"]]
        self.assertEqual(saves, ["2. Open 1 (2-3) (2).png", "2. Open 1 (2-3) (3).png", "2. Open 1 (10-11).png",
                                 "2. Open 1 (14-15).png", "3. Open 2 (8-9).png", "3. Open 2 (12-13).png",
                                 "4. Dedication.png"])

    def test_a_wrong_pick_is_refused(self):
        for picks in ({**PICKS, "open1": [2, 6]},              # too few
                      {**PICKS, "open2": [8, 13]},             # not the start of a spread
                      {**PICKS, "coverOpen": [30]},            # the afterword is not a spread
                      {k: v for k, v in PICKS.items() if k != "allOpen"}):
            with self.subTest(picks=picks), self.assertRaises(ApiError):
                self.plan(picks)

    def test_nothing_is_opened_or_saved_in_the_templates_folder(self):
        work = self.plan()
        text = mockups.script(work)
        for t in work["templates"]:
            self.assertFalse(mockups._inside(Path(t["file"]), self.templates))
            for s in t["shots"]:
                self.assertFalse(mockups._inside(Path(s["save"]), self.templates))
        self.assertNotIn(self.templates.as_posix(), text)
        self.assertNotIn(json.dumps(self.templates.as_posix()).strip('"'), text)   # nor as \u escapes
        text.encode("ascii")                                                        # Photoshop 2019 reads it as is


class FakePhotoshop:
    """Stands in for launch(): plays the script's part by writing its status file."""

    def __init__(self, states=("done",), opened=("1. Cover 1",)):
        self.states, self.opened, self.scripts = states, opened, []

    def __call__(self, script: Path):
        self.scripts.append(script.read_text(encoding="ascii"))
        work = json.loads((script.parent / "job.json").read_text(encoding="utf-8"))
        saved = [s["save"] for t in work["templates"] for s in t["shots"]]
        for s in saved:
            Path(s).write_bytes(b"png")
        status = {"state": self.states[-1], "step": 10, "total": 10, "saved": saved, "opened": list(self.opened),
                  "problems": [{"kind": "layer", "template": "3. Open 2", "layer": "Main/Left"}] * 2}
        Path(work["status"]).write_text(json.dumps(status), encoding="utf-8")


class Run(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.templates = self.root / "Трафарети мастхев"
        self.templates.mkdir()
        for t in mockups.TEMPLATES:
            (self.templates / t["file"]).write_bytes(t["file"].encode() * 1000)
        self.stamps = {p.name: p.stat().st_mtime_ns for p in self.templates.iterdir()}
        self.out = self.root / "Мокапи"
        self.out.mkdir()
        self.book = mockups.read_book(demo_book(self.root / "Goose"))
        patches = [
            mock.patch.object(mockups, "places", lambda: {"templates": self.templates, "photoshop": self.root, "lastOut": ""}),
            mock.patch.object(mockups, "find_photoshop", lambda base: {"exe": Path("Photoshop.exe"), "launcher": Path("Photoshop.exe")}),
            mock.patch.object(mockups, "running", lambda: True),
            mock.patch.object(mockups, "WORK", self.root / "work"),
            # small smart objects: the sizes themselves are checked in Pictures
            mock.patch.dict(mockups.HARD, {"page": (40, 40), "board": (44, 46), "spine": (4, 46)}),
            mock.patch.dict(mockups.SOFT, {"page": (40, 40), "board": (40, 40), "spine": (6, 40)}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, photoshop, cancel=None):
        with mock.patch.object(mockups, "launch", photoshop):
            return mockups.make(Job("mockups"), self.book, PICKS, self.out, cancel or threading.Event())

    def test_a_run_saves_the_pictures_and_keeps_the_templates_untouched(self):
        photoshop = FakePhotoshop(opened=("1. Cover 1", "Cover & Open 1", "All & Open 1"))
        result = self.make(photoshop)
        self.assertEqual(len(result["saved"]), 7)
        self.assertIn("4. Dedication.png", result["saved"])
        self.assertEqual(result["open"], ["Cover 1", "Cover & Open 1", "All & Open 1"])
        self.assertEqual(result["problems"], ["У «3. Open 2» немає смарт-об'єкта «Main/Left»"])
        self.assertEqual(len(photoshop.scripts), 1)                       # one script, one "run this?" click
        run = next((self.root / "work").iterdir())
        self.assertEqual(result["run"], run.name)                         # «Зберегти відкриті» finds it by this
        copies = sorted(p.name for p in (run / "templates").iterdir())
        self.assertEqual(copies, ["1. Cover 1.psd", "All & Open 1.psd", "Cover & Open 1.psd"])   # closed ones go
        self.assertFalse((run / "pictures").exists())                     # the smart objects hold them now
        # the templates folder: the same files, never written
        self.assertEqual({p.name: p.stat().st_mtime_ns for p in self.templates.iterdir()}, self.stamps)

    def test_the_output_may_not_be_the_templates_folder(self):
        with self.assertRaises(UserError):
            mockups.make(Job("mockups"), self.book, PICKS, self.templates, threading.Event())
        with self.assertRaises(ApiError):
            with mock.patch.object(mockups.desktop, "pick_folder", lambda *a: str(self.templates)):
                mockups._pick_out(SimpleNamespace())

    def test_stopping_before_photoshop_starts_the_script(self):
        """The owner stops while Photoshop still asks "run this script?": a late "Yes" must do nothing."""
        cancel = threading.Event()
        cancel.set()
        photoshop = mock.Mock()
        with self.assertRaises(UserError):
            self.make(photoshop, cancel)
        photoshop.assert_not_called()

    def test_a_late_stop_leaves_the_stop_mark_for_the_script(self):
        work = mockups.plan(self.book, PICKS, self.out, self.root / "run", self.templates)
        (self.root / "run").mkdir()
        cancel = threading.Event()
        clock = iter(range(0, 10_000, 1))
        with self.assertRaises(UserError):
            mockups.watch(Job("mockups"), work, cancel, clock=lambda: next(clock), pause=lambda s: cancel.set())
        self.assertTrue(Path(work["cancel"]).exists())

    def test_photoshop_closing_midway_ends_the_wait(self):
        work = mockups.plan(self.book, PICKS, self.out, self.root / "run", self.templates)
        (self.root / "run").mkdir()
        Path(work["status"]).write_text(json.dumps({"state": "running", "step": 2, "total": 10}), encoding="utf-8")
        now = [0.0]

        def pause(seconds):
            now[0] += 6
        with mock.patch.object(mockups, "running", lambda: False), self.assertRaises(UserError) as caught:
            mockups.watch(Job("mockups"), work, threading.Event(), clock=lambda: now[0], pause=pause)
        self.assertIn("закрився", str(caught.exception))

    def test_a_script_error_is_told(self):
        with self.assertRaises(UserError) as caught:
            self.make(FakePhotoshop(states=("error",)))
        self.assertIn("Photoshop", str(caught.exception))

    def test_old_runs_go_and_the_current_one_stays(self):
        work = self.root / "work"
        for name in ("old", "new"):
            (work / name).mkdir(parents=True)
        os.utime(work / "old", (0, 0))
        mockups.clean_runs(keep="new")
        self.assertEqual([p.name for p in work.iterdir()], ["new"])


class SaidInTheLog(unittest.TestCase):
    """23.09.2026: the owner's "I press it and nothing happens" left nothing to go by — each step is logged now."""

    def test_the_folder_dialog_and_its_answer_are_logged(self):
        with mock.patch.object(mockups.desktop, "pick_folder", lambda *a: None), self.assertLogs("studio", "INFO") as seen:
            self.assertEqual(mockups._pick_out(SimpleNamespace()), {"path": None})
        self.assertTrue(any("no folder picked" in line for line in seen.output))

    def test_a_failed_run_is_logged_and_still_reaches_the_page(self):
        job = Job("mockups")
        job.progress("Копіюю шаблони")

        def fails(j):
            raise UserError("Не знайшов Photoshop")
        with self.assertLogs("studio", "WARNING") as seen, self.assertRaises(UserError):
            mockups._logged(fails, job)
        self.assertIn("Копіюю шаблони", seen.output[0])
        self.assertIn("Не знайшов Photoshop", seen.output[0])


class Cleaning(unittest.TestCase):
    """What a run leaves behind goes as soon as nothing can need it (the owner, 23.09.2026: few leftovers, and
    nothing at all on drive C)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.work = self.root / "work"
        for p in (mock.patch.object(mockups, "WORK", self.work),
                  mock.patch.object(mockups, "PHOTOSHOP_TEMP", self.root / "ps-temp")):
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def run_folder(self, name: str, age: float = 0, owner_saved: bool = False) -> Path:
        run = self.work / name
        (run / "templates").mkdir(parents=True)
        (run / "job.json").write_text("{}", encoding="utf-8")
        copy = run / "templates" / "1. Cover 1.psd"
        copy.write_bytes(b"psd")
        written = (run / "job.json").stat().st_mtime
        os.utime(copy, (written - 5, written - 5))
        if owner_saved:
            os.utime(copy, (written + 60, written + 60))       # Ctrl+S in Photoshop, a minute later
        then = written - age
        os.utime(run, (then, then))
        return run

    def test_with_photoshop_closed_every_earlier_run_goes_at_once(self):
        self.run_folder("earlier")
        self.run_folder("current")
        with mock.patch.object(mockups, "running", lambda: False):
            self.assertEqual(mockups.clean_runs(keep="current"), 1)
        self.assertEqual([p.name for p in self.work.iterdir()], ["current"])

    def test_with_photoshop_open_the_copies_it_may_hold_stay_a_day(self):
        self.run_folder("fresh")
        self.run_folder("old", age=mockups.KEEP_RUNS + 60)
        with mock.patch.object(mockups, "running", lambda: True):
            mockups.clean_runs()
        self.assertEqual([p.name for p in self.work.iterdir()], ["fresh"])

    def test_a_copy_the_owner_saved_himself_stays_a_week(self):
        self.run_folder("saved", age=2 * 24 * 3600, owner_saved=True)
        with mock.patch.object(mockups, "running", lambda: False):
            mockups.clean_runs()
            self.assertTrue((self.work / "saved").exists())
            os.utime(self.work / "saved", (0, 0))
            mockups.clean_runs()
        self.assertFalse((self.work / "saved").exists())

    def test_photoshops_temp_folder_goes_only_once_photoshop_is_closed(self):
        (self.root / "ps-temp").mkdir()
        (self.root / "ps-temp" / "Photoshop Temp1234").write_bytes(b"scratch")
        with mock.patch.object(mockups, "running", lambda: True):
            mockups.clean_runs()
        self.assertTrue((self.root / "ps-temp").exists())
        with mock.patch.object(mockups, "running", lambda: False):
            mockups.clean_runs()
        self.assertFalse((self.root / "ps-temp").exists())

    def test_a_photoshop_started_from_here_keeps_its_temp_files_off_drive_c(self):
        ps = {"exe": Path("Photoshop.exe"), "launcher": Path("Photoshoр.exe")}
        with mock.patch.object(mockups, "find_photoshop", lambda base: ps), \
                mock.patch.object(mockups, "running", lambda: False), \
                mock.patch.object(mockups.subprocess, "Popen") as popen:
            mockups.launch(self.root / "mockups.jsx")
        env = popen.call_args.kwargs["env"]
        self.assertEqual(env["TEMP"], str(self.root / "ps-temp"))
        self.assertEqual(env["TMP"], str(self.root / "ps-temp"))

    def test_a_new_book_takes_the_place_of_the_last_one(self):
        order = drops.DROPS / ("e" * 32) / "Emma"                         # files just dropped into an order's card
        order.mkdir(parents=True)
        (order / "1.png").write_bytes(b"x")
        first = mockups.read_book(demo_book(mockups.BOOKS / ("b" * 32) / "Goose"))
        mockups._only_this_book(first)
        second = mockups.read_book(demo_book(mockups.BOOKS / ("c" * 32) / "Swan"))
        try:
            mockups._only_this_book(second)
            self.assertFalse((mockups.BOOKS / ("b" * 32)).exists())        # ~200 MB of a 4K book, gone at once
            self.assertTrue((mockups.BOOKS / ("c" * 32)).exists())
            self.assertTrue((order / "1.png").is_file())                    # the order's files are not the mockups'
            with self.assertRaises(ApiError):
                mockups._book(first["id"])
        finally:
            mockups.clear_books()
            shutil.rmtree(drops.DROPS / ("e" * 32), ignore_errors=True)

    def test_the_orders_cleaning_never_takes_the_demo_book(self):
        book = mockups.read_book(demo_book(mockups.BOOKS / ("f" * 32) / "Goose"))
        try:
            drops.clear_drops()                                             # Book Studio's start, /api/drop/done
            self.assertTrue(book["cover"].is_file())
        finally:
            mockups.clear_books()

    def test_the_old_utility_leaves_only_its_places_runs_and_logs(self):
        root = core.data_path("mockups")
        for name in (*mockups.OLD_UTILITY, "work", "logs"):
            (root / name).mkdir(parents=True, exist_ok=True)
            (root / name / "x.txt").write_text("x", encoding="utf-8")
        try:
            mockups.forget_old_utility()
            self.assertEqual(sorted(p.name for p in root.iterdir() if p.name in (*mockups.OLD_UTILITY, "work", "logs")),
                             ["logs", "work"])
        finally:
            for name in ("work", "logs"):
                shutil.rmtree(root / name, ignore_errors=True)

    def test_a_picked_zip_is_unpacked_straight_from_where_it_lies(self):
        import zipfile
        pages = demo_book(self.root / "export")
        archive = self.root / "Downloads" / "Goose demo.zip"
        archive.parent.mkdir()
        with zipfile.ZipFile(archive, "w") as zf:
            for f in pages.iterdir():
                zf.write(f, f.name)
        try:
            view = mockups._open_zip(SimpleNamespace(json={"path": str(archive)}))
            self.assertEqual(view["pageCount"], 30)
            self.assertEqual(len(list(mockups.BOOKS.iterdir())), 1)        # unpacked into the mockups' own folder
            self.assertTrue(archive.exists())                               # the owner's ZIP is only read
            with self.assertRaises(ApiError):
                mockups._open_zip(SimpleNamespace(json={"path": str(pages / "1.png")}))
        finally:
            mockups.clear_books()

    def test_the_program_puts_its_temp_files_on_drive_d_and_wipes_them(self):
        """The Edge window left its logs in Windows' temp folder on drive C: every program this one starts gets a
        temp folder inside the data folder instead."""
        saved = {k: os.environ.get(k) for k in ("TEMP", "TMP")}, tempfile.tempdir
        try:
            folder = core.own_temp()
            self.assertEqual(folder, core.data_path("tmp", "system"))
            self.assertEqual(os.environ["TEMP"], str(folder))
            self.assertEqual(os.environ["TMP"], str(folder))
            self.assertEqual(tempfile.gettempdir(), str(folder))
            (folder / "leftover.tmp").write_bytes(b"x")
            core.clear_own_temp()
            self.assertFalse(folder.exists())
        finally:
            for k, v in saved[0].items():
                os.environ[k] = v
            tempfile.tempdir = saved[1]


class SaveTheOpenOnes(unittest.TestCase):
    """«Зберегти відкриті»: the three templates the owner finished by hand are saved and closed by a second
    script, and the run's last files go with them."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out = self.root / "Мокапи"
        self.out.mkdir()
        self.run = self.root / "work" / "20260923-120000-abcdef"
        self.work = mockups.plan(book(), PICKS, self.out, self.run, self.root / "Трафарети")
        for t in self.work["templates"]:
            if t["keepOpen"]:
                Path(t["file"]).parent.mkdir(parents=True, exist_ok=True)
                Path(t["file"]).write_bytes(b"psd")
        core.write_json(self.run / "job.json", self.work, backup=False)
        (self.run / "status.json").write_text(json.dumps({"state": "done"}), encoding="utf-8")
        for p in (mock.patch.object(mockups, "WORK", self.root / "work"),
                  mock.patch.object(mockups, "running", lambda: True)):
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def test_they_are_named_like_the_rest_and_never_overwrite(self):
        (self.out / "1. Cover 1.png").write_bytes(b"saved by hand earlier")
        fin = mockups.finish_plan(self.run)
        self.assertTrue(fin["finish"])
        self.assertEqual([Path(t["shots"][0]["save"]).name for t in fin["templates"]],
                         ["1. Cover 1 (2).png", "Cover & Open 1 (4-5).png", "All & Open 1 (16-17).png"])
        self.assertEqual([t["file"] for t in fin["templates"]], [t["file"] for t in self.work["templates"] if t["keepOpen"]])
        self.assertIn('"finish": true', mockups.script(fin))

    def test_the_window_offers_them_again_after_a_reload(self):
        self.assertEqual(mockups.pending(), {"run": self.run.name, "folder": str(self.out),
                                             "open": ["Cover 1", "Cover & Open 1", "All & Open 1"], "cover": False})

    def test_saving_them_removes_the_run(self):
        def photoshop(script: Path):
            fin = json.loads((script.parent / "finish.json").read_text(encoding="utf-8"))
            saved = [t["shots"][0]["save"] for t in fin["templates"]]
            for s in saved:
                Path(s).write_bytes(b"png")
            Path(fin["status"]).write_text(json.dumps({"state": "done", "step": 3, "total": 3, "saved": saved,
                                                       "closed": [t["name"] for t in fin["templates"]]}), encoding="utf-8")
        (self.run / "finish-status.json").write_text(json.dumps({"state": "done"}), encoding="utf-8")  # an old try's
        with mock.patch.object(mockups, "launch", photoshop):
            result = mockups.finish(Job("mockups"), self.run.name, threading.Event())
        self.assertEqual(result["saved"], ["1. Cover 1.png", "Cover & Open 1 (4-5).png", "All & Open 1 (16-17).png"])
        self.assertTrue(result["cleaned"])
        self.assertFalse(self.run.exists())
        self.assertIsNone(mockups.pending())

    def test_a_template_the_owner_closed_keeps_its_copy_and_is_told(self):
        def photoshop(script: Path):
            fin = json.loads((script.parent / "finish.json").read_text(encoding="utf-8"))
            Path(fin["status"]).write_text(json.dumps({"state": "done", "saved": [], "closed": ["1. Cover 1"],
                                                       "problems": [{"kind": "closed", "template": "All & Open 1"}]}),
                                           encoding="utf-8")
        with mock.patch.object(mockups, "launch", photoshop):
            result = mockups.finish(Job("mockups"), self.run.name, threading.Event())
        self.assertFalse(result["cleaned"])
        self.assertEqual(sorted(p.name for p in (self.run / "templates").iterdir()), ["All & Open 1.psd", "Cover & Open 1.psd"])
        self.assertEqual(result["problems"], ["«All & Open 1» уже не відкритий у Photoshop — його не збережено"])

    def test_the_cover_is_named_for_the_owner_and_travels_to_the_second_script(self):
        self.assertEqual(Path(self.work["cover"]), self.run / "Cover.png")
        self.assertIsNone(mockups.finish_plan(self.run)["cover"])        # not there (not copied): nothing to close
        Path(self.work["cover"]).write_bytes(b"png")
        self.assertEqual(mockups.finish_plan(self.run)["cover"], self.work["cover"])
        self.assertIn('"cover": ', mockups.script(self.work))

    def test_finishing_the_page_forgets_the_waiting_run_and_the_book(self):
        books = self.root / "book"
        (books / "session").mkdir(parents=True)
        (books / "session" / "1.png").write_bytes(b"png")
        mockups._books["x" * 16] = {"id": "x" * 16}
        with mock.patch.object(mockups, "BOOKS", books), mock.patch.object(mockups.jobs, "running", lambda name: None):
            mockups.close(self.run.name)
        self.assertIsNone(mockups.pending())                               # «Ваша черга» isn't offered again
        self.assertTrue(self.run.exists())                                  # its copies go the usual way, later
        self.assertEqual(list(books.iterdir()), [])
        self.assertEqual(mockups._books, {})

    def test_finishing_waits_for_a_run_and_refuses_a_strange_name(self):
        with mock.patch.object(mockups.jobs, "running", lambda name: object()), self.assertRaises(ApiError):
            mockups.close(self.run.name)
        with mock.patch.object(mockups.jobs, "running", lambda name: None), self.assertRaises(ApiError):
            mockups.close("../../etc")
        self.assertIsNotNone(mockups.pending())

    def test_with_photoshop_closed_there_is_nothing_to_save(self):
        with mock.patch.object(mockups, "running", lambda: False), self.assertRaises(UserError):
            mockups.finish(Job("mockups"), self.run.name, threading.Event())


class Progress(unittest.TestCase):
    def test_every_template_is_listed_waiting_working_or_done(self):
        work = mockups.plan(book(), PICKS, Path("out"), Path("run"), Path("Трафарети"))
        open1_saves = [s["save"] for s in work["templates"][0]["shots"]]
        view = mockups.progress_view(work, {"step": 5, "saved": open1_saves[:4]}, "work")  # Open 1: fill + 4 pictures
        rows = {r["key"]: r for r in view["rows"]}
        self.assertEqual((rows["open1"]["state"], rows["open1"]["saved"], rows["open1"]["shots"]), ("done", 4, 4))
        self.assertEqual(rows["open2"]["state"], "work")
        self.assertEqual(rows["allOpen"]["state"], "wait")
        self.assertTrue(rows["cover1"]["keepOpen"])
        self.assertEqual(view["saved"], ["2. Open 1 (2-3).png", "2. Open 1 (6-7).png", "2. Open 1 (10-11).png", "2. Open 1 (14-15).png"])
        waiting = mockups.progress_view(work, None, "ask")
        self.assertEqual({r["state"] for r in waiting["rows"]}, {"wait"})
        self.assertEqual(waiting["mode"], "make")


# ---------------------------------------------------------------- the Photoshop script against a pretend Photoshop

HARNESS = r"""
const fs = require('fs');
const TREES = %s;
const CHANGED = %s;  // documents the owner has changed (Photoshop's doc.saved is false for them)
const LOG = { opened: [], closed: [], saves: [], replaced: [] };
function File(p) { this.path = p; this._buf = ''; }
Object.defineProperty(File.prototype, 'exists', { get() { return fs.existsSync(this.path); } });
File.prototype.open = function () { this._buf = ''; return true; };
File.prototype.write = function (s) { this._buf += s; };
File.prototype.close = function () { fs.writeFileSync(this.path, this._buf, 'utf8'); };
const LayerKind = { SMARTOBJECT: 'so', NORMAL: 'normal' };
const SaveOptions = { DONOTSAVECHANGES: 'no' };
const Extension = { LOWERCASE: 'lower' };
const DialogModes = { NO: 'NO', ALL: 'ALL' };
function PNGSaveOptions() {}
function charIDToTypeID(s) { return s; }
function stringIDToTypeID(s) { return s; }
function build(spec, parent) {
  const layer = { name: spec.name, parent: parent, visible: spec.visible !== false, contents: null };
  if (spec.children) { layer.typename = 'LayerSet'; layer.layers = spec.children.map((c) => build(c, layer)); }
  else { layer.typename = 'ArtLayer'; layer.kind = spec.so === false ? LayerKind.NORMAL : LayerKind.SMARTOBJECT; }
  return layer;
}
function walk(layers, path, out) {
  layers.forEach((l) => {
    const p = path.concat([l.name]);
    out[p.join('/')] = { visible: l.visible, contents: l.contents || null };
    if (l.layers) walk(l.layers, p, out);
  });
  return out;
}
function Doc(path) {
  const picture = !TREES[path] && /\.(png|jpe?g|webp)$/i.test(path) && fs.existsSync(path);  // the book's cover
  if (!TREES[path] && !picture) throw new Error('cannot open ' + path);
  this.typename = 'Document';
  this.path = path;
  this.saved = !CHANGED.includes(path);
  this.name = path.replace(/^.*[\\/]/, '');
  this.fullName = { fsName: path.replace(/\//g, '\\') };  // Windows gives the path with backslashes
  this.layers = picture ? [] : TREES[path].map((s) => build(s, this));
  let active = null;
  Object.defineProperty(this, 'activeLayer', {
    get: () => active,
    set: (l) => { active = l; for (let p = l; p && p.typename !== 'Document'; p = p.parent) p.visible = true; },
  });
  // Like Photoshop CC 2019 (seen live): a copy is saved from the ACTIVE document, whichever one is asked.
  this.saveAs = (file, opts, asCopy) => {
    if (!asCopy) throw new Error('saved over the document');
    const shown = app.activeDocument;
    LOG.saves.push({ doc: shown.path, file: file.path, layers: walk(shown.layers, [], {}) });
    fs.writeFileSync(file.path, 'png');
  };
  this.close = (how) => {
    if (how !== 'no') throw new Error('closed with saving');
    LOG.closed.push(this.path);
    app.open_ = app.open_.filter((d) => d !== this);
    if (app.activeDocument === this) app.activeDocument = app.open_[app.open_.length - 1] || null;
  };
}
const app = { displayDialogs: 'ALL', activeDocument: null, docs: [], open_: [] };
app.open = (f) => { const d = new Doc(f.path); LOG.opened.push(f.path); app.docs.push(d); app.open_.push(d); app.activeDocument = d; return d; };
Object.defineProperty(app, 'documents', { get: () => app.open_ });
%s.forEach((p) => app.open(new File(p)));  // documents the owner already has open (the first script's)
function ActionDescriptor() { this.map = {}; }
ActionDescriptor.prototype.putPath = function (k, f) { this.map[k] = f; };
function executeAction(id, d) {
  if (id !== 'placedLayerReplaceContents') throw new Error('unexpected ' + id);
  const layer = app.activeDocument.activeLayer;
  if (!fs.existsSync(d.map['null'].path)) throw new Error('no picture ' + d.map['null'].path);
  layer.contents = d.map['null'].path;
  LOG.replaced.push(layer.name);
}
process.on('exit', () => {
  fs.writeFileSync(%s, JSON.stringify({ log: LOG, dialogs: app.displayDialogs,
    active: app.activeDocument && app.activeDocument.path,
    docs: app.docs.map((d) => ({ path: d.path, layers: walk(d.layers, [], {}) })) }));
});
"""


def trees(work: dict) -> dict:
    """Layer trees shaped like the owner's templates (checked with psd-tools on 23.09.2026), with the
    decoys that matter: vendor B's nested same-named copies and the trailing spaces of All & Open 1."""
    so = lambda name, visible=False: {"name": name, "visible": visible}  # noqa: E731
    view = {"name": "PRESENTATIONS", "children": [{"name": "VIEW_09", "children": [so("COVER_2", True), so("Cover", True)]}]}
    main_a = lambda *names: [view, {"name": "Main", "children": [so(n) for n in names]}]  # noqa: E731
    editable = {"name": "Editable Layers", "children": [{"name": "Design Smart Objects", "children": [
        so("Back cover", True), so("Right Page", True), so("Left Page", True), so("Front Cover", True),
        so("Spine", True), so("Back Cover", True)]}]}
    shapes = {
        "open1": main_a("Right", "Left", "Back Cover", "Rige", "Cover"),
        "open2": main_a("Right", "Left", "Back Cover", "Rige", "Cover"),
        "dedication": main_a("Background", "Deck Color", "Page 1", "Back Cover", "Rige", "Cover"),
        "cover1": main_a("COVER_"),
        "coverOpen": [{"name": "Background", "so": False, "visible": True}, editable,
                      so("Right Page", True), so("Left Page", True), so("Front Cover", True)],
        "allOpen": [{"name": "Layer 0", "so": False, "visible": True}, editable,
                    so("Right "), so("Left "), so("Back Cover"), so("Spine"), so("Front Cover")],
    }
    return {t["file"]: shapes[t["key"]] for t in work["templates"]}


@unittest.skipUnless(shutil.which("node"), "Node.js runs the Photoshop script against a pretend Photoshop")
class PhotoshopScript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out = self.root / "Мокапи"
        self.out.mkdir()
        self.work = mockups.plan(book(), PICKS, self.out, self.root / "run", self.root / "Трафарети")
        for name in self.work["pictures"]:
            path = self.root / "run" / "pictures" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"png")
        Path(self.work["cover"]).write_bytes(b"png")  # the book's cover, copied for the owner (prepare())

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, shapes=None, work=None, open_already=(), changed=()):
        work = work or self.work
        report = self.root / "report.json"
        harness = HARNESS % (json.dumps(shapes or trees(self.work)), json.dumps(list(changed)), json.dumps(list(open_already)),
                             json.dumps(str(report)))
        script = self.root / "run.js"
        script.write_text(harness + mockups.script(work), encoding="utf-8")
        done = subprocess.run(["node", str(script)], capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        status = json.loads(Path(work["status"]).read_text(encoding="utf-8"))
        return status, json.loads(report.read_text(encoding="utf-8"))

    def test_no_slash_inside_a_regex_class_which_photoshop_cannot_read(self):
        # Node reads /^.*[\\/]/ but Photoshop 2019's ExtendScript ends the regex at that "/" and stops the whole
        # script: "Error 25: Expected: )" (the owner's screen, 26.09.2026). The node runs above can't see it.
        literal = re.compile(r"(?<![\w)\]\"'])/(?![/*])((?:\\.|\[(?:\\.|[^\]\\\n])*\]|[^/\\\n\[])+)/[gim]*")
        found = []
        for no, line in enumerate(mockups.SCRIPT.read_text(encoding="ascii").splitlines(), 1):
            code = line.split("//", 1)[0] if line.lstrip().startswith("//") else line
            for m in literal.finditer(code):
                for cls in re.findall(r"\[((?:\\.|[^\]\\])*)\]", m.group(1)):
                    if re.search(r"(?<!\\)/", re.sub(r"\\.", "", cls)):
                        found.append(f"line {no}: {m.group(0)}")
        self.assertEqual(found, [])
        self.assertTrue(literal.search(r'x.replace(/^.*[\\/]/, "")'))           # the check does see the old line
        bad = literal.search(r'x.replace(/^.*[\\/]/, "")').group(1)
        self.assertTrue(any(re.search(r"(?<!\\)/", re.sub(r"\\.", "", c)) for c in re.findall(r"\[((?:\\.|[^\]\\])*)\]", bad)))

    def test_the_script_fills_every_template_and_leaves_three_open(self):
        status, seen = self.run_script()
        self.assertEqual(status["state"], "done", status)
        self.assertEqual(status["problems"], [])
        self.assertEqual(len(status["saved"]), 7)
        self.assertEqual(status["opened"], ["1. Cover 1", "Cover & Open 1", "All & Open 1"])
        self.assertEqual(status["step"], status["total"])
        by_file = {t["file"]: t for t in self.work["templates"]}
        closed = {by_file[p]["key"] for p in seen["log"]["closed"]}
        self.assertEqual(closed, {"open1", "open2", "dedication"})          # saved and closed without saving
        self.assertEqual(by_file[seen["active"]]["key"], "cover1")      # the first one the owner finishes
        self.assertEqual(seen["dialogs"], "ALL")                            # Photoshop's own setting comes back
        # the book's cover opened last, beside them, and left open (the owner, 26.09.2026)
        self.assertEqual(seen["log"]["opened"][-1], self.work["cover"])
        self.assertTrue(status["coverOpened"])
        self.assertNotIn(self.work["cover"], seen["log"]["closed"])
        # Open 1: every picture carries its own spread, with the back, spine and rim already in
        saves = [s for s in seen["log"]["saves"] if by_file[s["doc"]]["key"] == "open1"]
        self.assertEqual([Path(s["file"]).name for s in saves],
                         ["2. Open 1 (2-3).png", "2. Open 1 (6-7).png", "2. Open 1 (10-11).png", "2. Open 1 (14-15).png"])
        second = saves[1]["layers"]
        self.assertTrue(second["Main/Left"]["contents"].endswith("hard-page-6.png"))
        self.assertTrue(second["Main/Right"]["contents"].endswith("hard-page-7.png"))
        self.assertTrue(second["Main/Back Cover"]["contents"].endswith("hard-back.png"))
        self.assertTrue(second["Main/Rige"]["contents"].endswith("hard-spine.png"))
        self.assertTrue(second["Main/Cover"]["contents"].endswith("hard-front.png"))
        self.assertIsNone(second["PRESENTATIONS/VIEW_09/Cover"]["contents"])  # a same-named layer elsewhere
        self.assertFalse(second["Main/Left"]["visible"])                     # hidden copies stay hidden
        self.assertTrue(second["Main"]["visible"])
        docs = {by_file[d["path"]]["key"]: d["layers"] for d in seen["docs"] if d["path"] in by_file}
        # All & Open 1: the top copies (with their trailing spaces), not the nested ones; the front untouched
        all_open = docs["allOpen"]
        self.assertTrue(all_open["Left "]["contents"].endswith("soft-page-16.png"))
        self.assertTrue(all_open["Back Cover"]["contents"].endswith("soft-back.png"))
        self.assertIsNone(all_open["Editable Layers/Design Smart Objects/Back Cover"]["contents"])
        self.assertFalse(all_open["Spine"]["visible"])
        for key, layer in (("allOpen", "Front Cover"), ("coverOpen", "Front Cover"), ("cover1", "Main/COVER_")):
            with self.subTest(template=key):
                self.assertIsNone(docs[key][layer]["contents"])          # the owner's front cover
        self.assertTrue(docs["coverOpen"]["Left Page"]["visible"])       # a visible copy stays visible

    def test_a_missing_layer_is_told_and_the_rest_goes_on(self):
        shapes = trees(self.work)
        open2 = next(t["file"] for t in self.work["templates"] if t["key"] == "open2")
        shapes[open2][1]["children"] = [c for c in shapes[open2][1]["children"] if c["name"] != "Left"]
        status, seen = self.run_script(shapes)
        self.assertEqual(status["state"], "done")
        self.assertEqual(len(status["saved"]), 5)                           # Open 2's two are the ones missing
        self.assertEqual(status["problems"], [{"kind": "layer", "layer": "Main/Left", "template": "3. Open 2"}] * 2)
        self.assertEqual(mockups._problem_text(status["problems"][0]), "У «3. Open 2» немає смарт-об'єкта «Main/Left»")

    def test_a_cover_that_cannot_be_opened_is_told_and_the_pictures_stand(self):
        Path(self.work["cover"]).unlink()
        status, seen = self.run_script()
        self.assertEqual(status["state"], "done")
        self.assertEqual(len(status["saved"]), 7)
        self.assertNotIn("coverOpened", status)
        self.assertEqual([p["template"] for p in status["problems"]], ["Cover"])
        self.assertTrue(mockups._problem_text(status["problems"][0]).startswith("«Cover» не відкрився"))

    def test_a_stop_mark_ends_the_run_before_anything_opens(self):
        Path(self.work["cancel"]).write_text("stop", encoding="utf-8")
        status, seen = self.run_script()
        self.assertEqual(status["state"], "cancelled")
        self.assertEqual(seen["log"]["opened"], [])

    def test_the_second_script_saves_the_open_ones_and_closes_them(self):
        """«Зберегти відкриті»: the documents the first script left open are found by their copy's path, saved as
        PNG from themselves and closed without saving the copy; one the owner closed is told, not guessed."""
        run = self.root / "run"
        core.write_json(run / "job.json", self.work, backup=False)
        kept = [t for t in self.work["templates"] if t["keepOpen"]]
        for t in kept:
            Path(t["file"]).parent.mkdir(parents=True, exist_ok=True)
            Path(t["file"]).write_bytes(b"psd")
        fin = mockups.finish_plan(run)
        still_open = [t["file"] for t in kept if t["key"] != "allOpen"]   # the owner closed All & Open 1 himself
        status, seen = self.run_script(work=fin, open_already=still_open)
        self.assertEqual(status["state"], "done", status)
        self.assertEqual([Path(p).name for p in status["saved"]], ["1. Cover 1.png", "Cover & Open 1 (4-5).png"])
        self.assertEqual(status["closed"], ["1. Cover 1", "Cover & Open 1"])
        self.assertEqual(status["problems"], [{"kind": "closed", "template": "All & Open 1"}])
        self.assertEqual(seen["log"]["opened"], still_open)                    # it opened nothing itself
        self.assertEqual(seen["log"]["closed"], still_open)
        self.assertEqual([s["doc"] for s in seen["log"]["saves"]], still_open)  # each picture from its own document
        self.assertEqual(seen["dialogs"], "ALL")

    def test_the_second_script_closes_the_cover_only_when_the_owner_has_not_changed_it(self):
        run = self.root / "run"
        core.write_json(run / "job.json", self.work, backup=False)
        kept = [t for t in self.work["templates"] if t["keepOpen"]]
        for t in kept:
            Path(t["file"]).parent.mkdir(parents=True, exist_ok=True)
            Path(t["file"]).write_bytes(b"psd")
        fin = mockups.finish_plan(run)
        self.assertEqual(fin["cover"], self.work["cover"])
        opened = [t["file"] for t in kept] + [self.work["cover"]]
        status, seen = self.run_script(work=fin, open_already=opened)
        self.assertTrue(status["coverClosed"])
        self.assertEqual(seen["log"]["closed"][-1], self.work["cover"])
        status, seen = self.run_script(work=fin, open_already=opened, changed=[self.work["cover"]])
        self.assertNotIn("coverClosed", status)                                # his changes stay open in Photoshop
        self.assertNotIn(self.work["cover"], seen["log"]["closed"])
        self.assertEqual(len(status["saved"]), 3)
