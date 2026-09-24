"""The Workshop (the Listings mode): books in development — a title is enough, prompts beside the texts, one JSON
for both, and «Передати в бібліотеку»; a Workshop book never reaches the orders."""
import json
import re
import shutil
import unittest
from types import SimpleNamespace

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import library, orders, workshop
from studio.server import ApiError

# Made-up listing numbers of their own: the other tests' library books live in the same temporary folder.
LISTING, TAKEN = "4100000951", "4100000952"


def request(book_id: str = "", body: dict | None = None, **params) -> SimpleNamespace:
    return SimpleNamespace(groups=[book_id], json=body or {}, param=lambda name: params.get(name))


def workshop_json(**changes) -> str:
    data = {"cover": {"prompt": "A wide cover", "text": "Silly Goose\nfor {Name}"},
            "page1": {"prompt": "A nest", "text": "Dear {Name},\nwith love,\n{Gifter}"},
            "spreads": {str(n): {"prompt": f"Spread {n}, 2:1", "text": f"Page text {n}"} for n in library.SPREAD_NUMBERS},
            "page30": {"prompt": "Stars", "text": "Goodnight, {Name}"}}
    data.update(changes)
    return json.dumps(data)


class WorkshopTestCase(unittest.TestCase):
    def setUp(self):
        self.made: list[str] = []

    def tearDown(self):
        for book_id in self.made:
            shutil.rmtree(library._book_dir(book_id), ignore_errors=True)

    def new_book(self, title: str = "Silly Goose") -> dict:
        book = workshop.create(title)
        self.made.append(book["id"])
        return book

    def library_book(self, listing_id: str) -> dict:
        book_id = library.core.new_id()
        library._book_dir(book_id).mkdir(parents=True)
        library.save({"id": book_id, "schema": 1, "rev": 0, "title": "Already on sale", "listing": {"id": listing_id},
                      "slots": library._empty_slots(), "text": {k: "" for k in library.TEXT_KEYS},
                      "cover": None, "thumbnail": None, "archived": False})
        self.made.append(book_id)
        return library.load(book_id)


class ANewBook(WorkshopTestCase):
    def test_a_title_is_all_it_needs(self):
        book = self.new_book("  Silly Goose  ")
        self.assertEqual(book["title"], "Silly Goose")
        self.assertEqual(book["stage"], library.WORKSHOP)
        self.assertEqual(book["listing"], {})
        self.assertEqual(sorted(book["prompts"]), sorted(library.PROMPT_KEYS))
        with self.assertRaises(ApiError):
            workshop.create("   ")

    def test_it_never_reaches_the_orders(self):
        book = self.new_book()
        on_sale = self.library_book(TAKEN)
        in_library = {b["id"] for b in library.all_books()}
        self.assertNotIn(book["id"], in_library)                        # orders, the book counter, the text check
        self.assertIn(on_sale["id"], in_library)
        self.assertEqual([b["id"] for b in library.all_books(library.WORKSHOP)], [book["id"]])
        self.assertNotIn(book["id"], {b["id"] for b in library._list(request())["books"]})
        shown = library._list(request(stage="workshop"))["books"]
        self.assertEqual([(b["id"], b["stage"]) for b in shown], [(book["id"], library.WORKSHOP)])
        self.assertIn(TAKEN, orders.books_by_listing())

    def test_a_library_book_gains_no_prompts(self):
        on_sale = self.library_book(TAKEN)
        self.assertNotIn("prompts", on_sale)
        library._patch(request(on_sale["id"], {"prompts": {"cover": "x"}}))
        self.assertNotIn("prompts", library.load(on_sale["id"]))
        self.assertEqual(library.summary(on_sale)["stage"], "library")

    def test_the_card_shows_the_first_spread_until_there_is_a_cover(self):
        book = self.new_book()
        picture = {"id": "a" * 32, "file": "a" * 32 + ".png", "width": 1600, "height": 800, "lqip": ""}
        book["slots"]["spread3"]["image"] = picture
        library.save(book)
        card = library.summary(library.load(book["id"]))
        self.assertEqual(card["image"], picture["file"])
        c = card["completeness"]
        self.assertEqual((c["pictures"], c["picturesTotal"], c["promptsTotal"]), (1, 17, 17))


