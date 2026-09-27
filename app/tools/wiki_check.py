"""Checks the project wiki (../../wiki) against the program code. Run it after every change.

  python app/tools/wiki_check.py            full check; exit code 1 when something is out of date
  python app/tools/wiki_check.py --changed  wiki pages that describe the files changed in git (what to update)
  python app/tools/wiki_check.py --map      every code file and the wiki pages that describe it

What is checked:
  - every page (except log.md and raw/) has front matter: title, type, updated (YYYY-MM-DD), code (existing files);
  - every relative link leads to an existing file;
  - on a line with a link to a code file, `name()` and `CONSTANT` code spans after that link exist in that file;
  - every page is linked from index.md;
  - every code file of the program is listed in the `code:` front matter of at least one page;
  - the route table in architecture/api-routes.md matches the @route declarations one to one;
  - log.md headings look like "## [YYYY-MM-DD] kind | title".
Standard library only.
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
APP = REPO / "app"
WIKI = REPO / "wiki"
CODE_SUFFIXES = {".py", ".pyw", ".js", ".jsx", ".css", ".html", ".bat"}
SKIP_DIRS = {"data", "bin", "__pycache__", ".git", "node_modules"}
TYPES = {"index", "overview", "reference", "architecture", "feature", "integration", "rule", "flow", "owner",
         "decision", "recipe", "dev", "plan"}
ROUTES_PAGE = "architecture/api-routes.md"

_LINK = re.compile(r"\]\((<[^>]+>|[^)\s]+)\)")
_SPAN = re.compile(r"`([^`\n]+)`")
_FUNC = re.compile(r"^(?:[A-Za-z_$][\w$]*\.)*([A-Za-z_$][\w$]*)\(\)$")
_CONST = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_LOG_HEAD = re.compile(r"^## \[\d{4}-\d{2}-\d{2}\] [a-z-]+ \| \S.*$")
_ROUTE = re.compile(r'@route\(\s*"(\w+)"\s*,\s*r?"([^"]+)"')


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


def code_files() -> list[Path]:
    out = []
    for path in APP.rglob("*"):
        parts = set(path.relative_to(APP).parts)
        if path.is_file() and path.suffix.lower() in CODE_SUFFIXES and not parts & SKIP_DIRS:
            out.append(path)
    return sorted(out)


def pages() -> list[Path]:
    return sorted(p for p in WIKI.rglob("*.md")
                  if not {"raw", ".obsidian"} & set(p.relative_to(WIKI).parts))


def front_matter(text: str) -> dict | None:
    """The small YAML subset the wiki uses: `key: value`, `key: []` and `key:` followed by `  - item` lines."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    data: dict = {}
    key = None
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and key is not None:
            if not isinstance(data[key], list):
                data[key] = []
            data[key].append(item.group(1).strip().strip('"'))
            continue
        pair = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if not pair:
            return None
        key, value = pair.group(1), pair.group(2).strip()
        data[key] = [] if value in ("", "[]") else value.strip('"')
    return data


def link_target(page: Path, raw: str) -> Path | None:
    raw = raw[1:-1] if raw.startswith("<") else raw
    if re.match(r"^[a-z]+:", raw) or raw.startswith("#"):
        return None
    raw = urllib.parse.unquote(raw.split("#", 1)[0])
    return (page.parent / raw).resolve() if raw else None


# What defines a name in a file. An import or a call is not enough: a moved function's old file still imports or calls
# it, and such stale lines passed the check until 27.09.2026.
_DEFINES = (
    r"\b(?:def|function\*?|class|const|let|var)\s+{n}\b",   # def f / function f / class C / const X = …
    r"^[ \t]*(?:self\.|cls\.)?{n}\s*(?::[^=\n]+)?=(?!=)",  # X = … / X: T = … / self.x = …
    r"^[ \t]*(?:async\s+)?{n}\s*\([^)\n]*\)\s*\{{",         # a method: f(a) {
    r"(?:^|[{{,])[ \t]*{n}\s*:",                            # an object's key: { f: … }
    r"export\s*\{{[^}}]*\b{n}\b",                           # export { f }
    r"[\"']{n}[\"']",                                       # in quotes: an environment variable, a setting's key
)


