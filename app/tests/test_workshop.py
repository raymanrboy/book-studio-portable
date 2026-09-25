"""The Workshop (the Listings mode): books in development — a title is enough, prompts beside the texts, one JSON
for both, and «Передати в бібліотеку»; a Workshop book never reaches the orders."""
import json
import re
import shutil
import unittest
from pathlib import Path
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


RED, BLUE, GREEN, WHITE = (220, 30, 30), (30, 60, 220), (40, 170, 70), (255, 255, 255)


def panorama(path, size=(800, 400), left=RED, right=BLUE, band=None, edge=0):
    """A made-up spread: the left half one colour, the right half another; `edge` px of `band` colour along the
    sides (a wide picture) or the top and bottom (a narrow one) — what the cut must take away."""
    from PIL import Image, ImageDraw
    w, h = size
    im = Image.new("RGB", size, left)
    d = ImageDraw.Draw(im)
    d.rectangle([w // 2, 0, w, h], fill=right)
    if band and edge:
        if w / h > 2:
            d.rectangle([0, 0, edge - 1, h], fill=band)
            d.rectangle([w - edge, 0, w, h], fill=band)
        else:
            d.rectangle([0, 0, w, edge - 1], fill=band)
            d.rectangle([0, h - edge, w, h], fill=band)
    im.save(path)
    return path


class SpreadsBecomeTwoPages(WorkshopTestCase):
    """A dropped spread: cut to 2:1, mirrored when it's one of the owner's flipper's, cut into two square pages."""

    def setUp(self):
        super().setUp()
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        super().tearDown()
        self.tmp.cleanup()

    def pages(self, book_id, key):
        from PIL import Image
        slot = library.load(book_id)["slots"][key]
        folder = library._book_dir(book_id) / "assets"
        out = []
        for part in ("left", "right"):
            with Image.open(folder / slot[part]["file"]) as im:
                out.append((im.size, im.convert("RGB").getpixel((im.width // 2, im.height // 2)),
                            im.convert("RGB").getpixel((1, 1))))
        return slot, out

    def test_the_flippers_spreads_are_mirrored(self):
        self.assertEqual(sorted(workshop.MIRRORED), [3, 5, 7, 9, 11, 13, 15])  # 4–5, 8–9 … 28–29
        book = self.new_book()
        src = panorama(self.dir / "p.png")
        res = workshop.place_spread(book["id"], "spread2", src, "p.png")          # 2–3: as it is
        self.assertFalse(res["mirrored"])
        slot, ((size_l, l, _), (size_r, r, _)) = self.pages(book["id"], "spread2")
        self.assertEqual((size_l, size_r, l, r), ((400, 400), (400, 400), RED, BLUE))
        self.assertIsNone(slot["image"])
        res = workshop.place_spread(book["id"], "spread3", src, "p.png")          # 4–5: mirrored
        self.assertTrue(res["mirrored"])
        slot, ((_, l, _), (_, r, _)) = self.pages(book["id"], "spread3")
        self.assertEqual((l, r, slot["mirrored"], slot["source"]), (BLUE, RED, True, [800, 400]))
        self.assertEqual(library.completeness(library.load(book["id"]))["pictures"], 2)

    def test_a_wide_picture_loses_its_sides_and_a_narrow_one_its_top_and_bottom(self):
        book = self.new_book()
        wide = panorama(self.dir / "wide.png", (1000, 400), band=GREEN, edge=100)
        res = workshop.place_spread(book["id"], "spread2", wide, "wide.png")
        self.assertEqual(res["cut"], "sides")
        _, ((size, _, corner_l), (_, _, corner_r)) = self.pages(book["id"], "spread2")
        self.assertEqual((size, corner_l, corner_r), ((400, 400), RED, BLUE))   # no green left at the edges
        narrow = panorama(self.dir / "narrow.png", (1792, 1024), band=GREEN, edge=64)
        res = workshop.place_spread(book["id"], "spread4", narrow, "narrow.png")
        self.assertEqual((res["cut"], res["source"]), ("top-bottom", [1792, 1024]))
        _, ((size, _, corner_l), _) = self.pages(book["id"], "spread4")
        self.assertEqual((size, corner_l), ((896, 896), RED))
        exact = panorama(self.dir / "exact.png")
        self.assertEqual(workshop.place_spread(book["id"], "spread6", exact, "exact.png")["cut"], "")

    def test_flip_by_hand_and_back_loses_nothing(self):
        from PIL import Image, ImageChops
        book = self.new_book()
        workshop.place_spread(book["id"], "spread2", panorama(self.dir / "p.png"), "p.png")
        _, before = self.pages(book["id"], "spread2")
        folder = library._book_dir(book["id"]) / "assets"
        first = {p: library.load(book["id"])["slots"]["spread2"][p]["file"] for p in ("left", "right")}
        with Image.open(folder / first["left"]) as im:
            original_left = im.copy()
        shown = workshop._flip(request(book["id"], {"slot": "spread2"}))
        self.assertTrue(shown["slots"]["spread2"]["mirrored"])
        _, ((_, l, _), (_, r, _)) = self.pages(book["id"], "spread2")
        self.assertEqual((l, r), (BLUE, RED))
        self.assertFalse(any((folder / f).exists() for f in first.values()))    # the replaced files are gone
        workshop.flip_spread(book["id"], "spread2")
        slot, after = self.pages(book["id"], "spread2")
        self.assertEqual((after, slot["mirrored"]), (before, False))
        with Image.open(folder / slot["left"]["file"]) as im:
            self.assertIsNone(ImageChops.difference(im.convert("RGB"), original_left.convert("RGB")).getbbox())

    def test_only_spreads_of_a_workshop_book_and_only_pictures(self):
        book = self.new_book()
        src = panorama(self.dir / "p.png")
        for key in ("cover", "page1", "spread16", "spread"):
            with self.assertRaises(ApiError):
                workshop.place_spread(book["id"], key, src, "p.png")
        (self.dir / "notes.png").write_text("not a picture", encoding="utf-8")
        with self.assertRaises(ApiError):
            workshop.place_spread(book["id"], "spread2", self.dir / "notes.png", "notes.png")
        with self.assertRaises(ApiError):                                  # nothing to flip yet
            workshop.flip_spread(book["id"], "spread2")
        on_sale = self.library_book(TAKEN)
        with self.assertRaises(ApiError) as caught:
            workshop.place_spread(on_sale["id"], "spread2", src, "p.png")
        self.assertEqual(caught.exception.status, 409)

    def test_removing_both_pages_forgets_the_notes(self):
        book = self.new_book()
        workshop.place_spread(book["id"], "spread3", panorama(self.dir / "p.png"), "p.png")
        for part in ("left", "right"):
            library._remove_asset(request(book["id"], slot=f"spread3:{part}"))
        self.assertNotIn("mirrored", library.load(book["id"])["slots"]["spread3"])


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
