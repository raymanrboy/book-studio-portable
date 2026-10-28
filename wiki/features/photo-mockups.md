---
title: Photo mockups — lifestyle photos with our book (the Workshop's «Фото» step and the «Фотомокапи» page)
type: feature
updated: 2026-10-28
code:
  - app/studio/photos.py
  - app/studio/scrub.py
  - app/web/js/pages/photos.js
---
# Photo mockups (Фотомокапи)

> "Live" photos for the Etsy listing: a grandmother reading, a child holding the book, a shelf. The owner prepared
> photos with a **blank white book** (templates); the generator (Gemini or ChatGPT — book 25's photos came from ChatGPT; any
> browser download is caught) swaps that book for ours. Book Studio lays
> the template, the book's cover and a JSON prompt into the clipboard one by one, and catches the finished photo into
> the book's `etsy/` folder. See [decisions](../decisions.md).

## Two places

- **A Workshop book's step «Фото»** (between «Мокапи» and «Бібліотека», `n/7`): the book's references on top
  (Cover 1 · Cover & Open 1 · the Canva cover — ✓ there / what to do), **a card per category** (its photo, or
  an empty frame with a camera; the video category — its video playing silently, or a frame with a film icon), and
  under them **the chosen category's templates**. A click on a template: the
  clipboard holds **the template → the book's reference → the prompt**, one by one (Ctrl+V in Chrome puts in the next,
  as the Workshop's other several-part pastes — `PasteWatch`); the generation bar says what's next. The photo the owner
  downloads is caught from Downloads into `etsy/photo-<category>.<ext>` (the one before → `.replaced/`). A finished card:
  view, «Зберегти як…», remove (to `.replaced/`); a photo dropped onto a card is taken as it is; the template used last is
  marked ✓ (`book.json` → `photos`; only in a category that has its result). **Categories may be skipped** (the owner): the step is done with every category's photo
  (and the video), or ticked by hand («Позначити зробленим»).
- **The «Фотомокапи» page** (`#/photos`, among [«Інструменти»](modes.md), a camera): no book — a click on a
  template puts **the template, then (Ctrl+V) the prompt** into the clipboard and the wait ends; the owner adds the cover
  himself (the owner: "just the blank and the prompt, I'll add the pictures myself"). Nothing is caught. A section per
  category: the prompt alone into the clipboard, the category's folder, **a photo dragged onto a section becomes a new
  template** (named `shelf-06.png` — the category's next number), × — a template into the Recycle Bin, at once with «Скасувати» (it waits 2 min on the program's shelf first).

## Categories — and what goes into the clipboard second

| Key | Shown as | The book's reference (2nd Ctrl+V) |
|---|---|---|
| `main` | Головне фото | `mockups/1. Cover 1*.png` — the drawn mockup of the front |
| `product` | Демонстрація продукту | Cover 1 — hands hold the closed square hardcover, white callouts written on the photo (Hardcover, Premium materials, Your name on the cover, 30 pages). The old category `open-book` («Відкрита книга») is not shown; its templates lie untouched in `app/data/photo-mockups/open-book/` |
| `grandma` | Бабуся читає | `mockups/canva-cover.*` — **the flat cover from the Canva ZIP** (back · spine · front): the grandmother holds the book open towards herself, the camera sees its outside (the owner: take the Canva cover, not a piece of «All & Open 1») |
| `child` | У руках дитини | Cover 1 |
| `shelf` | На полиці | Cover 1 |
| `video` | Для відео | Cover 1 — **a video, not a photo** (see below): 9:16 phone photos of the closed blank book on a sofa, a counter, a table |
| `size` | Розмір | Cover 1 — on both books: two hands hold the small softcover and the large hardcover side by side (the owner's `Трафарети мастхев\Size.jpg`, copied; "a very important mockup"; more of his — a woman holds both books at home, `size-02-nursery` … `size-06-terrace`) |

**«Для відео» — a video in Gemini Omni or Google Flow** (`"omni": True`, the only video card; the owner: "refuse the videos where people hold the book"). The owner animates
the template (the closed blank book on a surface) with the book's Cover 1 — **one step**: the generator swaps the book and
animates in one go. The clipboard goes as for any category — template → Cover 1 → the prompt — and then **a video is
awaited** in Downloads (MP4, MOV, WEBM; pictures there are ignored): **its first 0.5 s are cut off** (`TRIM_SECONDS`, the owner) by **ffmpeg** — encoded again (H.264 + AAC, CRF 16) so the cut is exact, MP4
that plays at once — into `etsy/video-video.mp4`; **the download as it came** goes into the book's
`originals/video-video.<ext>`; the ones before → `.replaced/` (`place_video()`, `trim()`). A video dropped onto the card
goes the same way; one shorter than 0.5 s is refused and nothing changes. ffmpeg is the one Windows finds (installed on the
Wrocław PC), else `app/bin/ffmpeg.exe` (`ffmpeg()`); without it — a clear error. The card plays the video muted and in a
loop; ↗ opens it in Windows' player.
Its prompt (`OMNI_PROMPTS["video"]`) is plain text in the form of the owner's tested Omni prompt: "Animate this exact
scene…", the book **a thin closed book with stiff covers, pressed shut like one rigid board**, **one continuous 8-second
handheld phone shot** (gentle sway, small organic shake, never jerky), then by seconds — **0–3 s** the camera pushes in with
momentum and rises over the book until it looks straight down, the front cover head-on (the templates show the book at an
angle; the book lies still); **3–4 s** **a woman's right hand and forearm enter from the right** and **grip the book by its
lower right corner** — thumb on the cover at the corner, fingers under, clamping the covers together; **4–6.5 s** it lifts the
book towards the camera, the cover still to it, and **tilts it back about 10°** so light glides over the cover, then levels
it; **6.5–8 s** it carries the book **out of the frame to the right**; only the hand and forearm are ever seen; **"small
book" on every mention** — without it the book grew as it came closer.
**Why the prompt is worded so — the generators opened and leafed through the book (the owner):**
(1) **the words name it**: "never opened", "pages never visible", "never flipped" put the very idea into the prompt —
video models follow negations poorly, so **the prompt never says open, page, flip or turn** (a test holds it); the book is
described by what it is (closed, rigid, pressed shut); (2) **the grip**: a right hand from the right meets the book's
fore-edge, where a book is opened — so it takes **the corner**, thumb clamping the covers; (3) **no idle seconds**: a hand
"holding" a book for 3 s is filled by the model with what hands do with books — every second has a motion, and the shot ends
with the book carried out; (4) **a turn without a way**: "turning it upright" flipped it — the life goes into the hand and
the camera, the book only gets a **numbered** tilt (about 10°).
Don't
rewrite it into the JSON frame. `PROMPTS["video"]` (the JSON «swap the book» prompt) stays as the **two-step fallback**:
a photo with our book first, then that photo as Flow's first frame — if the one step spoils the cover; no button reaches
it yet. The old books' `video-hands.mp4` files are not touched (the owner replaces them in the Workshop himself; the card
does not show them — another name).

**The Canva cover** is kept by the Mockups: a run for a Workshop book copies the demo book's cover (as Canva exported
it) into the book's `mockups/canva-cover.*` (`mockups._keep_canva_cover()`); for a book whose mockups were made before,
it can be dropped onto its frame in the step. **Only the finished cover, without the wrap** (the owner:
with the wrap the generator draws a wrong book): a hardcover's cover file is cut to what is inside the contour — back,
spine, front — when it comes in (`trim_box()`, `_save_trimmed()`). It is told by its proportions: Gelato's 458×246 mm,
cut 20 mm all round to 418×206 mm (4937×2434 px), or the Printify template's 17.90×9.50″, cut to 16.40×8.00″. A 2:1
cover has no wrap and stays whole. A cover kept with its wrap before is cut the first time the step opens or its
picture goes to the clipboard (`trim_kept_cover()`); the whole one goes to `.replaced/`. The cut is written beside
first (`_part_of()`), so a failed write leaves the cover there; it is on the book page's way, so it never waits: a cover
held by another program is moved once and otherwise left for the next time.

