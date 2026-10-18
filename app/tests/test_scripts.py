"""The interface's scripts, checked without a browser (there are no browser tests):
- each parses as the ES module it is — an identifier declared twice made the Order Creator a blank page (27.09.2026).
  `node --check` on a .js file doesn't parse it as a module, so each is checked as a copy named .mjs; skipped where
  Node.js isn't installed;
- no script uses a name another script exports without importing it — the syntax check can't see that, and the page
  only fails when that line runs (a helper moved to another module, 27.09.2026);
- no script imports a name it never uses;
- no script uses a name it neither declares nor imports (and isn't the browser's) — a constant left behind when a
  part moved to a module of its own (27.09.2026)."""
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
    for m in re.finditer(r"\b(?:let|var|const)\s+[^;\n]*", src):  # let a = 0, b = 0
        names |= set(re.findall(r",\s*([A-Za-z_$][\w$]*)\s*=(?!=)", m.group(0)))
    # destructuring: const { a, b: c } = … / const [a, b] = … / for (const [a] of …)
    for m in re.finditer(r"\b(?:const|let|var)\s*[\[{]([^=;]*?)[\]}]\s*(?:=|\bof\b|\bin\b)", src):
        names |= set(re.findall(r"(?:^|[,{\s:])\s*([A-Za-z_$][\w$]*)\s*(?=[,}\]=]|$)", m.group(1)))
    for m in re.finditer(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)\s*(?:=>|\{)", src):
        params = m.group(1).replace("...", "") + ")"  # a rest parameter: (a, ...rest)
        names |= set(re.findall(r"(?<![\w$.'\"`])([A-Za-z_$][\w$]*)(?=\s*(?:[,)=}\]]|$))", params))
    names |= set(re.findall(r"([A-Za-z_$][\w$]*)\s*=>", src))
    names |= set(re.findall(r"catch\s*\(\s*([A-Za-z_$][\w$]*)", src))
    return names


# What a script may use without declaring it: the language's and the browser's own names.
KEYWORDS = set("""break case catch class const continue debugger default delete do else export extends false finally
for function if import in instanceof let new null of return super switch this throw true try typeof undefined var void
while with yield async await static get set from as""".split())
GLOBALS = set("""Array ArrayBuffer Blob TextEncoder btoa Boolean CSS CustomEvent Date Error FontFace Image JSON Map Math Node Number Object Promise
ResizeObserver Set String URLSearchParams history WeakMap XMLHttpRequest cancelAnimationFrame clearInterval clearTimeout console
crypto decodeURIComponent document encodeURIComponent fetch innerHeight innerWidth localStorage location matchMedia
navigator parseInt performance requestAnimationFrame requestIdleCallback setInterval setTimeout window""".split())


def is_key_or_method(src, prev, end, prev_word=""):
    """The name ending at src[end] is an object's key ({ name: … }) or a method (name(…) { … }, get name() { … },
    a class's) — not a reference. `prev` — the character before it (comments skipped), `prev_word` — the word
    before it, when that was one."""
    after = src[end:end + 200].lstrip()
    if prev in "{," and after.startswith(":") and not after.startswith("::"):
        return True
    if after.startswith("(") and after[after.find(")") + 1:].lstrip().startswith("{"):
        return prev in "{,};" or prev_word in {"get", "set", "async", "static"}
    return False


def undeclared(src):
    """The names a script refers to that it neither declares nor imports, nor are the language's or the browser's."""
    own = declared(src) | KEYWORDS | GLOBALS
    found, last = [], ""
    for word, prev, _, end in tokens(src):
        before, last = (last if prev == "a" else ""), word
        if prev == "." or word in own or word in found or is_key_or_method(src, prev, end, before):
            continue
        found.append(word)
    return found


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

    def test_every_name_is_declared(self):
        missing = [f"{p.relative_to(WEB).as_posix()}: {name}" for p in scripts()
                   for name in undeclared(p.read_text(encoding="utf-8"))]
        self.assertEqual(missing, [])

    def test_a_name_left_behind_is_found(self):
        # Profit's rows moved to a module of their own without the list of states they show (27.09.2026): the row's
        # panel didn't open, and no other check saw it — the name was nobody's export.
        src = ("import { html } from '../lib.js';\nconst TEXT = { a: 1 };\n"
               "export function stateBox(o, mode) { return html`${segHtml(STATE_OPTS, o.state)}${TEXT[o.state]}`; }\n")
        self.assertEqual(undeclared(src), ["segHtml", "STATE_OPTS"])
        ok = ("const list = [];\nlet a = 0, b = 1;\nfor (const [k, v] of list) f(k, v);\nconst g = (x, ...rest) => rest;\n"
              "const o = { get size() { return a; }, async load() { return b; }, key: 1 };\n"
              "class C { constructor(s) { this.s = s; } toString() { return this.s; } }\nfunction f() {}\n")
        self.assertEqual(undeclared(ok), [])

    def test_the_tokenizer_sees_through_strings_and_spreads(self):
        src = "const a = 'it\\'s ${x}'; const b = `${ html`${y}` }`; f(...pageVersion(v)); o.z; // w\n"
        self.assertEqual(refs(src) & {"x", "y", "html", "pageVersion", "z", "w", "f"}, {"y", "html", "pageVersion", "f"})


if __name__ == "__main__":
    unittest.main()
