"""The project wiki keeps up with the code: links, named functions, file coverage, page size, no history in the text."""
import importlib.util
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "wiki_check.py"
WIKI_INDEX = TOOL.parents[2] / "wiki" / "index.md"


@unittest.skipUnless(WIKI_INDEX.exists(), "no wiki beside the program")
class WikiMatchesCode(unittest.TestCase):
    def test_wiki_check_passes(self):
        spec = importlib.util.spec_from_file_location("wiki_check", TOOL)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        problems = tool.check()
        self.assertEqual(problems, [], "wiki is out of date (python app/tools/wiki_check.py):\n" + "\n".join(problems))


class NamedInTheRightFile(unittest.TestCase):
    """A name the wiki puts after a file's link is defined there — an import or a call of it is not enough (a moved
    function's old file still imports and calls it; 27.09.2026)."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("wiki_check", TOOL)
        cls.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.tool)

    def test_defined(self):
        js = ("export function mount(view) {}\nconst WHO = {};\nexport const costOf = (o) => o;\n"
              "const api = {\n  refresh(x) {\n  },\n  wake: () => 1,\n};\n")
        for name in ["mount", "WHO", "costOf", "refresh", "wake"]:
            self.assertTrue(self.tool.defined_in(name, js), name)
        py = 'FULL_SYNC_EVERY = 5\nclass Job:\n    def share(self):\n        pass\nKEY = os.environ.get("BOOK_STUDIO_DATA")\n'
        for name in ["FULL_SYNC_EVERY", "Job", "Job.share", "BOOK_STUDIO_DATA"]:
            self.assertTrue(self.tool.defined_in(name, py), name)

    def test_only_used(self):
        js = "import { picture, STATE_TEXT } from '../workshop-bits.js';\nconst src = picture(b, 720);\nf(STATE_TEXT[s]);\n"
        for name in ["picture", "STATE_TEXT", "checkWord"]:
            self.assertFalse(self.tool.defined_in(name, js), name)
        py = "from . import archive\nclass Job:\n    pass\narchive.refresh_quietly()\n"
        self.assertTrue(self.tool.defined_in("archive.refresh_quietly", py))  # another module's function it calls
        self.assertFalse(self.tool.defined_in("Job.share", py))  # the class is this file's, the method is not

    def test_several_in_one_declaration(self):
        js = "const FAST = 1500, SLOW = 4000, OFFLINE = 10000;\n"
        for name in ["FAST", "SLOW", "OFFLINE"]:
            self.assertTrue(self.tool.defined_in(name, js), name)
        self.assertFalse(self.tool.defined_in("CALM", js))


class WikiToolsAndRules(unittest.TestCase):
    """The wiki says only what is now, and the code map / route table come from the code on demand."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("wiki_check", TOOL)
        cls.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.tool)

    def test_history_is_caught(self):
        for line in ["Since 12.10 the cover is drawn.", "until 2026-09-30 two keys", "during the move to Gelato",
                     "(the owner, 04.10.2026: weekly)"]:
            self.assertIsNotNone(self.tool._HISTORY.search(line), line)

    def test_the_present_passes(self):
        for line in ["after 14 days the files go", "Printify is read-only from 2026-10-01", "since the last sync",
                     "a backup when the last one is 3 days old", "after 1.5 seconds", "until 3/4 full", "before 10.5 MB"]:
            self.assertIsNone(self.tool._HISTORY.search(line), line)

    def test_route_table_has_every_route(self):
        table = self.tool.route_table()
        self.assertEqual({(m, p) for m, p, _, _ in table}, self.tool.routes_in_code())
        self.assertFalse([r for r in table if r[2] == "?"], "a route without its handler")
