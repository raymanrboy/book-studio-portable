---
title: Book Studio wiki — index
type: index
updated: 2026-10-08
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
- [Order Creator](features/order-creator.md) — a Gelato draft (Printify's book + On-hold order until 30 September).
- [Settings](features/settings.md) — keys, Etsy, Gelato (two accounts during the move), the Printify Master, data.
- [Send journal](features/send-journal.md) — exactly what went to Printify and Gelato on every attempt.
- [Order archive](features/archive.md) — files of books that went to print (14 days after "Sent"), and
  reprints.
- [Profit](features/profit.md) — counts only sales from 1 October 2026.
- [Backup](features/backup.md) — every 3 days the whole program and the mockup templates go to Google Drive as
  one 7-Zip archive under the owner's password.
- [The rail](features/modes.md) — places (Orders, Books, Profit), tools and search; the ink follows the area
  (orange / cyan).
- [Workshop](features/workshop.md) — «Книги»: books in development, written by the book pipeline's
  agents (`pipeline/`); the path strip, a prompt · a 2:1 spread · a text per row, the generation mode that catches
  the pictures from Downloads, the cover on the printer's template; passed to the library with their Etsy listing.
- [Cover](features/cover.md) — the cover's own tool: two squares → Gelato's cover made by Book Studio, no outpaint; or 2:1
- [Photo mockups](features/photo-mockups.md) — lifestyle photos with a blank book → our book in
  them (a Workshop book's step «Фото» and the «Фотомокапи» page): template, cover, JSON prompt into the clipboard.
- [Mockups](features/mockups.md) — a Canva demo book → Etsy listing pictures from the Photoshop templates (the owner
  fits the front cover by hand); the templates' structure.
- [Listing slides](features/slides.md) — the Mockups' last step: the pictures without background, the six Etsy
  slides made by themselves, a Canva-like editor loaded only when opened; the skill `/listing-slides`.
- [Etsy SEO studio](features/seo.md) — a book's long title, 13 tags and description from its files, the keyword database and
  eRank read in the browser pane; the skill `/etsy-seo` (`seo/`).
- [Canva extension](features/canva-extension.md) — a Chrome extension (`canva-extension/`): a Workshop book's folder → its Canva
  template — the pictures into the frames, the sphere and the text (Schoolbell 100) on the text pages; a second run skips what is done.

## Domain rules

- [Printer rule](rules/printer-rule.md) — from 1 October 2026 every book → Gelato (28 or 30); Printify only
  read for its earlier orders.
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
- [Server routes](architecture/api-routes.md) — every one, with who calls them.
- [Interface](architecture/frontend.md) — the shell, a page's contract, helpers, the visual system.
- [Data](architecture/data.md) — what's in `app/data`.

## Services

- [Etsy](integrations/etsy.md) — read-only; sign-in only from the Kyiv PC.
- [Printify](integrations/printify.md) — read-only from 1 October 2026; before: allowed actions, On-hold orders,
  the Master.
- [Gelato](integrations/gelato.md) — drafts, PDF, the Cloudflare temporary link; the move to the owner's own
  account (two keys, the old one read-only).
- [Canva](integrations/canva.md) — book templates and the owner's manual work.

## Owner

- [Working with the owner](owner/working-with-owner.md)
- [The interface the owner wants](owner/ui-principles.md)
- [Book ideas](owner/book-ideas.md) — the owner's shelf: links to books he finds and the key ideas he likes in them.
- [Listing ideas backlog](owner/listing-ideas.md) — the stock of listing ideas for two posts a day, the owner's shop compared with two others.
- [Five Christmas books and the two styles](owner/christmas-books.md) — the owner's Christmas focus: five books, and the looks of TheChildhoodKeeper and LunaBooksUS as pipeline style presets (`CG`, `FG`).

## Development

- [Setup, launch, GitHub](dev/setup.md)
- [Tests](dev/testing.md)
- [Interface preview](dev/preview.md) — a server on temporary data.
- [Data safety](architecture/data-safety.md) — history of every write, the daily snapshot, guards, the Recycle Bin, putting a version back.
- [Building a portable folder from the repository](dev/portable-setup.md) — the clone, `setup_portable.py`, what goes into `runtime/`.
- [Optional modules](features/modules.md) — the text check and upscaling, installed from the interface when asked.
- [Moving the settings and keys](features/settings-transfer.md) — one file for another PC or the other Book Studio.
- [MANUAL.md](../MANUAL.md) — the user manual written for an LLM: how to use the program, step by step, and what to do when it breaks.
- [The portable copy](dev/portable.md) — `runtime/` and how the program finds its programs there.
- [How to run this wiki](dev/wiki-rules.md) — page format, checks, operations.
- [Design and code skills](dev/design-skills.md) — the agent skills installed for interface logic, icons, visual craft and code.

## Decisions and recipes

- [Decisions](decisions.md) — what was decided and why (with dates).
- [Recipes](recipes.md) — where to change code for common tasks.
- [Known limits](dev/limits.md) — what the program deliberately doesn't do, what was only tried against fakes.

## Housekeeping

- [Wiki change log](log.md)
- [Owner's sources](raw/README.md)