def defined_in(name: str, text: str) -> bool:
    """`name` is defined in this file: `Class.method` — the method, when the class is this file's; any other dotted
    `module.name` (another module's function the file calls) only has to be there."""
    if "." in name:
        owner, _, last = name.rpartition(".")
        if re.search(rf"\bclass\s+{re.escape(owner)}\b", text):
            return defined_in(last, text)
        return re.search(rf"\b{re.escape(name)}\b", text) is not None
    return any(re.search(p.format(n=re.escape(name)), text, re.M) for p in _DEFINES)


def routes_in_code() -> set[tuple[str, str]]:
    found = set()
    for path in (APP / "studio").rglob("*.py"):  # the Workshop's routes live in its package
        found.update(_ROUTE.findall(path.read_text(encoding="utf-8")))
    return found


def routes_in_wiki(text: str) -> set[tuple[str, str]]:
    found = set()
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) >= 2 and re.fullmatch(r"GET|POST|PUT|PATCH|DELETE", cells[0]):
            span = re.fullmatch(r"`([^`]+)`", cells[1])
            if span:
                found.add((cells[0], span.group(1)))
    return found


def coverage() -> dict[str, list[str]]:
    """repo-relative code file -> wiki pages that list it (a `code:` entry ending in / covers a whole folder)."""
    listed: list[tuple[str, str]] = []
    for page in pages():
        fm = front_matter(page.read_text(encoding="utf-8")) or {}
        for entry in fm.get("code") or []:
            listed.append((entry, page.relative_to(WIKI).as_posix()))
    out = {}
    for path in code_files():
        name = rel(path)
        out[name] = sorted({p for entry, p in listed if entry == name or (entry.endswith("/") and name.startswith(entry))})
    return out


def check() -> list[str]:
    problems: list[str] = []
    if not (WIKI / "index.md").exists():
        return ["Missing wiki/index.md."]
    code_cache: dict[Path, str] = {}
    all_pages = pages()
    index_links: set[Path] = set()

    for page in all_pages:
        name = page.relative_to(WIKI).as_posix()
        text = page.read_text(encoding="utf-8")
        if name != "log.md":
            fm = front_matter(text)
            if fm is None:
                problems.append(f"{name}: missing or broken front matter.")
            else:
                for key in ("title", "type", "updated"):
                    if not fm.get(key):
                        problems.append(f"{name}: front matter is missing \"{key}\".")
                if fm.get("type") and fm["type"] not in TYPES:
                    problems.append(f"{name}: unknown type \"{fm['type']}\".")
                if fm.get("updated") and not _DATE.match(str(fm["updated"])):
                    problems.append(f"{name}: updated must be in YYYY-MM-DD format.")
                if "code" not in fm:
                    problems.append(f"{name}: front matter is missing \"code\" (for a page with no code — code: []).")
                for entry in fm.get("code") or []:
                    if not (REPO / entry).exists():
                        problems.append(f"{name}: code lists a path that doesn't exist: {entry}.")
        else:
            for line in text.splitlines():
                if line.startswith("## ") and not _LOG_HEAD.match(line):
                    problems.append(f"log.md: heading doesn't match \"## [YYYY-MM-DD] kind | title\": {line}")

        fenced = False
        for no, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue  # examples inside code blocks are not real links
            marks = []
            plain = _SPAN.sub(lambda s: " " * len(s.group(0)), line)  # links inside `code` are examples too
            for m in _LINK.finditer(plain):
                target = link_target(page, m.group(1))
                if target is None:
                    continue
                if not target.exists():
                    problems.append(f"{name}:{no}: link leads nowhere: {m.group(1)}")
                    continue
                if name == "index.md":
                    index_links.add(target)
                if target.is_file() and target.suffix.lower() in CODE_SUFFIXES and APP in target.parents:
                    marks.append((m.end(), target))
            if not marks:
                continue
            for s in _SPAN.finditer(line):
                owner = [t for pos, t in marks if pos <= s.start()]
                if not owner:
                    continue
                token = s.group(1).strip()
                func, const = _FUNC.match(token), _CONST.match(token)
                if not func and not const:
                    continue
                target = owner[-1]
                if target not in code_cache:
                    code_cache[target] = target.read_text(encoding="utf-8")
                ident = token[:-2] if func else token
                if not defined_in(ident, code_cache[target]):
                    problems.append(f"{name}:{no}: `{token}` not found in {rel(target)}")

    for page in all_pages:
        if page.name != "index.md" and page.relative_to(WIKI).as_posix() != "index.md" \
                and page.resolve() not in index_links:
            problems.append(f"index.md: no link to {page.relative_to(WIKI).as_posix()}")

    for name, described in coverage().items():
        if not described:
            problems.append(f"{name}: no wiki page describes this file (add it to the code: of the right page).")

    problems += stale_numbers()

    routes_page = WIKI / ROUTES_PAGE
    if routes_page.exists():
        in_code, in_wiki = routes_in_code(), routes_in_wiki(routes_page.read_text(encoding="utf-8"))
        for method, pattern in sorted(in_code - in_wiki):
            problems.append(f"{ROUTES_PAGE}: missing route {method} {pattern}")
        for method, pattern in sorted(in_wiki - in_code):
            problems.append(f"{ROUTES_PAGE}: route {method} {pattern} no longer exists in the code")
    else:
        problems.append(f"Missing page {ROUTES_PAGE}.")
    return problems


