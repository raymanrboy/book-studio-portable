"""The Workshop (the Listings mode) — the book console moved in: the books the agents write (made-up ones,
tools/sample_books.py), their path strip, their rows, a picture into its row (cut, flipped, two pages), the cover's two
stages, the generation mode catching downloads, passing a book to the library. All in the sandbox: the books, the
Downloads, the clipboard and the Recycle Bin are files in the tests' own folder."""
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw

from tests import __init__  # noqa: F401  (sets a temporary data folder and the sandbox)
from studio import core, library
from studio.jobs import jobs
from studio.server import ApiError
from studio.workshop import books, generate, pictures, routes, rows
from studio.workshop.rows import template_layout

TOOLS = Path(__file__).resolve().parents[1] / "tools"
_spec = importlib.util.spec_from_file_location("sample_books", TOOLS / "sample_books.py")
sample_books = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sample_books)

H, S, NEW = "40.moonlit-garden-lullaby", "41.little-lamb-prayers", "42.new-book"
LISTING = "4100000961"   # made-up listing numbers of their own: other tests' library books share the folder
PROMPT = {"task": "one wide watercolor illustration", "aspect_ratio": "2:1"}


def spread_png(path: Path, size=(2048, 1024)) -> Path:
    """Left half red, right half blue — so a mirror shows."""
    im = Image.new("RGB", size, (30, 60, 220))
    ImageDraw.Draw(im).rectangle((0, 0, size[0] // 2 - 1, size[1]), fill=(220, 40, 40))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "PNG")
    return path


def fenced(objs):
    return "".join(f"```json\n{json.dumps(o, indent=2)}\n```\n" for o in objs)


def request(book_id: str = "", body: dict | None = None, **params) -> SimpleNamespace:
    return SimpleNamespace(groups=[book_id], json=body or {}, param=lambda name: params.get(name))


def states(book_id):
    return {s["key"]: s["state"] for s in books.detail(book_id)["steps"]}


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = sample_books.make_books(core.WORKSHOP_BOOKS)
        self.tmp = core.data_path("workshop-test")
        for folder in (self.tmp, generate.downloads_folder(), core.data_path("clipboard"),
                       core.data_path("recycle-bin"), core.data_path("saved")):
            shutil.rmtree(folder, ignore_errors=True)
        self.tmp.mkdir(parents=True)
        self.downloads = generate.downloads_folder()
        self.downloads.mkdir(parents=True)
        self.made: list[str] = []

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        shutil.rmtree(self.tmp, ignore_errors=True)
        for book_id in self.made:
            shutil.rmtree(library._book_dir(book_id), ignore_errors=True)

    def pixel(self, book, name, xy=(5, 5), variant=None):
        folder = self.dir / book / "pictures" / ("variants/" + variant if variant else "")
        with Image.open(folder / name) as im:
            return im.convert("RGB").getpixel(xy)

    def clip(self):
        txt, png = core.data_path("clipboard", "clipboard.txt"), core.data_path("clipboard", "clipboard.png")
        return txt.read_text(encoding="utf-8") if txt.exists() else ("<image>" if png.exists() else None)


class TheSandbox(Base):
    def test_the_tests_never_reach_the_owners_books_clipboard_or_downloads(self):
        data = core.DATA_DIR
        self.assertTrue(core.SANDBOX)
        for path in (core.WORKSHOP_BOOKS, generate.downloads_folder()):
            self.assertTrue(path.resolve().is_relative_to(data), path)
        self.assertNotEqual(core.WORKSHOP_BOOKS, core.PIPELINE_DIR / "books")
        say = books.open_agent(S)                     # no Antigravity window: only the words, in the fake clipboard
        self.assertEqual(say, f"Продовжуємо книгу books/{S}")
        self.assertEqual(self.clip(), say)
        self.assertEqual(books.open_agent(None), "нова книга")


class TheBookList(Base):
    def test_books_come_in_number_order_with_their_titles(self):
        got = [(b["number"], b["title"]) for b in books.all_books()]
        self.assertEqual(got, [(40, "Moonlit garden lullaby"), (41, "Little lamb prayers"), (42, "New book")])

    def test_the_cover_title_comes_from_the_book_text(self):
        self.assertEqual(books.summary(H)["coverTitle"], "{Name}'s Moonlit Garden")

    def test_the_thumbnail_is_the_cover_else_a_spread_else_the_hero(self):
        self.assertEqual(books.summary(H)["thumb"]["name"], "canonical.png")
        self.assertEqual(books.summary(S)["thumb"], {"area": "pictures", "name": "2.png", "kind": "page"})
        self.assertIsNone(books.summary(NEW)["thumb"])

    def test_a_folder_starting_with_a_dot_or_underscore_is_not_a_book(self):
        (self.dir / ".trash").mkdir()
        (self.dir / "_old").mkdir()
        self.assertEqual(len(books.all_books()), 3)

    def test_the_list_and_a_book_come_with_what_they_were_drawn_from(self):
        listed = routes._list(request())
        self.assertEqual(len(listed["books"]), 3)
        self.assertIn("-", listed["sig"])
        self.assertIn("active", listed["gen"])
        one = routes._get(request(S))
        self.assertEqual(one["book"]["id"], S)
        self.assertEqual(one["sig"], routes._sig(request(book=S))["sig"])


class ThePathStrip(Base):
    def test_steps_are_ticked_by_the_files_that_exist(self):
        s = states(H)
        self.assertEqual([s[k] for k in ("formula", "hero", "story", "text", "prompts", "pictures", "cover", "library")],
                         ["done", "done", "done", "done", "todo", "todo", "todo", "todo"])

    def test_a_new_file_ticks_its_step_at_once(self):
        agent = self.dir / H / "agent"
        (agent / "spread-prompts-json.md").write_text("```json\n{}\n```\n", encoding="utf-8")
        self.assertEqual(states(H)["prompts"], "part")
        (agent / "endpage-prompts-json.md").write_text("```json\n{}\n```\n", encoding="utf-8")
        self.assertEqual(states(H)["prompts"], "done")

    def test_a_tier_s_book_skips_the_hero(self):
        self.assertEqual(states(S)["hero"], "skip")

    def test_a_hero_prompt_without_the_picture_is_started_not_done(self):
        (self.dir / H / "agent" / "canonical.png").unlink()
        self.assertEqual(states(H)["hero"], "part")

    def test_pictures_count_rows_whose_every_page_is_there(self):
        step = next(s for s in books.detail(S)["steps"] if s["key"] == "pictures")
        self.assertEqual((step["count"], step["total"], step["state"]), (5, 16, "part"))
        (self.dir / S / "pictures" / "10.png").write_bytes(b"x")  # half of 10–11
        step = next(s for s in books.detail(S)["steps"] if s["key"] == "pictures")
        self.assertEqual(step["count"], 5)

    def test_the_next_step_is_the_first_not_done(self):
        self.assertEqual([s["key"] for s in books.detail(S)["steps"] if s.get("next")], ["pictures"])
        self.assertEqual([s["key"] for s in books.detail(NEW)["steps"] if s.get("next")], ["formula"])

    def test_canva_and_the_mockups_are_ticked_by_hand_in_book_json_only(self):
        self.assertEqual(states(S)["canva"], "done")
        books.set_mark(NEW, "mockups", True)
        self.assertEqual(states(NEW)["mockups"], "done")
        books.set_mark(NEW, "mockups", False)
        self.assertEqual(states(NEW)["mockups"], "todo")
        self.assertEqual(json.loads((self.dir / NEW / "book.json").read_text(encoding="utf-8")), {"marks": {}})
        self.assertEqual(list((self.dir / NEW / "agent").iterdir()), [])
        for step in ("formula", "library"):          # a file's step, and the library's — never by hand
            with self.assertRaises(ApiError, msg=step):
                books.set_mark(NEW, step, True)


class OnlyInsideTheBook(Base):
    def test_a_book_outside_the_books_folder_is_refused(self):
        for bad in ("..", "../workshop-test", f"{H}/agent", "", ".trash"):
            with self.assertRaises(ApiError, msg=bad):
                books.book_path(bad)

    def test_only_the_agents_text_files_are_read(self):
        self.assertIn("Tier: H", books.agent_text(H, "formula.md"))
        for bad in ("../book.json", "canonical.png", "nothing.md"):
            with self.assertRaises(ApiError, msg=bad):
                books.agent_text(H, bad)

    def test_only_pictures_that_are_there(self):
        self.assertTrue(books.media_file(S, "pictures", "1.png").is_file())
        for area, name in (("pictures", "31.png"), ("agent", "formula.md"), ("..", "book.json")):
            with self.assertRaises(ApiError, msg=name):
                books.media_file(S, area, name)

    def test_only_the_books_own_folders_and_files_open_in_windows(self):
        books.open_in_windows(S, "pictures", "1.png")   # the sandbox opens nothing, but checks the same
        books.open_in_windows(H, "agent", "formula.md")
        for what, name in (("pictures", "../book.json"), ("agent", "nothing.md"), ("folder", "book.json"), ("..", "")):
            with self.assertRaises(ApiError, msg=f"{what}/{name}"):
                books.open_in_windows(S, what, name)


class TheSignature(Base):
    def test_it_changes_when_a_file_appears_or_changes_and_not_otherwise(self):
        first = books.signature()
        self.assertEqual(first, books.signature())
        agent = self.dir / NEW / "agent"
        (agent / "formula.md").write_text("Tier: S", encoding="utf-8")
        second = books.signature()
        self.assertNotEqual(first, second)
        (agent / "formula.md").write_text("Tier: H, longer", encoding="utf-8")
        self.assertNotEqual(second, books.signature())

    def test_one_books_signature_minds_only_that_book(self):
        mine = books.signature(S)
        (self.dir / NEW / "agent" / "formula.md").write_text("Tier: S", encoding="utf-8")
        self.assertEqual(mine, books.signature(S))
        (self.dir / S / "agent" / "formula.md").write_text("Tier: S, changed", encoding="utf-8")
        self.assertNotEqual(mine, books.signature(S))


class TheRows(Base):
    def setUp(self):
        super().setUp()
        self.agent = self.dir / H / "agent"

    def test_seventeen_rows_in_the_books_order(self):
        labels = [r["label"] for r in books.detail(H)["rows"]]
        self.assertEqual(len(labels), 17)
        self.assertEqual(labels[:2], ["Сторінка 1 · присвята", "Розворот 2–3"])
        self.assertEqual(labels[-3:], ["Розворот 28–29", "Сторінка 30 · післяслово", "Обкладинка"])  # the cover last

    def test_the_mirrored_spreads_are_those_whose_left_page_divides_by_4(self):
        got = [r["label"] for r in books.detail(H)["rows"] if r.get("mirrored")]
        self.assertEqual(got, [f"Розворот {p}–{p + 1}" for p in (4, 8, 12, 16, 20, 24, 28)])

    def test_texts_come_from_the_headings_of_book_text(self):
        (self.agent / "book-text.md").write_text(
            "## Cover — Title\n{Name}'s Garden\n\n## Spread 01 — Dedication\nFor [Name].\n\n"
            "## Spread 02 — Seed\nA seed,\n\na hand.\n---\n\n## Afterword — Wishes\nGood night.\n\n"
            "## Text Critic Report\nAll fine.\n", encoding="utf-8")
        by = {r["key"]: r["text"] for r in books.detail(H)["rows"]}
        self.assertEqual(by["cover"], "{Name}'s Garden")
        self.assertEqual(by["page1"], "For {Name}.")
        self.assertEqual(by["spread2"], "A seed,\n\na hand.")
        self.assertEqual(by["page30"], "Good night.")  # the critic's report is not the afterword's text
        self.assertEqual(by["spread3"], "")

    def test_prompts_go_in_order_and_whole(self):
        spreads = [dict(PROMPT, scene=n) for n in range(2, 16)]
        (self.agent / "spread-prompts-json.md").write_text(fenced(spreads), encoding="utf-8")
        (self.agent / "endpage-prompts-json.md").write_text(fenced([dict(PROMPT, end="dedication"), dict(PROMPT, end="afterword")]), encoding="utf-8")
        (self.agent / "cover-prompts-json.md").write_text(fenced([dict(PROMPT, cover=True)]), encoding="utf-8")
        d = books.detail(H)
        by = {r["key"]: r["prompt"] for r in d["rows"]}
        self.assertEqual(json.loads(by["spread2"])["scene"], 2)
        self.assertEqual(json.loads(by["spread15"])["scene"], 15)
        self.assertEqual(json.loads(by["page1"])["end"], "dedication")
        self.assertEqual(json.loads(by["page30"])["end"], "afterword")
        self.assertTrue(json.loads(by["cover"])["cover"])
        self.assertEqual(by["spread2"], json.dumps(spreads[0], indent=2, ensure_ascii=False))  # what the generator gets
        self.assertEqual(d["counts"]["prompts"], 17)
        self.assertEqual(d["notes"], [])

    def test_a_short_or_broken_file_is_named_and_what_parses_still_shows(self):
        (self.agent / "spread-prompts-json.md").write_text(fenced([PROMPT] * 3) + "```json\n{ broken\n```\n", encoding="utf-8")
        d = books.detail(H)
        self.assertEqual(sum(1 for r in d["rows"] if r["prompt"]), 3)
        self.assertTrue(any("блок 4: JSON не читається" in n for n in d["notes"]), d["notes"])
        self.assertTrue(any("3 промпти замість 14" in n for n in d["notes"]), d["notes"])

    def test_a_row_shows_its_pictures_only_when_every_page_is_there(self):
        d = books.detail(S)
        by = {r["key"]: r["pictures"] for r in d["rows"]}
        self.assertEqual(by["page1"], ["1.png"])
        self.assertEqual(by["spread2"], ["2.png", "3.png"])
        self.assertEqual(by["spread6"], [])
        self.assertEqual(d["counts"]["pictures"], 5)


class TheBookCheck(Base):
    def test_no_prompt_files_no_check(self):
        self.assertIsNone(books.detail(H)["check"])
        self.assertNotIn("check", next(s for s in books.detail(H)["steps"] if s["key"] == "prompts"))

    def test_the_check_runs_the_old_rules_and_shows_on_the_strip(self):
        d = books.detail(S)
        self.assertFalse(d["check"]["go"])
        self.assertIn("endpage-prompts-json.md: expected 2 square end-image prompts, found 1", d["check"]["fails"])
        step = next(s for s in d["steps"] if s["key"] == "prompts")
        self.assertEqual(step["check"], {"go": False, "fails": len(d["check"]["fails"]), "warns": len(d["check"]["warns"])})

    def test_it_runs_again_only_when_an_agents_file_changed(self):
        path = books.book_path(S)
        first = rows.book_check(path)
        self.assertIs(first, rows.book_check(path))  # the same result, not run again
        (path / "agent" / "book-text.md").write_text("## Spread 15 — Finale\nThe end.\n", encoding="utf-8")
        self.assertIsNot(first, rows.book_check(path))

    def test_the_agents_run_the_same_check_from_the_pipelines_folder(self):
        script = core.PIPELINE_DIR / "check_book.py"
        out = subprocess.run([sys.executable, "-B", str(script), str(self.dir / S)], capture_output=True, text=True,
                             encoding="utf-8", cwd=str(core.PIPELINE_DIR))
        self.assertIn("NOT READY", out.stdout)
        self.assertEqual(out.returncode, len(books.detail(S)["check"]["fails"]))


class APictureIntoItsRow(Base):
    def test_a_plain_spread_becomes_its_two_pages(self):
        r = pictures.place(H, "spread2", spread_png(self.tmp / "a.png"), "a.png")
        self.assertEqual(r["note"], "Розворот 2–3: дві сторінки готові")
        self.assertEqual(self.pixel(H, "2.png"), (220, 40, 40))
        self.assertEqual(self.pixel(H, "3.png"), (30, 60, 220))
        with Image.open(self.dir / H / "pictures" / "2.png") as im:
            self.assertEqual(im.size, (1024, 1024))

    def test_the_flippers_spreads_are_mirrored_and_a_narrow_one_loses_top_and_bottom(self):
        r = pictures.place(H, "spread3", spread_png(self.tmp / "a.png", (1792, 1024)), "a.png")
        self.assertTrue(r["mirrored"])
        self.assertEqual(r["cut"], "top-bottom")
        self.assertEqual(self.pixel(H, "4.png"), (30, 60, 220))  # the blue came to the left
        with Image.open(self.dir / H / "pictures" / "4.png") as im:
            self.assertEqual(im.size, (896, 896))
        marks = books.state(self.dir / H)["rows"]["spread3"]
        self.assertEqual((marks["mirrored"], marks["source"], marks["from"]), (True, [1792, 1024], "a.png"))

    def test_flip_twice_gives_back_the_same_pages(self):
        pictures.place(H, "spread2", spread_png(self.tmp / "a.png"), "a.png")
        before = (self.dir / H / "pictures" / "2.png").read_bytes()
        self.assertTrue(pictures.flip(H, "spread2")["mirrored"])
        self.assertEqual(self.pixel(H, "2.png"), (30, 60, 220))
        self.assertFalse(pictures.flip(H, "spread2")["mirrored"])
        with Image.open(self.dir / H / "pictures" / "2.png") as im, Image.open(io.BytesIO(before)) as old:
            self.assertEqual(im.tobytes(), old.tobytes())

    def test_page_1_is_cut_to_a_square(self):
        r = pictures.place(H, "page1", spread_png(self.tmp / "p.png", (1200, 1000)), "p.png")
        self.assertIn("обрізано з боків до квадрата", r["note"])
        with Image.open(self.dir / H / "pictures" / "1.png") as im:
            self.assertEqual(im.size, (1000, 1000))

    def test_the_picture_itself_is_kept_in_originals_named_by_its_row(self):
        pictures.place(H, "spread3", spread_png(self.tmp / "Generated Image.jpeg", (2048, 1024)), "Generated Image.jpeg")
        self.assertEqual(sorted(p.name for p in (self.dir / H / "originals").iterdir()), ["spread-04-05.jpg"])
        self.assertTrue((self.tmp / "Generated Image.jpeg").exists())  # a dropped file is copied, not taken
        self.assertEqual(books.detail(H)["rows"][2]["original"], "spread-04-05.jpg")

    def test_the_printers_template_in_numbers(self):
        # Gemini's cover 5824×2880 on the template 17.90″×9.50″ (finished 16.40″×8.00″): its width is the finished
        # width — 266 px of margin at the sides, 247 at the top and the bottom (worked out with the owner, 2026-09-26)
        self.assertEqual(template_layout(5824, 2880), {"canvas": [6357, 3374], "art": [266, 247, 5824, 2880], "ppi": 355.12})

    def test_the_cover_in_two_stages_the_picture_then_its_margins(self):
        pictures.place(H, "cover", spread_png(self.tmp / "c.png", (2000, 1000)), "c.png")
        self.assertFalse((self.dir / H / "pictures" / "Cover.png").exists())  # not the cover for Canva yet
        c = books.detail(H)["cover"]
        self.assertEqual((c["art"], c["expanded"], c["final"]), ("cover-art.png", "cover-expanded.png", None))
        with Image.open(self.dir / H / "originals" / "cover-expanded.png") as im:
            self.assertEqual(im.size, (2183, 1159))                                # the template's proportions
            self.assertEqual(im.getpixel((5, 5)), (255, 255, 255))                 # a white margin
            self.assertEqual(im.getpixel((95, 85)), (220, 40, 40))                 # the picture itself, untouched
        self.assertEqual(c["layout"]["art"], [91, 79, 2000, 1000])
        self.assertIn('"canvas": "2183 × 1159 px', c["outpaint"])
        pictures.place(H, "cover-wrap", spread_png(self.tmp / "w.png", (2200, 1200)), "w.png")
        c = books.detail(H)["cover"]
        self.assertEqual(c["final"], "Cover.png")
        with Image.open(self.dir / H / "pictures" / "Cover.png") as im:          # ready for the printer
            self.assertEqual(im.size, (5370, 2850))
            self.assertEqual(round(im.info["dpi"][0]), 300)
        self.assertEqual(states(H)["cover"], "done")

    def test_the_cover_without_margins(self):
        pictures.place(H, "cover", spread_png(self.tmp / "c.png", (2000, 1000)), "c.png")
        pictures.skip_margins(H)
        with Image.open(self.dir / H / "pictures" / "Cover.png") as im:
            self.assertEqual(im.size, (2000, 1000))
        self.assertTrue(books.detail(H)["cover"]["skipped"])

    def test_deleting_a_book_takes_its_whole_folder_into_the_recycle_bin(self):
        pictures.place(H, "spread2", spread_png(self.tmp / "a.png"), "a.png")
        r = routes._delete(request(H))
        self.assertEqual((r["number"], r["title"]), (40, "Moonlit garden lullaby"))
        self.assertFalse((self.dir / H).exists())
        self.assertNotIn(H, [b["id"] for b in books.all_books()])
        kept = list(core.data_path("recycle-bin").iterdir())                 # the sandbox's Recycle Bin
        self.assertEqual(len(kept), 1)
        self.assertTrue((kept[0] / "pictures" / "2.png").exists())

    def test_save_as_copies_a_picture_and_remembers_the_folder(self):
        pictures.place(H, "spread2", spread_png(self.tmp / "a.png"), "a.png")
        r = routes._save_as(request(H, {"area": "pictures", "name": "2.png"}))
        self.assertTrue(r["saved"])
        self.assertEqual(r["name"], f"{H} — 2.png")
        self.assertTrue(core.data_path("saved", r["name"]).is_file())
        self.assertEqual(core.settings.section("workshop")["saveDir"], str(core.data_path("saved")))

    def test_what_a_picture_replaces_or_a_removal_takes_goes_to_replaced_not_away(self):
        pictures.place(H, "spread2", spread_png(self.tmp / "a.png"), "a.png")
        pictures.place(H, "spread2", spread_png(self.tmp / "b.png"), "b.png")
        kept = sorted(p.name.split("-", 2)[2] for p in (self.dir / H / ".replaced").iterdir())
        self.assertEqual(kept, ["originals__spread-02-03.png", "pictures__2.png", "pictures__3.png"])
        pictures.remove(H, "spread2")
        self.assertFalse((self.dir / H / "pictures" / "2.png").exists())
        self.assertEqual(len(list((self.dir / H / ".replaced").iterdir())), 6)
        self.assertNotIn("spread2", books.state(self.dir / H).get("rows", {}))

    def test_not_a_picture_is_refused_and_nothing_is_moved(self):
        bad = self.tmp / "x.png"
        bad.write_bytes(b"not a picture")
        with self.assertRaises(ApiError):
            pictures.place(H, "spread2", bad, "x.png", take=True)
        self.assertTrue(bad.exists())

    def test_the_hero_goes_into_agent_and_the_old_one_is_kept(self):
        pictures.place(H, "hero", spread_png(self.tmp / "h.png", (600, 800)), "h.png")
        with Image.open(self.dir / H / "agent" / "canonical.png") as im:
            self.assertEqual(im.size, (600, 800))
        self.assertTrue(any("agent__canonical.png" in p.name for p in (self.dir / H / ".replaced").iterdir()))

    def test_a_dropped_cover_goes_on_to_wait_for_its_margins(self):
        tmp = spread_png(self.tmp / "c.png", (2000, 1000))
        session = generate.Session(watch=False)
        generate._session = session
        try:
            req = SimpleNamespace(groups=[H], param=lambda n: {"key": "cover", "name": "c.png"}.get(n),
                                  body_to_file=lambda target, limit: (target.parent.mkdir(parents=True, exist_ok=True), target.write_bytes(tmp.read_bytes())))
            self.assertEqual(routes._place(req)["key"], "cover")
            self.assertEqual(session.status()["active"]["key"], "cover-wrap")
        finally:
            generate._session = None


class CatchingDownloads(Base):
    def setUp(self):
        super().setUp()
        self.s = generate.Session(watch=False)

    def look(self):
        self.s.look()  # the first look sees the size, the second takes the picture
        self.s.look()

    def test_the_whole_book_row_after_row(self):
        (self.downloads / "old.png").write_bytes(b"there before")
        st = self.s.start(S, None, series=True)
        self.assertEqual(st["active"]["key"], "spread6")          # 2–3 … 8–9 already have pictures
        self.assertEqual(st["active"]["queue"], 9)                 # 12–13 … 28–29; page 30 has no prompt yet
        self.assertIn('"aspect_ratio": "2:1"', self.clip())        # the row's prompt is in the clipboard
        spread_png(self.downloads / "Gemini_1.png.crdownload")    # still downloading
        self.look()
        self.assertEqual(self.s.status()["active"]["key"], "spread6")
        (self.downloads / "Gemini_1.png.crdownload").replace(self.downloads / "Gemini_1.png")
        self.look()
        self.assertTrue((self.dir / S / "pictures" / "10.png").exists())
        self.assertFalse((self.downloads / "Gemini_1.png").exists())  # moved out of Downloads …
        self.assertTrue((self.dir / S / "originals" / "spread-10-11.png").exists())  # … into the book, renamed
        self.assertTrue((self.downloads / "old.png").exists())       # what was there before stays
        st = self.s.status()
        self.assertEqual(st["active"]["key"], "spread7")           # the next row, its prompt already in the clipboard
        self.assertEqual(st["last"]["note"], "Розворот 10–11: дві сторінки готові")
        self.assertEqual((st["active"]["step"], st["active"]["of"]), (2, 10))

    def test_only_pictures_count_and_stop_stops(self):
        self.s.start(S, "spread6")
        (self.downloads / "notes.txt").write_text("x")
        self.look()
        self.assertEqual(self.s.status()["active"]["key"], "spread6")
        spread_png(self.downloads / "g.png")
        self.look()
        self.assertIsNone(self.s.status()["active"])  # one row asked — one row done
        self.s.start(S, "spread7")
        self.s.stop()
        spread_png(self.downloads / "h.png")
        self.look()
        self.assertFalse((self.dir / S / "pictures" / "12.png").exists())

    def test_a_deleted_book_stops_only_its_own_wait(self):
        self.s.start(S, "spread6")
        self.s.stop(H)
        self.assertEqual(self.s.status()["active"]["book"], S)
        self.s.stop(S)
        self.assertIsNone(self.s.status()["active"])

    def test_a_row_without_a_prompt_cant_start(self):
        with self.assertRaises(ApiError):
            self.s.start(S, "page30")

    def test_the_cover_goes_on_to_its_margins_by_itself(self):
        st = self.s.start(S, "cover")
        self.assertEqual(st["active"]["items"], ["промпт"])
        self.assertIn("main focus on the right", self.clip())
        spread_png(self.downloads / "cover.png", (2000, 1000))
        self.look()
        st = self.s.status()
        self.assertEqual(st["active"]["key"], "cover-wrap")                 # the second stage, waiting already
        self.assertEqual(st["active"]["items"], ["обкладинка з полями", "промпт аутпейнту"])
        self.assertEqual(self.clip(), "<image>")                             # the picture with its margins
        self.assertTrue(st["f8"])
        self.s.next_item()
        self.assertIn("outpaint", self.clip())
        self.assertFalse(self.s.status()["f8"])                              # F8 is given back after the last thing
        spread_png(self.downloads / "wrap.png", (2160, 1160))
        self.look()
        self.assertIsNone(self.s.status()["active"])
        self.assertTrue((self.dir / S / "pictures" / "Cover.png").exists())
        self.assertEqual(sorted(p.name for p in (self.dir / S / "originals").iterdir()),
                         ["cover-art.png", "cover-expanded.png", "cover-wrap.png"])

    def test_a_hero_variant_needs_the_base_spread_and_its_hero(self):
        with self.assertRaises(ApiError):
            self.s.start(H, "spread3", "G2_brunette")        # no base spread 4–5 yet
        pictures.place(H, "spread3", spread_png(self.tmp / "base.png"), "base.png")
        with self.assertRaises(ApiError):
            self.s.start(H, "spread3", "G2_brunette")        # no hero.png of the variant yet
        st = self.s.start(H, "hero", "G2_brunette")
        self.assertEqual(st["active"]["items"], ["основний герой", "промпт героя"])
        Image.new("RGB", (600, 800), (90, 70, 50)).save(self.downloads / "hero.png")
        self.look()
        self.assertTrue((self.dir / H / "agent" / "variants" / "G2_brunette" / "hero.png").exists())
        st = self.s.start(H, "spread3", "G2_brunette")
        self.assertEqual(st["active"]["items"], ["основний розворот", "герой варіанта", "промпт"])
        with Image.open(core.data_path("clipboard", "clipboard.png")) as im:   # the base spread as Gemini made it
            self.assertEqual(im.convert("RGB").getpixel((5, 5)), (220, 40, 40))
        self.s.next_item()
        self.s.next_item()
        spread_png(self.downloads / "swap.png")
        self.look()
        self.assertTrue((self.dir / H / "pictures" / "variants" / "G2_brunette" / "4.png").exists())
        v = books.detail(H)["variants"][0]
        self.assertEqual((v["done"], len(v["rows"])), (1, 2))


class PassingToTheLibrary(Base):
    def wait(self, started: dict) -> dict:
        job = jobs.get(started["jobId"])
        for _ in range(600):
            if job.status != "running":
                break
            time.sleep(0.05)
        self.assertEqual(job.status, "done", job.error)
        self.made.append(job.result["book"]["id"])
        return job.result

    def test_the_library_gets_a_book_made_of_its_pages_texts_and_listing(self):
        pictures.place(S, "cover", spread_png(self.tmp / "c.png", (2000, 1000)), "c.png")
        pictures.skip_margins(S)
        res = self.wait(routes._to_library(request(S, {"listingRef": f"https://www.etsy.com/listing/{LISTING}/x"})))
        self.assertEqual((res["pages"], res["errors"]), (10, []))                # the cover and 9 pages
        book = library.load(res["book"]["id"])
        self.assertEqual((book["title"], book["listing"]["id"], book["workshop"]), ("Little lamb prayers", LISTING, S))
        self.assertTrue(book["cover"] and book["slots"]["page1"]["image"])
        self.assertTrue(book["slots"]["spread2"]["left"] and book["slots"]["spread2"]["right"])
        self.assertEqual(book["text"]["page1"], "For {Name}, with love from {Gifter}.")
        self.assertIn(book["id"], {b["id"] for b in library.all_books()})         # orders find it by its listing
        self.assertTrue((self.dir / S / "pictures" / "1.png").exists())           # the Workshop's folder stays
        self.assertEqual(states(S)["library"], "done")
        self.assertEqual(books.summary(S)["library"]["id"], book["id"])
        with self.assertRaises(ApiError) as again:                               # once is enough
            routes._to_library(request(S, {"listingRef": "4100000962"}))
        self.assertEqual(again.exception.extra["bookId"], book["id"])

    def test_a_listing_another_book_has_is_refused_and_nothing_changes(self):
        taken = library.create_book({"id": "4100000963"}, "Already on sale")
        self.made.append(taken["id"])
        with self.assertRaises(ApiError) as refused:
            routes._to_library(request(NEW, {"listing": {"id": "4100000963"}}))
        self.assertEqual((refused.exception.status, refused.exception.extra["bookId"]), (409, taken["id"]))
        self.assertEqual(states(NEW)["library"], "todo")

    def test_a_library_book_gone_to_the_trash_unticks_the_step(self):
        res = self.wait(routes._to_library(request(NEW, {"listingRef": "4100000964"})))
        self.assertEqual(states(NEW)["library"], "done")
        shutil.rmtree(library._book_dir(res["book"]["id"]))
        self.assertEqual(states(NEW)["library"], "todo")


if __name__ == "__main__":
    unittest.main()
