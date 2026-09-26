# Book Studio

A local Windows program for a shop selling personalized books on Etsy. Sections:

- **Orders** (start screen) — the queue of new Etsy orders and each one's card: the book and its Canva
  template, the buyer's personalization, files from Canva, proofing, sending to print. See the
  [order-to-print path in the wiki](../wiki/flows/order-to-print.md).
- **Book library** — the reference version of every book: cover, 16 pages/spreads, texts, Canva.
- **Order archive** — the exact files of every book sent to print, for a quick reprint; the files delete
  themselves 14 days after the order ships to the buyer. See [the archive in the wiki](../wiki/features/archive.md).
- **Text check** (in the order card) — a local model in Ollama reads the pages from Canva and checks them
  against the book passport; the pictures never leave the computer. See [the text check in the wiki](../wiki/features/text-check.md).
- **Profit** (hidden until 1 October) — a full equivalent of the Etsy Profit Calculator: net Etsy revenue
  minus Printify/Gelato cost.
- **Order Creator** — a full equivalent of Printify's Order Creator: photo-book drafts in Printify and
  Gelato from Canva files.

## Launch

Double-click the **Book Studio** shortcut on the desktop. A separate program window opens.
When the window is closed, the program shuts itself down on its own (but first waits for any unfinished
uploads and Gelato's temporary link).

If there's no shortcut: `python app\tools\make_shortcut.py` (from the Book Studio folder). If the program
doesn't start — `Запуск з консоллю.bat` (Run with console) will show the error. Needs Python 3.11+ with
the packages from `requirements.txt` (already present on this PC; tested on Python 3.14). For the text
check — Ollama with the `gemma4:12b-it-qat` model (~7 GB); without it the program still works, just
without that check.

## Two modes: Orders and Listings

A click on the Book Studio icon at the top left (or Alt+0) switches between **Orders** (everything below,
orange, like Etsy) and **Listings** (blue): the **Workshop** — new books in development: the agents in Antigravity
write a book (the pipeline — the `pipeline/` folder), the Workshop shows its path, puts every prompt into the
clipboard and catches the picture downloaded from Gemini into its row; passed to the library with their Etsy
listing — and the **Mockups**. Book Studio always opens in Orders. More — [the wiki](../wiki/features/workshop.md).
Antigravity once: Settings → Agent → *Agent Gitignore Access* on (the books are kept out of git).

## «Мокапи» — pictures for an Etsy listing

In the Listings mode (until 2026-09-24 it was a separate program with its own shortcut — delete the old
**Мокапи** shortcut): drag the demo book's Canva ZIP onto the page, click the spreads you like (4 for Open 1, 2 for Open 2, one each for Cover & Open 1 and
All & Open 1), press «Зробити мокапи» and pick a folder. Photoshop asks once whether to run the script —
answer **Yes**. About half a minute later the folder has 7 pictures, and Photoshop has three templates
open (1. Cover 1, Cover & Open 1, All & Open 1) — fit the front cover there and save them yourself. The
templates folder `Трафарети мастхев` is never changed: Photoshop works on copies. More —
[the wiki](../wiki/features/mockups.md).

## First-time setup (1 minute)

1. **Settings → Quick start → Import.** The program finds the keys in Order Creator Printify and Etsy
   Profit Calculator on its own and moves them into its own encrypted vault.
2. **Etsy:** the simplest way — in Profit Calculator click "Скопіювати лінк доступу" (Copy access link)
   and paste it into Settings → Etsy → "Активувати" (Activate). Or "Авторизуватися в Etsy (Київ)" (Sign
   in to Etsy — Kyiv) — signing in on the Etsy page is done **only on the Kyiv computer**; the program
   gives a link for Kyiv and accepts back the address the browser was sent to. The callback URL is shown
   in Settings — it needs to be added to Etsy Developers once.
3. **Printify:** the Master product is already set up (CozyCovenant, Hardcover 8x8 Template).

## Book library

A book = one Etsy listing. Structured like the pipeline: cover, **page 1** (dedication), **spreads 2–15**
(pages 2–29), **page 30** (afterword). A spread is either one picture `8-9.png` or two pages `8.png` +
`9.png`.

- To add one: "Додати книгу" (Add book) → a link to the listing. Everything else can be added later.
- The book-preparation guide (the icon next to sorting): the correct file names for batch upload and the
  `book-text.json` format — save it to a file or copy it to hand to an agent.
