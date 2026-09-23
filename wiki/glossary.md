---
title: Glossary — the owner's words and their places in the code
type: reference
updated: 2026-09-23
code: []
---
# Glossary

> The owner describes the program in his own words. This maps each such word to a place in the code.
> If the owner names something that isn't listed here, find it in the code and add a row.

Code paths below are relative to the repository root.

## Orders and printing

| Owner's word (Ukrainian) | What it is | Where in the code |
|---|---|---|
| Замовлення (сторінка), черга | The first screen: the list of Etsy orders by stage | [orders.js](../app/web/js/pages/orders.js) `mountQueue()` |
| Картка замовлення | One screen for one order | [orders.js](../app/web/js/pages/orders.js) `mountCard()` |
| Нові / В роботі / машинка / Відправлені | Order stages (`new` / `work` / `sent` / `shipped`) | [profit.py](../app/studio/profit.py) `order_stage()`; [order-bits.js](../app/web/js/order-bits.js) `STAGES` |
| Машинка (вкладка) | Stage `sent`: the printer has already shipped it (a tracking number or "shipped" status), but Etsy hasn't marked it yet | [profit.py](../app/studio/profit.py) `order_stage()`; [order-bits.js](../app/web/js/order-bits.js) `STAGES`; [rules/order-stages.md](rules/order-stages.md) |
| Замовлення на кілька книг, «Книга 1 / Книга 2» | One Etsy receipt with several books: in the card, each has its own folder, proofing and text check, and they go to print together as one draft to one address | [orders.js](../app/web/js/pages/orders.js) `readyBooks()`, `printCard()`; [creator.py](../app/studio/creator.py) `books_of()`, `joint_title()`; [features/orders.md](features/orders.md) |
| Швидкий огляд сторінок, пред-перевірка | The program looks at a preview of every page itself and works out where there's any text at all: only those pages are shown to the model | [images.py](../app/studio/images.py) `text_score()`; [textcheck.py](../app/studio/textcheck.py) `page_kinds()`; [features/text-check.md](features/text-check.md) |
| Замінити сторінку | The button in the viewer: a page fixed in Canva and downloaded separately takes the place of the old one; "Undo" sits next to it | [creator.py](../app/studio/creator.py) `replace_page()`; [orders.js](../app/web/js/pages/orders.js) `replacePage()`; [features/orders.md](features/orders.md) |
| Бокс, коробка (вкладка) | "Sent" — marked as shipped on Etsy | [profit.py](../app/studio/profit.py) `order_stage()` |
| Годинник (вкладка) | "In progress" | [order-bits.js](../app/web/js/order-bits.js) `STAGES` |
| Квадратик справа (у рядку черги), статус | The chip on the right: the printer's status in plain English ("In transit"), with a colored dot | [order-bits.js](../app/web/js/order-bits.js) `statusChip()`, `statusText()`; [profit.py](../app/studio/profit.py) `picker_orders()` (`printStatus`) |
| Трек-номер, перевізник (USPS…) | The chip after the printer chip: carrier \| number; a click copies the number | [order-bits.js](../app/web/js/order-bits.js) `trackChips()`, `copyChip()`; [printify.py](../app/studio/printify.py) `slim_order()`; [gelato.py](../app/studio/gelato.py) `attach_shipments()` |
| Останній стан, «повертає, де я був» | A new order's card and the Order Creator working on it are kept when switching to another tab | [keep.js](../app/web/js/keep.js); [app.js](../app/web/js/app.js) `navigate()`; [architecture/frontend.md](architecture/frontend.md) |
| Номер замовлення Etsy, номер чека | The `#…` in the queue and the card's header; a click copies the digits without "#" | [order-bits.js](../app/web/js/order-bits.js) `receiptCopy()`, `copyChip()` |
| Оновити замовлення, синхронізація | Loading orders from Etsy + Printify + Gelato | [profit.py](../app/studio/profit.py) `_sync()`, `startup_sync()`; [order-bits.js](../app/web/js/order-bits.js) `syncOrders()` |
| Друкарня, постачальник | Printify or Gelato | [orders.py](../app/studio/orders.py) `plan_for()` |
| Правило друкарні | Hardcover in the US → Printify, everything else → Gelato | [rules/printer-rule.md](rules/printer-rule.md) |
| Персоналізація, поля Etsy | The buyer's variations (name: value) | [profit.py](../app/studio/profit.py) `normalize_receipt()`; [orders.js](../app/web/js/pages/orders.js) `renderLeft()` |
| Ім'я дитини | The value of the field with "name/child…" in its name | [creator.py](../app/studio/creator.py) `guess_child_name()` |
| «Від кого» | The field name in the Etsy listing; shown as-is | [orders.js](../app/web/js/pages/orders.js) `renderLeft()` |
| Свій текст (присвята не DEFAULT) | The "custom text" tag next to a field | [order-bits.js](../app/web/js/order-bits.js) `isCustomText()` |
| Формат обкладинки (Cover Type & Size) | The field that decides the printer; no copy button and no line in the notes | [order-bits.js](../app/web/js/order-bits.js) `isFormatField()` |
| Повідомлення покупця | `message_from_buyer` from the Etsy receipt | [orders.py](../app/studio/orders.py) `_one()` |
| Файли з Canva, розставити сторінки | A ZIP/folder from Canva → `Cover.png` + `1…N.png` | [orders.py](../app/studio/orders.py) `arrange_pages()` |
| Звірка | Card step 2: the cover, the first spread, the filmstrip | [orders.js](../app/web/js/pages/orders.js) `proofCard()` |
| Записка (на форзаці) | The left half of the proof's first spread: the name and the buyer's fields | [orders.js](../app/web/js/pages/orders.js) `proofCard()`; CSS `.proof-note` in [app.css](../app/web/css/app.css) |
| Стрічка, слайдер сторінок | The horizontal row of every spread in the proof | [orders.js](../app/web/js/pages/orders.js) `proofCard()`; [order-bits.js](../app/web/js/order-bits.js) `smoothWheel()` |
| До друку | Handing the order off to the Order Creator | [orders.js](../app/web/js/pages/orders.js) `print()`; [handoff.js](../app/web/js/handoff.js) `give()` |
| Order Creator | The book/draft creation page | [creator.js](../app/web/js/pages/creator.js) `mount()`; [creator.py](../app/studio/creator.py) |
| Чернетка Gelato | A Gelato order with `orderType: draft` | [creator.py](../app/studio/creator.py) `create_gelato_draft()` |
| Логи відправки, журнал відправок | JSON for every send to Printify/Gelato (`data/logs/sends/`) | [sendlog.py](../app/studio/sendlog.py); [features/send-journal.md](features/send-journal.md) |
| Page 0 (у чернетці Gelato) | An empty endpaper — that's how it should be | [integrations/gelato.md](integrations/gelato.md) |
| 28-сторінкова / 30-сторінкова книга (Gelato) | How many pages were downloaded from Canva (28 — without one spread); there's no separate switch for it | [creator.py](../app/studio/creator.py) `gelato_page_options()`, `gelato_pages_problem()`; [integrations/gelato.md](integrations/gelato.md) |
| Чернетка замовлення Printify, «On hold» | A book + an order waiting on "Submit order" | [creator.py](../app/studio/creator.py) `create_printify_draft()`; [printify.py](../app/studio/printify.py) `create_order_on_hold()` |
| Книга без замовлення (Printify) | Only an unpublished product, the address left empty | [creator.py](../app/studio/creator.py) `create_printify_draft()` |
| Master, шаблон Printify | The reference product whose configuration gets copied | [creator.py](../app/studio/creator.py) `build_printify_payload()`; [settings.js](../app/web/js/pages/settings.js) `pickMaster()` |
| Ручне затвердження (Manual) | A Printify shop setting; the program asks about it once | [printify.py](../app/studio/printify.py) `manual_approval_confirmed()`; [creator.js](../app/web/js/pages/creator.js) `confirmManualApproval()` |
| Матовий фініш | The Master variant with "Matte" in its name | [creator.py](../app/studio/creator.py) `matte_variant()` |
| Тимчасове посилання (для Gelato) | A Cloudflare tunnel to a single PDF | [tunnel.py](../app/studio/tunnel.py) `FileTunnel` |
| Перетягнути папку або ZIP | Copying it into the program and unpacking it | [order-bits.js](../app/web/js/order-bits.js) `receiveDrop()`; [drops.py](../app/studio/drops.py) `extract_zip()` |
| Очистити адресу (гумка) | The icon in the address block | [creator.js](../app/web/js/pages/creator.js) `addressCard()` |
| Заповнити із замовлення Etsy | Picking an order in the Order Creator | [creator.js](../app/web/js/pages/creator.js) `fromEtsy()` |

