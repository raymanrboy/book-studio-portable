"""Mockups without Photoshop — the pilot's engine in one place.

Bake (once per template, Photoshop needed): every slot (smart object) is filled with black, white and a coordinate
ramp, each slot on its own; the boards also in four edge strips; a colour slot (Dedication's desk and floor) only
black and white. From those renders:
    out = black + sum over slots of gain_s * picture_s(uv_s) + sum over colour slots of gain_c * colour_c
and on a board's corner fold (two edge strips of the picture meeting in one pixel) the strips' own gains and uvs.
Render (every book, no Photoshop): the formula above.
"""
from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

EPS = 0.004
EDGES = ("top", "bottom", "left", "right")
LEVELS = [i / 8 for i in range(9)]   # a template with a curve: measured at these picture values (0, 1/2, 1 — black, grey, white)
HARD = {"page": (1900, 1900), "board": (2100, 2200), "spine": (80, 2200)}
SOFT = {"page": (1935, 1935), "board": (1935, 1935), "spine": (164, 1935)}
_KIND = {"left": "page", "right": "page", "page1": "page", "front": "board", "back": "board", "spine": "spine"}


def _slots(size, **paths):
    return {s: (list(p), size[_KIND[s]]) for s, p in paths.items()}


_A = dict(front=("Main", "Cover"), back=("Main", "Back Cover"), spine=("Main", "Rige"))
TEMPLATES = {
    "open1": {"file": "2. Open 1.psd", "size": HARD, "boards": ("front", "back"),
              "slots": _slots(HARD, left=("Main", "Left"), right=("Main", "Right"), **_A)},
    "open2": {"file": "3. Open 2.psd", "size": HARD, "boards": ("front", "back"),
              "slots": _slots(HARD, left=("Main", "Left"), right=("Main", "Right"), **_A)},
    "cover1": {"file": "1. Cover 1.psd", "size": HARD, "boards": ("front",),
               "slots": _slots(HARD, front=("Main", "COVER_"))},
    "dedication": {"file": "4. Dedication.psd", "size": HARD, "boards": ("front", "back"),
                   "slots": _slots(HARD, page1=("Main", "Page 1"), **_A),
                   "colours": {"desk": (["Main", "Deck Color"], (101, 101), (139, 110, 52)),
                               "floor": (["Main", "Background"], (5000, 5000), (225, 225, 225))}},
    "coverOpen": {"file": "Cover & Open 1.psd", "size": SOFT, "boards": (), "curve": True,
                  "slots": _slots(SOFT, left=("Left Page",), right=("Right Page",), front=("Front Cover",))},
    "allOpen": {"file": "All & Open 1.psd", "size": SOFT, "boards": (), "curve": True,
                "slots": _slots(SOFT, left=("Left",), right=("Right",), front=("Front Cover",), back=("Back Cover",),
                                spine=("Spine",))},
}


# ------------------------------------------------------------------ calibration pictures

def png16(path: Path, rgb: np.ndarray) -> None:
    """16-bit RGB PNG at 300 dpi (Photoshop places a picture by its dpi)."""
    ok, buf = cv2.imencode(".png", np.ascontiguousarray(rgb[..., ::-1]), [cv2.IMWRITE_PNG_COMPRESSION, 1])
    assert ok
    data = buf.tobytes()
    ppm = round(300 / 0.0254)
    body = struct.pack(">IIB", ppm, ppm, 1)
    chunk = struct.pack(">I", len(body)) + b"pHYs" + body + struct.pack(">I", zlib.crc32(b"pHYs" + body) & 0xFFFFFFFF)
    path.write_bytes(data[:33] + chunk + data[33:])


def strip_mask(size, edge):
    w, h = size
    x = np.arange(w)[None, :].repeat(h, 0)
    y = np.arange(h)[:, None].repeat(w, 1)
    return np.argmin(np.stack([y, h - 1 - y, x, w - 1 - x]), 0) == EDGES.index(edge)


