"""The slides' files: the schemes (whole looks of the six slides, one of them the default for new books) and a book's
slides (its set).

    app/studio/slides/design/slideN.json   the design as first drawn (in git) — the last «Скинути» goes back to it
    app/data/slides/schemes/<key>/         a scheme: scheme.json (name, default) + slide1…7.json — "not only the colours
                                           but the settings of the whole mockup" (the owner, 29.09.2026): Nature (the
                                           default), Night, and whatever the owner saves from the editor
    pipeline/books/<n>.<slug>/mockups/slides/   a Workshop book's slides (since 29.09.2026 — "tied to the book in the
                                           Workshop, not to a session"): set.json, scenes/, books/ (the cut-out books
                                           and their shadows), pictures/ (Dedication, page 30)
    app/data/slides/sets/<time>-<id>/      slides made before that, or for a folder that is no Workshop book

A scene is {id, title, bg, items[]} — every element with its kind, its centre (x, y on the 1000×1000 stage), size
and angle (wiki/features/slides.md). A book on a slide names its *slot* (which mockup: open1:1…4, open2:1…2, cover),
a flat picture its slot too (dedication, page30): the same six drawings serve every book, each set says which
pictures fill the slots. «template» — where the default scheme is edited in place.

Slide 7 — the hero's looks (the owner, 2026-10-02): only for a book whose hero has variants (agent/variants/<B2_blond>/
hero.png); each look in its own frame, hero:1 … hero:7, on its own white background, its name («B2») under it.

Every save carries the version the editor started from: a scene changed on disk meanwhile (the agent, working on
the same slide) is never overwritten — the editor takes the new one (the owner, 29.09.2026: "sometimes it will be
easier for me to work through an LLM").
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
from pathlib import Path

from .. import core

SLIDES = [f"slide{n}" for n in range(1, 8)]
LOOKS_SLIDE = "slide7"                      # the hero's looks: shown only for a book with two looks or more (2026-10-02)
FACTORY = Path(__file__).with_name("design")
ROOT = core.data_path("slides")
DESIGN = ROOT / "design"                    # the template before schemes (29.09.2026) — becomes the scheme Nature
SCHEMES = ROOT / "schemes"
SETS = ROOT / "sets"
TEMPLATE = "template"                       # «where» for the default scheme, edited in place
SCHEME_WHERE = "scheme:"                    # «where» for any scheme, edited in place: «scheme:night» (2026-09-30)
SET_ID = r"\d{8}-\d{6}-[0-9a-f]{6}"
BOOK_ID = r"\d{1,5}\.[^\\/:*?\"<>|]+"        # a Workshop book's folder: «25.sleepy-trucks-bedtime»
SCHEME_KEY = r"[a-z0-9][a-z0-9-]{0,39}"
BOOK_PRESET = "book:"                       # a Workshop book's slides offered as a preset for another book

# The mockups a book's slides hold, in the order they are filled (the Mockups' picks order)
BOOK_SLOTS = ["open1:1", "open1:2", "open1:3", "open1:4", "open2:1", "open2:2", "cover"]
PICTURE_SLOTS = ["dedication", "page30"]
HERO_SLOTS = [f"hero:{n}" for n in range(1, 8)]   # the hero's looks on slide 7, in the order of their names
SLOT_KIND = {"open1": "open1", "open2": "open2", "cover": "cover1"}
SLOT_LABEL = {"open1:1": "Open 1 · 1", "open1:2": "Open 1 · 2", "open1:3": "Open 1 · 3", "open1:4": "Open 1 · 4",
              "open2:1": "Open 2 · 1", "open2:2": "Open 2 · 2", "cover": "Cover 1",
              "dedication": "Dedication", "page30": "Сторінка 30", **{s: f"Герой {s[5:]}" for s in HERO_SLOTS}}
NUMBERS = {"pages": 24, "poems": 11}        # «24 unique pages», «11 unique little poems» (the owner, 29.09.2026)

KINDS = ("blob", "grain", "band", "book", "dashes", "leaves", "sticker", "sparkle", "text", "arrow", "image",
         "ribbon", "heart")
MAX_ITEMS = 200


def _fail(text: str, status: int = 400):
    from ..server import ApiError
    return ApiError(text, status)


def _read(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------- the schemes

def ensure_schemes() -> None:
    """The first scheme, Nature, is the template as it was — made once, from the owner's template if there is one."""
    if SCHEMES.is_dir() and any(SCHEMES.glob("*/scheme.json")):
        _new_slides()
        return
    target = SCHEMES / "nature"
    target.mkdir(parents=True, exist_ok=True)
    for slide in SLIDES:
        src = DESIGN / f"{slide}.json"
        shutil.copyfile(src if src.is_file() else FACTORY / f"{slide}.json", target / f"{slide}.json")
    core.write_json(target / "scheme.json", {"name": "Nature", "default": True, "saved": core.now_iso(),
                                             "from": "the template"}, backup=False)