## Book and library

| Owner's word (Ukrainian) | What it is | Where in the code |
|---|---|---|
| Бібліотека | The gallery of reference books | [library.js](../app/web/js/pages/library.js) `mount()`; [library.py](../app/studio/library.py) |
| Паспорт книги | One book's page | [book.js](../app/web/js/pages/book.js) `mount()` |
| Обкладинка | The full cover spread (`cover`, `Cover.png`) | [library.py](../app/studio/library.py) `SLOT_KEYS` (separate from the slots) |
| Заставка | The book's picture in the gallery (`thumbnail`) | [library.py](../app/studio/library.py) `summary()` |
| Присвята | Page 1 (`page1`) | [library.py](../app/studio/library.py) `slot_label()` |
| Розворот N | Pages 2N−2 and 2N−1 (`spread2`…`spread15`) | [library.py](../app/studio/library.py) `spread_pages()` |
| Післяслово | Page 30 (`page30`) | [library.py](../app/studio/library.py) `slot_label()` |
| Форзац / нахзац | The blank pages next to the cover (in print) | [order-bits.js](../app/web/js/order-bits.js) `spreadsOf()` |
| Текст книги, `book-text.json` | The texts of the cover, dedication, spreads, afterword | [library.py](../app/studio/library.py) `parse_text_json()` |
| `{Name}`, `{Gifter}` | Placeholders for the child's name and the gift-giver | [lib.js](../app/web/js/lib.js) `highlightTokens()` |
| Інструкція для агента | A file about file names and the JSON format | [library.py](../app/studio/library.py) `agent_guide()`; [library.js](../app/web/js/pages/library.js) `saveGuide()` |
| Імпорт з папки | Laying out a folder's files into the slots | [library.py](../app/studio/library.py) `scan_folder()` |
| Апскейл, Upscayl | The `_upscayl…` tail in file names is ignored | [library.py](../app/studio/library.py) `scan_folder()`; [drops.py](../app/studio/drops.py) `page_number()` |
| Архів (у бібліотеці) | The book is hidden from the working list | [library.py](../app/studio/library.py) `_archive()` |
| Архів замовлень | A separate menu with the files of books that went to print (14 days after "Sent"), and reprints | [archive.py](../app/studio/archive.py); [archive.js](../app/web/js/pages/archive.js); [features/archive.md](features/archive.md) |
| Передрук, редрук | Reprinting the same book from the order archive: Printify — a new order for the same book, Gelato — a new draft | [creator.py](../app/studio/creator.py) `create_printify_reprint()`; [features/archive.md](features/archive.md) |
| Не видаляти (у архіві) | The pin on a book in the archive: the files stay until the mark is removed | [archive.py](../app/studio/archive.py) `_keep()` |
| Оформлене замовлення (в друкарні) | Confirmed and paid, not a draft, not "on hold", not cancelled; only this moves the order into "in progress" and puts the book in the archive | [profit.py](../app/studio/profit.py) `is_placed()`; [rules/order-stages.md](rules/order-stages.md) |
| Завершити роботу над замовленням | The × in the order card and in the Order Creator after a successful send: the program forgets the saved work on this order and opens the queue | [keep.js](../app/web/js/keep.js) `finish()`; [features/orders.md](features/orders.md) |
| Вигаданий номер (телефон) | The phone number filled into Gelato when the Etsy order doesn't have one: `+1 555 555 0100` | [creator.py](../app/studio/creator.py) `GELATO_PLACEHOLDER_PHONE` |
| ШІ-валідатор, перевірка тексту, «кнопка перевірити» | A local model reads the pages in the order card, the program checks them against the book passport | [textcheck.py](../app/studio/textcheck.py) `check_order()`; [orders.js](../app/web/js/pages/orders.js) `startCheck()`; [features/text-check.md](features/text-check.md) |
| Gemma, локальна модель, Ollama | `gemma4:12b-it-qat` in Ollama, on this PC's graphics card | [textcheck.py](../app/studio/textcheck.py) `DEFAULT_MODEL`, `status()`, `start_ollama()` |
| Сліпе переписування / з підказкою | The "read" pass (the model doesn't know what should be there) and the "check" pass (it does) | [textcheck.py](../app/studio/textcheck.py) `READ_PROMPT`, `STRICT_PROMPT` |
| Паспорт застарів, оновити паспорт | The passport's texts don't match the Canva template — they're taken from the printed book | [orders.js](../app/web/js/pages/orders.js) `learnPassport()`; [textcheck.py](../app/studio/textcheck.py) `_passport()` |
| Взяти файли минулої відправки | The button in the order card: files from a send that never became an order (cancelled, a deleted draft) are taken from the archive — and the order is sent like a normal one | [orders.js](../app/web/js/pages/orders.js) `takeEarlier()`; [features/archive.md](features/archive.md) |
| «+N у друці» (чип у черзі) | This receipt has N more print orders besides the one whose status is shown: the books went in two batches, or to two printers | [order-bits.js](../app/web/js/order-bits.js) `alsoSentChip()`; [profit.py](../app/studio/profit.py) `picker_orders()` (`alsoSent`); [rules/reconciliation.md](rules/reconciliation.md) |
| Відправка (записана програмою) | The list of print orders the program itself created for a receipt — the full cost is counted from it | [profit.py](../app/studio/profit.py) `remember_print_order()`, `SENDS` |
| Кошик | `data/library/trash` — where a deleted book goes | [library.py](../app/studio/library.py) `_delete()` |
| Переглядач (лайтбокс) | The full-screen zoomable viewer | [lightbox.js](../app/web/js/lightbox.js) `openLightbox()` |

## Listing mockups (the «Мокапи» utility, built 2026-09-23)

| Owner's word (Ukrainian) | What it is | Where |
|---|---|---|
| Мокапи, мокапи для лістингу | Etsy listing pictures: the demo book dropped into Photoshop templates; also the utility's shortcut name | [features/mockups.md](features/mockups.md) `mockups.py`; [plans/listing-mockups.md](plans/listing-mockups.md) |
| Трафарети (мастхев), шаблони мокапів | The PSD templates in `D:\Roman\Desktop\Трафарети мастхев` — **read-only** | [plans/listing-mockups.md](plans/listing-mockups.md); [security.md](security.md) |
| Смарт-об'єкт | A layer that's a "container": the picture inside is bent by the template | [plans/listing-mockups.md](plans/listing-mockups.md) |
| Папка Main | Hidden linked copies of the layers to fill, at the bottom of templates 1–4 | [plans/listing-mockups.md](plans/listing-mockups.md) |
| Ковер, обкладинка (у мокапі) | The front cover — the owner fits it by hand (`COVER_` / `Cover` / `Front Cover`) | [plans/listing-mockups.md](plans/listing-mockups.md) |
| Корінець | The spine: the middle strip of the wide cover (`Rige` / `Spine`, files `RIDGE*.psb`) | [mockups.py](../app/studio/mockups.py) `cover_pictures()` |
| Задня частина (обкладинки) | The back cover — the left half of the wide cover (`Back Cover`) | [mockups.py](../app/studio/mockups.py) `cover_pictures()` |
| Презентабельні розвороти | The spreads the owner picks for the mockups, different for every book | [pages/mockups.js](../app/web/js/pages/mockups.js) `put()`; [features/mockups.md](features/mockups.md) |
| Опен 1, Опен 2 (копії) | Templates `2. Open 1` (used 4 times) and `3. Open 2` (twice), each time with another spread | [plans/listing-mockups.md](plans/listing-mockups.md) |
| Демо-книга, архів з Канви (для мокапів) | The Canva ZIP of a book with a sample name on the cover and `{Name}` in the pages | [mockups.py](../app/studio/mockups.py) `read_book()` |
| Кант (у мокапі) | The thin rim of the cover around the pages of an open book — filled from the cover by the script | [mockups.py](../app/studio/mockups.py) `plan()` |
| Драг енд дроп зона з пошуком (як у Бук Студіо) | The path field with the folder-and-magnifier button (`folderPick`) that lights up when files are dragged over the window — the look «Мокапи» took from the Order Creator | [pages/mockups.js](../app/web/js/pages/mockups.js) `paintBook()`; [features/mockups.md](features/mockups.md) |
| Зберегти відкриті (й закрити) | The button after a run: the templates left open, with the front cover fitted, saved as PNG next to the rest and closed | [mockups.py](../app/studio/mockups.py) `finish()`; [mockups.jsx](../app/studio/mockups.jsx) `finishOpen()` |
| Тимчасові файли, «чистити за собою» | What a run leaves (template copies, prepared pictures, the unpacked book) and when it goes | [features/mockups.md](features/mockups.md#temporary-files--what-is-left-and-when-it-goes) |

## The program in general

| Owner's word (Ukrainian) | What it is | Where in the code |
|---|---|---|
| Бокова панель, піктограми зліва | Navigation | [app.js](../app/web/js/app.js) `NAV`, `buildSidebar()` |
| Тримати диск C в чистоті | No temp files of the programs on drive C: their own temp folder on D, emptied on launch and close | [core.py](../app/studio/core.py) `own_temp()`; [runtime](architecture/runtime.md#temporary-files-and-drive-c) |
| Панель інструментів (пошук, сортування, «+») | `.lib-toolbar` | [library.js](../app/web/js/pages/library.js) `mount()`; [app.css](../app/web/css/app.css) |
| Підказка при наведенні | The shared tooltip | [lib.js](../app/web/js/lib.js) `showTip()`, `ib()` |
| Тема (темна/світла) | The menu at the bottom of the panel | [app.js](../app/web/js/app.js) `applyTheme()`, `openThemeMenu()` |
| Ключі, сховище | The encrypted service keys | [vault.py](../app/studio/vault.py) `Vault`; [settings.js](../app/web/js/pages/settings.js) `secretField()` |
| Лінк доступу (з Profit Calculator) | A `?sync=` link carrying an Etsy session | [etsy.py](../app/studio/etsy.py) `decode_session_key()` |
| Київський ПК / вроцлавський ПК | Where Etsy may be opened | [security.md](security.md) |
| Прибуток | The hidden accounting page | [profit.js](../app/web/js/pages/profit.js) `mount()` |
| Зіставлення | Finding the print order for an Etsy receipt | [reconcile.py](../app/studio/reconcile.py) `match()` |
| Скасування, повернення, заміна | Order states in the accounting | [outcomes.py](../app/studio/outcomes.py) `STATES` |

## Related

- [Code map](code-map.md) · [Overview](overview.md)
