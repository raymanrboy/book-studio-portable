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
    quotes and the full stop after the name are not printed (the order card and the text check agree)."""
    return str(value or "").strip().strip("\"'“”‘’«» ").rstrip(".,;:!").strip()


def custom_text(variation: dict) -> bool:
    """A dedication / closing field in which the buyer wrote words of their own."""
    return bool(DEDICATION.search(str(variation.get("name") or ""))) and not is_default(str(variation.get("value") or ""))