def _recoloured(slide: str, folder: Path) -> dict:
    """A slide the scheme never had (slide 7, 2026-10-02), in the scheme's colours: drawn on slide 4, so the colours slide
    4 has in the first design are swapped for the ones it has in this scheme (Night's slide 7 comes out blue)."""
    first, mine = factory("slide4"), _read(folder / "slide4.json") or {}
    swap = {str(first.get("bg")).lower(): mine.get("bg")} if mine.get("bg") else {}
    named = {e.get("name"): e for e in mine.get("items") or [] if isinstance(e, dict)}
    for e in first["items"]:
        twin = named.get(e.get("name")) or {}
        for k in ("color", "textColor"):
            if isinstance(e.get(k), str) and isinstance(twin.get(k), str):
                swap.setdefault(e[k].lower(), twin[k])
    scene = factory(slide)
    if isinstance(scene.get("bg"), str):
        scene["bg"] = swap.get(scene["bg"].lower(), scene["bg"])
    for e in scene["items"]:
        for k in ("color", "textColor"):
            if isinstance(e.get(k), str):
                e[k] = swap.get(e[k].lower(), e[k])
    return scene


def _new_slides() -> None:
    for meta in SCHEMES.glob("*/scheme.json"):
        for slide in SLIDES:
            path = meta.parent / f"{slide}.json"
            if not path.exists():
                core.write_json(path, {**_recoloured(slide, meta.parent), "id": slide}, backup=False)


def list_schemes() -> list[dict]:
    ensure_schemes()
    out = []
    for path in sorted(SCHEMES.glob("*/scheme.json")):
        meta = _read(path) or {}
        key = path.parent.name
        if re.fullmatch(SCHEME_KEY, key):
            out.append({"key": key, "name": str(meta.get("name") or key), "default": bool(meta.get("default")),
                        "colours": meta.get("colours") or {}})
    if out and not any(s["default"] for s in out):
        next((s for s in out if s["key"] == "nature"), out[0])["default"] = True
    return out


def scheme_of(where: str) -> str | None:
    """«scheme:night» → «night»: a scheme edited in place, with no book behind it."""
    w = str(where or "")
    key = w[len(SCHEME_WHERE):] if w.startswith(SCHEME_WHERE) else ""
    return key if re.fullmatch(SCHEME_KEY, key) else None


def is_plain(where: str) -> bool:
    """The default scheme («template») or a scheme picked by its key — slides with no book, no pictures, no numbers."""
    return where == TEMPLATE or scheme_of(where) is not None


def default_scheme() -> str | None:
    return next((s["key"] for s in list_schemes() if s["default"]), None)


def scheme_dir(key: str) -> Path:
    if not re.fullmatch(SCHEME_KEY, str(key or "")):
        raise _fail("Такої схеми немає.", 404)
    return SCHEMES / key


def scheme_name(key: str) -> str:
    return next((s["name"] for s in list_schemes() if s["key"] == key), key)


def _slug(name: str) -> str:
    table = str.maketrans("абвгґдеєжзиіїйклмнопрстуфхцчшщьюя", "abvggdeezziiijklmnoprstufhccss'uy")
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().translate(table)).strip("-")[:40].strip("-")
    return slug or f"scheme-{core.new_id()[:6]}"


def save_scheme(where: str, name: str, default: bool = False) -> str:
    """«Зберегти як схему»: the six slides as they are here, under a name (the same name — that scheme replaced)."""
    name = " ".join(str(name or "").split())[:60]
    if not name:
        raise _fail("Назвіть схему.")
    same = next((s for s in list_schemes() if s["name"].lower() == name.lower()), None)
    key = same["key"] if same else _slug(name)
    while not same and (SCHEMES / key).exists():
        key = f"{key[:33]}-{core.new_id()[:6]}"
    folder = SCHEMES / key
    folder.mkdir(parents=True, exist_ok=True)
    for slide in SLIDES:
        scene, _ = load(where, slide)
        core.write_json(folder / f"{slide}.json", {**scene, "id": slide}, backup=False)
    meta = _read(folder / "scheme.json") or {}
    meta.update(name=name, saved=core.now_iso(), **{"from": where})
    core.write_json(folder / "scheme.json", meta, backup=False)
    if default:
        set_default(key)
    return key


