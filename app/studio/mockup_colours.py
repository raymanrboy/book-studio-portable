"""The colours of the softcover scenes (Cover & Open 1, All & Open 1) taken from the book's own cover.

The owner (13.10.2026): the colour of the open book's edges is taken from the matching parts of the cover — its edges,
"as with an eyedropper"; the background he picks himself, and a suggestion of the best pastel shade would be welcome.
    edges(cover)     the front half's and the back half's colour along their outer edges
    pastels(cover)   light, soft shades of the cover's own leading hues (the first is the one used unless he picks)
Colours travel as "#rrggbb".
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

EDGE = 0.025          # the strip along an edge the colour is read from: this share of the half's width
LIGHT, SOFT = 0.93, 0.045   # a pastel: OKLCH lightness and chroma
NEUTRAL = (0.945, 0.012, 75.0)   # a warm off-white: always among the suggestions


def hex_of(rgb) -> str:
    return "#" + "".join(f"{max(0, min(255, round(v))):02x}" for v in rgb)


def rgb_of(text: str) -> tuple[int, int, int] | None:
    t = str(text or "").strip().lstrip("#")
    if len(t) != 6:
        return None
    try:
        return int(t[0:2], 16), int(t[2:4], 16), int(t[4:6], 16)
    except ValueError:
        return None


def _small(path: Path, width: int = 320):
    import numpy as np
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((width, width))
        return np.asarray(im, np.float32) / 255


def edges(cover: Path) -> dict[str, str]:
    """{"front": hex, "back": hex}: the median colour along the outer edges of each half of the wide cover (back on the
    left, front on the right): top, bottom and the outer side — not the spine's."""
    import numpy as np
    a = _small(cover, 640)
    h, w = a.shape[:2]
    half = w // 2
    d = max(1, round(half * EDGE))
    back = np.concatenate([a[:d, :half].reshape(-1, 3), a[-d:, :half].reshape(-1, 3), a[:, :d].reshape(-1, 3)])
    front = np.concatenate([a[:d, half:].reshape(-1, 3), a[-d:, half:].reshape(-1, 3), a[:, -d:].reshape(-1, 3)])
    return {"front": hex_of(np.median(front, 0) * 255), "back": hex_of(np.median(back, 0) * 255)}


# ---------------------------------------------------------------- OKLab (Björn Ottosson)

def _to_linear(c):
    import numpy as np
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _from_linear(c):
    import numpy as np
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def _oklab(rgb):
    import numpy as np
    r, g, b = np.moveaxis(_to_linear(rgb), -1, 0)
    l = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return np.stack([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                     1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                     0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s], -1)


def _rgb_from_oklch(L, C, h_deg):
    """sRGB 0..1 and whether it fits without clipping."""
    import numpy as np
    h = np.radians(h_deg)
    a, b = C * np.cos(h), C * np.sin(h)
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    lin = np.array([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
                    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                    -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s])
    return _from_linear(lin), bool(np.all(lin >= -1e-4) and np.all(lin <= 1 + 1e-4))


def _pastel(L, C, h) -> str:
    while C > 0:
        rgb, fits = _rgb_from_oklch(L, C, h)
        if fits:
            return hex_of(rgb * 255)
        C -= 0.004
    return hex_of(_rgb_from_oklch(L, 0, h)[0] * 255)


def pastels(cover: Path, count: int = 4) -> list[str]:
    """Up to `count` pastel shades: the cover's leading hues (weighted by how much of the cover they colour and how
    strongly), each made light and soft; a warm off-white closes the list."""
    import numpy as np
    lab = _oklab(_small(cover)).reshape(-1, 3)
    chroma = np.hypot(lab[:, 1], lab[:, 2])
    hue = (np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) + 360) % 360
    keep = chroma > 0.03
    out = []
    if keep.any():
        hist, _ = np.histogram(hue[keep], bins=36, range=(0, 360), weights=chroma[keep])
        smooth = np.convolve(np.concatenate([hist[-2:], hist, hist[:2]]), [1, 2, 3, 2, 1], "valid")
        taken: list[float] = []
        for i in np.argsort(smooth)[::-1]:
            if smooth[i] < smooth.max() * 0.08 or len(taken) >= count - 1:
                break
            # the peak's own mean hue, from the pixels of its 30° around
            centre = i * 10 + 5
            near = keep & (np.abs((hue - centre + 180) % 360 - 180) <= 15)
            h = float(np.degrees(np.arctan2(lab[near, 2].mean(), lab[near, 1].mean())) % 360) if near.any() else centre
            if all(abs((h - t + 180) % 360 - 180) >= 35 for t in taken):
                taken.append(h)
        out = [_pastel(LIGHT, SOFT, h) for h in taken]
    out.append(_pastel(*NEUTRAL))
    return list(dict.fromkeys(out))[:count]
