"""A new Workshop book: the next number (= the Etsy listing's number: the highest book folder + 1, `_later` and the like
not counted) and its folder `books/<number>.<slug>/agent/`. The Workshop makes the rest of the folder itself.

    python new_book.py little-otter-christmas      → books/56.little-otter-christmas/agent
"""
import re
import sys
from pathlib import Path

BOOKS = Path(__file__).resolve().parent.parent / "books"


def next_number() -> int:
    numbers = [int(m.group(1)) for p in BOOKS.iterdir() if p.is_dir() and (m := re.match(r"^(\d+)\.", p.name))]
    return max(numbers, default=0) + 1


def main(slug: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    if not slug:
        sys.exit("Give the book a short English slug, e.g. little-otter-christmas")
    folder = BOOKS / f"{next_number()}.{slug}" / "agent"
    folder.mkdir(parents=True)
    return folder


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    print(main(sys.argv[1]))
