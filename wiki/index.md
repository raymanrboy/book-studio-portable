---
title: Book Studio wiki — index
type: index
updated: 2026-09-23
code: []
---
# Book Studio wiki

> The project's knowledge base. **Agents:** start here → open the pages you need → only then the code
> (by the "Where in the code" sections). The wiki is updated after every code change —
> [rules](dev/wiki-rules.md).
> Owner: the pages can be read here or in Obsidian (the `wiki` folder).

## Start here

- [Overview](overview.md) — what this program is, the business, what it's made of.
- [Glossary](glossary.md) — the owner's words → places in the code. **The first place to look when the
  owner names something.**
- [Code map](code-map.md) — every file and its main functions.
- [Security](security.md) — what's forbidden for the program and for agents. **Mandatory.**
- [Working with the owner](owner/working-with-owner.md) — language, "analyze" / "do it" modes, reports.

## Parts of the program

- [Orders](features/orders.md) — the queue and the order card (the start screen).
- [Book library](features/library.md) — the gallery, a new book, a book's passport, the `book.json` model.
- [Text check](features/text-check.md) — a local Gemma model reads the pages, the program checks them
  against the book passport.
- [Order Creator](features/order-creator.md) — a book/On-hold order in Printify, a Gelato draft.
- [Settings](features/settings.md) — keys, Etsy, the Printify Master, data.
- [Send journal](features/send-journal.md) — exactly what went to Printify and Gelato on every attempt.
- [Order archive](features/archive.md) — files of books that went to print (14 days after "Sent"), and
  reprints.
- [Profit](features/profit.md) — hidden until 1 October.
- [Mockups](features/mockups.md) — a separate utility: a Canva demo book → Etsy listing pictures from the
  Photoshop templates (the owner fits the front cover by hand).

## Domain rules

- [Printer rule](rules/printer-rule.md) — Hardcover in the US → Printify (24), everything else → Gelato
  (28 or 30).
- [Book structure](rules/book-structure.md) — 30 pages, spreads, library slots, the print folder.
- [File naming](rules/file-naming.md) — laying out a Canva export, importing into the library.
- [Order stages](rules/order-stages.md) — new / in progress / sent.
- [When orders are refreshed](rules/sync-policy.md) — only on launch and by button.
- [Matching and profit](rules/reconciliation.md) — finding the print order, Etsy fees, states.

## Paths (step by step)

- [From Etsy to print](flows/order-to-print.md) — the owner's main workflow.
- [Filling the library](flows/book-import.md) — a new book, the agent's guide, import.
- [Dragging folders and ZIPs](flows/dropped-files.md) — how files get into the program.

## Program structure

- [Launch and shutdown](architecture/runtime.md)
- [Server](architecture/server.md) — routes, background jobs, errors, settings.
- [Server routes](architecture/api-routes.md) — all 105, with who calls them (15 of them — the mockups utility's own).
- [Interface](architecture/frontend.md) — the shell, a page's contract, helpers, the visual system.
- [Data](architecture/data.md) — what's in `app/data`.

## Services

- [Etsy](integrations/etsy.md) — read-only; sign-in only from the Kyiv PC.
- [Printify](integrations/printify.md) — allowed actions, On-hold orders, the Master.
- [Gelato](integrations/gelato.md) — drafts, PDF, the Cloudflare temporary link.
- [Canva](integrations/canva.md) — book templates and the owner's manual work.

## Owner

- [Working with the owner](owner/working-with-owner.md)
- [The interface the owner wants](owner/ui-principles.md)

## Development

- [Setup, launch, GitHub](dev/setup.md)
- [Tests](dev/testing.md)
- [Interface preview](dev/preview.md) — a server on temporary data.
- [How to run this wiki](dev/wiki-rules.md) — page format, checks, operations.

## Decisions, recipes, plans

- [Decisions](decisions.md) — what was decided and why (with dates).
- [Recipes](recipes.md) — where to change code for common tasks.
- [Plans](plans/roadmap.md) — agreed ideas for later.
- [Listing mockups](plans/listing-mockups.md) — the agreements and the templates' structure behind the
  [Mockups](features/mockups.md) utility.
- [Open questions and technical debt](plans/open-questions.md)

## Housekeeping

- [Wiki change log](log.md)
- [Owner's sources](raw/README.md)
