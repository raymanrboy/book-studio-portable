"""The cover's reference from the owner's best frames: the spreads stacked one under another with a white gap, saved in
the book's agent/ as ref_cover_<frames>.jpg (the cover tool pastes it as the reference — it takes one picture).

    python stack_frames.py <book folder> 04-05 06-07 10-11
"""
import sys
from pathlib import Path

from PIL import Image

WIDTH, GAP = 1600, 24


def original(folder: Path, frame: str) -> Path:
    """The spread as the generator gave it — the Workshop keeps .jpg, .png or .webp."""
    found = sorted((folder / "originals").glob(f"spread-{frame}.*"))
    if not found:
        sys.exit(f"No originals/spread-{frame}.* in {folder}")
    return found[0]


def main(book: str, frames: list[str]) -> Path:
    folder = Path(book)
    pics = [Image.open(original(folder, f)).convert("RGB") for f in frames]
    rows = [p.resize((WIDTH, round(p.height * WIDTH / p.width)), Image.LANCZOS) for p in pics]
    sheet = Image.new("RGB", (WIDTH, sum(r.height for r in rows) + GAP * (len(rows) - 1)), "white")
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height + GAP
    name = f"ref_cover_spread-{frames[0]}.jpg" if len(frames) == 1 else f"ref_cover_hybrid-{'-'.join(frames)}.jpg"
    out = folder / "agent" / name
    sheet.save(out, quality=90)
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    print(main(sys.argv[1], sys.argv[2:]))
