---
title: Book Studio overview
type: overview
updated: 2026-09-23
code:
  - app/studio/main.py
  - app/studio/core.py
---
# Book Studio overview

> A local Windows program for the owner of an Etsy shop selling personalized children's books. It
> carries every order from Etsy through to printing in Printify or Gelato, and keeps a reference library
> of books.

## The business in two paragraphs

The owner sells personalized books on Etsy: the text carries the child's name, the first page has a
dedication, and the end has a "from whom". The buyer fills in the personalization fields on Etsy. The
owner makes a copy of the book template in Canva, drops in the name with find-and-replace on `{Name}`,
downloads the PNG pages, and sends the book to print: **Printify** (hardcovers in the US, 24 pages) or
**Gelato** (everything else, 30 pages or 28 without one spread) — see the
[printer rule](rules/printer-rule.md).

The owner is not a programmer, writes in Ukrainian, and works from two computers: the **Wrocław** one
(day-to-day work, where the program runs) and a **remote Kyiv** one, where the Etsy shop is registered.
Etsy pages are only opened on the Kyiv one — see [security](security.md). The program itself is not run
on the Kyiv PC.

## Parts of the program

| Part | What it does | Wiki page |
|---|---|---|
| Orders (start screen) | The queue of new Etsy orders and the order card: the book, Canva, personalization, files, proofing, sending to print | [features/orders.md](features/orders.md) |
| Text check | A local Gemma model reads the pages, the program checks them against the book passport and Etsy data | [features/text-check.md](features/text-check.md) |
| Book library | The reference for every book: cover, 16 pages/spreads, texts, a link to Canva | [features/library.md](features/library.md) |
| Order Creator | An unpublished book (and an On-hold order) in Printify, a draft order in Gelato | [features/order-creator.md](features/order-creator.md) |
| Order archive | Files of books that went to print: proofing and reprints; live 14 days after "Sent" | [features/archive.md](features/archive.md) |
| Settings | Service keys, the Etsy connection, the Printify template, the text check, the data folder | [features/settings.md](features/settings.md) |
| Profit (hidden until 1 October) | An equivalent of the Etsy Profit Calculator: Etsy Net minus print cost | [features/profit.md](features/profit.md) |
| **«Мокапи»** — a separate utility (its own shortcut and window, since 2026-09-23) | Etsy listing pictures: a Canva demo book → the owner's Photoshop templates; he fits the front cover by hand | [features/mockups.md](features/mockups.md) |

## How it's built

- **Server** — Python (standard library + Pillow, img2pdf, cryptography), listens only on `127.0.0.1`.
  See [architecture/server.md](architecture/server.md).
- **Interface** — HTML/CSS/JS with no build step, opens as a separate Edge window (`--app`).
  See [architecture/frontend.md](architecture/frontend.md).
- **Data** — in `app/data/` (not in git): books, an order snapshot, keys (DPAPI), cache, logs.
  See [architecture/data.md](architecture/data.md).
- **Launch and shutdown** — [architecture/runtime.md](architecture/runtime.md).
- **Services** — [Etsy](integrations/etsy.md) (read-only), [Printify](integrations/printify.md),
  [Gelato](integrations/gelato.md), [Canva](integrations/canva.md) (links only).

## Earlier tools

Book Studio replaces three older programs that sit next to it on the desktop:
- **Etsy Profit Calculator** — its profit formulas were carried over one-to-one and checked by tests
  ([features/profit.md](features/profit.md));
- **Order Creator Printify** — its book-creation logic was carried into the Order Creator;
- **Etsy OS** — a failed attempt at an order pipeline; its lessons are reflected in the
  [decisions](decisions.md) ("one order — one screen").
Keys from the first two can be moved over with one button in Settings.

## Repository

```
Book Studio/            ← git root (private GitHub: raymanrboy/book-studio)
  AGENTS.md, CLAUDE.md  ← rules for agents
  app/                  ← the program (see the code map)
  wiki/                 ← this wiki
```

## Where in the code

- [app/studio/main.py](../app/studio/main.py) — `main()`: the server's entry point.
- [app/studio/core.py](../app/studio/core.py) — `APP_NAME`, `DEFAULT_PORT`, `ROOT`, `DATA_DIR`.
- The full file map — [code-map.md](code-map.md).

## Related

- [Glossary](glossary.md) · [Working with the owner](owner/working-with-owner.md) · [Decisions](decisions.md)
