"""Image inspection and cached previews (Pillow)."""
from __future__ import annotations

import hashlib
import io
import os
import shutil
import threading
import time
import weakref
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps

from . import core

Image.MAX_IMAGE_PIXELS = 400_000_000  # print artwork is large but trusted (own files)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

_gen_slots = threading.BoundedSemaphore(3)
_key_locks_guard = threading.Lock()
CACHE_DAYS = 21  # a preview nobody asked for in three weeks goes (it is made again when needed)
FRESH = 86400    # a preview in use gets a new date at most once a day


def _version(path: Path):
    """One version of a file: its place, id, size and time — a replaced page is a new version even when the Canva
    download kept an older time (the id changes with every file put in place)."""
    st = path.stat()
    return (str(path.resolve()), st.st_ino, st.st_size, st.st_mtime_ns), st


_digests: dict[tuple, str] = {}
_digests_lock = threading.Lock()


def digest(path: Path) -> str:
    """The file's sha256, read once per version of it: a Printify send and its upload cache ask for every page, and
    so does every check of the same folder."""
    key, _ = _version(path)
    with _digests_lock:
        if key in _digests:
            return _digests[key]
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    with _digests_lock:
        if len(_digests) > 5000:
            _digests.clear()
        _digests[key] = h.hexdigest()
    return _digests[key]


def image_info(path: Path) -> dict:
    """Header-only probe (fast): format and pixel size."""
    with Image.open(path) as im:
        return {"format": im.format, "width": im.width, "height": im.height, "mode": im.mode}


class _KeyLock:
    """One preview made by one thread at a time; forgotten once nobody holds it (the table no longer grows
    by a lock for every preview ever made)."""
    __slots__ = ("lock", "__weakref__")

    def __init__(self) -> None:
        self.lock = threading.Lock()

    def __enter__(self) -> "_KeyLock":
        self.lock.acquire()
        return self

    def __exit__(self, *exc) -> None:
        self.lock.release()


_key_locks: "weakref.WeakValueDictionary[str, _KeyLock]" = weakref.WeakValueDictionary()


def _lock_for(key: str) -> _KeyLock:
    with _key_locks_guard:
        lock = _key_locks.get(key)
        if lock is None:
            lock = _key_locks[key] = _KeyLock()
        return lock


def _hit(out: Path) -> bool:
    """The cached file is there. One in use gets a fresh date now and then, so prune_cache() leaves it."""
    try:
        age = time.time() - out.stat().st_mtime
    except FileNotFoundError:
        return False
    if age > FRESH:
        try:
            os.utime(out)
        except OSError:
            pass
    return True


def prune_cache(days: int = CACHE_DAYS) -> int:
    """Removes previews not used for `days` (and half-written ones older than an hour): the cache grew for
    ever — 152 MB in five days (19.09.2026), with previews of temporary copies long gone."""
    root = core.data_path("cache", "thumbs")
    now = time.time()
    removed = 0
    for f in root.rglob("*") if root.is_dir() else []:
        try:
            if f.is_file() and now - f.stat().st_mtime > (3600 if f.suffix == ".tmp" else days * 86400):
                f.unlink()
                removed += 1
        except OSError:
            continue
    return removed


def prune_cache_quietly() -> None:
    try:
        removed = prune_cache()
        if removed:
            core.log.info("Preview cache: %d old files removed", removed)
    except Exception:
        core.log.exception("Preview cache not pruned")


# Preview sizes the UI asks for from 1400 up (a smaller one is cut from these); a test holds the pages to
# them (tests/test_orders.py SharedNumbers), so a new size is not a new file per picture.
_LARGER = (1400, 2600, 4096)


def _cached(path: Path, stat, max_side: int) -> tuple[str, Path]:
    key_src = f"{path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}|{max_side}"
    key = hashlib.sha1(key_src.encode("utf-8")).hexdigest()
    return key, core.data_path("cache", "thumbs", key[:2], f"{key}.jpg")


VIEW_SIDES = (1400, 360)  # the viewer's preview and the page strip's (a page's own check makes both)


