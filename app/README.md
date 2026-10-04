# Book Studio

A local Windows program for a shop selling personalized children's books on Etsy: it carries every order from Etsy
to print at Gelato, keeps the library of books, and helps make new books and their listing pictures. The rail on the
left (Alt+1…4; the magnifier or Ctrl+K is the search):

- **Замовлення** (Orders, the start screen) — the queue of Etsy orders and each one's card: the book and its Canva
  template, the buyer's personalization, files from Canva, proofing, sending to print. See the
  [order-to-print path in the wiki](../wiki/flows/order-to-print.md).
- **Книги** (Books) — the **Workshop** (books in development, written by the agents in `pipeline/`; it catches the
  pictures downloaded from Gemini), the **library** (the reference version of every shop book) and the archive.
- **Прибуток** (Profit) — an equivalent of the Etsy Profit Calculator; counts only sales from 1 October 2026.
- **Інструменти** (Tools) — the Order Creator, the print archive, the Photoshop mockups, the photo mockups and the
  listing slides, each also usable on its own.
- **Text check** (in the order card) — a local model in Ollama reads the pages from Canva and checks them against the
  book passport; the pictures never leave the computer. See [the wiki](../wiki/features/text-check.md).
- **Backup** — every 3 days the whole program goes to Google Drive as one password-protected archive.

## Launch

Double-click the **Book Studio** shortcut (in the portable folder, or on the desktop). A separate program window opens.
When the window is closed, the program shuts itself down on its own (but first waits for any unfinished
uploads, upscaling and Gelato's temporary link) and stops its own Ollama.

If there's no shortcut: the hidden `Make desktop shortcut.bat` next to the program folder makes them (in the ordinary
install: `python app/tools/make_shortcut.py`). If the program doesn't start — `Start with console.bat` (also hidden) shows the error;
the same text is in `app/data/logs/`. The portable folder carries its own Python (`runtime/python`); the ordinary install needs
Python 3.11+ with the packages from `requirements.txt`. The text check and the upscaling are **optional modules**
(Settings → «Модулі»): the check needs Ollama and the `gemma4:12b-it-qat` model (~9 GB together); without them the program still
works, just without that check.

## «Книги» — the Workshop and the library

The agents in Antigravity write a book (the `pipeline/` folder); the Workshop shows its path, puts every prompt into
the clipboard and catches the picture downloaded from Gemini into its row, then passes the finished book to
the library with its Etsy listing. Once in Antigravity: Settings → Agent → *Agent Gitignore Access* on (the books are
kept out of git). More — [the wiki](../wiki/features/workshop.md).

## «Мокапи» and the slides — pictures for an Etsy listing

