# Book Studio — rules for agents

> **Making a book** (a new book, its story, text, prompts)? These rules are not yours: open the folder
> `pipeline/` and read **`pipeline/AGENTS.md`** — the book pipeline's rules. Everything below is for agents
> working on Book Studio's code.

A local Windows program for the owner of an Etsy shop selling personalized children's books. One icon rail (since
2026-09-30; before, two modes switched by the brand icon): **Orders** — the order queue and each order's path to print
(the Order Creator is its print step); **Books** — the Workshop (new books in development), the library, the archive;
**Profit**; **Tools** — the Order Creator, the print archive, the Photoshop mockups, the photo mockups, the listing slides.
The owner is not a programmer, writes in Ukrainian, and **uses the light theme** —
design and check in light first ([ui-principles](wiki/owner/ui-principles.md)).

## 0. This is the portable copy

You are in `Book Studio Portable\Book Studio\` — the repository of the **portable** Book Studio. Next to it lies `runtime\`
(Python, Photoshop, the mockup templates, Antigravity, Ollama, Upscayl, ffmpeg): the program finds them there
(`app/studio/portable.py`, [wiki/dev/portable.md](wiki/dev/portable.md)). The plan by stages is [`ROADMAP.md`](ROADMAP.md) in
this repository — read it first and take one stage per session. The repository is self-sufficient: the launchers are in `portable/`,
and a portable folder is built from a clone by `app/tools/setup_portable.py` ([wiki/dev/portable-setup.md](wiki/dev/portable-setup.md)). The original install (`D:\Roman\Desktop\Book Studio`) is a separate project: do not
change it from here. Python for the commands below: `..\runtime\python\python.exe`. This copy has its **own private GitHub repository**
`raymanrboy/book-studio-portable` (remote `origin`, since 2026-10-04) — never the original's `raymanrboy/book-studio`; commit and push only when the owner asks.

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
- **Etsy: look, but never sign in** (2026-10-11). Opening etsy.com in the browser pane to search listings and shops and
  analyse them is fine — as a visitor, never signed in. Never sign in to the owner's Etsy account from this (Wrocław) PC;
  signing in is only on the Kyiv PC. No clicks that change anything (favourite, follow, buy, message); a CAPTCHA — stop and ask.
- Etsy — **read-only**. Gelato — **drafts only** (the old account after the move to the owner's own one — read
  only). Printify — **read-only from 1 October 2026**; before: only image uploads, an unpublished
  product, and "On hold" orders after manual-approval confirmation; never send to production, cancel,
  use Express, publish, or change/delete products; the Master is never changed.
- **No live writes** to the owner's accounts without his direct permission in chat. Checks are done with
  tests and fakes.
- **Keys and tokens**: never read, print, or copy into code/docs/URLs/logs; never open
  `app/data/vault.json`. The file `.secrets.txt` in the repo root (keys in plain text, ignored by git) —
  never read, print, commit, change or delete it without the owner's direct request for exactly that.
  Never ask the owner to paste keys into chat.
- **A script that writes into `app/data` or `pipeline/books`**: first copy what it will touch, never import `studio` without `BOOK_STUDIO_DATA` set before it, start
  the preview only with `tools/dev_server.py`; a wrong write is undone from the history (`python app/tools/data_history.py`) — [wiki/architecture/data-safety.md](wiki/architecture/data-safety.md).
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
- Record decisions and agreements in the wiki, not only in memory.
- After changes under `app/studio/`, remind him to restart Book Studio.

## 4. Repository

```
AGENTS.md, CLAUDE.md    rules for agents (this file and the Claude Code addendum)
MANUAL.md              the program's manual written for an AI (what is where, how to use, what to do when it breaks)
ROADMAP.md             the plan of the portable version by stages, and what is not yet checked
portable/              the launchers (.bat) and the note for people — laid out beside the repository by app/tools/setup_portable.py
README.md               short intro for people
app/                    the program: studio/ (Python server), web/ (interface), tests/, tools/
                        data/ and bin/ — local only, not in git
seo/                    the Etsy SEO studio (`/etsy-seo`): seo.py, knowledge/; data/ — local only, not in git
pipeline/               the book pipeline — the book agents' rules and playbook (Antigravity opens this folder);
                        its books/ (the Workshop's books, every picture) — local only, not in git
wiki/                   knowledge base (index.md — entry point, log.md — change log, raw/ — owner's sources)
examples/               the owner's examples for the listing slides (his Canva slides, sample mockups) — local only
.claude/                interface preview and Claude Code skills
```

## 5. Commands

```
python app/tools/wiki_check.py                          # does the wiki match the code?
python app/tools/wiki_check.py --changed                # which wiki pages to update after changes
cd app && python -m unittest discover -s tests          # tests (including the wiki check)
python app/tools/dev_server.py --sample                 # interface on made-up data (every page, a pretend Photoshop), port 47890
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
