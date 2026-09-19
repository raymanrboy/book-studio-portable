"""Image inspection and cached previews (Pillow)."""
from __future__ import annotations

import hashlib
import io
import os
import threading
import time
import weakref
from pathlib import Path

from PIL import Image, ImageOps

from . import core

Image.MAX_IMAGE_PIXELS = 400_000_000  # print artwork is large but trusted (own files)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")

_gen_slots = threading.BoundedSemaphore(3)
_key_locks_guard = threading.Lock()
CACHE_DAYS = 21  # a preview nobody asked for in three weeks goes (it is made again when needed)
FRESH = 86400    # a preview in use gets a new date at most once a day


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


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


_LARGER = (1400, 2600, 4096)  # preview sizes the UI already asks for; a smaller one can be cut from these


def _cached(path: Path, stat, max_side: int) -> tuple[str, Path]:
    key_src = f"{path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}|{max_side}"
    key = hashlib.sha1(key_src.encode("utf-8")).hexdigest()
    return key, core.data_path("cache", "thumbs", key[:2], f"{key}.jpg")


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
                im = ImageOps.exif_transpose(im)
                im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS, reducing_gap=3.0)
                if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                    rgba = im.convert("RGBA")
                    bg = Image.new("RGB", rgba.size, (255, 255, 255))
                    bg.paste(rgba, mask=rgba.split()[-1])
                    im = bg
                elif im.mode != "RGB":
                    im = im.convert("RGB")
                buf = io.BytesIO()
                im.save(buf, "JPEG", quality=86, optimize=True, progressive=True)
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".tmp")
            tmp.write_bytes(buf.getvalue())
            tmp.replace(out)
    return out


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


def check_png(path: Path, full_decode: bool = True) -> tuple[dict | None, str | None]:
    """Validates a PNG: signature, format, optional full pixel decode.

    Returns (info, error). info has width/height/bytes.
    """
    try:
        size = path.stat().st_size
        if size == 0:
            return None, "файл порожній (0 байт)"
        with open(path, "rb") as f:
            if f.read(8) != PNG_SIGNATURE:
                return None, "це не справжній PNG (некоректна сигнатура)"
        with Image.open(path) as im:
            if im.format != "PNG":
                return None, f"формат {im.format}, а не PNG"
            info = {"width": im.width, "height": im.height, "bytes": size, "mode": im.mode,
                    "frames": getattr(im, "n_frames", 1)}
            if full_decode:
                im.load()
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
