"""Text check before print: the program's comparison and rules, which page is which library text, and a
whole check with the model faked (no Ollama needed; made-up children and buyers only)."""
import importlib.util
import io
import json
import random
import re
import shutil
import tempfile
import threading
import time
import unittest
import zlib
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from PIL import Image, ImageDraw

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core, images, library, textcheck as tc, wording
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


def gemma_answer(printed: str, prompt: str, schema) -> str:
    """What the stand-in model answers for a page with `printed` on it, the way Gemma does: a read — its first dozen
    words; a check — the transcript and whether it says what the prompt EXPECTED."""
    if schema is None:
        return " ".join(printed.split()[:12])
    expected = prompt.split("EXPECTED:", 1)[1].strip() if "EXPECTED:" in prompt else None
    bad = expected is not None and tc.words(expected) != tc.words(printed)
    return json.dumps({"transcript": printed, "verdict": "error" if bad else "ok",
                       "problems": ["Текст відрізняється"] if bad else []})


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

    def test_the_card_marks_own_text_by_the_same_rule(self):
        """22.09.2026 audit: the card called "“DEFAULT “" the buyer's own text while the check expected the book's."""
        from studio import orders
        order = {"items": [{"variations": [
            {"name": "Dedication and Closing", "value": "“DEFAULT “"},
            {"name": "Personalized Dedication", "value": "Dedication and Closing   Default"},
            {"name": "Dedication", "value": "Sweet dreams, Mia."},
            {"name": "Child's name", "value": "DEFAULT"}]}]}
        orders.enrich(order, {})
        self.assertEqual([v["custom"] for v in order["items"][0]["variations"]], [False, False, True, False])

    def test_own_dedication_and_closing_are_split(self):
        p = tc.personalization(item(dedication="Dedication:  Welcome to the world, Little Mia.\nClosing:  Sweet dreams, Mia."))
        self.assertEqual((p["dedication"], p["closing"]), ("Welcome to the world, Little Mia.", "Sweet dreams, Mia."))
        p = tc.personalization(item(dedication="Dedication:\nDear Mia,\nWe love you!\n\nClosing: DEFAULT + Mia Rose"))
        self.assertEqual((p["dedication"], p["closing"]), ("Dear Mia,\nWe love you!", None))  # closing: the book's own

    def test_a_possessive_name_is_the_name(self):
        """25.09.2026 calibration: a buyer typed «Olivia's» (thinking of «Olivia's Baptism Day») — every page of the
        book was red for «Olivia» instead of «Olivia's», and the cover wanted «Olivia's's»."""
        self.assertEqual([wording.clean_name(n) for n in ("Olivia's", "Leo & Mila’s.", "Charles'", "O'Neil", "Jo's")],
                         ["Olivia", "Leo & Mila", "Charles", "O'Neil", "Jo"])
        self.assertEqual(tc.personalization(item(child="Olivia's"))["child"], "Olivia")

    def test_the_buyers_slips_in_from_are_tidied(self):
        self.assertEqual(tc.personalization(item(gifter='"With love ,Anna and Mark"'))["gifter"], "With love, Anna and Mark")

    def test_fill_keeps_one_greeting(self):
        page1 = TEXTS["page1"]
        self.assertTrue(tc.fill(page1, "Olivia", "Your cousins, Sam and Max").endswith("With love,\nYour cousins, Sam and Max"))
        self.assertTrue(tc.fill(page1, "Olivia", "With Love, Aunt Kate & Uncle Tom").endswith("just for you.\n\nWith Love, Aunt Kate & Uncle Tom"))
        self.assertIsNone(tc.fill(page1, "Olivia", ""))       # «from» unknown: nothing exact to compare with
        self.assertIsNone(tc.fill("{Name} and {Pet}", "Olivia", "x"))
        # 06.10.2026 calibration: a «from whom» that signs off further in («… boy! Love, Mama & Dada») too
        self.assertTrue(tc.fill(page1, "Olivia", "We love you baby girl! Love, Mama & Dada").endswith(
            "just for you.\n\nWe love you baby girl! Love, Mama & Dada"))

    def test_the_buyers_headings_as_they_type_them(self):
        """06.10.2026 calibration: «Dedication -» … «Closing» alone on a line, «dedicati:» … «close:» (Etsy cut the
        word), a note to the seller before «DEDICATION:» — each once flagged its heading or note as missing words."""
        split = tc.split_dedication
        self.assertEqual(split("Dedication -\nTo our sweet Mia girl,\nWe love you!\n\nClosing\nKeep smiling!"),
                         ("To our sweet Mia girl,\nWe love you!", "Keep smiling!"))
        self.assertEqual(split("dedicati: To my precious Goddaughter,\nBe blessed.\n\nclose:I promise to guide you."),
                         ("To my precious Goddaughter,\nBe blessed.", "I promise to guide you."))
        self.assertEqual(split("Note: Please center the text to match the default.\n\nDEDICATION: \nDear Mia,\nWith Love, D"),
                         ("Dear Mia,\nWith Love, D", None))
        self.assertEqual(split("Dedicated to the little one who closed our hearts to sadness."),
                         ("Dedicated to the little one who closed our hearts to sadness.", None))


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

    def test_the_models_own_word_on_punctuation_is_taken(self):
        """22.09.2026 audit: whether a remark was shown hung on Ukrainian word stems in the model's wording. The
        model now also answers only_punctuation (Gemma 4 12B on made-up pages, 23.09.2026: true for a missing
        comma and for quotes, false for a line cut off at the edge); a cut-off word is shown whatever it says."""
        def issues(problem, flag):
            return tc.page_issues(self.target(), {"transcript": "Wave hello, sweet Olivia.", "verdict": "error",
                                                  "problems": [problem], "only_punctuation": flag},
                                  self.pers, set(tc.COMMON), set())
        self.assertEqual(issues("Інакше оформлено звертання", True), [])            # wording no rule knows
        self.assertEqual(len(issues("Інакше оформлено звертання", False)), 1)
        self.assertEqual(len(issues("Слово «Olivia» обрізане краєм сторінки", True)), 1)
        self.assertEqual(issues("Відсутні лапки навколо тексту", False), [])        # the words still decide too

    def test_capitals_of_the_storys_own_words_are_the_templates(self):
        """«love» for «Love», «Savior» for «savior»: in 30 real checks only ever the Canva template's own capitals
        (25.09.2026 calibration). A child's name in small letters stays red."""
        story = self.target(expected="The savior baby came, and love was near.")
        self.assertEqual(self.issues(story, "The Savior baby came, and Love was near.", "error",
                                     ["Слово 'Savior' написано з великої літери"]), [])
        self.assertEqual([i["level"] for i in self.issues(self.target(), "Wave hello, sweet olivia.")], ["error"])

    def test_the_model_saying_there_is_no_mistake_is_not_shown(self):
        said = ["Ім'я написане як \"Olivia's\". Однак помилки у словах немає. Перевірка показує повну відповідність."]
        self.assertEqual(self.issues(self.target(), "Wave hello, sweet Olivia.", "error", said), [])

    def test_where_a_line_breaks_is_the_owners(self):
        page1 = self.target("loose", None, 1)
        broken = ["'St.' стоїть в кінці рядка, а назва церкви 'Mary's Church' починається з нового рядка."]
        self.assertEqual(self.issues(page1, "Dear Olivia,\nBaptism: May 4 St.\nMary's Church", "error", broken), [])
        again = self.issues(page1, "Dear Olivia,\nBaptism: May 4", "error", ["Рядок 'Dear Olivia' повторюється на початку"])
        self.assertEqual(len(again), 1)

    def test_the_buyers_own_words_are_not_corrected(self):
        """The model «corrected» a Bible verse the buyer quoted their own way; the program sees every word of the
        buyer's message on the page, so that remark goes. A word the buyer wrote and the page lacks stays."""
        own = 'Made for Olivia with love!\n"I am with you until the end of age." Mt 28:20'
        page1 = {**self.target("loose", None, 1), "own": own}
        printed = 'Made for Olivia\nwith Love!\n"I am with you until the end\nof age." Mt 28:20\n\nWith love,\nGrandma'
        verse = ["У цитаті пропущено слово 'the' перед 'age' (має бути 'the end of the age')."]
        self.assertEqual(self.issues(page1, printed, "error", verse), [])
        lost = self.issues(page1, printed.replace("until ", ""), "error", ["Пропущено слово 'until'"])
        self.assertEqual([i["kind"] for i in lost], ["model"])
        cut = self.issues(page1, printed, "error", ["Слово 'age' обрізане краєм сторінки"])
        self.assertEqual([i["kind"] for i in cut], ["model"])

    def test_a_greeting_or_signature_printed_twice(self):
        """The owner merges the buyer's message with the page's template by hand; a greeting or the «from» line
        kept twice was missed by the model once (20.09.2026) — the program counts it itself."""
        pers = {**self.pers, "gifter": "With love, Mark and Anna"}
        page1 = {**self.target("loose", None, 1), "own": "Dear Olivia, we are so happy for you! Love, Anna & Mark"}

        def said(text):
            return [i["text"] for i in tc.page_issues(page1, {"transcript": text, "verdict": "ok", "problems": []},
                                                       pers, set(tc.COMMON), set())]
        twice = "Dear Olivia,\n\nDear Olivia, we are so happy for you!\nLove, Anna & Mark\n\nWith love,\nMark and Anna"
        self.assertEqual(said(twice), ["Підпис «від кого» двічі", "Двічі «Dear Olivia»"])
        self.assertEqual(said("Dear Olivia, we are so happy for you!\nLove, Anna & Mark"), [])
        pers["gifter"] = "Your family"   # one word of its own: the template's «your family» is not a second signature
        self.assertEqual(said("Loved by God and your family.\nWith love,\nYour family"), [])

    def test_a_misspelt_name_is_red_even_on_the_owners_own_pages(self):
        found = self.issues(self.target("personal", "Dear Olivia, with love, Grandma", 1), "Dear Ollivia, with love, Grandma")
        self.assertEqual([(i["level"], i["text"]) for i in found], [("error", "«Ollivia» замість «Olivia»")])
        edited = self.issues(self.target("personal", "Dear Olivia, with love, Grandma", 1), "Dear Olivia, love, Grandma")
        self.assertEqual([i["level"] for i in edited], ["warn"])  # the owner's edit of the greeting: worth a look

    def test_the_owners_marks_of_the_sixth_of_october(self):
        """06.10.2026 calibration on 71 journaled checks: 22 rows the owner marked «not a mistake» → 1 (a page the
        model could not read — `_salvage`). Each kind once, and what must still show beside it."""
        loose1 = {**self.target("loose", None, 1), "own": "Dear Ava, May you always know how loved you are."}
        printed = "Dear Ava,\nMay you always know how loved you are."
        pers = {**self.pers, "child": "Ava Rose"}

        def said(target, text, problems, who=pers):
            return [i["text"] for i in tc.page_issues(target, {"transcript": text, "verdict": "error", "problems": problems},
                                                       who, set(tc.COMMON), set())]
        self.assertEqual(said(loose1, printed, ["Ім'я дитини вказано як 'Ava', хоча в завданні зазначено 'Ava Rose'."]), [])
        cut = ["Ім'я 'Ava Ros' обрізане краєм сторінки, має бути 'Ava Rose'"]
        self.assertEqual(said(loose1, printed, cut), cut)
        story = self.target(expected="Amen, sweet Olivia.")
        self.assertEqual(said(story, "Amen, sweet Olivia.", ["Слово 'Amen.' знаходиться на новому рядку, тоді як в "
                                                             "очікуваному тексті воно у тому ж рядку після імені Olivia."]), [])
        self.assertEqual(said(story, "Amen, sweet Olivia.", ["Насправді написано 'Olivia'. Текст повністю збігається."]), [])
        self.assertEqual(len(said(story, "Amen, sweet Olivia.", ["Слово 'Olivia' обрізане краєм сторінки"])), 1)
        # A whole signed message from the buyer: the template's last wish above it may go, and the model's «a line is
        # missing» goes with it — but the line kept is never «extra».
        gifter = "God bless you and keep you always, our sweet grandson! Love, Pop-pop and Nonna"
        page1 = self.target("personal", tc.fill("Dear {Name},\nWishing you God's love.\n\nCongratulations on your Baptism!"
                                                "\n\nWith love,\n{Gifter}", "Olivia", gifter), 1)
        who = {**self.pers, "gifter": gifter}
        dropped = "Dear Olivia,\nWishing you God's love.\n\n" + gifter
        self.assertEqual(said(page1, dropped, ["Відсутній рядок тексту: 'Congratulations on your Baptism!'"], who), [])
        self.assertEqual(said(page1, dropped.replace("God's ", ""), [], who), ["Пропущено «God's»"])
        kept = "Dear Olivia,\nWishing you God's love.\nCongratulations on your Baptism!\n" + gifter
        self.assertEqual(said(page1, kept, [], who), [])


    def test_the_owners_marks_of_the_nineteenth_of_october(self):
        """19.10.2026 calibration on 103 journaled checks against the print archive: each kind of «not a mistake»
        once, and what must still show beside it."""
        def said(target, text, pers, problems=(), verdict="error"):
            return [i["text"] for i in tc.page_issues(target, {"transcript": text, "verdict": verdict,
                                                               "problems": list(problems)},
                                                       pers, tc._vocabulary(pers), {"john"})]
        # A name typed in small letters is printed with a capital — and printed small it is red.
        kobe = {**self.pers, "child": tc.personalization(item(child="kobe"))["child"]}
        self.assertEqual(kobe["child"], "Kobe")
        self.assertEqual(said(self.target(expected="Wave hello, sweet Kobe."), "Wave hello, sweet Kobe.", kobe), [])
        self.assertEqual(said(self.target(expected="Wave hello, sweet Kobe."), "Wave hello, sweet kobe.", kobe),
                         ["«kobe» замість «Kobe» — великі й малі літери"])
        # The owner's own line of love above a bare «from whom»; a line said twice still shows.
        nanny = {**self.pers, "gifter": "Nanny"}
        page1 = self.target("personal", tc.fill(TEXTS["page1"], "Olivia", "Nanny"), 1)
        mine = "Dear Olivia,\n\nWe made this little sky just for you.\n\nLove you always,\nNanny"
        self.assertEqual(said(page1, mine, nanny, ["Слово 'love' у підписі замінено на 'you always'."]), [])
        self.assertEqual(said(page1, mine.replace("you always", "you always and"), nanny), [])  # still a line of love
        self.assertEqual(said(page1, mine.replace("Love you always,", "Bye,"), nanny, verdict="ok"),
                         ["«Bye» замість «With love»"])
        # A «from whom» that is a wish of its own: no «With love,» above it.
        self.assertTrue(tc.fill(TEXTS["page1"], "Olivia", "Happy Diwali").endswith("just for you.\n\nHappy Diwali"))
        # «Godparents-John» laid out as «Godparents –\nJohn»: not another order's John, not a difference.
        godparents = {**self.pers, "gifter": "Love, Your Godparents-John and Danna"}
        signed = self.target("personal", "Dear Olivia,\n\nLove, Your Godparents-John and Danna", 1)
        self.assertEqual(said(signed, "Dear Olivia,\n\nLove, Your Godparents –\nJohn and Danna", godparents, verdict="ok"), [])
        self.assertEqual(said(signed, "Dear Olivia,\n\nLove, Your Godparents –\nJohn", godparents, verdict="ok"),
                         ["«Godparents John» замість «Godparents-John and Danna»"])  # a lost name still shows
        # «James'» for «James's»: one name, two spellings.
        self.assertEqual(tc.diff("James's First Birthday", "James' FIRST BIRTHDAY"), [])
        self.assertEqual(tc.diff("Olivia's First Birthday", "Olivia FIRST BIRTHDAY"),
                         [{"expected": "Olivia's", "printed": "Olivia"}])
        self.assertEqual(tc.diff("James's First Birthday", "James FIRST BIRTHDAY"),   # no apostrophe: a lost «'s»
                         [{"expected": "James's", "printed": "James"}])
        self.assertTrue(tc.diff("Happy birthday, Mary-Kate", "Happy birthday, mary-\nkate"))  # small letters still show
        # What the review of this calibration traced: names typed small, a typo in the owner's own line, a late wish.
        self.assertEqual([tc.printed_name(n) for n in ("leo and mila", "o'neil", "de la cruz", "mary-kate", "McKenzie")],
                         ["Leo and Mila", "O'Neil", "de la Cruz", "Mary-Kate", "McKenzie"])
        self.assertEqual(said(page1, mine.replace("always", "alwys"), nanny, verdict="ok"),
                         ["Пропущено «With»", "Зайве «you alwys»"])  # a typo in it still shows
        self.assertTrue(tc.fill(TEXTS["page1"], "Olivia", "Grandma Sue. Merry Christmas!").endswith(
            "With love,\nGrandma Sue. Merry Christmas!"))
        # Where a line breaks, said another way.
        story = self.target(expected="May God bless Olivia today\nand forevermore.")
        self.assertEqual(said(story, "May God bless\nOlivia today and forevermore.", self.pers,
                              ["Слово 'forevermore' записане в один рядок разом із ім'ям 'Olivia today'."]), [])


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
        for n in range(1, 25):  # each page its own pixels: answers are kept by a file's content
            Image.new("RGB", (40, 40), (n, 0, 0)).save(self.folder / f"{n}.png")
        self.calls = 0
        self.ready = mock.MagicMock()  # Ollama and the model, as run_check() fakes them
        tc._cache.clear()
        core.settings.update({"textcheck": {"prescan": False}})  # these pages are blank squares

    def tearDown(self):
        core.settings.update({"textcheck": {"prescan": True}})
        self.tmp.cleanup()

    def fake_chat(self, model, prompt, picture, schema=None, max_tokens=None):
        self.calls += 1
        return gemma_answer(self.printed.get(picture, ""), prompt, schema)

    def fake_job(self):
        """A job like the real one; self.shared keeps every list of findings the check handed out as it ran."""
        self.shared = []
        return SimpleNamespace(id="job1", progress=lambda *a, **k: None, share=self.shared.append)

    def run_check(self, item_):
        job = self.fake_job()
        with mock.patch.object(tc.ollama, "_ready", self.ready), mock.patch.object(tc.ollama, "_chat", side_effect=self.fake_chat), \
                mock.patch.object(tc.run, "picture", side_effect=lambda path, part=None: f"{path.name}|{part}"), \
                mock.patch.object(tc.run, "_other_children", return_value={"noah"}), \
                mock.patch.object(tc.ollama, "_release_model") as release:
            res = tc.check_book(job, "4100000101", item_, str(self.folder), 24)
        release.assert_called_once()   # the graphics card is freed right after the check
        self.assertEqual((tc.run._active, tc._runs), (0, {}))
        return res

    def test_a_stopped_check_stops(self):
        """The card was closed: pages not yet asked are never asked, the model is still let go."""
        asked = []

        def chat(*args, **kwargs):
            asked.append(1)
            if len(asked) == 3:
                self.assertTrue(tc.cancel("4100000101", "job1"))
                self.assertFalse(tc.cancel("4100000101", "another-job"))   # only that job's check
            return self.fake_chat(*args, **kwargs)

        job = self.fake_job()
        with mock.patch.object(tc.ollama, "_ready"), mock.patch.object(tc.ollama, "_chat", side_effect=chat), \
                mock.patch.object(tc.run, "picture", side_effect=lambda path, part=None: f"{path.name}|{part}"), \
                mock.patch.object(tc.ollama, "_release_model") as release, self.assertRaises(UserError):
            tc.check_book(job, "4100000101", item(book_id=self.book_id), str(self.folder), 24)
        self.assertLess(len(asked), 10)
        release.assert_called_once()
        self.assertEqual((tc.run._active, tc._runs), (0, {}))

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
        journal = sorted(tc.CHECKS.glob("*_4100000101-1.json"))
        self.assertTrue(journal)
        self.assertNotIn("key", json.loads(journal[-1].read_text(encoding="utf-8"))["pages"][0].get("prompt", ""))

    def test_a_template_unlike_the_passport_can_teach_it(self):
        self.printed["Cover.png|front"] = "Sweet Dreams\ndear Olivia"          # the Canva cover says it otherwise
        res = self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        cover = next(p for p in res["pages"] if p["key"] == "cover")
        self.assertEqual((cover["learn"], cover["text"]), ("cover", "Sweet Dreams\ndear Olivia"))
        self.assertTrue(all(i["kind"] == "diff" for i in res["issues"] if i["page"] == 0))

    def test_another_books_pages_raise_one_alarm(self):
        """21.09.2026 the owner laid out a book from the order's other book's Canva template: eleven amber rows then.
        Now one alarm, at once (the read pass already knows), naming the book the pages come from, and the passport
        can never be «updated» from them."""
        words = ("Red", "Blue", "Green", "Tall", "Small", "Old", "New", "Slow", "Fast", "Wide", "Proud", "Shy", "Bright", "Quiet")
        other = {"id": "b" * 32, "schema": 1, "rev": 0, "title": "Boats", "listing": {"id": "4100000901"},
                 "slots": library._empty_slots(), "cover": None, "thumbnail": None,
                 "text": {f"spread{n}": f"{w} boats sail across the bay,\nripples dancing all the day.\n{{Name}} counts them in a row."
                          for n, w in zip(STORY, words)}}
        library.save(other)
        refs = {fill(v, gifter="Grandma & Grandpa"): k for k, v in TEXTS.items()}
        try:
            for name, text in list(self.printed.items()):
                key = refs.get(text.replace("Ollivia", "Olivia"))
                if key and key.startswith("spread"):
                    self.printed[name] = fill(other["text"][key])
            res = self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        finally:
            shutil.rmtree(library._book_dir(other["id"]))  # the whole book, or later tests hear of a broken one
        alarms = [i for i in res["issues"] if i["kind"] == "book"]
        self.assertEqual(len(alarms), 1)
        self.assertEqual((alarms[0]["level"], alarms[0]["like"]["id"], len(alarms[0]["pages"])), ("error", other["id"], 11))
        self.assertFalse([i for i in res["issues"] if i["kind"] in ("unmatched", "model")])
        self.assertFalse(any(p["learn"] for p in res["pages"]))
        self.assertTrue(any(i["kind"] == "book" for i in self.shared[0]["issues"]), "the card hears it with the first page")

    def test_a_second_check_of_the_same_files_is_instant(self):
        self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        first = self.calls
        self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        self.assertEqual(self.calls, first)

    def test_a_broken_answer_is_asked_again_next_time(self):
        """Audit 26.09.2026: an answer cut off by the model was kept, so ↻ never asked that page again — «Сторінку не
        вдалося перевірити» stayed until the program was restarted."""
        broken = {"7.png|None"}

        def chat(model, prompt, picture, schema=None, max_tokens=None):
            if schema is not None and picture in broken:
                self.calls += 1
                return '{"transcript": "cut off here'
            return real(model, prompt, picture, schema, max_tokens)
        real = self.fake_chat
        self.fake_chat = chat
        try:
            res = self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        finally:
            self.fake_chat = real
        failed = lambda res: [i for i in res["issues"] if "не вдалося перевірити" in i["text"]]
        self.assertEqual(len(failed(res)), 1)
        before = self.calls
        res = self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        self.assertEqual(self.calls, before + 1)                   # only that page is asked again …
        self.assertEqual(failed(res), [])                            # … and now it is read

    def test_a_copy_that_came_through_whole_is_kept_from_a_runaway_answer(self):
        """ollama#15502: the model copies a correct page, then apologises until JUDGE_TOKENS cuts it. The copy is kept
        and the program's comparison decides (06.10.2026); a copy cut inside stays «не вдалося перевірити»."""
        runaway = '{"transcript": "Wave hello,\\nsweet \\"Olivia\\".", "verdict": "error", "problems": ["Вибачте, ' + "вибачте, " * 50
        self.assertEqual(tc.run._parse(runaway), {"transcript": 'Wave hello,\nsweet "Olivia".', "verdict": None,
                                                  "problems": [], "only_punctuation": None, "salvaged": True})
        self.assertIn("failed", tc.run._parse('{"transcript": "Wave hello, sweet Oli'))
        self.assertIn("failed", tc.run._parse('{"verdict": "error", "problems": ["x'))
        target = {"page": 5, "part": None, "file": "5.png", "label": "Стор. 5", "count": 24, "mode": "strict",
                  "expected": 'Wave hello, sweet "Olivia".'}
        pers = {"child": "Olivia", "gifter": "", "dedication": None, "closing": None}
        self.assertEqual(tc.page_issues(target, tc.run._parse(runaway), pers, set(tc.COMMON), set()), [])

    def test_a_page_that_timed_out_is_not_asked_twice(self):
        asked = []

        def chat(model, prompt, picture, schema=None, max_tokens=None):
            if schema is not None and picture == "7.png|None":
                asked.append(picture)
                raise tc.TimedOut("Модель не відповіла вчасно.")
            return real(model, prompt, picture, schema, max_tokens)
        real = self.fake_chat
        self.fake_chat = chat
        try:
            res = self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        finally:
            self.fake_chat = real
        self.assertEqual(asked, ["7.png|None"])
        self.assertTrue(any("не вдалося перевірити" in i["text"] for i in res["issues"]))

    def test_a_re_check_answered_from_memory_never_loads_the_model(self):
        """Audit 26.09.2026: every ↻ loaded 9 GB into the graphics card first (~4 s, up to ~70 s), answers cached or not."""
        self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        self.assertEqual(self.ready.call_count, 1)
        self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        self.assertEqual(self.ready.call_count, 1)                    # nothing to ask: no model needed

    def test_a_model_that_cannot_be_had_is_the_checks_error(self):
        job = self.fake_job()
        missing = tc.ModelError("В Ollama немає моделі gemma — встановіть її або оберіть іншу в Налаштуваннях.")
        with mock.patch.object(tc.ollama, "_ready", side_effect=missing), mock.patch.object(tc.ollama, "_chat") as chat,                 mock.patch.object(tc.ollama, "_release_model"), self.assertRaises(tc.Unavailable) as caught:
            tc.check_book(job, "4100000101", item(book_id=self.book_id), str(self.folder), 24)
        self.assertIn("немає моделі", str(caught.exception))
        chat.assert_not_called()

    def test_the_same_book_dropped_again_asks_only_about_the_changed_page(self):
        """Every drop copies the files into a new folder: answers are kept by content, not by folder."""
        self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        first = self.calls
        again = Path(self.tmp.name) / "dropped-again"
        shutil.copytree(self.folder, again)
        Image.new("RGB", (40, 40), (200, 1, 1)).save(again / "7.png")     # the one page fixed in Canva
        self.folder = again
        self.run_check(item(gifter="Grandma & Grandpa", book_id=self.book_id))
        self.assertLessEqual(self.calls - first, 2)                    # its read and its check, nothing else

    def test_light_check_without_library_texts(self):
        res = self.run_check(item(gifter="Grandma & Grandpa"))
        self.assertEqual((res["mode"], res["light"]), ("light", "noBook"))
        texts = [i["text"] for i in res["issues"]]
        self.assertIn("Залишився шаблон «{Name}»", texts)
        self.assertIn("«Ollivia» замість «Olivia»", texts)
        self.assertFalse([t for t in texts if "розвороті немає тексту" in t])


