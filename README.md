# Book Studio

A local Windows program for a shop selling personalized children's books on Etsy: an order queue, a book
library, and Gelato print drafts (Printify is read-only since 1 October 2026) — and making new books and their Etsy listing pictures.

- **How to use it** — [app/README.md](app/README.md); the manual for an AI agent — [MANUAL.md](MANUAL.md)
- **Building a portable folder from this repository** — [wiki/dev/portable.md](wiki/dev/portable.md)
- **How it's all built** — the project wiki: [wiki/index.md](wiki/index.md)
- **Rules for Claude Code** — [CLAUDE.md](CLAUDE.md), with its rules, skills and hooks in `.claude/`

```
portable/  the launchers and the note for people (`setup_portable.py` puts them beside the repository)
app/       the program (launch: the "Book Studio" shortcut or app/Book Studio.pyw; one icon rail —
           orders, books: the Workshop and the library, profit, tools such as the mockups)
pipeline/  the book pipeline — knowledge/ and scripts/ (the procedures are the book* skills in .claude/skills/);
           its books/ — the Workshop's books, local only
wiki/      knowledge base
listing-prompts/  prompts for the Etsy listing photos (ChatGPT)
```

Tests: `cd app && python -m unittest discover -s tests` · wiki check: `python app/tools/wiki_check.py`
Data safety (history of every write, a daily snapshot, `python app/tools/data_history.py` to put a version back): [wiki/architecture/data-safety.md](wiki/architecture/data-safety.md)
