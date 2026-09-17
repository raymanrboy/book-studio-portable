---
title: Словник — слова власника і назви в коді
type: reference
updated: 2026-09-17
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
| Нові / В роботі / Відправлені | Етапи замовлення (`new` / `work` / `shipped`) | [profit.py](../app/studio/profit.py) `order_stage()`; [order-bits.js](../app/web/js/order-bits.js) `STAGES` |
| Оновити замовлення, синхронізація | Завантаження замовлень Etsy + Printify + Gelato | [profit.py](../app/studio/profit.py) `_sync()`, `startup_sync()`; [order-bits.js](../app/web/js/order-bits.js) `syncOrders()` |
| Друкарня, постачальник | Printify або Gelato | [orders.py](../app/studio/orders.py) `plan_for()` |
| Правило друкарні | Hardcover у США → Printify, решта → Gelato | [rules/printer-rule.md](rules/printer-rule.md) |
| Персоналізація, поля Etsy | Варіації покупця (назва: значення) | [profit.py](../app/studio/profit.py) `normalize_receipt()`; [orders.js](../app/web/js/pages/orders.js) `renderLeft()` |
| Ім'я дитини | Значення поля з «name/child…» у назві | [creator.py](../app/studio/creator.py) `guess_child_name()` |
| «Від кого» | Назва поля в лістингу Etsy; показується як є | [orders.js](../app/web/js/pages/orders.js) `renderLeft()` |
| Свій текст (присвята не DEFAULT) | Позначка «свій текст» біля поля | [orders.js](../app/web/js/pages/orders.js) `isCustomText()` |
| Формат обкладинки (Cover Type & Size) | Поле, що вирішує друкарню; без кнопки копіювання і без рядка в записці | [orders.js](../app/web/js/pages/orders.js) `isFormatField()` |
| Повідомлення покупця | `message_from_buyer` з чека Etsy | [orders.py](../app/studio/orders.py) `_one()` |
| Файли з Canva, розставити сторінки | ZIP/папка з Canva → `Cover.png` + `1…N.png` | [orders.py](../app/studio/orders.py) `arrange_pages()` |
| Звірка | Крок 2 картки: обкладинка, перший розворот, стрічка | [orders.js](../app/web/js/pages/orders.js) `proofCard()` |
| Записка (на форзаці) | Ліва половина першого розвороту звірки: ім'я і поля покупця | [orders.js](../app/web/js/pages/orders.js) `proofCard()`; CSS `.proof-note` в [app.css](../app/web/css/app.css) |
| Стрічка, слайдер сторінок | Горизонтальний ряд усіх розворотів у звірці | [orders.js](../app/web/js/pages/orders.js) `proofCard()`; [order-bits.js](../app/web/js/order-bits.js) `smoothWheel()` |
| До друку | Передача замовлення в Order Creator | [orders.js](../app/web/js/pages/orders.js) `print()`; [handoff.js](../app/web/js/handoff.js) `give()` |
| Order Creator | Сторінка створення книги/чернетки | [creator.js](../app/web/js/pages/creator.js) `mount()`; [creator.py](../app/studio/creator.py) |
| Чернетка Gelato | Замовлення Gelato з `orderType: draft` | [creator.py](../app/studio/creator.py) `create_gelato_draft()` |
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
| Архів | Книга прихована з робочого списку | [library.py](../app/studio/library.py) `_archive()` |
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
