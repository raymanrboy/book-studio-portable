---
title: Mockups engine
type: feature
updated: 2026-11-12
code:
  - app/studio/mockups.py
  - app/studio/mockup_render.py
  - app/studio/mockups.jsx
  - app/tools/mockup_bake/bake.py
  - app/tools/mockup_bake/engine.py
  - app/tools/mockup_bake/mult.py
  - app/tools/mockup_bake/install.py
  - app/tools/mockup_bake/bake.jsx
---
# Mockups engine

> How the six templates are drawn: the template table, the layers, the baked files, the picture sizes and the run order. The tool's flow and the crop window are in [mockups.md](mockups.md).

## Templates

Folder `runtime/Templates` (`mockups.TEMPLATES_DIR`) — read-only, never edited, saved over or moved ([security](../security.md)). The six `.psd` files are 300 ppi, 8-bit RGB, every smart object 300 ppi. The same folder holds `Cover.png`, `Shelf.png`, `Size.jpg` — flat examples, not part of the tool. `TEMPLATES` in `mockups.py` lists the keys, files and layers; the table below is in run order (`RUN_ORDER`).

| Key | File | In the picture | Spreads | Layers filled → inner size |
|---|---|---|---|---|
| `open1` | `2. Open 1.psd` | open hardcover, flat (4000×2670) | 4 | `Main/Left`, `Main/Right` → 1900²; `Main/Cover`, `Main/Back Cover` → 2100×2200; `Main/Rige` (spine) → 80×2200 |
| `open2` | `3. Open 2.psd` | open hardcover at an angle | 2 | same names and sizes |
| `cover1` | `1. Cover 1.psd` | closed hardcover from above (2670²) | — | `Main/COVER_` → 2100×2200 |
| `coverOpen` | `Cover & Open 1.psd` | closed + open softcover (4000×3000) | 1 | `Left Page`, `Right Page` → 1935²; front cover `Front Cover` |
| `allOpen` | `All & Open 1.psd` | five softcovers: front, back, laid-open cover, open spread | 1 | `Back Cover`, `Left `, `Right ` → 1935²; `Spine` → 164×1935; `Front Cover` |
| `dedication` | `4. Dedication.psd` | open on the dedication | — | `Main/Page 1` → 1900²; `Cover`, `Back Cover`, `Rige` as Open 1 |

- Two vendors. Hardcover files (A) have groups `PRESENTATIONS / VIEW_xx / BOOK / OBJECT / SMART OBJECTS`, plus `ITEMS` and `FILTERS`; a group `Main` at the bottom holds hidden linked copies of the smart objects that matter. Softcover files (B) have `Editable Layers / Design Smart Objects / Reflection / Shadow` and colour layers `Change Color`, `Back Color`, `Front Color`; no `Main`.
- Layer names are not uniform: the front cover is `COVER_` / `Cover` / `Front Cover`; pages `Left` / `Left Page` / `Left ` (trailing space in `All & Open 1`); the spine `Rige` (A) or `Spine` (B). Paths are compared with spaces trimmed.
- One content id can sit in several layers (in `All & Open 1`, `Front Cover`, `Back Cover` and `Spine` appear twice); replacing one updates all.
- In the open-book templates the cover shows only as a thin rim around the pages.
- Never touched: `BACKGROUND`, `BACKGROUND_desk color`, `PAPER_edge color`, `SHADOW_editable`, `LIGHT_editable`, the pages under the spread, `SELECTIVE VARNISH`.

## Picture sizes

Pictures are cut by Pillow at the smart object's exact size, 300 dpi (`cover_pictures()`, `page_picture()`): the back is the left half of the wide cover, the front (and the rims) the right half, each filling its board centred; the spine is the strip from the middle; pages fill the square.

| Kind | page | board | spine |
|---|---|---|---|
| Hardcover (`HARD`) | 1900² | 2100×2200 | 80×2200 |
| Softcover (`SOFT`) | 1935² | 1935² | 164×1935 |

## Baked templates

Each template is baked once; a run then draws from the baked files.

