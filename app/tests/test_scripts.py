"""The interface's scripts, checked without a browser (there are no browser tests):
- each parses as the ES module it is — an identifier declared twice made the Order Creator a blank page (27.09.2026).
  `node --check` on a .js file doesn't parse it as a module, so each is checked as a copy named .mjs; skipped where
  Node.js isn't installed;
- no script uses a name another script exports without importing it — the syntax check can't see that, and the page
  only fails when that line runs (a helper moved to another module, 27.09.2026);
- no script imports a name it never uses."""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from tests.jstokens import refs, tokens

WEB = Path(__file__).resolve().parents[1] / "web" / "js"
IMPORT = re.compile(r"^import \{([^}]*)\} from '([^']+)';\n", re.M)
EXPORT = re.compile(r"^export\s+(?:async\s+)?(?:function\*?|const|let|class)\s+([A-Za-z_$][\w$]*)", re.M)


def scripts():
    return sorted(WEB.rglob("*.js"))


def imported(src):
    return [(m.group(2), [n.strip() for n in m.group(1).replace("\n", " ").split(",") if n.strip()])
            for m in IMPORT.finditer(src)]


def declared(src):
    """The names a script declares itself — imports, declarations, parameters (read loosely: enough to tell a local
    name from a missing import)."""
    names = {n.split(" as ")[-1].strip() for _, ns in imported(src) for n in ns}
    names |= set(re.findall(r"\b(?:const|let|var|function\*?|class)\s+([A-Za-z_$][\w$]*)", src))
    for m in re.finditer(r"\b(?:const|let|var)\s*[\[{]([^=;]*?)[\]}]\s*=", src):
        names |= set(re.findall(r"(?:^|[,{\s:])\s*([A-Za-z_$][\w$]*)\s*(?=[,}\]=]|$)", m.group(1)))
    for m in re.finditer(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)\s*(?:=>|\{)", src):
        names |= set(re.findall(r"(?<![\w$.'\"`])([A-Za-z_$][\w$]*)(?=\s*(?:[,)=}\]]|$))", m.group(1) + ")"))
    names |= set(re.findall(r"([A-Za-z_$][\w$]*)\s*=>", src))
    names |= set(re.findall(r"catch\s*\(\s*([A-Za-z_$][\w$]*)", src))
    return names


@unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
class ScriptsParse(unittest.TestCase):
    def test_every_script_is_a_valid_module(self):
        found = scripts()
        self.assertGreater(len(found), 10)
        with tempfile.TemporaryDirectory() as d:
            for script in found:
                copy = Path(d) / f"{script.stem}.mjs"
                shutil.copyfile(script, copy)
                result = subprocess.run(["node", "--check", str(copy)], capture_output=True, text=True, timeout=60)
                with self.subTest(script=script.relative_to(WEB).as_posix()):
                    self.assertEqual(result.returncode, 0, result.stderr.strip()[-600:])


class ScriptsImport(unittest.TestCase):
    def test_no_script_uses_an_exported_name_it_does_not_import(self):
        exported = {}
        for p in scripts():
            for name in EXPORT.findall(p.read_text(encoding="utf-8")):
                exported.setdefault(name, p.name)
        missing = []
        for p in scripts():
            src = p.read_text(encoding="utf-8")
            own = declared(src)
            for word, prev, _, end in tokens(src):
                if prev == "." or word in own or word not in exported:
                    continue
                after = src[end:end + 200].lstrip()
                if prev in "{," and after.startswith(":"):
                    continue  # an object's key
                if prev in "{," and after.startswith("(") and after[after.find(")") + 1:].lstrip().startswith("{"):
                    continue  # a method written in an object
                missing.append(f"{p.relative_to(WEB).as_posix()}: {word} (from {exported[word]})")
                own.add(word)
        self.assertEqual(missing, [])

    def test_every_imported_name_is_used(self):
        unused = []
        for p in scripts():
            src = p.read_text(encoding="utf-8")
            used = refs(IMPORT.sub("", src))
            unused += [f"{p.relative_to(WEB).as_posix()}: {n}" for _, names in imported(src) for n in names
                       if n.split(" as ")[-1].strip() not in used]
        self.assertEqual(unused, [])

    def test_the_tokenizer_sees_through_strings_and_spreads(self):
        src = "const a = 'it\\'s ${x}'; const b = `${ html`${y}` }`; f(...pageVersion(v)); o.z; // w\n"
        self.assertEqual(refs(src) & {"x", "y", "html", "pageVersion", "z", "w", "f"}, {"y", "html", "pageVersion", "f"})


if __name__ == "__main__":
    unittest.main()
