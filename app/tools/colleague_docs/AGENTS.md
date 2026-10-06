# Book Studio — rules for agents

> **Making a book** (a new book, its story, text, prompts)? These rules are not yours: open the folder
> `pipeline/` and read **`pipeline/AGENTS.md`** — the book pipeline's rules. Everything below is for agents
> working on Book Studio's code.

A local Windows program for the owner of an Etsy shop selling personalized children's books. One icon rail:
**Orders** — the order queue and each order's path to print (the Order Creator is its print step); **Books** — the
Workshop (new books in development), the library, the archive; **Profit**; **Tools** — the Order Creator, the print
archive, the Photoshop mockups, the photo mockups, the listing slides. The user is the shop's owner,
not necessarily a programmer; the program's interface is in Ukrainian. Design and check in the **light** theme first
([ui-principles](wiki/owner/ui-principles.md)).

## 0. This is a portable copy

You are in `Book Studio Portable\Book Studio\` — the repository of a **portable** Book Studio. Next to it lies `runtime\`
(Python, Photoshop, the mockup templates, Antigravity, Ollama, Upscayl, ffmpeg): the program finds them there
(`app/studio/portable.py`, [wiki/dev/portable.md](wiki/dev/portable.md)). Python for the commands below:
`..\runtime\python\python.exe`. This copy has **no git remote** (never push it anywhere); commit locally only when the
user asks. `app/data/` is the user's own data (orders, keys, books' state) and starts empty.

## 1. Wiki first, then code

1. Read [`wiki/index.md`](wiki/index.md).
2. Open the pages relevant to the task. If the user named something in his own words, look it up in
   [`wiki/glossary.md`](wiki/glossary.md). Files and functions — [`wiki/code-map.md`](wiki/code-map.md).
3. Only then go into the code — by the "Where in the code" sections (file + function name).
4. Before changing behavior, check [`wiki/decisions.md`](wiki/decisions.md): it may be a deliberate choice.
   (The wiki was written for the program's first owner: where it says "the owner", read "the person who owns this
   copy"; his personal rules — Etsy only from one computer, Printify read-only from a date — are settings, switched off
   in this copy: `security.etsyKyivOnly`, `printify.readOnlyFrom`.)

If the wiki contradicts the code — the code is the truth; fix the wiki within the same task.

## 2. Security — always

In full — [`wiki/security.md`](wiki/security.md). Briefly:
- Etsy — **read-only**. Gelato — **drafts only** (`orderType: draft`). Printify — only image uploads, an unpublished
  product, and "On hold" orders after manual-approval confirmation; never send to production, cancel, use Express,
  publish, or change/delete products; the Master is never changed. (If `printify.readOnlyFrom` holds a date, Printify
  is read-only from it.)
- **No live writes** to the user's accounts without his direct permission in chat. Checks are done with tests and
  fakes.
- **Keys and tokens**: never read, print, or copy into code/docs/URLs/logs; never open `app/data/vault.json`; never ask
  the user to paste keys into chat. A plain-text credentials file in the repo root, if one ever appears, is git-ignored:
  never read, print, commit, change or delete it unless the user directly asks for exactly that.
- Never permanently delete the user's data. The mockup templates (`runtime\Templates`) are read-only — never edit, save
  over or delete them; work on copies.
- **Commit and push only when the user asks.** `app/data/`, `app/bin/` and real customer data never go into git (tests
  use made-up data only).
- Preview the interface only on temporary data (`app/tools/dev_server.py`), never on the real program.

## 3. Working with the user

In full — [`wiki/owner/working-with-owner.md`](wiki/owner/working-with-owner.md), appearance
requirements — [`wiki/owner/ui-principles.md`](wiki/owner/ui-principles.md).
- Reply in the user's language (the interface is Ukrainian) in plain words; a report should say what changed, what was
  checked, what wasn't, and what he needs to do.
- "Just analyze, don't change anything" / "discussion mode" → no file changes. Start only on command.
- Record decisions and agreements in the wiki, not only in memory.
- After changes under `app/studio/`, remind him to restart Book Studio.

## 4. Repository

```
AGENTS.md, CLAUDE.md    rules for agents (this file and the Claude Code addendum)
README.md               short intro for people
app/                    the program: studio/ (Python server), web/ (interface), tests/, tools/
                        data/ and bin/ — local only, not in git
pipeline/               the book pipeline — the book agents' rules and playbook (Antigravity opens this folder);
                        its books/ (the Workshop's books, every picture) — local only, not in git
wiki/                   knowledge base (index.md — entry point, log.md — change log)
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
3. A new decision → `wiki/decisions.md`; a new word from the user → `wiki/glossary.md`; a new route →
   `wiki/architecture/api-routes.md`; a new file → `wiki/code-map.md` and the `code:` of the relevant page.
4. An entry in `wiki/log.md` (`## [YYYY-MM-DD] kind | what happened`, newest on top).
5. `python app/tools/wiki_check.py` — no errors.

Page format and wiki operations (adding a source, questions, review) —
[`wiki/dev/wiki-rules.md`](wiki/dev/wiki-rules.md).
