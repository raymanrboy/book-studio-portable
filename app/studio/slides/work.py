"""The slides made for a book: its mockups cut out, a set made from the template, the six baked into the owner's
folder — the Mockups' next step «Зробити слайди» (the owner, 29.09.2026: "after the Photoshop script the Mockups
page offers the next step, the listing slides; I press it and they are made by themselves").
"""
from __future__ import annotations

import re
import time
from pathlib import Path

from PIL import Image

from .. import core
from ..jobs import Job, UserError
from . import bake, cutout, store

TITLES = {  # what the rows say while the six are drawn
    "slide1": "Made just for them", "slide2": "Choose your format", "slide3": "Dedication & afterword",
    "slide4": "Unique little poems", "slide5": "Personalization made simple", "slide6": "Thank you",
    "slide7": "Appearance options",
}


def title(slide: str) -> str:
    try:
        scene, _ = store.load(store.TEMPLATE, slide)
        t = str(scene.get("title") or "")
        return t.split("·", 1)[1].strip() if "·" in t else TITLES[slide]
    except Exception:
        return TITLES[slide]


def mockups_in(folder: Path, order: list[str] | None = None) -> dict[str, list[Path]]:
    """The folder's mockups by kind: open1 / open2 / cover1 / dedication, each in the owner's picks order (the
    Mockups' result lists them so), else by spread."""
    files = [p for p in folder.glob("*.png") if p.is_file() and cutout.kind_of(p.name)]
    rank = {name.lower(): i for i, name in enumerate(order or [])}
    files.sort(key=lambda p: (rank.get(p.name.lower(), 10 ** 6), cutout.spread_of(p.name), p.name.lower()))
    out: dict[str, list[Path]] = {"open1": [], "open2": [], "cover1": [], "dedication": []}
    for p in files:
        out[cutout.kind_of(p.name)].append(p)
    return out


def slots_of(found: dict[str, list[Path]]) -> dict[str, Path]:
    """Which mockup fills which slot of the slides."""
    slots: dict[str, Path] = {}
    for kind, prefix, n in (("open1", "open1", 4), ("open2", "open2", 2)):
        for i, p in enumerate(found[kind][:n]):
            slots[f"{prefix}:{i + 1}"] = p
    if found["cover1"]:
        slots["cover"] = found["cover1"][0]
    return slots


def rows(states: dict[str, str]) -> list[dict]:
    return [{"slide": s, "title": title(s), "state": states.get(s, "wait")} for s in states]


def make(job: Job, folder: Path, name: str, order: list[str] | None, page30: Path | None, numbers: dict,
         templates_dir: Path, base: str, token: str, book: str | None = None, fresh: bool = False,
         scheme: str | None = None, only: list[str] | None = None) -> dict:
    """`book` — the Workshop book the mockups are for: its slides live in its folder, a second time keeps the owner's
    six scenes (only the pictures are new) unless `fresh`; page 30 is the book's own; its «Мокапи» step ticks.
    `only` — the slides to make (09.10.2026: one slide not prepared is redone alone): only their mockups are cut and
    put in, only they are baked, the other slides stay as they were; the «Мокапи» step is not ticked by it."""
    started = time.time()
    if not folder.is_dir():
        raise UserError("Папку з мокапами не знайдено.")
    only = [s for s in store.SLIDES if s in (only or [])] or None
    wanted = {slot for s in (only or store.SLIDES) for slot in store.SLIDE_SLOTS[s]}
    found = mockups_in(folder, order)
    slots = {k: v for k, v in slots_of(found).items() if k in wanted}
    use_dedication = bool(found["dedication"]) and "dedication" in wanted
    if not slots and not (only and use_dedication):
        raise UserError("У папці немає мокапів для цих слайдів — слайдам нема що показати." if only else
                        "У папці немає мокапів Open 1, Open 2 чи Cover 1 — слайдам нема що показати.")
    states: dict[str, str] = {}
    job.share({"phase": "cut", "rows": rows(states)})
    cuts: dict[str, Path] = {}
    todo = list(slots.items()) + ([("dedication", found["dedication"][0])] if use_dedication else [])
    for i, (slot, png) in enumerate(todo):
        job.progress(f"Вирізаю без фону · {i + 1} з {len(todo)}", 40 * i / len(todo))
        while cutout.cutter.status(folder).get(png.name) in ("wait", "work"):   # the background cutter has it
            time.sleep(0.3)
        try:
            cuts[slot] = cutout.ensure(png, templates_dir)
        except Exception as err:
            if slot != "dedication":
                raise
            core.log.warning("Slides: Dedication not cut (%s) — used whole", err)
    job.progress("Складаю слайди", 42)
    rec = store.new_set(name, str(folder), numbers, book=book, fresh=fresh and not only, scheme=scheme,
                        partial=bool(only))
    for slot, cut_folder in cuts.items():
        if slot != "dedication":
            store.put_book(rec, slot, cut_folder, slots[slot].name)
    if "dedication" in cuts:       # the book and the desk, the floor see-through
        with Image.open(cuts["dedication"] / "book.png") as b_, Image.open(cuts["dedication"] / "shadow.png") as s_:
            store.put_picture(rec, "dedication", cutout.combined(b_.convert("RGBA"), s_.convert("RGBA")),
                              name=found["dedication"][0].name, cut=True)
    elif use_dedication:
        store.put_picture(rec, "dedication", found["dedication"][0])
    page30 = page30 if page30 and page30.is_file() else _book_page30(book)
    if page30 and "page30" in wanted:
        store.put_picture(rec, "page30", page30)
    if book and (not only or "slide7" in only):
        put_heroes(rec, book)
    store.write_set(rec)
    store.forget_old_sets()
    shown = [s for s in store.shown(rec["id"], rec) if not only or s in only]
    baked = bake_set(job, rec, shown, base, token, states)
    if book and not only:
        _tick(book)
    missing = [store.SLOT_LABEL[s] for s in store.BOOK_SLOTS + store.PICTURE_SLOTS
               if s in wanted and s not in rec["books"] and s not in rec["pictures"]]
    return {"set": rec["id"], "folder": str(store.out_dir(rec)), "pictures": baked, "missing": missing,
            "seconds": round(time.time() - started)}


