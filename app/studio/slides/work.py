"""The slides made for a book: its mockups cut out, a set made from the template, the six baked into the owner's
folder — the Mockups' next step «Зробити слайди» (the owner, 29.09.2026: "after the Photoshop script the Mockups
page offers the next step, the listing slides; I press it and they are made by themselves").
"""
from __future__ import annotations

import time
from pathlib import Path

from .. import core
from ..jobs import Job, UserError
from . import bake, cutout, store

TITLES = {  # what the rows say while the six are drawn
    "slide1": "Made just for them", "slide2": "Choose your format", "slide3": "Dedication & afterword",
    "slide4": "Unique little poems", "slide5": "Personalization made simple", "slide6": "Thank you",
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
    return [{"slide": s, "title": title(s), "state": states.get(s, "wait")} for s in store.SLIDES]


def make(job: Job, folder: Path, name: str, order: list[str] | None, page30: Path | None, numbers: dict,
         templates_dir: Path, base: str, token: str) -> dict:
    started = time.time()
    if not folder.is_dir():
        raise UserError("Папку з мокапами не знайдено.")
    found = mockups_in(folder, order)
    slots = slots_of(found)
    if not slots:
        raise UserError("У папці немає мокапів Open 1, Open 2 чи Cover 1 — слайдам нема що показати.")
    states: dict[str, str] = {}
    job.share({"phase": "cut", "rows": rows(states)})
    cuts: dict[str, Path] = {}
    for i, (slot, png) in enumerate(slots.items()):
        job.progress(f"Вирізаю книги без фону · {i + 1} з {len(slots)}", 40 * i / len(slots))
        while cutout.cutter.status(folder).get(png.name) in ("wait", "work"):   # the background cutter has it
            time.sleep(0.3)
        cuts[slot] = cutout.ensure(png, templates_dir)
    job.progress("Складаю слайди", 42)
    rec = store.new_set(name, str(folder), numbers)
    for slot, cut_folder in cuts.items():
        store.put_book(rec, slot, cut_folder, slots[slot].name)
    if found["dedication"]:
        store.put_picture(rec, "dedication", found["dedication"][0])
    if page30 and page30.is_file():
        store.put_picture(rec, "page30", page30)
    store.write_set(rec)
    store.forget_old_sets()
    baked = bake_set(job, rec, store.SLIDES, base, token, states)
    missing = [store.SLOT_LABEL[s] for s in store.BOOK_SLOTS + store.PICTURE_SLOTS
               if s not in rec["books"] and s not in rec["pictures"]]
    return {"set": rec["id"], "folder": str(folder), "pictures": baked, "missing": missing,
            "seconds": round(time.time() - started)}


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
    return pictures(rec)


def pictures(rec: dict) -> list[dict]:
    """The baked slides that are in the owner's folder, in order: {slide, name, v} (v — changes with the file)."""
    out = []
    for slide in store.SLIDES:
        path = Path(rec.get("baked", {}).get(slide) or "")
        if path.name and path.is_file():
            out.append({"slide": slide, "name": path.name, "v": path.stat().st_mtime_ns})
    return out