## The prompts

One **JSON object per photo category** (`photos.PROMPTS`, pretty-printed by `rows.as_prompt()` — the Workshop's own format),
in English. A shared frame: Image 1 is the scene to keep, Image 2 — our book; replace **only** the blank book; **no white
of the blank book may stay** (the owner: "no white parts of the mockup — our book"; cover, spine and edges in our
colours); keep framing, light, people, hands, props, the book's position and bend; the artwork and title exactly as in
Image 2, never mirrored, no invented text. Each category adds its own `image_2`, `scene` and `book_placement` (the
grandmother: back cover on the left half, the spine at the fold, the front on the right; the inside pages not drawn).
Change a prompt there — nothing else holds a copy.

## Where things are

```
app/data/photo-mockups/<category>/<category>-NN-<what>.png   the templates (copies of the owner's set; in the backup)
pipeline/books/<book>/mockups/canva-cover.png                the grandmother's reference
pipeline/books/<book>/etsy/                                  what goes into the listing, numbered (below)
pipeline/books/<book>/originals/video-video.mp4              the video as it was downloaded
```

**`etsy/` in the listing's order** (the owner): every file of the program's there has its number in front
(`tidy_etsy()` — after a photo or video lands or goes, after the Mockups copy their scenes, after the slides are baked):

| № | File | № | File |
|---|---|---|---|
| 01 | `photo-main` | 09 | `Listing 4` |
| 02 | `video-video.mp4` — the video, its first 0.5 s cut | 10 | `photo-child` |
| 03 | `photo-grandma` | 11 | `Listing 2` |
| 04 | `All & Open 1 (…)` — a copy from `mockups/` | 12 | `photo-size` |
| 05 | `photo-product` — the product demonstration | 13 | `Listing 5` |
| 06 | `Listing 1` | 14 | `Listing 6` |
| 07 | `Cover & Open 1 (…)` (a legacy `photo-open-book` of an older book takes its place) | 15 | `photo-shelf` |
| 08 | `Listing 3` | 16 | `Listing 7` — the hero's looks (only a book with them; last in the numbering) |

- A number belongs to its file (`ETSY_ORDER`, `ETSY_SCENES`): a missing one leaves a gap — nothing moves up.
- **A legacy open-book photo takes Cover & Open 1's place**: that copy leaves `etsy/` (to `.replaced/`; the mockup itself stays
  in `mockups/`) and isn't copied again; the photo removed — it comes back.
