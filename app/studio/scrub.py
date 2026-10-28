"""Every picture and video put into a Workshop book's etsy/ without its metadata (the owner, 27.10.2026: Etsy now reads the photos'
metadata, and nothing in them should give it a reason to look at the shop).

What the generators and Photoshop leave in a picture — C2PA (the content credentials, `caBX` in a PNG, APP11 in a JPEG),
XMP, EXIF (the camera, the program, the date, the place), IPTC, comments, thumbnails, ICC profiles, the DPI, text
chunks, whatever trails after the picture's end — goes; the pixels stay as they are:

    PNG   only IHDR, PLTE, tRNS, IDAT, IEND (and an animated PNG's acTL, fcTL, fdAT) are kept — not re-encoded
    JPEG  every APPn and COM goes, a plain JFIF header in its place — not re-encoded (no quality lost)
    WEBP  only the picture's chunks; VP8X's flags for ICC, EXIF and XMP cleared
    MP4/MOV  copied by ffmpeg without the tags, the chapters, the encoder's name, the dates (C2PA's uuid box goes too) —
          not re-encoded; the program's own video (photos.trim()) is made so at once

Encoded again only where dropping the metadata alone would change how the picture looks: a colour profile other than
sRGB (converted to sRGB first), an EXIF rotation (turned first), a CMYK or an Adobe-RGB-encoded JPEG.

Only the files put into etsy/ from now on (`NEW_FROM`): the ones already there stay as they are (the owner,
27.10.2026). A file counts as new by its creation or modification time — a re-baked slide over an old one is new.

Called after every write of the program's into etsy/ (photos.tidy_etsy()) and, for the files the owner drops in
by hand, in the background when the book's page looks at the folder (`soon()`). A file written in the last few seconds
or one that can't be read as a whole picture (still being copied) is left for the next look.
"""
from __future__ import annotations

import io
import os
import struct
import subprocess
import threading
import time
from pathlib import Path

from PIL import Image, ImageCms, ImageOps

from . import core

PICTURE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
VIDEO_EXTS = (".mp4", ".mov")
NEW_FROM = 1793082600.0  # 2026-10-27 07:30 Warsaw time: what came into etsy/ before stays untouched (the owner)
SETTLE = 3.0             # seconds: a file younger than this may still be being copied in — the background look waits
LOCK = threading.RLock()  # one writer in a book's etsy/ at a time: the cleaning, tidy_etsy()'s renames

_clean: dict[str, tuple[int, int]] = {}   # path → (size, mtime) of a file found clean: not read again
_later: dict[str, float] = {}             # path → when to try a locked file again
RETRY = 60.0
_busy = threading.Lock()


class _Broken(Exception):
    """Not a whole picture (cut short, still being copied, not what its name says) — left alone."""


# ---------------------------------------------------------------- the folder

def folder(path: Path, settle: float = 0.0) -> list[str]:
    """Every new picture and video in `path` cleaned; returns the names changed. Never raises: a file that can't be
    cleaned now is logged and tried at the next look."""
    changed = []
    with LOCK:
        try:
            with os.scandir(path) as it:
                entries = [e for e in it if e.is_file() and e.name.lower().endswith(PICTURE_EXTS + VIDEO_EXTS)]
        except OSError:
            return []
        now = time.time()
        for e in entries:
            try:
                st = e.stat()
                if _clean.get(e.path) == (st.st_size, st.st_mtime_ns) or now < _later.get(e.path, 0):
                    continue
                if settle and 0 <= now - st.st_mtime < settle:   # a time in the future (a camera's clock) doesn't wait
                    continue
                full = os.stat(e.path)
                if max(getattr(full, "st_birthtime", full.st_ctime), full.st_mtime) < NEW_FROM:   # already there
                    _clean[e.path] = (st.st_size, st.st_mtime_ns)
                    continue
                if file(Path(e.path)):
                    changed.append(e.name)
                st = os.stat(e.path)
                _clean[e.path] = (st.st_size, st.st_mtime_ns)
            except _Broken:     # not looked at again until it changes (a copy still coming in will)
                _clean[e.path] = (st.st_size, st.st_mtime_ns)
                if not settle or now - st.st_mtime >= SETTLE:
                    core.log.warning("Metadata: %s isn't a whole picture or video — not cleaned", e.path)
            except FileNotFoundError:
                continue
            except OSError as err:   # locked (a viewer, Book Studio's own Edge): tried again in a minute
                _later[e.path] = now + RETRY
                core.log.warning("Metadata: %s not cleaned now: %s", e.path, err)
            except Exception:   # a picture Pillow can't redraw, ffmpeg failed: logged once, not tried again until it changes
                core.log.exception("Metadata: %s not cleaned", e.path)
                _clean[e.path] = (st.st_size, st.st_mtime_ns)
    if changed:
        core.log.info("Metadata: cleaned in %s: %s", path, ", ".join(changed))
    return changed


