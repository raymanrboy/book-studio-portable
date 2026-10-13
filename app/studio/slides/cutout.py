"""The book cut out of a mockup picture, with its real shadow, on a transparent background.

Why this works (found on 29.09.2026): in the owner's templates the shadows are grey layers in Multiply over the grey
studio background (plus Screen lights), so hiding the background in Photoshop "cuts some shadow". A Multiply layer of
grey v is exactly black with alpha 1 − v; a Screen layer is white with alpha v — so they become a real transparent
shadow. The book's outline is the mask of the template's BOOK/OBJECT group. The templates are only read (psd_tools,
imported only when a cut is made — nothing of it loads at launch).

The templates that are one book on the studio background are cut to the book: 2. Open 1, 3. Open 2 and 1. Cover 1.
4. Dedication is a book on a floor by a desk: its floor (the smart object BACKGROUND, with its own mask) goes and the
desk («BACKGROUND_desk color» — the colour the owner picks for the table) stays with the book, the shadows kept (the
owner, 29.09.2026: "the table stays, the background goes, without losing the shadows"). Cover & Open 1 and All & Open 1
are whole scenes (no book mask): they are kept whole.

    kind_of(name)       which template a mockup picture comes from (by its file name)
    cut(png, template)  the book and its shadow as two pictures, and where the book sits in them
    combined(...)       the two as one picture — the «Без фону» file
    Cutter              the background worker: pictures cut while Photoshop still works on the next ones
"""
from __future__ import annotations

import hashlib
import json
import queue
import re
import shutil
import threading
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageFilter

from .. import core

HAZE = 0.035        # the template's shadow darkens the whole canvas by a few %: that floor is cut
MAX_WIDTH = 2600    # plenty for a 2000² slide
NO_BG = "no-background"  # the folder beside the mockups where the cut-outs go — «Без фону» until 30.09.2026 (the
                         # owner: every name inside Book Studio in English)
CUTS = core.data_path("slides", "cuts")   # every cut once: <key>/book.png, shadow.png, info.json

# (kind, the template's file) — by the mockup's file name, the way the Mockups name them ("2. Open 1 (6-7).png")
KINDS = {"open1": "2. Open 1.psd", "open2": "3. Open 2.psd", "cover1": "1. Cover 1.psd", "dedication": "4. Dedication.psd"}


def kind_of(name: str) -> str | None:
    """open1 / open2 / cover1 / dedication — or None for a picture the slides don't use (Cover & Open 1, …)."""
    low = Path(name).stem.lower()
    if "&" in low:
        return None
    if "dedication" in low:
        return "dedication"
    for kind, pattern in (("open1", r"\bopen\s*1\b"), ("open2", r"\bopen\s*2\b"), ("cover1", r"\bcover\s*1\b")):
        if re.search(pattern, low):
            return kind
    return None


def spread_of(name: str) -> int:
    """The spread's first page in a mockup's name ("2. Open 1 (6-7).png" → 6); 0 when there is none."""
    m = re.search(r"\((\d+)\s*-\s*\d+\)", name)
    return int(m.group(1)) if m else 0


# ---------------------------------------------------------------- the template: the book's outline and its shadows

def _walk(group):
    for layer in group:
        yield layer
        if layer.is_group():
            yield from _walk(layer)


