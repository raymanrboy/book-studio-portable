"""Claude Code hooks for the book pipeline and the owner's secrets (wired in .claude/settings.json).

    book_guard.py pre    PreToolUse  Write|Edit       a book's files outside agent/ are the Workshop's; a Tier H book's
                                                      story, text and prompts wait for canonical.png
    book_guard.py bash   PreToolUse  Bash|PowerShell  never print .secrets.txt or vault.json
    book_guard.py post   PostToolUse Write|Edit       after a book file is written: the book check, its FAILs to Claude

Exit 2 with a reason on stderr blocks the call (pre) or hands the reason back to Claude (post); anything this script
cannot read or understand lets the call through — a hook must never stop unrelated work.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PIPELINE = Path(__file__).resolve().parents[2] / "pipeline"
BOOKS = PIPELINE / "books"
GATED = {"story-blueprint.md", "book-text.md", "spread-prompts-json.md", "endpage-prompts-json.md", "abc-prompts-json.md",
         "cover-prompts-json.md", "preflight-report.md"}
DRAFT = "DRAFT - NOT READY"
_TIER = re.compile(r"Tier\W{0,6}(H|S)\b", re.IGNORECASE)          # as the Workshop reads it (workshop/books.py)
_SECRET = r"(?:\.secrets\.txt|vault\.json)"
# A command that prints a file starts a command (the line, or after | ; & or "("); a word inside an argument or a message
# (git diff HEAD -- …, find -type f, "never print .secrets.txt") is not one. Best effort: the Read deny rules are the wall.
_SECRET_READ = re.compile(r"(?:^|[|;&(]\s*)(?:cat|type|more|less|head|tail|sed|awk|bat|get-content|gc|select-string|sls|"
                          r"copy|cp|xcopy|copy-item|notepad|code)\b[^|;&\n]*" + _SECRET
                          + r"|readall(?:text|lines|bytes)\s*\([^)]*" + _SECRET, re.IGNORECASE | re.MULTILINE)


def book_of(path: Path) -> tuple[Path, Path] | None:
    """(the book folder, the path inside it) for a file under pipeline/books/<book>/, else None. A book set aside in a
    folder such as `_later/` is `_later/<book>/`."""
    try:
        rel = path.resolve().relative_to(BOOKS.resolve())
    except ValueError:
        return None
    depth = 2 if rel.parts and rel.parts[0].startswith("_") else 1
    return (BOOKS.joinpath(*rel.parts[:depth]), Path(*rel.parts[depth:])) if len(rel.parts) > depth else None


def tier_h(agent: Path, written: str = "") -> bool:
    """Is it a Tier H book — by formula.md, else the blueprint, else the file being written (a first blueprint)."""
    texts = [(agent / n).read_text(encoding="utf-8", errors="replace") for n in ("formula.md", "story-blueprint.md")
             if (agent / n).is_file()]
    for text in texts + [written]:
        m = _TIER.search(text[:200_000])
        if m:
            return m.group(1).upper() == "H"
    return False


def pre(data: dict) -> str | None:
    tool = data.get("tool_input") or {}
    path = tool.get("file_path")
    found = book_of(Path(path)) if path else None
    if not found:
        return None
    book, inner = found
    if inner.parts[0] != "agent":
        return (f"{inner} belongs to the Workshop (Book Studio), not to the book agent: write only into "
                f"{book.name}/agent/.")
    agent = book / "agent"
    written = (tool.get("content") or "") + (tool.get("new_string") or "")
    if inner.name in GATED and "variants" not in inner.parts and tier_h(agent, written):
        if not any(agent.glob("canonical*.png")):
            target = book / inner
            existing = target.read_text(encoding="utf-8", errors="replace") if target.is_file() else ""
            if DRAFT not in written and DRAFT not in existing:
                return (f"{book.name} is a Tier H book and agent/canonical.png is not there yet: the story, text and "
                        f"prompts wait for the hero (the Hero stop). Ask the owner to generate and save canonical.png; "
                        f"only if he explicitly asked to draft ahead, start the file with '{DRAFT}'.")
    return None


def bash(data: dict) -> str | None:
    command = (data.get("tool_input") or {}).get("command") or ""
    if _SECRET_READ.search(command):
        return ("This command would print the owner's keys (.secrets.txt / app/data/vault.json). Never read them unless "
                "the owner asks for exactly that.")
    return None


def post(data: dict) -> str | None:
    path = (data.get("tool_input") or {}).get("file_path")
    found = book_of(Path(path)) if path else None
    if not found or found[1].parts[0] != "agent" or found[1].suffix != ".md":
        return None
    book = found[0]
    run = subprocess.run([sys.executable, "-B", str(PIPELINE / "check_book.py"), str(book)], capture_output=True,
                         text=True, encoding="utf-8", errors="replace", timeout=60)
    fails = [line.strip() for line in run.stdout.splitlines() if "[FAIL]" in line]
    if fails:
        return f"The book check of {book.name} after this write:\n" + "\n".join(fails)
    return None


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
        reason = {"pre": pre, "bash": bash, "post": post}[mode](data)
    except Exception:                                   # a broken hook must not block unrelated work
        return 0
    if reason:
        sys.stderr.write(reason + "\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