def soon(path: Path) -> None:
    """`folder()` in the background — for the page's look every 1.5 s, which mustn't wait; one at a time."""
    if not _busy.acquire(blocking=False):
        return

    def run():
        try:
            folder(path, settle=SETTLE)
        finally:
            _busy.release()
    threading.Thread(target=run, name="scrub", daemon=True).start()


def file(path: Path) -> bool:
    """One picture or video cleaned in place (through a temporary file beside it). True if it changed. A file that
    changed while it was read (a slide baked anew, a photo put over it) is left for the next look — never put back as
    it was."""
    if path.suffix.lower() in VIDEO_EXTS:
        return _video(path)
    before = os.stat(path)
    data = path.read_bytes()
    out = picture(data)
    if out is None:
        return False
    _same(data, out)
    part = path.with_name(path.name + ".part")
    try:
        part.write_bytes(out)
        os.utime(part, ns=(before.st_atime_ns, before.st_mtime_ns))   # tidy_etsy()'s "the newer keeps the place"
        now = os.stat(path)
        if (now.st_size, now.st_mtime_ns) != (before.st_size, before.st_mtime_ns):
            raise OSError(f"{path.name} changed while it was cleaned")
        core.replace_file(part, path)
    finally:
        part.unlink(missing_ok=True)
    return True


def _same(data: bytes, out: bytes) -> None:
    """The cleaned picture opens whole and is the same size as the original — else the original stays (_Broken)."""
    try:
        with Image.open(io.BytesIO(data)) as a, Image.open(io.BytesIO(out)) as b:
            size = ImageOps.exif_transpose(a).size if a.getexif().get(0x0112, 1) in (5, 6, 7, 8) else a.size
            b.load()
            ok = b.size == size
    except Exception:
        ok = False
    if not ok:
        raise _Broken