def flat_rgb(im: Image.Image) -> Image.Image:
    """The picture in RGB, its see-through parts on white (a preview, a mockup's picture, the clipboard's bitmap)."""
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        rgba = im.convert("RGBA")
        flat = Image.new("RGB", rgba.size, (255, 255, 255))
        flat.paste(rgba, mask=rgba.split()[-1])
        return flat
    return im if im.mode == "RGB" else im.convert("RGB")


def _shrink(im: Image.Image, max_side: int) -> Image.Image:
    """A picture as a preview shows it: turned by its EXIF, no larger than max_side, see-through parts on white."""
    im = ImageOps.exif_transpose(im)
    im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS, reducing_gap=3.0)
    return flat_rgb(im)


def _store(im: Image.Image, out: Path) -> None:
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=86, optimize=True, progressive=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_bytes(buf.getvalue())
    tmp.replace(out)


def preview(path: Path, max_side: int) -> Path:
    """Returns a cached JPEG preview no larger than max_side (never upscales).

    A small preview is made from an already cached larger one when there is one — a few milliseconds
    instead of decoding the whole 4000-pixel PNG again (the page strips need dozens of them at once)."""
    stat = path.stat()
    key, out = _cached(path, stat, max_side)
    if _hit(out):
        return out
    with _lock_for(key):
        if out.exists():
            return out
        source = next((big for size in _LARGER if size > max_side
                       for big in [_cached(path, stat, size)[1]] if big.exists()), path)
        with _gen_slots:
            with Image.open(source) as im:
                im.draft("RGB", (max_side, max_side))
                _store(_shrink(im, max_side), out)
    return out


def _previews_from(im: Image.Image, path: Path, stat, sizes: tuple[int, ...]) -> None:
    """Previews made from pixels already decoded (the largest first, each smaller one from it), where none is
    cached yet."""
    source = im
    for size in sorted(sizes, reverse=True):
        key, out = _cached(path, stat, size)
        with _lock_for(key):            # the order is always: the preview's lock, then a slot (as in preview()) — never the reverse
            if not out.exists():
                with _gen_slots:
                    source = _shrink(source.copy() if source is im else source, size)
                    _store(source, out)


def copy_previews(src: Path, dst: Path, sizes: tuple[int, ...] = VIEW_SIDES) -> None:
    """A file copied elsewhere (the order archive) takes the previews already made of it: the same pixels, so they
    are the same pictures — no page is decoded again."""
    s_stat, d_stat = src.stat(), dst.stat()
    for size in sizes:
        have, want = _cached(src, s_stat, size)[1], _cached(dst, d_stat, size)[1]
        if have.exists() and not want.exists():
            want.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(have, want)


TEXT_SIDE = 360   # the page preview the order card's strip already asks for — so this costs nothing extra


def text_score(path: Path) -> float:
    """How much a page looks like it carries lines of text, rather than only a picture.

    Printed text is thin strokes gathered into a few narrow rows, with empty space between them; an
    illustration spreads its detail evenly down the page. So: take what a slight blur cannot explain
    (the strokes and edges), keep the sharpest 1 %, and measure how unevenly that ink sits across the
    rows of the page. Measured on the owner's five real books (20.09.2026): a page with text scores
    2.4–2.6, a picture page 0.9–1.5 — see wiki/features/text-check.md.
    """
    with Image.open(preview(path, TEXT_SIDE)) as src:
        im = src.convert("L").resize((TEXT_SIDE, TEXT_SIDE), Image.Resampling.BILINEAR)
    ink = ImageChops.difference(im, im.filter(ImageFilter.GaussianBlur(1.6)))
    mask = ink.point(lambda v, cut=max(_percentile(ink.histogram(), 0.99), 8): 255 if v > cut else 0)
    rows = mask.resize((1, TEXT_SIDE), Image.Resampling.BOX).tobytes()  # ink per row of the page (0…255)
    mean = sum(rows) / len(rows)
    if mean <= 0:
        return 0.0
    spread = (sum((r - mean) ** 2 for r in rows) / len(rows)) ** 0.5
    return spread / mean


def _percentile(histogram: list[int], share: float) -> int:
    """The grey value below which `share` of the pixels sit."""
    total = sum(histogram)
    seen = 0
    for value, count in enumerate(histogram):
        seen += count
        if seen >= total * share:
            return value
    return 255