def set_default(key: str) -> None:
    """The scheme every new book's slides start from."""
    scheme_dir(key)
    for s in list_schemes():
        path = SCHEMES / s["key"] / "scheme.json"
        meta = _read(path) or {}
        meta["default"] = s["key"] == key
        core.write_json(path, meta, backup=False)


def presets(exclude: str | None = None) -> list[dict]:
    """What the editor offers to put on a book: the schemes, and the other Workshop books' slides ("presets that will
    be used in other books too, e.g. in another bedtime book" — the owner, 29.09.2026)."""
    out = [{**s, "kind": "scheme"} for s in list_schemes()]
    for rec in workshop_sets():
        if rec["id"] != exclude:
            out.append({"key": BOOK_PRESET + rec["id"], "name": rec.get("name") or rec["id"], "default": False,
                        "kind": "book"})
    return out


def preset_scene(key: str, slide: str) -> dict:
    if key.startswith(BOOK_PRESET):
        where = valid_where(key[len(BOOK_PRESET):])
        return load(where, slide)[0]
    path = scheme_dir(key) / f"{slide}.json"
    if not path.parent.is_dir():
        raise _fail("Такої схеми немає.", 404)
    return _read(path) or template(slide)


def apply_preset(where: str, key: str) -> None:
    """A scheme (or another book's slides) put on these six slides — the book's pictures and numbers stay."""
    scenes = {slide: preset_scene(key, slide) for slide in SLIDES}   # all read first: a missing one changes nothing
    for slide, scene in scenes.items():
        save(where, slide, {**scene, "id": slide}, None)
    if not is_plain(where):
        rec = read_set(where)
        rec["scheme"] = key
        write_set(rec)


# ---------------------------------------------------------------- where a scene lives

def is_book(where: str) -> bool:
    return bool(re.fullmatch(BOOK_ID, str(where or ""))) and not re.fullmatch(SET_ID, str(where or ""))


def book_folder(book_id: str) -> Path:
    """A Workshop book's folder (refused unless it is one)."""
    from ..workshop.books import book_path
    return book_path(book_id)


def valid_where(where: str) -> str:
    where = str(where or TEMPLATE)
    if where == TEMPLATE:
        return where
    if scheme_of(where):
        if not (scheme_dir(scheme_of(where)) / "scheme.json").is_file():
            raise _fail("Такої схеми немає.", 404)
        return where
    if not (re.fullmatch(SET_ID, where) or is_book(where)):
        raise _fail("Некоректний запит.")
    if is_book(where):
        book_folder(where)
    if not (set_dir(where) / "set.json").is_file():
        raise _fail("Слайдів цієї книги вже немає.", 404)
    return where


def shown(where: str, rec: dict | None = None) -> list[str]:
    """The slides these are: a scheme has all seven; a book's — slide 7 only when its hero has two looks or more."""
    if is_plain(where):
        return list(SLIDES)
    rec = rec if rec is not None else read_set(where)
    looks = sum(1 for s in HERO_SLOTS if s in (rec.get("pictures") or {}))
    return [s for s in SLIDES if s != LOOKS_SLIDE or looks >= 2]


def valid_slide(slide: str) -> str:
    if slide not in SLIDES:
        raise _fail("Такого слайда немає.")
    return slide


def scene_path(where: str, slide: str) -> Path:
    if scheme_of(where):
        return scheme_dir(scheme_of(where)) / f"{slide}.json"
    if where == TEMPLATE:
        ensure_schemes()
        return SCHEMES / (default_scheme() or "nature") / f"{slide}.json"
    return set_dir(where) / "scenes" / f"{slide}.json"


def _version(path: Path) -> str:
    try:
        return hashlib.sha1(path.read_bytes()).hexdigest()[:12]
    except OSError:
        return ""


def factory(slide: str) -> dict:
    return json.loads((FACTORY / f"{slide}.json").read_text(encoding="utf-8"))


def template(slide: str) -> dict:
    """This slide of the default scheme, else the design as first drawn."""
    ensure_schemes()
    key = default_scheme()
    scene = _read(SCHEMES / key / f"{slide}.json") if key else None
    if scene is None:
        core.log.warning("Slides: the default scheme's %s is missing or damaged — the first design is used", slide)
    return scene or factory(slide)


