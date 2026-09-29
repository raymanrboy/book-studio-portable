"""Photo mockups (Фотомокапи, the owner, 30.09.2026): lifestyle photos with a blank white book — a grandmother
reading, a child holding it, a shelf — in which the generator puts our real book.

The owner picks a template photo of a category; the clipboard then holds, one after another (Ctrl+V in Chrome puts in
the next, as the Workshop's other several-part pastes): the template, the book's reference picture (for a Workshop
book), and the category's prompt — change nothing in the photo but the book. The photo he downloads from the generator
is caught into the book's `etsy/` folder (workshop/generate.py). Without a book (the «Фотомокапи» page) only the
template and the prompt go into the clipboard — he adds the cover himself, nothing is caught.

    app/data/photo-mockups/<category>/<category>-NN-<what>.png   the templates — copies, the owner's own set
    pipeline/books/<book>/mockups/1. Cover 1.png …               the references the Mockups made for the book
    pipeline/books/<book>/mockups/canva-cover.png                the flat cover from the Canva ZIP (the grandmother)
    pipeline/books/<book>/etsy/photo-<category>.png              the results, beside the listing slides (Listing N.png)
                                                                 and copies of the whole-scene mockups (Cover & Open 1,
                                                                 All & Open 1) — the owner's etsy/ folder, 30.09.2026

Every name inside Book Studio is English; the page says it in Ukrainian (the owner, 30.09.2026).
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
from pathlib import Path

from . import core, desktop
from .server import ApiError

ETSY = "etsy"             # a Workshop book's folder of what goes into its Etsy listing: the slides and these photos
MOCKUPS = "mockups"
CANVA_COVER = "canva-cover"
RESULT = "photo-{key}"    # etsy/photo-main.png …

# The categories, in the page's order; `ref` — which of the book's pictures goes into the clipboard second.
CATEGORIES = [
    {"key": "main", "label": "Головне фото", "ref": "cover1"},
    {"key": "open-book", "label": "Відкрита книга", "ref": "cover-open"},
    {"key": "grandma", "label": "Бабуся читає", "ref": "canva-cover"},
    {"key": "child", "label": "У руках дитини", "ref": "cover1"},
    {"key": "shelf", "label": "На полиці", "ref": "cover1"},
    {"key": "video", "label": "Для відео", "ref": "cover1"},   # 9:16 phone photos for the listing's video
    {"key": "size", "label": "Розмір", "ref": "cover1"},       # the two formats side by side: softcover and hardcover
]
BY_KEY = {c["key"]: c for c in CATEGORIES}

# The book's reference pictures: how they are found in its mockups/ folder and what to do when one isn't there.
REFS = {
    "cover1": {"label": "Cover 1", "prefix": "1. cover 1",
               "missing": "Немає мокапу «Cover 1» — він з'являється в папці мокапів книги після «Зберегти відкриті» в Мокапах."},
    "cover-open": {"label": "Cover & Open 1", "prefix": "cover & open 1",
                   "missing": "Немає мокапу «Cover & Open 1» — він з'являється в папці мокапів книги після «Зберегти відкриті» в Мокапах."},
    "canva-cover": {"label": "Обкладинка з Canva", "prefix": None,
                    "missing": "Немає обкладинки з Canva — вона береться з архіву Canva, коли для книги робляться Мокапи, "
                               "або перетягніть її на рамку «Обкладинка з Canva»."},
}


def templates_dir() -> Path:
    return core.data_path("photo-mockups")


def category(key: str) -> dict:
    c = BY_KEY.get(str(key or ""))
    if not c:
        raise ApiError("Невідома категорія фото.", 404)
    return c


def _pictures(folder: Path) -> list[os.DirEntry]:
    try:
        with os.scandir(folder) as it:
            return sorted((e for e in it if e.is_file() and e.name.lower().endswith(core.IMAGE_EXTS)),
                          key=lambda e: e.name.lower())
    except OSError:
        return []


def _tag(e: os.DirEntry) -> str:
    st = e.stat()
    return f"{st.st_size:x}{st.st_mtime_ns:x}"


# ---------------------------------------------------------------- the templates

def _size(path: str) -> list[int] | None:
    """A picture's size from its header alone — the page lays the tiles out before the previews come."""
    from PIL import Image
    try:
        with Image.open(path) as im:
            return list(im.size)
    except (OSError, Image.DecompressionBombError):
        return None


def templates() -> list[dict]:
    """The categories with their templates, read from the folders each time (a file put there by hand counts)."""
    base = templates_dir()
    return [{**c, "refLabel": REFS[c["ref"]]["label"],
             "templates": [{"name": e.name, "v": _tag(e), "size": _size(e.path)} for e in _pictures(base / c["key"])]}
            for c in CATEGORIES]