def calibration(size, kind, mask=None):
    w, h = size
    if kind in ("black", "white", "grey"):
        a = np.full((h, w, 3), {"black": 0, "white": 65535, "grey": 32768}[kind], np.uint16)
    elif kind.startswith("level"):
        a = np.full((h, w, 3), round(float(kind[5:]) * 65535), np.uint16)
    else:
        f = np.zeros((h, w, 3))
        f[..., 0] = (np.arange(w) / (w - 1))[None, :]
        f[..., 1] = (np.arange(h) / (h - 1))[:, None]
        a = np.round(f * 65535).astype(np.uint16)
    if mask is not None:
        a[~mask] = 0
    return a


def units(t):
    """What is measured: (unit name, slot, edge or None, kinds)."""
    out = [(s, s, None, ("white", "uv")) for s in t["slots"]]
    out += [(f"{s}-{e}", s, e, ("white", "uv")) for s in t["boards"] for e in EDGES]
    out += [(c, c, None, ("white",)) for c in t.get("colours", {})]
    return out


def _sizes(t):
    return {**{s: v[1] for s, v in t["slots"].items()}, **{c: v[1] for c, v in t.get("colours", {}).items()}}


def _layers(t):
    return {**{s: v[0] for s, v in t["slots"].items()}, **{c: v[0] for c, v in t.get("colours", {}).items()}}


def passes(t, inp: Path):
    """The Photoshop passes of a bake; the calibration pictures written into `inp` (shared, named by size)."""
    inp.mkdir(parents=True, exist_ok=True)
    sizes, layers = _sizes(t), _layers(t)

    def pic(size, kind, edge=None):
        p = inp / f"{kind}-{size[0]}x{size[1]}{'-' + edge if edge else ''}.png"
        if not p.exists():
            png16(p, calibration(size, kind, strip_mask(size, edge) if edge else None))
        return p.as_posix()

    def fill(chosen):   # every slot black but the chosen ones
        return [{"layer": layers[s], "image": chosen.get(s) or pic(sizes[s], "black")} for s in sizes]

    result = [{"name": "black", "fills": fill({})},
              {"name": "grey", "fills": fill({s: pic(sizes[s], "grey") for s in sizes})}]
    for unit, slot, edge, kinds in units(t):
        for kind in kinds:
            result.append({"name": f"{kind}-{unit}", "fills": fill({slot: pic(sizes[slot], kind, edge)})})
    if t.get("curve"):
        result += level_passes(t, inp)
    return result


def level_name(x):
    return f"level{x:.3f}"


def level_passes(t, inp: Path):
    """Every slot filled with one flat value, for each level but 0, 1/2 and 1 (black, grey, the slot's white)."""
    sizes, layers = _sizes(t), _layers(t)
    out = []
    for x in LEVELS[1:-1]:
        if x == 0.5:
            continue
        fills = []
        for s, size in sizes.items():
            p = inp / f"{level_name(x)}-{size[0]}x{size[1]}.png"
            if not p.exists():
                png16(p, calibration(size, level_name(x)))
            fills.append({"layer": layers[s], "image": p.as_posix()})
        out.append({"name": level_name(x), "fills": fills})
    return out


# ------------------------------------------------------------------ bake

def _load(path: Path):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    assert im is not None and im.dtype == np.uint16, path
    return im[..., ::-1].astype(np.float32) / 65535


def _measure(renders: Path, k, unit, with_uv=True):
    gain = _load(renders / f"white-{unit}.png") - k
    on = gain.max(-1) > EPS
    if not on.any():
        return None   # not seen in this template (a strip of the board out of the picture)
    ys, xs = np.nonzero(on)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    g = gain[y0:y1, x0:x1]
    m = {"box": [int(y0), int(y1), int(x0), int(x1)], "gain": np.where(on[y0:y1, x0:x1, None], np.clip(g, 0, 1), 0)}
    if with_uv:
        uv = _load(renders / f"uv-{unit}.png")
        with np.errstate(divide="ignore", invalid="ignore"):
            rel = np.where(g[..., :2] > EPS, (uv[y0:y1, x0:x1, :2] - k[y0:y1, x0:x1, :2]) / g[..., :2], 0)
        m["u"], m["v"] = rel[..., 0], rel[..., 1]
    return m


def _strip_of(U, V, w, h, margin):
    d = np.stack([V, h - 1 - V, U, w - 1 - U])
    s = np.sort(d, 0)
    return np.where(s[1] - s[0] > margin, np.argmin(d, 0), -1)


