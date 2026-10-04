# Book Anatomy

> **Single source of truth for book structure.** Every other file (AGENTS.md, README, formulas,
> templates, agents) only POINTS here — none keeps its own page/spread count. If a count is
> needed elsewhere, restate it to match this file exactly.

## Physical Format

Square hardcover. **30 interior pages**, plus a separate wraparound Cover.

**Page math: 1 (dedication) + 14 story spreads × 2 + 1 (afterword) = 30.**

---

## What gets generated (the canonical model)

**14 story panoramas at 2:1 + 2 square end images + 1 Cover.** The Cover is separate and made last.

| Asset | Generated as | Becomes | Notes |
|---|---|---|---|
| **14 story spreads** | one 2:1 panorama each (×14) | each sliced → 2 facing square pages (28 pages total) | continuous panorama, **no center fold**; **text-safe always on the RIGHT** (no alternation) |
| **Dedication image** | ONE 1:1 square image | page 1 (first) | same house style; decorative corner/edge motifs; calm rounded center-safe area for text |
| **Afterword image** | ONE 1:1 square image | page 30 (last) | mirrors the Dedication image; decorative corner/edge motifs; calm rounded center-safe area for text |
| **Cover** | ONE 2:1 wraparound | front (right, with title space) + back (left); art flows continuously over the spine | premium, slightly more contrast; **generate LAST**, after slicing; **NOT sliced** |

**Production order:** generate the 14 story spreads + the two square end images →
the Workshop slices only the 14 story panoramas → run Agent 6 and generate the final
wide image LAST.

**Generator-language boundary:** the table above is internal print/workflow language. Any
generator-facing prompt must describe only a standalone 2:1 panoramic illustration. Do not copy
physical-format words like book/page/spread/cover/front/back/spine/fold/gutter/seam into prompt
objects, including negatives.

The Dedication and Afterword are generated as two separate square images with matched style, palette,
and motif language so they still feel like a designed pair.

---

## Numbering (blueprint / book-text) ↔ what prints

Blueprints and `book-text.md` number **Spread 01–15**. Here is how that maps to the printed pages
and to the panoramas above (this resolves the "14 vs 15" confusion — both are correct, in different
frames):

| Blueprint / text entry | Printed page | How it is generated |
|---|---|---|
| **Spread 01 — Dedication** | page 1 (first) | one separate **1:1 square Dedication image** with center-safe text area |
| **Spreads 02–15** | pages 2–29 (the 14 story spreads) | the **14 story panoramas** (2:1); **Spread 15 = the finale scene** |
| **Afterword / Wishes** | page 30 (last) | one separate **1:1 square Afterword image** with center-safe text area |

So Dedication (Spread 01) and the Afterword are **two separate square generations**. **Spread 15
"Finale" is a full story panorama** (pages 28–29); the **Afterword (page 30) is a separate short
closing page**, NOT the same thing as the Spread 15 finale.

---

## Spread Architecture

Every story spread is the atomic unit of the book. One spread = one scene = one emotional beat.

```
SPREAD (2:1 panorama, sliced into two facing square pages)
├── one side  → illustration focal action
└── other side → calm text-safe area, still part of the same scene
```

Production prompt note: describe this layout in natural image language only. Do not paste
percentages, layout labels, arrows, guide marks, or physical-print vocabulary into image prompts;
image models may draw that scaffolding.

### Layout Type A — Illustration + Text Side by Side
- One side: full illustration; other side: calm, light text-friendly area.
- Best for: quiet emotional moments, text-heavy spreads.

### Layout Type B — Illustration with Embedded Text
- Illustration dominates; text sits in a clear calm zone (sky, floor, negative space).
- Best for: action scenes, visually rich moments.

### Layout Type C — Continuous Before-to-After Motion
- One environment carries a before-to-after action through a single visual trajectory.
- Best for: Formula C (Character Adventure) when a continuous path can imply time without
  introducing separate visual regions.

> Note: text is overlaid later in layout (Canva), never baked into the generated image.

---

## Standard Spread Sequence

```
Spread 01 — Dedication (first page · separate square image)
Spread 02 — Opening scene (introduce character / world)
Spread 03 — Scene 1
Spread 04 — Scene 2
Spread 05 — Scene 3
Spread 06 — Scene 4
Spread 07 — Scene 5  (emotional midpoint — warmth peak)
Spread 08 — Scene 6
Spread 09 — Scene 7
Spread 10 — Scene 8
Spread 11 — Scene 9
Spread 12 — Scene 10
Spread 13 — Scene 11
Spread 14 — Scene 12  (emotional resolution)
Spread 15 — Finale scene / closing blessing  (a full story panorama)
Afterword — closing wishes (last page · separate square image)
```

Spreads 02–15 are the 14 story panoramas. Spread 01 and the Afterword are produced as separate
square end images.

---

## Scene Rhythm

Alternate "active" and "quiet" spreads to avoid visual fatigue:

- **Active spread:** character doing something, dynamic pose, richer background.
- **Quiet spread:** character resting, being held — minimal background, more text room.

Typical pattern: active → quiet → active → quiet → … → quiet (finale).

---

## Dedication Page (Spread 01) — separate square image

Always personalized. Center-safe. The generated image should feel like a quiet keepsake card:
small decorative details in the corners/edges, and a calm rounded central area for later text.
```
Dear {Name},

[2–3 lines: why this book was made / the occasion]

With love,
{Gifter name(s)}
```
This is the ONLY page where the gifter's name appears.

---

## Finale Page (Spread 15) — a full story panorama

Closes the emotional arc on pages 28–29. Must feel like a hug. Contains {Name}. Often ends with a
wish, promise, or blessing. This is the screenshot-worthy line of the book.

---

## Afterword / Wishes (page 30) — separate square image

The very last page: a short, warm closing wish, **distinct from the Spread 15 finale stanza**.
1–2 gentle lines, may include {Name}. May carry a tiny "about this book" note in fine print.
Center-safe, with the same house style and motif language as Spread 01 so the first and last pages
mirror each other.

