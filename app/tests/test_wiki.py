"""The project wiki keeps up with the code: links, named functions, routes and file coverage."""
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
