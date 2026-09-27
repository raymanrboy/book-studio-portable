"""Reading text: printed words compared word by word, how alike a page's first lines are to a library text, what
the buyer asked for (the child, the gifter, the dedication) and which library text each page is."""
from __future__ import annotations

import difflib
import re
import unicodedata

from .. import library
from ..wording import DEDICATION as _DEDICATION, clean_name, guess_child_name, is_default, words


MATCH = 0.45             # how alike a page's first lines and a library text must be to call them one


# words() — the printed words, quotes and dashes made alike — is in wording.py: the order card reads the
# buyer's fields by the same rules.

def _caps(word: str) -> bool:
    return len(word) > 1 and word.isupper()  # set in capitals by the design: FLOWER GIRL OLIVIA


def _same(a: str, b: str) -> bool:
    return a == b or ((_caps(a) or _caps(b)) and a.casefold() == b.casefold())


def diff(expected: str, printed: str) -> list[dict]:
    """Where the printed words differ from the expected ones: [{expected, printed}], either side may be ''."""
    a, b = words(expected), words(printed)
    ops = []
    matcher = difflib.SequenceMatcher(a=[w.casefold() for w in a], b=[w.casefold() for w in b], autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            ops += [{"expected": x, "printed": y} for x, y in zip(a[i1:i2], b[j1:j2]) if not _same(x, y)]
        else:
            ops.append({"expected": " ".join(a[i1:i2]), "printed": " ".join(b[j1:j2])})
    return ops


def similarity(read: list[str], reference: list[str]) -> float:
    """How alike a page's first lines are to the start of a library text (0…1)."""
    if len(read) < 3 or not reference:
        return 0.0
    a = [w.casefold() for w in reference[:len(read) + 4]]
    return difflib.SequenceMatcher(a=a, b=[w.casefold() for w in read], autojunk=False).ratio()


def _plain(word: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", word.casefold()) if not unicodedata.combining(c))


def _distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _base_word(word: str) -> str:
    return re.sub(r"'s$", "", word, flags=re.I) if len(word) > 3 else word


# Everyday words that look like names to a spelling rule (Ann ~ And, Mila ~ Mile): never a child's name typo.
COMMON = set("""a about after again all always an and any are around as at away back be because bed been before
began being best big bless blessed blue book both bright but by came can close come could day days dear did do
does dream dreams each even ever every eyes far feel filled find first fly for forever friend friends from full
gave gentle get give glad go god good grace great grew grow had hand hands happy has have he heart hearts her here
high him his hold home hope how i if in into is it its joy just keep kind know laugh let life light like little
live long look love loved made make many may me mile miles more morning most much my name need never new night no
not now of off on once one only or our out over own peace play please rest ride right said saw say see she shine
shining side sky sleep smile so some soft soon star stars stay still such sun sweet take tell than that the their
them then there these they thing things this those through time to today together told too took tree true two up
upon us very want was way we well went were what when where which while who whole why will wish with world would
year years yes yet you young your yours""".split())

_GIFTER = re.compile(r"\bfrom\b|від кого|gift", re.I)
_CLOSING = re.compile(r"\bclosing(?:\s+message)?\s*:", re.I)
_DEDICATION_HEAD = re.compile(r"^\s*dedication(?:\s+message)?\s*:\s*", re.I)
_NAME_SLOT = re.compile(r"\{\s*name\s*\}", re.I)
_GIFTER_SLOT = re.compile(r"\{\s*gifter\s*\}", re.I)
# «With Love, Aunt Kate & Uncle Tom»: the buyer's own greeting — the template's «With love,» line then goes.
_GREETING = re.compile(r"^\s*(?:with\s+(?:(?:all\s+)?(?:of\s+)?(?:my|our)\s+)?love|(?:lots\s+of\s+|much\s+|all\s+"
                       r"(?:my|our)\s+)?love|from|xoxo|hugs)\b", re.I)
_TEMPLATE_GREETING = re.compile(r"(?im)^[^\n{]{1,30},[ \t]*\n(?=[ \t]*\{\s*gifter\s*\})")


def personalization(item: dict) -> dict:
    """The child's name, who the book is from, and the buyer's own dedication / closing when there is one."""
    child = clean_name(item.get("childName") or guess_child_name([item]))  # «Leo & Mila.» -> «Leo & Mila»
    gifter, raw = "", ""
    for v in item.get("variations") or []:
        name, value = str(v.get("name") or ""), str(v.get("value") or "").strip()
        if _DEDICATION.search(name):
            raw = value
        elif _GIFTER.search(name) and not gifter:
            gifter = value
    # «"With love ,Anna and Mark"» → «With love, Anna and Mark»: the owner does not print the buyer's slips
    gifter = re.sub(r"\s+([,.!])", r"\1", gifter.strip().strip("\"'“”‘’«»").strip())
    gifter = re.sub(r",(?=[^\s\d])", ", ", gifter)
    dedication = closing = None
    if not is_default(raw):
        parts = _CLOSING.split(raw, maxsplit=1)
        dedication = _DEDICATION_HEAD.sub("", parts[0]).strip() or None
        if dedication and is_default(dedication):
            dedication = None
        if len(parts) > 1 and "default" not in {w.casefold() for w in words(parts[1])}:
            closing = parts[1].strip() or None
    return {"child": child, "gifter": gifter, "dedication": dedication, "closing": closing}


def fill(template: str, child: str, gifter: str) -> str | None:
    """A library text as it must be printed for this order; None when a placeholder cannot be filled."""
    text = template or ""
    if gifter and _GREETING.match(gifter.lstrip(" \"'“”‘’«»")):
        text = _TEMPLATE_GREETING.sub("", text)
    if (_NAME_SLOT.search(text) and not child) or (_GIFTER_SLOT.search(text) and not gifter):
        return None
    text = _GIFTER_SLOT.sub(lambda m: gifter, _NAME_SLOT.sub(lambda m: child, text))
    return None if "{" in text else text


def assign(count: int, reads: dict[int, str], refs: dict[str, str]) -> dict[int, str]:
    """Story page -> library text ("spread5"). A full book (30 pages) has every spread where the library
    has it — then a page that differs is still that spread's page, even when its text is another one. A
    shorter book lacks some spreads but keeps the order, so the best order-keeping match of first lines to
    texts wins (only matches above MATCH count)."""
    spreads = [[p for p in (first, first + 1) if p < count] for first in range(2, count, 2)]
    keys = [f"spread{n}" for n in library.SPREAD_NUMBERS if refs.get(f"spread{n}")]
    ref_words = {k: words(refs[k]) for k in keys}
    read_words = {p: words(reads.get(p, "")) for sp in spreads for p in sp}
    if len(spreads) == len(library.SPREAD_NUMBERS):
        out = {}
        for pair, n in zip(spreads, library.SPREAD_NUMBERS):
            key = f"spread{n}"
            lettered = [p for p in pair if read_words[p]]
            if key in ref_words and lettered:
                out[max(lettered, key=lambda p: (similarity(read_words[p], ref_words[key]), len(read_words[p])))] = key
        return out

    def score(i: int, j: int) -> tuple[float, int]:
        best = max(((similarity(read_words[p], ref_words[keys[j]]), p) for p in spreads[i]), default=(0.0, 0))
        return best if best[0] >= MATCH else (0.0, 0)

    scores = [[score(i, j) for j in range(len(keys))] for i in range(len(spreads))]
    total = [[0.0] * (len(keys) + 1) for _ in range(len(spreads) + 1)]
    for i in range(1, len(spreads) + 1):
        for j in range(1, len(keys) + 1):
            s = scores[i - 1][j - 1][0]
            total[i][j] = max(total[i - 1][j], total[i][j - 1], total[i - 1][j - 1] + s if s else 0.0)
    out: dict[int, str] = {}
    i, j = len(spreads), len(keys)
    while i and j:
        s, page = scores[i - 1][j - 1]
        if s and total[i][j] == total[i - 1][j - 1] + s:
            out[page] = keys[j - 1]
            i, j = i - 1, j - 1
        elif total[i][j] == total[i - 1][j]:
            i -= 1
        else:
            j -= 1
    return out