class AnotherBookByPosition(unittest.TestCase):
    """A 30-page book is matched to its passport by position, so another book's pages show as pages with another
    text altogether: half the spreads or more — one alarm; a couple — just their rows."""

    def check(self, unlike: int) -> list[dict]:
        pers = {"child": "Olivia", "gifter": "Grandma", "dedication": None, "closing": None}
        targets, answers = [], {}
        for k, n in enumerate(STORY):
            expected = fill(STORY[n])
            printed = "Seven small boats go sailing far across the silver sea tonight with lanterns lit." if k < unlike else expected
            targets.append({"page": 2 * k + 2, "part": None, "file": f"{2 * k + 2}.png", "label": f"Стор. {2 * k + 2}",
                            "count": 30, "key": f"spread{n}", "mode": "strict", "expected": expected})
            answers[k] = {"transcript": printed, "verdict": "error" if k < unlike else "ok", "problems": []}
        layout = {"blank": [], "unmatched": [], "mapping": {}}
        files = {t["page"]: Path(t["file"]) for t in targets}
        return tc._all_issues(targets, answers, layout, files, pers, 30, (set(tc.COMMON), set()))

    def test_half_the_book_unlike_its_passport(self):
        issues = self.check(8)
        self.assertEqual([(i["kind"], len(i["pages"])) for i in issues], [("book", 8)])

    def test_a_couple_of_pages_are_just_rows(self):
        self.assertEqual([i["text"] for i in self.check(2)], ["Текст сторінки інший, ніж у паспорті книги"] * 2)


