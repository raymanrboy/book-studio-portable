---
title: How to run this wiki
type: dev
updated: 2026-10-05
code:
  - app/tools/wiki_check.py
  - app/tests/test_wiki.py
---
# How to run this wiki

> The wiki is written and maintained by an agent; the owner reads it and gives sources and direction.
> The goal: a new agent should land in the right place in the code within a few minutes and know *why*
> things are the way they are, not just how.
> The idea — an "LLM wiki" (a lasting knowledge base an agent grows, instead of re-reading the sources
> every time).

## Three layers

1. **Sources** — the code (`app/`) as the truth about *how* the program works right now, and the
   owner's material in `wiki/raw/` (read-only, never changed).
2. **The wiki** — the pages in `wiki/`. Only an agent writes to it.
3. **The scheme** — `AGENTS.md` (+ `CLAUDE.md`) at the root: the working rules, and this page.

## Layout

| Folder / file | What's there | `type` |
|---|---|---|
| `index.md` | the catalog of every page | `index` |
| `log.md` | the wiki's change log (append-only) | — |
| `overview.md`, `glossary.md`, `code-map.md` | entry pages | `overview`, `reference` |
| `security.md` | prohibitions | `rule` |
| `architecture/` | structure: launch, server, interface, routes, data | `architecture`, `reference` |
| `features/` | parts of the program | `feature` |
| `integrations/` | external services | `integration` |
| `rules/` | domain rules | `rule` |
| `flows/` | step-by-step paths | `flow` |
| `owner/` | how the owner wants to work and see the interface | `owner` |
| `decisions.md`, `recipes.md` | decisions with reasons; "how to change X" | `decision`, `recipe` |
| `dev/` | setup, tests, preview, this page | `dev` |
| `raw/` | the owner's sources, as-is | — |

## A page

```markdown
---
title: Name, in English
type: feature
updated: 2026-09-17
code:
  - app/studio/orders.py
---
# Name

> The gist, in 1–3 sentences.

## …content sections…

## Where in the code
- [app/studio/orders.py](../../app/studio/orders.py) — `plan_for()`, `arrange_pages()`, `PRINTIFY_PAGES`

## Related
- [Another page](../rules/printer-rule.md)
```

- One page — one topic; short, without retelling the code.
- **A page says how things are now.** No "until 26.09 it was …, then …": the history of a change lives in
  [log.md](../log.md), the owner's reasons in [decisions.md](../decisions.md). A page keeps only the *why* of the
  present design in a few words ("the owner: …", with the date), when without it someone would "fix" it.
- **One fact — one page.** A thing is described in full where it belongs (the photo mockups' `etsy/` folder — on
  [photo-mockups](../features/photo-mockups.md)); every other page says it in a few words and links there. A change
  then touches one page, not seven.
- **No counts in prose** (how many tests, routes, pages): the runner and `wiki_check.py` say them; a number kept by
  hand was only ever rewritten.
- File names — Latin script, hyphenated; headings — in English.
- Links — plain relative Markdown links; a path with spaces goes in angle brackets:
  `[x](<../app/Book Studio.pyw>)`.
- **Code — a link to the file + function names** (`name()`) and constants (`NAME`) *after* the link, on
  the same line. Don't write line numbers.
- `code:` in the header — the files a page **describes** (for the "file → pages" map); a folder ending
  in `/` covers every file inside it.
- `updated:` — the date of the page's last substantive change.
- Write decisions down with a date and a reason in [decisions.md](../decisions.md): that way no one
  "fixes" a deliberate choice the owner made.
- No keys, tokens, passwords, or real customer data, ever.

## Checking — `app/tools/wiki_check.py`

```
python app/tools/wiki_check.py            # everything fine → exit code 0 (~2 s: the names are looked up in a set of the code's words, and `data` is never walked — it took 54 s)
python app/tools/wiki_check.py --changed  # which pages describe files changed in git
python app/tools/wiki_check.py --map      # code file → pages
```
It checks: headers, that links resolve, that every mentioned `function()` and `CONSTANT` exists in the
file, that every page is in `index.md`, that every code file (`.py`, `.pyw`, `.js`, `.jsx`, `.css`, `.html`, `.bat`) is described by at least one page, that the
[routes](../architecture/api-routes.md) table matches the code, the format of `log.md`. It doesn't check that
the prose is true — that is what the review (lint) is for.
A name after a file's link must be **defined** in that file (`defined_in()`: `def`, `function`,
`class`, `const`, an object's key or method, a name in quotes such as an environment variable): an import or a call
used to be enough, so a function moved to another file kept passing on its old file's line (the cleanup's splits
left eight such lines). `Class.method()` is looked for in the class's file; any other dotted `module.func()` is a
call the file makes, and it only has to be there.
The same check runs as the test `test_wiki.py`, so a wiki that's out of sync with the code fails the
tests.

## Operations

- **After every task that touches code** (mandatory):
  1. `wiki_check.py --changed` → update the listed pages (content, "Where in the code", `updated`);
  2. a new decision → [decisions.md](../decisions.md); a new word from the owner →
     [glossary.md](../glossary.md); a new route → [api-routes.md](../architecture/api-routes.md); a new
     file → [code-map.md](../code-map.md) and the `code:` of the right page;
  3. an entry in `log.md`;
  4. `wiki_check.py` and the tests — no errors.
- **Adding a source** (the owner gave text, a screenshot, a document): put it in `raw/` (if it's a
  file), read it, discuss the main points with the owner, spread it across pages (often 5–15 pages),
  update `index.md`, an `ingest` entry in `log.md`.
- **A question**: start with `index.md` → pages → code. Save a valuable answer (a comparison, an
  analysis) as a new page.
- **Review (lint)**, on request or from time to time: contradictions between pages, stale claims, pages
  with no inbound links, concepts with no page of their own, gaps; a `lint` entry in `log.md`.

## Log

An entry's heading: `## [YYYY-MM-DD] kind | what happened`, kind is `setup`, `ingest`, `update`,
`query`, `lint`, `decision`. Newest entries on top. The latest entries:
`grep "^## \[" wiki/log.md | head -5`.

## Where in the code

- [app/tools/wiki_check.py](../../app/tools/wiki_check.py) — `check()`, `coverage()`, `front_matter()`, `routes_in_code()`, `routes_in_wiki()`, `changed_files()`, `TYPES`
- [app/tests/test_wiki.py](../../app/tests/test_wiki.py) — `WikiMatchesCode`

## Related

- [Contents](../index.md) · [Log](../log.md) · [Owner's sources](../raw/README.md)
