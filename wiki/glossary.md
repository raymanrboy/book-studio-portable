---
title: Словник — слова власника і назви в коді
type: reference
updated: 2026-09-20
code: []
---
# Словник

> Власник описує програму своїми словами. Тут кожне таке слово зведено з місцем у коді.
> Якщо власник назвав щось, чого тут немає, — знайдіть це в коді й допишіть рядок.

Шляхи коду нижче — від кореня репозиторію.

## Замовлення і друк

| Слово власника | Що це | Де в коді |
|---|---|---|
| Замовлення (сторінка), черга | Перший екран: список замовлень Etsy за етапами | [orders.js](../app/web/js/pages/orders.js) `mountQueue()` |
| Картка замовлення | Один екран на одне замовлення | [orders.js](../app/web/js/pages/orders.js) `mountCard()` |
| Нові / В роботі / машинка / Відправлені | Етапи замовлення (`new` / `work` / `sent` / `shipped`) | [profit.py](../app/studio/profit.py) `order_stage()`; [order-bits.js](../app/web/js/order-bits.js) `STAGES` |
| Машинка (вкладка) | Етап `sent`: друкарня вже відправила (трек-номер або статус «відправлено»), а в Etsy ще не позначено | [profit.py](../app/studio/profit.py) `order_stage()`; [order-bits.js](../app/web/js/order-bits.js) `STAGES`; [rules/order-stages.md](rules/order-stages.md) |
| Замовлення на кілька книг, «Книга 1 / Книга 2» | Один чек Etsy з кількома книгами: у картці кожна має свою папку, звірку й перевірку тексту, а в друк вони йдуть однією чернеткою на одну адресу | [orders.js](../app/web/js/pages/orders.js) `readyBooks()`, `printCard()`; [creator.py](../app/studio/creator.py) `books_of()`, `joint_title()`; [features/orders.md](features/orders.md) |
| Швидкий огляд сторінок, пред-перевірка | Програма сама дивиться на прев'ю кожної сторінки й визначає, де взагалі є текст: моделі показуються лише такі сторінки | [images.py](../app/studio/images.py) `text_score()`; [textcheck.py](../app/studio/textcheck.py) `page_kinds()`; [features/text-check.md](features/text-check.md) |
| Замінити сторінку | Кнопка в переглядачі: сторінка, виправлена в Canva й скачана окремо, стає на місце старої; поруч «Повернути» | [creator.py](../app/studio/creator.py) `replace_page()`; [orders.js](../app/web/js/pages/orders.js) `replacePage()`; [features/orders.md](features/orders.md) |
| Бокс, коробка (вкладка) | «Відправлені» — позначені відправленими в Etsy | [profit.py](../app/studio/profit.py) `order_stage()` |
| Годинник (вкладка) | «В роботі» | [order-bits.js](../app/web/js/order-bits.js) `STAGES` |
| Квадратик справа (у рядку черги), статус | Чип праворуч: статус друкарні англійською, по-людськи («In transit»), з кольоровою крапкою | [order-bits.js](../app/web/js/order-bits.js) `statusChip()`, `statusText()`; [profit.py](../app/studio/profit.py) `picker_orders()` (`printStatus`) |
| Трек-номер, перевізник (USPS…) | Чип після чипа друкарні: перевізник \| номер; клік копіює номер | [order-bits.js](../app/web/js/order-bits.js) `trackChips()`, `copyChip()`; [printify.py](../app/studio/printify.py) `slim_order()`; [gelato.py](../app/studio/gelato.py) `attach_shipments()` |
| Останній стан, «повертає, де я був» | Картка нового замовлення й Order Creator з ним зберігаються при переході на іншу вкладку | [keep.js](../app/web/js/keep.js); [app.js](../app/web/js/app.js) `navigate()`; [architecture/frontend.md](architecture/frontend.md) |
| Номер замовлення Etsy, номер чека | `#…` у черзі й шапці картки; клік копіює цифри без «#» | [order-bits.js](../app/web/js/order-bits.js) `receiptCopy()`, `copyChip()` |
| Оновити замовлення, синхронізація | Завантаження замовлень Etsy + Printify + Gelato | [profit.py](../app/studio/profit.py) `_sync()`, `startup_sync()`; [order-bits.js](../app/web/js/order-bits.js) `syncOrders()` |
| Друкарня, постачальник | Printify або Gelato | [orders.py](../app/studio/orders.py) `plan_for()` |
| Правило друкарні | Hardcover у США → Printify, решта → Gelato | [rules/printer-rule.md](rules/printer-rule.md) |
| Персоналізація, поля Etsy | Варіації покупця (назва: значення) | [profit.py](../app/studio/profit.py) `normalize_receipt()`; [orders.js](../app/web/js/pages/orders.js) `renderLeft()` |
| Ім'я дитини | Значення поля з «name/child…» у назві | [creator.py](../app/studio/creator.py) `guess_child_name()` |
| «Від кого» | Назва поля в лістингу Etsy; показується як є | [orders.js](../app/web/js/pages/orders.js) `renderLeft()` |
| Свій текст (присвята не DEFAULT) | Позначка «свій текст» біля поля | [order-bits.js](../app/web/js/order-bits.js) `isCustomText()` |
| Формат обкладинки (Cover Type & Size) | Поле, що вирішує друкарню; без кнопки копіювання і без рядка в записці | [order-bits.js](../app/web/js/order-bits.js) `isFormatField()` |
| Повідомлення покупця | `message_from_buyer` з чека Etsy | [orders.py](../app/studio/orders.py) `_one()` |
| Файли з Canva, розставити сторінки | ZIP/папка з Canva → `Cover.png` + `1…N.png` | [orders.py](../app/studio/orders.py) `arrange_pages()` |
| Звірка | Крок 2 картки: обкладинка, перший розворот, стрічка | [orders.js](../app/web/js/pages/orders.js) `proofCard()` |
| Записка (на форзаці) | Ліва половина першого розвороту звірки: ім'я і поля покупця | [orders.js](../app/web/js/pages/orders.js) `proofCard()`; CSS `.proof-note` в [app.css](../app/web/css/app.css) |
| Стрічка, слайдер сторінок | Горизонтальний ряд усіх розворотів у звірці | [orders.js](../app/web/js/pages/orders.js) `proofCard()`; [order-bits.js](../app/web/js/order-bits.js) `smoothWheel()` |
| До друку | Передача замовлення в Order Creator | [orders.js](../app/web/js/pages/orders.js) `print()`; [handoff.js](../app/web/js/handoff.js) `give()` |
| Order Creator | Сторінка створення книги/чернетки | [creator.js](../app/web/js/pages/creator.js) `mount()`; [creator.py](../app/studio/creator.py) |
| Чернетка Gelato | Замовлення Gelato з `orderType: draft` | [creator.py](../app/studio/creator.py) `create_gelato_draft()` |
| Логи відправки, журнал відправок | JSON про кожну відправку в Printify/Gelato (`data/logs/sends/`) | [sendlog.py](../app/studio/sendlog.py); [features/send-journal.md](features/send-journal.md) |
| Page 0 (у чернетці Gelato) | Порожній форзац — так і має бути | [integrations/gelato.md](integrations/gelato.md) |
| 28-сторінкова / 30-сторінкова книга (Gelato) | Скільки сторінок скачано з Canva (28 — без одного розвороту); окремого перемикача немає | [creator.py](../app/studio/creator.py) `gelato_page_options()`, `gelato_pages_problem()`; [integrations/gelato.md](integrations/gelato.md) |
| Чернетка замовлення Printify, «On hold» | Книга + замовлення, що чекає «Submit order» | [creator.py](../app/studio/creator.py) `create_printify_draft()`; [printify.py](../app/studio/printify.py) `create_order_on_hold()` |
| Книга без замовлення (Printify) | Лише неопублікований продукт, адреса порожня | [creator.py](../app/studio/creator.py) `create_printify_draft()` |
| Master, шаблон Printify | Еталонний продукт, з якого копіюється конфігурація | [creator.py](../app/studio/creator.py) `build_printify_payload()`; [settings.js](../app/web/js/pages/settings.js) `pickMaster()` |
| Ручне затвердження (Manual) | Налаштування магазину Printify; програма питає один раз | [printify.py](../app/studio/printify.py) `manual_approval_confirmed()`; [creator.js](../app/web/js/pages/creator.js) `confirmManualApproval()` |
| Матовий фініш | Варіант Master із «Matte» у назві | [creator.py](../app/studio/creator.py) `matte_variant()` |
| Тимчасове посилання (для Gelato) | Cloudflare-тунель на один PDF | [tunnel.py](../app/studio/tunnel.py) `FileTunnel` |
| Перетягнути папку або ZIP | Копіювання в програму і розпакування | [order-bits.js](../app/web/js/order-bits.js) `receiveDrop()`; [creator.py](../app/studio/creator.py) `extract_zip()` |
| Очистити адресу (гумка) | Іконка в блоці адреси | [creator.js](../app/web/js/pages/creator.js) `addressCard()` |
| Заповнити із замовлення Etsy | Вибір замовлення в Order Creator | [creator.js](../app/web/js/pages/creator.js) `fromEtsy()` |

