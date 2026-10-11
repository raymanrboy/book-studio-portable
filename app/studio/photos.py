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
                                                                 All & Open 1) — the owner's etsy/ folder, 30.09.2026;
                                                                 each with its number in the listing («01 photo-main.png»
                                                                 … — ETSY_ORDER, tidy_etsy())

«Для відео» (the owner, 07.10.2026; before — the category «Книга в руках у людини», with people, taken out) is no photo
but a short video made in Gemini Omni or Google Flow: the same clipboard (a blank book on a surface, Cover 1, then the
video prompt — `OMNI_PROMPTS`: the camera glides in and rises over the thin book to show its cover head-on, a right hand coming from the right grips it by the corner, lifts it with a slight tilt and carries it out; handheld feel; the book a closed rigid board, its opening never named); the video he
downloads is caught, its first half second cut off (ffmpeg, `TRIM_SECONDS`), into `etsy/video-<category>.mp4` — the uncut download kept
in the book's `originals/`.

Every name inside Book Studio is English; the page says it in Ukrainian (the owner, 30.09.2026).
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path

from . import aside, core, desktop, portable
from .server import ApiError

ETSY = "etsy"             # a Workshop book's folder of what goes into its Etsy listing: the slides and these photos
MOCKUPS = "mockups"
CANVA_COVER = "canva-cover"
RESULT = "photo-{key}"    # etsy/photo-main.png …
VIDEO_RESULT = "video-{key}"   # etsy/video-video.mp4 — a video category's, its start cut off
TRIM_SECONDS = 0.5        # the owner: cut the start of the video — 2 s (30.09.2026), 0.5 s (07.10.2026)

# The categories, in the page's order; `ref` — which of the book's pictures goes into the clipboard second.
CATEGORIES = [
    {"key": "main", "label": "Головне фото", "ref": "cover1"},
    # «Демонстрація продукту» (2026-10-09) took the place of «Відкрита книга»: hands hold the closed hardcover, with the
    # callouts (Hardcover, Premium materials …) written on the photo. The old category's templates stay in data/photo-mockups/open-book/.
    {"key": "product", "label": "Демонстрація продукту", "ref": "cover1"},
    {"key": "grandma", "label": "Бабуся читає", "ref": "canva-cover"},
    {"key": "child", "label": "У руках дитини", "ref": "cover1"},
    {"key": "shelf", "label": "На полиці", "ref": "cover1"},
    # A video, not a photo (since 2026-10-07 the only one): 9:16 phone photos of the closed book on a sofa, a counter, a
    # table, animated in Gemini Omni / Google Flow with the owner's prompt (see OMNI_PROMPTS), caught and trimmed.
    {"key": "video", "label": "Для відео", "ref": "cover1", "omni": True},
    {"key": "size", "label": "Розмір", "ref": "cover1"},       # the two formats side by side: softcover and hardcover
]
BY_KEY = {c["key"]: c for c in CATEGORIES}
PHOTOS = [c for c in CATEGORIES if not c.get("omni")]   # the categories with a photo (and a JSON prompt)

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


def _pictures(folder: Path, exts: tuple[str, ...] = core.IMAGE_EXTS) -> list[os.DirEntry]:
    try:
        with os.scandir(folder) as it:
            return sorted((e for e in it if e.is_file() and e.name.lower().endswith(exts)),
                          key=lambda e: e.name.lower())
    except OSError:
        return []


def _result(c: dict) -> tuple[str, tuple[str, ...]]:
    """A category's file in etsy/: its stem and the extensions it may have — a photo, or a video category's video."""
    if c.get("omni"):
        return VIDEO_RESULT.format(key=c["key"]), core.VIDEO_EXTS
    return RESULT.format(key=c["key"]), core.IMAGE_EXTS


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
    """A template out of the set — into the Windows Recycle Bin, never deleted for good; a few minutes on the shelf
    first, for «Скасувати» (`aside`, 06.10.2026)."""
    path = template_file(key, name)
    token = aside.put(path, f"photo template {path.name}")
    core.log.info("Photo mockups: template %s set aside for the Recycle Bin", path.name)
    return {"removed": path.name, "undo": token}


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
    "product": _prompt(
        FRONT,
        "a square photo of a product demonstration: two hands hold the closed blank square hardcover in front of "
        "the camera, its front cover facing it, in a cosy room; white hand-drawn callouts with curved arrows are "
        "written on the photo (Hardcover, Premium materials, Your name on the cover, 30 pages)",
        ["our front cover on the front of the book, edge to edge, in the photo's perspective",
         "the visible spine, the cover edges and the pages' edge in our book's colours and paper — no white strip of "
         "the blank book left",
         "the fingers and thumbs over the book stay on top, exactly as they are",
         "the callout texts and their arrows stay exactly as they are, letter for letter, and are not covered by "
         "the cover"],
        ["changing, moving or re-spelling the callout texts and arrows", "adding callouts of your own"]),
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


