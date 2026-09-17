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

import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
APP = REPO / "app"
WIKI = REPO / "wiki"
CODE_SUFFIXES = {".py", ".pyw", ".js", ".css", ".html", ".bat"}
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


def defined_in(name: str, text: str, const: bool) -> bool:
    if const:
        return re.search(rf"\b{re.escape(name)}\b", text) is not None
    n = re.escape(name)
    return re.search(rf"(?:def|function|class)\s+{n}\b|\b{n}\s*(?:=|:|\()", text) is not None


def routes_in_code() -> set[tuple[str, str]]:
    found = set()
    for path in (APP / "studio").glob("*.py"):
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
        return ["Немає wiki/index.md."]
    code_cache: dict[Path, str] = {}
    all_pages = pages()
    index_links: set[Path] = set()

    for page in all_pages:
        name = page.relative_to(WIKI).as_posix()
        text = page.read_text(encoding="utf-8")
        if name != "log.md":
            fm = front_matter(text)
            if fm is None:
                problems.append(f"{name}: немає або зіпсована шапка (front matter).")
            else:
                for key in ("title", "type", "updated"):
                    if not fm.get(key):
                        problems.append(f"{name}: у шапці немає «{key}».")
                if fm.get("type") and fm["type"] not in TYPES:
                    problems.append(f"{name}: невідомий type «{fm['type']}».")
                if fm.get("updated") and not _DATE.match(str(fm["updated"])):
                    problems.append(f"{name}: updated має бути у форматі РРРР-ММ-ДД.")
                if "code" not in fm:
                    problems.append(f"{name}: у шапці немає «code» (для сторінки без коду — code: []).")
                for entry in fm.get("code") or []:
                    if not (REPO / entry).exists():
                        problems.append(f"{name}: у code є неіснуючий шлях {entry}.")
        else:
            for line in text.splitlines():
                if line.startswith("## ") and not _LOG_HEAD.match(line):
                    problems.append(f"log.md: заголовок не за форматом «## [РРРР-ММ-ДД] вид | назва»: {line}")

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
                    problems.append(f"{name}:{no}: посилання веде в нікуди: {m.group(1)}")
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
                ident = func.group(1) if func else token
                if not defined_in(ident, code_cache[target], bool(const)):
                    problems.append(f"{name}:{no}: `{token}` не знайдено в {rel(target)}")

    for page in all_pages:
        if page.name != "index.md" and page.relative_to(WIKI).as_posix() != "index.md" \
                and page.resolve() not in index_links:
            problems.append(f"index.md: немає посилання на {page.relative_to(WIKI).as_posix()}")

    for name, described in coverage().items():
        if not described:
            problems.append(f"{name}: жодна сторінка вікі не описує цей файл (додайте його в code: потрібної сторінки).")

    routes_page = WIKI / ROUTES_PAGE
    if routes_page.exists():
        in_code, in_wiki = routes_in_code(), routes_in_wiki(routes_page.read_text(encoding="utf-8"))
        for method, pattern in sorted(in_code - in_wiki):
            problems.append(f"{ROUTES_PAGE}: немає маршруту {method} {pattern}")
        for method, pattern in sorted(in_wiki - in_code):
            problems.append(f"{ROUTES_PAGE}: маршруту {method} {pattern} у коді вже немає")
    else:
        problems.append(f"Немає сторінки {ROUTES_PAGE}.")
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
            print("Змінених файлів програми немає.")
        for page, files in sorted(todo.items()):
            print(f"wiki/{page}\n    через: {', '.join(files)}")
        for name in loose:
            print(f"{name}: не описаний жодною сторінкою — додайте його в code: потрібної сторінки")
        print("Не забудьте: updated у шапці оновлених сторінок і запис у wiki/log.md.")
        return 0
    problems = check()
    if problems:
        print("Вікі розходиться з кодом:\n" + "\n".join(f"  - {p}" for p in problems))
        return 1
    print(f"Вікі в порядку: {len(pages())} сторінок, {len(code_files())} файлів коду, {len(routes_in_code())} маршрутів.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