def _folds(m, size, T=12, margin=15, grow=1):
    """Pixels of a board where neighbours (up to 5 px apart) come from two different edge strips of the picture,
    each clearly its own — the corner's fold — and the pixels between them."""
    w, h = size
    U, V, G = m["u"] * (w - 1), m["v"] * (h - 1), m["gain"].mean(-1)
    L = _strip_of(U, V, w, h, margin)
    out = np.zeros(U.shape, bool)
    for r in range(1, 6):
        for dy, dx in ((0, r), (r, 0), (r, r), (r, -r)):
            Ub, Vb, Gb, Lb = (np.roll(a, (-dy, -dx), (0, 1)) for a in (U, V, G, L))
            hit = (np.hypot(Ub - U, Vb - V) > T) & (G > 0.05) & (Gb > 0.05) & (L >= 0) & (Lb >= 0) & (L != Lb)
            for t in range(r + 1):
                out |= np.roll(hit, (round(dy * t / r), round(dx * t / r)), (0, 1))
    return cv2.dilate(out.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=grow).astype(bool)


def bake(key: str, renders: Path, asset: Path) -> dict:
    t = TEMPLATES[key]
    k = _load(renders / "black.png")
    a = {"key": key, "k": k, "slots": {}, "parts": [], "colours": {}}
    for unit, slot, edge, kinds in units(t):
        m = _measure(renders, k, unit, "uv" in kinds)
        if m is None:
            continue
        if "uv" not in kinds:
            a["colours"][slot] = m
        elif edge is None:
            if slot in t["boards"]:
                m["fold"] = _folds(m, t["slots"][slot][1])
            a["slots"][slot] = m
        else:
            m["slot"] = slot
            a["parts"].append(m)
    for p in a["parts"]:
        s = a["slots"].get(p["slot"])
        if not s or "fold" not in s:
            p["fold"] = np.zeros(p["gain"].shape[:2], bool)
            continue
        full = np.zeros(k.shape[:2], bool)
        y0, y1, x0, x1 = s["box"]
        full[y0:y1, x0:x1] = s["fold"]
        y0, y1, x0, x1 = p["box"]
        p["fold"] = full[y0:y1, x0:x1]
    a["parts"] = [p for p in a["parts"] if p["fold"].any()]
    if t.get("curve"):
        _curve(a, renders, k)
    # linearity: the all-grey render against the formula
    if not (renders / "grey.png").exists():
        save(a, asset)
        return a
    grey = _load(renders / "grey.png")
    pred = k.copy()
    for m in list(a["slots"].values()) + list(a["colours"].values()):
        y0, y1, x0, x1 = m["box"]
        pred[y0:y1, x0:x1] += m["gain"] * (32768 / 65535)
    a["linear_dev"] = np.abs(grey - pred).max(-1) * 255
    save(a, asset)
    return a


def _curve(a, renders: Path, k):
    """A template whose layers over the book bend its tones (Soft Light, Colour/Linear Burn): per pixel and channel,
    out = k + D(c) with D measured at LEVELS (flat passes; 0 — black, 1/2 — grey, 1 — the slot's own white) and
    read between them along straight lines. The picture position: the uv pass read back through the same curve."""
    levels = {}
    for x in LEVELS[1:-1]:
        levels[x] = renders / ("grey.png" if x == 0.5 else f"{level_name(x)}.png")
    crops = {s: [np.zeros(m["gain"].shape, np.float32)] for s, m in a["slots"].items()}
    for x, path in levels.items():
        img = _load(path) - k
        for s, m in a["slots"].items():
            y0, y1, x0, x1 = m["box"]
            crops[s].append(img[y0:y1, x0:x1])
        del img
    for s, m in a["slots"].items():
        y0, y1, x0, x1 = m["box"]
        D = np.stack(crops[s] + [m["gain"]])                  # (9, h, w, 3)
        D = np.maximum.accumulate(np.clip(D, 0, 1), axis=0)    # the curve only rises
        obs = np.clip(_load(renders / f"uv-{s}.png")[y0:y1, x0:x1, :2] - k[y0:y1, x0:x1, :2], 0, 1)
        rel = np.zeros(obs.shape, np.float32)
        rel[obs >= D[-1, ..., :2]] = 1
        n = len(LEVELS) - 1
        for j in range(n):
            lo, hi = D[j, ..., :2], D[j + 1, ..., :2]
            inside = (obs >= lo) & (obs < hi)
            with np.errstate(divide="ignore", invalid="ignore"):
                t = np.where(hi > lo, (obs - lo) / (hi - lo), 0)
            rel = np.where(inside, (j + t) / n, rel)
        m["u"], m["v"] = rel[..., 0], rel[..., 1]
        m["curve"] = D