class OwnerMarks(unittest.TestCase):
    """«Це не помилка» goes into that check's journal, next to the model's own verdict on every page, so the
    next calibration is made on the owner's answers (25.09.2026)."""

    def test_a_mark_is_kept_in_the_checks_journal(self):
        result = {"pages": [{"page": 1, "text": "Dear Olivia"}],
                  "issues": [{"id": "0123456789ab", "text": "Двічі «Dear Olivia»", "label": "Стор. 1", "page": 1}]}
        name = tc._journal("4100000110", result, {"child": "Olivia"}, 0,
                           {0: {"transcript": "Dear Olivia", "verdict": "error", "problems": ["x"], "only_punctuation": False}},
                           {"unmatched": [5], "blank": []})
        saved = json.loads((tc.CHECKS / name).read_text(encoding="utf-8"))
        self.assertEqual(saved["pages"][0]["model"], {"verdict": "error", "problems": ["x"], "onlyPunctuation": False})
        self.assertEqual(saved["layout"], {"unmatched": [5], "blank": []})
        self.assertEqual(tc._mark(SimpleNamespace(json={"journal": name, "id": "0123456789ab"})), {"kept": True})
        self.assertTrue(tc.mark(name, "0123456789ab"))          # twice: kept once
        saved = json.loads((tc.CHECKS / name).read_text(encoding="utf-8"))
        self.assertEqual([m["text"] for m in saved["notMistakes"]], ["Двічі «Dear Olivia»"])
        self.assertFalse(tc.mark(name, "ffffffffffff"))          # no such finding
        self.assertFalse(tc.mark("../../settings.json", "0123456789ab"))
        self.assertFalse(tc.mark(name.replace(".json", ".txt"), "0123456789ab"))