def read_psd(path: Path, size: tuple[int, int], desk: bool = False):
    """The book's outline (alpha, 0…1) and the shadow/light layers as (colour 0|1, alpha) — from the PSD, read only.
    `desk` (Dedication): what stays is the book and the desk — everything but the floor, the BACKGROUND smart object
    where its mask shows it."""
    import numpy as np
    from psd_tools import PSDImage
    warnings.filterwarnings("ignore")
    psd = PSDImage.open(path)
    W, H = psd.size
    layers = list(_walk(psd))
    book = next(l for l in layers if l.name == "BOOK" and l.is_group())
    background = next(l for l in layers if l.name == "BACKGROUND" and l.is_group())
    obj = next(l for l in book if l.name == "OBJECT")
    alpha = np.zeros((H, W), np.float32)
    x0, y0, x1, y1 = obj.mask.bbox
    alpha[y0:y1, x0:x1] = np.asarray(obj.mask.topil(), np.float32) / 255

    def full(layer):
        im = np.zeros((H, W, 4), np.float32)
        a = np.asarray(layer.topil().convert("RGBA"), np.float32) / 255
        x0, y0, x1, y1 = layer.bbox
        im[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] = \
            a[max(0, -y0):max(0, -y0) + min(H, y1) - max(0, y0), max(0, -x0):max(0, -x0) + min(W, x1) - max(0, x0)]
        return im

    effects = []
    for group in (background, next(l for l in book if l.name == "UNDER L/S")):
        for layer in group:
            if not layer.visible or layer.kind != "pixel" or layer.name == "LIGHT_global":
                continue
            a, opacity, mode = full(layer), layer.opacity / 255, str(layer.blend_mode)
            lum = a[..., :3].mean(-1)
            if "MULTIPLY" in mode:
                effects.append((0.0, (1 - lum) * a[..., 3] * opacity))
            elif "SCREEN" in mode:
                effects.append((1.0, lum * a[..., 3] * opacity))
    near = _near_book(alpha, effects)
    if desk:
        floor = next(l for l in background if l.name == "BACKGROUND" and not l.is_group())
        shown = full(floor)[..., 3]
        mask = np.zeros((H, W), np.float32)
        x0, y0, x1, y1 = floor.mask.bbox
        mask[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] =             (np.asarray(floor.mask.topil(), np.float32) / 255)[max(0, -y0):max(0, -y0) + min(H, y1) - max(0, y0), max(0, -x0):max(0, -x0) + min(W, x1) - max(0, x0)]
        alpha = np.maximum(1 - shown * mask, alpha)
    return alpha, near


def read_psd_desk(path: Path, size: tuple[int, int]):
    return read_psd(path, size, desk=True)