Under **Tools** (or a Workshop book's step): drag the demo book's Canva ZIP onto the page, click the spreads you
like (4 for Open 1, 2 for Open 2, one each for Cover & Open 1 and All & Open 1), press «Зробити мокапи». Photoshop asks
once whether to run the script — answer **Yes**. Under a minute later the folder has 6 pictures, and Photoshop has four
templates open (Cover 1, Cover & Open 1, All & Open 1, Dedication) — fit the front cover and pick Dedication's colours
there, then «Зберегти відкриті й закрити». Every picture is cut out without its background, and «Зробити слайди» makes
the six square Etsy slides, which open in a Canva-like editor for final touches. The templates folder
`Трафарети мастхев` is never changed: Photoshop works on copies. More — [mockups](../wiki/features/mockups.md),
[slides](../wiki/features/slides.md), [photo mockups](../wiki/features/photo-mockups.md).

## First-time setup (1 minute)

1. **Keys.** If the card «Знайдено ключі з попередніх програм» is in Settings, press «Перенести»: the keys of the earlier programs
   go into the program's own encrypted vault. On a new PC, or from the ordinary Book Studio, use Settings →
   «Перенесення налаштувань» (export on one side, import on the other; the file is closed with the backup password).
2. **Etsy:** the simplest way — in Profit Calculator copy the access link and paste it into Settings → Etsy → «Підключити за лінком».
   Or «Увійти в Etsy»: with the rule «Etsy only from Kyiv» on (the owner's own copy) the sign-in is done **only on the Kyiv
   computer** — the program gives a link for Kyiv and accepts back the address the browser was sent to. The callback URL is
   shown in Settings — it needs to be added to Etsy Developers once.
3. **Gelato:** paste the key in Settings → Gelato. To move to another Gelato account use «Перейти на новий акаунт
   Gelato»: the old key is kept read-only until its orders are finished. **Printify** only reads (its token stays
   for the earlier orders).
4. **Backup:** Settings → Backup — a password of at least 12 characters; the copy goes to Google Drive every 3 days.

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

`Etsy Net = card total − US tax − Etsy fees (6.5% item + 6.5% shipping + 6% + $0.30 payment processing +
$0.20 listing, all + 20% VAT)`; `Profit = Etsy Net − Gelato/Printify cost`; `Margin = Profit / Etsy Net`.
The formulas and matching rules are checked by tests against the original Profit Calculator's code
(identical results to the cent). Only sales from 1 October 2026 count. Orders refresh when the program starts and by
the refresh button; matching goes by the receipt number, then the recipient's name (closest by date); shared parcels
split the cost evenly. Any order can be linked manually or marked "without cost".

## Order Creator

- **Gelato:** a format, a folder with `Cover.png` + `1.png`…`30.png` or `1.png`…`28.png` (a book without one
  spread; which formats Gelato prints at 28 pages is decided by its catalog), an address → one PDF book (cover,
  endpaper, pages, endpaper) at the sizes from Gelato's catalog, with no recompression → a temporary link for Gelato
  (15 min) → a **draft** order, which the owner confirms and pays in Gelato.
- The folder can be picked or dragged into the block together with a ZIP archive. The page opens empty every time.
- "З замовлення Etsy" (From an Etsy order) fills in the title (`receipt number - child's name`) and the address.
  Orders are sorted into "Нові" (New), "В роботі" (In progress — a confirmed, paid print order), the truck
  (shipped by the printer, not yet marked on Etsy) and "Відправлені" (Sent).
- Printify created books and "On hold" orders until 30 September; since 1 October it is read-only.

## Known limits

- [Known limits](../wiki/dev/limits.md) — in the project wiki.

## Security

- Etsy — read-only. Printify — read-only since 1 October 2026 (every write is blocked in the client itself).
  Gelato — drafts only (`orderType: draft`), everything else is blocked.
- Keys are encrypted with Windows DPAPI and only work for your Windows user; they're never sent to the
  program window. The program listens only on `127.0.0.1`.

## Data

Everything is stored in the `app/data/` folder next to the program (several GB):

- `archive/` — files of books sent to print (the largest part; old ones delete themselves);
- `library/` — the library's books and illustrations, `library/trash/` — deleted books that
  can be restored;
- `profit/` — a snapshot of orders, manual links and states, `print-orders.json` (which print orders the
  program itself created for which receipt);
- `creator/` — the Printify upload cache; `vault.json` — encrypted keys;
- `logs/` — the program's log, `logs/sends/` (the send journal), `logs/checks/` (the text-check journal);
- `cache/` — image previews, `tmp/` — temporary copies (neither needs to be backed up: the program
  rebuilds them on its own);
- `mockups/` — the Mockups' folder (where the templates are, working copies of the templates, the unpacked
  demo book; no need to back up).

The program backs itself up to Google Drive every 3 days ([backup](../wiki/features/backup.md)); by hand, copying `app/data/` (without `cache/` and `tmp/`) is enough.

## For development

`studio/` — the Python server (standard library + Pillow, img2pdf, cryptography), `web/` — the interface
(HTML/CSS/JS, no build step). Tests (from the `app` folder): `python -m unittest discover -s tests`.
How it's all built — the [project wiki](../wiki/index.md); rules for agents — [AGENTS.md](../AGENTS.md).