class Replay(unittest.TestCase):
    """app/tools/textcheck_replay.py: a past check shown again through today's rules."""

    def test_an_old_journal_is_replayed(self):
        spec = importlib.util.spec_from_file_location("textcheck_replay", Path(__file__).resolve().parents[1] / "tools" / "textcheck_replay.py")
        replay = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(replay)
        page = {"page": 5, "part": None, "file": "5.png", "label": "Стор. 5", "key": "spread5", "mode": "strict",
                "expected": "The savior baby came.\nWave hello, sweet Olivia's.", "text": "The Savior baby came.\nWave hello, sweet Olivia."}
        journal = {"receiptId": "4100000111", "bookId": None,
                   "personalization": {"child": "Olivia's", "gifter": "", "dedication": None, "closing": None},
                   "pages": [page, {"page": 24, "part": None, "file": "24.png", "label": "Стор. 24", "key": None,
                                    "mode": "loose", "expected": None, "text": "Sweet dreams, Olivia"}],
                   "issues": [{"id": "a" * 12, "page": 5, "part": None, "label": "Стор. 5", "level": "error", "kind": "diff",
                               "text": "«Savior» замість «savior»", "note": "Слово з великої літери"},
                              {"id": "b" * 12, "page": 5, "part": None, "label": "Стор. 5", "level": "error", "kind": "diff",
                               "text": "«Olivia» замість «Olivia's»"}]}
        self.assertEqual(replay.replay(journal), [])   # the name read right, the template's capitals no mistake
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "2026-01-01_000000_4100000111-1.json").write_text(json.dumps(journal), encoding="utf-8")
            out = io.StringIO()
            with mock.patch.object(tc, "CHECKS", Path(folder)), mock.patch("sys.stdout", out):
                replay.main([])
        self.assertIn("checks: 1 · then: 2 · now: 0 · red then: 2 · red now: 0", out.getvalue())


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
        with self.assertRaises(Exception):
            library.update_texts(book_id, {"notes": "x"})
        for bad in ({"key": "page1", "text": "Dear Jasper"}, {"key": "cover", "text": ""}):  # the owner's own pages stay his
            with self.subTest(bad=bad), self.assertRaises(Exception):
                tc._passport(SimpleNamespace(json={"bookId": book_id, "child": "Jasper", "pages": [bad]}))

    def test_the_name_inside_other_words_stays(self):
        """22.09.2026 audit: «Eve» turned «Every» into «{Name}ry» and the passport kept it."""
        for child, printed, kept in (
                ("Eve", "Every night, Eve counts the stars. Never forget, Eve.",
                 "Every night, {Name} counts the stars. Never forget, {Name}."),
                ("Ian", "A giant hug for Ian.", "A giant hug for {Name}."),
                ("Leo", "Leo met a leopard.", "{Name} met a leopard."),
                ("Ann", "Ann planned a picnic with Joanna.", "{Name} planned a picnic with Joanna."),
                ("Leo & Mila", "Leo & Mila went out.", "{Name} went out.")):
            with self.subTest(child=child):
                self.assertEqual(tc.as_template(printed, child), kept)

    def test_a_name_that_is_also_a_word_follows_the_passport(self):
        """«Hope» the girl becomes {Name} where the passport had {Name}; «hope» the passport's own word stays."""
        self.assertEqual(tc.as_template("Hope never lost hope.\nHope smiled.", "Hope", "{Name} never lost hope."),
                         "{Name} never lost hope.\n{Name} smiled.")
        self.assertEqual(tc.as_template("Grace sang. By grace, Grace flew.", "Grace", "{Name} sang. By grace, {Name} flew."),
                         "{Name} sang. By grace, {Name} flew.")
        self.assertEqual(tc.as_template("Grace sang with grace.", "Grace", "{Name} sang."),
                         "{Name} sang with grace.")  # a new line: the everyday word stays a word

    def test_the_owner_sees_the_texts_before_they_are_kept(self):
        book_id = "c" * 32
        library.save({"id": book_id, "schema": 1, "rev": 0, "title": "Stars", "listing": {"id": "4100000902"},
                      "slots": library._empty_slots(), "text": {**TEXTS, "spread3": "Every night, {Name} counts."},
                      "cover": None, "thumbnail": None})
        body = {"bookId": book_id, "child": "Eve", "pages": [{"key": "spread3", "text": "Every night, Eve counts stars."}]}
        res = tc._passport(SimpleNamespace(json={**body, "preview": True}))
        self.assertEqual(res, {"texts": {"spread3": "Every night, {Name} counts stars."}})
        self.assertEqual(library.load(book_id)["text"]["spread3"], "Every night, {Name} counts.")  # nothing saved yet
        tc._passport(SimpleNamespace(json=body))
        self.assertEqual(library.load(book_id)["text"]["spread3"], "Every night, {Name} counts stars.")