def _near_book(alpha, effects):
    """Keeps the shadows near the book only: a soft falloff from its outline (the template's shadow layers cover the
    whole canvas faintly)."""
    import numpy as np
    H, W = alpha.shape
    small = Image.fromarray((alpha * 255).astype(np.uint8)).resize((max(1, W // 8), max(1, H // 8)))
    near = np.asarray(small.filter(ImageFilter.GaussianBlur(40)).resize((W, H), Image.BILINEAR), np.float32) / 255
    near = np.clip(near * 4, 0, 1)
    return [(c, a * near) for c, a in effects]


# The template reader: the PSD in the owner's templates folder. The preview server and the tests put a pretend one
# here (made-up templates are plain pictures).
READER = read_psd
DESK_READER = read_psd_desk     # Dedication: the book and the desk

_templates: dict[str, tuple] = {}   # the last template read (a few hundred MB of arrays — one kept at a time)
_templates_lock = threading.Lock()


def template(path: Path, size: tuple[int, int], kind: str = ""):
    try:
        stamp = path.stat().st_mtime_ns
    except OSError:
        stamp = 0
    key = f"{path}|{stamp}|{size}|{kind}"
    with _templates_lock:
        if key not in _templates:
            _templates.clear()
            _templates[key] = (DESK_READER if kind == "dedication" else READER)(path, size)
        return _templates[key]


def forget_templates() -> None:
    with _templates_lock:
        _templates.clear()


# ---------------------------------------------------------------- the cut

def cut(png: Path, tmpl, crop: bool = True) -> tuple[Image.Image, Image.Image, dict]:
    """The book alone and its shadow alone (so a slide can make the shadow lighter), both cropped to the pair, and
    where the book sits in them: cx, cy, w — shares of the picture; aspect — the book's height / width. Full size."""
    import numpy as np
    alpha, effects = tmpl
    with Image.open(png) as im:
        src = np.asarray(im.convert("RGB"), np.float32) / 255
    H, W = alpha.shape
    if src.shape[:2] != (H, W):
        raise _fail(f"«{png.name}»: розмір {src.shape[1]}×{src.shape[0]}, а шаблон {W}×{H}.")
    color = np.zeros((H, W, 3), np.float32)   # premultiplied
    a = np.zeros((H, W), np.float32)
    for c, fa in effects:
        color = c * fa[..., None] + color * (1 - fa[..., None])
        a = fa + a * (1 - fa)
    shadow_a = np.clip((a - HAZE) / (1 - HAZE), 0, 1)
    color *= (shadow_a / np.maximum(a, 1e-6))[..., None]
    shadow_rgb = np.where(shadow_a[..., None] > 1e-4, color / np.maximum(shadow_a[..., None], 1e-4), 0)

    def to_image(rgb, al):
        return Image.fromarray((np.dstack([rgb, al]) * 255 + .5).clip(0, 255).astype(np.uint8), "RGBA")

    book_im, shadow_im = to_image(src, alpha), to_image(shadow_rgb, shadow_a)
    both = alpha + shadow_a * (1 - alpha)
    ys, xs = np.where(both > 0.01)
    by, bx = np.where(alpha > 0.5)
    if not len(bx):
        raise _fail(f"«{png.name}»: у шаблоні не знайшлося обрису книги.")
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    pw, ph = box[2] - box[0], box[3] - box[1]
    bw, bh = max(1, int(bx.max()) - int(bx.min())), int(by.max()) - int(by.min())
    info = {"cx": ((bx.min() + bx.max()) / 2 - box[0]) / pw, "cy": ((by.min() + by.max()) / 2 - box[1]) / ph,
            "w": bw / pw, "aspect": bh / bw}
    if not crop:   # Dedication keeps the mockup's own frame: it lies on the slide where the whole mockup lay
        return book_im, shadow_im, {k: round(float(v), 5) for k, v in info.items()}
    return book_im.crop(box), shadow_im.crop(box), {k: round(float(v), 5) for k, v in info.items()}


def smaller(im: Image.Image) -> Image.Image:
    """The slides' copy: 2600 px wide is plenty for a 2000² slide (the «Без фону» file keeps the full size)."""
    return im.resize((MAX_WIDTH, round(im.height * MAX_WIDTH / im.width)), Image.LANCZOS) if im.width > MAX_WIDTH else im


def _fail(text: str) -> Exception:
    from ..jobs import UserError
    return UserError(text)


def combined(book: Image.Image, shadow: Image.Image) -> Image.Image:
    """The book over its shadow — one transparent picture, fit for anything (the «Без фону» file)."""
    out = shadow.copy()
    out.alpha_composite(book)
    return out


def cut_key(png: Path) -> str:
    st = png.stat()
    return hashlib.sha1(f"{png.resolve()}|{st.st_size}|{st.st_mtime_ns}".encode("utf-8")).hexdigest()[:16]


def cached(png: Path) -> Path | None:
    """The folder of this picture's cut, if it was cut already (the same file, size and time)."""
    try:
        folder = CUTS / cut_key(png)
    except OSError:
        return None
    return folder if (folder / "info.json").is_file() else None


def ensure(png: Path, templates_dir: Path, no_bg: bool = True, replace: bool = False) -> Path:
    """Cuts a mockup picture once: its folder in the cache (book.png, shadow.png, info.json); with `no_bg` the combined
    picture lands in «Без фону» beside it too (never over a file that is there — unless `replace`: the mockup itself
    was just drawn again, the owner's crop, and its cut-out goes with it)."""
    kind = kind_of(png.name)
    if kind not in KINDS:
        raise _fail(f"«{png.name}» — не Open 1, Open 2, Cover 1 чи Dedication: без фону не вирізається.")
    key = cut_key(png)          # taken before the picture is read: one drawn over it meanwhile is not cached as it
    folder = cached(png)
    target = png.parent / NO_BG / png.name
    if folder is not None and replace and no_bg:   # cut already (by someone else): its «Без фону» follows anyway
        _write_no_bg_from(folder, target)
    if folder is None:
        with Image.open(png) as im:
            size = im.size
        book, shadow, info = cut(png, template(Path(templates_dir) / KINDS[kind], size, kind), crop=kind != "dedication")
        if cut_key(png) != key:
            return ensure(png, templates_dir, no_bg, replace)
        folder = CUTS / key
        tmp = folder.with_name(folder.name + ".part")
        tmp.mkdir(parents=True, exist_ok=True)
        # The three pictures are written at once (each a second or more; 04.10.2026).
        with ThreadPoolExecutor(3) as pool:
            writes = [pool.submit(lambda: smaller(book).save(tmp / "book.png", compress_level=3)),
                      pool.submit(lambda: smaller(shadow).save(tmp / "shadow.png", compress_level=3))]
            if no_bg and (replace or not target.exists()):
                writes.append(pool.submit(_write_no_bg, target, book, shadow))       # the full size, for the owner
            for w in writes:
                w.result()
        (tmp / "info.json").write_text(json.dumps({**info, "kind": kind, "source": png.name}, ensure_ascii=False),
                                       encoding="utf-8")
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
        tmp.replace(folder)
    if no_bg and not target.exists():   # cut before without it: made from the kept copy
        _write_no_bg_from(folder, target)
    return folder


def _write_no_bg_from(folder: Path, target: Path) -> None:
    with Image.open(folder / "book.png") as b, Image.open(folder / "shadow.png") as s:
        _write_no_bg(target, b.convert("RGBA"), s.convert("RGBA"))


def _write_no_bg(target: Path, book: Image.Image, shadow: Image.Image) -> None:
    target.parent.mkdir(exist_ok=True)
    part = target.with_name(target.stem + ".part.png")
    combined(book, shadow).save(part, compress_level=4)   # the same pixels as at 6, twice as fast, ~3% bigger
    part.replace(target)


# ---------------------------------------------------------------- the background worker

class Cutter:
    """Cuts the mockups one by one in the background — the Mockups hand it every picture Photoshop saves, so most are
    ready before the owner has finished his part. Keeps each picture's state by its folder: wait / work / done / an
    error's text."""

    def __init__(self) -> None:
        self._q: queue.Queue = queue.Queue()
        self._state: dict[str, dict[str, str]] = {}
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    def add(self, png: Path, templates_dir: Path, again: bool = False) -> bool:
        """`again` — the picture was drawn anew over itself: cut once more, its «Без фону» file replaced."""
        png = Path(png)
        if kind_of(png.name) not in KINDS:
            return False
        with self._lock:
            files = self._state.setdefault(str(png.parent), {})
            if files.get(png.name) in ("wait", "work", "done") and not again:
                return True
            files[png.name] = "wait"
            self._q.put((png, Path(templates_dir), again))  # in the lock: a thread that is just timing out cannot miss it
            if not self._thread or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._run, name="slides-cutter", daemon=True)
                self._thread.start()
        return True

    def _set(self, png: Path, value: str) -> None:
        with self._lock:
            self._state.setdefault(str(png.parent), {})[png.name] = value

    def _run(self) -> None:
        while True:
            try:
                png, templates_dir, again = self._q.get(timeout=30)
            except queue.Empty:
                forget_templates()      # nothing more to cut: the template's arrays go
                with self._lock:
                    if self._q.empty():
                        self._thread = None
                        return
                continue
            self._set(png, "work")
            try:
                ensure(png, templates_dir, replace=again)
                self._finished(png, "done")
            except Exception as err:  # one picture failing never stops the rest
                core.log.warning("Slides: cutting %s failed: %s", png, err)
                self._finished(png, f"error:{err}")

    def _finished(self, png: Path, value: str) -> None:
        """A pass's end — unless the picture was queued again meanwhile (drawn over itself): it stays waiting."""
        with self._lock:
            files = self._state.setdefault(str(png.parent), {})
            if files.get(png.name) == "work":
                files[png.name] = value

    def status(self, folder: Path) -> dict[str, str]:
        with self._lock:
            return dict(self._state.get(str(Path(folder)), {}))

    def busy(self, folder: Path | None = None) -> bool:
        with self._lock:
            states = [v for k, files in self._state.items() if folder is None or k == str(Path(folder))
                      for v in files.values()]
        return any(v in ("wait", "work") for v in states)


cutter = Cutter()
