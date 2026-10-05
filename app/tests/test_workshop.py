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
import unittest.mock
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw

from tests import __init__  # noqa: F401  (sets a temporary data folder and the sandbox)
from studio import core, library, library_files
from studio.jobs import jobs
from studio.server import ApiError
from studio.workshop import books, generate, pictures, routes, rows, upscale
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
        # The upscaling's queue is turned by hand (test_upscale.py): a picture placed here stays as it was cut
        upscale._upscaler = upscale.Upscaler(run=False)
        upscale.FAKE_DELAY = 0

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
        self.assertEqual(self.clip(), say)
        self.assertTrue(say.startswith(f"Продовжуємо книгу {core.WORKSHOP_BOOKS / S} "), say)
        self.assertIn(str(core.PIPELINE_DIR / "AGENTS.md"), say)

    def test_the_agent_is_told_the_full_paths_whatever_project_antigravity_has(self):
        # Antigravity 2 ignores the folder it is started with: the words carry the rules and the books' folder
        say = books.open_agent(None)
        self.assertTrue(say.startswith("Нова книга."), say)
        self.assertIn(str(core.PIPELINE_DIR / "AGENTS.md"), say)
        self.assertTrue(say.endswith(str(core.WORKSHOP_BOOKS)), say)
        self.assertNotIn("Book Console", say)


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

    def test_a_variants_picture_opens_from_its_own_folder(self):
        """The viewer on a hero variant's tab: «the original» opens the variant's own picture (27.09.2026)."""
        pictures.place(H, "spread2", spread_png(self.tmp / "v.png"), "v.png", variant="G2_brunette")
        books.open_in_windows(H, "pictures", "2.png", "G2_brunette")
        for what, variant in (("pictures", ".."), ("agent", "G2_brunette"), ("pictures", "no-such")):
            with self.assertRaises(ApiError, msg=f"{what}/{variant}"):
                books.open_in_windows(H, what, "2.png", variant)


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
        # the story blueprint the check reads first lives in agent/_work/ (audit 26.09.2026: it was not looked at)
        second = rows.book_check(path)
        (path / "agent" / "_work").mkdir(exist_ok=True)
        (path / "agent" / "_work" / "story-blueprint.md").write_text("# Blueprint\n", encoding="utf-8")
        self.assertIsNot(second, rows.book_check(path))

    def test_the_agents_run_the_same_check_from_the_pipelines_folder(self):
        script = core.PIPELINE_DIR / "check_book.py"
        out = subprocess.run([sys.executable, "-B", str(script), str(self.dir / S)], capture_output=True, text=True,
                             encoding="utf-8", cwd=str(core.PIPELINE_DIR))
        self.assertIn("NOT READY", out.stdout)
        self.assertEqual(out.returncode, len(books.detail(S)["check"]["fails"]))


