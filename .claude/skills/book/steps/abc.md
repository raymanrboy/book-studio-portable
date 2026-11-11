# Formula F — the ABC square book

A different route: 28 square 1:1 pictures — two dedication squares and A–Z — no panoramas, no slicing, no cover unless
the owner asks for an outer image separately. The formula: [F-abc-alphabet.md](../../../../pipeline/knowledge/formulas/F-abc-alphabet.md).

- Tier S by default (no step 1, no `canonical.png`); Tier H only if he wants the same child on every letter.
- `formula.md` and the blueprint header say `Formula: F` — the book check recognises an ABC book by it.
- Steps 2–4 as usual, the text by the formula's pattern (a short couplet per letter, `{Name}` on most of them).
  `book-text.md` headings for an ABC book: `## Cover — Title`, `## Dedication 01`, `## Letter A` … `## Letter Z`, and
  `## Afterword` (or `## Dedication 02`) — the book check reads these.
- Step 5 writes **`agent/abc-prompts-json.md`** instead of the spread and end-page files: exactly 28 square prompts in
  order — Dedication 01, Dedication 02, A … Z.
- ABC is the one exception to "no letters in the picture": each A–Z prompt draws exactly one large readable uppercase
  letter as part of the art, the animal or object interacting with it. No other letters, words, names or numbers —
  Canva adds `{Name}`, the stanza and the dedication.
- The Workshop's rows are made for 30 pages; it shows an ABC book's prompts as a note only.