class WhileItRuns(unittest.TestCase):
    """A 30-page book, as long as the library passport: every spread is checked the moment its own two
    pages are read, and the findings reach the card while the rest of the book is still with the model."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name) / "print"
        self.folder.mkdir()
        self.book_id = "c" * 32
        library.save({"id": self.book_id, "schema": 1, "rev": 0, "title": "Planes", "listing": {"id": "4100000902"},
                      "slots": library._empty_slots(), "text": dict(TEXTS), "cover": None, "thumbnail": None})
        refs = {k: fill(v, gifter="Grandma & Grandpa") for k, v in TEXTS.items()}
        self.printed = {"Cover.png|front": refs["cover"], "Cover.png|back": "",
                        "1.png|None": refs["page1"], "30.png|None": refs["page30"]}
        for k, n in enumerate(STORY, 1):  # spread k holds pages 2k and 2k+1; the text is on one of them
            text_page, picture_page = (2 * k, 2 * k + 1) if k % 2 == 0 else (2 * k + 1, 2 * k)
            text = refs[f"spread{n}"]
            if n == 7:
                text = text.replace("Olivia", "Ollivia")                                 # a misspelt name
            self.printed[f"{text_page}.png|None"] = text
            self.printed[f"{picture_page}.png|None"] = ""
        Image.new("RGB", (60, 30)).save(self.folder / "Cover.png")
        for n in range(1, 31):  # each page its own pixels: answers are kept by a file's content
            Image.new("RGB", (40, 40), (n, 0, 0)).save(self.folder / f"{n}.png")
        self.asked = []
        self.lock = threading.Lock()
        tc._cache.clear()
        core.settings.update({"textcheck": {"prescan": False}})  # these pages are blank squares

    def tearDown(self):
        core.settings.update({"textcheck": {"prescan": True}})
        self.tmp.cleanup()

    def fake_chat(self, model, prompt, picture, schema=None, max_tokens=None):
        with self.lock:
            self.asked.append(("check" if schema else "read", picture))
        time.sleep(0.02 if schema else 0.005)   # a check takes longer than a read, as it does with Gemma
        return gemma_answer(self.printed.get(picture, ""), prompt, schema)

    def test_spreads_are_checked_before_the_last_page_is_read(self):
        shared = []
        job = SimpleNamespace(id="job1", progress=lambda *a, **k: None, share=shared.append)
        with mock.patch.object(tc.ollama, "_ready"), mock.patch.object(tc.ollama, "_chat", side_effect=self.fake_chat), \
                mock.patch.object(tc.run, "picture", side_effect=lambda path, part=None: f"{path.name}|{part}"), \
                mock.patch.object(tc.run, "_other_children", return_value=set()), \
                mock.patch.object(tc.ollama, "_release_model"):
            res = tc.check_book(job, "4100000102", item(book_id=self.book_id), str(self.folder), 30)
        kinds = [kind for kind, _ in self.asked]
        story_check = next(i for i, (kind, pic) in enumerate(self.asked)
                           if kind == "check" and pic not in ("Cover.png|front", "1.png|None", "30.png|None"))
        self.assertLess(story_check, len(kinds) - 1 - kinds[::-1].index("read"))  # before the last read
        self.assertEqual(res["mode"], "full")
        self.assertEqual([i["text"] for i in res["issues"]], ["«Ollivia» замість «Olivia»"])
        self.assertTrue(shared, "the check shares its findings while it runs")
        self.assertTrue(any(s["issues"] for s in shared[:-1]), "a mistake reaches the card before the end")
        self.assertEqual([i["id"] for i in shared[-1]["issues"]], [i["id"] for i in res["issues"]])


class BooksOfOneOrder(unittest.TestCase):
    """Two books of one order are two checks: starting the second must not stop the first (the card says
    a hidden book's check carries on). Only a new check of the same book replaces it."""

    def job(self, job_id):
        return SimpleNamespace(id=job_id, progress=lambda *a, **k: None, share=lambda data: None)

    def test_a_second_book_does_not_stop_the_first(self):
        with mock.patch.object(tc.ollama, "_release_model"):
            with tc._Run(self.job("job1"), "4100000108", "m", 0) as first:
                with tc._Run(self.job("job2"), "4100000108", "m", 1) as second:
                    self.assertFalse(first.cancel.is_set(), "book 1 keeps checking while book 2 starts")
                    self.assertEqual(sorted(tc._runs), ["4100000108#0", "4100000108#1"])
                    self.assertTrue(tc.cancel("4100000108", "job2"))      # only the job that was named
                    self.assertTrue(second.cancel.is_set())
                    self.assertFalse(first.cancel.is_set())
        self.assertEqual(tc._runs, {})

    def test_the_same_book_again_stops_the_older_check(self):
        with mock.patch.object(tc.ollama, "_release_model"):
            with tc._Run(self.job("job1"), "4100000108", "m", 1) as older:
                with tc._Run(self.job("job2"), "4100000108", "m", 1):
                    self.assertTrue(older.cancel.is_set())
        self.assertEqual(tc._runs, {})

    def test_closing_the_card_stops_every_book(self):
        with mock.patch.object(tc.ollama, "_release_model"):
            with tc._Run(self.job("job1"), "4100000108", "m", 0) as first, \
                    tc._Run(self.job("job2"), "4100000108", "m", 1) as second, \
                    tc._Run(self.job("job3"), "4100000109", "m", 0) as other_order:
                self.assertTrue(tc.cancel("4100000108"))                  # no job named: the whole card
                self.assertTrue(first.cancel.is_set() and second.cancel.is_set())
                self.assertFalse(other_order.cancel.is_set())
        self.assertFalse(tc.cancel("4100000108"))                         # nothing left to stop

    def test_each_book_writes_its_own_journal(self):
        tc._journal("4100000108", {"issues": []}, {"child": "Sofia"}, 0)
        tc._journal("4100000108", {"issues": []}, {"child": "Jack"}, 1)
        names = sorted(p.name.split("_")[-1] for p in tc.CHECKS.glob("*_4100000108-*.json"))
        self.assertEqual(names, ["4100000108-1.json", "4100000108-2.json"])


class Prescan(unittest.TestCase):
    """A local look at the pages before the model: drawn text against a drawn illustration, and a whole
    book where only the pages that may carry text are ever sent to Gemma."""

    SIZE = 600

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name) / "print"
        self.folder.mkdir()
        tc._cache.clear()

    def tearDown(self):
        core.settings.update({"textcheck": {"prescan": True}})
        self.tmp.cleanup()

    def draw(self, path, lines=0):
        """A page of a children's book: shapes everywhere, and `lines` rows of words on top."""
        size = self.SIZE
        im = Image.new("RGB", (size, size), (238, 230, 214))
        d = ImageDraw.Draw(im)
        rnd = random.Random(3 if not lines else 7)
        for _ in range(120 if not lines else 60):
            x, y = rnd.randrange(size), rnd.randrange(size)
            d.ellipse([x, y, x + rnd.randrange(30, 190), y + rnd.randrange(30, 190)],
                      fill=(rnd.randrange(80, 220), rnd.randrange(90, 220), rnd.randrange(70, 200)))
        for n in range(lines):
            y, x = size * 0.30 + n * size * 0.06, size * 0.18
            for w in (0.10, 0.06, 0.13, 0.08):
                d.rectangle([x, y, x + size * w, y + size * 0.028], fill=(40, 30, 25))
                x += size * (w + 0.02)
        mark = zlib.crc32(path.name.encode())
        im.putpixel((0, 0), (mark & 255, mark >> 8 & 255, mark >> 16 & 255))  # its own content, like every real page
        im.save(path)

    def test_text_and_picture_pages_are_told_apart(self):
        text, picture = self.folder / "t.png", self.folder / "p.png"
        self.draw(text, lines=4)
        self.draw(picture)
        self.assertGreaterEqual(images.text_score(text), tc.LOOKS_TEXT)
        self.assertLess(images.text_score(picture), tc.LOOKS_PICTURE)

    def book(self, slips=()):
        """A 30-page book with text on one page of every spread, as the owner's books are."""
        library.save({"id": "d" * 32, "schema": 1, "rev": 0, "title": "Planes", "listing": {"id": "4100000903"},
                      "slots": library._empty_slots(), "text": dict(TEXTS), "cover": None, "thumbnail": None})
        refs = {k: fill(v, gifter="Grandma & Grandpa") for k, v in TEXTS.items()}
        printed = {"Cover.png|front": refs["cover"], "Cover.png|back": "",
                   "1.png|None": refs["page1"], "30.png|None": refs["page30"]}
        self.draw(self.folder / "Cover.png", lines=2)
        self.text_pages = []
        for k, n in enumerate(STORY, 1):
            text_page, picture_page = (2 * k, 2 * k + 1) if k % 2 == 0 else (2 * k + 1, 2 * k)
            self.text_pages.append(text_page)
            printed[f"{text_page}.png|None"] = refs[f"spread{n}"].replace("Olivia", "Ollivia") if n in slips else refs[f"spread{n}"]
            self.draw(self.folder / f"{text_page}.png", lines=3)
            self.draw(self.folder / f"{picture_page}.png")
        for n in (1, 30):
            self.draw(self.folder / f"{n}.png", lines=3)
        self.printed = printed

    def run_check(self, chat=None):
        self.asked = []
        job = SimpleNamespace(id="job1", progress=lambda *a, **k: None, share=lambda data: None)

        def fake_chat(model, prompt, picture, schema=None, max_tokens=None):
            self.asked.append((picture, bool(schema)))
            text = self.printed.get(picture, "")
            return gemma_answer(chat(picture, text) if chat else text, prompt, schema)

        with mock.patch.object(tc.ollama, "_ready"), mock.patch.object(tc.ollama, "_chat", side_effect=fake_chat), \
                mock.patch.object(tc.run, "picture", side_effect=lambda path, part=None: f"{path.name}|{part}"), \
                mock.patch.object(tc.run, "_other_children", return_value=set()), \
                mock.patch.object(tc.ollama, "_release_model"):
            return tc.check_book(job, "4100000103", item(book_id="d" * 32), str(self.folder), 30)

    def test_only_pages_that_may_carry_text_reach_the_model(self):
        """The picture half of every spread is never sent; the read pass disappears altogether, because the
        passport says what each spread must carry — and a mistake is still found."""
        self.book(slips={7})
        res = self.run_check()
        seen = {name for name, _ in self.asked}
        for page in range(2, 30):
            if page not in self.text_pages:
                self.assertNotIn(f"{page}.png|None", seen, f"сторінку-малюнок {page} не треба показувати моделі")
        self.assertFalse([1 for _, judged in self.asked if not judged and "Cover" not in _],
                         "читання сторінок більше не потрібне")
        self.assertEqual([i["text"] for i in res["issues"]], ["«Ollivia» замість «Olivia»"])
        self.assertLessEqual(len(self.asked), 20)

    def test_the_other_half_is_checked_when_the_guess_was_wrong(self):
        """The local look pointed at the wrong half of a spread (the model sees nothing there): the check
        moves to the other page instead of crying about a missing text."""
        self.book()
        wrong = self.text_pages[3]

        def blind(picture, text):
            return "" if picture == f"{wrong}.png|None" else text

        res = self.run_check(chat=blind)
        other = wrong + 1 if wrong % 2 == 0 else wrong - 1
        self.assertIn(f"{other}.png|None", {name for name, _ in self.asked}, "друга половина розвороту перевірена")
        self.assertEqual([i["text"] for i in res["issues"] if i["page"] == wrong], [])

    def test_switched_off_it_is_the_old_check(self):
        core.settings.update({"textcheck": {"prescan": False}})
        self.book()
        self.run_check()
        reads = [name for name, judged in self.asked if not judged]
        self.assertGreaterEqual(len(reads), 28)   # every story page read again, as before