def load(where: str, slide: str) -> tuple[dict, str]:
    """A scene and its version ("" — not on disk yet)."""
    path = scene_path(where, slide)
    if path.is_file():
        scene = _read(path)
        if scene is not None:
            return scene, _version(path)
        core.log.warning("Slides: %s is damaged — its template is shown", path)
    return (template(slide) if not is_plain(where) else factory(slide)), ""


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
    (409, with the current one). None — no check (the command line, a scheme put on)."""
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
    """«Скинути слайд»: a book's slide back to its scheme (the one put on it, else the default); the default scheme
    back to its first design."""
    if is_plain(where):
        scene = factory(slide)
    else:
        key = read_set(where).get("scheme")
        try:
            scene = preset_scene(key, slide) if key else template(slide)
        except Exception:
            scene = template(slide)
    return scene, save(where, slide, scene, None)


def sig(where: str) -> str:
    """Changes anywhere in these slides (a scene, the set) — what the editor asks for every 1.5 s."""
    folder = scene_path(where, "slide1").parent if is_plain(where) else set_dir(where)
    stamps = []
    for path in sorted(folder.rglob("*.json")) if folder.is_dir() else []:
        try:
            stamps.append(f"{path.name}:{path.stat().st_mtime_ns}")
        except OSError:
            pass
    return hashlib.sha1("|".join(stamps).encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------- a book's set

def set_dir(set_id: str) -> Path:
    if is_book(set_id):
        return core.WORKSHOP_BOOKS / set_id / "mockups" / "slides"
    return SETS / set_id


def out_dir(rec: dict) -> Path:
    """Where a set's slides are baked: a Workshop book's etsy/ folder (beside its photo mockups — the owner,
    30.09.2026), else the set's own folder, beside its mockups."""
    if is_book(rec.get("id") or ""):
        return book_folder(rec["id"]) / "etsy"
    return Path(rec["folder"])


def _baked_file(book: Path, name: str) -> Path:
    """A book's baked slide by its name: in etsy/, with or without the listing's number («05 Listing 1.png»), else
    beside the mockups."""
    from ..photos import bare
    etsy = book / "etsy"
    try:
        with os.scandir(etsy) as entries:
            found = next((e.name for e in entries if e.is_file() and bare(e.name) == bare(name)), None)
    except OSError:
        found = None
    return etsy / found if found else book / "mockups" / name


def mockups_dir(book_id: str) -> Path:
    """Where a Workshop book's mockups go — no question asked (the owner, 29.09.2026)."""
    folder = book_folder(book_id) / "mockups"
    folder.mkdir(exist_ok=True)
    return folder


def read_set(set_id: str) -> dict:
    rec = core.read_json(set_dir(set_id) / "set.json", None)
    if not isinstance(rec, dict):
        raise _fail("Слайдів цієї книги вже немає.", 404)
    rec["id"] = set_id   # a Workshop book's number may change with its folder: the folder says who it is
    if is_book(set_id):
        rec["folder"] = str(set_dir(set_id).parent)
        rec["name"] = _book_name(set_id)
        book = set_dir(set_id).parent.parent   # its folder may have been renamed: the names are kept, not the paths
        # baked into etsy/ (beside the mockups before 30.09.2026), where the listing's number goes in front of the name
        rec["baked"] = {k: str(_baked_file(book, Path(v).name)) for k, v in (rec.get("baked") or {}).items()}
    return rec


def write_set(rec: dict) -> None:
    core.write_json(set_dir(rec["id"]) / "set.json", rec, backup=False)


def _book_name(book_id: str) -> str:
    from ..workshop.books import display_name
    return display_name(book_id)


def workshop_sets() -> list[dict]:
    """The Workshop books that have slides, by number (newest first)."""
    from ..workshop.books import book_ids
    out = []
    for book_id in reversed(book_ids()):
        if is_book(book_id) and (set_dir(book_id) / "set.json").is_file():
            try:
                out.append(read_set(book_id))
            except Exception:
                continue
    return out


def list_sets() -> list[dict]:
    """Every book's slides: the Workshop books', then the ones made before (newest first)."""
    out = workshop_sets()
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


