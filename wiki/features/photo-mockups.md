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
> photos with a **blank white book** (templates); the generator (Gemini) swaps that book for ours. Book Studio lays
> the template, the book's cover and a JSON prompt into the clipboard one by one, and catches the finished photo into
> the book's `etsy/` folder. Built 2026-09-30 from the owner's request — see [decisions](../decisions.md).

## Two places

- **A Workshop book's step «Фото»** (between «Мокапи» and «Бібліотека», `n/7`): the book's references on top
  (Cover 1 · Cover & Open 1 · the Canva cover — ✓ there / what to do), **seven cards** — one per category (its photo, or
  an empty frame with a camera), and under them **the chosen category's templates**. A click on a template: the
  clipboard holds **the template → the book's reference → the prompt**, one by one (Ctrl+V in Chrome puts in the next,
  as the Workshop's other several-part pastes — `PasteWatch`); the generation bar says what's next. The photo the owner
  downloads is caught from Downloads into `etsy/photo-<category>.<ext>` (the one before → `.replaced/`). A finished card:
  view, «Зберегти як…», remove (to `.replaced/`); a photo dropped onto a card is taken as it is; the template used last is
  marked ✓ (`book.json` → `photos`). **Categories may be skipped** (the owner): the step is done with all seven photos,
  or ticked by hand («Позначити зробленим»).
- **The «Фотомокапи» page** (`#/photos`, the Listings mode's third rail item, a camera): no book — a click on a
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
| `size` | Розмір | Cover 1 — on both books: two hands hold the small softcover and the large hardcover side by side (the owner's `Трафарети мастхев\Size.jpg`, copied; "a very important mockup") |

«Для відео» joined the same evening (the owner: "there are only three photos, without the women" — he took the others out).

**The Canva cover** is kept by the Mockups: a run for a Workshop book copies the demo book's cover (as Canva exported
it) into the book's `mockups/canva-cover.*` (`mockups._keep_canva_cover()`); for a book whose mockups were made before,
it can be dropped onto its frame in the step.

## The prompts

One **JSON object per category** (`photos.PROMPTS`, pretty-printed by `rows.as_prompt()` — the Workshop's own format),
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
pipeline/books/<book>/etsy/photo-<category>.png              the photos, beside the listing slides (Listing N.png) and
                                                             copies of Cover & Open 1 and All & Open 1
```

The owner's originals on the desktop (`Заготовки обкладинок`) were copied once with English names (2026-09-30) and are
not used by the program. Every name inside Book Studio is English; the page speaks Ukrainian.

## In the preview and the tests

`tools/sample_books.py`: `make_photo_templates()` — made-up scenes with a white book per category (the preview's
`photo-mockups/`), and book 40 has made-up references in its `mockups/` (book 41 has none — the missing states).
Tests — `app/tests/test_photos.py`.

## Where in the code

- [app/studio/photos.py](../../app/studio/photos.py) — `SCENES`, `scenes_to_etsy()`, `CATEGORIES`, `REFS`, `PROMPTS`, `prompt()`, `templates()`, `signature()`, `template_file()`, `add_template()`, `remove_template()`, `open_folder()`, `references()`, `results()`, `count()`, `state()`, `items()`, `place()`, `remove()`, `set_canva_cover()`, `ETSY`, `CANVA_COVER`
- [app/studio/workshop/generate.py](../../app/studio/workshop/generate.py) — `Session.start_photo()`, `Session._open()` (`catch=False` — nothing awaited), `_catch()` (a photo → `photos.place()`), `next_item()` (the wait ends after the last part when nothing is caught)
- [app/studio/workshop/books.py](../../app/studio/workshop/books.py) — the step `photos` in `STEPS`, `steps()`, `detail()` (`photos`), `ETSY` in `AREAS`
- [app/studio/workshop/routes.py](../../app/studio/workshop/routes.py) — `_gen_photo()`, `_photos()`, `_photos_sig()`, `_photo_media()`, `_photo_add()`, `_photo_remove()`, `_photo_open()`, `_photo_prompt()`, `_book_photo_remove()`, `_place()` (`photo:<category>`, `canva-cover`)
- [app/studio/mockups.py](../../app/studio/mockups.py) — `_keep_canva_cover()`, `_to_etsy()`
- [app/web/js/pages/photos.js](../../app/web/js/pages/photos.js) — `mount()`: `section()`, `addFiles()`, `remove()`, `zoom()`
- [app/web/js/pages/workshop-book.js](../../app/web/js/pages/workshop-book.js) — `photosBody()`, `templatesOf()`
- [app/web/js/workshop-live.js](../../app/web/js/workshop-live.js) — `startPhoto()`, `watch()` (`sigUrl`), `genBar()` (a wait without a book)
- [app/web/css/listings.css](../../app/web/css/listings.css) — `.ph-*`
- Tests: [app/tests/test_photos.py](../../app/tests/test_photos.py) (`TheTemplates`, `ThePrompts`, `InABook`, `WithoutABook`, `TheMockupsKeepTheCanvaCover`)

## Related

- [Workshop](workshop.md) · [Mockups](mockups.md) · [Listing slides](slides.md) · [Two modes](modes.md) · [Decisions](../decisions.md)
