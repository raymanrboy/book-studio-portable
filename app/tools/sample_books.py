"""Made-up Workshop books for the preview server and the tests — never the owner's real ones.

    make_books(folder) → three books in different states:
      40.moonlit-garden-lullaby  Tier H: formula, hero (canonical.png), story, text — prompts not yet;
                                 a hero variant G2_brunette (its hero prompt, swap prompts for spreads 3 and 4);
                                 four looks with their hero.png (G3_blond, G4_east_asian, G5_redhead, G6_afro) —
                                 the listing slide 7's frames;
                                 the photo mockups' references in mockups/ (Cover 1, Cover & Open 1, the Canva cover)
      41.little-lamb-prayers     Tier S: everything to the prompts (the cover's too), 5 of 16 rows in pictures/,
                                 Canva ticked
      42.new-book                just started: an empty agent/ folder

    make_photo_templates(folder) → the photo mockups' made-up templates: a scene with a blank white book, per category.
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


def book_shot(path: Path, size: tuple[int, int], scene: tuple[int, int, int], books: list[tuple], book=(250, 250, 250),
              label: str = "") -> Path:
    """A made-up photo: a coloured scene with a book (white — a template's blank book; coloured — a mockup's)."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", size, scene)
    d = ImageDraw.Draw(im)
    for box in books:
        d.rectangle(tuple(v + 8 for v in box), fill=tuple(max(0, c - 40) for c in scene))  # its shadow
        d.rectangle(box, fill=book)
    if label:
        d.text((16, 14), label, fill=(40, 40, 40))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path


# category → its made-up templates: (name, size, the scene's colour, the blank books)
PHOTO_TEMPLATES = {
    "main": [("main-01-pink-roses.png", (900, 900), (236, 214, 212), [(250, 250, 650, 650)]),
             ("main-02-leaf-shadows.png", (900, 900), (214, 226, 208), [(240, 230, 660, 640)]),
             ("main-03-fairy-lights.png", (900, 900), (90, 104, 140), [(260, 240, 640, 660)])],
    "product": [("product-01-sofa-sunset.png", (900, 900), (214, 206, 198), [(280, 250, 640, 640)])],
    "grandma": [("grandma-01-baby-daylight.png", (900, 820), (214, 200, 184), [(280, 360, 640, 560)]),
                ("grandma-02-baby-evening.png", (900, 820), (150, 128, 110), [(300, 380, 660, 580)])],
    "child": [("child-01-cream-outfit.png", (900, 900), (226, 214, 196), [(260, 330, 640, 700)])],
    "shelf": [("shelf-01-side-table-bunny-duck.png", (900, 900), (222, 214, 200), [(330, 300, 580, 560)]),
              ("shelf-02-middle-shelf.png", (900, 900), (208, 200, 186), [(340, 320, 590, 580)])],
    "video": [("video-01-sofa.png", (540, 960), (196, 188, 176), [(90, 360, 380, 640)]),
              ("video-02-kitchen.png", (540, 960), (200, 196, 186), [(140, 310, 390, 550)])],
    "size": [("size-01-softcover-hardcover.png", (900, 900), (226, 220, 212), [(120, 330, 400, 640), (460, 250, 820, 640)])],
}


def hero_png(path: Path, hair: tuple[int, int, int], skin: tuple[int, int, int] = (246, 214, 190)) -> Path:
    """A made-up look of the hero: a toddler drawn in a few shapes on a white page, 2:3 (as Gemini gives them)."""
    from PIL import Image, ImageDraw
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", (400, 600), (253, 253, 251))
    d = ImageDraw.Draw(im)
    d.ellipse((120, 560, 280, 590), fill=(236, 214, 196))                       # the floor's shadow
    d.rounded_rectangle((135, 250, 265, 470), 30, fill=(236, 150, 60), outline=(120, 70, 40), width=4)   # overalls
    d.rectangle((150, 470, 190, 560), fill=(236, 150, 60), outline=(120, 70, 40), width=4)
    d.rectangle((210, 470, 250, 560), fill=(236, 150, 60), outline=(120, 70, 40), width=4)
    d.ellipse((115, 70, 285, 250), fill=skin, outline=(120, 70, 40), width=4)    # the head
    d.chord((105, 50, 295, 200), 180, 360, fill=hair, outline=(120, 70, 40), width=4)
    for x in (170, 230):
        d.ellipse((x - 9, 150, x + 9, 172), fill=(60, 40, 30))
    d.arc((175, 170, 225, 210), 20, 160, fill=(150, 60, 50), width=4)
    im.save(path)
    return path


def make_photo_templates(folder: Path) -> Path:
    folder = Path(folder)
    for key, shots in PHOTO_TEMPLATES.items():
        for name, size, scene, blank in shots:
            book_shot(folder / key / name, size, scene, blank, label=name.rsplit(".", 1)[0])
    return folder


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

    for name, hair in (("G3_blond", (232, 196, 110)), ("G4_east_asian", (35, 30, 30)), ("G6_afro", (60, 40, 30)),
                       ("G5_redhead", (214, 90, 40))):
        hero_png(h / "variants" / name / "hero.png", hair)

    m = folder / "40.moonlit-garden-lullaby" / "mockups"   # what the Mockups leave: the photo mockups' references
    book_shot(m / "1. Cover 1.png", (800, 600), (225, 225, 230), [(250, 110, 550, 490)], (70, 90, 150))
    book_shot(m / "Cover & Open 1 (6-7).png", (800, 600), (150, 105, 70), [(90, 250, 330, 490), (360, 110, 740, 340)],
              (70, 90, 150))
    png(m / "canva-cover.png", (1074, 570), (70, 90, 150), "back | spine | front")

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


def seed_workshop() -> None:
    """The Workshop's made-up books (tools/sample_books.py) in the preview's own books folder, and an empty made-up
    Downloads the generation mode watches — only when there are none yet (a book the preview changed stays)."""
    from studio import core
    if not core.WORKSHOP_BOOKS.is_dir() or not any(core.WORKSHOP_BOOKS.iterdir()):
        make_books(core.WORKSHOP_BOOKS)
    templates = core.data_path("photo-mockups")
    if not templates.is_dir() or not any(templates.iterdir()):
        make_photo_templates(templates)
    core.data_path("downloads").mkdir(parents=True, exist_ok=True)
