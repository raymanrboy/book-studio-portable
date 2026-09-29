"""The slides' files: the template (the six drawings every book starts from) and a book's slides (its set).

    app/studio/slides/design/slideN.json   the design as first drawn (in git) — «Скинути» of the template goes back to it
    app/data/slides/design/slideN.json     the owner's template: his touches, carried to every new book
    app/data/slides/sets/<id>/             a book's slides: set.json, scenes/slideN.json, books/ (the cut-out books
                                           and their shadows), pictures/ (Dedication, page 30)

A scene is {id, title, bg, items[]} — every element with its kind, its centre (x, y on the 1000×1000 stage), size
and angle (wiki/features/slides.md). A book on a slide names its *slot* (which mockup: open1:1…4, open2:1…2, cover),
a flat picture its slot too (dedication, page30): the same six drawings serve every book, each set says which
pictures fill the slots.

Every save carries the version the editor started from: a scene changed on disk meanwhile (the agent, working on
the same slide) is never overwritten — the editor takes the new one (the owner, 29.09.2026: "sometimes it will be
easier for me to work through an LLM").
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from pathlib import Path

from .. import core

SLIDES = [f"slide{n}" for n in range(1, 7)]
FACTORY = Path(__file__).with_name("design")
ROOT = core.data_path("slides")
DESIGN = ROOT / "design"
SETS = ROOT / "sets"
TEMPLATE = "template"                       # «where» for the template itself
SET_ID = r"\d{8}-\d{6}-[0-9a-f]{6}"

# The mockups a book's slides hold, in the order they are filled (the Mockups' picks order)
BOOK_SLOTS = ["open1:1", "open1:2", "open1:3", "open1:4", "open2:1", "open2:2", "cover"]
PICTURE_SLOTS = ["dedication", "page30"]
SLOT_KIND = {"open1": "open1", "open2": "open2", "cover": "cover1"}
SLOT_LABEL = {"open1:1": "Open 1 · 1", "open1:2": "Open 1 · 2", "open1:3": "Open 1 · 3", "open1:4": "Open 1 · 4",
              "open2:1": "Open 2 · 1", "open2:2": "Open 2 · 2", "cover": "Cover 1",
              "dedication": "Dedication", "page30": "Сторінка 30"}
NUMBERS = {"pages": 24, "poems": 11}        # «24 unique pages», «11 unique little poems» (the owner, 29.09.2026)

KINDS = ("blob", "grain", "band", "book", "dashes", "leaves", "sticker", "sparkle", "text", "arrow", "image",
         "ribbon", "heart")
MAX_ITEMS = 200


def _fail(text: str, status: int = 400):
    from ..server import ApiError
    return ApiError(text, status)


# ---------------------------------------------------------------- where a scene lives

def valid_where(where: str) -> str:
    where = str(where or TEMPLATE)
    if where != TEMPLATE and not re.fullmatch(SET_ID, where):
        raise _fail("Некоректний запит.")
    if where != TEMPLATE and not (SETS / where / "set.json").is_file():
        raise _fail("Слайдів цієї книги вже немає.", 404)
    return where


def valid_slide(slide: str) -> str:
    if slide not in SLIDES:
        raise _fail("Такого слайда немає.")
    return slide


def scene_path(where: str, slide: str) -> Path:
    return DESIGN / f"{slide}.json" if where == TEMPLATE else SETS / where / "scenes" / f"{slide}.json"


def _version(path: Path) -> str:
    try:
        return hashlib.sha1(path.read_bytes()).hexdigest()[:12]
    except OSError:
        return ""


def factory(slide: str) -> dict:
    return json.loads((FACTORY / f"{slide}.json").read_text(encoding="utf-8"))


def template(slide: str) -> dict:
    """The owner's template of this slide, else the design as first drawn."""
    path = DESIGN / f"{slide}.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            core.log.warning("Slides: the template's %s is damaged — the first design is used", slide)
    return factory(slide)


def load(where: str, slide: str) -> tuple[dict, str]:
    """A scene and its version ("" — not on disk yet: the template's first design)."""
    path = scene_path(where, slide)
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8")), _version(path)
        except ValueError:
            core.log.warning("Slides: %s is damaged — its template is shown", path)
    return (template(slide) if where != TEMPLATE else factory(slide)), ""


def check(scene) -> dict:
    """A scene as the editor (or the agent) sends it: a dict with items, each a known kind with a numeric centre."""
    if not isinstance(scene, dict) or not isinstance(scene.get("items"), list):
        raise _fail("Слайд прийшов без елементів.")
    if len(scene["items"]) > MAX_ITEMS:
        raise _fail("Забагато елементів на слайді.")
    for item in scene["items"]:
        if not isinstance(item, dict) or item.get("type") not in KINDS:
            raise _fail(f"Невідомий елемент: {item.get('type') if isinstance(item, dict) else item!r}.")
        for key in ("x", "y"):
            if not isinstance(item.get(key, 0), (int, float)):
                raise _fail(f"«{item.get('name') or item['type']}»: {key} — не число.")
    return scene


