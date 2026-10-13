---
title: Mockups — listing pictures from a demo book (a tool, and a Workshop book's step)
type: feature
updated: 2026-10-11
code:
  - app/studio/mockups.py
  - app/studio/mockups.jsx
  - app/web/js/pages/mockups.js
  - app/web/js/pages/mockups-run.js
  - app/web/js/pages/mockups-slides.js
---
# Mockups (Мокапи)

> A tool (`#/mockups`) — among [«Інструменти»](modes.md) on its own, and a Workshop book's «Мокапи» step: opened from
> the book it shows «Для книги №41 …», goes back to the book and keeps the rail on «Книги» (`arrived()`, `navFor()`)
> — **until it is opened from «Інструменти» or for another book**; coming back to it from anywhere else (the slides'
> editor, another page) it stays the book's. Bring in the demo book's Canva ZIP,
> click the "presentable" spreads — one Photoshop script fills the owner's mockup templates and saves **6 PNG
> pictures**; **4 templates are left open** (the 3 where the front cover shows — the owner fits it by hand — and
> **Dedication**, whose background and table colours he picks), and **«Зберегти відкриті»** saves them too. Every saved
> picture is cut out without its background, and step 4 makes the [listing slides](slides.md). The templates' structure
> and what was learned about scripting Photoshop — below.

## How the owner uses it

The page looks like the Order Creator (the owner: "exactly like Book Studio"): **numbered steps on the left**, the
**demo book's structure on the right**. A done step's number turns into a ✓. **The page is kept when he steps away**:
the book, the picks, a run and its result wait — but **only for a way back that is not the tools list**: a click on the tile in
«Інструменти» opens it clean every time (2026-09-30, the owner), except while Photoshop works for it or templates wait there for his save;
a run going on elsewhere puts a cyan dot on «Інструменти», and a notice says when it ends.

**The demo book** comes in on the right: a dashed veil «Перетягніть сюди ZIP із Canva» — drop the ZIP (anywhere on the
window), the unpacked folder or the pictures, or click for the Windows dialog (Downloads first, then where the last ZIP
was — `lastZip`). The veil says what goes on; the header reads «Структура · <name> · 24 стор.». The pages are read by
the print folder's rules ([file naming](../rules/file-naming.md)): the cover is `cover…` or the one wide picture; page 1
is the dedication; the spreads `2–3`, `4–5`, …; page 30 is not offered.

1. **Розвороти в шаблонах.** A row per template with its own preview (read from the PSD, only read) and its slots:
   **Open 1 ×4, Open 2 ×2, Cover & Open 1 ×1, All & Open 1 ×1**; Dedication (page 1) and Cover 1 go in by themselves;
   ✋ — the owner's touch. **Click a spread** → it goes into the highlighted slot, the next one lights up (the header
   says where the next click goes); drag a spread onto a slot, or a slot onto another (they swap); × / Delete empties;
   the eraser empties all; the magnifier opens a spread large. **A book dropped in again gets its picks back** (the
   last 12, `localStorage`).
