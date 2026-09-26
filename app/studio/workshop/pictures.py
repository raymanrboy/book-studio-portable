"""A picture into its row — the owner's flipper and slicer (Etsy-Book-Pipeline's mirror-alternate.py and
slice-spreads.py, 2026-09-24):

- a spread: mirrored first when it's one of the flipper's spreads (4–5, 8–9 … 28–29), cut to 2:1 around the centre
  (a wider picture loses its sides, a narrower one its top and bottom), cut into two square pages;
- page 1 / page 30: a square page (cut to a square around the centre when it's more than 4 % off);
- the cover, in two stages: the picture (`cover`) is kept and laid on the printer's template, the rest white, for the
  outpaint (`build_expanded()`); the outpainted one (`cover-wrap`) becomes `pictures/Cover.png` at the template's
  exact size (`fit_template()`);
- the hero: `agent/canonical.png` (or a variant's `hero.png`) — the one picture the Workshop puts into agent/.

The picture itself is kept in `originals/`, named by its row (spread-04-05.jpg …) — a download is **moved** there out
of Downloads (the owner, 2026-09-26: "it should live in the program"). Whatever a new picture replaces, or a removal
takes, goes to the book's `.replaced/` folder — never deleted.
"""
from __future__ import annotations

import shutil
import time
from pathlib import Path

from PIL import Image, ImageOps

from .. import core
from ..server import ApiError
from . import books
from .rows import MIRRORED, TEMPLATE, cover_state, original_of, original_stem, row, template_layout

OFF = 0.04       # a picture more than 4 % away from its frame's proportion is cut (and says so)
FORMATS = {"PNG", "JPEG", "WEBP", "MPO"}
CUT_WORDS = {"sides": "обрізано з боків", "top-bottom": "обрізано зверху й знизу"}


def open_picture(source: Path, name: str) -> Image.Image:
    try:
        with Image.open(source) as im:
            if (im.format or "").upper() not in FORMATS:
                raise ApiError(f"Формат {im.format or 'невідомий'} не підтримується — потрібен PNG, JPG або WEBP.")
            dpi = im.info.get("dpi")
            im = ImageOps.exif_transpose(im)
            if im.mode not in ("RGB", "RGBA"):   # a see-through picture stays see-through
                im = im.convert("RGBA" if im.mode in ("LA", "PA") or "transparency" in im.info else "RGB")
            im.load()
            im.info["dpi"] = dpi
            return im
    except (OSError, Image.DecompressionBombError):
        raise ApiError(f"Файл «{name}» не є картинкою або пошкоджений.") from None


