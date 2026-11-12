"""Checks the project wiki (../../wiki) against the program code. Run it after every change.

  python app/tools/wiki_check.py            full check; exit code 1 when something is out of date
  python app/tools/wiki_check.py --changed  wiki pages that describe the files changed in git (what to update)
  python app/tools/wiki_check.py --map      the code map: every code file, its docstring's first line, the pages that describe it
  python app/tools/wiki_check.py --routes   the route table: method, pattern, handler, file

What is checked:
  - every page has front matter: title, type, updated (YYYY-MM-DD), code (existing files);
  - every relative link leads to an existing file;
  - on a line with a link to a code file, `name()` and `CONSTANT` code spans after that link exist in that file;
  - every page is linked from index.md;
  - every code file of the program is listed in the `code:` front matter of at least one page;
  - a page is at most MAX_PAGE_KB;
  - no page tells history ("since 12.10", "until 2026-…", "during the move"): the wiki says only what is, history is git.
The code map and the route table are printed on demand, never kept as pages; counts are not written in the wiki at all.
Standard library only.
"""
from __future__ import annotations

import os
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
         "decision", "recipe", "dev"}
MAX_PAGE_KB = 12          # a page an agent reads whole; a bigger topic is split into two pages
CODE_ROOTS = ("app", "seo", "canva-extension")
# History told in prose. A date with "since/until/before/after", or the move between accounts.
_HISTORY = re.compile(r"\b(?:since|until|till|before|after)\s+(?:\d{1,2}\.\d{2}(?:\.\d{2,4})?|20\d\d-\d\d-\d\d)\b"
                      r"|\bduring the move\b|\(the owner,? \d{1,2}[./]\d{1,2}|\(the owner,? 20\d\d-", re.I)

_LINK = re.compile(r"\]\((<[^>]+>|[^)\s]+)\)")
_SPAN = re.compile(r"`([^`\n]+)`")
_FUNC = re.compile(r"^(?:[A-Za-z_$][\w$]*\.)*([A-Za-z_$][\w$]*)\(\)$")
_CONST = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ROUTE = re.compile(r'@route\(\s*"(\w+)"\s*,\s*r?"([^"]+)"')


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


_CODE_FILES: list[Path] = []


def code_files() -> list[Path]:
    """Every code file of the program, found once per run. The walk never enters SKIP_DIRS: `data` holds gigabytes of the owner's files,
    and listing them only to drop them took ~3 s of every call."""
    if not _CODE_FILES:
        for root in (REPO / r for r in CODE_ROOTS):   # the program, the Etsy SEO studio, the Canva extension
            for top, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                _CODE_FILES.extend(Path(top, f) for f in files if Path(f).suffix.lower() in CODE_SUFFIXES)
        _CODE_FILES.sort()
    return list(_CODE_FILES)


def pages() -> list[Path]:
    return sorted(p for p in WIKI.rglob("*.md") if ".obsidian" not in p.relative_to(WIKI).parts)


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
    r"\b(?:const|let|var)\s+[^;\n]*,\s*{n}\s*=",            # const A = 1, B = 2
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


_DEF = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)", re.M)


def route_table() -> list[tuple[str, str, str, str]]:
    """(method, pattern, handler, file) of every route, for `--routes`; stacked decorators share the def below them."""
    rows = []
    for path in sorted((APP / "studio").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for m in _ROUTE.finditer(text):
            handler = _DEF.search(text, m.end())
            rows.append((m.group(1), m.group(2), handler.group(1) if handler else "?", rel(path)))
    return sorted(rows, key=lambda r: (r[1], r[0]))


def first_doc_line(path: Path) -> str:
    """The first line of a file's own description: a Python docstring, or the opening /* … */ or // comment of JS/CSS."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace").lstrip("﻿")
    except OSError:
        return ""
    m = re.match(r'\s*(?:#![^\n]*\n|#[^\n]*coding[^\n]*\n)*\s*(?:[rubRUB]{0,2})("""|\'\'\')\s*(.*?)(?:\n|\1)', text, re.S) \
        or re.match(r"\s*/\*+\s*(.*?)(?:\n|\*/)", text, re.S) or re.match(r"\s*//\s*(.*)", text) \
        or re.match(r"\s*<!--\s*(.*?)(?:\n|-->)", text, re.S) or re.match(r"\s*(?:@?echo off\s*\n)?\s*(?:rem|::)\s*(.*)", text, re.I)
    if not m:
        return ""
    line = m.group(m.lastindex).strip()
    if re.fullmatch(r"[=*\-#~ ]*", line):           # a banner line (/* ===== ): the text is on the next line
        nxt = re.search(r"\n\s*\**\s*([^\n=*\-#~][^\n]*)", text[m.end():])
        line = nxt.group(1).strip() if nxt else ""
    return re.sub(r"^\*\s*", "", line)[:140]


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