def lqip(path: Path, size: int = 20) -> str:
    """A ~500-byte blurred stand-in (data URI) shown until the real picture is decoded."""
    import base64
    with Image.open(path) as im:
        im.draft("RGB", (size * 8, size * 8))
        im.thumbnail((size, size), Image.Resampling.BILINEAR, reducing_gap=2.0)
        im = im.convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=62)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def display_size(width: int, height: int) -> int:
    """Preview size the UI asks for: spreads and covers are wide, pages are square."""
    return 1400 if width >= 1.5 * max(height, 1) else 720


_checked: dict[tuple, tuple] = {}
_checked_lock = threading.Lock()


def check_png(path: Path, previews: tuple[int, ...] = ()) -> tuple[dict | None, str | None]:
    """Validates a PNG: signature, format, every pixel decoded. Returns (info, error); info has width/height/bytes.

    Remembered per version of the file (`_version()`): a check of a folder after one page was replaced reads only
    that page (4–5 s → ~0.5 s for a 30-page book). `previews` — sizes made from the pixels just decoded, so the
    viewer and the page strip are ready when the check ends, without a second decode of every 4000-pixel page."""
    try:
        key, st = _version(path)
    except OSError as err:
        return None, f"не вдалося прочитати файл ({err})"
    with _checked_lock:
        known = _checked.get(key)
    if known and all(_cached(path, st, s)[1].exists() for s in previews if known[0]):
        return known
    result = _check(path, st, previews)
    with _checked_lock:
        if len(_checked) > 5000:
            _checked.clear()
        _checked[key] = result
    return result


def _check(path: Path, st, previews: tuple[int, ...]) -> tuple[dict | None, str | None]:
    try:
        if st.st_size == 0:
            return None, "файл порожній (0 байт)"
        with open(path, "rb") as f:
            if f.read(8) != PNG_SIGNATURE:
                return None, "це не справжній PNG (некоректна сигнатура)"
        with Image.open(path) as im:
            if im.format != "PNG":
                return None, f"формат {im.format}, а не PNG"
            info = {"width": im.width, "height": im.height, "bytes": st.st_size, "mode": im.mode,
                    "frames": getattr(im, "n_frames", 1)}
            im.load()
            if previews:
                _previews_from(im, path, st, previews)
        return info, None
    except Exception as err:  # Pillow raises many different types for damaged files
        return None, f"не вдалося прочитати файл ({err})"


def compose_spread(left: Path | None, right: Path | None, height: int) -> Path:
    """Two pages side by side (blank side = paper colour) for spread previews."""
    parts = []
    for p in (left, right):
        if p is not None:
            st = p.stat()
            parts.append(f"{p.resolve()}|{st.st_mtime_ns}|{st.st_size}")
        else:
            parts.append("-")
    key = hashlib.sha1(("spread|" + "|".join(parts) + f"|{height}").encode("utf-8")).hexdigest()
    out = core.data_path("cache", "thumbs", key[:2], f"{key}.jpg")
    if _hit(out):
        return out
    with _lock_for(key):
        if out.exists():
            return out
        sides: list[Image.Image | None] = []
        for p in (left, right):
            if p is None:
                sides.append(None)
                continue
            # one of the sizes kept anyway (1400 / 2600): the viewer's zoom (2400) decoded the 4000-px pages again
            src = preview(p, next((s for s in _LARGER if s >= height), _LARGER[-1]))
            with Image.open(src) as im:
                im = im.convert("RGB")
                w = max(1, round(im.width * height / im.height))
                sides.append(im.resize((w, height), Image.Resampling.LANCZOS))
        widths = [s.width if s else None for s in sides]
        default_w = next((w for w in widths if w), height)
        widths = [w or default_w for w in widths]
        canvas = Image.new("RGB", (sum(widths), height), (243, 239, 230))
        x = 0
        for s, w in zip(sides, widths):
            if s is not None:
                canvas.paste(s, (x, 0))
            x += w
        buf = io.BytesIO()
        canvas.save(buf, "JPEG", quality=86, optimize=True, progressive=True)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".tmp")
        tmp.write_bytes(buf.getvalue())
        tmp.replace(out)
    return out
