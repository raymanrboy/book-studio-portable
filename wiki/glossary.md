---
title: Glossary — the owner's words
type: reference
updated: 2026-11-12
code: []
---
# Glossary

> The owner describes the program in his own words (Ukrainian). Each word leads to the page that explains it; the page leads to the code. A word not listed: find the Ukrainian label in `app/web/js` and add a line.

## Orders and printing
- **Замовлення, черга** — the start screen: Etsy orders by stage → [Orders](features/orders.md)
- **Нові / В роботі / Машинка / Відправлені** — the four stage tabs; «Машинка» = the printer shipped it, Etsy not yet marked → [Order stages](rules/order-stages.md)
- **Позначити в Etsy** — the «Машинка» list: tracking numbers copied, the owner marks them shipped in Etsy → [Orders](features/orders.md)
- **Картка замовлення** — one screen for one order → [Orders](features/orders.md)
- **Замовлення на кілька книг, «Книга 1 / Книга 2»** — one receipt, several books, one draft to one address → [Orders](features/orders.md), [Order Creator](features/order-creator.md)
- **Квадратик справа (статус), трек-номер** — the printer's status chip and the tracking chip in a queue row → [Orders](features/orders.md)
- **«+N у друці»** — the receipt has N more print orders than the one shown → [Order stages](rules/order-stages.md)
- **Останній стан, «повертає, де я був»** — a new order's card and Order Creator work are kept across tab switches → [Frontend](architecture/frontend.md)
- **Оновити замовлення, синхронізація** — loading orders from Etsy, Gelato and Printify → [Refresh policy](rules/sync-policy.md)
- **Друкарня, правило друкарні** — Gelato prints every new book; which format a book gets → [Gelato](integrations/gelato.md)
- **Старий акаунт Gelato (лише читання)** — a second saved key that is only read → [Gelato](integrations/gelato.md)
- **Printify** — read-only; what a copy with the date unset can still do → [Printify](integrations/printify.md)
- **Оформлене замовлення** — placed and paid at the printer (not draft, not cancelled); only this moves an order to «В роботі» → [Order stages](rules/order-stages.md)
- **Передрук, редрук** — printing the same book again from the card or the archive → [Print archive](features/archive.md), [Order stages](rules/order-stages.md)
- **Звірка, зіставлення** — card step 2 (cover, first spread, filmstrip); and finding a receipt's print order → [Order to print](flows/order-to-print.md), [Matching](rules/reconciliation.md)
- **До друку** — handing the order to the Order Creator → [Order Creator](features/order-creator.md)
- **Файли з Canva, розставити сторінки** — a ZIP or folder becomes `Cover.png` + `1…N.png` → [Intake](flows/intake.md), [Book files](rules/book-files.md)
- **Перетягнути папку або ZIP** — dropping into the program; «Куди?» asks where → [Intake](flows/intake.md)
- **Замінити сторінку** — a page fixed in Canva replaces the page in the order; «Скасувати» next to it → [Order Creator](features/order-creator.md)
- **28- / 30-сторінкова книга** — how many pages came from Canva → [Book files](rules/book-files.md), [Gelato](integrations/gelato.md)
- **Order Creator, Чернетка Gelato** — the tool that makes the Gelato draft → [Order Creator](features/order-creator.md)
- **Логи відправки, журнал відправок** — one JSON per send, add-only → [Order Creator](features/order-creator.md)
- **Тимчасове посилання (для Gelato)** — a Cloudflare tunnel to one PDF → [Gelato](integrations/gelato.md)
- **Завершити роботу над замовленням (✓)** — closes the card and the Order Creator after a send → [Order Creator](features/order-creator.md)
- **Бугалтерія, облік, «Прибуток»** — the Profit page, sales from 1 October 2026 → [Profit](features/profit.md)
- **Скасування, повернення, заміна** — order states in the accounting → [Matching](rules/reconciliation.md)
- **Персоналізація, поля Etsy, «Від кого», Ім'я дитини** — the buyer's variations shown in the card → [Orders](features/orders.md)
- **Формат обкладинки (Cover Type & Size)** — the variation that decides the product → [Gelato](integrations/gelato.md)

## Text check
- **ШІ-валідатор, перевірка тексту, «кнопка перевірити»** — a local model reads the pages and the program compares them with the passport → [Text check](features/text-check.md)
- **Gemma, локальна модель, Ollama** — the model on this PC → [Text check](features/text-check.md), [Modules](features/modules.md)
- **Сліпе переписування / з підказкою** — the "read" pass and the "check" pass → [Text check](features/text-check.md)
- **Швидкий огляд сторінок, пред-перевірка** — the program finds the pages that have text; only those go to the model → [Text check](features/text-check.md)
- **Не та книга, «захист від дурня»** — pages laid out from another book's template: a red banner → [Text check](features/text-check.md)
- **Паспорт застарів, оновити паспорт** — the passport texts differ from the template → [Text check](features/text-check.md)