def signature() -> str:
    """Changes whenever a template appears, changes or goes — the page redraws itself then."""
    h = hashlib.sha1()
    for c in CATEGORIES:   # only the folders' listings — no picture is opened
        for e in _pictures(templates_dir() / c["key"]):
            h.update(f"{c['key']}/{e.name}:{_tag(e)}\0".encode("utf-8", "replace"))
    return h.hexdigest()[:16]


def template_file(key: str, name: str) -> Path:
    """A template only by a name that really is in its category's folder."""
    folder = templates_dir() / category(key)["key"]
    name = str(name or "")
    if name != Path(name).name or name not in {e.name for e in _pictures(folder)}:
        raise ApiError("Заготовку не знайдено.", 404)
    return folder / name


def _suffix(name: str) -> str:
    suffix = Path(name).suffix.lower()
    return ".jpg" if suffix == ".jpeg" else suffix if suffix in core.IMAGE_EXTS else ".png"


def add_template(key: str, source: Path, name: str) -> dict:
    """A photo dropped onto a category: copied in with the category's next number — `shelf-06.png`."""
    from .workshop.pictures import open_picture
    c = category(key)
    open_picture(source, name)  # only a real picture goes in
    folder = templates_dir() / c["key"]
    folder.mkdir(parents=True, exist_ok=True)
    numbers = [int(m.group(1)) for e in _pictures(folder) if (m := re.match(rf"{re.escape(c['key'])}-(\d+)", e.name))]
    target = folder / f"{c['key']}-{max(numbers, default=0) + 1:02d}{_suffix(name)}"
    shutil.copyfile(source, target)
    core.log.info("Photo mockups: a new template %s", target.name)
    return {"category": c["key"], "name": target.name}


def remove_template(key: str, name: str) -> dict:
    """A template out of the set — into the Windows Recycle Bin, never deleted for good."""
    path = template_file(key, name)
    desktop.to_recycle_bin(path)
    core.log.info("Photo mockups: template %s went to the Recycle Bin", path.name)
    return {"removed": path.name}


def open_folder(key: str = "") -> None:
    folder = templates_dir() / category(key)["key"] if key else templates_dir()
    folder.mkdir(parents=True, exist_ok=True)
    if not core.SANDBOX:
        desktop.open_in_explorer(folder)


# ---------------------------------------------------------------- the prompts (one JSON object per category)

def _prompt(image_2: str, scene: str, placement: list[str], extra_negative: list[str] = ()) -> dict:
    return {
        "task": "product photo edit: put our real children's book into the photo in place of the blank white book",
        "inputs": {
            "image_1": "the finished lifestyle photo — the scene to keep",
            "image_2": image_2,
        },
        "scene": scene,
        "edit_scope": "replace ONLY the blank white book; nothing else in Image 1 changes",
        "no_blank_left": "the whole placeholder book becomes our book — cover, spine and cover edges in our book's "
                         "colours; no white surface of the blank book may remain visible",
        "book_placement": placement,
        "preserve_exactly": [
            "framing, crop, aspect ratio and camera angle",
            "lighting, colours, shadows and reflections",
            "background, furniture, props and textiles",
            "people, faces, expressions, hands and fingers",
            "the book's position, size, perspective, tilt, bend, thickness, corners and the shadow it casts",
        ],
        "cover_fidelity": [
            "artwork, colours and title exactly as in Image 2 — same illustration, same letters, spelled the same",
            "text reads normally, never mirrored",
            "no text, logos or details of your own",
        ],
        "realism": "the cover takes the scene's light and shadows — photographed there, not pasted on; fingers or "
                   "objects over the book stay on top of it",
        "ignore": "Image 2's background and everything around the book in it",
        "output": {"size": "the same size and aspect ratio as Image 1", "count": 1},
        "negative": ["restyling, relighting or re-imagining the scene", "moving or resizing the book",
                     "changing hands, faces or props", "mirrored or invented text", "extra books", "watermarks",
                     "borders", *extra_negative],
    }


FRONT = "a photo of our book, closed — its front cover with the illustration and the title"

