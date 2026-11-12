---
title: Wiki index
type: index
updated: 2026-11-12
code: []
---
# Book Studio — wiki index

Book Studio is a local Windows program for an Etsy shop of personalized children's books printed by Gelato: orders, the book library and Workshop, profit, and tools (Order Creator, mockups, slides, cover). A Python standard-library server on `127.0.0.1` and a plain-JS interface in an Edge app window; data in `app/data` (not in git). On the owner's setup the program runs on one PC and Etsy is signed in to on another.
Read this page, then one or two pages below; history is git. Code map and route table on demand: `python app/tools/wiki_check.py --map` / `--routes`.

## Start here
- [Security](security.md) — before touching keys, accounts, deletions or printers
- [Glossary](glossary.md) — when the owner uses a Ukrainian word
- [Decisions](decisions.md) — before undoing a cross-cutting choice

## Orders and printing
- [Orders](features/orders.md) — the queue, order card, tabs
- [Order to print](flows/order-to-print.md) — the whole path from Etsy order to print
- [Order stages](rules/order-stages.md) — why an order is New, In progress, Sent
- [Refresh policy](rules/sync-policy.md) — when orders are loaded
- [Matching and profit](rules/reconciliation.md) — receipt to print order, costs, fees
- [Order Creator](features/order-creator.md) — files to Gelato draft, send journal
- [Print archive](features/archive.md) — printed books' files, reprints
- [Intake](flows/intake.md) — dropped files, ZIPs, filling the library
- [Book files](rules/book-files.md) — cover, 28/30 pages, file names
- [Profit](features/profit.md) — the Profit page and its numbers

## Services
- [Gelato](integrations/gelato.md) — formats, drafts, PDF, tracking
- [Etsy](integrations/etsy.md) — sign-in, receipts, ledger, read-only
- [Printify](integrations/printify.md) — read-only gate; a copy that still sends

## Books and listings
- [Workshop](features/workshop.md) — making a new book, steps, generation
- [Library](features/library.md) — book passport, slots, book.json
- [Cover tool](features/cover.md) — outpainted cover, guides
- [Mockups](features/mockups.md) — the Mockups tool, crop window, output
- [Mockups engine](features/mockups-engine.md) — templates, layers, baking
- [Photo mockups](features/photo-mockups.md) — lifestyle photos and videos
- [Listing slides](features/slides.md) — the six slides and their editor
- [Text check](features/text-check.md) — local model proofreading pages
- [Etsy SEO](features/seo.md) — titles, tags, descriptions, eRank
- [Canva extension](features/canva-extension.md) — Chrome extension inside Canva
- [Workshop books](owner/workshop-books.md) — the owner's book series

## Program, settings and data
- [Rail](features/rail.md) — places, tools, navigation, path strip
- [Settings](features/settings.md) — keys, Etsy link, settings transfer
- [Modules](features/modules.md) — optional text check and upscaling
- [Backup](features/backup.md) — Google Drive backup and restore
- [Launch and shutdown](architecture/runtime.md) — startup, ports, temp, logs
- [Server](architecture/server.md) — routes, auth modes, jobs, errors
- [Data](architecture/data.md) — data files, book.json, write_json
- [Data safety](architecture/data-safety.md) — history, snapshots, shelf, restore
- [Frontend](architecture/frontend.md) — shell, page contract, helpers

## The owner
- [Working with the owner](owner/working-with-owner.md) — how he works, what to ask
- [UI principles](owner/ui-principles.md) — interface rules and open items
- [Ideas](owner/ideas.md) — book and listing ideas, open ones
- [Future plans](owner/future-plans.md) — what is planned next

## Development
- [Portable copy](dev/portable.md) — setup, runtime folder, copy for a colleague
- [Testing](dev/testing.md) — running tests, fixtures, pitfalls
- [Preview](dev/preview.md) — viewing the interface on made-up data
- [Limits](dev/limits.md) — known limits
- [Recipes](dev/recipes.md) — steps for common changes