def test_count() -> int:
    """How many tests the runner finds: every test_… method of a class in app/tests, read with ast — a
    `def test_` inside a string or a helper outside a class is not a test (22.09.2026 audit)."""
    total = 0
    for path in sorted((REPO / "app" / "tests").glob("test_*.py")):
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.ClassDef):
                total += sum(1 for f in node.body if isinstance(f, ast.FunctionDef) and f.name.startswith("test_"))
    return total


# Where the wiki states how many tests and routes there are, and how: every mention on these pages is checked,
# not only the first. "117 tests against 182" is history (how it used to be) and is left alone.
NUMBER_CLAIMS = [
    ("dev/testing.md", r"(\d+)\s+tests?\b(?!\s+against)", "tests"),
    ("index.md", r"all\s+(\d+)\b", "routes"),
    ("architecture/api-routes.md", r"(\d+)\s+routes?\b(?!\s+against)", "routes"),
    ("architecture/server.md", r"(\d+)\s+routes?\b(?!\s+against)", "routes"),
]


def stale_numbers() -> list[str]:
    """Numbers the wiki states in plain words. Links, names and route tables were always checked; counts
    were not, and they quietly drifted (117 tests against 162, 88 routes against 92 — audit, 22.09.2026)."""
    real = {"tests": test_count(), "routes": len(routes_in_code())}
    problems, seen = [], set()
    for name, pattern, what in NUMBER_CLAIMS:
        page = WIKI / name
        if not page.exists():
            continue
        lines = page.read_text(encoding="utf-8").splitlines()
        # index.md: "all N" counts routes only on the line about the routes
        found = [(n, m) for n, line in enumerate(lines, 1) for m in re.finditer(pattern, line)
                 if what != "routes" or name != "index.md" or "route" in line.lower()]
        if found:
            seen.add(what)
        for n, m in found:
            if int(m.group(1)) != real[what]:
                problems.append(f"{name}:{n}: says {m.group(1)} {what}, actually {real[what]}.")
    for what in real:
        if what not in seen:
            problems.append(f"No number for \"{what}\" found in the wiki — the stale-number check can't see it.")
    return problems


def changed_files() -> list[str]:
    out = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain=v1", "-uall"],
                         capture_output=True, text=True, encoding="utf-8").stdout
    files = []
    for line in out.splitlines():
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        files.append(path)
    return files


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if "--map" in argv:
        for name, described in coverage().items():
            print(f"{name}  →  {', '.join(described) or '— (не описано)'}")
        return 0
    if "--changed" in argv:
        cov = coverage()
        changed = changed_files()
        todo: dict[str, list[str]] = {}
        loose = []
        for name in changed:
            if name in cov:
                if cov[name]:
                    for page in cov[name]:
                        todo.setdefault(page, []).append(name)
                else:
                    loose.append(name)
        if not todo and not loose:
            print("No changed program files.")
        for page, files in sorted(todo.items()):
            print(f"wiki/{page}\n    because of: {', '.join(files)}")
        for name in loose:
            print(f"{name}: not described by any page — add it to the code: of the right page")
        print("Don't forget: updated in the header of the pages you changed, and an entry in wiki/log.md.")
        return 0
    problems = check()
    if problems:
        print("The wiki is out of sync with the code:\n" + "\n".join(f"  - {p}" for p in problems))
        return 1
    print(f"Wiki is in order: {len(pages())} pages, {len(code_files())} code files, {len(routes_in_code())} routes.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
