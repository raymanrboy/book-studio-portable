"""«Запекти»: a slide drawn at 2000×2000 by headless Edge/Chrome — the same drawing code as the editor
(web/js/slides/engine.js), the page web/slides/render.html of Book Studio's own server.

The browser starts only for a bake and goes right after; its profile lives in app/data/tmp (drive D — nothing on
drive C) and is removed. Three slides are drawn at once (~3 s each).
"""
from __future__ import annotations

import shutil
import subprocess
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .. import core, desktop
from ..jobs import UserError
from . import store

SIZE = 1000        # the stage in CSS pixels; × 2 → 2000×2000
AT_ONCE = 3
NAME = "Listing {n}.png"   # the owner's folder: «Listing 1.png … Listing 6.png» (the plan's default, 29.09.2026)
CREATE_NO_WINDOW = 0x08000000


def browser() -> str:
    found = desktop.find_browser()
    if not found:
        raise UserError("Не знайшов ні Edge, ні Chrome — слайди малює браузер.")
    return found


def run_browser(args: list[str], timeout: int) -> None:
    """The one place a browser is started (the tests put a pretend one here)."""
    subprocess.run(args, capture_output=True, timeout=timeout,
                   creationflags=CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0)


def render(where: str, slide: str, out: Path, base: str, token: str, profile: Path) -> Path:
    """One slide into `out` (a file of the program's own: written through a temporary one, then put in place)."""
    query = urllib.parse.urlencode({"w": where, "s": slide, "t": token})
    tmp = core.data_path("tmp", "slides", f"{core.new_id()[:12]}.png")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    try:
        run_browser([
            browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--force-device-scale-factor=2", f"--window-size={SIZE},{SIZE}", "--virtual-time-budget=15000",
            f"--user-data-dir={profile}", f"--screenshot={tmp}", f"{base}/slides/render.html?{query}",
        ], timeout=120)
        if not tmp.is_file():
            raise UserError(f"Браузер не намалював {slide.replace('slide', 'слайд ')}.")
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tmp), str(out))
    except subprocess.TimeoutExpired:
        raise UserError(f"Браузер завис на {slide.replace('slide', 'слайді ')}.") from None
    finally:
        tmp.unlink(missing_ok=True)
    return out


def outputs(rec: dict, slides: list[str]) -> dict[str, Path]:
    """Where each slide goes in the owner's folder: the file it was baked into before (the program's own — it is
    replaced), else «Listing N.png», never over a file that is there."""
    folder = Path(rec["folder"])
    taken, out = set(), {}
    for slide in store.SLIDES:
        before = rec.get("baked", {}).get(slide)
        if before and Path(before).parent == folder:
            taken.add(Path(before).name.lower())
    for slide in slides:
        before = rec.get("baked", {}).get(slide)
        if before and Path(before).parent == folder:
            out[slide] = Path(before)
            continue
        n = store.SLIDES.index(slide) + 1
        name, k = NAME.format(n=n), 1
        while name.lower() in taken or (folder / name).exists():
            k += 1
            name = NAME.format(n=n).replace(".png", f" ({k}).png")
        taken.add(name.lower())
        out[slide] = folder / name
    return out


def bake(where: str, slides: list[str], outs: dict[str, Path], base: str, token: str, progress=None) -> dict:
    """Draws the slides into their files; `progress(slide, state)` — waiting / work / done. Returns slide → path."""
    profiles = core.data_path("tmp", "slides-browser")
    done: dict[str, Path] = {}

    def one(i_slide):
        i, slide = i_slide
        if progress:
            progress(slide, "work")
        path = render(where, slide, outs[slide], base, token, profiles / str(i))   # a profile per slide: two browsers never share one
        if progress:
            progress(slide, "done")
        return slide, path

    try:
        with ThreadPoolExecutor(AT_ONCE) as pool:
            for slide, path in pool.map(one, enumerate(slides)):
                done[slide] = path
    finally:
        shutil.rmtree(profiles, ignore_errors=True)
    return done