## Books and the library
- **Книги** — the rail place with «Майстерня · Бібліотека · Архів» → [Rail](features/rail.md)
- **Бібліотека, Паспорт книги** — the reference books and one book's page → [Library](features/library.md)
- **Обкладинка / Заставка / Присвята / Розворот N / Післяслово** — the library slots (`cover`, `thumbnail`, page 1, spreads, page 30) → [Library](features/library.md), [Book files](rules/book-files.md)
- **Форзац / нахзац** — blank pages added in the print PDF → [Gelato](integrations/gelato.md)
- **Текст книги, `{Name}`, `{Gifter}`** — the texts and the placeholders → [Library](features/library.md)
- **Інструкція для агента, Імпорт з папки** — the file-name guide and laying a folder into slots → [Intake](flows/intake.md), [Book files](rules/book-files.md)
- **Кошик** — where a deleted library book goes → [Data safety](architecture/data-safety.md)
- **Архів друку, не видаляти** — files of printed books, kept for the retention days unless pinned → [Print archive](features/archive.md)
- **Апскейл, Upscayl** — enlarging a picture ×2 → [Workshop](features/workshop.md), [Modules](features/modules.md)

## Workshop and covers
- **Майстерня, книги в розробці** — where a new book is made → [Workshop](features/workshop.md)
- **Пайплайн, агенти 0–6, GO, перевірка книги** — the `book` skill's steps and the book check → [Workshop](features/workshop.md), [Workshop books](owner/workshop-books.md)
- **Смуга шляху, «Далі: …»** — the book's step strip → [Workshop](features/workshop.md)
- **Генерувати, Далі / F8** — the prompt goes to the clipboard and the download is caught → [Workshop](features/workshop.md)
- **Промпт, плейсхолдер (рамка 2:1)** — the picture's description and its empty frame → [Workshop](features/workshop.md)
- **Схема, поля обкладинки, аутпейнт** — the cover's layout guide and its second stage → [Cover tool](features/cover.md)
- **Варіанти героя (G2, G3…)** — a Tier H book's hero looks → [Workshop](features/workshop.md)
- **Фліпер, нарізати на квадрати** — mirroring a spread; cutting a 2:1 spread into two pages → [Workshop](features/workshop.md)
- **Передати в бібліотеку** — a library book made from a Workshop book → [Workshop](features/workshop.md), [Library](features/library.md)
- **Розширення для Canva, «Книга → Canva», «Розкласти», бімба** — the Chrome extension and the sphere under the text → [Canva extension](features/canva-extension.md)

## Listing pictures
- **Мокапи, Фотошоп модуль** — the Mockups tool → [Mockups](features/mockups.md)
- **Трафарети, шаблони мокапів, смарт-об'єкт, папка Main, кант** — the templates and their layers → [Mockups engine](features/mockups-engine.md)
- **Без фотошопу, «запечений» шаблон** — mockups drawn by the program → [Mockups engine](features/mockups-engine.md)
- **Міні-редактор для кадрування** — the crop window → [Mockups](features/mockups.md)
- **Опен 1, Опен 2, демо-книга, презентабельні розвороти** — templates and the picked spreads → [Mockups](features/mockups.md)
- **Без фону** — the book with its shadow on a transparent background → [Mockups engine](features/mockups-engine.md)
- **Зберегти відкриті** — save and close the templates left open → [Mockups](features/mockups.md)
- **Фотомокапи, заготовки, пустишка, ковер, Для відео, Omni, папка etsy** — lifestyle photos and videos of the book → [Photo mockups](features/photo-mockups.md)
- **Слайди, запекти, схема, пресет, редактор** — the six listing pictures and their editor → [Listing slides](features/slides.md)
- **SEO, теги, назва і опис лістингу, eRank, База SEO** — the listing text and keyword tools → [Etsy SEO](features/seo.md)

## The program
- **Бокова панель, Інструменти** — the rail, places and tools → [Rail](features/rail.md)
- **Шлях (замовлення, книги)** — the path strip of an order or a book → [Rail](features/rail.md)
- **Скасувати (toast)** — undo on a notice, offered only when it really restores → [Data safety](architecture/data-safety.md), [UI principles](owner/ui-principles.md)
- **Анімації (мінімум), підказка, панель інструментів** — motion setting, tooltips, list toolbars → [UI principles](owner/ui-principles.md), [Frontend](architecture/frontend.md)
- **Ключі, сховище** — the encrypted service keys → [Settings](features/settings.md), [Security](security.md)
- **Модулі, розумна вичитка** — optional heavy parts (text check, upscaling) → [Modules](features/modules.md)
- **Перенесення налаштувань** — one file with settings and keys for another computer → [Settings](features/settings.md)
- **Резервна копія** — the Google Drive backup → [Backup](features/backup.md)
- **Київський ПК, вроцлавський ПК** — where Etsy may be signed in to, and where the program runs → [Etsy](integrations/etsy.md), [Working with the owner](owner/working-with-owner.md)