class APictureIntoItsRow(Base):
    def test_a_variant_is_a_folder_of_the_book_or_nothing_is_written(self):
        """Audit 26.09.2026: the variant from a request went into paths unchecked — «../..» wrote outside the book."""
        for bad in ("../..", "..", "no-such-variant"):
            with self.subTest(variant=bad), self.assertRaises(ApiError):
                pictures.place(H, "spread2", spread_png(self.tmp / "a.png"), "a.png", variant=bad)
        self.assertFalse((self.dir / H / "originals" / "variants").exists())
        self.assertFalse((self.dir / "originals").exists())
        with self.assertRaises(ApiError):
            pictures.flip(H, "spread2", variant="..")
        with self.assertRaises(ApiError):
            pictures.remove(H, "spread2", variant="..")

    def test_a_locked_page_leaves_no_half_written_file(self):
        """A page open in a viewer can stay locked: the write fails, but no «2.png.tmp» is left among the pages."""
        def locked(src, dst, copy_only=False):
            raise PermissionError("in use")
        with unittest.mock.patch.object(core, "replace_file", locked), self.assertRaises(PermissionError):
            pictures.place(H, "spread2", spread_png(self.tmp / "a.png"), "a.png")
        self.assertEqual([p.name for p in (self.dir / H / "pictures").glob("*.tmp")], [])

    def test_a_spreads_pages_are_written_together_or_not_at_all(self):
        """The two pages are written at once (04.10.2026): one that cannot be written leaves both old pages in place."""
        pictures.place(H, "spread2", spread_png(self.tmp / "a.png"), "a.png")
        before = {n: (self.dir / H / "pictures" / n).read_bytes() for n in ("2.png", "3.png")}
        real_save = Image.Image.save

        def save(im, fp, *a, **kw):
            if str(fp).endswith("3.png.tmp"):
                raise OSError("disk full")
            return real_save(im, fp, *a, **kw)
        with unittest.mock.patch.object(Image.Image, "save", save), self.assertRaises(OSError):
            pictures.place(H, "spread2", spread_png(self.tmp / "b.png", (1800, 900)), "b.png")
        self.assertEqual({n: (self.dir / H / "pictures" / n).read_bytes() for n in before}, before)
        self.assertEqual([p.name for p in (self.dir / H / "pictures").glob("*.tmp")], [])

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
        pictures.place(H, "spread2", spread_png(self.tmp / "b.png", (2000, 1000)), "b.png")  # another picture
        kept = sorted(p.name.split("-", 2)[2] for p in (self.dir / H / ".replaced").iterdir())
        self.assertEqual(kept, ["originals__spread-02-03.png", "pictures__2.png", "pictures__3.png"])
        pictures.remove(H, "spread2")
        self.assertFalse((self.dir / H / "pictures" / "2.png").exists())
        self.assertEqual(len(list((self.dir / H / ".replaced").iterdir())), 6)
        self.assertNotIn("spread2", books.state(self.dir / H).get("rows", {}))

    def test_a_removed_picture_comes_back_with_its_marks(self):
        """«Прибрати» acts at once and offers «Скасувати»: the files return from .replaced and the row's marks are as they were."""
        pictures.place(H, "spread2", spread_png(self.tmp / "a.png"), "a.png")
        marks_before = books.state(self.dir / H)["rows"]["spread2"]
        page = self.dir / H / "pictures" / "2.png"
        original_bytes = page.read_bytes()
        done = pictures.remove(H, "spread2")
        self.assertFalse(page.exists())
        self.assertNotIn("spread2", books.state(self.dir / H).get("rows", {}))
        back = pictures.restore(H, done["undo"])
        self.assertGreaterEqual(back["restored"], 2)
        self.assertEqual(page.read_bytes(), original_bytes)
        self.assertEqual(books.state(self.dir / H)["rows"]["spread2"], marks_before)

    def test_a_restore_never_overwrites_a_picture_put_there_meanwhile(self):
        pictures.place(H, "spread2", spread_png(self.tmp / "a.png"), "a.png")
        done = pictures.remove(H, "spread2")
        pictures.place(H, "spread2", spread_png(self.tmp / "b.png", (2000, 1000)), "b.png")
        newer = (self.dir / H / "pictures" / "2.png").read_bytes()
        with self.assertRaises(ApiError) as caught:
            pictures.restore(H, done["undo"])
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual((self.dir / H / "pictures" / "2.png").read_bytes(), newer)

    def test_a_restore_takes_only_files_that_are_in_replaced_and_inside_the_book(self):
        for bad in ({"files": [{"kept": "../book.json", "to": "pictures/2.png"}]},
                    {"files": [{"kept": "nothing.png", "to": "pictures/2.png"}]}):
            with self.assertRaises(ApiError):
                pictures.restore(H, bad)
        (self.dir / H / ".replaced").mkdir(exist_ok=True)
        (self.dir / H / ".replaced" / "x.png").write_bytes(b"x")
        with self.assertRaises(ApiError):
            pictures.restore(H, {"files": [{"kept": "x.png", "to": "../../outside.png"}]})
        self.assertFalse((self.dir.parent / "outside.png").exists())

    def test_an_old_picture_held_by_another_program_is_named_and_nothing_changes(self):
        """28.09.2026, the owner's book 41: «WinError 32» as an internal error, over and over — now the error says
        which program holds the old picture (Windows tells), after waiting a few seconds for it to let go."""
        pictures.place(H, "spread2", spread_png(self.tmp / "a.png"), "a.png")
        held = PermissionError(32, "used by another process")
        with unittest.mock.patch.object(core, "replace_file", side_effect=held),                 unittest.mock.patch("studio.desktop.file_holders", return_value=["Провідник Windows"]),                 unittest.mock.patch.object(pictures.time, "sleep"):
            with self.assertRaises(ApiError) as caught:
                pictures.place(H, "spread2", spread_png(self.tmp / "b.png", (2000, 1000)), "b.png")
        self.assertIn("Провідник Windows", str(caught.exception))
        self.assertIn("spread-02-03.png", str(caught.exception))
        self.assertEqual(self.pixel(H, "2.png"), (220, 40, 40))  # the row keeps its picture

    def test_the_rows_own_original_dropped_back_is_only_cut_again(self):
        """28.09.2026: the owner dragged a picture into the window straight out of the book's originals/ — the window
        held that very file and moving it to .replaced failed. The same picture byte for byte replaces nothing."""
        pictures.place(H, "spread2", spread_png(self.tmp / "a.png"), "a.png")
        original = self.dir / H / "originals" / "spread-02-03.png"
        pictures.place(H, "spread2", original, "spread-02-03.png")
        self.assertTrue(original.exists())                              # the original isn't touched …
        kept = [p.name for p in (self.dir / H / ".replaced").iterdir()]
        self.assertFalse([n for n in kept if "originals__" in n])      # … nor moved away
        self.assertEqual(self.pixel(H, "2.png"), (220, 40, 40))           # its pages cut again

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


