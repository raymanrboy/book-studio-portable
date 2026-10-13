"""Listing mockups: a demo book from Canva goes into the owner's Photoshop templates, filled by one script.

For every new book the owner makes ~10 Etsy listing pictures from purchased mockup templates. Here he drops
the demo book's Canva ZIP and clicks the "presentable" spreads; one Photoshop script then fills copies of
the templates (the templates folder is read-only — the owner's rule): the spreads' pages, the back cover and
the spine everywhere, and the front cover's thin rim in the open-book templates. Seven pictures are saved as
PNG into the folder he picks; the three templates where the front cover really shows are left open in
Photoshop, because he fits the front cover himself ("the cover sells", 23.09.2026).

Since 24.09.2026 a page of Book Studio's Listings mode (it was a program of its own, with its own window).
Its places and runs stay in app/data/mockups; the demo book it unpacks lives there too (BOOKS), apart from
the files dropped for orders. The templates' structure and how it works: wiki/features/mockups.md.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

from PIL import Image, ImageOps

from . import core, desktop, drops, images, portable
from .jobs import Job, UserError, jobs
from .server import ApiError, Request, file_response, route
from .slides import cutout as slide_cutout

# Where things are on the owner's PC; places.json overrides them when he points somewhere else.
TEMPLATES_DIR = core.ROOT.parent.parent / "runtime" / "Templates"    # read-only: only ever read and copied
PHOTOSHOP_DIR = core.ROOT.parent.parent / "runtime" / "Photoshop"    # Photoshop CC 2019, portable
# app/data/mockups — the same files the separate utility kept (its data folder), so they carry over.
PLACES = core.data_path("mockups", "places.json")
WORK = core.data_path("mockups", "work")   # one folder per run: template copies, prepared pictures, the script
# The unpacked demo book: its own folder, never among the files dropped for orders (drops.DROPS) — clearing one
# must not touch the other.
BOOKS = core.data_path("mockups", "book")
PHOTOSHOP_TEMP = core.data_path("tmp", "photoshop")  # a Photoshop started from here keeps its temp files on D
# What the separate utility (until 24.09.2026) left in its data folder: its temp files, previews, window profile.
DISMISSED = "dismissed"             # a run's mark: the owner finished the page («×») — its templates aren't offered again
KEEP_RUNS = 24 * 3600                # with Photoshop open, a run's copies left open in it stay a day at most
KEEP_SAVED = 7 * 24 * 3600           # a copy the owner saved himself (Ctrl+S lands in the run folder): a week
DPI = 300                            # the smart objects are 300 ppi; another dpi would change the placed size
PNG_COMPRESSION = 3                  # Photoshop's PNG level: tested on 23.09.2026 (4000×3000 ≈ 17 MB, ~1.5 s)
START_WAIT = 600                     # a cold start plus the owner's "run this script?" click
GONE_CHECKS = 3                      # Photoshop missing this many checks in a row (5 s apart) = it closed

# Inner sizes of the smart objects, px at 300 ppi (read from the templates with psd-tools, 23.09.2026).
HARD = {"page": (1900, 1900), "board": (2100, 2200), "spine": (80, 2200)}    # files 1–4: a hardcover
SOFT = {"page": (1935, 1935), "board": (1935, 1935), "spine": (164, 1935)}   # the vendor's square softcover

# What the script fills where. Layer paths are compared with spaces trimmed ("Left " in All & Open 1); a
# one-name path is looked for at the top of the layer list, where the shortcut copies are. "slots" — how many
# spreads the owner picks for the template; "hand" — the front cover he fits himself, so the template is left
# open in Photoshop; "keep" — left open too, for his own touch: Dedication's background and table colours (the
# owner, 26.09.2026 — it was saved and closed by itself until then). In the order the owner sees them.
_A = {"front": ("Main", "Cover"), "back": ("Main", "Back Cover"), "spine": ("Main", "Rige")}
TEMPLATES = [
    {"key": "open1", "file": "2. Open 1.psd", "label": "Open 1", "size": HARD, "slots": 4,
     "layers": {**_A, "left": ("Main", "Left"), "right": ("Main", "Right")}},
    {"key": "open2", "file": "3. Open 2.psd", "label": "Open 2", "size": HARD, "slots": 2,
     "layers": {**_A, "left": ("Main", "Left"), "right": ("Main", "Right")}},
    {"key": "coverOpen", "file": "Cover & Open 1.psd", "label": "Cover & Open 1", "size": SOFT, "slots": 1,
     "layers": {"left": ("Left Page",), "right": ("Right Page",)}, "hand": ("Front Cover",)},
    {"key": "allOpen", "file": "All & Open 1.psd", "label": "All & Open 1", "size": SOFT, "slots": 1,
     "layers": {"back": ("Back Cover",), "spine": ("Spine",), "left": ("Left",), "right": ("Right",)},
     "hand": ("Front Cover",)},
    {"key": "dedication", "file": "4. Dedication.psd", "label": "Dedication", "size": HARD, "slots": 0,
     "layers": {**_A, "page1": ("Main", "Page 1")}, "keep": "colours"},
    {"key": "cover1", "file": "1. Cover 1.psd", "label": "Cover 1", "size": HARD, "slots": 0, "layers": {},
     "hand": ("Main", "COVER_")},
]
# Photoshop works through the saved pictures first; the templates it leaves open come last.
RUN_ORDER = ("open1", "open2", "cover1", "coverOpen", "allOpen", "dedication")


def kept_open(t: dict) -> bool:
    """A template the script leaves open in Photoshop for the owner (his front cover, or Dedication's colours)."""
    return bool(t.get("hand") or t.get("keep"))

_RUN_NAME = r"\d{8}-\d{6}-[0-9a-f]{6}"

_lock = threading.Lock()
_shown: dict | None = None            # the dropped demo book — one at a time (memory only: a restart forgets it)
_run_stop = threading.Event()         # «Зупинити» of the run going now (runs are exclusive: one at a time)
_results: dict[str, list[Path]] = {}  # job id -> the pictures it saved (the page shows them; nothing else is served)


# ---------------------------------------------------------------- where the templates and Photoshop are

def _saved_or_runtime(saved: str | None, runtime_name: str, default: Path) -> Path:
    """In the portable copy the program's own `runtime/` folder; else a place remembered in the settings, else the default."""
    return portable.runtime(runtime_name) or (portable.relocate(saved) if saved else default)


def places() -> dict:
    saved = core.read_json(PLACES, {}) or {}
    return {"templates": _saved_or_runtime(saved.get("templates"), "Templates", TEMPLATES_DIR),
            "photoshop": _saved_or_runtime(saved.get("photoshop"), "Photoshop", PHOTOSHOP_DIR),
            "lastOut": saved.get("lastOut") or "", "lastZip": saved.get("lastZip") or ""}


def _remember(**values: str) -> None:
    with _lock:
        saved = core.read_json(PLACES, {}) or {}
        saved.update(values)
        core.write_json(PLACES, saved)


def find_photoshop(base: Path) -> dict | None:
    """Photoshop.exe and the portable launcher (Photoshoр.exe — the "р" is Cyrillic, so it is looked up by a
    mask). The launcher keeps the portable copy's settings off drive C, so a cold start goes through it."""
    for root in (base / "Portable Adobe Photoshop", base):
        exe = root / "App" / "Photoshop" / "Photoshop.exe"
        if exe.is_file():
            launcher = next((p for p in sorted(root.glob("Photosho*.exe")) if p.is_file()), None)
            return {"exe": exe, "launcher": launcher or exe}
    exe = base / "Photoshop.exe"
    return {"exe": exe, "launcher": exe} if exe.is_file() else None


# ---------------------------------------------------------------- the dropped demo book

def read_book(folder: Path) -> dict:
    """The demo book in a dropped Canva export: the wide cover and pages 1..N (renumbered in order, like the
    print folder). Page 1 is the dedication, then spreads [2|3], [4|5], …"""
    global _shown
    cover, numbered = drops.export_files(folder, core.IMAGE_EXTS)
    pages = {i: p for i, (_, p) in enumerate(numbered, 1)}
    if len(pages) < 3:
        raise ApiError("Замало сторінок: потрібні присвята й хоча б один розворот.")
    book = {"id": core.new_id()[:16], "name": folder.name, "folder": folder, "cover": cover, "pages": pages}
    with _lock:
        _shown = book  # a run of the one before keeps its own copy of it
    return book


def book_view(book: dict) -> dict:
    count = len(book["pages"])
    try:
        info = images.image_info(book["cover"])
        cover = [info["width"], info["height"]]
    except Exception:
        cover = None
    return {"id": book["id"], "name": book["name"], "pageCount": count, "cover": cover,
            "spreads": [[n, n + 1] for n in range(2, count, 2)]}


def _book(book_id: str) -> dict:
    with _lock:
        book = _shown if _shown and _shown["id"] == str(book_id or "") else None
    if not book:
        raise ApiError("Книгу не знайдено — перетягніть архів ще раз.", 404)
    return book


def _only_this_book(book: dict) -> None:
    """One demo book at a time (read_book() puts it in the one slot): the unpacked copy of the one before goes at once
    (a 4K book is ~200 MB), not only at the next launch. Never while a run still reads its pictures. Only the
    mockups' own folder is touched — the files dropped into an order's card stay."""
    if jobs.running("mockups"):
        return
    try:
        own = Path(book["folder"]).resolve().relative_to(BOOKS.resolve()).parts[0]
    except (ValueError, IndexError):
        return
    clear_books(keep=own)


def clear_books(keep: str = "") -> None:
    """The unpacked demo books go (on launch, when Book Studio closes, when another book comes in)."""
    if not BOOKS.is_dir():
        return
    for entry in BOOKS.iterdir():
        if entry.name != keep:
            shutil.rmtree(entry, ignore_errors=True) if entry.is_dir() else entry.unlink(missing_ok=True)


def _take_dropped(folder: Path) -> Path:
    """A demo book dropped into the window arrives among the files dropped for orders (drops.DROPS/<session>):
    its session moves into the mockups' own folder (the same drive — at once), so the cleaning of one never
    reaches the other."""
    session = folder.resolve().relative_to(drops.DROPS.resolve()).parts[0]
    target = BOOKS / session
    BOOKS.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(target, ignore_errors=True)
    shutil.move(str(drops.DROPS / session), str(target))
    return target / folder.resolve().relative_to((drops.DROPS / session).resolve())


# ---------------------------------------------------------------- pictures for the smart objects

def _rgb(im: Image.Image) -> Image.Image:
    return images.flat_rgb(ImageOps.exif_transpose(im))


def _fill(im: Image.Image, size: tuple[int, int], centre: tuple[float, float] | None = None,
          scale: float | None = None) -> Image.Image:
    """`size` cut from `im` around `centre`, the picture scaled to fill it (the edges that do not fit go)."""
    w, h = im.size
    cx, cy = centre or (w / 2, h / 2)
    scale = scale or max(size[0] / w, size[1] / h)
    cw, ch = size[0] / scale, size[1] / scale
    x0 = min(max(cx - cw / 2, 0), max(w - cw, 0))
    y0 = min(max(cy - ch / 2, 0), max(h - ch, 0))
    return im.resize(size, Image.Resampling.LANCZOS, box=(x0, y0, x0 + min(cw, w), y0 + min(ch, h)))


def page_picture(path: Path, size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as im:
        return _fill(_rgb(im), size)


def cover_pictures(path: Path, size: dict) -> dict[str, Image.Image]:
    """From the wide Canva cover (back on the left, front on the right): the back — its left half, the front —
    its right half, each scaled to fill its board and centred; the spine — the strip from the exact middle, at
    the halves' scale (what the owner did by hand)."""
    with Image.open(path) as im:
        im = _rgb(im)
        w, h = im.size
        bw, bh = size["board"]
        scale = max(bw / (w / 2), bh / h)
        return {"back": _fill(im.crop((0, 0, w // 2, h)), size["board"], scale=scale),
                "front": _fill(im.crop((w - w // 2, 0, w, h)), size["board"], scale=scale),
                "spine": _fill(im, size["spine"], centre=(w / 2, h / 2), scale=scale)}


def _save_png(im: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "PNG", dpi=(DPI, DPI), compress_level=1)  # read once by Photoshop: speed over size


# ---------------------------------------------------------------- one run

def _free_name(out: Path, name: str, taken: set[str]) -> Path:
    """A file name in `out` that is neither there already nor planned: an earlier picture is never overwritten."""
    stem, suffix = name[: -len(".png")], ".png"
    candidate, n = name, 1
    while candidate.lower() in taken or (out / candidate).exists():
        n += 1
        candidate = f"{stem} ({n}){suffix}"
    taken.add(candidate.lower())
    return out / candidate


def selected(only) -> list[dict]:
    """The templates a run covers: all of them, or only the ones asked for (a single one — «Зробити лише цей»,
    09.10.2026: a slide not made right is redone without Photoshop redrawing everything). In the page's order."""
    if only is None:
        return list(TEMPLATES)
    keys = [only] if isinstance(only, str) else only
    if not isinstance(keys, (list, tuple)) or not keys or any(k not in {t["key"] for t in TEMPLATES} for k in keys):
        raise ApiError("Невідомий шаблон мокапів.")
    return [t for t in TEMPLATES if t["key"] in keys]


def plan(book: dict, picks: dict, out: Path, run: Path, templates_dir: Path, only=None) -> dict:
    """Everything a run does, decided before anything is written: the pictures to make, the template copies,
    what goes into which layer, and the file each picture is saved as. `only` — the templates to make (all when None)."""
    starts = {n for n in range(2, len(book["pages"]), 2)}
    wanted = selected(only)
    for t in wanted:
        chosen = picks.get(t["key"]) or []
        if len(chosen) != t["slots"] or any(not isinstance(n, int) or n not in starts for n in chosen):
            raise ApiError(f"Оберіть {t['slots']} розвороти для «{t['label']}»." if t["slots"] > 1
                           else f"Оберіть розворот для «{t['label']}».")
    pictures: dict[str, tuple] = {}

    def picture(what: str, size: dict, page: int | None = None) -> str:
        kind = "hard" if size is HARD else "soft"
        name = f"{kind}-{what}{'-' + str(page) if page else ''}.png"
        pictures[name] = (what, kind, page)
        return (run / "pictures" / name).as_posix()

    taken: set[str] = set()
    steps = []
    by_key = {t["key"]: t for t in TEMPLATES}
    for key in (k for k in RUN_ORDER if by_key[k] in wanted):
        t = by_key[key]
        stem, layers, size = Path(t["file"]).stem, t["layers"], t["size"]
        fills = [{"layer": list(layers[role]), "image": picture(role, size)}
                 for role in ("front", "back", "spine") if role in layers]
        if "page1" in layers:
            fills.append({"layer": list(layers["page1"]), "image": picture("page", size, 1)})
        shots = []
        for n in picks.get(key) or []:
            pages = [{"layer": list(layers["left"]), "image": picture("page", size, n)},
                     {"layer": list(layers["right"]), "image": picture("page", size, n + 1)}]
            if kept_open(t):
                fills += pages  # its one spread stays in the document the owner finishes
            else:
                shots.append({"fills": pages, "title": f"{t['label']} · {n}–{n + 1}",
                              "save": _free_name(out, f"{stem} ({n}-{n + 1}).png", taken).as_posix()})
        steps.append({"key": key, "name": stem, "title": t["label"], "source": str(templates_dir / t["file"]),
                      "file": (run / "templates" / t["file"]).as_posix(), "keepOpen": kept_open(t),
                      # the spread a template left open holds: its picture is named by it when saved later
                      "spread": (picks.get(key) or [None])[0] if kept_open(t) else None,
                      "fills": fills, "shots": shots})
    # The book's cover as Canva exported it, opened in Photoshop beside the templates left open: the owner fits the
    # front cover from it (26.09.2026: "open the Cover image too, so I can work with it at once"). A copy in the run's
    # folder — the demo book's own folder goes when another book comes in.
    source = book.get("cover") if any(s["keepOpen"] for s in steps) else None   # nothing left open — no cover to fit
    cover = (run / f"Cover{Path(source).suffix.lower()}").as_posix() if source else None
    return {"run": str(run), "out": str(out), "pictures": pictures, "templates": steps,
            "cover": cover, "coverSource": str(source) if source else None,
            "status": (run / "status.json").as_posix(), "cancel": (run / "cancel").as_posix()}


def prepare(job: Job, book: dict, work: dict) -> None:
    run = Path(work["run"])
    wanted = sorted(work["pictures"].items())
    covers = {kind: cover_pictures(book["cover"], HARD if kind == "hard" else SOFT)
              for kind in sorted({kind for what, kind, _ in work["pictures"].values() if what != "page"})}

    def make(item) -> None:
        name, (what, kind, page) = item
        im = page_picture(book["pages"][page], (HARD if kind == "hard" else SOFT)["page"]) if what == "page" else covers[kind][what]
        _save_png(im, run / "pictures" / name)

    # Four pictures at a time: each is a full read, a resize and a save (04.10.2026).
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(4) as pool:
        for i, _ in enumerate(pool.map(make, wanted), 1):
            job.progress("Готую картинки", 8 * i / max(1, len(wanted)))
    if work.get("cover"):
        try:
            shutil.copyfile(work["coverSource"], work["cover"])
        except OSError as err:  # the mockups still go on; only the cover isn't opened for the owner
            core.log.warning("Mockups: the cover was not copied for Photoshop: %s", err)
            work["cover"] = None


def copy_templates(job: Job, work: dict) -> None:
    """The run's own copies: Photoshop never opens a template itself, so even a stray Ctrl+S cannot touch one."""
    total = sum(Path(t["source"]).stat().st_size for t in work["templates"]) or 1
    done = 0
    for t in work["templates"]:
        src, dst = Path(t["source"]), Path(t["file"])
        if core.inside(dst, src.parent, or_same=True):
            raise UserError("Копія шаблону не може лежати в папці з трафаретами.")
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(src, "rb") as a, open(dst, "wb") as b:
            while chunk := a.read(16 * 1024 * 1024):
                b.write(chunk)
                done += len(chunk)
                job.progress("Копіюю шаблони", 8 + 17 * done / total)


SCRIPT = Path(__file__).with_name("mockups.jsx")


def script(work: dict) -> str:
    """The job as a JavaScript literal (ASCII only: a Cyrillic folder name travels as \\u escapes) in front of
    the fixed script. Only copies, the prepared pictures and the output files are named in it."""
    job = {"status": work["status"], "cancel": work["cancel"], "compression": PNG_COMPRESSION,
           "finish": bool(work.get("finish")), "cover": work.get("cover") or None,
           "templates": [{k: t[k] for k in ("name", "title", "file", "keepOpen", "fills", "shots")}
                         for t in work["templates"]]}
    return f"var JOB = {json.dumps(job, ensure_ascii=True, indent=1)};\n\n" + SCRIPT.read_text(encoding="utf-8")


def finish_plan(run: Path) -> dict:
    """«Зберегти відкриті»: the templates a run left open, now with the front cover the owner fitted, are saved
    as PNG into the same folder (named like the others) and closed; the script finds them among Photoshop's
    open documents by their copy's path."""
    work = core.read_json(run / "job.json", None)
    if not isinstance(work, dict):
        raise UserError("Цей запуск уже прибрано — збережіть шаблони в Photoshop самі.")
    out = Path(work["out"])
    if not out.is_dir():
        raise UserError("Папку для мокапів не знайдено.")
    taken: set[str] = set()
    docs = []
    for t in work["templates"]:
        if not t.get("keepOpen") or not Path(t["file"]).is_file():
            continue
        n = t.get("spread")
        name = f"{t['name']} ({n}-{n + 1}).png" if n else f"{t['name']}.png"
        docs.append({"key": t["key"], "name": t["name"], "title": t["title"], "file": t["file"], "keepOpen": False,
                     "span": 1, "fills": [],
                     "shots": [{"title": t["title"], "fills": [], "save": _free_name(out, name, taken).as_posix()}]})
    if not docs:
        raise UserError("Відкритих шаблонів цього запуску вже немає.")
    cover = work.get("cover") if work.get("cover") and Path(work["cover"]).is_file() else None
    return {"run": str(run), "out": str(out), "finish": True, "templates": docs, "pictures": {}, "cover": cover,
            "status": (run / "finish-status.json").as_posix(), "cancel": (run / "finish-cancel").as_posix()}


def _tasklist() -> str:
    try:
        return subprocess.run(["tasklist", "/FI", "IMAGENAME eq Photoshop.exe", "/NH", "/FO", "CSV"],
                              capture_output=True, text=True, errors="replace", timeout=15,
                              creationflags=desktop.CREATE_NO_WINDOW).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def running() -> bool:
    return "photoshop.exe" in _tasklist().lower()


def launch(script_path: Path) -> None:
    """Hands the script to Photoshop: a running one gets it through Photoshop.exe, a closed one is started with
    it through the portable launcher. Photoshop asks "run this script?" once — the owner answers."""
    ps = find_photoshop(places()["photoshop"])
    if not ps:
        raise UserError("Не знайшов Photoshop.")
    exe = ps["exe"] if running() else ps["launcher"]
    # Windows' temp folder is on drive C, which the owner keeps clean: a Photoshop this starts gets one on D
    # (emptied by clean_runs() once Photoshop is closed; the portable launcher keeps its own there too).
    PHOTOSHOP_TEMP.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "TEMP": str(PHOTOSHOP_TEMP), "TMP": str(PHOTOSHOP_TEMP)}
    subprocess.Popen([str(exe), str(script_path)], cwd=str(Path(exe).parent), close_fds=True, env=env)


def _status(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None  # not there yet, or caught half-written
    return data if isinstance(data, dict) else None


def progress_view(work: dict, st: dict | None, phase: str) -> dict:
    """What the page lists while Photoshop works: every template — waiting, in work or done — with the pictures
    it has saved so far. The script counts one step for filling a template and one per picture."""
    step = int((st or {}).get("step") or 0)
    saved = {str(p) for p in (st or {}).get("saved") or []}
    rows, at, current = [], 0, False
    for t in work["templates"]:
        span = t.get("span") or 1 + len(t["shots"])
        if st and step >= at + span:
            state = "done"
        elif st and not current and phase == "work":
            state, current = "work", True
        else:
            state = "wait"
        rows.append({"key": t["key"], "title": t["title"], "state": state, "keepOpen": t["keepOpen"],
                     "shots": len(t["shots"]), "saved": sum(s["save"] in saved for s in t["shots"])})
        at += span
    return {"mode": "finish" if work.get("finish") else "make", "phase": phase, "rows": rows,
            "saved": [Path(p).name for p in (st or {}).get("saved") or []]}


def watch(job: Job, work: dict, cancel: threading.Event, clock=time.monotonic, pause=time.sleep) -> dict:
    """Follows the script through its status file until it has finished (or was stopped)."""
    status_file, cancel_file = Path(work["status"]), Path(work["cancel"])
    started, seen, gone, checked, stopped = clock(), None, 0, clock(), None
    handed: set[str] = set()   # the pictures already given to the slides' cutter
    while True:
        if cancel.is_set() and not cancel_file.exists():
            cancel_file.write_text("stop", encoding="utf-8")  # a script that starts late stops at once too
            stopped = clock()
            if seen is None:
                raise UserError("Скасовано.")
        if stopped is not None and clock() - stopped > 120:
            raise UserError("Скасовано, але Photoshop ще не відповів — погляньте на його вікно.")
        st = _status(status_file)
        if st:
            seen = st
            _cut_without_background(work, st, handed)
            state = st.get("state")
            job.share(progress_view(work, st, "work"))
            if state in ("done", "cancelled"):
                return st
            if state == "error":
                raise UserError(f"Скрипт у Photoshop зупинився: {st.get('detail') or 'невідома помилка'}")
            total = max(1, int(st.get("total") or 1))
            job.progress(st.get("title") or "Photoshop", 25 + 75 * int(st.get("step") or 0) / total)
        elif clock() - started > START_WAIT:
            cancel_file.write_text("stop", encoding="utf-8")
            raise UserError("Photoshop так і не запустив скрипт. Можливо, на запитання про скрипт відповіли «No».")
        else:
            job.share(progress_view(work, None, "ask"))
            job.progress("Photoshop питає про скрипт — натисніть «Yes»", 25)
        if clock() - checked >= 5:
            checked = clock()
            gone = 0 if running() else gone + 1
            if gone >= GONE_CHECKS and (seen is not None or clock() - started > 60):
                raise UserError("Photoshop закрився, не закінчивши мокапи.")
        pause(0.5)


def _cut_without_background(work: dict, st: dict, handed: set[str]) -> None:
    """Every picture Photoshop has saved goes to the slides' cutter at once: the book without its background lands in
    «Без фону» beside it while Photoshop works on the next ones (the owner, 29.09.2026: "the Mockups must also save
    the pictures without background, fit for the listing templates"). Only Open 1, Open 2 and Cover 1 can be cut."""
    for saved in st.get("saved") or []:
        if saved in handed:
            continue
        handed.add(saved)
        t = next((t for t in work["templates"] if any(s.get("save") == saved for s in t.get("shots") or [])
                  or t.get("save") == saved), None) or (work["templates"][0] if work["templates"] else None)
        source = Path(str((t or {}).get("source") or ""))
        try:
            slide_cutout.cutter.add(Path(saved), source.parent if source.name else places()["templates"])
        except Exception:
            core.log.warning("Mockups: %s not handed to the cutter", saved, exc_info=True)


def _problem_text(p: dict) -> str:
    where = f"«{p.get('template') or '?'}»"
    detail = f": {p['detail']}" if p.get("detail") else ""
    kind = p.get("kind")
    if kind == "open":
        return f"{where} не відкрився{detail}"
    if kind == "closed":
        return f"{where} уже не відкритий у Photoshop — його не збережено"
    if kind == "layer":
        return f"У {where} немає смарт-об'єкта «{p.get('layer')}»"
    if kind == "save":
        return f"«{Path(str(p.get('file') or '')).name}» не збережено{detail}"
    return f"{where}: не вдалося замінити «{p.get('layer')}»{detail}"


def _saved_by_owner(run: Path) -> bool:
    """A template copy changed after the run wrote its job: the owner pressed Ctrl+S on it in Photoshop."""
    try:
        written = (run / "job.json").stat().st_mtime
        return any(p.stat().st_mtime > written + 2 for p in (run / "templates").glob("*.psd"))
    except OSError:
        return False


def clean_runs(keep: str = "", older_than: float = KEEP_RUNS) -> int:
    """Earlier runs go once nothing can need them: at once when Photoshop is closed (it has none of their copies
    open any more), else after a day. A copy the owner saved himself stays a week. On launch, before every run
    and when the window closes; the temp folder of a Photoshop started from here goes with Photoshop closed.
    Returns how many runs went."""
    closed = not running()
    if closed:
        shutil.rmtree(PHOTOSHOP_TEMP, ignore_errors=True)
    runs = [r for r in WORK.iterdir() if r.name != keep] if WORK.is_dir() else []
    now, removed = time.time(), 0
    for run in runs:
        try:
            limit = KEEP_SAVED if _saved_by_owner(run) else 0 if closed else older_than
            if now - run.stat().st_mtime >= limit:
                shutil.rmtree(run, ignore_errors=True)
                removed += 1
        except OSError:
            pass
    return removed


def make(job: Job, book: dict, picks: dict, out: Path, cancel: threading.Event, only=None) -> dict:
    where = places()
    ps = find_photoshop(where["photoshop"])
    if not ps:
        raise UserError("Не знайшов Photoshop — вкажіть його папку.")
    missing = [t["file"] for t in selected(only) if not (where["templates"] / t["file"]).is_file()]
    if missing:
        raise UserError(f"У папці з трафаретами немає: {', '.join(missing)}.")
    if not out.is_dir():
        raise UserError("Папку для мокапів не знайдено.")
    if core.inside(out, where["templates"], or_same=True):
        raise UserError("Це папка з трафаретами — у ній нічого не можна змінювати. Оберіть іншу.")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    run = WORK / f"{stamp}-{core.new_id()[:6]}"
    clean_runs(keep=run.name)
    work = plan(book, picks, out, run, where["templates"], only)
    job.share(progress_view(work, None, "prepare"))
    started = time.time()
    prepare(job, book, work)
    copy_templates(job, work)
    try:
        st = _run_script(job, work, run / "mockups.jsx", run / "job.json", "Запускаю Photoshop", cancel)
    finally:
        # The pictures Photoshop saved are in the owner's folder; the copies it closed are no use any more, and
        # neither are the prepared pictures once the script has finished (the smart objects hold them now).
        last = _status(Path(work["status"]))
        if last:
            for t in work["templates"]:
                if not t["keepOpen"]:
                    Path(t["file"]).unlink(missing_ok=True)
        if last and last.get("state") in ("done", "cancelled", "error"):
            shutil.rmtree(run / "pictures", ignore_errors=True)
    saved = [Path(p) for p in st.get("saved") or []]
    _results[job.id] = saved
    names = set(st.get("opened") or [])
    opened = [t["title"] for t in work["templates"] if t["name"] in names]
    return {"folder": str(out), "saved": [p.name for p in saved], "open": opened,
            "coverOpen": bool(st.get("coverOpened")),
            "run": run.name if opened else "", "cancelled": st.get("state") == "cancelled",
            "seconds": round(time.time() - started), "problems": _problems(st)}


def _run_script(job: Job, work: dict, jsx: Path, js: Path, step: str, cancel: threading.Event) -> dict:
    """The run's script written (with the same job as JSON — readable, for a look when something fails), started in
    Photoshop and followed to its end: its last status."""
    jsx.write_text(script(work), encoding="ascii")
    core.write_json(js, work, backup=False)
    if cancel.is_set():
        raise UserError("Скасовано.")
    job.progress(step, 25)
    launch(jsx)
    return watch(job, work, cancel)


def _problems(st: dict) -> list[str]:
    # one missing layer fails every picture of its template: said once
    return list(dict.fromkeys(_problem_text(p) for p in st.get("problems") or [] if isinstance(p, dict)))


def finish(job: Job, run_name: str, cancel: threading.Event) -> dict:
    """Saves the templates a run left open (the owner has fitted the front cover) and closes them; their copies
    — the last of the run's files — go right after."""
    run = WORK / run_name
    if not running():
        raise UserError("Photoshop закрито — відкритих шаблонів уже немає.")
    work = finish_plan(run)
    job.share(progress_view(work, None, "prepare"))
    started = time.time()
    for leftover in (work["status"], work["cancel"]):  # an earlier try's status must not read as this one's
        Path(leftover).unlink(missing_ok=True)
    st = _run_script(job, work, run / "finish.jsx", run / "finish.json", "Запускаю скрипт у Photoshop", cancel)
    closed = set(st.get("closed") or [])
    for t in work["templates"]:
        if t["name"] in closed:
            Path(t["file"]).unlink(missing_ok=True)
    if not any((run / "templates").glob("*.psd")):
        shutil.rmtree(run, ignore_errors=True)
    saved = [Path(p) for p in st.get("saved") or []]
    _results[job.id] = saved
    return {"folder": work["out"], "saved": [p.name for p in saved], "cleaned": not run.exists(),
            "cancelled": st.get("state") == "cancelled", "seconds": round(time.time() - started),
            "problems": _problems(st)}


def pending() -> dict | None:
    """The newest run whose templates are still waiting for the owner's front cover (their copies are there):
    after a reload of the window «Зберегти відкриті» is offered again."""
    runs = sorted((p for p in WORK.glob("*") if p.is_dir() and re.fullmatch(_RUN_NAME, p.name)), reverse=True) \
        if WORK.is_dir() else []
    if not runs:
        return None
    run = runs[0]
    if (run / DISMISSED).exists():
        return None
    st, work = _status(run / "status.json"), core.read_json(run / "job.json", None)
    if not st or st.get("state") != "done" or not isinstance(work, dict):
        return None
    left = [t["title"] for t in work.get("templates") or [] if t.get("keepOpen") and Path(t["file"]).is_file()]
    return {"run": run.name, "folder": work.get("out"), "open": left, "cover": bool(st.get("coverOpened"))} if left else None


# ---------------------------------------------------------------- routes

def state() -> dict:
    where = places()
    ps = find_photoshop(where["photoshop"])
    busy = jobs.running("mockups")
    return {
        "templates": [{"key": t["key"], "label": t["label"], "file": t["file"], "slots": t["slots"],
                       "hand": bool(t.get("hand")), "keep": t.get("keep") or "",
                       "found": (where["templates"] / t["file"]).is_file()}
                      for t in TEMPLATES],
        "templatesDir": str(where["templates"]), "templatesFound": where["templates"].is_dir(),
        "photoshopDir": str(where["photoshop"]), "photoshopFound": bool(ps),
        "jobId": busy.id if busy else None, "lastOut": where["lastOut"], "books": _workshop_books(),
        "pending": None if busy else pending(),
    }


def _workshop_books() -> list[dict]:
    """The Workshop's books, newest first: the mockups go into the chosen one's folder, no question asked (the owner,
    29.09.2026: "save the mockups into the book's folder where the Workshop works, and don't ask where")."""
    from .workshop.books import book_ids, display_name
    return [{"id": b, "name": display_name(b)} for b in reversed(book_ids())]


@route("GET", "/api/mockups/state")
def _state(req: Request):
    return state()


def _template_of(name: str) -> str | None:
    """The template a saved mockup came from, by its name: «2. Open 1 (6-7).png» → open1, «4. Dedication (2).png» →
    dedication; None for anything else in the folder (canva-cover.png)."""
    stem = re.sub(r"(\s*\([\d\s-]+\))+$", "", Path(name).stem).strip().lower()
    return next((t["key"] for t in TEMPLATES if t["file"][:-4].lower() == stem), None)


def existing(workshop: str) -> dict:
    """What a Workshop book already has in its folder — mockups made another day or by an earlier run, its slides: the
    page shows them and its step 4 makes the listing slides from them, whatever this session ran (the owner,
    11.10.2026: "the mockups are made, but the program says there are none"; "I redo one mockup — the whole session
    goes and I can't get to the next step")."""
    from .slides import store as slide_store, work as slide_work
    folder = slide_store.book_folder(workshop) / "mockups"
    rank = {t["key"]: i for i, t in enumerate(TEMPLATES)}
    files = []
    for p in folder.glob("*.png") if folder.is_dir() else []:
        key = _template_of(p.name)
        if key and p.is_file():
            files.append({"name": p.name, "template": key, "v": p.stat().st_mtime_ns})
    files.sort(key=lambda f: (rank[f["template"]], slide_cutout.spread_of(f["name"]), f["name"].lower()))
    slides = None
    if (slide_store.set_dir(workshop) / "set.json").is_file():
        try:
            rec = slide_store.read_set(workshop)
            pictures = slide_work.pictures(rec)
            slides = {"set": workshop, "folder": str(slide_store.out_dir(rec)), "pictures": pictures,
                      "numbers": rec.get("numbers") or {}, "todo": slide_work.not_baked(rec, pictures)}
        except Exception:
            core.log.warning("Mockups: the slides of %s not read", workshop, exc_info=True)
    return {"folder": str(folder), "files": files, "slides": slides}


def _existing_file(workshop: str, name: str) -> Path:
    from .slides import store as slide_store
    folder = slide_store.book_folder(workshop) / "mockups"
    path = folder / name
    if not name or Path(name).name != name or not name.lower().endswith(".png") or not _template_of(name) \
            or not path.is_file():
        raise ApiError("Не знайдено.", 404)
    return path


@route("GET", "/api/mockups/existing")
def _existing(req: Request):
    return existing(str(req.param("workshop") or ""))


@route("GET", "/media/mockups/existing", auth="media")
def _existing_media(req: Request):
    path = _existing_file(str(req.param("workshop") or ""), str(req.param("name") or ""))
    return file_response(images.preview(path, req.int_param("w", 480, 64, 4096)), "image/jpeg", cache="private, max-age=600")


@route("POST", "/api/mockups/open-existing")
def _open_existing(req: Request):
    body = req.json or {}
    desktop.open_image_file(_existing_file(str(body.get("workshop") or ""), str(body.get("name") or "")))
    return {"ok": True}


@route("POST", "/api/mockups/book")
def _open_book(req: Request):
    folder = Path(str((req.json or {}).get("path") or ""))
    if not core.inside(folder, drops.DROPS) or not folder.is_dir():
        raise ApiError("Перетягніть ZIP-архів із Canva у вікно.")
    moved = _take_dropped(folder)
    try:
        return _opened(read_book(moved))
    except Exception:
        shutil.rmtree(BOOKS / moved.relative_to(BOOKS).parts[0], ignore_errors=True)  # not a book: nothing kept
        raise


def _opened(book: dict) -> dict:
    _only_this_book(book)
    view = book_view(book)
    core.log.info("Mockups: book «%s», %d pages, %d spreads", view["name"], view["pageCount"], len(view["spreads"]))
    return view


@route("POST", "/api/mockups/pick-zip")
def _pick_zip(req: Request):
    """The folder button of the book field: Canva's ZIP picked in the Windows dialog (the Downloads folder the
    first time, then wherever the last one was)."""
    core.log.info("Mockups: the ZIP dialog is open")
    path = desktop.pick_zip("Демо-книга з Canva (ZIP)", places()["lastZip"] or desktop.downloads_folder())
    core.log.info("Mockups: the ZIP dialog closed: %s", path or "nothing picked")
    if path:
        _remember(lastZip=str(Path(path).parent))
    return {"path": path}


@route("POST", "/api/mockups/open-zip")
def _open_zip(req: Request):
    """The picked ZIP is unpacked right from where it lies (nothing goes through the window) — only read."""
    archive = Path(str((req.json or {}).get("path") or ""))
    if archive.suffix.lower() != ".zip" or not archive.is_file():
        raise ApiError("Оберіть ZIP-архів із Canva.")
    if jobs.running("mockups"):
        raise ApiError("Зачекайте, поки Photoshop закінчить.")
    root = BOOKS / core.new_id()
    try:
        drops.extract_zip(archive, root / drops.archive_folder(archive.name))
        return _opened(read_book(drops.dropped_folder(root)))
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise


@route("POST", "/api/mockups/place")
def _place(req: Request):
    what = (req.json or {}).get("what")
    if what not in ("templates", "photoshop"):
        raise ApiError("Некоректний запит.")
    title = "Папка з трафаретами мокапів" if what == "templates" else "Папка з Photoshop"
    path = desktop.pick_folder(title, str(places()[what]))
    if path:
        _remember(**{what: path})
    return state()


@route("POST", "/api/mockups/pick-folder")
def _pick_out(req: Request):
    core.log.info("Mockups: the folder dialog is open")
    path = desktop.pick_folder("Куди зберегти мокапи", places()["lastOut"])
    core.log.info("Mockups: the folder dialog closed: %s", path or "no folder picked")
    if path and core.inside(Path(path), places()["templates"], or_same=True):
        raise ApiError("Це папка з трафаретами — у ній нічого не можна змінювати. Оберіть іншу.")
    return {"path": path}


@route("POST", "/api/mockups/make")
def _make(req: Request):
    global _run_stop
    body = req.json or {}
    book = _book(body.get("book"))
    picks = body.get("picks") if isinstance(body.get("picks"), dict) else {}
    workshop = str(body.get("workshop") or "")
    if workshop:
        from .slides import store as slide_store
        out = slide_store.mockups_dir(workshop)       # the Workshop book's own folder (refused unless it is one)
    else:
        out = Path(str(body.get("folder") or ""))
        if not str(body.get("folder") or "") or not out.is_dir():
            raise ApiError("Оберіть папку для мокапів.")
    only = body.get("only") or None                  # a list of template keys: make just these (None — all)
    plan(book, picks, out, WORK / "check", places()["templates"], only)  # a wrong pick is said at once, not in the job
    if workshop:
        _keep_canva_cover(workshop, book)
    else:
        _remember(lastOut=str(out))
    cancel = threading.Event()
    core.log.info("Mockups: a run for «%s» into %s, spreads %s, templates %s", book["name"], out, picks,
                  only or "all")
    job = jobs.start("mockups", lambda j: _to_etsy(_ticked(_logged(make, j, book, picks, out, cancel, only), workshop,
                                                          whole=not only)), exclusive="mockups")
    _run_stop = cancel
    return {"jobId": job.id}


@route("POST", "/api/mockups/finish")
def _finish(req: Request):
    global _run_stop
    run = str((req.json or {}).get("run") or "")
    if not re.fullmatch(_RUN_NAME, run):
        raise ApiError("Некоректний запит.")
    cancel = threading.Event()
    core.log.info("Mockups: saving the templates run %s left open", run)
    job = jobs.start("mockups", lambda j: _to_etsy(_logged(finish, j, run, cancel)), exclusive="mockups")
    _run_stop = cancel
    return {"jobId": job.id}


def _to_etsy(result: dict) -> dict:
    """Mockups saved into a Workshop book's mockups/: its whole-scene ones (Cover & Open 1, All & Open 1) are copied
    into the book's etsy/ too — they go into the listing as they are (the owner, 30.09.2026)."""
    folder = Path(str(result.get("folder") or ""))
    try:
        if folder.name == "mockups" and folder.parent.parent.resolve() == core.WORKSHOP_BOOKS.resolve():
            from . import photos
            copied = photos.scenes_to_etsy(folder.parent)
            if copied:
                core.log.info("Mockups: into %s/etsy: %s", folder.parent.name, ", ".join(copied))
    except Exception:
        core.log.warning("Mockups: the whole-scene mockups not copied into etsy/", exc_info=True)
    return result


def _keep_canva_cover(workshop: str, book: dict) -> None:
    """The demo book's flat cover, as Canva exported it, into the Workshop book's mockups/ as canva-cover.* — the
    photo mockups' reference for the grandmother (the owner, 30.09.2026: "the Cover picture from the Canva ZIP")."""
    cover = book.get("cover")
    if not cover:
        return
    try:
        from . import photos
        from .workshop.books import book_path
        photos.set_canva_cover(book_path(workshop), Path(cover), Path(cover).name)
    except Exception:
        core.log.warning("Mockups: the Canva cover of %s not kept", workshop, exc_info=True)


def _ticked(result: dict, workshop: str, whole: bool = True) -> dict:
    """The Workshop book's «Мокапи» step ticks itself once its mockups are saved (the owner, 29.09.2026) — not after a
    run of some templates only (`whole`): it is the owner's touch-up, not the book's mockups."""
    if workshop and whole and result.get("saved"):
        try:
            from .workshop.books import set_mark
            set_mark(workshop, "mockups", True)
        except Exception:
            core.log.warning("Mockups: the Workshop's «Мокапи» step of %s not ticked", workshop, exc_info=True)
    return {**result, "workshop": workshop or None}


def _logged(fn, job: Job, *args):
    """The run's outcome in the log as well (the owner's report is "nothing happens" — the log says what did)."""
    try:
        result = fn(job, *args)
    except Exception as err:
        core.log.warning("Mockups: the run stopped at «%s»: %s", job.step, err)
        raise
    core.log.info("Mockups: done in %ss — %d saved, left open: %s, problems: %s", result.get("seconds"),
                  len(result.get("saved") or []), result.get("open") or "none", result.get("problems") or "none")
    return result


def close(run_name: str = "") -> None:
    """«×» — the owner has finished with this book (26.09.2026): the demo book goes (its unpacked copy too), and a
    run whose templates still wait in Photoshop is not offered again. Photoshop and what is open in it are left as
    they are; the run's copies are cleaned as always (once Photoshop is closed)."""
    global _shown
    if jobs.running("mockups"):
        raise ApiError("Зачекайте, поки Photoshop закінчить, — або зупиніть його.")
    if run_name:
        if not re.fullmatch(_RUN_NAME, run_name):
            raise ApiError("Некоректний запит.")
        if (WORK / run_name).is_dir():
            (WORK / run_name / DISMISSED).write_text("", encoding="utf-8")
    with _lock:
        _shown = None
    clear_books()
    core.log.info("Mockups: finished by the owner%s", f" (run {run_name} no longer offered)" if run_name else "")


@route("POST", "/api/mockups/close")
def _close(req: Request):
    close(str((req.json or {}).get("run") or ""))
    return {"ok": True}


@route("POST", "/api/mockups/cancel")
def _stop(req: Request):
    if jobs.running("mockups"):
        _run_stop.set()
    return {"ok": True}


@route("POST", "/api/mockups/open-folder")
def _open_folder(req: Request):
    path = Path(str((req.json or {}).get("path") or ""))
    if not path.is_dir():
        raise ApiError("Папку не знайдено.")
    desktop.open_in_explorer(path)
    return {"ok": True}


@route("POST", "/api/mockups/open-picture")
def _open_picture(req: Request):
    body = req.json or {}
    files = _results.get(str(body.get("job") or "")) or []
    i = body.get("i")
    if not isinstance(i, int) or not 0 <= i < len(files):
        raise ApiError("Картинку не знайдено.", 404)
    desktop.open_image_file(files[i])
    return {"ok": True}


@route("POST", "/api/mockups/attention")
def _attention(req: Request):
    """The page asks for it when a run finishes while the owner is in Photoshop."""
    return {"ok": desktop.attention(core.APP_NAME)}


@route("GET", r"/media/mockups/template/([a-zA-Z0-9]+)", auth="media")
def _template_media(req: Request):
    """The template's own preview (the picture Photoshop keeps inside the PSD) — the file is only read."""
    t = next((t for t in TEMPLATES if t["key"] == req.groups[0]), None)
    path = places()["templates"] / t["file"] if t else None
    if not path or not path.is_file():
        raise ApiError("Не знайдено.", 404)
    try:
        preview = images.preview(path, req.int_param("w", 320, 64, 4096))
    except Exception:
        raise ApiError("Прев'ю шаблону не читається.", 404) from None
    return file_response(preview, "image/jpeg", cache="private, max-age=600")


@route("GET", r"/media/mockups/out/([0-9a-f]{12})/([0-9]+)", auth="media")
def _out_media(req: Request):
    files = _results.get(req.groups[0]) or []
    i = int(req.groups[1])
    if i >= len(files) or not files[i].is_file():
        raise ApiError("Не знайдено.", 404)
    return file_response(images.preview(files[i], req.int_param("w", 480, 64, 4096)), "image/jpeg", cache="private, max-age=600")


@route("GET", r"/media/mockups/([0-9a-f]{16})/(cover|page|spread)", auth="media")
def _media(req: Request):
    book, what = _book(req.groups[0]), req.groups[1]
    n = req.int_param("n", 0)
    if what == "spread":
        left, right = book["pages"].get(n), book["pages"].get(n + 1)
        if not left:
            raise ApiError("Не знайдено.", 404)
        height = req.int_param("h", 360, 120, 2400)
        return file_response(images.compose_spread(left, right, height), "image/jpeg", cache="private, max-age=600")
    target = book["cover"] if what == "cover" else book["pages"].get(n)
    if not target:
        raise ApiError("Не знайдено.", 404)
    size = req.int_param("w", 480, 64, 4096)
    return file_response(images.preview(target, size), "image/jpeg", cache="private, max-age=600")