def save(a, path: Path):
    flat = {"k": np.round(a["k"] * 65535).astype(np.uint16), "meta": np.frombuffer(json.dumps(
        {"key": a["key"], "slots": {s: m["box"] for s, m in a["slots"].items()},
         "colours": {c: m["box"] for c, m in a["colours"].items()},
         "parts": [[p["slot"], p["box"]] for p in a["parts"]]}).encode(), np.uint8)}
    named = [(s, m) for s, m in a["slots"].items()] + [(f"part{i}", p) for i, p in enumerate(a["parts"])] + \
            [(f"colour-{c}", m) for c, m in a["colours"].items()]
    for name, m in named:
        flat[f"{name}_gain"] = np.round((m["gain"] + 1) * 32767.5).astype(np.uint16)
        if "u" in m:
            flat[f"{name}_uv"] = np.round(np.clip(np.stack([m["u"], m["v"]], -1), -0.5, 1.5) * 32768 + 16384).astype(np.uint16)
        if "fold" in m:
            flat[f"{name}_fold"] = np.packbits(m["fold"], axis=-1)
        if "curve" in m:
            flat[f"{name}_curve"] = np.round(m["curve"][1:] * 65535).astype(np.uint16)
        if "interp" in m:
            flat[f"{name}_interp"] = np.array([m["interp"]])
    np.savez_compressed(path, **flat)


def load(path: Path) -> dict:
    z = np.load(path)
    meta = json.loads(z["meta"].tobytes())
    a = {"key": meta["key"], "k": z["k"].astype(np.float32) / 65535, "slots": {}, "parts": [], "colours": {}}

    def unpack(name, box):
        g = z[f"{name}_gain"].astype(np.float32) / 32767.5 - 1
        m = {"box": box, "gain": g}
        if f"{name}_curve" in z:
            c = z[f"{name}_curve"].astype(np.float32) / 65535
            m["curve"] = np.concatenate([np.zeros((1,) + c.shape[1:], np.float32), c])
        if f"{name}_interp" in z:
            m["interp"] = int(z[f"{name}_interp"][0])
        if f"{name}_uv" in z:
            uv = (z[f"{name}_uv"].astype(np.float32) - 16384) / 32768
            m["u"], m["v"] = uv[..., 0], uv[..., 1]
        if f"{name}_fold" in z:
            m["fold"] = np.unpackbits(z[f"{name}_fold"], axis=-1, count=g.shape[1]).astype(bool)
        return m
    for s, box in meta["slots"].items():
        a["slots"][s] = unpack(s, box)
    for i, (slot, box) in enumerate(meta["parts"]):
        m = unpack(f"part{i}", box)
        m["slot"] = slot
        a["parts"].append(m)
    for c, box in meta["colours"].items():
        a["colours"][c] = unpack(f"colour-{c}", box)
    return a


# ------------------------------------------------------------------ render

def _sample(img, m):
    h, w = img.shape[:2]
    return cv2.remap(img, (m["u"] * (w - 1)).astype(np.float32), (m["v"] * (h - 1)).astype(np.float32),
                     m.get("interp", cv2.INTER_LINEAR), borderMode=cv2.BORDER_REPLICATE)


def _apply(m, c):
    if "curve" not in m:
        return m["gain"] * c
    D = m["curve"]
    n = D.shape[0] - 1
    x = np.clip(c, 0, 1) * n
    j = np.minimum(x.astype(np.int64), n - 1)
    t = x - j
    lo = np.take_along_axis(D, j[None], 0)[0]
    hi = np.take_along_axis(D, j[None] + 1, 0)[0]
    return lo + (hi - lo) * t


