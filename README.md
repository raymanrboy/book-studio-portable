# Book Studio

A local Windows program for a shop selling personalized children's books on Etsy: an order queue, a book
library, and creating books/drafts in Printify and Gelato.

- **How to use it** — [app/README.md](app/README.md)
- **How it's all built** — the project wiki: [wiki/index.md](wiki/index.md)
- **Rules for agents** — [AGENTS.md](AGENTS.md) (Claude Code reads [CLAUDE.md](CLAUDE.md))

```
app/    the program (launch: the "Book Studio" shortcut or app/Book Studio.pyw;
        the listing-mockups utility: the "Мокапи" shortcut or app/Mockups.pyw)
wiki/   knowledge base
```

Tests: `cd app && python -m unittest discover -s tests` · wiki check: `python app/tools/wiki_check.py`
