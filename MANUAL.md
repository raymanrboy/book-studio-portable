# Book Studio — user manual, written for an LLM agent

> **Who this is for.** A person who owns (or helps run) an Etsy shop of personalized children's books, and the AI agent
> (Claude Code, Antigravity, Codex, …) sitting next to them. The agent reads this file first, then answers the person's
> questions, walks them through the program, and fixes small problems. The interface is in **Ukrainian**; interface words
> are quoted here as «Ukrainian» with a short English gloss. For code changes read `AGENTS.md`, not this file.
>
> **How to use it.** Find the person's situation in §3 (first start), §5 (what they want to do) or §8 (something is
> broken). Every section ends with where the details live (`wiki/…`). If this file and the program disagree, the program
> is right — say so and fix this file.

## 1. What Book Studio is

A local Windows program (a Python server on `127.0.0.1` + an Edge app window). It does five jobs:

1. **Orders** — pulls the shop's Etsy orders, shows a queue, and carries each order *Etsy → Canva → files → proofing →
   print* until the book is at the print shop (**Gelato**; **Printify** where the setting allows it).
2. **Books** — the **Workshop** («Майстерня») where new books are developed with AI agents, the **library**
   («Бібліотека») of finished books (one book = one Etsy listing), and the archive.
3. **Listing pictures** — Photoshop **mockups**, photo mockups and six **listing slides** per book, made without Canva.
4. **Profit** («Прибуток») — Etsy net revenue minus print cost per order.
5. **Safety net** — a local AI **text check** of the pages, a **backup** every 3 days, an **export/import** of settings.

Everything is stored locally in `Book Studio/app/data/`. The program never publishes anything, never changes the Etsy shop
(read-only), and creates only *drafts* at Gelato.

## 2. The folder and how to start

```
Book Studio Portable/
  Start Book Studio.bat          start (no console window)       Start with console.bat — start, errors stay visible
  Make desktop shortcut.bat      puts «Book Studio Portable» on the desktop
  ПРОЧИТАЙ.md                    a short note for the person
  (the launchers and the note are kept in the repository's portable/; a missing portable folder is built from a clone:
   python app/tools/setup_portable.py --python — see wiki/dev/portable-setup.md)
  runtime/                       the programs the app needs — nothing is installed on the PC:
    python/  Photoshop/  Templates/  ffmpeg/  Antigravity/  Installers/   (always there)
    Ollama/ (+models)  Upscayl/                                           (appear when the optional modules are installed, §3)
  Book Studio/                   the program itself
    MANUAL.md                    this file
    AGENTS.md, CLAUDE.md         rules for agents that change the code
    app/                         studio/ (server), web/ (interface), tests/, tools/, data/ (the person's own data)
    pipeline/                    the book agents' rules (pipeline/AGENTS.md) + books/ (the Workshop's books)
    wiki/                        the knowledge base — start at wiki/index.md
```

- **Start:** double-click `Start Book Studio.bat`. The app window opens. A second start of the same copy just opens another window of the running one; a different copy (the ordinary Book Studio, another portable folder) on the same PC starts its own server on another port.
- **Close:** close the window; the server stops (a running backup or upload makes it wait).
- **Move to another PC or another folder:** copy the whole folder. The program keeps to its own folder and does not depend on where it
  lies (the few paths it stores inside `app/data` follow the folder automatically). On a new PC it shows one window
  «Немає в теці runtime» (what is missing, if anything) and «Перший запуск…» (what to log in to).