PROMPTS = {
    "main": _prompt(
        FRONT,
        "a top-down flat lay: the closed book lies on a soft blanket among toys, flowers and nursery decor",
        ["our front cover on the top face of the book, edge to edge",
         "the visible spine and cover edges in our book's colours, as in Image 2 — no white strip left"]),
    "open-book": _prompt(
        "a photo of our book twice: closed, showing its front cover, and lying open on a spread",
        "a top-down view of two blank white books: one closed, one lying open",
        ["the closed blank book gets the front cover from Image 2",
         "the open blank book gets the open spread from Image 2 — both pages, their pictures and text copied exactly",
         "the open pages keep their curve toward the gutter and the soft shadow in the fold"],
        ["pages or text of your own on the open book"]),
    "grandma": _prompt(
        "our book's flat printed cover: the left half is the back cover, the narrow strip in the middle is the spine, "
        "the right half is the front cover with the title; the thin margin along its edges is trim — leave it out",
        "a grandmother holds the book open, facing herself, while reading to a child — so the camera sees the book's "
        "outside",
        ["the back cover on the left half of the book as seen by the camera, the spine at the fold, the front cover "
         "with the title on the right half",
         "follow the book's perspective, its opening angle and the bend of the covers",
         "the inside pages are not seen — do not draw them"],
        ["drawing the inside pages", "the cover flat or unbent"]),
    "child": _prompt(
        FRONT,
        "a small child holds the closed book in front of them, its front cover facing the camera",
        ["our front cover on the front of the book, edge to edge",
         "the child's fingers along the edges stay over the cover, exactly as they are"]),
    "shelf": _prompt(
        FRONT,
        "the closed book stands on a shelf among nursery decor, its front cover facing the camera",
        ["our front cover on the front of the book, edge to edge",
         "the spine and edges in our book's colours; the shelf's shadow and any reflection stay"]),
    "video": _prompt(
        FRONT,
        "a casual vertical 9:16 phone photo at home: the closed book lies on a sofa, a kitchen counter or a coffee "
        "table, a satin bow beside it",
        ["our front cover on the top face of the book, edge to edge, in the photo's perspective",
         "the visible spine and cover edges in our book's colours — no white strip left",
         "the bow, the surface and the phone photo's natural light and grain stay exactly as they are"],
        ["a studio look", "changing the 9:16 frame"]),
    "size": _prompt(
        FRONT,
        "two hands hold up two blank books side by side to compare their sizes: on the left a small thin softcover "
        "(saddle-stitched, a soft paper cover), on the right a large square hardcover with a rounded spine",
        ["the same front cover of ours on BOTH books, each edge to edge, scaled to its own book",
         "each book keeps its own size, thickness and binding — the small one stays a thin stapled softcover, the "
         "large one a hardcover with its spine; the difference in size is the point of the photo",
         "the hardcover's visible spine in our book's colours — no white strip left",
         "the thumbs and fingers over the books stay on top, exactly as they are"],
        ["making the two books the same size", "a different cover on either book"]),
}


def prompt(key: str) -> str:
    from .workshop.rows import as_prompt
    return as_prompt(PROMPTS[category(key)["key"]])


# ---------------------------------------------------------------- a Workshop book's references and results

def references(book: Path) -> dict[str, str | None]:
    """The book's reference pictures in its mockups/ folder: Cover 1 and Cover & Open 1 (the newest when a run
    saved another beside it, «… (2).png»), and the Canva cover."""
    entries = _pictures(book / MOCKUPS)
    out: dict[str, str | None] = {}
    for key, ref in REFS.items():
        if ref["prefix"]:
            found = [e for e in entries if e.name.lower().startswith(ref["prefix"])]
        else:
            found = [e for e in entries if Path(e.name).stem.lower() == CANVA_COVER]
        out[key] = max(found, key=lambda e: e.stat().st_mtime).name if found else None
    return out


def results(book: Path) -> dict[str, str]:
    """category → the file of its finished photo in etsy/."""
    names = {Path(e.name).stem.lower(): e.name for e in _pictures(book / ETSY)}
    return {c["key"]: names[RESULT.format(key=c["key"])] for c in CATEGORIES if RESULT.format(key=c["key"]) in names}


def count(book: Path) -> int:
    return len(results(book))


def state(book: Path) -> dict:
    """What the book's «Фото» step shows: the references, a card per category, how many are done."""
    from .workshop import books
    refs = references(book)
    done = results(book)
    record = books.state(book).get("photos") or {}
    return {
        "refs": [{"key": k, "label": r["label"], "name": refs[k], "missing": r["missing"]} for k, r in REFS.items()],
        "cards": [{"key": c["key"], "label": c["label"], "ref": c["ref"], "refLabel": REFS[c["ref"]]["label"],
                   "photo": done.get(c["key"]), "template": (record.get(c["key"]) or {}).get("template")}
                  for c in CATEGORIES],
        "count": len(done), "total": len(CATEGORIES),
    }


