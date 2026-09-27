---
title: Listing mockups — a Photoshop utility (plan and templates)
type: plan
updated: 2026-09-26
code: []
---
# Listing mockups (plan and templates)

> For every new book the owner makes ~10 Etsy listing pictures in Photoshop by hand: he drops a demo
> book's cover and spreads into purchased mockup templates. **Agreed on 2026-09-23:** a **separate
> utility** first (moved into Book Studio later) — drop the Canva ZIP, click the "presentable" spreads,
> and a Photoshop script fills everything **except the front cover**, which the owner fits himself.
> **Built on 2026-09-23** at the owner's command, **moved into Book Studio's Listings mode on 2026-09-24**
> ([plan](listings-mode.md)) — how it works now: [features/mockups.md](../features/mockups.md).
> This page keeps the agreements, the templates' structure and the Photoshop findings.

## Sources

- The owner's step-by-step description of his screen recording —
  [raw/2026-09-23-mockups-video-breakdown.md](../raw/2026-09-23-mockups-video-breakdown.md) (the
  recording itself wasn't analyzed: too slow and costly frame by frame, the owner's decision).
- His answers in chat, word for word — [raw/2026-09-23-mockups-owner-answers.md](../raw/2026-09-23-mockups-owner-answers.md).
- An agent's **read-only** analysis of the templates on 2026-09-23 (`psd-tools`: the layer tree, smart
  object sizes and ids, the saved previews) — the tables below.