# A video category's prompt: plain text for Gemini Omni / Google Flow (the owner, 07.10.2026; the form is that of his
# tested Omni prompt) — the camera pushes in on the closed book, a hand takes it away; "small" on every mention keeps
# the book from growing as the camera comes closer. The JSON in PROMPTS["video"] is the two-step fallback: a photo with
# our book first, then that photo as the first frame in Flow.
OMNI_PROMPTS = {
    "video": """Animate this exact scene. Keep the room, the surface, the light, the props and the
small book — its cover artwork, title and colours — exactly as they are; do not redraw anything.

The small book is a thin closed book with stiff covers, pressed shut like one solid
rigid board. It stays closed in every frame and only ever moves as one rigid piece.

One continuous 8-second handheld phone shot with a lively, natural handheld feel:
gentle sway, small organic shake and micro-corrections, smooth and never jerky.

[0-3s] The camera pushes in towards the small book with confident momentum and rises
over it, ending up looking straight down at it: the front cover faces the camera
head-on, centred, sharp and fully visible. The small book lies still.

[3-4s] A woman's right hand and forearm enter from the right side of the frame. The
hand grips the small book firmly by its lower right corner: the thumb on top of the
front cover right at the corner, the fingers underneath, clamping the covers together.
The cover artwork stays uncovered.

[4-6.5s] The hand lifts the small book up towards the camera, the front cover still
facing the camera, and tilts it back gently, about 10 degrees, so a soft glint of
light slides across the cover, then levels it again. The hand and wrist move
naturally, a slight relaxed sway, while the small book stays one closed rigid board
held in the same grip.

[6.5-8s] The hand carries the small book out of the frame to the right, the front cover
facing the camera until it leaves. The surface and the props stay as they are.

Only the hand and forearm are ever in the frame. The small book's size, its thinness,
the cover artwork and the title stay exactly the same in every frame.
Quiet room ambience, no music, no dialogue.""",
}


def prompt(key: str) -> str:
    from .workshop.rows import as_prompt
    key = category(key)["key"]
    return OMNI_PROMPTS[key] if key in OMNI_PROMPTS else as_prompt(PROMPTS[key])


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
    """category → the file of its finished photo (or video) in etsy/."""
    names = {Path(bare(e.name)).stem.lower(): e.name for e in _pictures(book / ETSY, core.IMAGE_EXTS + core.VIDEO_EXTS)}
    out = {}
    for c in CATEGORIES:
        stem, exts = _result(c)
        if stem in names and names[stem].lower().endswith(exts):
            out[c["key"]] = names[stem]
    return out


def count(book: Path) -> int:
    return len(results(book))


