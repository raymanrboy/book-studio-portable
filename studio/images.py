"""Image inspection and cached previews (Pillow)."""
from __future__ import annotations

import hashlib
import io
import threading
from pathlib import Path

from PIL import Image, ImageOps

from . import core

Image.MAX_IMAGE_PIXELS = 400_000_000  # print artwork is large but trusted (own files)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")

_gen_slots = threading.BoundedSemaphore(3)
_key_locks: dict[str, threading.Lock] = {}
_key_locks_guard = threading.Lock()


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


def _lock_for(key: str) -> threading.Lock:
    with _key_locks_guard:
        lock = _key_locks.get(key)
        if lock is None:
            lock = _key_locks[key] = threading.Lock()
        return lock


def preview(path: Path, max_side: int) -> Path:
    """Returns a cached JPEG preview no larger than max_side (never upscales)."""
    stat = path.stat()
    key_src = f"{path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}|{max_side}"
    key = hashlib.sha1(key_src.encode("utf-8")).hexdigest()
    out = core.data_path("cache", "thumbs", key[:2], f"{key}.jpg")
    if out.exists():
        return out
    with _lock_for(key):
        if out.exists():
            return out
        with _gen_slots:
            with Image.open(path) as im:
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
    if out.exists():
        return out
    with _lock_for(key):
        if out.exists():
            return out
        sides: list[Image.Image | None] = []
        for p in (left, right):
            if p is None:
                sides.append(None)
                continue
            src = preview(p, max(height, 1400))
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