- The idea was first recorded on 2026-09-19 — [roadmap](roadmap.md#etsy-listings).

## How the owner does it today (by hand)

1. Makes a **demo book** in Canva: the cover with a sample name (in the recording — "Our Little Silly
   Goose Oliver"), the pages with a literal `{Name}`. Downloads it as a ZIP of PNGs.
2. Opens the templates in Photoshop CC 2019. In each one: double-clicks a smart object → it opens as a
   flat `.psb` tab → pastes the picture → Ctrl+T to fit → Ctrl+S → Ctrl+W. The template itself applies the
   bend, shadows and light; he never deforms anything by hand.
3. **The cover:** he pastes the **whole wide cover** (back on the left, front on the right) and slides it
   so only the needed part shows: the right half for the front, the exact middle for the spine.
4. **Different spreads every time**, chosen by eye: `2. Open 1` is used **4 times** and `3. Open 2`
   **twice**, each with a different spread (his answer). ~10 pictures per book.

What was seen in the recording (for reference): Open 1 — a picture on the left (the gosling waking in a
nest), text on the right ("Morning sun begins to glow…"); Open 2 — text on the left ("Silly {Name}
shakes his wings…"), a picture on the right; Dedication — page 1 ("Dear {Name}, On your very first
birthday…"); Cover & Open 1 — the front cover (slid to show "Oliver"), a picture with a frog, text
"Waddling down the dusty road…"; All & Open 1 — the spine (the middle strip), text "Goose {Name} sees a
butterfly…", a picture with a butterfly.

## The templates

Folder: **`D:\Roman\Desktop\Трафарети мастхев`** ("must-have templates"). **Read-only** — never edit,
save over, move, rename or delete anything there ([security](../security.md), the owner's words). It
replaces the earlier sample folder `D:\Roman\Desktop\Photoshop demo\Prep`.

All six are 300 ppi, 8-bit RGB, and every smart object inside is 300 ppi. They come from two vendors:

- **A — hardcover** (files 1–4). Layer groups `PRESENTATIONS / VIEW_xx / BOOK / OBJECT / SMART OBJECTS`,
  plus `ITEMS` and `FILTERS` (all filter looks are off). At the bottom of the layer list — a group
  **`Main`** with **hidden linked copies** of the smart objects that matter (the same content id as the
  visible ones): replacing a copy's contents changes the book in the picture. Most likely the owner's own
  shortcuts (the names `Rige`, `Deck Color` are his typing).
- **B — softcover, the vendor's "Square Catalogue Mockup"** (`Cover & Open 1`, `All & Open 1`). Groups
  `Editable Layers / Design Smart Objects / Reflection / Shadow`, color layers `Change Color`,
  `Back Color`, `Front Color` at the top. No `Main`: the linked copies are at the top of the layer list.

| Template (file size) | Canvas | What's in the picture | Layers to fill → inner size | Who fills |
|---|---|---|---|---|
| `1. Cover 1.psd` (156 MB) | 2670×2670 | a closed hardcover, front, from above | `Main/COVER_` → 2100×2200 | the owner (front cover) |
| `2. Open 1.psd` (364 MB), ×4 | 4000×2670 | an open book, flat, from above | `Main/Left`, `Main/Right` → 1900×1900; `Main/Cover`, `Main/Back Cover` → 2100×2200; `Main/Rige` → 80×2200 | the script (all) |
| `3. Open 2.psd` (406 MB), ×2 | 4000×2670 | an open book at an angle | the same names and sizes as Open 1 | the script (all) |
| `4. Dedication.psd` (341 MB) | 4000×2670 | open on the dedication: the inside of the cover on the left, page 1 on the right | `Main/Page 1` → 1900×1900; `Main/Cover`, `Main/Back Cover` → 2100×2200; `Main/Rige` → 80×2200 | the script (all) |
| `Cover & Open 1.psd` (120 MB) | 4000×3000 | a closed softcover + an open one | `Front Cover`, `Left Page`, `Right Page` → 1935×1935 | the script: pages; the owner: front cover |
| `All & Open 1.psd` (175 MB) | 4000×3000 | five books: closed (front), face down (back), a cover laid open (back + spine + front), an open spread | `Front Cover`, `Back Cover`, `Left `, `Right ` → 1935×1935; `Spine` → 164×1935 | the script: pages, back, spine; the owner: front cover |

**Details that matter for the script:**
- **Linked copies.** One content id can appear in several layers: in All & Open 1, `Front Cover`,
  `Back Cover` (+ `Back cover` with a small "c") and `Spine` are there twice each — two books show the
  same design. Replacing the contents of any one of them updates all.
- **Names aren't uniform:** the front cover is `COVER_` / `Cover` / `Front Cover`; pages are `Left` /
  `Left Page` / `Left ` — **with a trailing space** in All & Open 1 (and `Right ` too); the spine is `Rige`
  (A) or `Spine` (B), and the files inside are `RIDGE*.psb`. The script needs a per-template table of layer
  names and must compare names with spaces trimmed.
- **Hidden vs. visible copies:** in A (`Main`) and in All & Open 1 the shortcut copies are hidden. In
  **Cover & Open 1 they are visible** — checked on 2026-09-23: they don't change the picture at all
  (identical colors with them on and off, [below](#photoshop-scripting-check-2026-09-23-done--it-works)).
  Nothing to fix.
- **Not every "square" is square:** pages are 1900×1900 (A) / 1935×1935 (B); the cover and back in A are
  2100×2200 (extra margin for wrapping around the board); the spine is 80×2200 (A) / 164×1935 (B).
- **In the open-book templates (2, 3, 4) the cover only shows as a thin rim** around the pages (the
  left rim is the front board, the right one the back). Left white, it stays white; filled from the cover,
  it looks like a real book.
- **Smart objects the script never touches:** `BACKGROUND`, `BACKGROUND_desk color` (`Deck Color`),
  `PAPER_edge color`, `SHADOW_editable`, `LIGHT_editable`, the pages under the open spread (`PAGE 2_`,
  `PAGE 5_`, `COVER_endpaper_` — they stay white), `Rectangle 1` (a reflection in B), and **"selective
  varnish"** (`SELECTIVE VARNISH` — separate, *unlinked* copies of the cover; empty/off).
- **The templates are clean** (1–4 white, B with the vendor's demo design): the owner never saves a book
  into them.
- The other files in the folder — `Cover.png`, `Shelf.png`, `Size.jpg` — are flat pictures and **not part
  of this**: the owner's examples for a diffusion model, no automation (his answer).
- `psd-tools` (in `D:\Programs\Regular\python-libs`) read the layer tree and the saved preview of all six
  (up to 406 MB) in under a second each. This **corrects** the 2026-09-19 note "can't parse files over
  ~350 MB": that was about something heavier (rendering layers), not re-checked. Rendering a finished
  mockup still needs Photoshop (custom warps).

## What was agreed with the owner (2026-09-23)

- **A separate utility for now** with its own window ("a web interface"); later it becomes part of Book
  Studio.
- **Input:** the demo book's Canva ZIP, dragged in.
- **The owner picks the "presentable" spreads** by clicking: 4 for Open 1, 2 for Open 2, 1 for
  Cover & Open 1, 1 for All & Open 1 — 8 in total, different every time. The dedication (page 1) goes into
  Dedication by itself.
- **The script fills in every template:** the chosen spread's pages; the **spine** — the middle strip of
  the wide cover; the **back cover** — its left half. In the open-book templates (2, 3, 4) — the **front
  cover's rim** too (its right half, centered; the rim is too thin for precision to matter).
- **The front cover — by the owner, by hand**, in the three templates where it's really visible:
  `1. Cover 1`, `Cover & Open 1`, `All & Open 1`. His reason: he's "pixel-perfect", and "the cover sells",
  so he centers and fits it himself. The script fills everything else in these three and **leaves them
  open** in Photoshop.
- **The script opens a copy** of each template (in a temporary folder) — even an accidental Ctrl+S never
  touches the originals.
- The fully automatic pictures (Open 1 ×4, Open 2 ×2 — and Dedication until 2026-09-26, when the owner asked to
  keep it open for its background and table colours) are saved and closed by the script;
  a template used several times is opened once, and only the spread is swapped between saves.
- **Output — PNG**; the owner picks the folder **every time** (the Windows dialog).
- A small "save the open ones" script — saves the three hand-finished documents into the same folder with
  the right names in one click: **built on 2026-09-23 as an optional button «Зберегти відкриті й закрити»**
  (when the owner asked about leftovers and a "done" message); saving them by hand still works.
- Suggested, **not confirmed:** file names like `Open 1 (spread 6-7).png` (built as `2. Open 1 (6-7).png`,
  see [the utility](../features/mockups.md#what-goes-where)).

## How it could be built (the design before building; what was built — [features/mockups.md](../features/mockups.md))

- **Where:** in this repository, a separate small program (its own shortcut, window and port) that
  reuses Book Studio's parts, so moving it into Book Studio later is cheap:
  - [app/studio/drops.py](../../app/studio/drops.py) — `extract_zip()` (a dropped ZIP; moved out of creator.py for this)
  - [app/web/js/drop.js](../../app/web/js/drop.js) — `receiveDrop()` (drag-and-drop in the window)
  - [app/studio/orders.py](../../app/studio/orders.py) — `arrange_pages()` (a Canva export → `Cover.png` + `1…N.png`)
  - [app/studio/desktop.py](../../app/studio/desktop.py) — `pick_folder()`, `open_app_window()` (the folder dialog, the window)
  - spreads as pairs — [book structure](../rules/book-structure.md): `[endpaper | 1]`, `[2 | 3]`, `[4 | 5]`, …
- **Preparing the pictures (Python + Pillow, already a Book Studio dependency):** from `Cover.png` (the
  wide back + front): the back = the left half, the front = the right half, each scaled to **fill** its
  target and centered (2100×2200 for A, 1935×1935 for B); the spine = a strip from the exact middle at
  the same scale as the halves (80 px out of a 2200-px-high cover for A, 164 out of 1935 for B); pages
  scaled to 1900 / 1935. Save the PNGs **at 300 dpi** — the smart objects are 300 ppi, and a different
  dpi would change the placed size.
- **Photoshop (an ExtendScript `.jsx`, CC 2019):** open a copy of the template → find the layer by name
  (trimmed) → "Replace Contents" (`placedLayerReplaceContents`) with a prepared PNG of exactly the inner
  size — this keeps the bend, blend mode and position and updates every linked copy → save a PNG copy →
  close without saving. Selecting a hidden layer from a script makes it visible — put `visible` back
  afterwards. How to launch a script and what was confirmed — [below](#photoshop-scripting-check-2026-09-23-done--it-works).
- **Suggested order of work:** 1) the Photoshop part with a fixed test job; 2) picture preparation + tests
  (Pillow, made-up images, no real books); 3) the window: drop, spread thumbnails, template slots, the
  folder, "Make mockups"; 4) the owner tries it on a real demo book, and the cover/spine crop gets tuned
  by eye; 5) later — into Book Studio.

## Open questions

- Output file names: built as `2. Open 1 (6-7).png`, `4. Dedication.png` — the owner hasn't confirmed.
- The back/spine/rim crop rule ("fill and center") — to check on the first real book; the Canva cover's
  exact size decides the crop.
- «Зберегти відкриті й закрити» (built 2026-09-23, optional) — does the owner use it, or keep saving by hand?
  Not yet tried in the real Photoshop.
- **The "run this script?" dialog:** built with one "Yes" per script (the run, and «Зберегти відкриті» if
  pressed); the owner can turn the warning off
  himself (`WarnRunningScripts 0`, see below) — his choice. The question is in English: "You are about to
  run the script contained in file "mockups.jsx"…" (Yes / No); the "Yes" there isn't a standard Windows
  button (UI Automation sees a pane), so an agent's test presses it by a mouse click inside its frame.
- Etsy's file size limit for listing pictures — not checked (the utility's PNGs are ≈ 5 MB).

## Photoshop scripting check (2026-09-23, done — it works)

Done at the owner's request, **on copies** of `Cover & Open 1` and `2. Open 1` in the agent's temp folder
(deleted afterwards), with made-up colored test pictures; the templates folder wasn't touched (its file
dates didn't change). Photoshop wasn't running before; the last test script closed it.

**Launching a script from outside — works, with one confirmation:**
- `…\Portable Adobe Photoshop\App\Photoshop\Photoshop.exe "<path>\job.jsx"` — when Photoshop is already
  running, the file is handed to it and the script runs.
- The portable launcher `…\Portable Adobe Photoshop\Photoshoр.exe` (**the "р" before `.exe` is Cyrillic**,
  U+0440 — look it up by the mask `Photosho*.exe`; 155 KB) starts Photoshop with its settings kept inside
  `…\Portable Adobe Photoshop\Data\` (not on drive C); a `.jsx` passed to it also got delivered. Start
  Photoshop through the launcher, not `Photoshop.exe` directly — otherwise it would use settings on
  drive C. The cold start time wasn't measured.
- **Every externally launched script shows a dialog:** "You are about to run the script contained in file
  "….jsx". Are you sure you want to do this?" (Yes / No). It can be turned off by adding the line
  `WarnRunningScripts 0` to `PSUserConfig.txt` in Photoshop's settings folder (for this portable copy:
  `…\Portable Adobe Photoshop\Data\AppDataRoaming\Adobe Photoshop CC 2019\Adobe Photoshop CC 2019 Settings\`,
  the file already exists) and restarting Photoshop. **This is the owner's decision; an agent doesn't
  change Photoshop's settings itself.** Without it — one "Yes" click per batch (the utility should run all
  templates in **one** script). In the test the agent pressed "Yes" programmatically, only on the dialog
  naming its own test script.
- There's no COM registration (`Photoshop.Application` isn't in the registry) — so no COM automation;
  running a `.jsx` is the way.

**The core operation — confirmed:**
- Find a layer by name (trimmed), `doc.activeLayer = layer`, "Replace Contents"
  (`placedLayerReplaceContents`) with an exact-size 300-dpi PNG: the picture takes the template's bend,
  shadows and light exactly like by hand; the frame of the test picture lands right on the page edges.
- Replacing the **hidden** copy in `Main` changes the book in the picture (linked copies work).
- **Selecting a hidden layer from a script makes it visible** (confirmed) — put `visible` back right after.
- **The rims:** in `2. Open 1` the left rim showed the front cover (`Main/Cover`), the right one the back
  (`Main/Back Cover`), the spine strip at the fold — the same as a real case-bound book.
- **Swapping the spread and saving again** in the same open document works — one opening per template.
- `layer.bounds` came back as NaN in this setup — don't rely on it without setting the units.
- **Cover & Open 1's visible top copies change nothing:** the same fill saved with them on and off gave
  identical colors (measured in four areas). The earlier worry is closed.
- **Speed:** opening a template 1.2–1.5 s (even the 364 MB one), one replacement 0.2–0.4 s, saving a PNG
  0.9–1.6 s; two templates and three PNGs — **11 s** in total. A whole book (~10 pictures) should take well
  under a minute.
- **The PNGs:** 4000×3000 ≈ 17 MB, 4000×2670 ≈ 5 MB (compression 3), 300 dpi. Etsy's file size limit
  wasn't checked.

**Learned while building the utility (2026-09-23, live, on copies, a made-up book):**
- A **cold start through the launcher** with the script as an argument reached the "run this script?"
  question in ~5 s; the whole run (7 pictures, 3 templates left open) took 32–37 s.
- **"Save a copy" and "Replace Contents" act on the active document**, whatever document the script calls
  them on: a copy saved from a non-active document held the active one's picture. The utility makes its
  document active before every replacement and save.
- A "Yes" given after the utility stopped waiting runs the script, which sees the stop mark and ends at
  once — nothing opened, nothing saved (checked live).

The tested core (ExtendScript, Photoshop CC 2019):

```
function replaceContents(file) {            // the active layer must be a smart object
    var d = new ActionDescriptor();
    d.putPath(charIDToTypeID("null"), file);
    executeAction(stringIDToTypeID("placedLayerReplaceContents"), d, DialogModes.NO);
}
app.displayDialogs = DialogModes.NO;
var doc = app.open(new File(copyOfTemplate));   // a copy, never the template itself
var layer = /* find by trimmed name, e.g. group "Main" → "Left" */;
var wasVisible = layer.visible;
doc.activeLayer = layer;                     // makes a hidden layer visible!
replaceContents(new File(pagePng));
doc.activeLayer.visible = wasVisible;
var o = new PNGSaveOptions(); o.compression = 3; o.interlaced = false;
doc.saveAs(new File(outPng), o, true, Extension.LOWERCASE);   // true = save a copy
doc.close(SaveOptions.DONOTSAVECHANGES);
// quit when done and nothing else is open:
// executeAction(charIDToTypeID("quit"), undefined, DialogModes.NO);
```

## Related

- [The utility as built](../features/mockups.md) · [Plans](roadmap.md) · [Canva](../integrations/canva.md) · [Book structure](../rules/book-structure.md)
- [Security](../security.md) · [Decisions](../decisions.md) · [Working with the owner](../owner/working-with-owner.md)
