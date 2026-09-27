"""What the buyer wrote, read the same way everywhere: printed words, which Etsy field is the dedication, and
whether its value only asks for the book's own text («DEFAULT»). The order card marks «свій текст» and the
text check expects the template's dedication by the same rule (22.09.2026 audit: they disagreed)."""
from __future__ import annotations

import re
import unicodedata

QUOTES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "`": "'", "´": "'", "“": '"', "”": '"', "„": '"',
                        "«": '"', "»": '"'})
DASHES = re.compile("[‐-―−]")
_TOKEN = re.compile(r"[\w{}\[\]'\-]+")

_POSSESSIVE = re.compile(r"(?<=\w\w)['’]s$", re.I)          # «Leo's» — the buyer thought of «Leo's Baptism Day»
DEDICATION = re.compile(r"dedicat|closing|присвят", re.I)   # the Etsy field of the buyer's own words
META = {"dedication", "closing", "message", "messages", "and", "default", "defaults", "please", "use", "the",
        "standard", "both", "is", "fine", "ok", "okay", "keep", "as", "one"}


def words(text: str) -> list[str]:
    """Printed words without punctuation; quotes, apostrophes and dashes of every style made alike.
    Capitals and accents stay: «Zoe» is not «Zoë»."""
    text = DASHES.sub("-", unicodedata.normalize("NFC", text or "").translate(QUOTES))
    return [w for w in (t.strip("-'") for t in _TOKEN.findall(text)) if w]


def is_default(value: str) -> bool:
    """«DEFAULT», "“DEFAULT “", «Dedication and Closing   Default» — the book's own text is wanted."""
    ws = [w.casefold() for w in words(value)]
    return not ws or (("default" in ws or "defaults" in ws) and all(w in META for w in ws))


def clean_name(value: str) -> str:
    """The child's name as it is printed: «"Leo."» -> «Leo», «Leo & Mila.» -> «Leo & Mila» — the buyer's
    quotes and the full stop after the name are not printed (the order card and the text check agree).
    «Leo's» -> «Leo»: the covers say «{Name}'s Baptism Day» themselves (25.09.2026 calibration: the
    possessive made every page of one order red)."""
    name = str(value or "").strip().strip("\"'“”‘’«» ").rstrip(".,;:!").strip()
    return _POSSESSIVE.sub("", name).strip()


def alike(text: str) -> str:
    """The text with quotes and dashes of every style made alike, letter for letter (the same length)."""
    return DASHES.sub("-", text.translate(QUOTES))


_NAME_HINT = re.compile(r"(child|kid|baby|boy|girl|name|ім'я|имя)", re.I)


def guess_child_name(items: list) -> str:
    """The child's name from what the buyer filled in: a field named like one, else «Name: …» inside a value. The
    order card, the Order Creator's picker and the text check read it here."""
    for item in items or []:
        for v in item.get("variations") or []:
            name, value = (v.get("name") or ""), (v.get("value") or "").strip()
            if _NAME_HINT.search(name) and value and len(value) <= 40 and "\n" not in value:
                return clean_name(value)
        for v in item.get("variations") or []:
            value = (v.get("value") or "")
            m = re.search(r"(?:child'?s?\s*name|name)\s*[:\-–]\s*([^\n,;]{2,40})", value, re.I)
            if m:
                return clean_name(m.group(1))
    return ""


def custom_text(variation: dict) -> bool:
    """A dedication / closing field in which the buyer wrote words of their own."""
    return bool(DEDICATION.search(str(variation.get("name") or ""))) and not is_default(str(variation.get("value") or ""))