def picture(data: bytes) -> bytes | None:
    """The picture without its metadata, or None if it has none. Raises _Broken for what isn't a whole picture."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        clean, look = _png(data)
    elif data[:2] == b"\xff\xd8":
        clean, look = _jpeg(data)
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        clean, look = _webp(data)
    else:
        raise _Broken
    if look:
        clean = _redraw(data)
    return None if clean == data else clean


# ---------------------------------------------------------------- PNG

PNG_KEEP = {b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND", b"acTL", b"fcTL", b"fdAT"}


def _png(d: bytes) -> tuple[bytes, bool]:
    out, i, look, animated = [d[:8]], 8, False, False
    while True:
        if i + 12 > len(d):
            raise _Broken
        n, kind = struct.unpack(">I4s", d[i:i + 8])
        end = i + 12 + n
        if end > len(d):
            raise _Broken
        if kind in PNG_KEEP:
            out.append(d[i:end])
            animated |= kind == b"acTL"
        elif kind == b"iCCP":
            look |= not _srgb_icc(_png_icc(d[i + 8:i + 8 + n]))
        elif kind == b"eXIf":
            look |= _rotated(d)
        i = end
        if kind == b"IEND":
            return b"".join(out), look and not animated   # an animated one is never redrawn: only its first frame would stay


def _png_icc(body: bytes) -> bytes | None:
    import zlib
    try:
        return zlib.decompress(body[body.index(b"\0") + 2:])
    except (ValueError, zlib.error):
        return None


# ---------------------------------------------------------------- JPEG

# A plain JFIF 1.01 header: no density, no thumbnail — what a JPEG has in place of the APPn segments.
JFIF = b"\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"


def _jpeg(d: bytes) -> tuple[bytes, bool]:
    out, i = [d[:2], JFIF], 2
    icc, adobe, components, look = [], None, 3, False
    while True:
        if i + 2 > len(d) or d[i] != 0xFF:
            raise _Broken
        m = d[i + 1]
        if m == 0xFF:                       # a fill byte before a marker
            i += 1
            continue
        if m == 0xD9:                       # the end: whatever trails after it goes
            out.append(b"\xff\xd9")
            break
        if m == 0x01 or 0xD0 <= m <= 0xD7:  # markers without a length
            out.append(d[i:i + 2])
            i += 2
            continue
        if i + 4 > len(d):
            raise _Broken
        end = i + 2 + struct.unpack(">H", d[i + 2:i + 4])[0]
        if end > len(d):
            raise _Broken
        seg = d[i:end]
        if 0xE0 <= m <= 0xEF or m == 0xFE:  # APP0–APP15 (JFIF, EXIF, XMP, ICC, IPTC, Adobe, C2PA …), comments
            if m == 0xE2 and seg[4:16] == b"ICC_PROFILE\0":
                icc.append((seg[16], seg[18:]))
            elif m == 0xEE and seg[4:9] == b"Adobe" and len(seg) >= 16:
                adobe = seg[15]
            elif m == 0xE1 and seg[4:10] == b"Exif\0\0":
                look |= _rotated(d)
            i = end
            continue
        if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC) and len(seg) >= 10:
            components = seg[9]
        out.append(seg)
        i = end
        if m == 0xDA:                       # the scan's data, up to the next marker
            j = i
            while True:
                k = d.find(b"\xff", j)
                if k < 0 or k + 1 >= len(d):
                    raise _Broken
                n = d[k + 1]
                if n == 0x00 or 0xD0 <= n <= 0xD7:
                    j = k + 2
                elif n == 0xFF:
                    j = k + 1
                else:
                    break
            out.append(d[i:k])
            i = k
    if icc:
        look |= not _srgb_icc(b"".join(part for _, part in sorted(icc)))
    # Without the Adobe segment a decoder reads 3 channels as YCbCr: an RGB-encoded one (transform 0) and CMYK change.
    look |= components == 4 or (components == 3 and adobe == 0)
    return b"".join(out), look


# ---------------------------------------------------------------- WEBP

WEBP_KEEP = {b"VP8 ", b"VP8L", b"VP8X", b"ALPH", b"ANIM", b"ANMF"}


def _webp(d: bytes) -> tuple[bytes, bool]:
    size = struct.unpack("<I", d[4:8])[0] + 8
    if size > len(d):
        raise _Broken
    out, i, look = [], 12, False
    while i < size:
        if i + 8 > size:
            raise _Broken
        kind, n = d[i:i + 4], struct.unpack("<I", d[i + 4:i + 8])[0]
        end = i + 8 + n + (n & 1)
        if end > size:
            raise _Broken
        if kind == b"VP8X":
            out.append(d[i:i + 8] + bytes([d[i + 8] & ~0x2C]) + d[i + 9:end])   # no ICC (0x20), EXIF (0x08), XMP (0x04)
        elif kind in WEBP_KEEP:
            out.append(d[i:end])
        elif kind == b"ICCP":
            look |= not _srgb_icc(d[i + 8:i + 8 + n])
        elif kind == b"EXIF":
            look |= _rotated(d)
        i = end
    body = b"WEBP" + b"".join(out)
    return b"RIFF" + struct.pack("<I", len(body)) + body, look and not any(c[:4] == b"ANIM" for c in out)


# ---------------------------------------------------------------- what changes the look

def _srgb_icc(icc: bytes | None) -> bool:
    """An ICC profile that says sRGB (or one that can't be read — then there's nothing to convert by)."""
    if not icc:
        return True
    try:
        profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        return "srgb" in (ImageCms.getProfileDescription(profile) or "").lower().replace(" ", "")
    except (ImageCms.PyCMSError, OSError, ValueError):
        return True


def _rotated(d: bytes) -> bool:
    try:
        with Image.open(io.BytesIO(d)) as im:
            return im.getexif().get(0x0112, 1) not in (0, 1)
    except Exception:
        return False


def _redraw(d: bytes) -> bytes:
    """Encoded again: turned by its EXIF rotation, in sRGB by its profile — then cleaned as any other.
    A JPEG at quality 95 with full colour, a PNG and a lossless WEBP as they were."""
    with Image.open(io.BytesIO(d)) as im:
        fmt = "JPEG" if im.format == "MPO" else im.format   # a phone's JPEG with its HDR map / preview: the first picture
        lossless = fmt == "WEBP" and b"VP8L" in _webp(d)[0][12:40]   # the image chunk comes first once the rest is gone
        im.load()
        icc = im.info.get("icc_profile")
        im = ImageOps.exif_transpose(im)
        if im.mode in ("P", "PA"):
            im = im.convert("RGBA")
        if icc and not _srgb_icc(icc):
            mode = "RGBA" if im.mode in ("RGBA", "LA") else "RGB"
            try:
                im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)),
                                               ImageCms.createProfile("sRGB"), outputMode=mode)
            except ImageCms.PyCMSError:   # a profile LittleCMS can't convert by: the profile goes, the pixels stay
                core.log.warning("Metadata: a colour profile not converted to sRGB")
        if im.mode not in ("RGB", "RGBA", "L", "LA"):
            im = im.convert("RGB")
        buf = io.BytesIO()
        if fmt == "JPEG":
            im.convert("RGB" if im.mode != "L" else "L").save(buf, "JPEG", quality=95, subsampling=0)
        elif fmt == "WEBP":
            im.save(buf, "WEBP", lossless=lossless, quality=100 if lossless else 95)
        else:
            im.save(buf, "PNG", compress_level=6)
    out = buf.getvalue()
    return {"PNG": _png, "JPEG": _jpeg, "WEBP": _webp}[fmt](out)[0]


# ---------------------------------------------------------------- video

# ffmpeg's flags for a video without metadata: no tags, no chapters, no encoder's name, no dates (photos.trim() too).
VIDEO_CLEAN = ["-map_metadata", "-1", "-map_chapters", "-1", "-fflags", "+bitexact",
               "-flags:v", "+bitexact", "-flags:a", "+bitexact"]


def _video(path: Path) -> bool:
    if not video_dirty(path):
        return False
    from . import desktop
    from .photos import ffmpeg
    before = os.stat(path)
    part = path.with_name(path.stem + ".part" + path.suffix)
    try:
        run = subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(path),
                              "-map", "0:v", "-map", "0:a?", "-c", "copy", *VIDEO_CLEAN, "-movflags", "+faststart",
                              str(part)], capture_output=True, timeout=600, creationflags=desktop.CREATE_NO_WINDOW)
        if run.returncode != 0 or not part.is_file() or part.stat().st_size < 1024 or video_dirty(part):
            raise RuntimeError("ffmpeg: " + run.stderr.decode("utf-8", "replace").strip()[-300:])
        os.utime(part, ns=(before.st_atime_ns, before.st_mtime_ns))
        now = os.stat(path)
        if (now.st_size, now.st_mtime_ns) != (before.st_size, before.st_mtime_ns):
            raise OSError(f"{path.name} changed while it was cleaned")
        core.replace_file(part, path)
    finally:
        part.unlink(missing_ok=True)
    return True


_MP4_TOP = {b"ftyp", b"moov", b"mdat", b"free", b"skip", b"wide"}
_MP4_INTO = {b"moov", b"trak", b"mdia", b"minf", b"stbl", b"edts", b"dinf"}
_MP4_TIMES = {b"mvhd", b"tkhd", b"mdhd"}


def _empty_tags(body: bytes) -> bool:
    """The udta ffmpeg writes even without metadata: a meta box with its handler and an empty tag list — nothing in it."""
    if len(body) < 12 or body[4:8] != b"meta":
        return False
    meta, at, kinds = body[12:struct.unpack(">I", body[:4])[0]], 0, []
    while at + 8 <= len(meta):
        n, kind = struct.unpack(">I4s", meta[at:at + 8])
        if n < 8:
            return False
        kinds.append((kind, n))
        at += n
    return (len(body) == struct.unpack(">I", body[:4])[0] and len(kinds) == 2 and kinds[0][0] == b"hdlr"
            and kinds[1] == (b"ilst", 8))


def video_dirty(path: Path) -> bool:
    """An MP4/MOV with anything beyond the picture and the sound: a box of tags (udta, meta, uuid where C2PA lives,
    XMP_) anywhere, a box ffmpeg doesn't write at the top, a creation date. One that can't be read whole is _Broken."""
    with open(path, "rb") as f:
        def walk(start: int, stop: int, top: bool) -> bool:
            at = start
            while at + 8 <= stop:
                f.seek(at)
                n, kind = struct.unpack(">I4s", f.read(8))
                head = 8
                if n == 1:
                    n, head = struct.unpack(">Q", f.read(8))[0], 16
                elif n == 0:
                    n = stop - at
                if n < head or at + n > stop:
                    raise _Broken
                if kind == b"udta" and n - head <= 64:
                    f.seek(at + head)
                    if _empty_tags(f.read(n - head)):
                        at += n
                        continue
                if kind in (b"udta", b"meta", b"uuid", b"XMP_") or (top and kind not in _MP4_TOP):
                    return True
                if kind in _MP4_TIMES:
                    f.seek(at + head)
                    version = f.read(1)[0]
                    f.seek(at + head + 4)
                    times = struct.unpack(">QQ", f.read(16)) if version == 1 else struct.unpack(">II", f.read(8))
                    if any(times):
                        return True
                if kind in _MP4_INTO and walk(at + head, at + n, False):
                    return True
                at += n
            if at != stop:
                raise _Broken
            return False
        return walk(0, os.fstat(f.fileno()).st_size, True)