_ALL_CODE: list = []        # [the code as one text, the set of every word in it]


def _anywhere(ident: str) -> bool:
    """The name is in some code file (a looser check than `defined_in`: for names the page does not link to a file).
    A plain word is looked up in the set of all words, made once — a regex over the whole code for each of ~2800 names
    took 46 s of the 54 s this check lasted."""
    if not _ALL_CODE:
        text = chr(10).join(p.read_text(encoding="utf-8", errors="replace") for p in code_files())
        _ALL_CODE.extend([text, set(re.findall(r"\w+", text))])
    if ident in BUILTIN_NAMES:
        return True
    if re.fullmatch(r"\w+", ident):
        return ident in _ALL_CODE[1]
    return re.search(r"\b" + re.escape(ident) + r"\b", _ALL_CODE[0]) is not None


# Names of the language and its library that the pages mention in passing.
BUILTIN_NAMES = {"open", "print", "len", "str", "int", "dict", "list", "set", "sorted", "iterdir", "glob", "rglob", "is_file", "is_dir",
                 "exists", "rmtree", "replace", "fsync", "unlink", "mkdir", "read_text", "write_text", "stat", "resolve", "sleep",
                 "urlopen", "Popen", "run", "fetch", "push", "pull", "clear", "get", "set", "post", "add", "start", "stop"}


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
        fm = front_matter(text)
        if fm is None:
            problems.append(f"{name}: missing or broken front matter (UTF-8 without BOM, LF line ends).")
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
        size_kb = len(text.encode("utf-8")) / 1024
        if size_kb > MAX_PAGE_KB:
            problems.append(f"{name}: {size_kb:.1f} KB — over {MAX_PAGE_KB} KB; split the topic or cut what another page says.")

        fenced = False
        for no, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue  # examples inside code blocks are not real links
            told = _HISTORY.search(_SPAN.sub("", line))
            if told:
                problems.append(f"{name}:{no}: history in the text (\"{told.group(0)}\") — say only what is now; the past is git")
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
                if target.is_file() and target.suffix.lower() in CODE_SUFFIXES \
                        and any((REPO / r).resolve() in target.parents for r in CODE_ROOTS):
                    marks.append((m.end(), target))
            for s in _SPAN.finditer(line):                # a function named in prose must exist somewhere in the code
                token = s.group(1).strip()
                func = _FUNC.match(token)
                if func and not _anywhere(token[:-2].rpartition(".")[2]):
                    problems.append(f"{name}:{no}: `{token}` is not in the code at all")
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
            doc = first_doc_line(REPO / name)
            print(f"{name}  —  {doc or '…'}\n    →  {', '.join(described) or '— (не описано)'}")
        return 0
    if "--routes" in argv:
        for method, pattern, handler, path in route_table():
            print(f"{method:6} {pattern:55} {handler}()  {path}")
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
        print("Don't forget: updated in the header of the pages you changed. No log: the wiki says what is now.")
        return 0
    problems = check()
    if problems:
        print("The wiki is out of sync with the code:\n" + "\n".join(f"  - {p}" for p in problems))
        return 1
    print(f"Wiki is in order: {len(pages())} pages, {len(code_files())} code files, {len(routes_in_code())} routes.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
