---
paths:
  - "app/**"
---

# Working on the program's code

## Wiki first, then code

1. [wiki/index.md](../../wiki/index.md) → the pages of the task (a word the owner uses: `wiki/glossary.md`; a file or
   function: `wiki/code-map.md`).
2. Then the code, by the pages' "Where in the code" (file + function names).
3. Before changing behavior, check `wiki/decisions.md` — it may be a deliberate choice of the owner's. If the wiki and
   the code disagree, the code is the truth: fix the wiki in the same task.

## Data safety

A script that writes into `app/data` or `pipeline/books`: copy what it touches first, never import `studio` without
`BOOK_STUDIO_DATA` set before it, start the preview only with `app/tools/dev_server.py`; a wrong write is undone from the
history (`python app/tools/data_history.py`) — `wiki/architecture/data-safety.md`. Tests use made-up data only.

## Done means

1. The tests pass (`cd app && python -m unittest discover -s tests`).
2. The wiki matches — the `wiki-update` skill does the rest: `wiki_check.py --changed` → the listed pages (content,
   "Where in the code", `updated:`); a new decision → `wiki/decisions.md`; a new owner's word → `wiki/glossary.md`; a new
   route → `wiki/architecture/api-routes.md`; a new file → `wiki/code-map.md` and the `code:` of its page; an entry in
   `wiki/log.md`; `wiki_check.py` with no errors.
3. A change the owner can see → checked in the preview (`preview_start("book-studio-dev")`), with proof.
4. The report reminds him to restart Book Studio after changes under `app/studio/`.