class OllamaAndRoutes(unittest.TestCase):
    def test_only_this_computer(self):
        with mock.patch.object(core.settings, "section", return_value={"url": "http://192.168.1.5:11434"}):
            with self.assertRaises(tc.ModelError):
                tc._base()
        with mock.patch.object(core.settings, "section", return_value={"url": "http://example.com"}),                 mock.patch.object(tc._NO_PROXY, "open", side_effect=AssertionError("no request may leave")):
            self.assertFalse(tc.status()["running"])

    def test_ollama_down_is_said_plainly(self):
        with mock.patch.object(tc.ollama, "_alive", return_value=False), mock.patch.object(tc.ollama, "start_ollama", return_value=False):
            with self.assertRaises(tc.Unavailable) as err:
                tc._ready("gemma", lambda step: None)
        self.assertIn("Ollama", str(err.exception))

    def test_ollama_starts_quietly_without_the_model(self):
        with mock.patch.object(tc.run, "START_DELAY", 0), mock.patch.object(tc.ollama, "start_ollama", return_value=True) as start, \
                mock.patch.object(tc.ollama, "_call", side_effect=AssertionError("no model is asked for at the start")):
            with mock.patch.object(core, "SANDBOX", True):
                tc.run.start_quietly()
                self.assertFalse(tc.warm())            # nor a warm-up from an opened card
            start.assert_not_called()                  # made-up or test data (the preview, tests): never the PC's real Ollama
            with mock.patch.object(core, "SANDBOX", False), mock.patch("studio.portable.root", return_value=None):
                tc.run.start_quietly()
            start.assert_called_once_with(hidden=True)
            core.settings.update({"textcheck": {"enabled": False}})
            try:
                tc.run.start_quietly()
            finally:
                core.settings.update({"textcheck": {"enabled": True}})
            start.assert_called_once()                 # switched off in Settings: Ollama is left alone

    def test_test_data_never_starts_the_real_ollama(self):
        with mock.patch.object(tc.ollama, "_alive", return_value=False), \
                mock.patch.object(tc.ollama.subprocess, "Popen", side_effect=AssertionError("Ollama may not be started")):
            self.assertTrue(core.SANDBOX)              # the tests' own data folder
            self.assertFalse(tc.start_ollama())
            with self.assertRaises(tc.Unavailable):
                tc._ready("gemma", lambda step: None)

    def test_the_hidden_start_never_opens_the_tray_app(self):
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, folder, True)
        for name in ("ollama app.exe", "ollama.exe"):
            (folder / name).write_bytes(b"")
        with mock.patch("studio.portable.root", return_value=None), mock.patch("studio.portable.ollama_folder", return_value=folder), \
                mock.patch.object(tc.ollama.shutil, "which", return_value=None):
            self.assertEqual(tc.ollama._ollama_command(), [str(folder / "ollama app.exe")])
            self.assertEqual(tc.ollama._ollama_command(hidden=True), [str(folder / "ollama.exe"), "serve"])

    def test_missing_model(self):
        with mock.patch.object(tc.ollama, "_alive", return_value=True), \
                mock.patch.object(tc.ollama, "_call", return_value={"models": [{"name": "other:1b"}]}):
            with self.assertRaises(tc.ModelError) as err:
                tc._ready("gemma4:12b-it-qat", lambda step: None)
        self.assertIn("gemma4:12b-it-qat", str(err.exception))

    def test_switched_off_and_settings(self):
        core.settings.update({"textcheck": {"enabled": False}})
        try:
            self.assertEqual(tc._check(SimpleNamespace(groups=["4100000101"], json={"folder": "x", "pages": 24})), {"off": True})
        finally:
            core.settings.update({"textcheck": {"enabled": True}})
        with mock.patch.object(tc.ollama, "status", return_value={}):
            tc._save_settings(SimpleNamespace(json={"model": "gemma4:12b-it-qat"}))
            with self.assertRaises(Exception):
                tc._save_settings(SimpleNamespace(json={"model": "bad model; rm"}))

    def test_a_check_needs_the_order(self):
        with mock.patch("studio.stages.picker_order", return_value=None):
            with self.assertRaises(UserError):
                tc.check_order(SimpleNamespace(progress=lambda *a, **k: None, share=lambda data: None),
                               "4100000101", "x", 24)


if __name__ == "__main__":
    unittest.main()
