# Book Studio — rules for agents

A local Windows program for the owner of an Etsy shop selling personalized children's books. Two modes
(the brand icon switches): **Orders** — the order queue, the book library, creating books/drafts in Printify
and Gelato; **Listings** — the Workshop (new books in development) and the Photoshop mockups for listings. The owner is not a programmer and
writes in Ukrainian.

## 1. Wiki first, then code

1. Read [`wiki/index.md`](wiki/index.md).
2. Open the pages relevant to the task. If the owner named something in his own words, look it up in
   [`wiki/glossary.md`](wiki/glossary.md). Files and functions — [`wiki/code-map.md`](wiki/code-map.md).
3. Only then go into the code — by the "Where in the code" sections (file + function name).
4. Before changing behavior, check [`wiki/decisions.md`](wiki/decisions.md): it may be a deliberate
   choice the owner made.

If the wiki contradicts the code — the code is the truth; fix the wiki within the same task.

## 2. Security — always

In full — [`wiki/security.md`](wiki/security.md). Briefly:
- **Never open Etsy from this (Wrocław) PC**, in any browser; sign in to Etsy only on the Kyiv PC.
- Etsy — **read-only**. Gelato — **drafts only**. Printify — only image uploads, an unpublished
  product, and "On hold" orders after manual-approval confirmation; never send to production, cancel,
  use Express, publish, or change/delete products; the Master is never changed.
- **No live writes** to the owner's accounts without his direct permission in chat. Checks are done with
  tests and fakes.
- **Keys and tokens**: never read, print, or copy into code/docs/URLs/logs; never open
  `app/data/vault.json`. The file `.secrets.txt` in the repo root (keys in plain text, ignored by git) —
  never read, print, commit, change or delete it without the owner's direct request for exactly that.
  Never ask the owner to paste keys into chat.
- Never permanently delete the owner's data. The mockup templates `D:\Roman\Desktop\Трафарети мастхев`
  are read-only — never edit, save over or delete them; work on copies.
- **Commit and push only when the owner asks.** `app/data/`, `app/bin/` and real customer data never go
  into git (tests use made-up data only).
- Preview the interface only on temporary data (`app/tools/dev_server.py`), never on the real program.

## 3. Working with the owner

In full — [`wiki/owner/working-with-owner.md`](wiki/owner/working-with-owner.md), appearance
requirements — [`wiki/owner/ui-principles.md`](wiki/owner/ui-principles.md).
- Reply in Ukrainian, in plain words; a report should say what changed, what was checked, what wasn't,
  and what he needs to do.
- "Just analyze, don't change anything" / "discussion mode" → no file changes. Start only on command
  ("go ahead", "do it").
- Record plans and agreements in the wiki, not only in memory.
- After changes under `app/studio/`, remind him to restart Book Studio.

## 4. Repository

```
AGENTS.md, CLAUDE.md    rules for agents (this file and the Claude Code addendum)
README.md               short intro for people
app/                    the program: studio/ (Python server), web/ (interface), tests/, tools/
                        data/ and bin/ — local only, not in git
wiki/                   knowledge base (index.md — entry point, log.md — change log, raw/ — owner's sources)
.claude/                interface preview and Claude Code skills
```

## 5. Commands

```
python app/tools/wiki_check.py                          # does the wiki match the code?
python app/tools/wiki_check.py --changed                # which wiki pages to update after changes
cd app && python -m unittest discover -s tests          # tests (including the wiki check)
python app/tools/dev_server.py --sample                 # interface on made-up data (both modes, a pretend Photoshop), port 47890
python app/tools/make_shortcut.py                       # the desktop shortcut
```

## 6. Every task that touches code ends like this (mandatory)

1. Tests pass.
2. `python app/tools/wiki_check.py --changed` → the listed wiki pages are updated (content, "Where in
   the code", `updated:`).
3. A new decision → `wiki/decisions.md`; a new word from the owner → `wiki/glossary.md`; a new route →
   `wiki/architecture/api-routes.md`; a new file → `wiki/code-map.md` and the `code:` of the relevant page.
4. An entry in `wiki/log.md` (`## [YYYY-MM-DD] kind | what happened`, newest on top).
5. `python app/tools/wiki_check.py` — no errors.

Page format and wiki operations (adding a source, questions, review) —
[`wiki/dev/wiki-rules.md`](wiki/dev/wiki-rules.md).
