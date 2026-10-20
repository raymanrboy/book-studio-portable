"""Reading text: printed words compared word by word, how alike a page's first lines are to a library text, what
the buyer asked for (the child, the gifter, the dedication) and which library text each page is."""
from __future__ import annotations

import difflib
import re
import unicodedata

from .. import library
from ..wording import DEDICATION as _DEDICATION, alike, clean_name, guess_child_name, is_default, words


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
        elif not _said_alike(_spelled(a[i1:i2], printed), _spelled(b[j1:j2], printed)):
            ops.append({"expected": " ".join(a[i1:i2]), "printed": " ".join(b[j1:j2])})
    return ops


def _said_alike(x: list[str], y: list[str]) -> bool:
    """The same words, capitals by the same rule as an equal run (a «mary-kate» printed small still shows)."""
    return len(x) == len(y) and all(_same(p, q) for p, q in zip(x, y))


def _spelled(ws: list[str], printed: str) -> list[str]:
    """The words as said aloud (19.10.2026 calibration): «Godparents-John» laid out as «Godparents –\nJohn», and
    «James'» for «James's» — both spellings of a name ending in s (a reprint asked for «James'»); only where the page
    really carries the apostrophe: «James» alone for «James's» is a lost possessive."""
    out = []
    for w in ws:
        stem = re.sub(r"(?<=s)'s$", "", w, flags=re.I)
        if stem != w and not re.search(rf"(?<!\w){re.escape(stem)}'(?!\w)", alike(printed), re.I):
            stem = w
        out += [part for part in stem.split("-") if part]
    return out


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
# The buyer's headings, as typed into Etsy's box: «Closing:», «close:», «Closing» alone on its line; «Dedication -»,
# «DEDICATION:», «dedicati:» (Etsy's field cut the word). A text before a dedication heading is a note to the
# seller («Note: please center the text…») — not printed (06.10.2026 calibration).
_CLOSING = re.compile(r"\bclos(?:ing|e)(?:\s+message)?\s*:|^[ \t]*closing(?:\s+message)?[ \t]*(?:[-–—][ \t]*)?$",
                      re.I | re.M)
_DEDICATION_HEAD = re.compile(r"^[ \t]*dedicat\w*(?:\s+message)?[ \t]*(?:[:\-–—]|$)[ \t]*\n?", re.I | re.M)
_NAME_SLOT = re.compile(r"\{\s*name\s*\}", re.I)
_GIFTER_SLOT = re.compile(r"\{\s*gifter\s*\}", re.I)
# «With Love, Aunt Kate & Uncle Tom»: the buyer's own greeting — the template's «With love,» line then goes.
_GREETING = re.compile(r"^\s*(?:with\s+(?:(?:all\s+)?(?:of\s+)?(?:my|our)\s+)?love|(?:lots\s+of\s+|much\s+|all\s+"
                       r"(?:my|our)\s+)?love|from|xoxo|hugs)\b", re.I)
# «Happy Diwali» as the «from whom»: a wish of its own — «With love, Happy Diwali» is never printed (19.10.2026).
# Only first: «Grandma Sue. Merry Christmas!» still signs under the template's «With love,».
_WISH = re.compile(r"^\s*(?:happy|merry)\b", re.I)
_TEMPLATE_GREETING = re.compile(r"(?im)^[^\n{]{1,30},[ \t]*\n(?=[ \t]*\{\s*gifter\s*\})")


def personalization(item: dict) -> dict:
    """The child's name, who the book is from, and the buyer's own dedication / closing when there is one."""
    child = printed_name(item.get("childName") or guess_child_name([item]))  # «Leo & Mila.» -> «Leo & Mila»
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
    dedication, closing = split_dedication(raw)
    return {"child": child, "gifter": gifter, "dedication": dedication, "closing": closing}


def printed_name(value: str) -> str:
    """The child's name as the owner prints it: «kobe» typed in small letters is «Kobe» on every page (19.10.2026
    calibration: fifteen red rows on one book). A name typed with any capital is kept as typed («McKenzie»)."""
    name = clean_name(value)
    if name != name.lower():
        return name
    # «leo and mila» → «Leo and Mila», «de la cruz» → «de la Cruz», «o'neil» → «O'Neil»
    return re.sub(r"(?<![\w'])\w+|(?<=\b\w')\w+", lambda m: m.group() if m.group() in COMMON | _PARTICLES
                  else m.group()[0].upper() + m.group()[1:], name)


_PARTICLES = {"de", "la", "le", "del", "della", "da", "di", "dos", "van", "von", "der", "den", "du", "bin", "ibn"}


def split_dedication(raw: str) -> tuple[str | None, str | None]:
    """The buyer's own box: (dedication, closing), each None when it is the book's default."""
    if not raw or is_default(raw):
        return None, None
    parts = _CLOSING.split(raw, maxsplit=1)
    head = _DEDICATION_HEAD.search(parts[0])
    dedication = (parts[0][head.end():] if head else parts[0]).strip() or None
    if dedication and is_default(dedication):
        dedication = None
    closing = None
    if len(parts) > 1 and "default" not in {w.casefold() for w in words(parts[1])}:
        closing = parts[1].strip() or None
    return dedication, closing


def signs_off(gifter: str) -> bool:
    """«God bless you… Love, Pop-pop and Nonna», «We love you baby boy! Love, Mama & Dada»: the buyer's «from whom»
    carries its own «Love,» — the template's «With love,» line goes, as when it starts with one."""
    said = [s.lstrip(" \"'“”‘’«»") for s in re.split(r"[.!?\n]+", gifter or "") if s.strip()]
    return any(_GREETING.match(s) for s in said) or bool(said and _WISH.match(said[0]))


def fill(template: str, child: str, gifter: str) -> str | None:
    """A library text as it must be printed for this order; None when a placeholder cannot be filled."""
    text = template or ""
    if gifter and signs_off(gifter):
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