class IdleGeneration(Base):
    def test_asking_about_an_idle_generation_mode_starts_nothing(self):
        """Book Studio's start and every background look made the generation mode — the Downloads watcher and F8's
        thread ran for the whole session, the Workshop used or not (26.09.2026)."""
        saved = generate._session
        generate._session = None
        try:
            self.assertEqual(generate.status()["active"], None)
            generate.stop(S)
            self.assertEqual(routes._gen(SimpleNamespace())["version"], 0)
            self.assertIsNone(generate._session)
        finally:
            generate._session = saved


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

    def test_a_stop_while_the_picture_is_placed_stays_a_stop(self):
        """Audit 26.09.2026: placing a picture takes up to a few seconds outside the lock; «Стоп» pressed meanwhile
        was undone — the old queue started again and took the clipboard."""
        self.s.start(S, None, series=True)
        place = pictures.place

        def slow_place(*args, **kwargs):
            self.s.stop()  # the owner presses «Стоп» while the picture is being cut
            return place(*args, **kwargs)
        spread_png(self.downloads / "g.png")
        self.s.look()
        with unittest.mock.patch.object(pictures, "place", slow_place):
            self.s.look()
        st = self.s.status()
        self.assertIsNone(st["active"])                              # stopped stays stopped
        self.assertEqual(st["last"]["file"], "g.png")                 # the picture itself is kept in its row
        self.assertTrue((self.dir / S / "pictures" / "10.png").exists())

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

    def test_a_spread_of_a_book_with_a_hero_gives_the_hero_then_the_prompt(self):
        """The owner attaches the reference to every prompt (27.09.2026): Ctrl+V the hero, Ctrl+V the prompt. Pages 1
        and 30 — the prompt alone; a book without a hero (Tier S) — the prompt alone, as before."""
        agent = self.dir / H / "agent"
        (agent / "spread-prompts-json.md").write_text(fenced([PROMPT] * 14), encoding="utf-8")
        (agent / "endpage-prompts-json.md").write_text(fenced([PROMPT] * 2), encoding="utf-8")
        st = self.s.start(H, "spread2")
        self.assertEqual(st["active"]["items"], ["герой", "промпт"])
        with Image.open(core.data_path("clipboard", "clipboard.png")) as im:       # the hero first
            self.assertEqual(im.size, (300, 400))
        self.assertTrue(st["paste"])                   # Ctrl+V in Chrome puts the prompt in by itself
        self.s.next_item()                             # (what Ctrl+V, F8 and «Далі» call)
        self.assertIn('"aspect_ratio": "2:1"', self.clip())
        self.assertFalse(self.s.status()["paste"])     # the last part: nothing is watched any more
        self.assertEqual(self.s.start(H, "page1")["active"]["items"], ["промпт"])
        self.assertEqual(self.s.start(S, "spread6")["active"]["items"], ["промпт"])

    def test_a_variants_cover_is_one_frame_the_wide_cover_at_once(self):
        """The owner, 27.09.2026: every variant has its own cover — no two stages, a place for the finished wide one
        at once, no prompt."""
        st = self.s.start(H, "cover-wrap", "G2_brunette")
        self.assertEqual(st["active"]["items"], [])     # no base cover and no variant hero yet: only waiting
        self.assertIsNone(self.clip())                   # the owner's clipboard left alone
        spread_png(self.downloads / "cover-g2.png", (2160, 1160))
        self.look()
        self.assertIsNone(self.s.status()["active"])
        final = self.dir / H / "pictures" / "variants" / "G2_brunette" / "Cover.png"
        with Image.open(final) as im:
            self.assertEqual(im.size, tuple(rows.TEMPLATE["px"]))  # brought to the printer's template
        self.assertFalse((self.dir / H / "pictures" / "Cover.png").exists())  # the base cover untouched
        self.assertEqual(books.detail(H)["variants"][0]["cover"]["final"], "Cover.png")
        with self.assertRaises(ApiError):
            pictures.place(H, "cover", spread_png(self.tmp / "c.png"), "c.png", "G2_brunette")  # no first stage
        pictures.place(H, "cover-wrap", spread_png(self.tmp / "wrap.png", (2000, 1000)), "wrap.png")  # the base's own
        pictures.remove(H, "cover-wrap", "G2_brunette")
        self.assertFalse(final.exists())
        self.assertTrue((self.dir / H / "pictures" / "Cover.png").exists())  # removing the variant's leaves the base
        pictures.place(H, "hero", spread_png(self.tmp / "h.png", (600, 800)), "h.png", "G2_brunette")
        st = self.s.start(H, "cover-wrap", "G2_brunette")
        self.assertEqual(st["active"]["items"], ["основна обкладинка", "герой варіанта"])


