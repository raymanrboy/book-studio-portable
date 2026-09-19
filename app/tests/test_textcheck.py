"""Text check before print: the program's comparison and rules, which page is which library text, and a
whole check with the model faked (no Ollama needed; made-up children and buyers only)."""
import json
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from PIL import Image

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core, library, textcheck as tc
from studio.jobs import UserError

STORY = {  # made-up library texts: every spread starts differently, as real books do
    2: "Morning hums along the ground,\npropellers make a gentle sound.\n{Name}, a happy day begins.",
    3: "Clouds are drifting soft and slow,\nover fields and rivers low.\nWave hello, sweet {Name}.",
    4: "Little wings wake slow and bright,\nready for a sunny flight.\n{Name} laughs and claps along.",
    5: "Rain taps softly on the hangar roof,\npuddles shine like silver proof.\n{Name} splashes in her boots.",
    6: "Warm cups wait beside the door,\nplanes rest on the hangar floor.\n{Name} sees friends gather tight.",
    7: "Stars peek out above the trees,\ncarried by the evening breeze.\nGoodnight, {Name}, sleep so sound.",
    8: "Helicopter hovers slow,\nchecking every runway glow.\n{Name}, someone guards your way.",
    9: "Glider rests upon the hill,\ntreetops whisper calm and still.\n{Name}, put your worries down.",
    10: "Seaplanes bob on quiet waves,\nnear the rocks and hidden caves.\n{Name} counts them one by one.",
    11: "Jets draw ribbons in the blue,\nwhite and long and fresh and new.\n{Name} follows every line.",
    12: "Balloons rise in morning air,\ncolors floating everywhere.\n{Name} waves from far below.",
    13: "Runway lights begin to glow,\nleading pilots nice and slow.\n{Name} yawns a sleepy yawn.",
    14: "Moonlight silvers every wing,\ncrickets hum and robins sing.\n{Name} snuggles in her bed.",
    15: "Engines hush and hangars close,\nevery plane in dreamland goes.\nSweet dreams, {Name}, goodnight.",
}
TEXTS = {"cover": "Sweet Dreams, Little Planes\nfor {Name}",
         "page1": "Dear {Name},\n\nWe made this little sky just for you.\n\nWith love,\n{Gifter}",
         "page30": "Sweet dreams, {Name}.\nMay love carry you gently, tonight and always.",
         **{f"spread{n}": t for n, t in STORY.items()}}


def fill(text, name="Olivia", gifter="Grandma & Grandpa"):
    return text.replace("{Name}", name).replace("{Gifter}", gifter)


def item(child="Olivia", gifter="With love, Grandma & Grandpa", dedication="DEFAULT", book_id=None):
    return {"childName": child, "book": {"id": book_id} if book_id else None, "variations": [
        {"name": "Your child’s name", "value": child},
        {"name": "Who the book is from", "value": gifter},
        {"name": "Dedication & Closing message", "value": dedication},
        {"name": "Cover Type & Size", "value": "8\" x 8\" Hardcover"}]}


class Words(unittest.TestCase):
    def test_quotes_dashes_and_punctuation_are_not_differences(self):
        self.assertEqual(tc.diff("Olivia’s garden — “wide”, bright!", "Olivia's garden - \"wide\" bright"), [])

    def test_capitals_by_design_are_fine_but_a_lowercase_name_is_not(self):
        self.assertEqual(tc.diff("FLOWER GIRL Olivia", "FLOWER GIRL OLIVIA"), [])
        self.assertEqual(tc.diff("Dear Olivia", "Dear olivia"), [{"expected": "Olivia", "printed": "olivia"}])

    def test_accents_are_strict(self):
        self.assertEqual(tc.diff("Zoë's shadow", "Zoe's shadow"), [{"expected": "Zoë's", "printed": "Zoe's"}])

    def test_missing_extra_changed_and_stuck_words(self):
        self.assertEqual(tc.diff("our hearts grew a little bit wider", "our hearts grew a little wider"),
                         [{"expected": "bit", "printed": ""}])
        self.assertEqual(tc.diff("Isabella walked on tiny toes", "Isabellawalked on tiny toes"),
                         [{"expected": "Isabella walked", "printed": "Isabellawalked"}])
        self.assertEqual(tc.diff("a gentle sound", "a soft sound"), [{"expected": "gentle", "printed": "soft"}])

    def test_the_models_apology_is_not_text(self):
        self.assertFalse(tc.has_text("I'm sorry, but I cannot transcribe the text from this image."))
        self.assertFalse(tc.has_text("Tapy"))
        self.assertTrue(tc.has_text("Morning hums along the ground,\npropellers make"))
        self.assertTrue(tc.has_text("I cannot wait to see you fly"[2:]))  # «cannot» inside a story is fine