def state(book: Path) -> dict:
    """What the book's «Фото» step shows: the references, a card per category, how many are done. The template used last
    is marked only for a category that has its result — a record left from a removed photo (or from the time the category
    was a photo, 07.10.2026) is no ✓."""
    from .workshop import books
    refs = references(book)
    done = results(book)
    record = books.state(book).get("photos") or {}
    return {
        "refs": [{"key": k, "label": r["label"], "name": refs[k], "missing": r["missing"]} for k, r in REFS.items()],
        "cards": [{"key": c["key"], "label": c["label"], "ref": c["ref"], "refLabel": REFS[c["ref"]]["label"],
                   "photo": done.get(c["key"]), "template": (record.get(c["key"]) or {}).get("template") if c["key"] in done else None,
                   "omni": bool(c.get("omni"))}
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


def _retire_all(book: Path, folder: Path, stem: str, exts: tuple[str, ...] = core.IMAGE_EXTS) -> None:
    from .workshop.pictures import _retire
    for e in _pictures(folder, exts):
        if Path(bare(e.name)).stem.lower() == stem:
            _retire(book, Path(e.path))


# ---------------------------------------------------------------- the etsy/ folder in the listing's order

# The owner's order of a listing's files (30.09.2026): a number in front of the name, so Explorer shows them in the
# order they go into the listing. By the name without its number; a file that isn't here keeps its name and so comes
# after the numbered ones. A number belongs to its file — a missing one leaves a gap, nothing moves up.
ETSY_ORDER = {"photo-main": 1, "video-video": 2, "photo-grandma": 3, "photo-product": 5, "listing 1": 6,
              "photo-open-book": 7, "listing 3": 8, "listing 4": 9, "photo-child": 10, "listing 2": 11, "photo-size": 12,
              "listing 5": 13, "listing 6": 14, "photo-shelf": 15, "listing 7": 16}
# 5 — the product demonstration (the owner, 09.10.2026: "the fifth"; everything from the old 5 on moved one down);
# 16 — the hero's looks (2026-10-02), last for now
ETSY_SCENES = {"all & open 1": 4, "cover & open 1": 7}   # by the start of the name: «All & Open 1 (8-9).png»
OPEN_BOOK = "photo-open-book"   # when there is one, it takes Cover & Open 1's place: that mockup stays in mockups/ only
_NUMBERED = re.compile(r"^(\d{2}) (.+)$")


def bare(name: str) -> str:
    """A file's name without the listing's number: «05 Listing 1.png» → «Listing 1.png»."""
    m = _NUMBERED.match(name)
    return m.group(2) if m else name


def etsy_number(name: str) -> int | None:
    """Where a file goes in the listing (by its name without a number), or None — not one of the program's."""
    stem = Path(bare(name)).stem.lower()
    if stem in ETSY_ORDER:
        return ETSY_ORDER[stem]
    return next((n for prefix, n in ETSY_SCENES.items() if stem.startswith(prefix)), None)


def _has_open_book(folder: Path) -> bool:
    return any(Path(bare(e.name)).stem.lower() == OPEN_BOOK for e in _pictures(folder))


def tidy_etsy(book: Path) -> list[str]:
    """Every file of the program's in the book's etsy/ gets its number («01 photo-main.png» …); the owner's own files
    are left as they are. With an open-book photo there, Cover & Open 1's copy goes (to .replaced/ — the mockup itself
    is in mockups/). Two of one kind (a slide baked anew beside a numbered one): the newer keeps the place, the older
    goes to .replaced/. Returns the new names."""
    from .workshop.pictures import _retire
    folder = book / ETSY
    open_book = _has_open_book(folder)
    renamed = []
    for e in _pictures(folder, core.IMAGE_EXTS + core.VIDEO_EXTS):
        path, name = Path(e.path), bare(e.name)
        n = etsy_number(name)
        if n is None or not path.exists():
            continue
        if open_book and Path(name).stem.lower().startswith("cover & open 1"):
            _retire(book, path)
            continue
        want = folder / f"{n:02d} {name}"
        if path == want:
            continue
        if want.exists():
            older = min((path, want), key=lambda p: p.stat().st_mtime)
            _retire(book, older)
            if older == path:
                continue
        path.rename(want)
        renamed.append(want.name)
    if renamed:
        core.log.info("Etsy folder of %s in order: %s", book.name, ", ".join(renamed))
    return renamed


def place(book_id: str, key: str, source: Path, name: str, template: str | None = None, take: bool = False) -> dict:
    """A finished photo into the book's etsy/ folder as `photo-<category>`; the one before goes to .replaced/.
    `take` moves the file (a download) instead of copying it."""
    from .workshop import books
    from .workshop.pictures import _move, open_picture
    c = category(key)
    if c.get("omni"):
        return place_video(book_id, key, source, name, template, take)
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
    tidy_etsy(book)
    core.log.info("Photo mockups: %s → %s/%s", name, book_id, target.name)
    return {"key": f"photo:{c['key']}", "label": c["label"], "note": f"Фото «{c['label']}» на місці"}


def ffmpeg() -> str:
    """ffmpeg: the one Windows finds (installed on the owner's PC), else app/bin/ffmpeg.exe."""
    found = (str(portable.ffmpeg()) if portable.ffmpeg() else None) or shutil.which("ffmpeg") or (str(core.BIN_DIR / "ffmpeg.exe") if (core.BIN_DIR / "ffmpeg.exe").is_file() else None)
    if not found:
        raise ApiError("Не знайдено ffmpeg — без нього відео не обрізати. Встановіть ffmpeg або покладіть ffmpeg.exe "
                       "у папку bin програми.")
    return found


def _sec(seconds: float) -> str:
    return f"{seconds:g}".replace(".", ",")   # «0,5»


def trim(source: Path, target: Path, seconds: float = TRIM_SECONDS) -> None:
    """The video without its first `seconds`: cut exactly (encoded again — H.264 + AAC, the quality kept), the MP4 ready
    to play at once (faststart). Written beside the target first, so a failure leaves nothing half-made."""
    part = target.with_name(target.stem + ".part.mp4")
    command = [ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-ss", str(seconds), "-i", str(source),
               "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(part)]
    try:
        run = subprocess.run(command, capture_output=True, timeout=600,
                             creationflags=desktop.CREATE_NO_WINDOW)
    except subprocess.TimeoutExpired:
        part.unlink(missing_ok=True)
        raise ApiError("ffmpeg обрізав відео надто довго — спробуйте ще раз.")
    if run.returncode != 0 or not part.is_file() or part.stat().st_size < 1024:
        part.unlink(missing_ok=True)
        said = run.stderr.decode("utf-8", "replace").strip().splitlines()[-1:] if run.stderr else []
        raise ApiError(f"Не вдалося обрізати відео (воно коротше за {_sec(seconds)} с або пошкоджене)."
                       + (f" ffmpeg: {said[0]}" if said else ""))
    core.replace_file(part, target)


def place_video(book_id: str, key: str, source: Path, name: str, template: str | None = None,
                take: bool = False) -> dict:
    """A video category's video: its start (`TRIM_SECONDS`) cut off into etsy/video-<category>.mp4, the download as it came
    into the book's originals/ (`take` moves it out of Downloads); the ones before go to .replaced/."""
    from .workshop import books
    from .workshop.pictures import _move
    c = category(key)
    if not name.lower().endswith(core.VIDEO_EXTS):
        raise ApiError(f"«{Path(name).name}» — не відео (MP4, MOV, WEBM).")
    book = books.book_path(book_id)
    stem = VIDEO_RESULT.format(key=c["key"])
    folder = book / ETSY
    folder.mkdir(exist_ok=True)
    made = folder / f"{stem}.new.mp4"
    trim(source, made)                  # nothing is moved or replaced before the cut is made
    _retire_all(book, folder, stem, core.VIDEO_EXTS)
    core.replace_file(made, folder / f"{stem}.mp4")
    originals = book / books.ORIGINALS
    originals.mkdir(exist_ok=True)
    _retire_all(book, originals, stem, core.VIDEO_EXTS)
    uncut = originals / f"{stem}{Path(name).suffix.lower()}"
    if take:
        _move(source, uncut)
    else:
        shutil.copyfile(source, uncut)

    def change(data):
        photos = data.setdefault("photos", {})
        photos[c["key"]] = {"template": template or (photos.get(c["key"]) or {}).get("template"),
                            "from": Path(name).name[:160], "at": core.now_iso()}
    books.update_state(book, change)
    tidy_etsy(book)
    core.log.info("Photo mockups: video %s → %s/%s (first %ss cut)", name, book_id, stem, TRIM_SECONDS)
    return {"key": f"photo:{c['key']}", "label": c["label"],
            "note": f"Відео «{c['label']}» на місці — перші {_sec(TRIM_SECONDS)} с обрізано"}


def remove(book_id: str, key: str) -> dict:
    """A finished photo (or video) out of etsy/ — into the book's .replaced/, never deleted."""
    from .workshop import books
    c = category(key)
    book = books.book_path(book_id)
    stem, exts = _result(c)
    _retire_all(book, book / ETSY, stem, exts)
    books.update_state(book, lambda d: (d.get("photos") or {}).pop(c["key"], None))
    tidy_etsy(book)
    return {"removed": c["key"]}


SCENES = ("cover & open 1", "all & open 1")   # whole-scene mockups: they go into the listing as they are


def scenes_to_etsy(book: Path) -> list[str]:
    """The newest «Cover & Open 1 …» and «All & Open 1 …» of the book's mockups/ copied into its etsy/ (the owner's
    etsy/ of book 25, 30.09.2026: the slides, the photos and these two). The same file there is left as it is; one of
    another run (another spread) goes to .replaced/. Cover & Open 1 isn't copied while the book has its open-book photo
    — the photo takes its place. The folder is put in order after. Returns the names copied."""
    from .workshop.pictures import _retire
    made = [e for e in _pictures(book / MOCKUPS)]
    folder = book / ETSY
    open_book = _has_open_book(folder)
    copied = []
    for prefix in SCENES:
        found = [e for e in made if e.name.lower().startswith(prefix)]
        if not found or (open_book and prefix == "cover & open 1"):
            continue
        newest = Path(max(found, key=lambda e: e.stat().st_mtime).path)
        there = [Path(e.path) for e in _pictures(folder) if bare(e.name).lower().startswith(prefix)]
        same = [p for p in there if bare(p.name) == newest.name and p.stat().st_size == newest.stat().st_size]
        for old in there:
            if old not in same:
                _retire(book, old)
        if not same:
            folder.mkdir(exist_ok=True)
            shutil.copy2(newest, folder / newest.name)
            copied.append(newest.name)
    tidy_etsy(book)
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
