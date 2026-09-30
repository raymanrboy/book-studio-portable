---
title: Photo mockups — lifestyle photos with our book (the Workshop's «Фото» step and the «Фотомокапи» page)
type: feature
updated: 2026-09-30
code:
  - app/studio/photos.py
  - app/web/js/pages/photos.js
---
# Photo mockups (Фотомокапи)

> "Live" photos for the Etsy listing: a grandmother reading, a child holding the book, a shelf. The owner prepared
> photos with a **blank white book** (templates); the generator (Gemini or ChatGPT — book 25's photos came from ChatGPT; any
> browser download is caught) swaps that book for ours. Book Studio lays
> the template, the book's cover and a JSON prompt into the clipboard one by one, and catches the finished photo into
> the book's `etsy/` folder. Built 2026-09-30 from the owner's request — see [decisions](../decisions.md).

## Two places

- **A Workshop book's step «Фото»** (between «Мокапи» and «Бібліотека», `n/8`): the book's references on top
  (Cover 1 · Cover & Open 1 · the Canva cover — ✓ there / what to do), **a card per category** (its photo, or
  an empty frame with a camera; the video category — its video playing silently, or a frame with a film icon), and
  under them **the chosen category's templates**. A click on a template: the
  clipboard holds **the template → the book's reference → the prompt**, one by one (Ctrl+V in Chrome puts in the next,
  as the Workshop's other several-part pastes — `PasteWatch`); the generation bar says what's next. The photo the owner
  downloads is caught from Downloads into `etsy/photo-<category>.<ext>` (the one before → `.replaced/`). A finished card:
  view, «Зберегти як…», remove (to `.replaced/`); a photo dropped onto a card is taken as it is; the template used last is
  marked ✓ (`book.json` → `photos`). **Categories may be skipped** (the owner): the step is done with every category's photo
  (and the video), or ticked by hand («Позначити зробленим»).
- **The «Фотомокапи» page** (`#/photos`, among [«Інструменти»](modes.md) since 2026-09-30, a camera): no book — a click on a
  template puts **the template, then (Ctrl+V) the prompt** into the clipboard and the wait ends; the owner adds the cover
  himself (the owner: "just the blank and the prompt, I'll add the pictures myself"). Nothing is caught. A section per
  category: the prompt alone into the clipboard, the category's folder, **a photo dragged onto a section becomes a new
  template** (named `shelf-06.png` — the category's next number), × — a template into the Recycle Bin.

## Categories — and what goes into the clipboard second

| Key | Shown as | The book's reference (2nd Ctrl+V) |
|---|---|---|
| `main` | Головне фото | `mockups/1. Cover 1*.png` — the Photoshop mockup of the front |
| `open-book` | Відкрита книга | `mockups/Cover & Open 1*.png` (the newest) — the book closed and open, as in the template |
| `grandma` | Бабуся читає | `mockups/canva-cover.*` — **the flat cover from the Canva ZIP** (back · spine · front): the grandmother holds the book open towards herself, the camera sees its outside (the owner: take the Canva cover, not a piece of «All & Open 1») |
| `child` | У руках дитини | Cover 1 |
| `shelf` | На полиці | Cover 1 |
| `video` | Для відео | Cover 1 — 9:16 phone photos, the closed book on a sofa, a counter, a table (for the listing's video) |
| `hands` | Книга в руках у людини | Cover 1 — **a video, not a photo** (see below): a woman, face out of frame, holds the blank book (9:16) |
| `size` | Розмір | Cover 1 — on both books: two hands hold the small softcover and the large hardcover side by side (the owner's `Трафарети мастхев\Size.jpg`, copied; "a very important mockup"; five more of his — a woman holds both books at home, `size-02-nursery` … `size-06-terrace`) |

«Для відео» joined the same evening (the owner: "there are only three photos, without the women" — he took the others out).

**«Книга в руках у людини» — a video in Gemini Omni** (`"omni": True`, the seventh card). The owner animates the template
(a woman holding the blank book) with the book's Cover 1 in **Gemini Omni**. The clipboard goes as for any category —
template → Cover 1 → the prompt — and then **a video is awaited** in Downloads (MP4, MOV, WEBM; pictures there are
ignored): **its first 2 seconds are cut off** (the owner; `TRIM_SECONDS`) by **ffmpeg** — encoded again (H.264 + AAC,
CRF 16) so the cut is exact, MP4 that plays at once — into `etsy/video-<category>.mp4`; **the download as it came**
goes into the book's `originals/video-<category>.<ext>`; the ones before → `.replaced/` (`place_video()`, `trim()`).
A video dropped onto the card goes the same way; one shorter than 2 s is refused and nothing changes. ffmpeg is the
one Windows finds (installed on the Wrocław PC), else `app/bin/ffmpeg.exe` (`ffmpeg()`); without it — a clear error.
The card plays the video muted and in a loop; ↗ opens it in Windows' player.
Its prompt is **the owner's own, tested in Omni, word for word** (`OMNI_PROMPTS`) — plain text, not JSON: "Animate this
exact scene…", the book held flat and facing the camera, a step closer, a slight steering-wheel rock, never turned,
flipped or opened, the face never seen; **"small book" on every mention** — without it the book grew as it came closer.
Don't rewrite it into the JSON frame. The templates — the owner's `Desktop\Книга в руках у людини` (five 9:16 photos,
copied as `hands-01-living-room` … `hands-05-workspace`).

**The Canva cover** is kept by the Mockups: a run for a Workshop book copies the demo book's cover (as Canva exported
it) into the book's `mockups/canva-cover.*` (`mockups._keep_canva_cover()`); for a book whose mockups were made before,
it can be dropped onto its frame in the step.

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
pipeline/books/<book>/originals/video-hands.mp4              the Omni video as it was downloaded
```

**`etsy/` in the listing's order** (the owner, 30.09.2026): every file of the program's there has its number in front
(`tidy_etsy()` — after a photo or video lands or goes, after the Mockups copy their scenes, after the slides are baked):

| № | File | № | File |
|---|---|---|---|
| 01 | `photo-main` | 08 | `Listing 4` |
| 02 | `video-hands.mp4` — the Omni video, its first 2 s cut | 09 | `photo-child` |
| 03 | `photo-grandma` | 10 | `Listing 2` |
| 04 | `All & Open 1 (…)` — a copy from `mockups/` | 11 | `photo-size` |
| 05 | `Listing 1` | 12 | `Listing 5` |
| 06 | `photo-open-book` when there is one, else `Cover & Open 1 (…)` | 13 | `Listing 6` |
| 07 | `Listing 3` | 14 | `photo-shelf` |

- A number belongs to its file (`ETSY_ORDER`, `ETSY_SCENES`): a missing one leaves a gap — nothing moves up.
- **The open-book photo takes Cover & Open 1's place**: that copy leaves `etsy/` (to `.replaced/`; the mockup itself stays
  in `mockups/`) and isn't copied again; the photo removed — it comes back.
- Anything else there (`photo-video`, the owner's own files) keeps its name, so it sorts after the numbered ones; the
  owner's own numbered files are never renamed.
- Everything finds its file by the name without the number (`bare()`): the step's cards, the slides' re-bake
  (`slides.store._baked_file()`), the scenes' copy.

The owner's originals on the desktop (`Заготовки обкладинок`) were copied once with English names (2026-09-30) and are
not used by the program. Every name inside Book Studio is English; the page speaks Ukrainian.

## In the preview and the tests

`tools/sample_books.py`: `make_photo_templates()` — made-up scenes with a white book per category (the preview's
`photo-mockups/`), and book 40 has made-up references in its `mockups/` (book 41 has none — the missing states).
Tests — `app/tests/test_photos.py`.

## Where in the code

- [app/studio/photos.py](../../app/studio/photos.py) — `ETSY_ORDER`, `ETSY_SCENES`, `tidy_etsy()`, `bare()`, `etsy_number()`, `SCENES`, `scenes_to_etsy()`, `CATEGORIES`, `PHOTOS`, `REFS`, `PROMPTS`, `OMNI_PROMPTS`, `prompt()`, `place_video()`, `trim()`, `ffmpeg()`, `TRIM_SECONDS`, `templates()`, `signature()`, `template_file()`, `add_template()`, `remove_template()`, `open_folder()`, `references()`, `results()`, `count()`, `state()`, `items()`, `place()`, `remove()`, `set_canva_cover()`, `ETSY`, `CANVA_COVER`
- [app/studio/workshop/generate.py](../../app/studio/workshop/generate.py) — `Session.start_photo()` (no catch without a book; `video` — a video awaited), `Session._open()` (`catch=False` — nothing awaited), `look()` (pictures, or videos for a video category), `_catch()` (a photo or a video → `photos.place()`), `next_item()` (the wait ends after the last part when nothing is caught)
- [app/studio/workshop/books.py](../../app/studio/workshop/books.py) — the step `photos` in `STEPS`, `steps()`, `detail()` (`photos`), `ETSY` in `AREAS`
- [app/studio/workshop/routes.py](../../app/studio/workshop/routes.py) — `_gen_photo()`, `_photos()`, `_photos_sig()`, `_photo_media()`, `_photo_add()`, `_photo_remove()`, `_photo_open()`, `_photo_prompt()`, `_book_photo_remove()`, `_place()` (`photo:<category>`, `canva-cover`)
- [app/studio/mockups.py](../../app/studio/mockups.py) — `_keep_canva_cover()`, `_to_etsy()`
- [app/web/js/pages/photos.js](../../app/web/js/pages/photos.js) — `mount()`: `section()`, `addFiles()`, `remove()`, `zoom()`
- [app/web/js/pages/workshop-book.js](../../app/web/js/pages/workshop-book.js) — `photosBody()`, `templatesOf()`
- [app/web/js/workshop-live.js](../../app/web/js/workshop-live.js) — `startPhoto()`, `watch()` (`sigUrl`), `genBar()` (a wait without a book)
- [app/web/css/listings.css](../../app/web/css/listings.css) — `.ph-*`
- Tests: [app/tests/test_photos.py](../../app/tests/test_photos.py) (`TheTemplates`, `ThePrompts`, `InABook`, `TheOmniVideo`, `WithoutABook`, `TheMockupsKeepTheCanvaCover`)

## Related

- [Workshop](workshop.md) · [Mockups](mockups.md) · [Listing slides](slides.md) · [Two modes](modes.md) · [Decisions](../decisions.md)