class BuyerFields(unittest.TestCase):
    def test_default_in_all_its_spellings(self):
        for value in ("DEFAULT", "“DEFAULT “", "Dedication and Closing   Default", "default please", ""):
            with self.subTest(value=value):
                self.assertTrue(tc.is_default(value))
        self.assertFalse(tc.is_default("May you always fly high and soar among the stars."))

    def test_own_dedication_and_closing_are_split(self):
        p = tc.personalization(item(dedication="Dedication:  Welcome to the world, Little Mia.\nClosing:  Sweet dreams, Mia."))
        self.assertEqual((p["dedication"], p["closing"]), ("Welcome to the world, Little Mia.", "Sweet dreams, Mia."))
        p = tc.personalization(item(dedication="Dedication:\nDear Mia,\nWe love you!\n\nClosing: DEFAULT + Mia Rose"))
        self.assertEqual((p["dedication"], p["closing"]), ("Dear Mia,\nWe love you!", None))  # closing: the book's own

    def test_the_buyers_slips_in_from_are_tidied(self):
        self.assertEqual(tc.personalization(item(gifter='"With love ,Anna and Mark"'))["gifter"], "With love, Anna and Mark")

    def test_fill_keeps_one_greeting(self):
        page1 = TEXTS["page1"]
        self.assertTrue(tc.fill(page1, "Olivia", "Your cousins, Sam and Max").endswith("With love,\nYour cousins, Sam and Max"))
        self.assertTrue(tc.fill(page1, "Olivia", "With Love, Aunt Kate & Uncle Tom").endswith("just for you.\n\nWith Love, Aunt Kate & Uncle Tom"))
        self.assertIsNone(tc.fill(page1, "Olivia", ""))       # «from» unknown: nothing exact to compare with
        self.assertIsNone(tc.fill("{Name} and {Pet}", "Olivia", "x"))


class NameRules(unittest.TestCase):
    def kinds(self, text, child="Olivia", vocab=frozenset(tc.COMMON), others=frozenset()):
        return [(f["kind"], f["printed"]) for f in tc.findings(tc.words(text), child, set(vocab), set(others))]

    def test_the_program_catches_names_and_placeholders(self):
        self.assertEqual(self.kinds("Dear Ollivia, from {Gifter}"), [("name", "Ollivia"), ("placeholder", "{Gifter}")])
        self.assertEqual(self.kinds("Zoe danced", child="Zoë"), [("name", "Zoe")])
        self.assertEqual(self.kinds("and Isabellawalked on", child="Isabella"), [("stuck", "Isabellawalked")])
        self.assertEqual(self.kinds("so olivia smiled"), [("case", "olivia")])
        self.assertEqual(self.kinds("OLIVIA'S GARDEN and Olivia's hat"), [])

    def test_everyday_words_and_the_books_own_names_are_left_alone(self):
        self.assertEqual(self.kinds("And then Ann sang", child="Ann"), [])            # «And» is not a typo of «Ann»
        self.assertEqual(self.kinds("Kind Ruth chose", child="Ruthie", vocab=tc.COMMON | {"ruth"}), [])
        self.assertEqual(self.kinds("God's love, grace and GRACE", child="Grace"), [])   # a child named Grace
        self.assertEqual(self.kinds("the sun rose over Lily Rose", child="Lily Rose", vocab=tc.COMMON | {"rose"}), [])

    def test_another_orders_child(self):
        self.assertEqual(self.kinds("Mason and Noah built a snowman", child="Mason", others={"noah"}),
                         [("foreign", "Noah")])