def two_squares(im: Image.Image) -> tuple[Image.Image, Image.Image, str]:
    """The spread's two pages, each a square as high as the picture, centred (the owner's slice-spreads.py);
    returns the left page, the right page and what went ('', 'sides', 'top-bottom')."""
    w, h = im.size
    side = min(h, w // 2)
    x0, y0 = (w - 2 * side) // 2, (h - side) // 2
    cut = "top-bottom" if h > side else "sides" if w > 2 * side + 1 else ""
    return im.crop((x0, y0, x0 + side, y0 + side)), im.crop((x0 + side, y0, x0 + 2 * side, y0 + side)), cut


def square(im: Image.Image) -> tuple[Image.Image, str]:
    w, h = im.size
    if abs(w / h - 1) <= OFF:
        return im, ""
    side = min(w, h)
    x0, y0 = (w - side) // 2, (h - side) // 2
    return im.crop((x0, y0, x0 + side, y0 + side)), "sides" if w > h else "top-bottom"


# ---------------------------------------------------------------- files

def _retire(book: Path, target: Path) -> None:
    """A file a new picture replaces, or a removal takes, into the book's .replaced/ — never deleted."""
    if target.exists():
        keep = book / ".replaced"
        keep.mkdir(exist_ok=True)
        rel = target.relative_to(book).as_posix().replace("/", "__")
        stamp, n = time.strftime("%Y%m%d-%H%M%S"), 1
        dest = keep / f"{stamp}-{rel}"
        while dest.exists():  # twice in one second: each kept copy has a name of its own
            n += 1
            dest = keep / f"{stamp}.{n}-{rel}"
        core.replace_file(target, dest)


def _write(im: Image.Image, target: Path, keep_old_of: Path | None = None) -> None:
    """A picture written beside its target and swapped in. A page open in a viewer can be locked for a moment on
    Windows (the swaps try again); a failed write never leaves a half-written `.tmp` among the pages.
    `keep_old_of`: the book whose .replaced/ keeps what the new picture replaces."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    dpi = im.info.get("dpi")
    try:
        im.save(tmp, "PNG", compress_level=4, **({"dpi": dpi} if dpi else {}))
        if keep_old_of is not None:
            _retire(keep_old_of, target)
        core.replace_file(tmp, target)
    finally:
        tmp.unlink(missing_ok=True)


def _save(book: Path, im: Image.Image, target: Path) -> None:
    _write(im, target, keep_old_of=book)


def _move(source: Path, dest: Path) -> None:
    """A download out of Downloads — it may still be held by the browser for a moment."""
    for _ in range(20):
        try:
            shutil.move(str(source), str(dest))
            return
        except PermissionError:
            time.sleep(0.15)
    shutil.copyfile(source, dest)  # still held: the Workshop keeps a copy, the file stays in Downloads


def _keep_original(book: Path, key: str, variant: str | None, source: Path, name: str, take: bool) -> Path:
    folder = book / books.ORIGINALS / ("variants/" + variant if variant else "")
    folder.mkdir(parents=True, exist_ok=True)
    stem = original_stem(key)
    for old in list(folder.glob(f"{stem}.*")):
        _retire(book, old)
    suffix = Path(name).suffix.lower()
    suffix = ".jpg" if suffix == ".jpeg" else suffix if suffix in books.IMAGE_SUFFIXES else ".png"
    dest = folder / f"{stem}{suffix}"
    if take:
        _move(source, dest)
    else:
        shutil.copyfile(source, dest)
    return dest


def _variant(book: Path, variant: str | None) -> str | None:
    """The variant a request names, checked before anything is written: an existing folder in agent/variants/,
    never a path out of the book."""
    return variant_dir(book, variant).name if variant else None


def _pictures_dir(book: Path, variant: str | None) -> Path:
    return book / books.PICTURES / "variants" / variant if variant else book / books.PICTURES


def variant_dir(book: Path, variant: str) -> Path:
    base = (book / books.AGENT / "variants").resolve()
    folder = (base / variant).resolve()
    if not variant or folder.parent != base or not folder.is_dir():
        raise ApiError("Варіант не знайдено.", 404)
    return folder


def _mark(book: Path, variant: str | None, key: str, marks: dict | None) -> None:
    """What the Workshop notes about a row's picture (mirrored, cut, where it came from, its size), in book.json."""
    slot = f"{variant}/{key}" if variant else key

    def change(data):
        rows = data.setdefault("rows", {})
        if marks is None:
            rows.pop(slot, None)
        else:
            rows[slot] = {**rows.get(slot, {}), **marks}
    books.update_state(book, change)


# ---------------------------------------------------------------- a picture into its row

def place(book_id: str, key: str, source: Path, name: str, variant: str | None = None, take: bool = False) -> dict:
    """Puts one picture into a row; `take` moves the file (a download) instead of copying it. Returns what
    happened, in the owner's words."""
    book = books.book_path(book_id)
    variant = _variant(book, variant)
    if key not in ("hero", "cover-wrap"):
        row(key)
    im = open_picture(source, name)  # only a real picture goes anywhere, and nothing is moved before that
    size = list(im.size)
    stamp = {"from": Path(name).name[:160], "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": size}
    _keep_original(book, key, variant, source, name, take)
    if key == "hero":
        target = variant_dir(book, variant) / "hero.png" if variant else book / books.AGENT / "canonical.png"
        _save(book, im, target)
        return {"key": key, "label": "Герой", "note": "Герой на місці" + (f" ({variant})" if variant else "")}
    if key == "cover":
        _mark(book, None, "cover", {**stamp, "cut": ""})
        _mark(book, None, "cover-wrap", None)
        final = _pictures_dir(book, None) / "Cover.png"
        if final.exists():
            _retire(book, final)  # a new picture: the old cover with margins no longer fits it
        build_expanded(book, im)
        return {"key": key, "label": "Обкладинка", "note": "Обкладинка на місці — додано поля, далі аутпейнт"}
    if key == "cover-wrap":
        final, cut = fit_template(im)
        _save(book, final, _pictures_dir(book, None) / "Cover.png")
        _mark(book, None, "cover-wrap", {**stamp, "skipped": False, "cut": cut})
        w, h = TEMPLATE["px"]
        return {"key": key, "label": "Обкладинка",
                "note": f"Обкладинка з полями — готова: {w}×{h}, 300 dpi, у папці сторінок"}
    r = row(key)
    folder = _pictures_dir(book, variant)
    if r["kind"] == "single":
        page, cut = square(im)
        page.info["dpi"] = im.info.get("dpi")
        _save(book, page, folder / f"{r['pages'][0]}.png")
        _mark(book, variant, key, {"mirrored": False, "cut": cut, **stamp})
        return {"key": key, "label": r["label"], "cut": cut,
                "note": f"{r['label']}: {CUT_WORDS[cut] + ' до квадрата' if cut else 'готова'}"}
    mirrored = int(key[6:]) in MIRRORED
    if mirrored:
        im = ImageOps.mirror(im)
    left, right, cut = two_squares(im)
    if cut and abs(size[0] / size[1] / 2 - 1) <= OFF:
        cut = ""  # a pixel or two isn't worth a mark
    for page, n in zip((left, right), r["pages"]):
        page.info["dpi"] = im.info.get("dpi")
        _save(book, page, folder / f"{n}.png")
    _mark(book, variant, key, {"mirrored": mirrored, "cut": cut, **stamp})
    parts = [p for p in ("віддзеркалено" if mirrored else "", CUT_WORDS.get(cut, "")) if p]
    return {"key": key, "label": r["label"], "mirrored": mirrored, "cut": cut,
            "note": f"{r['label']}: {', '.join(parts) + ' — і ' if parts else ''}дві сторінки готові"}


# ---------------------------------------------------------------- the cover's margins

def _art(book: Path) -> Path:
    name = original_of(books._names(book / books.ORIGINALS), "cover")
    if not name:
        raise ApiError("Спершу сама обкладинка — перший етап.")
    return book / books.ORIGINALS / name


def build_expanded(book: Path, im: Image.Image | None = None) -> list[int]:
    """The cover's picture laid on the printer's template — its width the finished width, centred — and white all
    round, for the generator to fill (`template_layout()`)."""
    if im is None:
        im = open_picture(_art(book), "cover")
    lay = template_layout(*im.size)
    cw, ch = lay["canvas"]
    canvas = Image.new("RGB", (cw, ch), (255, 255, 255))
    canvas.paste(im.convert("RGB"), tuple(lay["art"][:2]))
    _write(canvas, book / books.ORIGINALS / "cover-expanded.png")  # made from the picture — nothing to keep
    _mark(book, None, "cover-expanded", {"size": [cw, ch], "art": lay["art"], "ppi": lay["ppi"], "template": True})
    return [cw, ch]


def fit_template(im: Image.Image) -> tuple[Image.Image, str]:
    """The outpainted cover brought to the template's exact size (5370×2850 px, 300 dpi): a result of other
    proportions is first cut around its centre to the template's."""
    tw, th = TEMPLATE["px"]
    w, h = im.size
    cut = ""
    if abs((w / h) / (tw / th) - 1) > 0.005:
        if w / h > tw / th:
            nw = round(h * tw / th)
            im, cut = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h)), "sides"
        else:
            nh = round(w * th / tw)
            im, cut = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh)), "top-bottom"
    out = im.convert("RGB").resize((tw, th), Image.LANCZOS)
    out.info["dpi"] = (TEMPLATE["dpi"], TEMPLATE["dpi"])
    return out, cut


