"""«Обкладинка» — the cover's own tool (the owner, 2026-10-25), its «Два квадрати» way: the back and the front generated
as two squares — each with a layout guide picture attached (where the title, the name's room and the scene go) and,
for the front, the book's best frame as the reference — then laid on Gelato's 8×8 hardcover template by Book Studio
itself, no generator: the spine and the wrap are filled from the colours along the squares' edges (a 4 mm ring;
what is inside never tints them), smoothly from the back's to the front's, and the squares go on top with a soft edge.

The choices of the book live in book.json under "coverSquares": {"feather": mm, "guides": {side: guide}, "ref": spread}.
The guides are pictures of the program (web/img/cover-guides/); their words for the prompt are GUIDES below.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from .. import core
from ..server import ApiError
from . import books
from .rows import SQUARE_KEYS, SQUARES, original_of

GUIDE_DIR = core.WEB_DIR / "img" / "cover-guides"
FILL_K, RING_MM = 2, 4                     # the fill is worked out at 2 px/mm from a 4 mm ring along each edge
FEATHERS = (0, 2, 4, 6)                    # the soft edge of the squares, mm

_DONT_DRAW = ("Follow its proportions and positions exactly, but never draw its flat shapes, colors or edges — "
              "paint the real picture there.")
# name: (side, label, what goes where — for the prompt's "layout_guide"; {n} is the guide's number among the pictures)
GUIDES = {
    "front-title-scene": ("cover-front", "Назва й сцена",
                          "Image {n} is ONLY a layout guide for where things go: the brown-grey shape at the top is where "
                          "the title lettering goes, the plain cream gap under it is the open room, the big green-grey "
                          "shape is where the scene and the characters go. " + _DONT_DRAW),
    "front-title-name-scene": ("cover-front", "Назва, під нею ім'я, сцена",
                               "Image {n} is ONLY a layout guide for where things go: the brown-grey shape at the top is "
                               "where the title lettering goes; the pale blue shape under it is open room — keep it "
                               "plain cream paper, paint nothing there; the big green-grey shape is where the scene and "
                               "the characters go. " + _DONT_DRAW),
    "front-name-title-scene": ("cover-front", "Ім'я над назвою, сцена",
                               "Image {n} is ONLY a layout guide for where things go: the pale blue shape at the very "
                               "top is open room — keep it plain cream paper, paint nothing there; the brown-grey shape "
                               "under it is where the title lettering goes; the big green-grey shape is where the scene "
                               "and the characters go. " + _DONT_DRAW),
    "front-scene": ("cover-front", "Тільки сцена",
                    "Image {n} is ONLY a layout guide for where the scene goes: the big green-grey shape is where the "
                    "scene and the characters go; the plain cream above it is for the title and the open room, as the "
                    "prompt describes. " + _DONT_DRAW),
    "back-scene": ("cover-back", "Сцена, верх відкритий",
                   "Image {n} is ONLY a layout guide for where things go: the big green-grey shape is where the scene "
                   "goes, the plain cream above it stays open. " + _DONT_DRAW),
}
DEFAULT_GUIDES = {"cover-front": "front-title-scene", "cover-back": "back-scene"}


# ---------------------------------------------------------------- the book's choices

def settings(path: Path) -> dict:
    raw = books.state(path).get("coverSquares") or {}
    guides = {**DEFAULT_GUIDES, **{k: v for k, v in (raw.get("guides") or {}).items()
                                   if k in SQUARE_KEYS and v in GUIDES and GUIDES[v][0] == k}}
    feather = raw.get("feather", 2)
    return {"feather": feather if feather in FEATHERS else 2, "guides": guides, "ref": str(raw.get("ref") or "")}


def set_settings(book_id: str, body: dict) -> dict:
    """The tool's choices: the soft edge, a side's guide, the front's reference (a spread, or none). A new soft edge
    makes the cover again at once."""
    from . import pictures
    path = books.book_path(book_id)
    now = settings(path)
    if "feather" in body:
        if body["feather"] not in FEATHERS:
            raise ApiError("Невідомий м'який край.")
        now["feather"] = body["feather"]
    if body.get("guide"):
        side, name = str(body.get("side") or ""), str(body["guide"])
        if side not in SQUARE_KEYS or name not in GUIDES or GUIDES[name][0] != side:
            raise ApiError("Ця схема не для цієї сторони.")
        now["guides"][side] = name
    if "ref" in body:
        ref = str(body["ref"] or "")
        if ref not in ("", "none") and not (ref.startswith("spread") and ref[6:].isdigit()):
            raise ApiError("Референсом може бути тільки розворот книги.")
        now["ref"] = ref
    books.update_state(path, lambda data: data.__setitem__("coverSquares", now))
    if "feather" in body or body.get("assemble"):
        with pictures.WRITING:
            assemble(path)
    return now


def tool_state(path: Path, rows: list[dict]) -> dict:
    """What the page needs: the guides (each side's), the book's choices, the spreads that can be the reference."""
    return {"settings": settings(path), "feathers": list(FEATHERS),
            "guides": [{"name": n, "side": side, "label": label, "src": f"/img/cover-guides/{n}.png"}
                       for n, (side, label, _) in GUIDES.items()],
            "refs": [{"key": r["key"], "label": r["label"], "page": r["pictures"][0]}
                     for r in rows if r["kind"] == "spread" and r["pictures"]]}


def reference(detail: dict, st: dict) -> dict:
    """The front's reference: a spread the owner picked; «none»; else (by default) the picture Agent 6 named in the
    prompt and put into agent/ («Референс у буфер», 24.10.2026), if there is one."""
    ref = st["ref"]
    if ref.startswith("spread") and any(r["key"] == ref and r["pictures"] for r in detail["rows"]):
        return {"spread": ref}
    if ref != "none" and (detail["cover"].get("refs") or {}).get("cover-front"):
        return {"agent": detail["cover"]["refs"]["cover-front"]}
    return {}


# ---------------------------------------------------------------- the prompt and the clipboard

def prompt_with_guide(prompt: str, guide: str, n: int, referenced: bool = True) -> str:
    """Agent 6's prompt with the guide's words put in, right after the reference's rule (where the pictures are named).
    No reference picture pasted: the prompt names none — else «the attached image» would be the guide."""
    words = GUIDES[guide][2].format(n=n)
    try:
        obj = json.loads(prompt)
    except json.JSONDecodeError:
        return f"{prompt}\n\nlayout_guide: {words}"
    if not referenced:
        obj = {k: v for k, v in obj.items() if k not in ("reference_image", "reference_rule")}
    anchor = next((k for k in ("reference_rule", "canvas") if k in obj), None)
    out = {}
    for k, v in obj.items():
        if k == "layout_guide":
            continue
        out[k] = v
        if k == anchor:
            out["layout_guide"] = words
    if anchor is None:
        out["layout_guide"] = words
    return json.dumps(out, indent=2, ensure_ascii=False)


def items(book_id: str, key: str, detail: dict) -> tuple[str, list[dict]]:
    """What a square's «Генерувати» pastes, in order: the front — the reference (the chosen spread), the guide, the
    prompt; the back — the finished front (its look to match), the guide, the prompt."""
    path = books.book_path(book_id)
    c = detail["cover"]
    side = "лицьова" if key == "cover-front" else "задня"
    prompt = (c.get("prompts") or {}).get(key)
    if not prompt:
        ids = {"cover-front": "title-square", "cover-back": "quiet-square"}
        raise ApiError(f"Обкладинка · {side}: промпту ще немає — його пише агент 6 (id «{ids[key]}»).")
    st = settings(path)
    pics: list[dict] = []
    if key == "cover-front":
        ref = reference(detail, st)
        if ref.get("spread"):
            pics.append({"kind": "image", "label": "референс", "spread": ref["spread"]})
        elif ref.get("agent"):
            pics.append({"kind": "image", "label": "референс", "path": str(path / books.AGENT / ref["agent"])})
    if key == "cover-back":
        if not c.get("front"):
            raise ApiError("Спершу лицьова сторона — задня генерується з нею, щоб збігся стиль.")
        pics.append({"kind": "image", "label": "лицьова сторона", "path": str(path / books.ORIGINALS / c["front"])})
    guide = st["guides"][key]
    referenced = bool(pics)
    pics.append({"kind": "image", "label": "схема", "path": str(GUIDE_DIR / f"{guide}.png")})
    return f"Обкладинка · {side}", pics + [{"kind": "text", "label": "промпт",
                                            "text": prompt_with_guide(prompt, guide, len(pics), referenced)}]


# ---------------------------------------------------------------- the cover, made of the two squares

def _push_pull(p: np.ndarray, a: np.ndarray) -> np.ndarray:
    """p: premultiplied H×W×3, a: H×W in [0, 1] → every pixel filled from its neighbourhood (averaged down level by
    level to one pixel, then filled back up, each level from the smoothly sampled one above)."""
    levels = [(p, a)]
    while levels[-1][1].shape[0] > 1 or levels[-1][1].shape[1] > 1:
        p, a = levels[-1]
        h, w = a.shape
        ph, pw = h + h % 2, w + w % 2
        pp = np.zeros((ph, pw, 3), np.float32)
        pp[:h, :w] = p
        aa = np.zeros((ph, pw), np.float32)
        aa[:h, :w] = a
        ps = pp.reshape(ph // 2, 2, pw // 2, 2, 3).sum((1, 3))
        asum = aa.reshape(ph // 2, 2, pw // 2, 2).sum((1, 3))
        over = asum > 1
        ps[over] /= asum[over][:, None]
        asum[over] = 1
        levels.append((ps, asum))
    p, a = levels[-1]
    col = p / a[..., None] if a[0, 0] > 0 else np.full_like(p, 245)
    for p, a in reversed(levels[:-1]):
        h, w = a.shape
        ch, cw = col.shape[:2]
        fy = np.clip((np.arange(h) + 0.5) / 2 - 0.5, 0, ch - 1)
        fx = np.clip((np.arange(w) + 0.5) / 2 - 0.5, 0, cw - 1)
        y0, x0 = np.floor(fy).astype(int), np.floor(fx).astype(int)
        y1, x1 = np.minimum(y0 + 1, ch - 1), np.minimum(x0 + 1, cw - 1)
        ay, ax = (fy - y0)[:, None, None], (fx - x0)[None, :, None]
        up = ((col[y0][:, x0] * (1 - ax) + col[y0][:, x1] * ax) * (1 - ay)
              + (col[y1][:, x0] * (1 - ax) + col[y1][:, x1] * ax) * ay)
        col = p + (1 - a)[..., None] * up
    return col


def _box_blur(c: np.ndarray, r: int) -> np.ndarray:
    for axis in (1, 0):
        pad = [(0, 0)] * 3
        pad[axis] = (r, r)
        cs = np.cumsum(np.pad(c, pad, mode="edge"), axis)
        cs = np.concatenate([np.zeros_like(np.take(cs, [0], axis)), cs], axis)
        n = c.shape[axis]
        c = (np.take(cs, range(2 * r + 1, 2 * r + 1 + n), axis) - np.take(cs, range(n), axis)) / (2 * r + 1)
    return c


def _square(path: Path) -> Image.Image:
    from .pictures import open_picture, square
    im, _ = square(open_picture(path, path.name))
    return im.convert("RGB")


def compose(back: Image.Image, front: Image.Image, feather_mm: float) -> Image.Image:
    """The two squares on Gelato's spread (458×246 mm, 300 dpi), the rest filled from their edges."""
    w_mm, h_mm = SQUARES["mm"]
    ppmm = SQUARES["dpi"] / 25.4
    places = [(back, SQUARES["back"]), (front, SQUARES["front"])]
    fw, fh = w_mm * FILL_K, h_mm * FILL_K
    small = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    for im, (x, y, side) in places:
        s, b = side * FILL_K, RING_MM * FILL_K
        sq = im.resize((s, s), Image.LANCZOS).convert("RGBA")
        ring = Image.new("L", (s, s), 255)
        ring.paste(0, (b, b, s - b, s - b))
        sq.putalpha(ring)
        small.alpha_composite(sq, (x * FILL_K, y * FILL_K))
    arr = np.asarray(small, np.float32)
    a = arr[..., 3] / 255
    fill = _push_pull(arr[..., :3] * a[..., None], a)
    for _ in range(2):                     # ~1.5 mm, twice: no blocks left
        fill = _box_blur(fill, 3)
    out = Image.fromarray(np.clip(fill, 0, 255).astype(np.uint8)).resize(
        (round(w_mm * ppmm), round(h_mm * ppmm)), Image.BICUBIC)
    for im, (x, y, side) in places:
        s, f = round(side * ppmm), feather_mm * ppmm
        mask = None
        if f >= 1:
            mask = Image.new("L", (s, s), 0)
            mask.paste(255, (round(f), round(f), s - round(f), s - round(f)))
            mask = mask.filter(ImageFilter.GaussianBlur(f / 2))
        out.paste(im.resize((s, s), Image.LANCZOS), (round(x * ppmm), round(y * ppmm)), mask)
    out.info["dpi"] = (SQUARES["dpi"], SQUARES["dpi"])
    return out


def assemble(path: Path) -> bool:
    """Both squares there → pictures/Cover.png made of them (the one before goes to .replaced); False while one is
    missing (nothing changes). The caller holds pictures.WRITING."""
    from . import pictures
    from .rows import cover_mode
    folder = path / books.ORIGINALS
    names = books._names(folder)
    found = {k: original_of(names, k) for k in SQUARE_KEYS}
    if not all(found.values()) or cover_mode(path) != "squares":
        return False  # a 2:1 book keeps its cover
    st = settings(path)
    out = compose(_square(folder / found["cover-back"]), _square(folder / found["cover-front"]), st["feather"])
    pictures._save(path, out, pictures._pictures_dir(path, None) / "Cover.png")
    pictures._mark(path, None, "cover-wrap", {"squares": True, "skipped": False, "feather": st["feather"],
                                              "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "pic": core.new_id()[:12],
                                              "upscaled": None, "cut": "", "from": "", "source": list(out.size)})
    return True