class Assign(unittest.TestCase):
    def test_a_printify_book_without_three_spreads(self):
        refs = {k: fill(v) for k, v in TEXTS.items()}
        kept = [n for n in STORY if n not in (5, 9, 12)]              # 11 spreads → pages 2..23, 24 pages
        reads = {}
        for k, n in enumerate(kept, 1):
            left, right = 2 * k, 2 * k + 1
            text_page = left if k % 2 == 0 else right
            reads[text_page] = " ".join(tc.words(refs[f"spread{n}"])[:12])
        mapping = tc.assign(24, reads, refs)
        self.assertEqual(len(mapping), 11)
        self.assertEqual([mapping[p] for p in sorted(mapping)], [f"spread{n}" for n in kept])

    def test_a_page_unlike_any_text_is_left_unmatched_in_a_short_book(self):
        refs = {k: fill(v) for k, v in TEXTS.items()}
        reads = {3: "Completely different words that the library never had at all"}
        self.assertEqual(tc.assign(24, reads, refs), {})

    def test_a_full_book_keeps_every_page_in_its_place(self):
        """30 pages: the last two spreads printed in the other order stay spreads 14 and 15 — each page is then
        compared with its own library text, so the difference shows (and can teach the passport)."""
        refs = {k: fill(v) for k, v in TEXTS.items()}
        reads = {2 * k + 1: " ".join(tc.words(refs[f"spread{n}"])[:12]) for k, n in enumerate(STORY, 1)}
        reads[27], reads[29] = reads[29], reads[27]
        mapping = tc.assign(30, reads, refs)
        self.assertEqual((mapping[27], mapping[29]), ("spread14", "spread15"))
        self.assertEqual(len(mapping), 14)


class PageIssues(unittest.TestCase):
    pers = {"child": "Olivia", "gifter": "Grandma", "dedication": None, "closing": None}

    def target(self, mode="strict", expected="Wave hello, sweet Olivia.", page=5):
        return {"page": page, "part": None, "file": f"{page}.png", "label": f"Стор. {page}", "count": 24,
                "mode": mode, "expected": expected}

    def issues(self, target, transcript, verdict="ok", problems=()):
        return tc.page_issues(target, {"transcript": transcript, "verdict": verdict, "problems": list(problems)},
                              self.pers, set(tc.COMMON), set())

    def test_both_agree_red(self):
        found = self.issues(self.target(), "Wave hello, sweet child.", "error", ["Ім'я замінено"])
        self.assertEqual([(i["level"], i["text"]) for i in found], [("error", "«child» замість «Olivia»")])
        self.assertEqual(found[0]["note"], "Ім'я замінено")

    def test_only_the_comparison_amber(self):
        found = self.issues(self.target(), "Wave hello, dear Olivia.", "ok")
        self.assertEqual([(i["level"], i["text"]) for i in found], [("warn", "«dear» замість «sweet»")])

    def test_only_the_model_amber_but_not_for_punctuation(self):
        cut = self.issues(self.target(), "Wave hello, sweet Olivia.", "error", ["Слово «Olivia» обрізане краєм сторінки"])
        self.assertEqual([i["level"] for i in cut], ["warn"])
        quotes = self.issues(self.target(), "Wave hello, sweet Olivia.", "error", ["Відсутні лапки навколо тексту", "Пробіл після коми"])
        self.assertEqual(quotes, [])

    def test_a_misspelt_name_is_red_even_on_the_owners_own_pages(self):
        found = self.issues(self.target("personal", "Dear Olivia, with love, Grandma", 1), "Dear Ollivia, with love, Grandma")
        self.assertEqual([(i["level"], i["text"]) for i in found], [("error", "«Ollivia» замість «Olivia»")])
        edited = self.issues(self.target("personal", "Dear Olivia, with love, Grandma", 1), "Dear Olivia, love, Grandma")
        self.assertEqual([i["level"] for i in edited], ["warn"])  # the owner's edit of the greeting: worth a look


