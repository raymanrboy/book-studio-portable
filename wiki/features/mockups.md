---
title: Mockups — listing pictures from a demo book (the Listings mode)
type: feature
updated: 2026-09-24
code:
  - app/studio/mockups.py
  - app/studio/mockups.jsx
  - app/web/js/pages/mockups.js
---
# Mockups (Мокапи)

> A page of Book Studio's **Listings mode** (`#/mockups`, Alt+2 there — [two modes](modes.md)): bring in the
> demo book's Canva ZIP, click the "presentable" spreads, pick a folder — one Photoshop script fills the
> owner's mockup templates and saves **7 PNG pictures**; the **3 templates where the front cover really
> shows** are left open in Photoshop for the owner to fit the cover by hand, and **«Зберегти відкриті»** then
> saves those 3 as well. Built on 2026-09-23 as a separate utility from the
> [plan](../plans/listing-mockups.md) (the templates' structure and the agreements live there); **moved into
> Book Studio on 2026-09-24**, working exactly as before (the owner: "Ні, як зараз" — not tied to library
> books).

## How the owner uses it

The page looks like Book Studio's Order Creator (the owner's request, 2026-09-23 evening: "exactly like
Book Studio, with the search", i.e. the path field with the folder-and-magnifier button): **four numbered
steps on the left**, the **demo book's structure on the right**. A step's number turns into a green ✓ when
it is done. **The page is kept when the owner steps away** (another page, the orders): the book, the picks, a
run in Photoshop and its result wait for him; while a run goes on elsewhere, a cyan dot sits on the rail,
and a notice says when it ends («Мокапи: готово · 7 картинок»).

1. **Демо-книга з Canva.** Drag the ZIP anywhere onto the window (the book field lights up), or press the
   field / its folder button — the Windows dialog opens in the Downloads folder the first time, then where
   the last ZIP was (`lastZip`). The unpacked folder or the pictures themselves can be dragged too. The
   badge says what is going on: «Вікно Windows», «Розпаковую», the upload percent, then «✓ 24 стор.».
   The pages are read by the same rules as the print folder ([file naming](../rules/file-naming.md)):
   the cover is the file named `cover`… or the one wide picture, the rest go by the number in the name
   and become pages 1…N. Page 1 is the dedication; the spreads are `2–3`, `4–5`, … (page 30, the
   afterword, is alone and not offered). Before a book is in, the right side shows the structure's outline
   under a dashed veil «Перетягніть сюди ZIP із Canva» (a click there opens the dialog too).
2. **Розвороти в шаблонах.** Each template is a row with **its own preview** (the picture Photoshop keeps
   inside the PSD, read by Pillow — the file is only read) and its slots: **Open 1 ×4, Open 2 ×2,
   Cover & Open 1 ×1, All & Open 1 ×1**; **Dedication** (page 1) and **Cover 1** (the cover) go in by
   themselves. The ✋ mark — the front cover is the owner's. A click on a template's preview opens all six
   templates large.
   - **Click a spread** on the right → it goes into the highlighted slot, and the next empty slot lights
     up. The structure's header says where the next click goes («Клацніть розворот → Open 1 · 3»), and
     hovering a spread shows the same on it («+ Open 1 · 3»).
   - **Drag** a spread onto any slot, or a slot onto another (the two swap).
   - A click on a slot highlights it (the next spread replaces it); × on a slot or on a spread's template
     chip empties it; Delete/Backspace on a slot too; the eraser empties all.
   - The magnifier opens a spread large, with «Обрати» there.
   - **A book dropped in again gets its picks back** (the last 12 books, by name and page count — the
     window's own memory, `localStorage`), with a toast saying so.
3. **Куди зберегти.** The folder field with its folder button (the Windows dialog, starting in the last
   folder). «Та сама, що минулого разу · <name>» takes the last folder in one click. A new book starts
   with the field empty — the folder is picked for every book (the owner's rule). No folder yet when
   «Зробити мокапи» is pressed → the dialog opens then.
4. **Photoshop.** One line says what will happen («Photoshop сам збереже 7 картинок, а 3 шаблони залишить
   відкритими…»), then **«Зробити мокапи»**. The button **always answers** (since 2026-09-23): no book →
   the book field blinks and a toast asks for the ZIP; empty slots → they blink amber, the first one is
   highlighted and a toast names the templates; while the folder dialog is open the card says so; closed
   without a folder → «Папку не вибрано — мокапи не робились».
   - **While it runs**: every template is a row — waiting, in work (highlighted, a spinner), done (✓) —
     with its pictures counted («2/4») or «✋ лишиться відкритим»; a progress bar; × stops. While
     Photoshop asks "run this script?", the card draws that dialog small with its **Yes** pulsing and
     says «Натисніть «Yes» у його вікні — далі все саме».
   - **Done**: a green card «Готово · 7 картинок · 45 с» with **the saved pictures themselves** (their
     previews; a click opens them large, the viewer's "original" button opens the file) and the folder
     button. When Book Studio's window isn't in front (the owner watches Photoshop), **its taskbar button
     flashes, Windows plays its notification sound and the title says «Готово · 7 картинок · Book Studio»** —
     the owner's question "is there any message that it's finished?".
   - **«Ваша черга — у Photoshop»** (amber): the templates left open are named; after fitting the front
     cover in each, **«Зберегти відкриті й закрити»** runs a second, short script (one more "Yes") that
     saves them as PNG into the same folder, named like the rest (`1. Cover 1.png`,
     `Cover & Open 1 (20-21).png`, `All & Open 1 (22-23).png`, never overwriting), closes them and removes
     their copies — «Збережено ще 3 картинки · Тимчасові копії шаблонів прибрано». Saving them by hand
     as before still works; the copies are then cleaned up by themselves (below). A reloaded window
     offers the button again (`pending()`).

The sliders button in the header: **where the templates and Photoshop are** (path fields with folder
buttons and a ✓/✗ line). A missing folder also shows a yellow line above the steps.

A whole run from a cold Photoshop start took **37 s** on the owner's PC (2026-09-23, made-up book), the
owner's own first run with a real demo book **45 s**: ~3 s preparing the pictures, <1 s copying 1.5 GB of
templates, the rest Photoshop.

## What goes where

| Template | Spreads | The script puts in | Result |
|---|---|---|---|
| `2. Open 1` | 4 | the spread's pages, the back, the spine, the front cover's rim | 4 PNG |
| `3. Open 2` | 2 | the same | 2 PNG |
| `4. Dedication` | — | page 1, the back, the spine, the rim | 1 PNG |
| `1. Cover 1` | — | nothing (its only layer is the front cover) | left open → «Зберегти відкриті» |
| `Cover & Open 1` | 1 | the spread's pages | left open → «Зберегти відкриті» |
| `All & Open 1` | 1 | the spread's pages, the back, the spine | left open → «Зберегти відкриті» |

- **Pictures are cut by Python (Pillow) at exactly the smart object's size, 300 dpi**
  (`cover_pictures()`, `page_picture()`): the back — the left half of the wide cover, the front (only for
  the rims) — the right half, each scaled to **fill** its board and centred; the spine — the strip from
  the exact middle at the halves' scale; pages — filled into the square (a non-square page loses its
  edges, a see-through one lies on white). Sizes: hardcover templates (1–4) pages 1900², boards
  2100×2200, spine 80×2200; the square softcover (B) pages and boards 1935², spine 164×1935 (`HARD`,
  `SOFT`). This "fill and centre" rule is still to be checked by the owner on a real book.
- **Names**: `<template> (<pages>).png` — `2. Open 1 (6-7).png`, `3. Open 2 (12-13).png`,
  `4. Dedication.png`, `1. Cover 1.png` (sorted by template, like the owner's numbering). An existing file
  is **never overwritten**: ` (2)`, ` (3)` are added (`_free_name()`). Not confirmed by the owner yet.
- **PNG**, Photoshop compression 3 (`PNG_COMPRESSION`): 4000×2670, ≈ 5 MB each, 300 dpi.

## How it works inside

1. `plan()` decides everything first: the pictures to make, the template copies, which layer gets which
   picture, the output names, the spread each template left open holds (`spread` — for its later name).
   A wrong choice (a missing slot, not the start of a spread) is refused at once.
2. `prepare()` makes the pictures, `copy_templates()` copies **all six templates** into the run's folder
   `app/data/mockups/work/<time>-<id>/templates/` — Photoshop never opens a template from
   `Трафарети мастхев` ([security](../security.md) rule 10).
3. `script()` writes one `mockups.jsx`: the job as a JavaScript literal (`var JOB = …`, ASCII only —
   Cyrillic folder names travel as `\u` escapes) in front of the fixed [mockups.jsx](../../app/studio/mockups.jsx).
   `job.json` beside it — the same job, readable.
4. `launch()` hands it to Photoshop: if Photoshop runs — through `Photoshop.exe`, if not — through the
   portable launcher `Photoshoр.exe` (Cyrillic "р", found by the mask `Photosho*.exe`; keeps the settings
   off drive C), with its temp folder set to `data/mockups/tmp/photoshop` on D. **One script per run → one
   "Yes"**.
5. The script (ExtendScript, Photoshop CC 2019): for every template — open the copy, "Replace Contents"
   of each smart object by the layer path (names compared with spaces trimmed; a one-name path is looked
   for at the top of the layer list, where the owner's shortcut copies are), put the layer's and its
   groups' visibility back (selecting a hidden layer shows it), then per spread — swap the pages and save
   a PNG **copy**; the automatic templates close **without saving**, the three with the owner's cover stay
   open, and the first of them becomes the active document. Photoshop's "show dialogs" setting is put back.
   Replacing and saving always act on the **active** document (seen live: a copy "saved" from another
   document held the active one's picture), so the script activates its document first.
6. `watch()` follows `status.json` the script writes (step, saved, left open, problems) and hands the page
   `progress_view()` — every template's state and the pictures saved so far (`job.share()`). No status for
   10 min (`START_WAIT`) → "Photoshop never ran the script" (and the stop mark is left, so a late "Yes"
   does nothing); Photoshop gone for 3 checks → "Photoshop closed". Stop → the file `cancel`, checked by
   the script before every template and picture.
7. **«Зберегти відкриті»** — `finish()`: `finish_plan()` reads the run's `job.json`, names the pictures,
   and the same script runs with `JOB.finish`: it finds each copy among Photoshop's open documents (by its
   path, else by its file name), saves a PNG copy, closes it without saving; one the owner already closed
   is reported («…уже не відкритий у Photoshop — його не збережено»), its copy stays. Its own status is
   `finish-status.json` (an earlier try's is deleted first).

## Temporary files — what is left and when it goes

The owner: "are there many temporary files, does it clean up after itself?" and "keep drive C clean — any
temporary file must go when the work is done" (2026-09-23). What a run makes, all on drive **D** in
`app/data/mockups/`:

| What | Size (a 24-page 4K book) | Goes |
|---|---|---|
| `mockups/work/<run>/pictures/` — the prepared pages, back, spine | ~50 MB | right after the script finishes (the smart objects hold them now) |
| `mockups/work/<run>/templates/` — copies of the 3 closed templates | ~1.2 GB | right after the run |
| `mockups/work/<run>/templates/` — copies of the 3 left open | ~470 MB | after «Зберегти відкриті»; otherwise at once when Photoshop is closed (checked on launch, before every run, when Book Studio closes), at most a day later with Photoshop open (`KEEP_RUNS`) |
| a copy the owner saved himself (Ctrl+S in Photoshop lands there) | — | kept a week (`KEEP_SAVED`), so his work is never lost |
| `mockups/book/` — the unpacked demo book (`BOOKS`) | ~200 MB | when another book comes in, when Book Studio closes, on launch |
| `tmp/photoshop/` — temp files of a Photoshop started from here | — | once Photoshop is closed |
| `tmp/system/` — temp files of the window, the dialogs | — | on launch and when Book Studio closes |
| `cache/thumbs/` — previews of pages, templates, results | ~10 MB a book | not used for 21 days (`images.prune_cache()`) |

**The demo book has a folder of its own** (`app/data/mockups/book/`, since 2026-09-24): a dropped ZIP arrives
among the files dropped for orders (`tmp/dropped/<session>`) and its session is moved out at once
(`_take_dropped()`, the same drive — instant); a ZIP picked in the dialog is unpacked straight there. The
separate utility wiped *all* dropped files when a new demo book came in — inside Book Studio that would have
removed the files just dropped into an order's card; and Book Studio's own cleaning of dropped files (older
than 2 hours, on every drop) would have taken the demo book from under a run. Now each cleans only its own.

**What the separate utility left** in its data folder `app/data/mockups/` — its temp files (`tmp/`, ~218 MB on
the owner's PC), previews (`cache/`, ~11 MB) and window profile (`window-profile/`, ~71 MB) — goes once, on
Book Studio's first launch after the move (`forget_old_utility()`, `OLD_UTILITY`); `places.json`, `work/` and
`logs/` stay.

Nothing goes to drive C: the program, the Edge window and the Windows dialogs get their temp folder inside
the data folder (`core.own_temp()`, [runtime](../architecture/runtime.md#temporary-files-and-drive-c)); the
portable Photoshop keeps its settings and temp in `…\Portable Adobe Photoshop\Data\`. Only the pictures in
the owner's folder, `places.json` and the log stay.

## Inside Book Studio (since 2026-09-24)

- The routes are Book Studio's own (`import mockups` in `main.py`); the page is `pages/mockups.js` with the
  usual `mount()` and `keep()`/`revive()`, reached from the Listings mode's rail. Until 2026-09-24 it was a
  program of its own (`Mockups.pyw`, `mockups_app.py`, `mockups.html`, port 47831, the shortcut «Мокапи») —
  all removed; the owner deletes the old shortcut from the desktop.
- **Its files stay where they were** — the utility's data folder was `app/data/mockups`, and the paths are
  now `core.data_path("mockups", …)`: `places.json` (the templates' and Photoshop's folders, `lastOut`,
  `lastZip`) and `work/` (a run whose templates wait for «Зберегти відкриті») carry over as they are.
- Book Studio's closing waits for a run still copying or watching Photoshop (`jobs.any_running()`), as the
  utility did; on launch and on close the demo book goes and the runs are cleaned (`clear_books()`,
  `clean_runs()`).
- The theme is Book Studio's own (the utility read it from `settings.json`); the taskbar flash looks for the
  window titled «Book Studio» (`core.APP_NAME`).
- Where things are: the templates `D:\Roman\Desktop\Трафарети мастхев`, Photoshop
  `D:\Programs\Portable\Photoshop_Portable` (`TEMPLATES_DIR`, `PHOTOSHOP_DIR`); the sliders button or the
  yellow line points elsewhere (saved in `places.json`).
- Output **may not be the templates folder** (refused in the dialog and in the run).

## When something goes wrong

Book Studio's log `app/data/logs/app.log` (the utility's own was `app/data/mockups/logs/app.log`) — the lines `Mockups: …`: the ZIP dialog and the folder dialog opened /
closed (and what was picked), the book read (name, pages, spreads), the run started (folder, spreads),
finished (how many saved, left open, problems) or stopped (at which step, why) — `_logged()`; the same for
«Зберегти відкриті». A run's own files are in `app/data/mockups/work/<time>-<id>/` (`job.json`,
`status.json`, `mockups.jsx`, `finish.json`, `finish-status.json`) while the run is kept.

The owner's "I press it and nothing happens" (2026-09-23 evening) was traced this way: no `work/` folder, no
`places.json` — the run never started; the folder dialog opened in front in every reproduction (also from an
Edge app window right after a real click), so the silent greyed-out button was the cause.

## What was checked

**2026-09-24 (inside Book Studio):** the tests (`test_mockups.py`, 40: the dropped demo book moves into the
mockups' own folder, a folder that is no book isn't kept, a new book clears only the mockups' folder — an
order's dropped files stay, Book Studio's cleaning of dropped files never takes the demo book, the old
utility's leftovers go and its places, runs and logs stay; the ZIP from the dialog unpacks into the own
folder); the preview server (`dev_server.py --sample`, a pretend Photoshop): the page in the Listings mode, the
ZIP through the dialog, 8 spreads, a whole run; the owner steps into the orders mid-run — the dot on the brand
icon, «Мокапи: готово · 7 картинок», back in the listings the page as left with its result and «Ваша черга —
у Photoshop». **Not checked live:** the real Photoshop inside Book Studio.

**2026-09-23 (the separate utility):**

- Tests `test_mockups.py`: reading a Canva export, the cuts (back/front/spine by colour), sizes and dpi,
  the plan (every layer, the front cover never touched, names, wrong picks), the run with a pretend
  Photoshop, stop, Photoshop closing, **the cleaning rules** (Photoshop closed / open, a copy the owner
  saved, Photoshop's temp, one book at a time, a picked ZIP only read, the program's own temp folder),
  **«Зберегти відкриті»** (names, the run gone, a template the owner closed, Photoshop closed), the
  progress rows, **and the script itself run by Node.js against a pretend Photoshop** (layer lookup with
  trailing spaces and nested same-named layers, hidden copies stay hidden, a missing layer, the stop mark,
  "save" taking the active document, the second script finding the open copies and closing them).
- The window on the preview server (`dev_server.py --mockups`: made-up templates with pictures, a made-up
  Canva ZIP, a pretend Photoshop): the empty state, the ZIP button, clicks and drags into slots, the
  missing-book and missing-slot answers, the run's rows and the "Yes" drawing, the result with the pictures,
  «Зберегти відкриті» (all 10 files named right, the run folder gone), picks back for a re-dropped book,
  the light theme, the sliders window.
- **Live, on the owner's PC** (the first version): the real Photoshop, copies of the real templates, a
  made-up demo book — all 7 pictures and the 3 open templates came out right; the owner's own run with a
  real demo book the same evening: 7 saved in 45 s, no problems.
- **Not checked live:** the second script («Зберегти відкриті») in the real Photoshop (only against the
  pretend one), the taskbar flash and sound in the real window, the ZIP dialog on the owner's PC.

## Where in the code

- [app/studio/mockups.py](../../app/studio/mockups.py) — `_logged()`, `TEMPLATES`, `RUN_ORDER`, `HARD`, `SOFT`, `TEMPLATES_DIR`, `PHOTOSHOP_DIR`, `PHOTOSHOP_TEMP`, `PLACES`, `WORK`, `BOOKS`, `OLD_UTILITY`, `KEEP_RUNS`, `KEEP_SAVED`, `START_WAIT`, `read_book()`, `book_view()`, `_only_this_book()`, `clear_books()`, `_take_dropped()`, `forget_old_utility()`, `cover_pictures()`, `page_picture()`, `plan()`, `prepare()`, `copy_templates()`, `script()`, `finish_plan()`, `find_photoshop()`, `running()`, `launch()`, `progress_view()`, `watch()`, `make()`, `finish()`, `pending()`, `clean_runs()`, `_saved_by_owner()`, `state()`, `_free_name()`, `_problem_text()`, `_pick_zip()`, `_open_zip()`, `_open_book()`, `_attention()`, `_template_media()`, `_out_media()`
- [app/studio/mockups.jsx](../../app/studio/mockups.jsx) — `findLayer()`, `replaceContents()`, `fill()`, `savePng()`, `runTemplate()`, `findOpen()`, `finishOpen()`, `report()`, `cancelled()`
- [app/studio/main.py](../../app/studio/main.py) — `main()`: the routes, `clear_books()`, `forget_old_utility()` and `clean_runs()` on launch and close
- [app/web/js/pages/mockups.js](../../app/web/js/pages/mockups.js) — `mount()`, `paintBook()`, `paintTemplates()`, `paintPicks()`, `paintOut()`, `paintAction()`, `paintStructure()`, `paintTiles()`, `put()`, `pickZip()`, `takeDrop()`, `make()`, `follow()`, `tellDone()`, `rememberPicks()`, `recallPicks()`, `openPlaces()`
- [app/web/js/app.js](../../app/web/js/app.js) — the route `#/mockups`, `paintBusy()` (the rail's dot)
- [app/studio/desktop.py](../../app/studio/desktop.py) — `pick_zip()`, `downloads_folder()`, `attention()`
- [app/studio/drops.py](../../app/studio/drops.py) — `export_files()` (the same naming rules as the print folder), `archive_folder()`
- Tests: [app/tests/test_mockups.py](../../app/tests/test_mockups.py) (`ReadingTheDemoBook`, `Pictures`, `RunPlan`, `Run`, `SaidInTheLog`, `Cleaning`, `SaveTheOpenOnes`, `Progress`, `PhotoshopScript`)

## Related

- [Two modes](modes.md) · [The plan and the templates](../plans/listing-mockups.md) · [Security](../security.md) ·
  [Dragging files](../flows/dropped-files.md) · [Decisions](../decisions.md) · [Preview](../dev/preview.md) ·
  [Launch and shutdown](../architecture/runtime.md)