2. **Книга** — shown **only when the page is a book's step** (the Workshop's «Мокапи» step sent one — `mk-for-book` — or the
   owner pressed the small book icon of «Куди зберегти»); opened from «Інструменти» it asks for a folder when it runs, and
   never fills a Workshop book's folder by itself (until 2026-09-30 it chose the last or the first book on its own). The
   Workshop's books, newest first: its `mockups\` takes the pictures and their cut-outs — **no dialog** (the owner: "don't ask where").
   For such a book the run also keeps **the Canva cover** as `mockups\canva-cover.*` (`_keep_canva_cover()`) and copies
   Cover & Open 1 and All & Open 1 into its **`etsy\`** once saved (`_to_etsy()`) — see [photo mockups](photo-mockups.md);
   its «Мокапи» step ticks itself (`_ticked()`). «Інша папка…» gives the folder field and dialog instead.
2b. **The book's folder as it is** (11.10.2026, the owner: "the mockups are made, but the program says there are none";
   "I redo one mockup — the whole session goes and I can't get to the next step"). With a Workshop book chosen, the page
   reads its `mockups\` (`loadExisting()` → `GET /api/mockups/existing`, `existing()`): step 3 shows the card **«У папці книги ·
   11 картинок»** (`existingCard()`; a click — large, the original opens), under a run's result too, and step 4 «Слайди для
   лістингу» is there whenever the folder has mockups for the slides — **no demo book and no Photoshop run needed**, and a run
   of one template no longer leaves only that one. It is read when the page opens for a book, when another book is chosen
   (the select or the small book icon), after every run and after «Завершити». The book's slides already made show as
   they are (see [slides](slides.md)).
2a. **A tick per template** (09.10.2026, the owner: "just tick the category"): every template row starts with a tick, all ticked.
   **«Зробити мокапи» makes only the ticked ones** — Photoshop opens, fills and saves just them (a lone Dedication, say, when one
   slide was not prepared); the spreads are asked for only in ticked templates, the two chips count the ticked ones, an unticked
   row is dimmed. All ticked = the whole run as before. The page sends `only` (template keys) to `/api/mockups/make`; `plan()`
   and `make()` take `only` (`selected()`), a run of some templates **does not tick the Workshop book's «Мокапи» step**
   (`_ticked(whole=False)`), and the book's cover is opened beside only when a ticked template is left open. A file already
   there is never overwritten (` (2)`), so a redone slide lands beside the old one.
3. **Photoshop** — one line says what will happen, then **«Зробити мокапи»**. The button always answers: no book → the
   veil blinks; empty slots → they blink amber and a toast names them.
   - **While it runs**: a row per template (waiting / in work / ✓, «2/4» or «✋ лишиться відкритим»), a bar, × stops.
     While Photoshop asks "run this script?", the card draws that dialog with its **Yes** pulsing.
   - **Done**: «Готово · 6 картинок · 45 с» with the pictures themselves (a click — large). When the window is behind,
     its taskbar button flashes, Windows chimes and the title says so (the shell writes the title — `bs:busy`).
   - **«Ваша черга — у Photoshop»**: the templates left open are named; after his touches **«Зберегти відкриті й
     закрити»** runs a second short script (one more "Yes"): PNGs named like the rest, the documents closed, their
     copies removed. Saving by hand still works. A reloaded window offers the button again (`pending()`).
   - **The book's cover opens beside them** (the owner: "so I can work with it at once") — the Canva cover as
     `Cover.png`; «Зберегти відкриті» closes it only when unchanged (`doc.saved`).
4. **Слайди для лістингу** — «Без фону · 5/6», **«Схема: Nature ▾»** (pick the scheme the six start from — Nature, Night, his own; since 2026-09-30), the book's numbers, **«Зробити слайди»**, the six with ✎, «Відкрити в
   редакторі» — see [slides](slides.md).
4a. **The Photoshop card's summary is two counting chips** (since the late evening of 2026-09-30 — a paragraph before): a picture
   icon with the number Photoshop saves itself, a hand with the number of templates it leaves open for the owner; the
   sentences are their tooltips. The make button carries `aria-disabled` and `aria-describedby` while something is missing.
5. **«✓» — «Завершити»** (was «×» until 2026-09-30): the page starts clean for the next book, the unpacked demo book is deleted (`close()`). With
   templates still waiting it asks first; they stay open, and the run is marked `dismissed`.

The sliders button: where the templates and Photoshop are (a missing folder — a yellow line above the steps).
A whole run takes ~45 s on the owner's PC: ~3 s the pictures, <1 s copying the templates, the rest Photoshop.

## What goes where

| Template | Spreads | The script puts in | Result |
|---|---|---|---|
| `2. Open 1` | 4 | the spread's pages, the back, the spine, the front cover's rim | 4 PNG |
| `3. Open 2` | 2 | the same | 2 PNG |
| `1. Cover 1` | — | nothing (its only layer is the front cover) | left open → «Зберегти відкриті» |
| `Cover & Open 1` | 1 | the spread's pages | left open → «Зберегти відкриті» |
| `All & Open 1` | 1 | the spread's pages, the back, the spine | left open → «Зберегти відкриті» |
| `4. Dedication` | — | page 1, the back, the spine, the rim | left open — the owner picks its colours (`"keep": "colours"`) |

The templates left open come last (`RUN_ORDER`), Cover 1 first — it is in front when the script ends. `kept_open()`: a
template with `hand` (the front cover) or `keep` (Dedication's colours).

- **Pictures are cut by Pillow at the smart object's exact size, 300 dpi** (`cover_pictures()`, `page_picture()`): the
  back — the left half of the wide cover, the front (for the rims) — the right half, each filling its board, centred;
  the spine — the strip from the middle; pages filled into the square. Hardcover templates: pages 1900², boards
  2100×2200, spine 80×2200; the softcover: pages and boards 1935², spine 164×1935 (`HARD`, `SOFT`).
- **Names**: `<template> (<pages>).png` — `2. Open 1 (6-7).png`, `1. Cover 1.png`; never over a file (` (2)` —
  `_free_name()`). **PNG**, compression 3 (`PNG_COMPRESSION`), each at its template's own size — on book 25:
  Open 1 3727×2397 and Open 2 3227×2248 (5–7 MB), the whole scenes Cover & Open 1 and All & Open 1 4000×3000
  (16–18 MB).

## The templates

Folder `D:\Roman\Desktop\Трафарети мастхев` ("must-have templates") — **read-only**, never edited, saved over, moved
or deleted ([security](../security.md)); the program only ever opens copies. All six are 300 ppi, 8-bit RGB, every smart
object inside is 300 ppi. Two vendors:

- **A — hardcover** (files 1–4). Groups `PRESENTATIONS / VIEW_xx / BOOK / OBJECT / SMART OBJECTS`, plus `ITEMS` and
  `FILTERS` (all filter looks off). At the bottom of the layer list a group **`Main`** holds **hidden linked copies** of
  the smart objects that matter (the same content id as the visible ones): replacing a copy's contents changes the book
  in the picture.
- **B — softcover** (`Cover & Open 1`, `All & Open 1`). Groups `Editable Layers / Design Smart Objects / Reflection /
  Shadow`, colour layers `Change Color`, `Back Color`, `Front Color`. No `Main`: the linked copies are at the top.

| Template | Canvas | In the picture | Layers to fill → inner size |
|---|---|---|---|
| `1. Cover 1` | 2670×2670 | a closed hardcover from above | `Main/COVER_` → 2100×2200 |
| `2. Open 1` (×4) | 4000×2670 | an open book, flat | `Main/Left`, `Main/Right` → 1900²; `Main/Cover`, `Main/Back Cover` → 2100×2200; `Main/Rige` → 80×2200 |
| `3. Open 2` (×2) | 4000×2670 | an open book at an angle | the same names and sizes |
| `4. Dedication` | 4000×2670 | open on the dedication (the cover's inside left, page 1 right) | `Main/Page 1` → 1900²; `Cover`, `Back Cover`, `Rige` as above |
| `Cover & Open 1` | 4000×3000 | a closed softcover + an open one | `Front Cover`, `Left Page`, `Right Page` → 1935² |
| `All & Open 1` | 4000×3000 | five books: front, back, a cover laid open, an open spread | `Front Cover`, `Back Cover`, `Left `, `Right ` → 1935²; `Spine` → 164×1935 |

What matters for the script:
- **Linked copies.** One content id can sit in several layers (in `All & Open 1`, `Front Cover`, `Back Cover` and `Spine`
  are there twice): replacing any one updates all. In `Cover & Open 1` the top copies are visible and change nothing.
- **Names aren't uniform:** the front cover is `COVER_` / `Cover` / `Front Cover`; pages `Left` / `Left Page` / `Left `
  (**a trailing space** in `All & Open 1`, `Right ` too); the spine is `Rige` (A) or `Spine` (B). Hence the per-template
  table and names compared trimmed.
- **In the open-book templates the cover shows only as a thin rim** around the pages (left — the front board, right —
  the back): white if left empty, a real book when filled from the cover.
- **Never touched:** `BACKGROUND`, `BACKGROUND_desk color`, `PAPER_edge color`, `SHADOW_editable`, `LIGHT_editable`, the
  pages under the open spread (`PAGE 2_`, `PAGE 5_`, `COVER_endpaper_`), `Rectangle 1`, and `SELECTIVE VARNISH`.
- The templates are clean (1–4 white, B with the vendor's demo design); the owner never saves a book into them. The other
  files in the folder (`Cover.png`, `Shelf.png`, `Size.jpg`) are his flat examples, not part of the tool.
- `psd-tools` reads a template's layer tree and preview in under a second (up to 406 MB); rendering a finished mockup
  still needs Photoshop (custom warps).

## Photoshop facts (checked on copies)

- **Launching.** Photoshop is the owner's portable CC 2019: the launcher `Photoshoр.exe` (**the "р" is Cyrillic**, found by
  `Photosho*.exe`) keeps its settings inside its own folder, off drive C — start it through the launcher, not
  `Photoshop.exe`. A `.jsx` handed to a running Photoshop runs there. There is no COM; a script file is the way.
- **Every externally launched script asks "run this script?"** (Yes / No). `WarnRunningScripts 0` in `PSUserConfig.txt`
  would silence it, but that is the owner's setting, never an agent's; hence **one script per run → one "Yes"**.
- **The core operation:** make the layer active, `placedLayerReplaceContents` with an exact-size 300-dpi PNG — the picture
  takes the template's bend, shadows and light as by hand. Replacing the hidden copy in `Main` works.
  Selecting a hidden layer makes it visible, so `visible` is restored at once. Swapping the spread and saving again in
  the same open document works (one opening per template). `layer.bounds` is NaN unless the units are set — not relied on.
- **"Save a copy" and "Replace Contents" act on the active document**, whatever document the script calls them on — the
  script makes its document active before every replacement and save.
- A "Yes" given after the tool stopped waiting runs a script that sees the stop mark and ends at once.
- **Speed:** a template opens in 1.2–1.5 s, a replacement 0.2–0.4 s, a PNG saves in 0.9–1.6 s; a cold start to the "run this
  script?" question ~5 s; a real run (7 pictures, 3 templates left open) 32–37 s.
- PNGs: 4000×3000 ≈ 17 MB, 4000×2670 ≈ 5 MB (compression 3), 300 dpi.

## How it works inside

1. `plan()` decides everything first: the pictures, the template copies, which layer gets which picture, the names. A
   wrong choice is refused at once.
2. `prepare()` makes the pictures; `copy_templates()` copies the six templates into
   `app/data/mockups/work/<time>-<id>/templates/` — **Photoshop never opens a template from `Трафарети мастхев`**
   ([security](../security.md)).
3. `script()` writes one `mockups.jsx`: the job as a JavaScript literal (ASCII only; Cyrillic as `\u` escapes) in front
   of the fixed [mockups.jsx](../../app/studio/mockups.jsx); `job.json` beside it.
4. `launch()` hands it to Photoshop — `Photoshop.exe` when it runs, else the portable launcher `Photoshoр.exe` (Cyrillic
   "р", found by `Photosho*.exe`; keeps its settings off drive C), temp in `data/mockups/tmp/photoshop`. **One script
   per run → one "Yes"**.
5. The script (ExtendScript, Photoshop CC 2019 — **no `/` inside a regex's `[...]`**, it ends the regex there): per
   template — open the copy, "Replace Contents" of each smart object by its layer path (names trimmed; a one-name path
   looked for at the top of the list), restore the visibility, per spread swap the pages and save a PNG copy; always
   act on the **active** document; the automatic templates close without saving, the four stay open.
6. `watch()` follows the script's `status.json` and hands the page `progress_view()`; each saved picture goes to the
   slides' cutter (`_cut_without_background()`). No status for 10 min (`START_WAIT`) → "Photoshop never ran the script";
   Photoshop gone → "Photoshop closed"; stop → the file `cancel`.
7. **«Зберегти відкриті»** — `finish()`: `finish_plan()` reads `job.json`, the same script runs with `JOB.finish`, finds
   each copy among the open documents, saves, closes; one the owner closed is reported.

## Temporary files

The owner: "keep drive C clean — any temporary file must go when the work is done". All on drive **D**, in
`app/data/mockups/`:

| What | Size | Goes |
|---|---|---|
| `work/<run>/pictures/` — the prepared pages | ~50 MB | right after the script |
| `work/<run>/templates/` — the closed templates' copies | ~1.2 GB | right after the run |
| `work/<run>/templates/` — the ones left open | ~470 MB | after «Зберегти відкриті»; else when Photoshop is closed (checked on launch, before a run, on close), at most a day later (`KEEP_RUNS`) |
| a copy he saved himself with Ctrl+S | — | kept a week (`KEEP_SAVED`) |
| `book/` — the unpacked demo book (`BOOKS`) | ~200 MB | when another book comes, on close, on launch |
| `tmp/photoshop/` | — | once Photoshop is closed |
| `cache/thumbs/` (the previews) | ~10 MB a book | unused for 21 days (`images.prune_cache()`) |

**The demo book has a folder of its own**: a dropped ZIP arrives among the files dropped for orders and is moved out
at once (`_take_dropped()`) — so a new demo book never clears an order's dropped files, and the orders' cleaning never
takes the demo book. Nothing goes to drive C (`core.own_temp()`, [runtime](../architecture/runtime.md#temporary-files-and-drive-c)).

## Where things are

- `places.json` (`PLACES`): the templates `D:\Roman\Desktop\Трафарети мастхев`, Photoshop
  `D:\Programs\Portable\Photoshop_Portable` (`TEMPLATES_DIR`, `PHOTOSHOP_DIR`), `lastOut`, `lastZip`. Output may not be
  the templates folder.
- Book Studio's closing waits for a run still copying or watching (`jobs.any_running()`); on launch and close the demo
  book goes and the runs are cleaned (`clear_books()`, `clean_runs()`).
- **When something goes wrong**: `app/data/logs/app.log`, lines `Mockups: …` (the dialogs, the book read, the run started
  / finished / stopped — `_logged()`); a run's own files in `work/<time>-<id>/` while kept.
- **Not checked live**: the second script in the real Photoshop (only against a pretend one), the taskbar flash.

## Where in the code

- [app/studio/mockups.py](../../app/studio/mockups.py) — `existing()`, `_template_of()`, `_existing_file()`, `_keep_canva_cover()`, `_to_etsy()`, `close()`, `DISMISSED`, `_logged()`, `TEMPLATES`, `RUN_ORDER`, `HARD`, `SOFT`, `TEMPLATES_DIR`, `PHOTOSHOP_DIR`, `PHOTOSHOP_TEMP`, `PLACES`, `WORK`, `BOOKS`, `KEEP_RUNS`, `KEEP_SAVED`, `START_WAIT`, `read_book()`, `book_view()`, `_only_this_book()`, `clear_books()`, `_take_dropped()`, `cover_pictures()`, `page_picture()`, `selected()`, `plan()`, `prepare()`, `copy_templates()`, `script()`, `finish_plan()`, `find_photoshop()`, `running()`, `launch()`, `progress_view()`, `watch()`, `_cut_without_background()`, `_workshop_books()`, `_ticked()`, `make()`, `finish()`, `_run_script()`, `pending()`, `clean_runs()`, `_saved_by_owner()`, `state()`, `_free_name()`, `_problem_text()`, `_pick_zip()`, `_open_zip()`, `_open_book()`, `_attention()`, `_template_media()`, `_out_media()`
- [app/studio/mockups.jsx](../../app/studio/mockups.jsx) — `openCover()`, `closeCover()`, `findLayer()`, `replaceContents()`, `fill()`, `savePng()`, `runTemplate()`, `findOpen()`, `finishOpen()`, `report()`, `cancelled()`
- [app/studio/main.py](../../app/studio/main.py) — `main()`: the routes, `mockups.clear_books()` and `mockups.clean_runs()` on launch and close
- [app/web/js/pages/mockups.js](../../app/web/js/pages/mockups.js) — `arrived()`, `paintBack()`, `takeWorkshopBook()`, `existingNow()`, `loadExisting()`, `FOR_BOOK`, `paintHead()`, `finishPage()`, `mount()`, `paintBookState()`, `paintTemplates()`, `ticked()`, `paintPicks()`, `paintOut()`, `paintAction()`, `paintStructure()`, `paintTiles()`, `put()`, `pickZip()`, `takeDrop()`, `make()`, `follow()`, `tellDone()`, `rememberPicks()`, `recallPicks()`, `openPlaces()`
- [app/web/js/pages/mockups-slides.js](../../app/web/js/pages/mockups-slides.js) — step 4, the listing slides: `slidesStep()` ([slides](slides.md))
- [app/web/js/pages/mockups-run.js](../../app/web/js/pages/mockups-run.js) — step 3 drawn: `runView()`, `rowsHtml()`, `resultCard()`, `existingCard()`, `turnCard()`, `finishedCard()`
- [app/web/js/app.js](../../app/web/js/app.js) — the route `#/mockups`, `paintBusy()` (the rail's dot)
- [app/studio/desktop.py](../../app/studio/desktop.py) — `pick_zip()`, `downloads_folder()`, `attention()`
- [app/studio/drops.py](../../app/studio/drops.py) — `export_files()` (the same naming rules as the print folder), `archive_folder()`
- Tests: [app/tests/test_mockups.py](../../app/tests/test_mockups.py) (`ReadingTheDemoBook`, `Pictures`, `RunPlan`, `Run`, `SaidInTheLog`, `Cleaning`, `SaveTheOpenOnes`, `Progress`, `PhotoshopScript` — the script itself run by Node.js against a pretend Photoshop)

## Related

- [Listing slides](slides.md) · [Photo mockups](photo-mockups.md) · [The rail](modes.md) · [Security](../security.md) ·
  [Dragging files](../flows/dropped-files.md) · [Decisions](../decisions.md) · [Preview](../dev/preview.md) ·
  [Launch and shutdown](../architecture/runtime.md)
