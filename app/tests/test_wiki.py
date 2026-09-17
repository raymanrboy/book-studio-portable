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
