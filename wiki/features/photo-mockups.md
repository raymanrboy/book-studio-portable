---
title: Photo mockups
type: feature
updated: 2026-11-12
code:
  - app/studio/photos.py
  - app/studio/scrub.py
  - app/web/js/pages/photos.js
  - app/web/js/pages/workshop-book.js
---
# Photo mockups (Фотомокапи)

> "Live" photos for the Etsy listing: a grandmother reading, a child holding the book, a shelf, a video. The owner prepared photos with a **blank white book** (templates); the generator (Gemini or ChatGPT; any browser download is caught) swaps that book for ours. Book Studio puts the template, the book's cover and a JSON prompt into the clipboard one by one and catches the finished photo into the book's `etsy/` folder. Two places: the Workshop book's step **«Фото»** and the page **«Фотомокапи»** (`#/photos`, under «Інструменти»).

## Two places
- **Step «Фото»** (`photosBody()`, `templatesOf()`; step `photos` in `workshop/books.py`): the book's references on top (Cover 1, Cover & Open 1, the Canva cover — ✓ or what to do), **a card per category** (its photo, or an empty frame; the video card plays muted in a loop), and under them the chosen category's templates. A click on a template puts into the clipboard **the template → the book's reference → the prompt**, one by one (Ctrl+V in Chrome advances, `PasteWatch`). The photo downloaded is caught from Downloads into `etsy/photo-<category>.<ext>` (the previous one → `.replaced/`). A finished card: view, «Зберегти як…», remove; a photo dropped onto a card is taken as is. The last template used is marked ✓ (`book.json` → `photos`, only in a category that has a result). Categories may be skipped; the step is done when every category (video included) has a result, or by hand.
- **Page «Фотомокапи»**: no book. A click on a template puts the template, then the prompt, into the clipboard; the owner adds the cover himself; nothing is caught. A section per category: the prompt alone, the category's folder, and a photo dropped onto a section becomes a new template (next number, `shelf-06.png`). Removing a template acts at once with «Скасувати»; it waits 2 min on the program's shelf, then goes to the Recycle Bin.

## Categories
Exactly seven (`photos.CATEGORIES`); the six photo ones are `PHOTOS`, each with a JSON prompt in `photos.PROMPTS`.

| Key | Shown as | The book's reference (second paste) |
|---|---|---|
| `main` | Головне фото | `mockups/1. Cover 1*.png`, the drawn front |
| `product` | Демонстрація продукту | Cover 1 — hands hold the closed hardcover, white callouts on the photo |
| `grandma` | Бабуся читає | `mockups/canva-cover.*` — the flat Canva cover (back, spine, front) |
| `child` | У руках дитини | Cover 1 |
| `shelf` | На полиці | Cover 1 |
| `video` | Для відео | Cover 1 — **a video, not a photo** |
| `size` | Розмір | Cover 1 — two hands hold the small softcover and the large hardcover side by side |

