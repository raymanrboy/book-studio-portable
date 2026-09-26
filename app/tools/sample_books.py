"""Made-up Workshop books for the preview server and the tests — never the owner's real ones.

    make_books(folder) → three books in different states:
      40.moonlit-garden-lullaby  Tier H: formula, hero (canonical.png), story, text — prompts not yet;
                                 a hero variant G2_brunette (its hero prompt, swap prompts for spreads 3 and 4)
      41.little-lamb-prayers     Tier S: everything to the prompts (the cover's too), 5 of 16 rows in pictures/,
                                 Canva ticked
      42.new-book                just started: an empty agent/ folder
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

FORMULA_H = """Formula: A — Milestone Journey
Occasion: 1st birthday
Tone: playful
Tier: H = recurring hero child
Theme / central idea: a garden that grows along with the child
"""
FORMULA_S = """Formula: D — Anthology
Occasion: baptism
Tone: meditative
Tier: S = style/anthology, figures vary
Theme / central idea: little prayers for every part of the day
"""
BLUEPRINT = """# Story Blueprint

## Visual header
Palette: sage, cream, butter yellow. Mood: calm morning light.

## Spread 02 — The first seed
{Name} plants a seed with a little watering can.
"""
TEXT = """## Cover — Title
{Name}'s Moonlit Garden

## Spread 01 — Dedication
For {Name}, with love from {Gifter}.

## Spread 02 — The first seed
A tiny seed, a tiny hand,
a patch of warm and sleepy land.
"""
PROMPT = {"task": "one wide 2:1 watercolor illustration", "aspect_ratio": "2:1",
          "scene": {"setting": "a meadow at dawn"}, "negative": ["text", "letters"]}


def png(path: Path, size: tuple[int, int], color: tuple[int, int, int], label: str = "") -> Path:
    """A made-up picture: a flat colour with a lighter oval (and a label), so a cut or a mirror shows."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", size, color)
    d = ImageDraw.Draw(im)
    w, h = size
    d.ellipse((w * .3, h * .25, w * .7, h * .75), fill=tuple(min(255, c + 40) for c in color))
    if label:
        d.text((w * .08, h * .08), label, fill=(60, 60, 60))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path


def make_books(folder: Path) -> Path:
    folder = Path(folder)
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)

    h = folder / "40.moonlit-garden-lullaby" / "agent"
    h.mkdir(parents=True)
    (h / "formula.md").write_text(FORMULA_H, encoding="utf-8")
    (h / "canonical-prompt.md").write_text("```json\n" + json.dumps({"task": "a portrait", "aspect_ratio": "3:4"}, indent=2) + "\n```\n", encoding="utf-8")
    (h / "character-card.md").write_text("# Character card\nHair: soft brown curls. Eyes: warm brown.\n", encoding="utf-8")
    png(h / "canonical.png", (300, 400), (233, 214, 190))
    (h / "story-blueprint.md").write_text(BLUEPRINT, encoding="utf-8")
    (h / "book-text.md").write_text(TEXT, encoding="utf-8")
    v = h / "variants" / "G2_brunette"
    v.mkdir(parents=True)
    (v / "hero-prompt.md").write_text("Please edit the attached canonical image based on this JSON.\n\n```json\n"
                                      + json.dumps({"task": "identity-preserving edit", "change_set": {"hair": "brunette"}}, indent=2)
                                      + "\n```\n", encoding="utf-8")
    for n in (3, 4):
        (v / f"{n}.json").write_text(json.dumps({"edit_target": f"{n}.png", "character_reference": "hero.png",
                                                 "prompt": "Replace only the main toddler with the one from Image 2."}, indent=2),
                                     encoding="utf-8")

    s = folder / "41.little-lamb-prayers"
    a = s / "agent"
    a.mkdir(parents=True)
    (a / "formula.md").write_text(FORMULA_S, encoding="utf-8")
    (a / "story-blueprint.md").write_text(BLUEPRINT, encoding="utf-8")
    (a / "book-text.md").write_text(TEXT.replace("Moonlit Garden", "Little Prayers"), encoding="utf-8")
    spreads = "".join(f"```json\n{json.dumps(PROMPT, indent=2)}\n```\n" for _ in range(14))
    (a / "spread-prompts-json.md").write_text(spreads, encoding="utf-8")
    (a / "endpage-prompts-json.md").write_text(spreads.split("```\n", 1)[0] + "```\n", encoding="utf-8")
    colors = [(206, 225, 212), (240, 226, 196), (214, 222, 240)]
    for i, page in enumerate(range(1, 10)):
        png(s / "pictures" / f"{page}.png", (400, 400), colors[i % 3], str(page))
    (a / "cover-prompts-json.md").write_text("```json\n" + json.dumps(dict(PROMPT, task="one wide 2:1 panorama, "
                                             "main focus on the right"), indent=2) + "\n```\n", encoding="utf-8")
    (s / "book.json").write_text(json.dumps({"marks": {"canva": True}}), encoding="utf-8")

    (folder / "42.new-book" / "agent").mkdir(parents=True)
    return folder
