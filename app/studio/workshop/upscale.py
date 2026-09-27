"""Upscaling — the step after a picture lands in its row (the owner, 2026-09-27: "a dropped spread is cut, flipped
and upscaled at once", with a way to skip it for a whole book).

The owner's own Upscayl does the work: its command-line engine (`upscayl-bin.exe`, no window), the model
**upscayl-standard-4x**, the output **×2** — whatever size the picture came in ("just 2× — I use different
generators, their sizes differ"). The picture upscaled is the row's original (the spread as the generator made it,
before it is cut — the two halves stay alike, no seam); the big one is then mirrored and cut exactly as the small one
was, and its pages replace the small ones in `pictures/`. The original itself stays as it came.

    rows upscaled   page 1 (the dedication), spreads 2–3 … 28–29, page 30 (the afterword), the cover — its outpainted
                    picture (or, «Без полів», the picture itself) before it is brought to the printer's template;
                    each hero variant's spreads and cover (the owner, 2026-09-27: "there's no upscale in the variants")
    not upscaled    the hero pictures themselves (canonical.png, a variant's hero.png — "the hero — no")

A row is named by its slot, as in book.json's marks: «spread3», or «G2_brunette/spread3» in a variant.

The work goes on in the background, one picture at a time (the graphics card is shared with the text check's
model): the small pages are there at once, the big ones replace them some seconds later. A book can be left without
upscaling (book.json → "upscale": false; on by default). A picture replaced or removed while it waited is left
alone. A row that failed keeps its small pages and says why; nothing waits on it.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

from PIL import Image, ImageOps

from .. import core, desktop
from ..server import ApiError
from . import books, rows

MODEL = "upscayl-standard-4x"  # the model the owner picked in Upscayl himself
SCALE = 2                      # "just 2×, whatever size the picture comes in"
KEYS = ["page1"] + [f"spread{n}" for n in rows.SPREADS] + ["page30", "cover-wrap"]  # in the book's order
# A page this many pixels a side is print-ready already (8″ at 300 dpi) — a picture that big (upscaled elsewhere, or
# a generator that gives big ones) isn't offered for upscaling (the owner, 2026-09-27: "it doesn't recognise big
# pictures"). For the cover — its height (the template's is 2850).
BIG = 2400
FAKE_DELAY = 0.6  # the sandbox's pretend engine takes a moment, so the preview shows the progress
_PERCENT = re.compile(r"(\d{1,3}(?:\.\d+)?)%")


# ---------------------------------------------------------------- the engine

def _candidates():
    """Where Upscayl may be: the place remembered, the place Upscayl's own log names (it writes the engine's path
    on every start — the owner's is on drive D), its usual installs. Looked at one by one, the logs only when needed."""
    saved = core.settings.section("workshop").get("upscayl")
    if saved:
        yield Path(saved)
    appdata = os.environ.get("APPDATA")
    logs = Path(appdata) / "Upscayl" / "logs" if appdata else None
    if logs and logs.is_dir():
        for log in sorted(logs.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]:
            try:
                text = log.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in reversed(re.findall(r"UPSCAYL EXEC PATH:\s*(.+)", text)):
                yield Path(m.strip())
    for base in (os.environ.get("LOCALAPPDATA", "") + r"\Programs", os.environ.get("ProgramFiles", "")):
        if base.strip("\\"):
            yield Path(base) / "Upscayl" / "resources" / "bin" / "upscayl-bin"


_missing_until = 0.0  # Upscayl not found: looked for again only after a while (a page asks every 1.5 s)


def engine() -> tuple[Path, Path] | None:
    """The engine (upscayl-bin.exe) and its models' folder — the first place that has both; remembered."""
    global _missing_until
    if time.monotonic() < _missing_until:
        return None
    for c in _candidates():
        exe = c if c.suffix.lower() == ".exe" else c.with_name(c.name + ".exe")
        models = exe.parent.parent / "models"
        if exe.is_file() and (models / f"{MODEL}.param").is_file():
            if core.settings.section("workshop").get("upscayl") != str(exe):
                core.settings.update({"workshop": {"upscayl": str(exe)}})
            return exe, models
    _missing_until = time.monotonic() + 30
    return None


def available() -> bool:
    return core.SANDBOX or engine() is not None