def new_set(name: str, folder: str, numbers: dict | None = None, book: str | None = None,
            scheme: str | None = None, fresh: bool = False) -> dict:
    """A book's slides. For a Workshop book: in its folder, one set; made again, its pictures are new and its six
    scenes stay as the owner left them — unless `fresh` («Зробити заново»: from the scheme again)."""
    if book:
        set_id = book
        folder_path = set_dir(book)
        old = read_set(book) if (folder_path / "set.json").is_file() else None
        for part in ("books", "pictures"):
            shutil.rmtree(folder_path / part, ignore_errors=True)
    else:
        set_id, old = f"{time.strftime('%Y%m%d-%H%M%S')}-{core.new_id()[:6]}", None
    keep_scenes = bool(old) and not fresh
    key = scheme or (old or {}).get("scheme") if keep_scenes else scheme or default_scheme()
    rec = {"id": set_id, "name": name, "folder": folder, "created": (old or {}).get("created") or core.now_iso(),
           "numbers": {**NUMBERS, **((old or {}).get("numbers") or {}), **(numbers or {})},
           "books": {}, "pictures": {}, "baked": (old or {}).get("baked") or {}, "scheme": key}
    if not keep_scenes:
        for slide in SLIDES:  # every slide starts as the scheme
            try:
                scene = preset_scene(key, slide) if key else template(slide)
            except Exception:
                scene = template(slide)
            core.write_json(set_dir(set_id) / "scenes" / f"{slide}.json", {**scene, "id": slide}, backup=False)
    write_set(rec)
    return rec


def put_book(rec: dict, slot: str, cut_folder: Path, source: str) -> None:
    """A cut-out book into a slot of the set (its own copy: the cut cache goes when the program closes)."""
    books = set_dir(rec["id"]) / "books"
    books.mkdir(parents=True, exist_ok=True)
    name = slot_file(slot)
    shutil.copyfile(cut_folder / "book.png", books / f"{name}.png")
    shutil.copyfile(cut_folder / "shadow.png", books / f"{name}_shadow.png")
    info = json.loads((cut_folder / "info.json").read_text(encoding="utf-8"))
    rec["books"][slot] = {k: info[k] for k in ("cx", "cy", "w", "aspect")} | {"source": source}


PICTURE_MAX = 2400   # a flat picture on a 2000² slide never needs more


def put_picture(rec: dict, slot: str, source, name: str = "", cut: bool = False) -> None:
    """A flat picture into a slot (a path or a picture); `cut` — its background is see-through (Dedication without its
    background): drawn without a white card under it."""
    from PIL import Image
    pictures = set_dir(rec["id"]) / "pictures"
    pictures.mkdir(parents=True, exist_ok=True)
    if isinstance(source, Image.Image):
        im, label = source, name
    else:
        with Image.open(source) as opened:
            im = opened.copy()
        label = name or Path(source).name
    im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
    if max(im.size) > PICTURE_MAX:
        im.thumbnail((PICTURE_MAX, PICTURE_MAX), Image.LANCZOS)
    im.save(pictures / f"{slot_file(slot)}.png", compress_level=3)
    rec["pictures"][slot] = {"source": label, "aspect": round(im.height / im.width, 4), **({"cut": True} if cut else {})}


def delete_set(set_id: str) -> None:
    if re.fullmatch(SET_ID, set_id) and set_dir(set_id).is_dir():
        shutil.rmtree(set_dir(set_id), ignore_errors=True)


def forget_old_sets(keep: int = 12) -> None:
    """The slides made before the Workshop books had them are kept for the last dozen (a Workshop book keeps its own)."""
    old = [r for r in list_sets() if re.fullmatch(SET_ID, r["id"])]
    for rec in old[keep:]:
        delete_set(rec["id"])


# ---------------------------------------------------------------- cleaning (the owner, 29.09.2026)

def clean_temporary() -> None:
    """The quite temporary things go when the program starts and closes: the cut-outs' cache, the bake's browser
    files. What the owner keeps — the mockups, «Без фону», the slides — is in the book's folder."""
    from . import cutout
    for folder in (cutout.CUTS, core.data_path("tmp", "slides"), core.data_path("tmp", "slides-browser")):
        shutil.rmtree(folder, ignore_errors=True)


def book_done(book_id: str) -> None:
    """The book is done (passed to the library): its slides' cache goes — the smaller copies of the books and pictures
    the editor draws with. The six scenes stay: a preset for other books."""
    if not is_book(book_id):
        return
    folder = set_dir(book_id)
    for part in ("books", "pictures"):
        shutil.rmtree(folder / part, ignore_errors=True)
    if (folder / "set.json").is_file():
        rec = read_set(book_id)
        rec["books"], rec["pictures"], rec["done"] = {}, {}, core.now_iso()
        write_set(rec)
    core.log.info("Slides: %s is done — its slides' cache went, the scenes stay as a preset", book_id)
