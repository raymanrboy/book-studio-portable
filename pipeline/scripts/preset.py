"""A medium preset from knowledge/media-presets.md, ready to paste: its full `"style": {...}` block and its `negative+`
list — so every prompt of a book carries the same paint system word for word.

    python preset.py --list       every preset: what it looks like (in Ukrainian, for the owner) and the books made in it
    python preset.py FG           the FG style block and its extra negatives
"""
import json
import re
import sys
from pathlib import Path

PIPELINE = Path(__file__).resolve().parent.parent
PRESETS = PIPELINE / "knowledge" / "media-presets.md"
_SECTION = re.compile(r"^## ([A-Z]{1,3}) - (.+)$", re.M)
_MEDIUM = re.compile(r"^(?:Medium:|- \*\*Visual Medium / Style:\*\*)\s*([A-Z]{1,3})\b", re.M)


def books_by_preset() -> dict[str, list[str]]:
    """Which books were made in which preset — by the blueprint's `Medium:` line, else the brief's."""
    out: dict[str, list[str]] = {}
    for book in sorted((PIPELINE / "books").glob("[0-9]*.*/agent")):
        for name in ("story-blueprint.md", "input.md"):
            f = book / name
            m = _MEDIUM.search(f.read_text(encoding="utf-8", errors="replace")) if f.is_file() else None
            if m:
                out.setdefault(m.group(1), []).append(book.parent.name.split(".", 1)[0])
                break
    return out


def presets() -> dict[str, dict]:
    text = PRESETS.read_text(encoding="utf-8")
    heads = list(_SECTION.finditer(text))
    out = {}
    for i, h in enumerate(heads):
        body = text[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        block = re.search(r"```json\n(.*?)\n```", body, re.S)
        neg = re.search(r"`negative\+`:\s*`(\[.*?\])`", body)
        if not block:
            continue
        style = json.loads("{" + block.group(1) + "}")["style"]      # the block is `"style": {...}` without braces
        look = {k: (re.search(rf"^\*\*{k}:\*\*\s*(.+)$", body, re.M) or [None, ""])[1].strip()
                for k in ("Коротко", "Як виглядає", "Найкраще для")}
        out[h.group(1)] = {"name": h.group(2).strip(), "style": style, "look": look,
                           "negative": json.loads(neg.group(1)) if neg else []}
    return out


def main(argv: list[str]) -> str:
    found = presets()
    if not argv or argv[0] == "--list":
        made = books_by_preset()
        return "\n\n".join(f"{code} — {p['look']['Коротко'] or p['name']}\n   {p['look']['Як виглядає']}\n"
                           f"   Найкраще для: {p['look']['Найкраще для']}\n"
                           f"   Книги в ньому: {', '.join(made.get(code, [])) or 'ще немає'}"
                           for code, p in found.items())
    code = argv[0].upper()
    if code not in found:
        sys.exit(f"No preset {code}; the codes: {', '.join(found)}")
    p = found[code]
    return ('"style": ' + json.dumps(p["style"], indent=2, ensure_ascii=False)
            + "\n\nnegative+ " + json.dumps(p["negative"], ensure_ascii=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(main(sys.argv[1:]))
