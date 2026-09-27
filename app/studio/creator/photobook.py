"""The photobook PDF Gelato prints from: cover sheet, blank, the pages, blank — the PNGs go in as they are (no
re-encoding), each page at the size the catalog gives."""
from __future__ import annotations

import functools
import io
import math
import struct
import zlib
from pathlib import Path

from .. import images


MM_TO_PT = 72 / 25.4


def _one_idat(data: bytes) -> bytes:
    """The same PNG with its compressed pixel data in a single IDAT chunk — nothing is re-encoded.

    Canva writes thousands of 8 KB IDAT chunks; img2pdf 0.6 joins them one by one (quadratic copying,
    ~3 s per page). Joined once here, img2pdf reads the page in milliseconds.
    """
    if data[:8] != images.PNG_SIGNATURE:
        return data
    chunks, idat, pos = [], [], 8
    while pos + 8 <= len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        chunks.append((kind, data[pos:pos + 12 + length]))
        if kind == b"IDAT":
            idat.append(data[pos + 8:pos + 8 + length])
        pos += 12 + length
    if len(idat) <= 1:
        return data
    body = b"".join(idat)
    merged = struct.pack(">I", len(body)) + b"IDAT" + body + struct.pack(">I", zlib.crc32(b"IDAT" + body) & 0xFFFFFFFF)
    out, placed = [images.PNG_SIGNATURE], False
    for kind, raw in chunks:
        if kind == b"IDAT":
            if not placed:
                out.append(merged)
                placed = True
            continue
        out.append(raw)
    return b"".join(out)


class _Page:
    """A page of the PDF as img2pdf reads it — when it gets to it: the file is read and joined into one IDAT then,
    so the book is never held twice in memory (it used to be copied to temporary files first, and the finished
    PDF built in memory and copied once more: ~2.5–3 GB for 30 pages, 26.09.2026)."""

    def __init__(self, path: Path | None = None, data: bytes | None = None):
        self.path, self.data = path, data

    def read(self) -> bytes:
        return self.data if self.data is not None else _one_idat(self.path.read_bytes())


@functools.lru_cache(maxsize=4)
def _blank_png(px: tuple[int, int]) -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", px, (255, 255, 255)).save(buf, "PNG")
    return buf.getvalue()


COVER_TRIM_WARN_MM = 10  # the Canva cover is always a few mm off Gelato's; only a wrong picture trims more

BLANK_DPI = 300  # the blank endpapers, as in the PDFs Gelato makes itself (1725 px for a 14 cm page)


def build_photobook_pdf(cover: Path, pages: list[Path], out: Path, geo: dict) -> dict:
    """One PDF laid out the way Gelato prints a photo book (its only accepted file for books):

      page 1          — the cover sheet (back + spine + front);
      page 2          — blank: the front endpaper (Gelato's draft view calls it "Page 0");
      pages 3 … N+2   — the inner pages in order ("Page 1" … "Page N");
      last page       — blank: the back endpaper (not shown in the draft view).

    The blanks are required: without them the book's page 1 took the endpaper's place ("Page 0")
    and the last page was left empty (test draft, 17.09.2026). The PDF Gelato itself printed for the
    owner's good API order (made over in Gelato's editor) has the same shape; only a book from that
    editor is listed without "Page 0". The blanks are white pictures at print resolution: Gelato rates
    the whole book by its poorest picture, and a 16-pixel blank made it 3 dpi.

    Every PDF page gets Gelato's physical size; pictures are embedded without recompression and
    scaled to fill their page (a slightly different aspect is trimmed evenly at the edges).
    Returns what was built, for the send journal, with a warning only when the cover loses much more
    than the usual few millimetres.
    """
    import img2pdf
    from PIL import Image

    cover_page = (geo["coverMm"][0] * MM_TO_PT, geo["coverMm"][1] * MM_TO_PT)
    inner_page = (geo["pageMm"][0] * MM_TO_PT, geo["pageMm"][1] * MM_TO_PT)
    blank = _Page(data=_blank_png(tuple(math.ceil(mm / 25.4 * BLANK_DPI) for mm in geo["pageMm"])))
    sequence = ([(_Page(cover), cover_page), (blank, inner_page)] + [(_Page(p), inner_page) for p in pages]
                + [(blank, inner_page)])
    sizes = iter([size for _, size in sequence])  # img2pdf lays images out in the order they are given

    def layout(img_w: float, img_h: float, _dpi) -> tuple:
        page_w, page_h = next(sizes)
        scale = max(page_w / img_w, page_h / img_h)
        return page_w, page_h, img_w * scale, img_h * scale

    # Written straight into the file. The engine is named: img2pdf would quietly take another one on a computer
    # without pikepdf, and only this one has made the books Gelato printed (requirements.txt).
    with open(out, "wb") as f:
        img2pdf.convert(*(page for page, _ in sequence), layout_fun=layout, outputstream=f,
                        engine=img2pdf.Engine.pikepdf)

    with Image.open(cover) as im:
        img_w, img_h = im.size
    want_w, want_h = geo["coverMm"]
    scale = max(want_w / img_w, want_h / img_h)
    trim_side = round(max(img_w * scale - want_w, img_h * scale - want_h) / 2, 2)
    warnings = []
    if trim_side > COVER_TRIM_WARN_MM:
        warnings.append(f"Cover.png ({img_w}×{img_h}) зовсім іншої форми, ніж обкладинка Gelato "
                        f"{round(want_w)}×{round(want_h)} мм: краї обріжуться на {trim_side:.0f} мм. "
                        f"Перевірте, що це справді обкладинка.")
    return {"pdfPages": len(sequence), "pdfBytes": out.stat().st_size, "coverPx": [img_w, img_h],
            "coverMm": geo["coverMm"], "pageMm": geo["pageMm"], "coverTrimMm": trim_side, "warnings": warnings}