- **Needs from Windows itself:** only the *Microsoft Visual C++ 2015–2022 (x64)* runtime (for Photoshop, Upscayl, Antigravity). If it is
  missing the program asks «Встановити зараз — тихо?» and installs it quietly (administrator's permission is asked by Windows). By hand in a
  terminal: `runtime\Installers\vc_redist.x64.exe /install /quiet /norestart`, or `winget install --id Microsoft.VCRedist.2015+.x64 -e --silent`.
  Everything else (Python, ffmpeg, 7-Zip, the Photoshop and its templates…) is inside the folder; Ollama and Upscayl come as optional modules.
  Edge is used for the app window and for the Gelato/Canva links (the default browser if Edge is missing).
- In the Workshop's *generation mode* the person pastes prompts into an image generator in the browser, and the program follows **Ctrl+V while
  Chrome is the front window** (F8 works anywhere). Chrome is normally the person's own browser; nothing is bundled or installed for it.
- **Restart after code changes:** changes under `app/studio/` take effect only after a restart.
- The page address is `http://127.0.0.1:<port>/` (port 47821; a random free port if that one is busy); the server answers only this PC.

## 3. First start — the checklist

Do these in order. The person only needs to do each once per PC.

| # | What | Where / how |
|---|---|---|
| 1 | Read the startup window; put in `runtime/` whatever it says is missing | folder `runtime/<name>` |
| 2 | **Gelato** key | Settings → «Gelato» ← Gelato Dashboard → Developer → API keys |
| 3 | **Etsy** keys: *Keystring* and *Shared Secret*; add the **Callback URL** shown in the block's details (the chevron under the fields — `http://localhost:<port>/etsy/callback`) to the Etsy app; then sign in | Settings → «Etsy» ← Etsy Developers → Your apps (Keystring, Shared Secret, Callback URLs). Sign in with the button «Увійти в Etsy» — read-only access. The address contains the port, so keep port 47821 free (if it is busy the program uses another and Settings warns) |
| 4 | **Printify** token (only if the person prints at Printify) | Settings → «Printify» ← Printify → My account → Connections → API. The shop and the Master (template product) are preset; «Обрати шаблон (Master)» appears only when none is set — see `wiki/integrations/printify.md` |
| 5 | **Backup password** (≥ 8 chars; the person must write it down — it cannot be recovered) | Settings → «Резервна копія» |
| 6 | Antigravity: sign in with the person's Google account | open Antigravity once (Workshop → «Нова книга» does it) |
| 7 | Gelato / Canva links open in Edge in the program's own profile (`app/data/work-browser`): sign in once | click «Відкрити шаблон у Canva» in an order card / «Замовлення в Gelato» on a created draft |
| 8 | Optional: the text check and upscaling | Settings → «Модулі» → «Встановити» (internet, then it works by itself) — see below |
| 9 | Click refresh (↻) in «Замовлення» | the first sync fills the queue |

Keys are stored encrypted for the **current Windows user** (DPAPI). They do **not** open on another PC or another Windows
user. To carry keys: Settings → «Перенесення налаштувань» → «Експорт у файл» on the old PC (needs the backup password) and
«Імпорт із файлу» on the new one — it moves settings + keys + slide schemes (not books or orders).
**Never** ask the person to paste keys into the chat, and never read `app/data/vault.json`.

Etsy connection: normally the person signs in from the same PC. If the settings say `security.etsyKyivOnly: true` (an
owner's personal rule), Etsy pages are refused on this PC and the sign-in is done elsewhere — see `wiki/integrations/etsy.md`.

### Optional modules (the heavy parts)

Two features are **not installed by default** and the program offers them where they would be used (or Settings → «Модулі»):
**«Розумна вичитка тексту»** (Ollama + a model, ≈ 9 GB, needs a graphics card — the proofing step of an order) and **«Апскейл картинок ×2»**
(Upscayl, ≈ 40 MB — the Workshop's switch). Click «Встановити»: the program downloads the official files, checks them and sets them up in
`runtime/` by itself, showing progress; no administrator's rights. «з файлу» installs from a ZIP without the internet; the bin icon removes a module
(its folder under `runtime/`, the text check's model included; books and settings stay). In the portable copy a module counts only when it is in
`runtime/` — an Ollama or Upscayl the PC has is never used; so after removing one, the offer to install it returns.
Without a module the rest of the program works as usual.

## 4. The screens

One icon rail on the left (hover for names): **Замовлення** (Alt+1), **Книги** (Alt+2), **Прибуток** (Alt+3),
**Інструменти** (Alt+4), **Пошук** (Ctrl+K), and at the bottom **Налаштування** and the theme switch («Вигляд»).

| Screen | What it is | Wiki |
|---|---|---|
| Замовлення | The queue in four tabs (icons with counts): **Нові** · **Друкуються** · **Позначити в Etsy** (truck: the printer shipped it, the person still has to mark it shipped on Etsy) · **Відправлені**. Click an order → the order card | `features/orders.md` |
| Книги → Майстерня | Books in development: a path strip (Формула · Герой · Історія · Текст · Промпти · Картинки · Обкладинка · Canva · Мокапи · Фото · Бібліотека), then rows of prompt · 2:1 spread · text | `features/workshop.md` |
| Книги → Бібліотека / Архів | Finished books, one per Etsy listing | `features/library.md` |
| Прибуток | Profit per order (counts only sales from **1 Oct 2026**) | `features/profit.md` |
| Інструменти → Order Creator | Steps Формат · Папка з файлами · Назва · Адреса отримувача → «Створити чернетку» (a Gelato draft; Printify where allowed) | `features/order-creator.md` |
| Інструменти → Архів друку | What was really sent to print (files kept 14 days after the order is marked shipped; «не видаляти» keeps one) and reprints («Передрук у Gelato») | `features/archive.md` |
| Інструменти → Мокапи | Canva demo book → Photoshop → Etsy pictures | `features/mockups.md` |
| Інструменти → Фотомокапи | Lifestyle photos with our book (via an image generator) | `features/photo-mockups.md` |
| Інструменти → Слайди лістингу | The scheme of the listing slides (Nature, Night…) and its Canva-like editor; a book's own slides are made in the Mockups | `features/slides.md` |
| Налаштування | Keys, Etsy, Gelato, Printify, text check, backup, settings transfer, data folder | `features/settings.md` |

## 5. What the person wants to do

### 5.1 Fulfil an Etsy order (the main job)

1. «Замовлення» → click ↻ (the program also refreshes once at start). New orders are in the first tab, **Нові**.
2. Open the order. The card has a path strip on top — **Canva → Файли → Вичитка → Друк → Відправка** — and under it the buyer's
   personalization (child's name, dedication, «From whom», the buyer's message, the address) with **«Копіювати»** buttons: copy, never
   retype. The book is found by the Etsy listing number in the library.
3. «Відкрити шаблон у Canva» (the link from the book's passport). In Canva: make a copy, replace `{Name}` with the child's name,
   fill the dedication, **download the PNG pages** (30 pages, or 28 without one spread).
4. Step 2 **«Файли з Canва»**: drag the downloaded ZIP or folder onto the card, or press «Обрати папку». The program lays out
   `Cover.png` + `1…N.png` and checks the files.
5. Step 3 **«Вичитка»** (proofing): look at the cover and the spreads. If the text-check module is installed the local model reads the
   text pages and flags mismatches against the book passport (≈ 20–50 s); without it the badge says «Вичитка не встановлена» with a
   download icon. The check **never blocks printing — it only asks**. A wrong page → fix it in Canva, download **just that page** and
   replace it in the viewer (the swap icon with the page number, tooltip «Замінити …»; «Undo» is next to it).
6. Step 4 **«Друк»**: the big button **«До друку в Gelato»** (with «· N книги» for several books) opens the Order Creator filled in
   (format, folder, title `receipt - name`, address) → **«Створити чернетку»**. A **draft** is created at Gelato; nothing is paid or
   produced yet. The card then shows the green «Чернетку замовлення створено в Gelato!» with the button «Замовлення в Gelato».
7. In Gelato (that button) the person opens the draft, confirms and pays. Back in Book Studio click ↻: the order moves to
   **Друкуються** only when it is confirmed and paid (a draft leaves it in **Нові** with a `Draft` chip).
8. When the printer ships, the order appears on the truck tab **«Позначити в Etsy»** with carrier + tracking (click the carrier or the
   number to copy it). The person marks it shipped on Etsy, then ↻ → **Відправлені**.
9. If a book was damaged: the order card's archive icon («Що пішло в друк · передрук») or Інструменти → Архів друку → the entry →
   **«Передрук у Gelato»** — a new draft from the same files.

Several books in one order: the card has a switch «Книга 1 / Книга 2»; each is proofed separately; one draft, one address is created.
Details and every edge case: `wiki/flows/order-to-print.md`, `wiki/features/orders.md`.

**Which printer.** Gelato prints every book since 1 Oct 2026 in the original owner's setup (`printify.readOnlyFrom`). Where
that setting is empty (Printify is live), the older rule applies: a hardcover with 24 pages → Printify; 28 or 30 pages →
Gelato; softcovers (incl. 5.5×5.5) → Gelato only. Gelato formats: Hardcover 8×8, Softcover 8×8, Softcover 5.5×5.5.
See `wiki/rules/printer-rule.md`.

### 5.2 Make a new book (the Workshop)

1. Книги → Майстерня → **«Нова книга»** (tooltip «Нова книга — в Antigravity»). Antigravity opens and the clipboard holds the words to paste into the agent's chat
   (the agent reads `pipeline/AGENTS.md` and leads the person step by step: formula, hero, story, text, prompts).
2. The book appears in the Workshop as a card; its page shows the path strip and the rows (page 1, spreads 2–3 … 28–29, page 30, the
   cover). Each row has a **prompt**, a **2:1 spread** and a **text**. «Canva» and «Мокапи» are ticked by hand.
3. **Generation mode** («Генерувати решту» / «Ще раз» on a row): the program puts the prompt in the clipboard; the person pastes it into
   the image generator (Gemini/ChatGPT; for a multi-part paste — the hero picture, then the prompt — **Ctrl+V in Chrome** or **F8** puts in
   the next part), downloads the picture, and the program **catches it from Downloads**, cuts it, flips it and places it in the row. With
   the upscale module installed it also upscales ×2 («Апскейл ×2» switch; «Апскейлити ×2» on a row).
4. Next steps of the same book: «Мокапи» (Photoshop), «Фото» (photo mockups), then **«Передати в бібліотеку»** (hands the finished
   book over to the library with its Etsy listing).
Details: `wiki/features/workshop.md`, `wiki/flows/book-import.md`, `pipeline/AGENTS.md` (the book agents' rules).

### 5.3 Etsy pictures for a listing

- **Mockups** (Інструменти → Мокапи, or the book's «Мокапи» step; titled «Демо-книга з Canva → картинки для лістингу Etsy»): drop the Canva
  demo-book ZIP on the right («Перетягніть сюди ZIP із Canva»); step 1 «Розвороти в шаблонах» — click the spreads that look good in each
  template; 2 «Куди зберегти»; 3 «Photoshop»; 4 **«Зробити мокапи»** — one Photoshop script fills the templates and saves 6 PNGs; a few
  templates stay open for the hand fitting of the cover, and «Зберегти відкриті й закрити» saves them. Each picture is also cut out
  without its background.
- **Listing slides**: after the mockups, **«Зробити слайди»** builds the book's slides — six, or seven when the hero has two or more looks
  (slide 7 shows them on white); a *scheme* such as Nature or Night sets the look; «Відкрити в редакторі» is for touches. An agent can
  change them through files: skill `/listing-slides`.
- **Photo mockups** (Фотомокапи; categories «Головне фото», «Відкрита книга», «Бабуся читає», «У руках дитини», «На полиці», «Для відео»):
  add the book's cover where asked, click a template — the clipboard gets the photo, then **Ctrl+V in Chrome** (or F8) puts in the prompt — the
  generator makes the picture, and the program catches the finished photo into the book's `etsy/` folder.
Photoshop, the templates and the cut-out use `runtime/Photoshop` and `runtime/Templates` (the templates are **read-only** —
never edit them; the program works on copies).

### 5.4 Profit

«Прибуток» lists each Etsy receipt with net revenue, print cost and margin, with periods (Сьогодні · 7 днів · 30 днів · Увесь час · Свій період)
and filters (**Усі · Без пари · Проблемні**); the button «Оновити замовлення» (↻) refreshes the data. Orders can be linked by hand («receipt → print order») or marked cancelled / refunded / replaced.
`wiki/features/profit.md`, `wiki/rules/reconciliation.md`.

### 5.5 Backup, export, import

- **Backup** — every 3 days (2 minutes after start) the whole program folder + the mockup templates go to the person's
  Google Drive as one password-protected 7-Zip (keys inside). Needs "Google Drive for desktop". Button «Зробити копію зараз».
  Restore: unpack with 7-Zip + password; keys on another PC via `app/tools/restore_keys.py`. `wiki/features/backup.md`.
- **Settings export/import** — see §3. Before an import the current settings are saved to `app/data/import-backup/`.

## 6. Rules the program (and any agent) must keep

- **Etsy is read-only.** The program never edits the shop. **Gelato: drafts only.** Printify (if live): only image
  uploads, an unpublished product and «On hold» orders after manual-approval confirmation; never *send to production,
  cancel, Express, publish*, or change/delete products; the Master product is never changed.
- **No live writes** to the person's accounts without their direct permission in chat. For checks use the tests and the
  sample-data preview, not the real accounts.
- Keys are never read, printed or copied into files/URLs/logs. Never open `app/data/vault.json`.
- The person's data is never permanently deleted by an agent (the program itself deletes archive files 14 days after «Sent»).
- The mockup templates in `runtime/Templates` are read-only.
- Interface preview on **sample data only**: `python app/tools/dev_server.py --sample` (port 47890) — never on the real data.
- Commit/push only when the person asks. This copy has no git remote.

Personal switches in `app/data/settings.json` (edit only if the person asks): `security.etsyKyivOnly` (true = Etsy pages
refused on this PC), `printify.readOnlyFrom` (a date, or null = Printify is never read-only), `ui.theme` (`light`/`dark`).

## 7. Where things are (for diagnosing)

| What | Where |
|---|---|
| Logs | `app/data/logs/app.log`, `printify.log`, `gelato.log`; a startup crash — `startup-error.txt` |
| What was sent to a printer | `app/data/logs/sends/` (one JSON per attempt, no keys) |
| Text-check results | `app/data/logs/checks/` |
| Orders snapshot, links, states | `app/data/profit/` |
| Library books | `app/data/library/books/<id>/book.json` |
| Order archive | `app/data/archive/` (self-deleting) |
| Mockups, slide schemes | `app/data/mockups/`, `app/data/slides/` |
| The Workshop's books | `pipeline/books/<n>.<slug>/` (outside `app/data`) |
| Settings / keys | `app/data/settings.json` / `vault.json` (never open) |

Full map: `wiki/architecture/data.md`, `wiki/code-map.md`.

## 8. Troubleshooting

| Symptom | Likely cause → what to do |
|---|---|
| «Потрібна системна програма» (Visual C++) at start | Answer Yes (quiet install) or run the command from the window in a terminal; then start again |
| The Workshop's «Апскейл ×2» is grey, with «Встановити апскейл» beside it | The upscale module is not installed → click it (≈ 40 MB, internet needed) |
| Window at start lists missing programs | A folder in `runtime/` is empty → copy it from a computer that has it. `Start with console.bat` shows more |
| Nothing opens; `startup-error.txt` exists | Read it. A missing Python package → the bundled Python is complete; if you changed `runtime/python`, restore it |
| «Ключі … не відкриваються на цьому комп'ютері» | Keys are locked to another Windows user → enter them in Settings, or import the settings file (§3) |
| Etsy: «Сесія … більше не дійсна» | Etsy refresh tokens are single-use and another program used it → sign in again (Settings → Etsy) |
| Etsy page refused: «лише з київського» | `security.etsyKyivOnly` is true → set it to false only if the person says so |
| «Printify лише для читання» | `printify.readOnlyFrom` holds a date in the past → empty it (null) if the person still prints at Printify |
| Gelato draft created but the print shop can't fetch files | The PDFs are served by a temporary Cloudflare link (`app/bin/cloudflared.exe`) while the program runs; keep the program open ~a minute after «Create» |
| «Вичитка не встановлена», or the text check does not work | The module is not installed → «Встановити» (Settings → «Модулі»). If it is installed but not running: «Запустити» under the module (the text check's switches, the model and «Перевірити зв'язок» are there too). The copy's own Ollama listens on port **11435** and keeps its model in `runtime/Ollama/models`; an Ollama the PC has (port 11434) is neither used nor touched |
| Photoshop asks «run this script?» | Normal in a fresh Photoshop; the person confirms. An agent must not change Photoshop's own settings |
| A second window opens when starting | The same copy is already running; use the open window |
| Etsy sign-in fails with a redirect/port message | The Callback URL in the Etsy app must match the one in Settings → Etsy exactly, port included; keep port 47821 free |
| Gelato/Canva links open in the usual browser, not the program's profile | The program's Edge profile is used only when Edge is installed (`data/work-browser`); otherwise the default browser opens them |
| Orders look stale | Orders refresh only at start and with ↻ (by design) |
| Slow first start of the Workshop | Thumbnails are built once and cached (`app/data/cache/`) |

If something is wrong and not in this table: read `app/data/logs/app.log` (tail), then the wiki page of that screen, then the
code via `wiki/code-map.md`.

## 9. What an agent may do

- **Explain** any screen or step above; point to the right button; translate the Ukrainian labels.
- **Diagnose** from logs and settings (read-only), and propose the fix as exact steps.
- **Small safe changes** with the person's consent: the personal switches in §6, a slide scheme through the
  `/listing-slides` skill, a book's text in the Workshop.
- **Code changes** only following `AGENTS.md` (wiki first; tests pass; wiki updated). Commands:
  `python app/tools/wiki_check.py`; `cd app && python -m unittest discover -s tests`; `python app/tools/dev_server.py --sample`.
  Use the bundled Python: `..\runtime\python\python.exe`.
- **Never**: use the person's real keys or accounts for experiments, publish, send to production, or touch files outside
  this folder.

## 10. Glossary (Ukrainian interface → meaning)

| Word | Meaning |
|---|---|
| Замовлення / Книги / Прибуток / Інструменти | Orders / Books / Profit / Tools |
| Майстерня | Workshop — books in development |
| Бібліотека, Архів | Library of finished books; archive (hidden books) |
| Вичитка | Proofing — the step where text is checked (the model's findings) |
| Файли з Canva | The folder/ZIP of PNG pages downloaded from Canva |
| Мокапи, Фотомокапи | Photoshop mockups; photo mockups |
| Слайди лістингу | The six Etsy listing slides |
| Архів друку | Print archive — what was sent to print; reprints |
| Передрук | Reprint |
| Чернетка / `Draft` | A Gelato draft order — not yet confirmed or paid (the step «Чернетка» in the Order Creator; the chip `Draft` in the queue) |
| Позначити в Etsy | The truck tab: the printer shipped it, now the person marks the order shipped on Etsy |
| Друкуються / Відправлені / Нові | Printing / Sent / New (the queue's tabs) |
| Вигляд | The theme switch (light/dark) at the bottom of the rail |
| Модулі | Optional heavy parts: the text check and upscaling |
| Резервна копія | Backup |
| Перенесення налаштувань | Settings transfer (export/import) |

More terms: `wiki/glossary.md`. Where every question is answered: `wiki/index.md`.