def skip_margins(book_id: str) -> dict:
    """«Без полів»: the cover's picture itself becomes Cover.png."""
    book = books.book_path(book_id)
    im = open_picture(_art(book), "cover")
    _save(book, im, _pictures_dir(book, None) / "Cover.png")
    _mark(book, None, "cover-wrap", {"skipped": True, "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
    return {"note": "Обкладинка без полів — у папці сторінок"}


# ---------------------------------------------------------------- ⇄, removing, a picture for the clipboard

def _pages(book: Path, key: str, variant: str | None) -> list[Path]:
    folder = _pictures_dir(book, variant)
    names = set(books._names(folder))
    return [folder / books.picture(names, p) for p in row(key)["pages"] if books.picture(names, p)]


def flip(book_id: str, key: str, variant: str | None = None) -> dict:
    """⇄ on a spread: the right page mirrored becomes the left one and the other way round (the same as mirroring
    the whole panorama); twice gives back what was there, pixel for pixel."""
    book = books.book_path(book_id)
    variant = _variant(book, variant)
    if row(key)["kind"] != "spread":
        raise ApiError("Віддзеркалити можна тільки розворот.")
    pages = _pages(book, key, variant)
    if len(pages) != 2:
        raise ApiError("У розвороті немає двох сторінок — спершу покладіть картинку.")
    with Image.open(pages[0]) as l_im, Image.open(pages[1]) as r_im:
        new_left, new_right = ImageOps.mirror(r_im), ImageOps.mirror(l_im)
    for im, target in ((new_left, pages[0]), (new_right, pages[1])):
        _write(im, target)  # the flip itself is lossless — the old pages aren't kept
    slot = f"{variant}/{key}" if variant else key
    was = (books.state(book).get("rows") or {}).get(slot, {}).get("mirrored", int(key[6:]) in MIRRORED)
    _mark(book, variant, key, {"mirrored": not was})
    return {"key": key, "mirrored": not was}


def remove(book_id: str, key: str, variant: str | None = None) -> dict:
    """The row's pictures out of the book — into .replaced/, with the picture as it came."""
    book = books.book_path(book_id)
    variant = _variant(book, variant)
    originals = book / books.ORIGINALS / ("variants/" + variant if variant else "")
    if key in ("cover", "cover-wrap"):
        targets = [_pictures_dir(book, None) / "Cover.png"]
        stems = ("cover-art", "cover-wrap") if key == "cover" else ("cover-wrap",)
        if key == "cover":
            targets.append(originals / "cover-expanded.png")
            _mark(book, None, "cover", None)
            _mark(book, None, "cover-expanded", None)
        targets += [originals / n for n in books._names(originals) if Path(n).stem in stems]
        _mark(book, None, "cover-wrap", None)
    else:
        targets = _pages(book, key, variant) + [originals / n for n in books._names(originals)
                                                if Path(n).stem == original_stem(key)]
        _mark(book, variant, key, None)
    for t in targets:
        _retire(book, t)
    return {"key": key}


def spread_panorama(book_id: str, key: str) -> Image.Image:
    """The base spread as one 2:1 picture — as it came from Gemini (its original), else its two pages side by
    side, un-mirrored — what a hero variant's swap prompt edits, or what goes to an agent as «the best frame»."""
    book = books.book_path(book_id)
    original = original_of(books._names(book / books.ORIGINALS), key)
    if original:
        return open_picture(book / books.ORIGINALS / original, original)
    pages = _pages(book, key, None)
    if len(pages) != 2:
        raise ApiError("Спершу потрібен сам розворот.")
    with Image.open(pages[0]) as a, Image.open(pages[1]) as b:
        pano = Image.new("RGB", (a.width + b.width, max(a.height, b.height)), (255, 255, 255))
        pano.paste(a.convert("RGB"), (0, 0))
        pano.paste(b.convert("RGB"), (a.width, 0))
    mirrored = (books.state(book).get("rows") or {}).get(key, {}).get("mirrored", int(key[6:]) in MIRRORED)
    return ImageOps.mirror(pano) if mirrored else pano


def picture_for_clipboard(book_id: str, key: str) -> Image.Image:
    """«Копіювати картинку»: a spread as Gemini made it; a page, the cover — as they are."""
    book = books.book_path(book_id)
    if key.startswith("spread"):
        return spread_panorama(book_id, key)
    if key == "cover":
        c = cover_state(book)
        path = (book / books.PICTURES / c["final"] if c["final"]
                else book / books.ORIGINALS / c["art"] if c["art"] else None)
    else:
        pages = _pages(book, key, None)
        path = pages[0] if pages else None
    if not path or not path.is_file():
        raise ApiError("Картинки ще немає.")
    return open_picture(path, path.name)
