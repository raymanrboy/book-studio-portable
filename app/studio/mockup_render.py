"""Mockups without Photoshop: the owner's templates drawn by Book Studio itself from their "baked" form.

Each template was rendered once in Photoshop with calibration pictures (black, white, a coordinate ramp in every smart
object — the bake, `app/tools/mockup_bake/`); what came out says, for every pixel of the template, which point of which
picture lands there and how the template's light and shadow change it. Drawing a book is then arithmetic (13.10.2026,
the owner: "try to drop Photoshop"): 0.2–0.4 s a hardcover picture, 2–3 s a softcover scene, equal to Photoshop by eye
(on average under 1 of 255 for the hardcovers, 1–2 for the softcover scenes as the eye sees them).

Two kinds of baked template (`.npz` in BAKED, one per template key):
    linear    — 2. Open 1, 3. Open 2, 1. Cover 1, 4. Dedication:
                out = black + sum over smart objects of gain * picture(uv); a board's corner folds drawn from the
                picture's edge strips (`parts`).
    multiply  — Cover & Open 1, All & Open 1: the vendor's smart objects lie over each other in Multiply and the
                layers above bend the tones: P = product of (1 - a + a * picture(uv)), out = F(P) per pixel (F kept as
                8-bit rises at 9 levels). Their colour fills (`Change Color` — the background, `Back Color` /
                `Front Color` — the open book's edges) are baked at the vendor's colours and swapped here with the
                fills' own masks.

A baked file is used only while its template is the very file it was baked from (`stamp()`); otherwise the Mockups go
the old way, through Photoshop.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path

from PIL import Image

from . import core

BAKED = core.data_path("mockups", "baked")     # <key>.npz + baked.json (which template file each was baked from)
STAMPS = "baked.json"
EPS = 0.004
CHUNK = 384           # rows drawn at once in a multiply template (memory)
KEEP = 120            # s: a baked template stays in memory this long after its last use (the editor redraws often)
FILL_ORDER = ("Change Color", "Back Color", "Front Color")   # bottom to top, as in the PSD

_lock = threading.Lock()
_loaded: dict[str, tuple[str, dict]] = {}     # key -> (stamp, asset): one at a time (a few hundred MB)
_used = 0.0
_stamps: dict[tuple, str] = {}


# ---------------------------------------------------------------- which templates are baked

def stamp(psd: Path) -> str:
    """The template file's identity: its size and the hash of its first and last 4 MB (a whole hash of 400 MB would
    take seconds; a resaved PSD changes both ends)."""
    st = psd.stat()
    key = (str(psd), st.st_size, st.st_mtime_ns)
    if key not in _stamps:
        h = hashlib.sha1(str(st.st_size).encode())
        with open(psd, "rb") as f:
            h.update(f.read(4 << 20))
            if st.st_size > 8 << 20:
                f.seek(-(4 << 20), 2)
                h.update(f.read())
        _stamps[key] = h.hexdigest()[:20]
    return _stamps[key]


def _stamps_file() -> dict:
    data = core.read_json(BAKED / STAMPS, {})
    return data if isinstance(data, dict) else {}


def ready(key: str, psd: Path) -> bool:
    """A baked form of this very template file is there."""
    try:
        return (BAKED / f"{key}.npz").is_file() and (_stamps_file().get(key) or {}).get("stamp") == stamp(psd)
    except OSError:
        return False


# ---------------------------------------------------------------- loading

def _load(key: str):
    import numpy as np
    z = np.load(BAKED / f"{key}.npz")
    meta = json.loads(z["meta"].tobytes())
    a = {"kind": "multiply" if "rise" in z.files else "linear", "meta": meta}
    if a["kind"] == "multiply":
        a["k"] = z["k"]                                  # uint16, the whole picture as the template has it
        # Only the pixels some book covers are drawn: kept packed, one column per pixel (less memory, plain slices)
        y0, y1, x0, x1 = meta["box"]
        alphas = z["alphas"]
        on = (alphas > EPS * 65535).any(0)
        idx = np.flatnonzero(on).astype(np.int32)
        a["on"] = idx                                    # flat index inside the box
        a["alphas"] = alphas.reshape(len(alphas), -1)[:, idx]
        a["uv"] = z["uv"].reshape(len(alphas), -1, 2)[:, idx]
        a["rise"] = z["rise"].reshape(len(z["rise"]), -1, 3)[:, idx]
        a["fills"] = {name: (mode, z[f"fill{i}"], tuple(rgb)) for i, (name, mode, rgb) in enumerate(meta.get("fills") or [])}
        union = np.zeros(a["k"].shape[:2], bool)
        for _, mask, _ in a["fills"].values():
            union |= mask > 0
        # Most of the background is under the burn fill alone, fully: there a new colour is a plain shift
        plain = np.zeros_like(union)
        if "Change Color" in a["fills"]:
            plain = a["fills"]["Change Color"][1] == 255
            for name, (_, mask, _) in a["fills"].items():
                if name != "Change Color":
                    plain &= mask == 0
        a["fill_plain"] = np.flatnonzero(plain).astype(np.int32)
        a["fill_on"] = np.flatnonzero(union & ~plain).astype(np.int32)
        a["fill_masks"] = {name: mask.reshape(-1)[a["fill_on"]] for name, (_, mask, _) in a["fills"].items()}
        return a
    a["k"] = z["k"].astype(np.float32) / 65535
    a["slots"], a["parts"], a["colours"] = {}, [], {}

    def unpack(name, box):
        g = z[f"{name}_gain"].astype(np.float32) / 32767.5 - 1
        m = {"box": box, "gain": g}
        if f"{name}_interp" in z.files:
            m["interp"] = int(z[f"{name}_interp"][0])
        if f"{name}_uv" in z.files:
            uv = (z[f"{name}_uv"].astype(np.float32) - 16384) / 32768
            m["u"], m["v"] = np.ascontiguousarray(uv[..., 0]), np.ascontiguousarray(uv[..., 1])
        if f"{name}_fold" in z.files:
            m["fold"] = np.unpackbits(z[f"{name}_fold"], axis=-1, count=g.shape[1]).astype(bool)
        return m
    for s, box in meta["slots"].items():
        a["slots"][s] = unpack(s, box)
    for i, (slot, box) in enumerate(meta["parts"]):
        a["parts"].append({**unpack(f"part{i}", box), "slot": slot})
    for c, box in meta["colours"].items():
        a["colours"][c] = unpack(f"colour-{c}", box)
    a["default_colours"] = {c: tuple(v) for c, v in (meta.get("default_colours") or {}).items()}
    return a


def _asset(key: str) -> dict:
    global _used
    want = (_stamps_file().get(key) or {}).get("stamp") or ""
    with _lock:
        _used = time.monotonic()
        if key in _loaded and _loaded[key][0] == want:
            return _loaded[key][1]
        _loaded.clear()                    # one in memory at a time
        asset = _load(key)
        _loaded[key] = (want, asset)
        _forget_later()
        return asset


_timer: threading.Timer | None = None


def _forget_later() -> None:
    """One timer at a time (called under _lock): it lets the baked template go once unused for KEEP seconds."""
    global _timer
    if _timer is not None and _timer.is_alive():
        return

    def check():
        global _timer
        with _lock:
            _timer = None
            if not _loaded:
                return
            if time.monotonic() - _used >= KEEP:
                _loaded.clear()
                return
            _forget_later()
    _timer = threading.Timer(KEEP / 2, check)
    _timer.daemon = True
    _timer.start()


def forget() -> None:
    with _lock:
        _loaded.clear()


# ---------------------------------------------------------------- drawing

def slots(key: str) -> list[str]:
    """The smart objects the baked template takes pictures for (front, back, spine, left, right, page1)."""
    a = _asset(key)
    return list(a["meta"]["slots"]) if a["kind"] == "multiply" else list(a["slots"])


def fills(key: str) -> dict:
    """A softcover scene's colour fills and the vendor's colours: name -> (r, g, b)."""
    a = _asset(key)
    return {name: rgb for name, (_, _, rgb) in a.get("fills", {}).items()}


def render(key: str, pictures: dict, colours: dict | None = None) -> Image.Image:
    """The mockup: pictures — slot -> PIL picture at the smart object's own size; colours — a softcover scene's fill
    -> (r, g, b) (the vendor's where left out). 8-bit RGB at the template's size."""
    import numpy as np
    a = _asset(key)
    pics = {s: np.asarray(im.convert("RGB"), np.float32) / 255 for s, im in pictures.items()}
    out = _render_multiply(a, pics) if a["kind"] == "multiply" else _render_linear(a, pics)
    if a.get("fills") and colours:
        out = _recolour(out, a, colours)
    return Image.fromarray(out, "RGB")


def _sample(img, m):
    import cv2
    import numpy as np
    h, w = img.shape[:2]
    return cv2.remap(img, (m["u"] * (w - 1)).astype(np.float32), (m["v"] * (h - 1)).astype(np.float32),
                     m.get("interp", cv2.INTER_LINEAR), borderMode=cv2.BORDER_REPLICATE)


def _render_linear(a, pics):
    import numpy as np
    out = a["k"].copy()
    for s, m in a["slots"].items():
        y0, y1, x0, x1 = m["box"]
        c = m["gain"] * _sample(pics[s], m)
        if "fold" in m:
            c[m["fold"]] = 0          # the corner's fold: drawn from the edge strips below
        out[y0:y1, x0:x1] += c
    for p in a["parts"]:
        y0, y1, x0, x1 = p["box"]
        c = p["gain"] * _sample(pics[p["slot"]], p)
        c[~p["fold"]] = 0
        out[y0:y1, x0:x1] += c
    for name, m in a["colours"].items():   # Dedication's desk and floor: the template's own colours
        y0, y1, x0, x1 = m["box"]
        out[y0:y1, x0:x1] += m["gain"] * (np.array(a["default_colours"][name], np.float32) / 255)
    return np.clip(np.round(out * 255), 0, 255).astype(np.uint8)


def _between(lo_knots, hi_knots, x):
    """Piecewise-linear: x placed among the increasing knots `lo_knots`, read off `hi_knots` (both (n, ...))."""
    import numpy as np
    n = lo_knots.shape[0]
    j = np.zeros(x.shape, np.int64)
    for i in range(1, n - 1):
        j += x >= lo_knots[i]
    lo = np.take_along_axis(lo_knots, j[None], 0)[0]
    hi = np.take_along_axis(lo_knots, j[None] + 1, 0)[0]
    a = np.take_along_axis(hi_knots, j[None], 0)[0]
    b = np.take_along_axis(hi_knots, j[None] + 1, 0)[0]
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.clip(np.where(hi > lo, (x - lo) / (hi - lo), 0), 0, 1)
    out = a + t * (b - a)
    out = np.where(x >= lo_knots[-1], hi_knots[-1], out)
    return np.where(x < lo_knots[0], hi_knots[0], out)


LEVELS = [i / 8 for i in range(9)]
ROW = 4096            # packed pixels go to cv2.remap as rows of this width (it takes no side over 32767)


def _render_multiply(a, pics):
    import cv2
    import numpy as np
    meta = a["meta"]
    y0, y1, x0, x1 = meta["box"]
    out = a["k"].astype(np.float32) / 65535
    box = out[y0:y1, x0:x1].reshape(-1, 3)
    interp, prescale = meta.get("interp") or {}, meta.get("prescale") or {}
    shrunk = {}
    for s in meta["slots"]:
        img = pics[s]
        pre = prescale.get(s)
        if pre:     # Photoshop shrinks a picture well before bending it: the same, by the slot's own squeeze
            f = pre[1]
            img = cv2.resize(img, (max(1, round(img.shape[1] * f)), max(1, round(img.shape[0] * f))),
                             interpolation=cv2.INTER_AREA)
        shrunk[s] = img
    idx = a["on"]
    step = ROW * CHUNK
    for c0 in range(0, len(idx), step):
        c1 = min(len(idx), c0 + step)
        n = c1 - c0
        rows = -(-n // ROW)
        alphas = a["alphas"][:, c0:c1].astype(np.float32) / 65535          # (S, n)
        P = np.ones((n, 3), np.float32)
        for i, s in enumerate(meta["slots"]):
            al = alphas[i]
            img = shrunk[s]
            ph, pw = img.shape[:2]
            uv = np.zeros((rows * ROW, 2), np.float32)
            uv[:n] = (a["uv"][i, c0:c1].astype(np.float32) - 16384) / 32768
            uv = uv.reshape(rows, ROW, 2)
            c = cv2.remap(img, uv[..., 0] * (pw - 1), uv[..., 1] * (ph - 1), interp.get(s, cv2.INTER_LINEAR),
                          borderMode=cv2.BORDER_REPLICATE).reshape(-1, 3)[:n]
            P *= 1 - al[:, None] + al[:, None] * c
        knots = np.stack([np.prod(1 - alphas + alphas * x, axis=0) for x in LEVELS])[..., None]   # (9, n, 1)
        base = box[idx[c0:c1]]
        L = np.concatenate([base[None], base[None] + a["rise"][:, c0:c1].astype(np.float32) / 255])  # (9, n, 3)
        box[idx[c0:c1]] = _between(np.broadcast_to(knots, L.shape), L, P)
    out[y0:y1, x0:x1] = box.reshape(y1 - y0, x1 - x0, 3)
    return np.clip(np.round(out * 255), 0, 255).astype(np.uint8)


def _recolour(img, a, colours: dict):
    """The scene's fills taken off (the vendor's colours) and put back in the chosen ones, where their masks show.
    Multiply: x * (1 - m + m c); Linear Burn: x + m (max(x + c - 1, 0) - x)."""
    import numpy as np
    fills, idx = a["fills"], a["fill_on"]
    flat = img.reshape(-1, 3)
    x = flat[idx].astype(np.float32) / 255
    order = [n for n in FILL_ORDER if n in fills]
    for name in reversed(order):
        mode, _, rgb = fills[name]
        m, c = a["fill_masks"][name][:, None].astype(np.float32) / 255, np.array(rgb, np.float32) / 255
        x = x / np.maximum(1 - m + m * c, 1e-3) if mode == "multiply" else x - m * (c - 1)
    for name in order:
        mode, _, rgb = fills[name]
        m = a["fill_masks"][name][:, None].astype(np.float32) / 255
        c = np.array(colours.get(name) or rgb, np.float32) / 255
        x = x * (1 - m + m * c) if mode == "multiply" else x + m * (np.maximum(x + c - 1, 0) - x)
    out = flat.copy()
    out[idx] = np.clip(np.round(x * 255), 0, 255).astype(np.uint8)
    if len(a["fill_plain"]):   # x + c_new - 1 where it was x + c_old - 1 (Photoshop's black clip aside)
        _, _, rgb = fills["Change Color"]
        shift = np.round(np.array(colours.get("Change Color") or rgb, np.float32) - np.array(rgb, np.float32))
        if shift.any():
            plain = a["fill_plain"]
            out[plain] = np.clip(flat[plain].astype(np.int16) + shift.astype(np.int16), 0, 255).astype(np.uint8)
    return out.reshape(img.shape)