- Anything else there (an old `video-hands.mp4`, the owner's own files) keeps its name, so it sorts after the numbered ones; the
  owner's own numbered files are never renamed.
- **No metadata in what goes into `etsy/`** (the owner: Etsy reads it). C2PA (the generators' content
  credentials), XMP, EXIF, ICC, DPI, text chunks, comments and whatever
  trails after the picture go; the pixels stay — PNG, JPEG and WEBP are cut chunk by chunk, not encoded again (`scrub.py`).
  Encoded again only when dropping the metadata would change the look: an EXIF rotation, a colour profile other than
  sRGB, a CMYK / RGB-encoded JPEG. **Videos too**: MP4/MOV copied by ffmpeg without tags, dates, the encoder's name and
  C2PA's box (not re-encoded); the video category's trim makes its video so at once (`trim()` → `scrub.VIDEO_CLEAN`).
  Done in `tidy_etsy()` (after every write of the program's) and, for a file the owner drops in by hand, in the
  background when the book's page looks (`detail()` → `scrub.soon()`, a file at least 3 s old).
  **Only what comes in after `NEW_FROM`** (by the file's creation or modification time — a re-baked
  slide is new): the files the books had before are left as they were (the owner). The copies in `mockups/`,
  `originals/`, `.replaced/` keep theirs — only `etsy/` goes to Etsy.
- Everything finds its file by the name without the number (`bare()`): the step's cards, the slides' re-bake
  (`slides.store._baked_file()`), the scenes' copy.

The owner's originals on the desktop (`Заготовки обкладинок`) are not used by the program. Every name inside Book Studio is
English; the page speaks Ukrainian.

## In the preview and the tests

`tools/sample_books.py`: `make_photo_templates()` — made-up scenes with a white book per category (the preview's
`photo-mockups/`), and book 40 has made-up references in its `mockups/` (book 41 has none — the missing states).
Tests — `app/tests/test_photos.py`.

## Where in the code

- [app/studio/photos.py](../../app/studio/photos.py) — `ETSY_ORDER`, `ETSY_SCENES`, `tidy_etsy()`, `bare()`, `etsy_number()`, `SCENES`, `scenes_to_etsy()`, `CATEGORIES`, `PHOTOS`, `REFS`, `PROMPTS`, `OMNI_PROMPTS`, `prompt()`, `place_video()`, `trim()`, `ffmpeg()`, `TRIM_SECONDS`, `templates()`, `signature()`, `template_file()`, `add_template()`, `remove_template()`, `open_folder()`, `references()`, `results()`, `count()`, `state()`, `items()`, `place()`, `remove()`, `set_canva_cover()`, `trim_box()`, `_trims()`, `_part_of()`, `_save_trimmed()`, `trim_kept_cover()`, `_trim_quietly()`, `ETSY`, `CANVA_COVER`
- [app/studio/scrub.py](../../app/studio/scrub.py) — `folder()`, `soon()`, `file()`, `picture()`, `_png()`, `_jpeg()`, `_webp()`, `_redraw()`, `video_dirty()`, `VIDEO_CLEAN`, `NEW_FROM`, `LOCK`, `SETTLE`
- [app/studio/workshop/generate.py](../../app/studio/workshop/generate.py) — `Session.start_photo()` (no catch without a book; `video` — a video awaited), `Session._open()` (`catch=False` — nothing awaited), `look()` (pictures, or videos for a video category), `_catch()` (a photo or a video → `photos.place()`), `next_item()` (the wait ends after the last part when nothing is caught)
- [app/studio/workshop/books.py](../../app/studio/workshop/books.py) — the step `photos` in `STEPS`, `steps()`, `detail()` (`photos`, `scrub.soon()`), `ETSY` in `AREAS`
- [app/studio/workshop/routes.py](../../app/studio/workshop/routes.py) — `_gen_photo()`, `_photos()`, `_photos_sig()`, `_photo_media()`, `_photo_add()`, `_photo_remove()`, `_photo_open()`, `_photo_prompt()`, `_book_photo_remove()`, `_place()` (`photo:<category>`, `canva-cover`)
- [app/studio/mockups.py](../../app/studio/mockups.py) — `_keep_canva_cover()`, `_to_etsy()`
- [app/web/js/pages/photos.js](../../app/web/js/pages/photos.js) — `mount()`: `section()`, `addFiles()`, `remove()`, `zoom()`
- [app/web/js/pages/workshop-book.js](../../app/web/js/pages/workshop-book.js) — `photosBody()`, `templatesOf()`
- [app/web/js/workshop-live.js](../../app/web/js/workshop-live.js) — `startPhoto()`, `watch()` (`sigUrl`), `genBar()` (a wait without a book)
- [app/web/css/listings.css](../../app/web/css/listings.css) — `.ph-*`
- Tests: [app/tests/test_photos.py](../../app/tests/test_photos.py) (`TheTemplates`, `ThePrompts`, `InABook`, `TheOmniVideo`, `WithoutABook`, `TheMockupsKeepTheCanvaCover`), [app/tests/test_scrub.py](../../app/tests/test_scrub.py) (`Pictures`, `TheEtsyFolder`)

## Related

- [Workshop](workshop.md) · [Mockups](mockups.md) · [Listing slides](slides.md) · [The rail](modes.md) · [Decisions](../decisions.md)