def save(where: str, slide: str, scene: dict, base: str | None) -> str:
    """Writes a scene; `base` — the version the change was made on. A scene changed on disk meanwhile is refused
    (409, with the current one). None — no check (the command line)."""
    path = scene_path(where, slide)
    current = _version(path)
    if base is not None and base != current:
        from ..server import ApiError
        now, version = load(where, slide)
        raise ApiError("Слайд тим часом змінився.", 409, {"scene": now, "version": version})
    scene = check(scene)
    scene["id"] = slide
    core.write_json(path, scene, backup=False)
    return _version(path)


def reset(where: str, slide: str) -> tuple[dict, str]:
    """«Скинути слайд»: a book's slide back to the template, the template back to its first design."""
    scene = template(slide) if where != TEMPLATE else factory(slide)
    return scene, save(where, slide, scene, None)


def to_template(where: str, slide: str) -> None:
    """«Зробити шаблоном»: a book's slide becomes the template for every book made after it."""
    scene, _ = load(where, slide)
    save(TEMPLATE, slide, scene, None)


def sig(where: str) -> str:
    """Changes anywhere in these slides (a scene, the set) — what the editor asks for every 1.5 s."""
    folder = DESIGN if where == TEMPLATE else SETS / where
    stamps = []
    for path in sorted(folder.rglob("*.json")) if folder.is_dir() else []:
        try:
            stamps.append(f"{path.name}:{path.stat().st_mtime_ns}")
        except OSError:
            pass
    return hashlib.sha1("|".join(stamps).encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------- a book's set

def set_dir(set_id: str) -> Path:
    return SETS / set_id


def read_set(set_id: str) -> dict:
    rec = core.read_json(set_dir(set_id) / "set.json", None)
    if not isinstance(rec, dict):
        raise _fail("Слайдів цієї книги вже немає.", 404)
    return rec


def write_set(rec: dict) -> None:
    core.write_json(set_dir(rec["id"]) / "set.json", rec, backup=False)


def list_sets() -> list[dict]:
    out = []
    for path in sorted(SETS.glob("*/set.json"), reverse=True) if SETS.is_dir() else []:
        rec = core.read_json(path, None)
        if isinstance(rec, dict) and re.fullmatch(SET_ID, str(rec.get("id") or "")):
            out.append(rec)
    return out


def newest_set() -> str | None:
    sets = list_sets()
    return sets[0]["id"] if sets else None


def slot_file(slot: str) -> str:
    return slot.replace(":", "-")


def new_set(name: str, folder: str, numbers: dict | None = None) -> dict:
    set_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{core.new_id()[:6]}"
    rec = {"id": set_id, "name": name, "folder": folder, "created": core.now_iso(),
           "numbers": {**NUMBERS, **(numbers or {})}, "books": {}, "pictures": {}, "baked": {}}
    for slide in SLIDES:  # every slide starts as the template
        core.write_json(set_dir(set_id) / "scenes" / f"{slide}.json", {**template(slide), "id": slide}, backup=False)
    write_set(rec)
    return rec


def put_book(rec: dict, slot: str, cut_folder: Path, source: str) -> None:
    """A cut-out book into a slot of the set (its own copy: the cut cache may be cleaned)."""
    books = set_dir(rec["id"]) / "books"
    books.mkdir(parents=True, exist_ok=True)
    name = slot_file(slot)
    shutil.copyfile(cut_folder / "book.png", books / f"{name}.png")
    shutil.copyfile(cut_folder / "shadow.png", books / f"{name}_shadow.png")
    info = json.loads((cut_folder / "info.json").read_text(encoding="utf-8"))
    rec["books"][slot] = {k: info[k] for k in ("cx", "cy", "w", "aspect")} | {"source": source}


PICTURE_MAX = 2400   # a flat picture on a 2000² slide never needs more


def put_picture(rec: dict, slot: str, source: Path) -> None:
    from PIL import Image
    pictures = set_dir(rec["id"]) / "pictures"
    pictures.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as im:
        im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
        if max(im.size) > PICTURE_MAX:
            im.thumbnail((PICTURE_MAX, PICTURE_MAX), Image.LANCZOS)
        im.save(pictures / f"{slot}.png", compress_level=3)
    rec["pictures"][slot] = {"source": source.name}


def delete_set(set_id: str) -> None:
    if re.fullmatch(SET_ID, set_id) and set_dir(set_id).is_dir():
        shutil.rmtree(set_dir(set_id), ignore_errors=True)


def forget_old_sets(keep: int = 12) -> None:
    """A book's slides are kept for the last dozen books (their pictures are in the owner's folder anyway)."""
    for rec in list_sets()[keep:]:
        delete_set(rec["id"])

