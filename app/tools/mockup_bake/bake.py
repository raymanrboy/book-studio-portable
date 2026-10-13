"""Bakes the owner's mockup templates for Book Studio's own drawing (studio/mockup_render.py) — needed once per
template, and again only when a template file changes (the Mockups then go the Photoshop way for it by themselves).

    1. python app/tools/mockup_bake/bake.py prepare [keys…] [--check 36.dinosaur-bedtime:20 …]
         copies the templates into the work folder, writes the calibration pictures and one Photoshop script (bake.jsx
         in the work folder): every smart object filled with black, white, flat levels and a coordinate ramp, and the
         check books filled as they really are (Photoshop's own mockups to compare with).
    2. Run that script in Photoshop (a running one: `Photoshop.exe <work>/bake.jsx`; it asks "run this script?" once).
       It takes 10–40 minutes and a few GB in the work folder; the status file beside it says how far it is.
    3. python app/tools/mockup_bake/bake.py build [keys…]
         makes <key>.npz (the hardcover ones) and <key>-m.npz (the softcover scenes) in the work folder and says how
         close Book Studio comes to Photoshop's own check mockups (mean / 99% of the pixels within, of 255).
    4. python app/tools/mockup_bake/install.py --from <work folder>
         puts them where Book Studio draws from. Close Photoshop before 3 — it holds 10+ GB of memory.

keys: open1 open2 cover1 dedication coverOpen allOpen (all when none is named). The templates are only read and copied.
How it works and what was learned: wiki/features/mockups.md («Drawn without Photoshop»); engine.py and mult.py here.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E  # noqa: E402
import mult as M  # noqa: E402

REPO = HERE.parents[2]
WORK = REPO / ".tmp" / "mockup-bake"
TEMPLATES = REPO.parent / "runtime" / "Templates"
BOOKS = REPO / "pipeline" / "books"
# The books and spreads Photoshop's own check mockups are made of (the pilot's, 13.10.2026). A template without spreads
# takes page 2 for its spread number (it has no pages of a spread).
CHECKS = {"open1": ["40.christmas-with-grandma:6", "25.sleepy-trucks-bedtime:12"],
          "open2": ["36.dinosaur-bedtime:8", "40.christmas-with-grandma:10"],
          "cover1": ["36.dinosaur-bedtime:2", "40.christmas-with-grandma:2"],
          "dedication": ["36.dinosaur-bedtime:2", "40.christmas-with-grandma:2"],
          "coverOpen": ["36.dinosaur-bedtime:20", "40.christmas-with-grandma:4"],
          "allOpen": ["36.dinosaur-bedtime:26", "40.christmas-with-grandma:16"]}


def _book(spec: str) -> tuple[Path, int]:
    name, _, spread = spec.rpartition(":")
    folder = Path(name) if Path(name).is_dir() else BOOKS / name
    if not folder.is_dir():
        raise SystemExit(f"no book {name}")
    return folder, int(spread)


def _multiply_passes(t: dict, inp: Path) -> list:
    """The softcover scenes: their smart objects multiply each other, so each is measured with the others WHITE."""
    sizes = {s: v[1] for s, v in t["slots"].items()}
    layers = {s: v[0] for s, v in t["slots"].items()}

    def pic(size, kind):
        p = inp / f"{kind}-{size[0]}x{size[1]}.png"
        if not p.exists():
            E.png16(p, E.calibration(size, kind))
        return p.as_posix()

    def fill(chosen):
        return [{"layer": layers[s], "image": chosen.get(s) or pic(sizes[s], "white")} for s in sizes]
    out = [{"name": "all-white", "fills": fill({})}]
    for s in sizes:
        out.append({"name": f"bkw-{s}", "fills": fill({s: pic(sizes[s], "black")})})
        out.append({"name": f"uvw-{s}", "fills": fill({s: pic(sizes[s], "uv")})})
    return out


def prepare(keys: list[str], work: Path, templates: Path, checks: dict) -> None:
    items = []
    for key in keys:
        t = E.TEMPLATES[key]
        copy = work / "templates" / t["file"]
        copy.parent.mkdir(parents=True, exist_ok=True)
        if not copy.exists():
            shutil.copyfile(templates / t["file"], copy)      # Photoshop only ever opens the copy
        out = work / "renders" / key
        out.mkdir(parents=True, exist_ok=True)
        inp = work / "in-cal"
        # the softcover scenes need black, grey and the flat levels (their tone curve), then each slot with the rest white
        passes = E.passes(t, inp)[:2] + E.level_passes(t, inp) + _multiply_passes(t, inp) if t.get("curve")             else E.passes(t, inp)
        truths = []
        for spec in checks[key]:
            folder, spread = _book(spec)
            fills = []
            for slot, im in E.book_pictures(folder, spread, key).items():
                p = work / "in-real" / f"{key}-{folder.name[:2]}-{spread}-{slot}.png"
                p.parent.mkdir(parents=True, exist_ok=True)
                im.save(p, "PNG", dpi=(300, 300), compress_level=1)
                fills.append({"layer": t["slots"][slot][0], "image": p.as_posix()})
            truths.append({"name": f"truth-{folder.name[:2]}-{spread}", "fills": fills})
        items.append({"template": copy.as_posix(), "out": out.as_posix(), "passes": passes, "truths": truths})
        print(f"{key}: {len(passes)} passes, {len(truths)} checks")
    job = {"status": (work / "status.json").as_posix(), "items": items}
    jsx = work / "bake.jsx"
    jsx.write_text(f"var JOB = {json.dumps(job, ensure_ascii=True)};\n\n" + (HERE / "bake.jsx").read_text(encoding="ascii"),
                   encoding="ascii")
    print(f"Now run in Photoshop: {jsx}")


def _checks(key: str, work: Path, checks: dict) -> list:
    out = []
    for spec in checks[key]:
        folder, spread = _book(spec)
        truth = work / "renders" / key / f"truth-{folder.name[:2]}-{spread}.png"
        if truth.is_file():
            pics = {s: E.as_float(im) for s, im in E.book_pictures(folder, spread, key).items()}
            out.append((truth.stem, pics, cv2.imread(str(truth))[..., ::-1]))
    return out


def _stats(ours, truth, region) -> str:
    d = np.abs(ours.astype(np.int16) - truth.astype(np.int16)).max(-1)[region]
    return f"mean {d.mean():.2f} / 99% within {np.percentile(d, 99):.0f}"


def build_linear(key: str, work: Path, checks: list) -> None:
    asset = work / f"{key}.npz"
    E.bake(key, work / "renders" / key, asset)
    a = E.load(asset)
    print("  interpolation:", E.tune(a, [(p, tr.astype(np.int16)) for _, p, tr in checks], asset))
    a = E.load(asset)
    book = np.zeros(a["k"].shape[:2], bool)
    for m in a["slots"].values():
        y0, y1, x0, x1 = m["box"]
        book[y0:y1, x0:x1] |= m["gain"].max(-1) > 0.02
    for name, pics, truth in checks:
        print(f"  {name}: {_stats(E.render(a, pics), truth, book)}")


def build_multiply(key: str, work: Path, checks: list) -> None:
    asset = work / f"{key}-m.npz"
    M.bake(key, work / "renders" / key, asset)
    a = M.load(asset)
    y0, y1, x0, x1 = a["box"]
    book = np.zeros(a["k"].shape[:2], bool)
    book[y0:y1, x0:x1] = a["alphas"].max(0) > 0.05
    a["interp"], a["blur"], a["prescale"] = {}, {}, {}
    for i, s in enumerate(a["slots"]):      # per slot: the interpolation and the shrinking closest to Photoshop
        region = np.zeros_like(book)
        region[y0:y1, x0:x1] = a["alphas"][i] > 0.5
        w = E.TEMPLATES[key]["slots"][s][1][0]
        U, V = a["uv"][i, ..., 0] * (w - 1), a["uv"][i, ..., 1] * (w - 1)
        sq = np.maximum(np.hypot(np.gradient(U, axis=1), np.gradient(V, axis=1)),
                        np.hypot(np.gradient(U, axis=0), np.gradient(V, axis=0)))[a["alphas"][i] > 0.9]
        f0 = 1 / float(np.median(sq)) if sq.size else 1.0
        err = {}
        for mode in (cv2.INTER_LINEAR, cv2.INTER_CUBIC):
            for k in (None, 1.0, 1.25, 1.5):
                a["interp"][s] = mode
                a["prescale"][s] = ("area", min(1.0, f0 * k)) if k else None
                err[(mode, k)] = np.mean([np.abs(M.render(a, p).astype(np.int16) - tr).max(-1)[region].mean()
                                          for _, p, tr in checks])
        mode, k = min(err, key=err.get)
        a["interp"][s], a["prescale"][s] = mode, (("area", min(1.0, f0 * k)) if k else None)
        print(f"  {s}: squeeze {1 / f0:.2f}, {'cubic' if mode == cv2.INTER_CUBIC else 'linear'}, shrink x{k}")
    a["prescale"] = {s: v for s, v in a["prescale"].items() if v}
    print("  placement corrected (px):", M.register(a, [(p, tr) for _, p, tr in checks]))
    M.save(a, asset)
    for name, pics, truth in checks:
        print(f"  {name}: {_stats(M.render(a, pics), truth, book)} (raw; the eye sees ~1–2)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Bake the mockup templates (see the module's text).")
    ap.add_argument("step", choices=("prepare", "build"))
    ap.add_argument("keys", nargs="*")
    ap.add_argument("--work", type=Path, default=WORK)
    ap.add_argument("--templates", type=Path, default=TEMPLATES)
    ap.add_argument("--check", action="append", default=[], help="BOOK:SPREAD — the check books (instead of the pilot's)")
    args = ap.parse_args()
    keys = args.keys or list(E.TEMPLATES)
    bad = [k for k in keys if k not in E.TEMPLATES]
    if bad:
        raise SystemExit(f"unknown: {', '.join(bad)}")
    checks = {k: args.check or CHECKS[k] for k in keys}
    args.work = args.work.resolve()          # the script names absolute paths: Photoshop runs elsewhere
    args.work.mkdir(parents=True, exist_ok=True)
    if args.step == "prepare":
        prepare(keys, args.work, args.templates, checks)
        return
    for key in keys:
        t0 = time.time()
        print(key)
        found = _checks(key, args.work, checks)
        (build_multiply if E.TEMPLATES[key].get("curve") else build_linear)(key, args.work, found)
        print(f"  {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
