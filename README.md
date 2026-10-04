# Book Studio

A local Windows program for a shop selling personalized children's books on Etsy: an order queue, a book
library, and Gelato print drafts (Printify is read-only since 1 October 2026) — and making new books and their Etsy listing pictures.

- **How to use it** — [app/README.md](app/README.md); the manual for an AI agent — [MANUAL.md](MANUAL.md)
- **Building a portable folder from this repository** — [wiki/dev/portable-setup.md](wiki/dev/portable-setup.md); the plan — [ROADMAP.md](ROADMAP.md)
- **How it's all built** — the project wiki: [wiki/index.md](wiki/index.md)
- **Rules for agents** — [AGENTS.md](AGENTS.md) (Claude Code reads [CLAUDE.md](CLAUDE.md))

```
portable/  the launchers and the note for people (`setup_portable.py` puts them beside the repository)
app/       the program (launch: the "Book Studio" shortcut or app/Book Studio.pyw; one icon rail —
           orders, books: the Workshop and the library, profit, tools such as the mockups)
pipeline/  the book pipeline — the book agents' rules and playbook (Antigravity opens this folder);
           its books/ — the Workshop's books, local only
wiki/      knowledge base
```

Tests: `cd app && python -m unittest discover -s tests` · wiki check: `python app/tools/wiki_check.py`