def _book_page30(book: str | None) -> Path | None:
    """The Workshop book's own page 30 (its pictures/ folder), when the demo book isn't at hand."""
    if not book:
        return None
    try:
        pictures = store.book_folder(book) / "pictures"
    except Exception:
        return None
    return next((p for p in sorted(pictures.glob("30.*")) if p.suffix.lower() in core.IMAGE_EXTS), None)


_LOOK = re.compile(r"^([A-Za-z]{1,3})(\d{1,3})")


def looks(book: str) -> list[tuple[str, Path]]:
    """The hero's looks of a Workshop book — agent/variants/<B2_blond>/hero.png (saved by the Workshop), by their names'
    numbers: [(«B2», the picture), …], at most seven (slide 7's frames)."""
    from ..workshop.rows import variant_names
    try:
        folder = store.book_folder(book)
    except Exception:
        return []
    out = []
    for name in variant_names(folder):
        hero = folder / "agent" / "variants" / name / "hero.png"
        if hero.is_file():
            m = _LOOK.match(name)
            out.append(((m.group(1).upper(), int(m.group(2))) if m else (name, 0), m.group(0).upper() if m else name, hero))
    out.sort(key=lambda x: x[0])
    return [(label, hero) for _, label, hero in out[:len(store.HERO_SLOTS)]]


def _looks_sig(found: list[tuple[str, Path]]) -> str:
    stamps = []
    for label, hero in found:
        try:
            stamps.append(f"{label}:{hero.parent.name}:{hero.stat().st_mtime_ns}")
        except OSError:
            pass
    return "|".join(stamps)


def put_heroes(rec: dict, book: str) -> bool:
    """The hero's looks into slide 7's frames (hero:1 … hero:7), each on its own white background — no cutting (the owner,
    2026-10-02: "it can stay with its white background"). Returns whether anything changed."""
    found = looks(book)
    sig = _looks_sig(found)
    if rec.get("looks") == sig and all(s in rec.get("pictures", {}) for s in store.HERO_SLOTS[:len(found)]):
        return False
    pictures = rec.setdefault("pictures", {})
    for slot in store.HERO_SLOTS:
        pictures.pop(slot, None)
        (store.set_dir(rec["id"]) / "pictures" / f"{store.slot_file(slot)}.png").unlink(missing_ok=True)
    for slot, (label, hero) in zip(store.HERO_SLOTS, found):
        store.put_picture(rec, slot, hero, name=f"{hero.parent.name}/hero.png")
        pictures[slot]["label"] = label
    rec["looks"] = sig
    return True


def sync_heroes(where: str) -> None:
    """A Workshop book's looks made (or changed) after its slides: slide 7 takes them when the slides are opened."""
    if not store.is_book(where):
        return
    try:
        rec = store.read_set(where)
        if put_heroes(rec, where):
            store.write_set(rec)
            core.log.info("Slides: the hero's looks of %s put on slide 7", where)
    except Exception:
        core.log.warning("Slides: the hero's looks of %s not taken", where, exc_info=True)


def _tick(book: str) -> None:
    """The Workshop's «Мокапи» step ticks itself when the mockups were made for its book (the owner, 29.09.2026)."""
    try:
        from ..workshop.books import set_mark
        set_mark(book, "mockups", True)
    except Exception:
        core.log.warning("Slides: the Workshop's «Мокапи» step of %s not ticked", book, exc_info=True)


def bake_set(job: Job, rec: dict, slides: list[str], base: str, token: str, states: dict | None = None) -> list[dict]:
    """The slides of a set baked into the owner's folder; the rows say how far."""
    states = states if states is not None else {}
    for s in slides:
        states[s] = "wait"
    outs = bake.outputs(rec, slides)
    total = len(slides)

    def progress(slide: str, state: str) -> None:
        states[slide] = state
        done = sum(states.get(s) == "done" for s in slides)
        job.share({"phase": "bake", "rows": rows(states)})
        job.progress(f"Малюю слайди · {done} з {total}", 45 + 55 * done / total)

    job.share({"phase": "bake", "rows": rows(states)})
    baked = bake.bake(rec["id"], slides, outs, base, token, progress)
    rec = store.read_set(rec["id"])  # the editor may have changed the numbers meanwhile
    for slide, path in baked.items():
        rec.setdefault("baked", {})[slide] = str(path)
    store.write_set(rec)
    core.log.info("Slides: baked %s of «%s» into %s", ", ".join(slides), rec.get("name"), rec.get("folder"))
    if store.is_book(rec["id"]):   # a Workshop book's etsy/: the slides take their numbers in the listing's order
        from .. import photos
        photos.tidy_etsy(store.book_folder(rec["id"]))
        rec = store.read_set(rec["id"])
    return pictures(rec)


def pictures(rec: dict) -> list[dict]:
    """The baked slides that are in the owner's folder, in order: {slide, name, v} (v — changes with the file)."""
    out = []
    for slide in store.shown(rec["id"], rec) if rec.get("id") else store.SLIDES:
        path = Path(rec.get("baked", {}).get(slide) or "")
        if path.name and path.is_file():
            out.append({"slide": slide, "name": path.name, "v": path.stat().st_mtime_ns})
    return out
