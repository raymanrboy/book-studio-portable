---
paths:
  - "pipeline/**"
---

# The book pipeline

- Making or continuing a book is the `book` skill; its cover `book-cover`, hero variants `book-variant`. Follow the
  skill — the steps, the stops for the owner and the formats are there.
- In a book folder `pipeline/books/<number>.<slug>/` write only into `agent/` — flat, except `variants/<G#_name>/`. `pictures/`, `originals/`, `etsy/`,
  `mockups/` and `book.json` are the Workshop's (a hook refuses writes there). Never touch another book's folder.
- The file names in `agent/` and the headings of `book-text.md` are read by the Workshop — keep them exactly.
- `pipeline/knowledge/` is the one source of the rules and reference data (presets, formulas, text rules, the master
  prompt); `pipeline/scripts/` the helpers; `pipeline/check_book.py` the mechanical check (a hook runs it after each
  write of a book file and shows its FAILs). Never edit the check (`check_book.py`, `app/studio/workshop/check.py`) to
  make a book pass — fix the book.
- The Workshop's code is in `app/studio/workshop/` — that is program work, with the rules for `app/`.