class CtrlVInTheBrowser(unittest.TestCase):
    """Ctrl+V in Chrome puts the next part in — a moment after V is let go; nothing else counts."""

    def play(self, presses):
        from studio.clipboard import PasteWatch
        w, fired = PasteWatch(settle=0.25), []
        for i, (ctrl, v, browser) in enumerate(presses):  # a look every 0.1 s
            if w.step(ctrl, v, browser, i / 10):
                fired.append(i / 10)
        return fired

    def test_ctrl_v_in_the_browser_counts_once_after_v_is_let_go(self):
        up, held = (True, False, True), (True, True, True)
        self.assertEqual(self.play([up, held, held, up, up, up, up, up, up]), [0.6])

    def test_v_alone_or_in_another_program_doesnt_count(self):
        self.assertEqual(self.play([(False, False, True), (False, True, True), (False, False, True)] + [(False, False, True)] * 5), [])
        self.assertEqual(self.play([(True, False, False), (True, True, False), (True, False, False)] + [(True, False, False)] * 5), [])


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


class OnePlaceForThePages(Base):
    """A book passed on takes its cover and pages from the Workshop's folder — no copy in the library (the owner,
    27.09.2026: "one place, no doubles")."""
    wait = PassingToTheLibrary.wait

    def passed(self) -> dict:
        pictures.place(S, "cover", spread_png(self.tmp / "c.png", (2000, 1000)), "c.png")
        pictures.skip_margins(S)
        return library.load(self.wait(routes._to_library(request(S, {"listingRef": LISTING})))["book"]["id"])

    def media(self, book: dict, name: str):
        """The picture's address, as the page asks for it."""
        return library._media(SimpleNamespace(groups=(book["id"], name), param=lambda _: None))

    def test_the_pages_are_the_workshops_files_and_nothing_is_copied(self):
        book = self.passed()
        pages = self.dir / S / "pictures"
        self.assertEqual(book["pagesFrom"], "workshop")
        self.assertEqual(library.asset_path(book, book["cover"]), pages / "Cover.png")
        self.assertEqual(library.asset_path(book, book["slots"]["spread2"]["left"]), pages / "2.png")
        self.assertFalse(any((library._book_dir(book["id"]) / "assets").glob("*")))    # not one copy
        self.assertEqual(self.media(book, book["cover"]["file"]).file, pages / "Cover.png")
        self.assertEqual(library.load(book["id"])["cover"]["id"], book["cover"]["id"])  # a page read once

    def test_a_page_changed_in_the_workshop_is_the_librarys_at_once(self):
        book = self.passed()
        before = book["slots"]["page1"]["image"]
        page = Image.new("RGB", (1200, 1200), (20, 160, 90))
        page.save(self.tmp / "p1.png", "PNG")
        pictures.place(S, "page1", self.tmp / "p1.png", "p1.png")
        after = library.load(book["id"])["slots"]["page1"]["image"]
        self.assertNotEqual(after["id"], before["id"])          # a new address: no old picture stays cached
        self.assertNotEqual(after["stamp"], before["stamp"])
        fresh = library.load(book["id"])
        self.assertEqual(self.media(fresh, after["file"]).file, self.dir / S / "pictures" / after["workshop"])
        with self.assertRaises(ApiError):
            self.media(fresh, before["file"])
        self.assertEqual(library.load(book["id"])["rev"], book["rev"])  # an open passport's edit isn't refused for it

    def test_a_page_taken_out_in_the_workshop_leaves_its_place_empty(self):
        book = self.passed()
        pictures.remove(S, "page1")
        after = library.load(book["id"])
        self.assertIsNone(after["slots"]["page1"]["image"])
        self.assertEqual(library.completeness(after)["illustrations"], library.completeness(book)["illustrations"] - 1)

    def test_a_workshop_folder_gone_by_hand_is_said(self):
        book = self.passed()
        self.assertFalse(library._book_response(book)["workshopMissing"])
        (self.dir / S).rename(self.dir / "41.renamed-by-hand")
        after = library.load(book["id"])
        self.assertTrue(library._book_response(after)["workshopMissing"])
        self.assertIsNone(after["cover"])                                      # nothing to show, nothing lost:
        (self.dir / "41.renamed-by-hand").rename(self.dir / S)                  # the files are where they were
        self.assertEqual(library.completeness(library.load(book["id"])), library.completeness(book))

    def test_the_passport_changes_only_the_thumbnail(self):
        book = self.passed()
        cover = (self.dir / S / "pictures" / "Cover.png").read_bytes()
        for call in (lambda: library._upload_asset(request(book["id"], slot="page1", name="p.png")),
                     lambda: library._remove_asset(SimpleNamespace(groups=(book["id"],), param=lambda n: "cover")),
                     lambda: library._swap_halves(request(book["id"], {"slot": "spread2"})),
                     lambda: library_files._folder_scan(request(book["id"], {"path": str(self.tmp)}))):
            with self.assertRaises(ApiError) as refused:
                call()
            self.assertEqual(refused.exception.status, 409)
        thumb = library._store_asset(book["id"], spread_png(self.tmp / "t.png", (800, 800)), "t.png")
        library._put_asset(book["id"], "thumbnail", thumb)
        after = library.load(book["id"])
        self.assertEqual(after["thumbnail"]["id"], thumb["id"])                  # the thumbnail is the library's own
        self.assertEqual((self.dir / S / "pictures" / "Cover.png").read_bytes(), cover)
        self.assertEqual(after["cover"]["id"], book["cover"]["id"])

    def test_the_export_takes_the_pages_from_the_workshop(self):
        book = self.passed()
        out = library_files.export_book(book, self.tmp / "export", SimpleNamespace(progress=lambda *a, **k: None))
        self.assertEqual(out["files"], 10)
        self.assertEqual((self.tmp / "export" / "Cover.png").read_bytes(),
                         (self.dir / S / "pictures" / "Cover.png").read_bytes())

    def test_deleting_the_workshop_book_leaves_the_library_its_pages(self):
        book = self.passed()
        cover = (self.dir / S / "pictures" / "Cover.png").read_bytes()
        books.delete_book(S)
        self.assertFalse((self.dir / S).exists())                               # into the (sandbox's) Recycle Bin
        after = library.load(book["id"])
        self.assertNotIn("pagesFrom", after)
        self.assertEqual(library.completeness(after), library.completeness(book))
        self.assertEqual(library.asset_path(after, after["cover"]).read_bytes(), cover)
        self.assertEqual(self.media(after, after["cover"]["file"]).file.parent, library._book_dir(book["id"]) / "assets")

    def copied_the_old_way(self) -> dict:
        """A book passed on before 27.09.2026: its pages copied into the library, and a thumbnail of its own."""
        pictures.place(S, "cover", spread_png(self.tmp / "c.png", (2000, 1000)), "c.png")
        pictures.skip_margins(S)
        book = library.create_book({"id": LISTING}, "Little lamb prayers", workshop=S)
        self.made.append(book["id"])
        folder = self.dir / S / "pictures"
        names = set(books._names(folder))
        files = [(slot, folder / name, name) for slot, page in library.WORKSHOP_PAGES
                 if (name := books.picture(names, page))]
        library.import_pictures(book["id"], files, SimpleNamespace(progress=lambda *a, **k: None))
        thumb = library._store_asset(book["id"], spread_png(self.tmp / "t.png", (800, 800)), "t.png")
        library._put_asset(book["id"], "thumbnail", thumb)
        return library.load(book["id"])

    def test_a_book_passed_on_before_takes_the_workshop_pages_and_its_copies_go(self):
        book = self.copied_the_old_way()
        library.link_workshop_books()
        after = library.load(book["id"])
        self.assertEqual(after["pagesFrom"], "workshop")
        self.assertEqual(library.completeness(after), library.completeness(book))
        self.assertEqual(library.asset_path(after, after["cover"]), self.dir / S / "pictures" / "Cover.png")
        own = sorted(p.name for p in (library._book_dir(book["id"]) / "assets").iterdir())
        self.assertEqual(own, [after["thumbnail"]["file"]])                     # only the thumbnail is left here
        binned = [p for p in core.data_path("recycle-bin").iterdir() if p.name.startswith("copied-pages-")]
        self.assertEqual(len(binned), 1)
        self.assertEqual(len(list(binned[0].iterdir())), 10)                    # the copies: in the Recycle Bin
        library.link_workshop_books()                                           # once is enough
        self.assertEqual(library.load(book["id"])["cover"]["id"], after["cover"]["id"])

    def test_a_book_with_a_page_changed_since_keeps_its_own(self):
        book = self.copied_the_old_way()
        spread_png(library.asset_path(book, book["slots"]["page1"]["image"]), (900, 900))  # changed in the passport
        library.link_workshop_books()
        after = library.load(book["id"])
        self.assertNotIn("pagesFrom", after)
        self.assertEqual(len(list((library._book_dir(book["id"]) / "assets").iterdir())), 11)


if __name__ == "__main__":
    unittest.main()