- Files: `app/data/mockups/baked/<key>.npz` for all six keys plus `baked.json`, the stamp of the template file each was baked from (`mockup_render.stamp()`: size and the first and last 4 MB). `mockup_render.ready()` compares it; `mockups.drawn()` is true only when every ticked template is ready.
- **A changed template is not drawn**: its run falls to the [Photoshop fallback](#photoshop-fallback) until it is baked again.
- **Hardcovers** (Open 1, Open 2, Cover 1, Dedication — "linear"): `out = black + Σ gain × picture(uv)`. Board corner folds come from the picture's four edge strips; bilinear or bicubic per smart object, whichever is closer to Photoshop. Dedication's desk and floor are flat-colour smart objects at the template's colours.
- **Softcover scenes** (Cover & Open 1, All & Open 1 — "multiply"): smart objects lie over each other in Multiply and the layers above bend the tones: `P = Π(1 − a + a × picture(uv))`, `out = F(P)` with `F` a per-pixel tone curve measured from 9 flat levels. Pictures are first shrunk by the smart object's own squeeze.
- **Scene colour fills** sit over everything: `Change Color` (the background) and `Back Color` / `Front Color` (the thin edge lines of the open book's halves). They are baked at the vendor's colours, taken off with the PSD's own masks and put back in the chosen ones (`mockup_render._recolour()`).
- Baking calibrates with pictures filled into every smart object (black, white, flat levels, a coordinate ramp, 16-bit at 300 dpi — the dpi decides the placed size) and reads Photoshop's renders. Tools: `app/tools/mockup_bake/` — `bake.py prepare` → Photoshop runs the script → `bake.py build` → `install.py`. Close Photoshop before `build` (memory). Photoshop renames a smart object named like its old file on Replace Contents (`COVER_` in Cover 1); the bake script puts the name back. This is the only time Photoshop is needed on the main path.

## A run

`make()` → `draw()` when `drawn()`: pictures are cut, each mockup is rendered (`mockup_render.render()`; one baked template in memory at a time, released 2 minutes after its last use), saved as PNG at 300 dpi (`PNG_COMPRESSION = 3`) and handed to the cutter at once. `RUN_ORDER` is `open1, open2, cover1, coverOpen, allOpen, dedication`. `EDITABLE`, `CUT_ONLY`, `SCENES` are explained in [mockups.md](mockups.md#where-the-output-goes).

## Temporary files

All on drive D under `app/data/mockups/` (drive C stays clean; the general rule: [runtime](../architecture/runtime.md)).

| What | Goes |
|---|---|
| `book/` — the unpacked demo book | when another book comes, on close, on launch (`clear_books()`) |
| `work/<run>/` — a run's copies and pictures (fallback only) | right after the run; copies left open: after «Зберегти відкриті», else when Photoshop closes, at most a day (`KEEP_RUNS`); a copy the owner saved himself: a week (`KEEP_SAVED`) — `clean_runs()` |
| `tmp/photoshop/` | once Photoshop is closed |
| `cache/thumbs/` previews | unused for 21 days (`images.prune_cache()`) |

Closing waits for a run still working (`jobs.any_running()`).

## Photoshop fallback

Photoshop (`runtime/Photoshop`, `mockups.PHOTOSHOP_DIR`, a portable CC 2019) is used when a ticked template is not baked or has changed since. The run then goes through one script instead of `draw()`; the card shows a Photoshop warning and the run's own states.

- `plan()` decides everything first (pictures, template copies, which layer gets which picture, names). `prepare()` makes the pictures; `copy_templates()` copies the templates into `work/<time>-<id>/templates/` — Photoshop never opens a template in `runtime/Templates`. `script()` writes one `mockups.jsx` (the job as an ASCII literal in front of the fixed `app/studio/mockups.jsx`). `launch()` hands it to Photoshop: **one script per run, one "Yes"** — `WarnRunningScripts` in `PSUserConfig.txt` is the owner's setting, never an agent's.
- The script replaces each smart object's contents by layer path (`placedLayerReplaceContents` with an exact-size 300-dpi PNG), restores the visibility, swaps pages per spread and saves a PNG copy; it always acts on the active document. No `/` inside a regex's `[...]` in the script (ExtendScript ends the regex there).
- `watch()` follows the script's `status.json`; each saved picture goes to the slides' cutter. No status for `START_WAIT` (10 min) → "Photoshop never ran the script"; Photoshop gone → "Photoshop closed".
- Templates with `hand` (the front cover) or `keep` (Dedication's colours) are left open for the owner (`kept_open()`), the Canva cover opens beside them; the card says «Ваша черга — у Photoshop». **«Зберегти відкриті й закрити»** (`finish()`, `pending()`) runs a second short script (one more "Yes") that saves PNGs named like the rest and closes the copies.
- Launching: through the portable launcher `Photosho*.exe` (the "р" is Cyrillic), not `Photoshop.exe`; there is no COM, a script file is the way.

## Why

- Calibration pictures instead of reverse-engineering layer maths: the baked files reproduce Photoshop's light, warps and shadows.
- A template is re-baked, not hand-edited, when it changes — a stale bake would silently draw the old template.

## Where in the code

- [app/studio/mockups.py](../../app/studio/mockups.py) — `TEMPLATES`, `HARD`, `SOFT`, `RUN_ORDER`, `kept_open()`, `plan()`, `launch()`, `watch()`, `finish()`
- [app/studio/mockup_render.py](../../app/studio/mockup_render.py) — `stamp()`, `ready()`, `render()`
- [app/tools/mockup_bake/bake.py](../../app/tools/mockup_bake/bake.py) — `prepare()`; [install.py](../../app/tools/mockup_bake/install.py) — `main()`
- [app/studio/mockups.jsx](../../app/studio/mockups.jsx) — the fixed Photoshop script

## Related

- [Mockups](mockups.md) · [Slides](slides.md) · [Photo mockups](photo-mockups.md) · [Runtime](../architecture/runtime.md) · [Security](../security.md)