- Files: "Імпорт з папки" (Import from folder — understands the pipeline folder: `generated/`, `Cover`,
  `1.png`, `2-3.png`…`30.png`, `book-text.json`), or just drag a folder, ZIP, or files into the window —
  the program lays them out by the same rules and shows what will go where before importing.
- Text: JSON `{cover, page1, spreads: {"2"…"15"}, page30}`; edited right on the page, `{Name}`/`{Gifter}`
  highlighted; copy buttons for Canva.
- Zoomable viewer: click any picture (mouse wheel, drag, ← →, Esc).
- Archive and delete (files move to `data/library/trash`, and can be restored).

## Profit

Still hidden: accounting starts on 1 October.

`Etsy Net = card total − US tax − Etsy fees (6.5% item + 6.5% shipping + 6% + $0.30 payment processing +
$0.20 listing, all + 20% VAT)`; `Profit = Etsy Net − Printify/Gelato cost`; `Margin = Profit / Etsy Net`.
The formulas and matching rules are checked by tests against the original Profit Calculator's code
(identical results to the cent).

Updates only happen via the "Update / Sync" button; between runs, the last snapshot is shown. **All** of
the shop's orders are loaded. Matching: the receipt number in Printify, the recipient's name (closest by
date), Gelato by reference/name; shared parcels split the cost evenly. Any order can be linked manually or
marked "without cost".

## Order Creator

- **Printify:** a folder with `Cover.png` + `1.png`…`24.png` (exact sizes 4672×2464 and 4000×4000) → a
  full check → upload (already-uploaded files aren't duplicated) → a new **unpublished** book built from
  the Master's configuration → a check of the positions and that the Master hasn't changed. If the
  address is filled in — also a **draft order**: an order for this book (matte variant, standard
  shipping), which in Printify waits "On hold" and only goes into production after "Submit order".
  Before the first such order, the program asks once to confirm that manual order approval (Manual) is
  turned on in the Printify shop.
- **Gelato:** a format, a folder with `Cover.png` + `1.png`…`30.png` or `1.png`…`28.png` (a book without
  one spread; which formats Gelato prints at 28 pages is decided by its catalog), an address → one PDF
  book (cover, endpaper, pages, endpaper) at the sizes from Gelato's catalog, with no recompression → a
  temporary link for Gelato (15 min) → a **draft** order.
- The folder can be picked or dragged into the block together with a ZIP archive. The page opens empty
  every time.
- "З замовлення Etsy" (From an Etsy order) fills in the title (`receipt number - child's name`) and the
  address. Orders are sorted into "Нові" (New), "В роботі" (In progress — already has an order in
  Printify/Gelato) and "Відправлені" (Sent).
- Orders from Etsy, Printify and Gelato refresh once when the program starts, and after that only with
  the refresh button.

## Plans

- [Plans](../wiki/plans/roadmap.md) and [open questions](../wiki/plans/open-questions.md) — in the
  project wiki.

## Security

- Etsy — read-only. Printify — only image uploads, creating an unpublished product, and an order waiting
  "On hold" (only after manual-approval confirmation in the shop); sending to production, cancelling,
  Express, publishing, or changing/deleting products are blocked in the client itself. Gelato — drafts
  only (`orderType: draft`), everything else is blocked.
- Keys are encrypted with Windows DPAPI and only work for your Windows user; they're never sent to the
  program window. The program listens only on `127.0.0.1`.

## Data

Everything is stored in the `app/data/` folder next to the program (as of 2026-09-22, about 6.6 GB):

- `archive/` — files of books sent to print (the largest part, ~4 GB; old ones delete themselves);
- `library/` — the library's books and illustrations (~1.6 GB), `library/trash/` — deleted books that
  can be restored;
- `profit/` — a snapshot of orders, manual links and states, `print-orders.json` (which print orders the
  program itself created for which receipt);
- `creator/` — the Printify upload cache; `vault.json` — encrypted keys;
- `logs/` — the program's log, `logs/sends/` (the send journal), `logs/checks/` (the text-check journal);
- `cache/` — image previews, `tmp/` — temporary copies (neither needs to be backed up: the program
  rebuilds them on its own);
- `mockups/` — the Mockups' folder (where the templates are, working copies of the templates, the unpacked
  demo book; no need to back up).

For a backup, it's enough to copy `app/data/` (without `cache/` and `tmp/`).

## For development

`studio/` — the Python server (standard library + Pillow, img2pdf, cryptography), `web/` — the interface
(HTML/CSS/JS, no build step). Tests (from the `app` folder): `python -m unittest discover -s tests`.
How it's all built — the [project wiki](../wiki/index.md); rules for agents — [AGENTS.md](../AGENTS.md).