## Книга і бібліотека

| Слово власника | Що це | Де в коді |
|---|---|---|
| Бібліотека | Галерея еталонних книг | [library.js](../app/web/js/pages/library.js) `mount()`; [library.py](../app/studio/library.py) |
| Паспорт книги | Сторінка однієї книги | [book.js](../app/web/js/pages/book.js) `mount()` |
| Обкладинка | Повний розворот обкладинки (`cover`, `Cover.png`) | [library.py](../app/studio/library.py) `SLOT_KEYS` (окремо від слотів) |
| Заставка | Картинка книги в галереї (`thumbnail`) | [library.py](../app/studio/library.py) `summary()` |
| Присвята | Сторінка 1 (`page1`) | [library.py](../app/studio/library.py) `slot_label()` |
| Розворот N | Сторінки 2N−2 і 2N−1 (`spread2`…`spread15`) | [library.py](../app/studio/library.py) `spread_pages()` |
| Післяслово | Сторінка 30 (`page30`) | [library.py](../app/studio/library.py) `slot_label()` |
| Форзац / нахзац | Порожні сторінки біля обкладинки (у друці) | [order-bits.js](../app/web/js/order-bits.js) `spreadsOf()` |
| Текст книги, `book-text.json` | Тексти обкладинки, присвяти, розворотів, післяслова | [library.py](../app/studio/library.py) `parse_text_json()` |
| `{Name}`, `{Gifter}` | Плейсхолдери імені дитини і дарувальника | [lib.js](../app/web/js/lib.js) `highlightTokens()` |
| Інструкція для агента | Файл про назви файлів і формат JSON | [library.py](../app/studio/library.py) `agent_guide()`; [library.js](../app/web/js/pages/library.js) `saveGuide()` |
| Імпорт з папки | Розкладання файлів папки по слотах | [library.py](../app/studio/library.py) `scan_folder()` |
| Апскейл, Upscayl | Хвіст `_upscayl…` у назвах файлів ігнорується | [library.py](../app/studio/library.py) `scan_folder()`; [orders.py](../app/studio/orders.py) `page_number()` |
| Архів (у бібліотеці) | Книга прихована з робочого списку | [library.py](../app/studio/library.py) `_archive()` |
| Архів замовлень | Окреме меню з файлами книг, що пішли в друк (14 днів після «Відправлених»), і передруком | [archive.py](../app/studio/archive.py); [archive.js](../app/web/js/pages/archive.js); [features/archive.md](features/archive.md) |
| Передрук, редрук | Повторний друк тієї самої книги з архіву замовлень: Printify — нове замовлення на ту саму книгу, Gelato — нова чернетка | [creator.py](../app/studio/creator.py) `create_printify_reprint()`; [features/archive.md](features/archive.md) |
| Не видаляти (у архіві) | Шпилька на книзі в архіві: файли лишаються, доки позначку не знято | [archive.py](../app/studio/archive.py) `_keep()` |
| Оформлене замовлення (в друкарні) | Підтверджене й оплачене, не чернетка, не «on hold», не скасоване; лише воно переводить замовлення «в роботу» і кладе книгу в архів | [profit.py](../app/studio/profit.py) `is_placed()`; [rules/order-stages.md](rules/order-stages.md) |
| Завершити роботу над замовленням | Хрестик у картці замовлення й в Order Creator після вдалої відправки: програма забуває збережену роботу над цим замовленням і відкриває чергу | [keep.js](../app/web/js/keep.js) `finish()`; [features/orders.md](features/orders.md) |
| Вигаданий номер (телефон) | Телефон, який підставляється в Gelato, коли в замовленні Etsy його немає: `+1 555 555 0100` | [creator.py](../app/studio/creator.py) `GELATO_PLACEHOLDER_PHONE` |
| ШІ-валідатор, перевірка тексту, «кнопка перевірити» | Локальна модель читає сторінки в картці замовлення, програма звіряє з паспортом книги | [textcheck.py](../app/studio/textcheck.py) `check_order()`; [orders.js](../app/web/js/pages/orders.js) `startCheck()`; [features/text-check.md](features/text-check.md) |
| Gemma, локальна модель, Ollama | `gemma4:12b-it-qat` в Ollama на відеокарті цього ПК | [textcheck.py](../app/studio/textcheck.py) `DEFAULT_MODEL`, `status()`, `start_ollama()` |
| Сліпе переписування / з підказкою | Прохід «читання» (модель не знає, що мало бути) і «звірки» (знає) | [textcheck.py](../app/studio/textcheck.py) `READ_PROMPT`, `STRICT_PROMPT` |
| Паспорт застарів, оновити паспорт | Тексти паспорта не збігаються з шаблоном Canva — беруться з надрукованої книги | [orders.js](../app/web/js/pages/orders.js) `learnPassport()`; [textcheck.py](../app/studio/textcheck.py) `_passport()` |
| Взяти файли минулої відправки | Кнопка в картці замовлення: файли відправки, що не стала замовленням (скасовано, чернетку видалено), беруться з архіву — і замовлення відправляється як звичайне | [orders.js](../app/web/js/pages/orders.js) `takeEarlier()`; [features/archive.md](features/archive.md) |
| Кошик | `data/library/trash` — куди йде видалена книга | [library.py](../app/studio/library.py) `_delete()` |
| Переглядач (лайтбокс) | Повноекранний перегляд із зумом | [lightbox.js](../app/web/js/lightbox.js) `openLightbox()` |