def items(book_id: str | None, key: str, template: str) -> tuple[str, list[dict]]:
    """What goes into the clipboard, in order: the template, the book's reference (for a Workshop book), the prompt."""
    c = category(key)
    out = [{"kind": "image", "label": "фото-заготовка", "path": str(template_file(key, template))}]
    if book_id:
        from .workshop import books
        book = books.book_path(book_id)
        ref = references(book)[c["ref"]]
        if not ref:
            raise ApiError(REFS[c["ref"]]["missing"])
        out.append({"kind": "image", "label": REFS[c["ref"]]["label"], "path": str(book / MOCKUPS / ref)})
    out.append({"kind": "text", "label": "промпт", "text": prompt(key)})
    return f"Фото · {c['label']}", out


def _retire_all(book: Path, folder: Path, stem: str) -> None:
    from .workshop.pictures import _retire
    for e in _pictures(folder):
        if Path(e.name).stem.lower() == stem:
            _retire(book, Path(e.path))


def place(book_id: str, key: str, source: Path, name: str, template: str | None = None, take: bool = False) -> dict:
    """A finished photo into the book's etsy/ folder as `photo-<category>`; the one before goes to .replaced/.
    `take` moves the file (a download) instead of copying it."""
    from .workshop import books
    from .workshop.pictures import _move, open_picture
    c = category(key)
    book = books.book_path(book_id)
    open_picture(source, name)  # only a real picture goes anywhere, and nothing is moved before that
    folder = book / ETSY
    folder.mkdir(exist_ok=True)
    stem = RESULT.format(key=c["key"])
    _retire_all(book, folder, stem)
    target = folder / f"{stem}{_suffix(name)}"
    if take:
        _move(source, target)
    else:
        shutil.copyfile(source, target)

    def change(data):
        photos = data.setdefault("photos", {})
        photos[c["key"]] = {"template": template or (photos.get(c["key"]) or {}).get("template"),
                            "from": Path(name).name[:160], "at": core.now_iso()}
    books.update_state(book, change)
    core.log.info("Photo mockups: %s → %s/%s", name, book_id, target.name)
    return {"key": f"photo:{c['key']}", "label": c["label"], "note": f"Фото «{c['label']}» на місці"}


def remove(book_id: str, key: str) -> dict:
    """A finished photo out of etsy/ — into the book's .replaced/, never deleted."""
    from .workshop import books
    c = category(key)
    book = books.book_path(book_id)
    _retire_all(book, book / ETSY, RESULT.format(key=c["key"]))
    books.update_state(book, lambda d: (d.get("photos") or {}).pop(c["key"], None))
    return {"removed": c["key"]}


SCENES = ("cover & open 1", "all & open 1")   # whole-scene mockups: they go into the listing as they are


def scenes_to_etsy(book: Path) -> list[str]:
    """The newest «Cover & Open 1 …» and «All & Open 1 …» of the book's mockups/ copied into its etsy/ (the owner's
    etsy/ of book 25, 30.09.2026: the slides, the photos and these two). The same file there is left as it is; one of
    another run (another spread) goes to .replaced/. Returns the names copied."""
    from .workshop.pictures import _retire
    made = [e for e in _pictures(book / MOCKUPS)]
    folder = book / ETSY
    copied = []
    for prefix in SCENES:
        found = [e for e in made if e.name.lower().startswith(prefix)]
        if not found:
            continue
        newest = Path(max(found, key=lambda e: e.stat().st_mtime).path)
        there = [Path(e.path) for e in _pictures(folder) if e.name.lower().startswith(prefix)]
        same = [p for p in there if p.name == newest.name and p.stat().st_size == newest.stat().st_size]
        for old in there:
            if old not in same:
                _retire(book, old)
        if not same:
            folder.mkdir(exist_ok=True)
            shutil.copy2(newest, folder / newest.name)
            copied.append(newest.name)
    return copied


def set_canva_cover(book: Path, source: Path, name: str) -> dict:
    """The flat cover from the Canva ZIP into the book's mockups/ as canva-cover.* (the grandmother's reference);
    the one before goes to .replaced/."""
    from .workshop.pictures import open_picture
    open_picture(source, name)
    folder = book / MOCKUPS
    folder.mkdir(exist_ok=True)
    _retire_all(book, folder, CANVA_COVER)
    shutil.copyfile(source, folder / f"{CANVA_COVER}{_suffix(name)}")
    return {"key": CANVA_COVER, "label": REFS["canva-cover"]["label"], "note": "Обкладинка з Canva на місці"}
