"""The Canva extension (canva-extension/): its book logic (book.js) reads a book exactly as the Workshop does —
the same text sections as rows.text_sections(), the same text side of a spread as rows.MIRRORED. book.js runs in node;
without node on the PC these tests are skipped (the manifest check still runs)."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from tests import __init__  # noqa: F401  (sets a temporary data folder and the sandbox)
from studio import library
from studio.workshop import rows

EXT = Path(__file__).resolve().parents[2] / "canva-extension"
NODE = shutil.which("node")

BOOK_TEXT = """## Cover — Title
An Angel Watches Over [Name]

## Spread 01 — Dedication
Dear {Name},

There is someone watching over you
in every little thing you do.



With love,
{Gifter}

---

## Spread 02 — Good Morning
Little fawn wakes in the dew,   \r
Good morning, `{Name}`, wake and play.

## Spread 07 — Sharing
Fox and squirrel share a treat.

## Spread 16 — Not in the book
Nothing.

## Afterword — Closing Wishes
Sleep sweet, dear {Name}.

## Text Critic Report
PASS everything
"""


def node(script: str, data) -> object:
    out = subprocess.run([NODE, "-e", script], input=json.dumps(data), capture_output=True, text=True,
                         encoding="utf-8", cwd=EXT, timeout=30)
    if out.returncode:
        raise AssertionError(out.stderr)
    return json.loads(out.stdout)


RUN = """
const B = require('./book.js');
let raw = ''; process.stdin.on('data', d => raw += d).on('end', () => {
  const d = JSON.parse(raw);
  process.stdout.write(JSON.stringify(eval(d.expr)));
});
"""


def js(expr: str, **data):
    return node(RUN, {"expr": expr, **data})


@unittest.skipUnless(NODE, "node is not installed")
class BookLogic(unittest.TestCase):
    def test_text_sections_match_the_workshop(self):
        self.assertEqual(js("B.textSections(d.text)", text=BOOK_TEXT), rows.text_sections(BOOK_TEXT))

    def test_the_real_books_read_the_same(self):
        books = Path(__file__).resolve().parents[2] / "pipeline" / "books"
        texts = sorted(books.glob("*/agent/book-text.md"))[:4]
        if not texts:
            self.skipTest("no books on this PC")
        for path in texts:
            text = path.read_text(encoding="utf-8")
            self.assertEqual(js("B.textSections(d.text)", text=text), rows.text_sections(text), path.parent.parent.name)

    def test_the_text_side_of_every_spread(self):
        got = js("Object.fromEntries([...Array(14)].map((_, i) => [i + 2, B.textPageOf(i + 2, {})]))")
        for n in range(2, 16):
            left, right = library.spread_pages(n)
            self.assertEqual(got[str(n)], left if n in rows.MIRRORED else right, n)
        # ⇄ in the Workshop (book.json) wins over the default
        self.assertEqual(js("B.textPageOf(2, {spread2: {mirrored: true}})"), 2)
        self.assertEqual(js("B.textPageOf(3, {spread3: {mirrored: false}})"), 5)

    def test_the_plan(self):
        plan = js("B.buildPlan(d.pics, B.textSections(d.text), {})",
                  text=BOOK_TEXT, pics={**{str(n): f"{n}.png" for n in range(1, 31) if n != 9}, "cover": "Cover.png"})
        self.assertEqual([p["page"] for p in plan], list(range(1, 32)))
        by = {p["page"]: p for p in plan}
        self.assertIsNone(by[1]["text"])                                       # the dedication page: only its picture
        self.assertFalse(by[1]["textMissing"])
        self.assertEqual(by[3]["text"], "Little fawn wakes in the dew,\nGood morning, {Name}, wake and play.")
        self.assertIsNone(by[2]["text"])
        self.assertEqual(by[12]["text"], "Fox and squirrel share a treat.")   # spread 7 = 12–13, mirrored → left
        self.assertIsNone(by[13]["text"])
        self.assertTrue(by[4]["textMissing"])                                  # spread 3 = 4–5, mirrored → left
        self.assertFalse(by[5]["textMissing"])
        self.assertEqual(by[30]["text"], "Sleep sweet, dear {Name}.")
        self.assertIsNone(by[9]["picture"])
        self.assertEqual(by[31]["picture"], "Cover.png")
        self.assertIsNone(by[31]["text"])                                      # the owner sets the title himself
        self.assertEqual(sum(1 for p in plan if p["text"] or p["textMissing"]), 15)   # 14 spreads + the afterword

    def test_pages_and_names(self):
        self.assertEqual(js("B.parsePages('1-31')"), list(range(1, 32)))
        self.assertEqual(js("B.parsePages('12, 3 7-5;40')"), [3, 5, 6, 7, 12])
        self.assertEqual(js("B.parsePages('30-3111111111')"), [30, 31])
        self.assertIsNone(js("B.parsePages('3a')"))
        self.assertIsNone(js("B.parsePages('')"))
        self.assertEqual(js("[B.pictureKey('07.png'), B.pictureKey('Cover.PNG'), B.pictureKey('cover-art.png')]"),
                         ["7", "cover", None])
        self.assertEqual(js("[B.uploadName('33.guardian-angel', 2, '2.png'), B.uploadName('b', 31, 'Cover.jpg')]"),
                         ["33.guardian-angel-p02.png", "b-cover.jpg"])
        self.assertEqual(js("B.uploadName('b', 2, '2.png', '1008-1432')"), "b-p02-1008-1432.png")   # a run's mark


class Manifest(unittest.TestCase):
    def test_every_file_it_names_exists(self):
        m = json.loads((EXT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(m["manifest_version"], 3)
        files = [*m["icons"].values(), *(f for cs in m["content_scripts"] for f in cs["js"])]
        for f in files:
            self.assertTrue((EXT / f).is_file(), f)
        self.assertEqual(m["content_scripts"][0]["world"], "MAIN")   # Canva's file chooser is answered from the page


if __name__ == "__main__":
    unittest.main()