class WholeCheck(unittest.TestCase):
    """24 pages for Printify without spreads 5, 9 and 12; the model is a stand-in that «reads» what the test
    printed on each page and answers like Gemma does."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name) / "print"
        self.folder.mkdir()
        self.book_id = "a" * 32
        book = {"id": self.book_id, "schema": 1, "rev": 0, "title": "Planes", "listing": {"id": "4100000900"},
                "slots": library._empty_slots(), "text": dict(TEXTS), "cover": None, "thumbnail": None}
        library.save(book)
        refs = {k: fill(v, gifter="Grandma & Grandpa") for k, v in TEXTS.items()}
        self.printed = {"Cover.png|front": refs["cover"].replace("Olivia", "{Name}"),   # a placeholder left
                        "Cover.png|back": "", "1.png|None": refs["page1"], "24.png|None": refs["page30"]}
        kept = [n for n in STORY if n not in (5, 9, 12)]
        for k, n in enumerate(kept, 1):
            text_page, picture_page = (2 * k, 2 * k + 1) if k % 2 == 0 else (2 * k + 1, 2 * k)
            text = refs[f"spread{n}"]
            if n == 7:
                text = text.replace("Olivia", "Ollivia")                                 # a misspelt name
            self.printed[f"{text_page}.png|None"] = text
            self.printed[f"{picture_page}.png|None"] = "I'm sorry, but I cannot transcribe this lettering." if k == 3 else ""
        Image.new("RGB", (60, 30)).save(self.folder / "Cover.png")
        for n in range(1, 25):
            Image.new("RGB", (40, 40)).save(self.folder / f"{n}.png")
        self.calls = 0
        tc._cache.clear()

    def tearDown(self):
        self.tmp.cleanup()

    def fake_chat(self, model, prompt, picture, schema=None, max_tokens=None):
        self.calls += 1
        text = self.printed.get(picture, "")
        if schema is None:
            return " ".join(text.split()[:12])
        expected = prompt.split("EXPECTED:\n", 1)[1] if "EXPECTED:\n" in prompt else None
        bad = expected is not None and tc.words(expected) != tc.words(text)
        return json.dumps({"transcript": text, "verdict": "error" if bad else "ok",
                           "problems": ["Текст відрізняється"] if bad else []})

    def run_check(self, item_):
        job = SimpleNamespace(progress=lambda *a, **k: None)
        with mock.patch.object(tc, "_ready"), mock.patch.object(tc, "_chat", side_effect=self.fake_chat), \
                mock.patch.object(tc, "picture", side_effect=lambda path, part=None: f"{path.name}|{part}"), \
                mock.patch.object(tc, "_other_children", return_value={"noah"}):
            return tc.check_book(job, "4100000101", item_, str(self.folder), 24)

    def test_finds_the_planted_mistakes_and_nothing_else(self):
        res = self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        self.assertEqual(res["mode"], "full")
        self.assertEqual(res["skipped"], [5, 9, 12])
        found = [(i["level"], i["label"], i["text"]) for i in res["issues"]]
        page_of_7 = next(p["page"] for p in res["pages"] if p["key"] == "spread7")
        self.assertEqual(found, [("error", "Обкладинка", "Залишився шаблон «{Name}»"),
                                 ("error", f"Стор. {page_of_7}", "«Ollivia» замість «Olivia»")])
        checked = {p["key"] for p in res["pages"] if p["key"]}
        self.assertEqual(checked, {"cover", "page1", "page30"} | {f"spread{n}" for n in STORY if n not in (5, 9, 12)})
        learn = {p["key"]: p["learn"] for p in res["pages"] if p["key"]}
        self.assertIsNone(learn["spread7"])        # a misspelt name never teaches the passport
        self.assertFalse(any(learn.values()))      # clean pages have nothing to teach
        journal = sorted(tc.CHECKS.glob("*_4100000101.json"))
        self.assertTrue(journal)
        self.assertNotIn("key", json.loads(journal[-1].read_text(encoding="utf-8"))["pages"][0].get("prompt", ""))

    def test_a_template_unlike_the_passport_can_teach_it(self):
        self.printed["Cover.png|front"] = "Sweet Dreams\ndear Olivia"          # the Canva cover says it otherwise
        res = self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        cover = next(p for p in res["pages"] if p["key"] == "cover")
        self.assertEqual((cover["learn"], cover["text"]), ("cover", "Sweet Dreams\ndear Olivia"))
        self.assertTrue(all(i["kind"] == "diff" for i in res["issues"] if i["page"] == 0))

    def test_a_second_check_of_the_same_files_is_instant(self):
        self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        first = self.calls
        self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        self.assertEqual(self.calls, first)

    def test_light_check_without_library_texts(self):
        res = self.run_check(item(gifter="Grandma & Grandpa"))
        self.assertEqual((res["mode"], res["light"]), ("light", "noBook"))
        texts = [i["text"] for i in res["issues"]]
        self.assertIn("Залишився шаблон «{Name}»", texts)
        self.assertIn("«Ollivia» замість «Olivia»", texts)
        self.assertFalse([t for t in texts if "розвороті немає тексту" in t])


class Passport(unittest.TestCase):
    def test_a_printed_page_becomes_the_library_text(self):
        self.assertEqual(tc.as_template("Sweet Dreams\ndear JASPER\n\n\n", "Jasper"), "Sweet Dreams\ndear {Name}")
        book_id = "b" * 32
        library.save({"id": book_id, "schema": 1, "rev": 0, "title": "Planes", "listing": {"id": "4100000901"},
                      "slots": library._empty_slots(), "text": dict(TEXTS), "cover": None, "thumbnail": None})
        res = tc._passport(SimpleNamespace(json={"bookId": book_id, "child": "Jasper", "pages": [
            {"key": "cover", "text": "Sweet Dreams\ndear Jasper"}, {"key": "spread15", "text": "Jasper's plane sleeps."}]}))
        self.assertEqual(res["updated"], ["cover", "spread15"])
        text = library.load(book_id)["text"]
        self.assertEqual((text["cover"], text["spread15"]), ("Sweet Dreams\ndear {Name}", "{Name}'s plane sleeps."))
        self.assertEqual(text["spread2"], TEXTS["spread2"])
        for bad in ({"key": "page1", "text": "Dear Jasper"}, {"key": "cover", "text": ""}):  # the owner's own pages stay his
            with self.subTest(bad=bad), self.assertRaises(Exception):
                tc._passport(SimpleNamespace(json={"bookId": book_id, "child": "Jasper", "pages": [bad]}))


class OllamaAndRoutes(unittest.TestCase):
    def test_only_this_computer(self):
        with mock.patch.object(core.settings, "section", return_value={"url": "http://192.168.1.5:11434"}):
            with self.assertRaises(tc.ModelError):
                tc._base()
        with mock.patch.object(core.settings, "section", return_value={"url": "http://example.com"}),                 mock.patch.object(tc._NO_PROXY, "open", side_effect=AssertionError("no request may leave")):
            self.assertFalse(tc.status()["running"])

    def test_ollama_down_is_said_plainly(self):
        with mock.patch.object(tc, "_alive", return_value=False), mock.patch.object(tc, "start_ollama", return_value=False):
            with self.assertRaises(tc.Unavailable) as err:
                tc._ready("gemma", lambda step: None)
        self.assertIn("Ollama", str(err.exception))

    def test_missing_model(self):
        with mock.patch.object(tc, "_alive", return_value=True), \
                mock.patch.object(tc, "_call", return_value={"models": [{"name": "other:1b"}]}):
            with self.assertRaises(tc.ModelError) as err:
                tc._ready("gemma4:12b-it-qat", lambda step: None)
        self.assertIn("gemma4:12b-it-qat", str(err.exception))

    def test_switched_off_and_settings(self):
        core.settings.update({"textcheck": {"enabled": False}})
        try:
            self.assertEqual(tc._check(SimpleNamespace(groups=["4100000101"], json={"folder": "x", "pages": 24})), {"off": True})
        finally:
            core.settings.update({"textcheck": {"enabled": True}})
        with mock.patch.object(tc, "status", return_value={}):
            tc._save_settings(SimpleNamespace(json={"model": "gemma4:12b-it-qat"}))
            with self.assertRaises(Exception):
                tc._save_settings(SimpleNamespace(json={"model": "bad model; rm"}))

    def test_a_check_needs_the_order(self):
        with mock.patch("studio.profit.picker_orders", return_value=[]):
            with self.assertRaises(UserError):
                tc.check_order(SimpleNamespace(progress=lambda *a, **k: None), "4100000101", "x", 24)


if __name__ == "__main__":
    unittest.main()