class PromptsAndTexts(WorkshopTestCase):
    def test_a_prompt_is_saved_like_a_text(self):
        book = self.new_book()
        saved = library._patch(request(book["id"], {"rev": book["rev"], "prompts": {"spread2": "A gosling wakes", "nope": "x"},
                                                    "text": {"spread2": "Morning sun"}}))
        self.assertEqual(saved["prompts"]["spread2"], "A gosling wakes")
        self.assertNotIn("nope", saved["prompts"])
        self.assertEqual(saved["completeness"]["prompts"], 1)
        with self.assertRaises(ApiError):                                # the other window's revision
            library._patch(request(book["id"], {"rev": book["rev"], "prompts": {"cover": "late"}}))

    def test_one_json_fills_every_prompt_and_text(self):
        book = self.new_book()
        res = workshop.import_json(book["id"], workshop_json())
        self.assertEqual((res["prompts"], res["texts"]), (17, 17))
        self.assertEqual(res["missing"], {"prompts": [], "texts": []})
        saved = library.load(book["id"])
        self.assertEqual(saved["prompts"]["spread15"], "Spread 15, 2:1")
        self.assertEqual(saved["text"]["page1"], "Dear {Name},\nwith love,\n{Gifter}")
        # read back: the book's own JSON is the same thing
        self.assertEqual(json.loads(workshop_json()), library.export_book_json(saved))

    def test_what_is_missing_is_said_and_the_rest_taken(self):
        book = self.new_book()
        raw = workshop_json(cover={"text": "Only a title"}, page30="The library's old way: a text alone")
        res = workshop.import_json(book["id"], raw)
        self.assertEqual(res["missing"]["prompts"], ["«cover»", "«page30»"])
        self.assertEqual(res["missing"]["texts"], [])
        self.assertEqual(library.load(book["id"])["text"]["page30"], "The library's old way: a text alone")
        with self.assertRaises(ApiError):
            workshop.import_json(book["id"], json.dumps({"cover": {}, "spreads": {}}))  # nothing at all in it

    def test_a_dry_run_counts_what_would_be_replaced_and_writes_nothing(self):
        book = self.new_book()
        library._patch(request(book["id"], {"prompts": {"cover": "My own cover prompt", "page1": "A nest"},
                                            "text": {"page30": "My own ending"}}))
        res = workshop.import_json(book["id"], workshop_json(), dry_run=True)
        self.assertEqual(res["replaces"], {"prompts": 1, "texts": 1})    # page1's prompt is the same: not counted
        self.assertNotIn("book", res)
        self.assertEqual(library.load(book["id"])["prompts"]["cover"], "My own cover prompt")

    def test_the_library_import_takes_only_the_texts(self):
        text, problems, _ = library.parse_text_json(workshop_json())
        self.assertEqual(len(text), len(library.TEXT_KEYS))
        self.assertEqual(problems, [])
        self.assertEqual(text["cover"], "Silly Goose\nfor {Name}")

    def test_a_library_book_is_not_filled_from_here(self):
        on_sale = self.library_book(TAKEN)
        with self.assertRaises(ApiError) as caught:
            workshop.import_json(on_sale["id"], workshop_json())
        self.assertEqual(caught.exception.status, 409)

    def test_the_agents_instruction_is_what_the_workshop_reads(self):
        guide = workshop.guide()
        block = re.search(r"```json\n(\{.*?\n\})\n```", guide, re.S).group(1)
        text, prompts, no_text, no_prompt, notes = library.parse_book_json(block)
        self.assertEqual((len(text), len(prompts)), (17, 17))
        self.assertEqual((no_text, no_prompt, notes), ([], [], []))
        for word in ("{Name}", "{Gifter}", "2:1", "лише JSON"):
            self.assertIn(word, guide)


class PassingToTheLibrary(WorkshopTestCase):
    def test_the_book_leaves_the_workshop_with_its_listing(self):
        book = self.new_book()
        workshop.import_json(book["id"], workshop_json())
        passed = workshop._to_library(request(book["id"], {"listingRef": f"https://www.etsy.com/listing/{LISTING}/silly-goose"}))
        self.assertNotIn("stage", passed)
        self.assertEqual(passed["listing"]["id"], LISTING)
        self.assertIn(book["id"], {b["id"] for b in library.all_books()})
        self.assertNotIn(book["id"], {b["id"] for b in library.all_books(library.WORKSHOP)})
        self.assertEqual(orders.books_by_listing()[LISTING]["id"], book["id"])   # orders find it now
        self.assertEqual(library.load(book["id"])["prompts"]["spread2"], "Spread 2, 2:1")  # kept, unseen
        with self.assertRaises(ApiError) as caught:                     # one way: it's in the library now
            workshop._to_library(request(book["id"], {"listingRef": LISTING}))
        self.assertEqual(caught.exception.status, 409)

    def test_a_listing_is_needed(self):
        book = self.new_book()
        with self.assertRaises(ApiError):
            workshop._to_library(request(book["id"], {"listingRef": "not a listing"}))
        self.assertEqual(library.load(book["id"])["stage"], library.WORKSHOP)

    def test_a_listing_another_book_has_is_refused(self):
        book = self.new_book()
        on_sale = self.library_book(TAKEN)
        with self.assertRaises(ApiError) as caught:
            workshop._to_library(request(book["id"], {"listing": {"id": TAKEN, "title": "On Etsy", "verifiedAt": "x"}}))
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(caught.exception.extra["bookId"], on_sale["id"])
        self.assertEqual(library.load(book["id"])["stage"], library.WORKSHOP)


if __name__ == "__main__":
    unittest.main()