## Програма загалом

| Слово власника | Що це | Де в коді |
|---|---|---|
| Бокова панель, піктограми зліва | Навігація | [app.js](../app/web/js/app.js) `NAV`, `buildSidebar()` |
| Панель інструментів (пошук, сортування, «+») | `.lib-toolbar` | [library.js](../app/web/js/pages/library.js) `mount()`; [app.css](../app/web/css/app.css) |
| Підказка при наведенні | Спільна підказка | [lib.js](../app/web/js/lib.js) `showTip()`, `ib()` |
| Тема (темна/світла) | Меню внизу панелі | [app.js](../app/web/js/app.js) `applyTheme()`, `openThemeMenu()` |
| Ключі, сховище | Зашифровані ключі сервісів | [vault.py](../app/studio/vault.py) `Vault`; [settings.js](../app/web/js/pages/settings.js) `secretField()` |
| Лінк доступу (з Profit Calculator) | Посилання `?sync=` із сесією Etsy | [etsy.py](../app/studio/etsy.py) `decode_session_key()` |
| Київський ПК / вроцлавський ПК | Де можна відкривати Etsy | [security.md](security.md) |
| Прибуток | Прихована сторінка обліку | [profit.js](../app/web/js/pages/profit.js) `mount()` |
| Зіставлення | Пошук замовлення друку для чека Etsy | [reconcile.py](../app/studio/reconcile.py) `match()` |
| Скасування, повернення, заміна | Стани замовлення в обліку | [outcomes.py](../app/studio/outcomes.py) `STATES` |

## Пов'язане

- [Карта коду](code-map.md) · [Огляд](overview.md)
