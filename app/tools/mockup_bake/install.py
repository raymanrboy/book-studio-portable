"""Puts baked mockup templates where Book Studio draws from (app/data/mockups/baked) — see studio/mockup_render.py.

    python app/tools/mockup_bake/install.py --from <folder with the bake's .npz> [--data <data folder>]

Takes open1.npz, open2.npz, cover1.npz, dedication.npz (the linear ones) and coverOpen-m.npz, allOpen-m.npz (the
multiply ones) as the bake left them; adds what drawing needs besides: Dedication's own desk and floor colours, the
softcover scenes' colour fills (mode, the vendor's colour, the mask — read from the template, only read), and the
stamp of the template file each was baked from (baked.json). Templates whose file is missing are skipped.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from pathlib import Path

APP = Path(__file__).resolve().parents[2]

# What the bake files are called, and the template each was baked from.
FILES = {"open1": ("open1.npz", "2. Open 1.psd"), "open2": ("open2.npz", "3. Open 2.psd"),
         "cover1": ("cover1.npz", "1. Cover 1.psd"), "dedication": ("dedication.npz", "4. Dedication.psd"),
         "coverOpen": ("coverOpen-m.npz", "Cover & Open 1.psd"), "allOpen": ("allOpen-m.npz", "All & Open 1.psd")}
# Dedication's flat-colour smart objects as the template has them (Main/Deck Color — the desk, Main/Background — the floor).
DEDICATION_COLOURS = {"desk": (139, 110, 52), "floor": (225, 225, 225)}
FILL_MODES = {"Change Color": "linear_burn", "Back Color": "multiply", "Front Color": "multiply"}


def read_fills(psd_path: Path) -> list:
    """[(name, mode, rgb, mask uint8 at the canvas size)] — the softcover scene's colour fill layers."""
    import numpy as np
    from psd_tools import PSDImage
    warnings.filterwarnings("ignore")
    psd = PSDImage.open(psd_path)
    W, H = psd.size
    out = []
    for layer in psd:
        if layer.kind != "solidcolorfill" or layer.name not in FILL_MODES or not layer.visible:
            continue
        clr = layer.tagged_blocks.get_data(b"SoCo")[b"Clr "]
        rgb = [round(float(clr[k]), 3) for k in (b"Rd  ", b"Grn ", b"Bl  ")]
        m = layer.mask
        full = np.full((H, W), m.background_color, np.uint8)
        im = np.asarray(m.topil())
        x0, y0, x1, y1 = max(m.left, 0), max(m.top, 0), min(m.right, W), min(m.bottom, H)
        full[y0:y1, x0:x1] = im[y0 - m.top:y1 - m.top, x0 - m.left:x1 - m.left]
        out.append((layer.name, FILL_MODES[layer.name], rgb, full))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--from", dest="src", required=True, type=Path)
    ap.add_argument("--data", type=Path, default=APP / "data")
    ap.add_argument("--templates", type=Path, default=APP.parent.parent / "runtime" / "Templates")
    args = ap.parse_args()
    os.environ["BOOK_STUDIO_DATA"] = str(args.data.resolve())     # before studio is imported (data safety)
    sys.path.insert(0, str(APP))
    import numpy as np
    from studio import mockup_render as R

    R.BAKED.mkdir(parents=True, exist_ok=True)
    stamps = R._stamps_file()
    for key, (name, psd_name) in FILES.items():
        src, psd = args.src / name, args.templates / psd_name
        if not src.is_file() or not psd.is_file():
            print(f"{key}: skipped ({'no ' + name if not src.is_file() else 'no template ' + psd_name})")
            continue
        z = np.load(src)
        arrays = {n: z[n] for n in z.files if n != "meta"}
        meta = json.loads(z["meta"].tobytes())
        if key == "dedication":
            meta["default_colours"] = DEDICATION_COLOURS
        if "rise" in arrays:
            fills = read_fills(psd)
            meta["fills"] = [[n, mode, rgb] for n, mode, rgb, _ in fills]
            for i, (_, _, _, mask) in enumerate(fills):
                arrays[f"fill{i}"] = mask
        part = R.BAKED / f"{key}.part.npz"
        np.savez_compressed(part, meta=np.frombuffer(json.dumps(meta).encode(), np.uint8), **arrays)
        part.replace(R.BAKED / f"{key}.npz")
        stamps[key] = {"stamp": R.stamp(psd), "template": psd_name, "from": name}
        print(f"{key}: {(R.BAKED / f'{key}.npz').stat().st_size / 1e6:.1f} MB")
    (R.BAKED / R.STAMPS).write_text(json.dumps(stamps, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