## Video
`video` has `omni: True`: the owner animates the template (the closed blank book on a surface) with the book's Cover 1 in Gemini Omni or Google Flow, **in one step**.
- The clipboard goes as for any category; then a **video** is awaited in Downloads (MP4, MOV, WEBM; pictures are ignored). Its first `TRIM_SECONDS` = 0.5 s is cut off with ffmpeg (re-encoded H.264 + AAC, CRF 16, so the cut is exact) into `etsy/video-video.mp4`; the download as it came goes to `originals/video-video.<ext>`; the previous video → `.replaced/` (`place_video()`, `trim()`). A video dropped onto the card goes the same way; one shorter than 0.5 s is refused.
- ffmpeg is found by `photos.ffmpeg()`: the portable runtime, else PATH, else `app/bin/ffmpeg.exe`; without it the error says so.
- The prompt `OMNI_PROMPTS["video"]` is plain text: a thin closed book with stiff covers, pressed shut like one rigid board; one continuous 8-second handheld shot; by seconds — the camera pushes in and rises until it looks straight down, a right hand and forearm enter and grip the book by its lower right corner, lift it, tilt it back about 10°, and carry it out of the frame to the right. "small book" appears on every mention.
- `PROMPTS["video"]` (the JSON «swap the book» prompt) is the two-step fallback (a photo with our book, then that photo as Flow's first frame); no button reaches it.
- No video where people hold the book; only the hand and forearm are shown.

## The Canva cover
A Mockups run for a Workshop book copies the demo book's cover as Canva exported it into `mockups/canva-cover.*` (`mockups._keep_canva_cover()`); it can also be dropped onto its frame in the step. **Only the finished cover without the wrap** is kept: a hardcover cover file is cut to what is inside the contour when it comes in (`trim_box()`, `_save_trimmed()`, `trim_kept_cover()`). Gelato's 458×246 mm is cut 20 mm all round to 418×206 mm; a 2:1 cover has no wrap and stays whole; the whole file goes to `.replaced/`. The cut is written beside first, so a failed write leaves the cover there.

## The prompts
One JSON object per category (`photos.PROMPTS`, pretty-printed by `rows.as_prompt()`), in English. Shared frame: Image 1 is the scene to keep, Image 2 is our book; replace **only** the blank book; **no white of the blank book may stay** (cover, spine and edges in our colours); keep framing, light, people, hands, props, the book's position and bend; the artwork and title exactly as in Image 2, never mirrored, no invented text. Each category adds its own `image_2`, `scene` and `book_placement` (grandmother: back cover on the left half, spine at the fold, front on the right). Edit prompts only in `photos.PROMPTS`; nothing else holds a copy. A literal `{Name}` in inside-page text of a listing mockup is on purpose.

## `etsy/` — the listing's order
Every file the program puts there has its number in front (`tidy_etsy()` runs after a photo or video lands or goes, after the Mockups copy their scenes, after the slides are baked). This is the one home of the table; [slides](slides.md) and [workshop](workshop.md) link here.

| № | File | № | File |
|---|---|---|---|
| 01 | `photo-main` | 09 | `Listing 4` |
| 02 | `video-video.mp4` | 10 | `photo-child` |
| 03 | `photo-grandma` | 11 | `Listing 2` |
| 04 | `All & Open 1 (…)`, a copy from `mockups/` | 12 | `photo-size` |
| 05 | `photo-product` | 13 | `Listing 5` |
| 06 | `Listing 1` | 14 | `Listing 6` |
| 07 | `Cover & Open 1 (…)`; a file named `photo-open-book` takes its place | 15 | `photo-shelf` |
| 08 | `Listing 3` | 16 | `Listing 7` (the hero's looks, only a book that has them) |

- A number belongs to its file (`ETSY_ORDER`, `ETSY_SCENES`): a missing one leaves a gap, nothing moves up. Unknown files keep their name and sort after the numbered ones; the owner's own numbered files are never renamed.
- `bare()` strips the number: the step's cards, the slides' re-bake and the scenes' copy find their file by the bare name.
- **No metadata in `etsy/`** (Etsy reads it). `scrub.py` removes C2PA, XMP, EXIF, ICC, DPI, text chunks and trailing data chunk by chunk from PNG, JPEG and WEBP; it re-encodes only when keeping the metadata would change the look (EXIF rotation, a non-sRGB profile, CMYK). Videos are copied by ffmpeg without tags (`VIDEO_CLEAN`). It runs in `tidy_etsy()` and, for a file the owner drops in by hand, in the background when the book page looks (`scrub.soon()`, file at least 3 s old). Only files newer than `scrub.NEW_FROM` are scrubbed. Copies in `mockups/`, `originals/` and `.replaced/` keep their metadata.

## Where things are
```
app/data/photo-mockups/<category>/<category>-NN-<what>.png   the templates (in the backup)
pipeline/books/<book>/mockups/canva-cover.png                the grandmother's reference
pipeline/books/<book>/etsy/                                  the listing's files, numbered
pipeline/books/<book>/originals/video-video.<ext>            the video as downloaded
```
The preview ([preview](../dev/preview.md)) builds made-up scenes with a white book per category (`tools/sample_books.py`).

## Why
- The video prompt never says open, page, flip or turn: video models follow negations poorly, so the book is described by what it is (closed, rigid, pressed shut), the hand grips the corner (not the fore-edge, where a book opens), every second has a motion (an idle hand gets filled with opening the book), and the book gets a numbered tilt instead of "turn". A test holds it. Do not rewrite it as JSON.
- The grandmother uses the flat Canva cover, never a piece of a mockup, and only the finished cover without wrap, or the generator draws a wrong book.
- Photo templates carry a blank WHITE book so the generator swaps only the book.
- No metadata in `etsy/`: Etsy reads it.

## Where in the code
- [app/studio/photos.py](../../app/studio/photos.py) — `CATEGORIES`, `PROMPTS`, `OMNI_PROMPTS`, `ETSY_ORDER`, `tidy_etsy()`, `place_video()`, `trim()`, `ffmpeg()`, `TRIM_SECONDS`
- [app/studio/scrub.py](../../app/studio/scrub.py) — `soon()`, `NEW_FROM`, `VIDEO_CLEAN`
- [app/studio/mockups.py](../../app/studio/mockups.py) — `_keep_canva_cover()`, `_to_etsy()`
- [app/web/js/pages/photos.js](../../app/web/js/pages/photos.js) — `mount()`; [workshop-book.js](../../app/web/js/pages/workshop-book.js) — `photosBody()`, `templatesOf()`

## Related
- [Workshop](workshop.md) · [Mockups](mockups.md) · [Slides](slides.md) · [Cover](cover.md) · [Rail](rail.md)
