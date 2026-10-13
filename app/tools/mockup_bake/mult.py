"""The softcover scenes (Cover & Open 1, All & Open 1): their pictures overlap and multiply into each other (the open
book lies over the closed one's cover, the left page runs under the right one), and the layers over them bend the
tones (Soft Light, Colour/Linear Burn). Per pixel and channel:

    P   = product over slots of (1 - a_s + a_s * c_s(u_s, v_s))      a_s — how much of the pixel slot s covers
    out = F(P)                                                        F — the pixel's tone curve

F is measured with every slot at one flat level x (P = product of (1 - a_s + a_s x)); a_s from the slot black and the
rest white (P = 1 - a_s); u_s, v_s from the slot's coordinate ramp with the rest white. White is neutral for Multiply,
so a slot is seen even where another lies over it.
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

import engine as E

EPS = 0.004
CHUNK = 384


def _load(p):
    return E._load(p)


def _inverse(Lc, Pc, obs):
    """P with F(P) = obs; Lc, Pc: (n, ...) increasing knots of one channel; obs: (...)."""
    n = Lc.shape[0]
    out = np.where(obs >= Lc[-1], Pc[-1], Pc[0]).astype(np.float32)
    for j in range(n - 1):
        lo, hi = Lc[j], Lc[j + 1]
        inside = (obs >= lo) & (obs < hi)
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(hi > lo, (obs - lo) / (hi - lo), 0)
        out = np.where(inside, Pc[j] + t * (Pc[j + 1] - Pc[j]), out)
    return out


def _forward(Lc, Pc, P):
    n = Lc.shape[0]
    out = np.where(P >= Pc[-1], Lc[-1], Lc[0]).astype(np.float32)
    for j in range(n - 1):
        lo, hi = Pc[j], Pc[j + 1]
        inside = (P >= lo) & (P < hi)
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(hi > lo, (P - lo) / (hi - lo), 0)
        out = np.where(inside, Lc[j] + t * (Lc[j + 1] - Lc[j]), out)
    return out


def _knots(alphas, levels):
    """P at each level: product over slots of (1 - a + a x). alphas: (S, h, w) -> (n, h, w)."""
    return np.stack([np.prod(1 - alphas + alphas * x, axis=0) for x in levels])


def despeckle(rel, size, valid, limit=1.0, rounds=3):
    """The picture position is smooth (perspective, a gentle bend); a pixel that points far from its neighbours
    (the paper's grain read back through a flat part of the curve) takes its neighbours' median."""
    out = rel.copy()
    for ch, n in enumerate(size):
        x = (out[..., ch] * (n - 1)).astype(np.float32)
        for _ in range(rounds):
            med = cv2.medianBlur(x, 5)
            bad = valid & (np.abs(x - med) > limit)
            if not bad.any():
                break
            x = np.where(bad, med, x)
        out[..., ch] = x / (n - 1)
    return out


def smooth(rel, valid, sigma=6.0):
    """Photoshop hands some slots' coordinate ramp through at 8 bits (steps of 1/256 of the page, All & Open 1's
    open spread): the true position is smooth (a perspective), so the steps are evened out — a Gaussian inside
    the slot only (normalised, so the slot's edge is not pulled towards zero)."""
    w = valid.astype(np.float32)
    den = cv2.GaussianBlur(w, (0, 0), sigma)
    out = rel.copy()
    for ch in range(rel.shape[-1]):
        num = cv2.GaussianBlur(rel[..., ch] * w, (0, 0), sigma)
        out[..., ch] = np.where(valid & (den > 1e-3), num / np.maximum(den, 1e-3), rel[..., ch])
    return out


def bake(key: str, renders: Path, asset: Path) -> dict:
    t = E.TEMPLATES[key]
    slots = list(t["slots"])
    K, W = _load(renders / "black.png"), _load(renders / "all-white.png")
    on = (W - K).max(-1) > EPS
    ys, xs = np.nonzero(on)
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1
    box = (y0, y1, x0, x1)
    levels = E.LEVELS
    L = [K[y0:y1, x0:x1]]
    for x in levels[1:-1]:
        L.append(_load(renders / ("grey.png" if x == 0.5 else f"{E.level_name(x)}.png"))[y0:y1, x0:x1])
    L.append(W[y0:y1, x0:x1])
    L = np.maximum.accumulate(np.stack(L), axis=0)              # (n, h, w, 3) rising
    Bk = np.stack([_load(renders / f"bkw-{s}.png")[y0:y1, x0:x1] for s in slots])
    Uv = np.stack([_load(renders / f"uvw-{s}.png")[y0:y1, x0:x1, :2] for s in slots])
    Kb, Wb = K[y0:y1, x0:x1], W[y0:y1, x0:x1]
    span = np.maximum(Wb - Kb, 1e-6)
    alphas = np.clip(((Wb[None] - Bk) / span[None]).mean(-1), 0, 1)        # first guess (straight-line tones)
    alphas[:, ~on[y0:y1, x0:x1]] = 0
    for _ in range(3):                                                     # through the curve
        P = _knots(alphas, levels)
        new = []
        for i in range(len(slots)):
            est = np.mean([_inverse(L[..., ch], P, Bk[i, ..., ch]) for ch in range(3)], axis=0)
            new.append(np.clip(1 - est, 0, 1))
        alphas = np.where(alphas > 0, np.stack(new), 0)
    P = _knots(alphas, levels)
    uvs = []
    for i in range(len(slots)):
        a = alphas[i]
        rel = []
        for ch in range(2):
            Pu = _inverse(L[..., ch], P, Uv[i, ..., ch])
            with np.errstate(divide="ignore", invalid="ignore"):
                rel.append(np.where(a > 0.02, (Pu - (1 - a)) / a, 0))
        size = t["slots"][slots[i]][1]
        uvs.append(smooth(np.stack(rel, -1), a > 0.5))
    out = {"key": key, "box": box, "k": K, "levels": L, "alphas": alphas, "uv": np.stack(uvs), "slots": slots}
    save(out, asset)
    return out


def save(a, path: Path):
    """Only what the book covers is kept: the curve as rises over its black (zero off the book — packs to nothing),
    the slots' positions only where they show."""
    meta = {"key": a["key"], "box": a["box"], "slots": a["slots"], "interp": a.get("interp", {}), "blur": a.get("blur", {}),
            "prescale": a.get("prescale", {})}
    on = a["alphas"].max(0) > EPS
    rise = np.where(on[None, ..., None], a["levels"][1:] - a["levels"][:1], 0)
    uv = np.where((a["alphas"] > EPS)[..., None], np.clip(a["uv"], -0.5, 1.5), 0)
    np.savez_compressed(path, meta=np.frombuffer(json.dumps(meta).encode(), np.uint8),
                        k=np.round(a["k"] * 65535).astype(np.uint16),
                        rise=np.round(np.clip(rise, 0, 1) * 255).astype(np.uint8),
                        alphas=np.round(a["alphas"] * 65535).astype(np.uint16),
                        uv=np.round(uv * 32768 + 16384).astype(np.uint16))


def load(path: Path) -> dict:
    z = np.load(path)
    meta = json.loads(z["meta"].tobytes())
    k = z["k"].astype(np.float32) / 65535
    y0, y1, x0, x1 = meta["box"]
    base = k[y0:y1, x0:x1][None]
    rise = z["rise"].astype(np.float32) / (255 if z["rise"].dtype == np.uint8 else 65535)
    levels = np.concatenate([base, base + rise])
    return {**meta, "k": k, "levels": levels, "alphas": z["alphas"].astype(np.float32) / 65535,
            "uv": (z["uv"].astype(np.float32) - 16384) / 32768}


def render(a, pictures: dict) -> np.ndarray:
    y0, y1, x0, x1 = a["box"]
    out = a["k"].copy()
    h = y1 - y0
    interp = a.get("interp", {})
    for r0 in range(0, h, CHUNK):
        r1 = min(h, r0 + CHUNK)
        alphas = a["alphas"][:, r0:r1]
        P = np.ones((r1 - r0, x1 - x0, 3), np.float32)
        for i, s in enumerate(a["slots"]):
            al = alphas[i]
            if not (al > EPS).any():
                continue
            img = pictures[s]
            sigma = a.get("blur", {}).get(s, 0)
            if sigma:      # a slot Photoshop softens before it bends it (All & Open 1's open spread)
                img = cv2.GaussianBlur(img, (0, 0), sigma)
            pre = a.get("prescale", {}).get(s)
            if pre:        # Photoshop shrinks the picture well before bending it: the same, by the slot's own squeeze
                kind, f = pre
                img = cv2.resize(img, (max(1, round(img.shape[1] * f)), max(1, round(img.shape[0] * f))),
                                 interpolation={"area": cv2.INTER_AREA, "lanczos": cv2.INTER_LANCZOS4, "cubic": cv2.INTER_CUBIC}[kind])
            ph, pw = img.shape[:2]
            uv = a["uv"][i, r0:r1]
            c = cv2.remap(img, (uv[..., 0] * (pw - 1)).astype(np.float32), (uv[..., 1] * (ph - 1)).astype(np.float32),
                          interp.get(s, cv2.INTER_LINEAR), borderMode=cv2.BORDER_REPLICATE)
            P *= 1 - al[..., None] + al[..., None] * c
        knots = _knots(alphas, E.LEVELS)
        L = a["levels"][:, r0:r1]
        res = np.stack([_forward(L[..., ch], knots, P[..., ch]) for ch in range(3)], -1)
        out[y0 + r0:y0 + r1, x0:x1] = res
    return np.clip(np.round(out * 255), 0, 255).astype(np.uint8)


def register(a, checks):
    """Photoshop's own check renders show these scenes placed ~0.3–1.5 px off from the calibration (the same for every
    book; the cause not found): per slot a smooth (affine) shift field, fitted to the optical flow between ours and
    Photoshop's over all checks, moves the picture positions. Returns the shift at each slot's middle."""
    y0, y1, x0, x1 = a["box"]
    yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0].astype(np.float32)
    A = np.stack([np.ones_like(xx), xx / 1000, yy / 1000], -1).reshape(-1, 3)
    flows, texs = [], []
    for pictures, truth in checks:
        g1 = cv2.cvtColor(truth.astype(np.uint8), cv2.COLOR_RGB2GRAY)
        g2 = cv2.cvtColor(render(a, pictures), cv2.COLOR_RGB2GRAY)
        flows.append(cv2.calcOpticalFlowFarneback(g1, g2, None, 0.5, 4, 31, 5, 7, 1.5, 0)[y0:y1, x0:x1])
        texs.append(np.abs(cv2.Laplacian(cv2.GaussianBlur(g1, (0, 0), 2).astype(np.float32), cv2.CV_32F))[y0:y1, x0:x1])
    shifts = {}
    uv = a["uv"].copy()
    for i, s in enumerate(a["slots"]):
        core = cv2.erode((a["alphas"][i] > 0.9).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
        if core.sum() < 1000:
            continue
        rows, bx, by = [], [], []
        for f, t in zip(flows, texs):
            w = np.sqrt(np.where(core, t, 0).ravel())[:, None]
            rows.append(A * w); bx.append(f[..., 0].ravel() * w[:, 0]); by.append(f[..., 1].ravel() * w[:, 0])
        Aw = np.concatenate(rows)
        cx = np.linalg.lstsq(Aw, np.concatenate(bx), rcond=None)[0]
        cy = np.linalg.lstsq(Aw, np.concatenate(by), rcond=None)[0]
        fx, fy = (A @ cx).reshape(xx.shape), (A @ cy).reshape(xx.shape)
        for ch in range(2):
            uv[i, ..., ch] = cv2.remap(a["uv"][i, ..., ch], xx + fx, yy + fy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        shifts[s] = (round(float(fx[core].mean()), 2), round(float(fy[core].mean()), 2))
    a["uv"] = uv
    return shifts