def _run_engine(source: Path, target: Path, progress) -> None:
    """source → target, ×2, by the owner's Upscayl; the sandbox pretends (a plain resize), touching nothing of his."""
    if core.SANDBOX:
        with Image.open(source) as im:
            big = im.resize((im.width * SCALE, im.height * SCALE), Image.LANCZOS)
        for pct in (30, 70):
            time.sleep(FAKE_DELAY / 2)
            progress(pct)
        big.save(target, "PNG")
        return
    found = engine()
    if not found:
        raise ApiError("Upscayl не знайдено — встановіть його або запустіть хоч раз, щоб програма його знайшла.")
    exe, models = found
    proc = subprocess.Popen(
        [str(exe), "-i", str(source), "-o", str(target), "-s", str(SCALE), "-m", str(models), "-n", MODEL, "-f", "png"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=desktop.CREATE_NO_WINDOW if os.name == "nt" else 0)
    tail = b""
    while True:
        chunk = proc.stdout.read(64)
        if not chunk:
            break
        tail = (tail + chunk)[-400:]
        found_pct = _PERCENT.findall(tail.decode("utf-8", "replace"))
        if found_pct:
            progress(min(99, float(found_pct[-1])))
    code = proc.wait()
    if code != 0 or not target.is_file():
        said = " ".join(tail.decode("utf-8", "replace").split())[-160:]
        raise ApiError(f"Upscayl не впорався (код {code}){': ' + said if said else ''}")


# ---------------------------------------------------------------- one row

def enabled(path: Path) -> bool:
    """On unless the owner turned it off for this book."""
    return books.state(path).get("upscale") is not False


def _marks(path: Path, slot: str) -> dict:
    return (books.state(path).get("rows") or {}).get(slot) or {}


def split(slot: str) -> tuple[str | None, str]:
    """A row's slot — «spread3» in the base book, «G2_brunette/spread3» in a hero variant — as (variant, key)."""
    variant, _, key = slot.rpartition("/")
    return variant or None, key


def _folders(path: Path, variant: str | None) -> tuple[Path, Path]:
    tail = f"variants/{variant}" if variant else ""
    return path / books.ORIGINALS / tail, path / books.PICTURES / tail


def _source(path: Path, slot: str) -> Path | None:
    """The picture a row's pages are made from, while the row has its pages: a page's or a spread's original; the
    cover's outpainted picture (or, «Без полів», the picture itself) once Cover.png is there; a variant's — in its
    own folders."""
    variant, key = split(slot)
    if key not in KEYS or (variant and (key.startswith("page") or variant not in rows.variant_names(path))):
        return None
    orig_dir, pic_dir = _folders(path, variant)
    originals = books._names(orig_dir)
    pictures = set(books._names(pic_dir))
    if key == "cover-wrap":
        if not books.picture(pictures, "Cover"):
            return None
        name = rows.original_of(originals, "cover" if _marks(path, slot).get("skipped") else "cover-wrap")
    else:
        if not all(books.picture(pictures, p) for p in rows.row(key)["pages"]):
            return None
        name = rows.original_of(originals, key)
    return orig_dir / name if name else None


def slots(path: Path) -> list[str]:
    """Every row that can be upscaled: the base book's, then each hero variant's spreads and cover."""
    out = list(KEYS)
    for v in rows.variant_names(path):
        out += [f"{v}/spread{n}" for n in rows.SPREADS] + [f"{v}/cover-wrap"]
    return out


_sizes: dict[tuple[str, int, int], tuple[int, int]] = {}  # a picture's size by its path, mtime and length


def _size(file: Path) -> tuple[int, int] | None:
    """A picture's size from its header (cached; the page asks often)."""
    try:
        st = file.stat()
        key = (str(file), st.st_mtime_ns, st.st_size)
        if key not in _sizes:
            if len(_sizes) > 5000:
                _sizes.clear()
            with Image.open(file) as im:  # only the header is read
                w, h = im.size
                # A photo turned on its side by its EXIF. A PNG's EXIF is looked for only when it came before the
                # picture itself: asking a PNG for it unpacks the whole picture — 31 s to open a book with 8 hero
                # variants (the owner's book 41, 28.09.2026).
                turned = ((im.format != "PNG" or "exif" in im.info)
                          and im.getexif().get(0x0112) in (5, 6, 7, 8))
            _sizes[key] = (h, w) if turned else (w, h)
        return _sizes[key]
    except (OSError, Image.DecompressionBombError):
        return None


def side(key: str, size) -> int:
    """How many pixels a side the row's page gets from a picture of this size: a spread's half, a page, the cover's
    height."""
    w, h = size
    return h if key == "cover-wrap" else min(h, w // 2) if key.startswith("spread") else min(w, h)


def _page_side(path: Path, slot: str) -> int | None:
    """The side of the row's pages as they are in pictures/ now (the smaller, if the two differ)."""
    variant, key = split(slot)
    folder = _folders(path, variant)[1]
    names = set(books._names(folder))
    found = [books.picture(names, p) for p in rows.row(key)["pages"]]
    sizes = [_size(folder / n) for n in found if n]
    return min(min(sz) for sz in sizes) if sizes and all(sizes) else None


def sides(path: Path) -> dict[str, dict]:
    """Every row with pages: its page's side as it is in the book now, and whether it is big enough already — what the
    chips over the pictures say, and what's left to upscale. The pages themselves are measured (an original replaced
    by a bigger one by hand doesn't make its pages big); the cover — by its picture's height, its Cover.png is always
    the template's size."""
    marks = books.state(path).get("rows") or {}
    out = {}
    for slot in slots(path):
        source = _source(path, slot)
        size = source and _size(source)
        if not size:
            continue
        variant, key = split(slot)
        up = (marks.get(slot) or {}).get("upscaled")
        now = side(key, up["size"] if up else size) if key == "cover-wrap" else _page_side(path, slot)
        if now is None:
            continue
        big = not up and now >= BIG
        # an original bigger than its pages (upscaled by hand, put back into originals/): the pages are only cut again
        recut = not up and not big and side(key, size) >= BIG
        out[slot] = {"side": now, "upscaled": bool(up), "big": big, "recut": recut, "original": side(key, size)}
    return out


def todo(book_id: str, known: dict | None = None) -> list[str]:
    """The rows with pages that aren't upscaled yet and aren't big already (their slots) — those whose original is
    big already among them (they are only cut again)."""
    known = known if known is not None else sides(books.book_path(book_id))
    return [s for s, v in known.items() if not v["upscaled"] and not v["big"]]


def upscale_row(book_id: str, slot: str, progress=lambda pct: None) -> dict | None:
    """One row upscaled: its original ×2, then mirrored and cut as before — the big pages replace the small ones.
    None when there is nothing to do (the row emptied, or its picture replaced while this ran)."""
    from . import pictures
    path = books.book_path(book_id)
    variant, key = split(slot)
    source = _source(path, slot)
    if not source:
        return None
    stamp = _marks(path, slot).get("pic")
    size = _size(source)
    recut = bool(size) and side(key, size) >= BIG  # the original is big already (upscaled by hand): only cut again
    if recut:
        big = pictures.open_picture(source, source.name)
    else:
        tmp = core.data_path("tmp", f"upscale-{core.new_id()}.png")
        tmp.parent.mkdir(parents=True, exist_ok=True)
        # Upscayl gets a copy: while it works, the book's own picture stays free — replacing it then no longer
        # fails with «the file is used by another process» (28.09.2026).
        given = tmp.with_name(tmp.stem + "-in" + source.suffix.lower())
        try:
            shutil.copyfile(source, given)
            _run_engine(given, tmp, progress)
            big = pictures.open_picture(tmp, tmp.name)
        finally:
            tmp.unlink(missing_ok=True)
            given.unlink(missing_ok=True)
    with pictures.WRITING:  # a picture placed, flipped or removed meanwhile wins
        marks = _marks(path, slot)
        if marks.get("pic") != stamp or _source(path, slot) != source:
            return None
        folder = _folders(path, variant)[1]
        if key == "cover-wrap":
            final = big if marks.get("skipped") else pictures.fit_template(big)[0]
            pictures._write(final, folder / "Cover.png")
        elif key.startswith("spread"):
            if marks.get("mirrored", int(key[6:]) in rows.MIRRORED):
                big = ImageOps.mirror(big)
            left, right, _ = pictures.two_squares(big)
            for page, n in zip((left, right), rows.row(key)["pages"]):
                pictures._write(page, folder / f"{n}.png")
        else:
            pictures._write(pictures.square(big)[0], folder / f"{rows.row(key)['pages'][0]}.png")
        if recut:  # not upscaled — its pages are simply as big as its original now
            return {"recut": True, "size": list(big.size)}
        done = {"scale": SCALE, "model": MODEL, "size": list(big.size), "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        pictures._mark(path, variant, key, {"upscaled": done})
    return done


# ---------------------------------------------------------------- the queue

class Upscaler:
    """One picture at a time, for the whole program; the rest wait in order."""

    def __init__(self, run=True):
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.queue: list[tuple[str, str]] = []
        self.current: dict | None = None     # book, key, pct
        self.errors: dict[tuple[str, str], str] = {}
        self.version = 0
        if run:  # the tests turn the handle by hand (step())
            threading.Thread(target=self._loop, name="upscale", daemon=True).start()

    def add(self, book_id: str, keys: list[str]) -> int:
        with self.lock:
            added = 0
            for key in keys:
                self.errors.pop((book_id, key), None)
                if (book_id, key) not in self.queue:
                    self.queue.append((book_id, key))
                    added += 1
            self.version += 1
        self.wake.set()
        return added

    def drop(self, book_id: str) -> None:
        """Nothing more waits for this book (turned off, deleted); the picture in work finishes."""
        with self.lock:
            self.queue = [q for q in self.queue if q[0] != book_id]
            self.errors = {k: v for k, v in self.errors.items() if k[0] != book_id}
            self.version += 1

    def status(self, book_id: str) -> dict:
        with self.lock:
            cur = self.current if self.current and self.current["book"] == book_id else None
            return {"queue": [k for b, k in self.queue if b == book_id],
                    "current": {"key": cur["key"], "pct": cur["pct"]} if cur else None,
                    "errors": {k: msg for (b, k), msg in self.errors.items() if b == book_id}}

    def _progress(self, pct: float) -> None:
        with self.lock:
            if self.current and int(pct) != int(self.current["pct"]):
                self.current["pct"] = int(pct)
                self.version += 1

    def step(self) -> bool:
        """The next picture in the queue; False when there is none."""
        with self.lock:
            if not self.queue:
                return False
            book_id, key = self.queue.pop(0)
            self.current = {"book": book_id, "key": key, "pct": 0}
            self.version += 1
        try:
            upscale_row(book_id, key, self._progress)
            core.log.info("Workshop: upscaled %s %s", book_id, key)
        except (ApiError, OSError, Image.DecompressionBombError) as exc:
            core.log.warning("Workshop: upscaling %s %s failed: %s", book_id, key, exc)
            with self.lock:
                self.errors[(book_id, key)] = str(exc) or "не вдалося"
        finally:
            with self.lock:
                self.current = None
                self.version += 1
        return True

    def _loop(self):
        while True:
            self.wake.wait()
            self.wake.clear()
            while self.step():
                pass


_upscaler: Upscaler | None = None
_lock = threading.Lock()


def upscaler() -> Upscaler:
    """Made (its thread started) the first time something is queued."""
    global _upscaler
    with _lock:
        if _upscaler is None:
            _upscaler = Upscaler()
        return _upscaler


def version() -> int:
    with _lock:
        return _upscaler.version if _upscaler else 0


def status(book_id: str) -> dict:
    """What a book's page shows: on or off, Upscayl found, the queue, the picture in work, what failed, what's left."""
    path = books.book_path(book_id)
    with _lock:
        u = _upscaler
    live = u.status(book_id) if u else {"queue": [], "current": None, "errors": {}}
    known = sides(path)
    return {"on": enabled(path), "available": available(), "scale": SCALE, "model": MODEL, "big": BIG, **live,
            "sides": known, "todo": todo(book_id, known)}


def after_place(book_id: str, key: str, variant: str | None = None) -> None:
    """A picture has just gone into a row (caught, dropped, «Без полів»): upscaled next, when the book wants it."""
    path = books.book_path(book_id)
    slot = f"{variant}/{key}" if variant else key
    if key in KEYS and enabled(path) and available():
        source = _source(path, slot)
        size = source and _size(source)
        if size and side(key, size) >= BIG:
            return  # big already: its pages are cut big, nothing to upscale
        upscaler().add(book_id, [slot])


def set_on(book_id: str, on: bool) -> dict:
    path = books.book_path(book_id)
    books.update_state(path, lambda d: d.pop("upscale", None) if on else d.update(upscale=False))
    if not on:
        with _lock:
            u = _upscaler
        if u:
            u.drop(book_id)
    return status(book_id)


def start(book_id: str, keys: list[str] | None = None) -> dict:
    """«Апскейлити решту» (every row not yet upscaled) or one row again."""
    books.book_path(book_id)
    if not available():
        raise ApiError("Upscayl не знайдено — встановіть його або запустіть хоч раз, щоб програма його знайшла.")
    wanted = todo(book_id) if keys is None else [k for k in keys if k in slots(books.book_path(book_id))]
    if not wanted:
        raise ApiError("Апскейлити нічого — усі сторінки вже апскейлені." if keys is None else "Цей рядок не апскейлиться.")
    upscaler().add(book_id, wanted)
    return status(book_id)


def forget(book_id: str) -> None:
    """The book is gone: nothing waits for it."""
    with _lock:
        u = _upscaler
    if u:
        u.drop(book_id)