def render(a, pictures: dict, colours: dict | None = None) -> np.ndarray:
    """pictures: slot -> float32 RGB 0..1 of the slot's own size; colours: colour slot -> (r, g, b) 0..255 (the
    template's own when left out). Returns 8-bit RGB."""
    t = TEMPLATES[a["key"]]
    out = a["k"].copy()
    for s, m in a["slots"].items():
        y0, y1, x0, x1 = m["box"]
        c = _apply(m, _sample(pictures[s], m))
        if "fold" in m:
            c[m["fold"]] = 0
        out[y0:y1, x0:x1] += c
    for p in a["parts"]:
        y0, y1, x0, x1 = p["box"]
        c = _apply(p, _sample(pictures[p["slot"]], p))
        c[~p["fold"]] = 0
        out[y0:y1, x0:x1] += c
    for name, m in a["colours"].items():
        y0, y1, x0, x1 = m["box"]
        rgb = (colours or {}).get(name) or t["colours"][name][2]
        out[y0:y1, x0:x1] += m["gain"] * (np.array(rgb, np.float32) / 255)
    return np.clip(np.round(out * 255), 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ the production pictures (as mockups.py makes them)

def _fill(im, size, centre=None, scale=None):
    w, h = im.size
    cx, cy = centre or (w / 2, h / 2)
    scale = scale or max(size[0] / w, size[1] / h)
    cw, ch = size[0] / scale, size[1] / scale
    x0 = min(max(cx - cw / 2, 0), max(w - cw, 0))
    y0 = min(max(cy - ch / 2, 0), max(h - ch, 0))
    return im.resize(size, Image.Resampling.LANCZOS, box=(x0, y0, x0 + min(cw, w), y0 + min(ch, h)))


def book_pictures(book: Path, spread: int, key: str) -> dict:
    """slot -> PIL picture for the template, the way mockups.prepare() makes them (pages from pictures/, the cover
    from canva-cover; page 1 is the dedication)."""
    t = TEMPLATES[key]
    size = t["size"]
    out = {}
    pages = {"left": spread, "right": spread + 1, "page1": 1}
    for slot in t["slots"]:
        if slot in pages:
            with Image.open(book / "pictures" / f"{pages[slot]}.png") as im:
                out[slot] = _fill(im.convert("RGB"), size["page"])
    if any(s in t["slots"] for s in ("front", "back", "spine")):
        with Image.open(next((book / "mockups").glob("canva-cover.*"))) as im:
            im = im.convert("RGB")
            w, h = im.size
            bw, bh = size["board"]
            scale = max(bw / (w / 2), bh / h)
            cover = {"back": _fill(im.crop((0, 0, w // 2, h)), (bw, bh), scale=scale),
                     "front": _fill(im.crop((w - w // 2, 0, w, h)), (bw, bh), scale=scale),
                     "spine": _fill(im, size["spine"], centre=(w / 2, h / 2), scale=scale)}
        out.update({s: cover[s] for s in ("front", "back", "spine") if s in t["slots"]})
    return out


def as_float(pil) -> np.ndarray:
    return np.asarray(pil, np.float32) / 255


# ------------------------------------------------------------------ tuning at bake

def tune(a, checks, asset: Path) -> dict:
    """checks: [(pictures, Photoshop's own render as uint8 RGB)]. Per slot: bilinear or bicubic, whichever is closer
    to Photoshop (it draws a warped picture one way and a plainly transformed one another). Saved into the asset."""
    chosen = {}
    for s, m in a["slots"].items():
        y0, y1, x0, x1 = m["box"]
        region = m["gain"].max(-1) > 0.05
        err = {}
        for mode in (cv2.INTER_LINEAR, cv2.INTER_CUBIC):
            m["interp"] = mode
            for p in a["parts"]:
                if p["slot"] == s:
                    p["interp"] = mode
            e = 0.0
            for pictures, truth in checks:
                out = render(a, pictures)[y0:y1, x0:x1].astype(np.int16)
                e += np.abs(out - truth[y0:y1, x0:x1]).max(-1)[region].mean()
            err[mode] = e / len(checks)
        best = min(err, key=err.get)
        m["interp"] = best
        for p in a["parts"]:
            if p["slot"] == s:
                p["interp"] = best
        chosen[s] = ("bicubic" if best == cv2.INTER_CUBIC else "bilinear", round(float(err[best]), 3))
    save(a, asset)
    return chosen
