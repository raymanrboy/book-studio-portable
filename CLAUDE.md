# Book Studio

A local Windows program for the owner's Etsy shop of personalized children's books: **Orders** (the queue and each
order's path to print), **Books** (the Workshop for new books, the library, the archive), **Profit**, **Tools** (the
Order Creator, mockups, photo mockups, listing slides, the cover tool). A Python server (`app/studio/`) and a plain-JS
interface (`app/web/`); the knowledge base is `wiki/`; making the books themselves is `pipeline/`; Etsy SEO is `seo/`.

This is the **portable copy**: it sits next to `..\runtime\` (Python, Photoshop, templates, Upscayl, ffmpeg…), its own
private repository is `raymanrboy/book-studio-portable` (remote `origin`). The original install
`D:\Roman\Desktop\Book Studio` and its repository `raymanrboy/book-studio` are a separate project — never touched from here.

## The owner

- He writes in Ukrainian, often quickly. Reply in Ukrainian, in plain words — no jargon, no function names; that
  includes the wrap-up box, questions and buttons. A report says what changed for him, what was checked, what wasn't,
  and what he has to do (after changes under `app/studio/`: restart Book Studio).
- «Просто проаналізуй» / discussion → no file changes. He likes to talk a big idea through point by point first;
  «роби», «приступай», «доклади зусиль» (= check thoroughly before reporting) start the work.
- Plans, agreements and decisions go into the wiki (`wiki/decisions.md`), not only into memory.
- He uses the light theme; the program has only that one.
- Who he is, his computers, his folders: [wiki/owner/working-with-owner.md](wiki/owner/working-with-owner.md).

## Never

In full, with the reasons: [wiki/security.md](wiki/security.md). The short form:

- **Etsy**: browse as a visitor, never sign in from this (Wrocław) PC; nothing that changes anything; a CAPTCHA → stop
  and ask. **Printify** read-only. **Gelato** drafts only. **No live writes** to his accounts without his direct
  permission in chat — checks use tests and fakes.
- **Keys**: never read, print, copy, change or delete them; `.secrets.txt` and `app/data/vault.json` are blocked by the settings and a
  hook. Never ask him to paste a key.
- Never permanently delete his data. The mockup templates `D:\Roman\Desktop\Трафарети мастхев` are read-only.
- Commit and push only when he asks — then everything together. `app/data/`, `app/bin/` and real customer data never
  go into git.
- Preview the interface only on made-up data (`preview_start("book-studio-dev")`), never on the real program.
- A script that writes into `app/data` or `pipeline/books` first copies what it touches:
  [wiki/architecture/data-safety.md](wiki/architecture/data-safety.md).

## Where to start

| The task | Start with |
|---|---|
| Code of the program | [wiki/index.md](wiki/index.md) → the page → the code (rules for `app/` load by themselves) |
| A book: new, next step, text, prompts | the `book` skill (`/book 52`, `/book new`) |
| A book's cover / hero variants | `book-cover` / `book-variant` |
| Etsy SEO of a book · listing slides | `etsy-seo` · `listing-slides` |
| The wiki: after code changes · new material · health check | `wiki-update` · `wiki-ingest` · `wiki-lint` |
| A word the owner uses | [wiki/glossary.md](wiki/glossary.md) |
| Prompts for the Etsy listing photos (ChatGPT) | [listing-prompts/](listing-prompts/README.md) |

The program's manual for people and for an assistant answering "how do I…": [MANUAL.md](MANUAL.md).

## Commands

Python is `..\runtime\python\python.exe` (from this folder). In Bash prefer absolute paths; Cyrillic output needs
`PYTHONIOENCODING=utf-8`, tests `PYTHONDONTWRITEBYTECODE=1`.

```
cd app && python -m unittest discover -s tests          # the tests (they include the wiki check)
python app/tools/wiki_check.py [--changed]              # does the wiki match the code? which pages to update?
python pipeline/check_book.py "pipeline/books/<book>"   # a book's mechanical check
```

- Interface preview: `preview_start("book-studio-dev")` — made-up data, port 47890: [wiki/dev/preview.md](wiki/dev/preview.md).
- GitHub CLI is not on PATH: `C:\Users\Roman\AppData\Local\Programs\GitHubCLI\bin\gh.exe`; the push command is in
  [wiki/dev/setup.md](wiki/dev/setup.md).

## How this setup works

Open **this folder** (`Book Studio`) as the session's project: the permissions and hooks in `.claude/settings.json` apply
only to the folder a session starts in (the parent `Book Studio Portable` has a copy of them as a safety net).
`.claude/rules/` hold the rules for `app/`, `app/web/`, `wiki/` and `pipeline/` — each loads when its files are touched;
`.claude/skills/` the procedures; `.claude/agents/` the subagents; `.claude/hooks/book_guard.py` the book and key guards.
Personal notes go to Claude's memory; everything about the project lives in the wiki.
