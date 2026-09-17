---
title: Замовлення — черга і картка замовлення
type: feature
updated: 2026-09-17
code:
  - app/studio/orders.py
  - app/web/js/pages/orders.js
  - app/web/js/order-bits.js
  - app/web/js/handoff.js
---
# Замовлення

> Стартовий екран. Черга замовлень Etsy за етапами і картка, яка проводить одне замовлення шляхом
> *книга і Canva → файли → звірка → друк*. Нічого не зберігає: усе виводиться зі знімка синхронізації
> і бібліотеки. Покроково — [flows/order-to-print.md](../flows/order-to-print.md).

## Черга (`#/orders`)

- Панель: пошук (ім'я покупця або номер чека; Enter відкриває перше), перемикач етапів
  **Нові / В роботі / Відправлені** з лічильниками, кнопка «Оновити замовлення».
- Рядок: обкладинка книги з бібліотеки, ім'я покупця, `#номер чека`, кількість книг (якщо > 1),
  чип друкарні (для «Нових» — за правилом, з поясненням у підказці; для «В роботі» — де вже замовлено;
  «друкарня?» — якщо тип обкладинки не прочитався), час, назва книги або «книги немає в бібліотеці»,
  місто й країна, ім'я дитини.
- Оновлення: сторінка сама **не** синхронізує. Якщо відкрити її під час синхронізації після запуску,
  вона дочекається її (`runningSync()` → `watchSync()`). Кнопка запускає нову (`syncOrders()`).
- Після оновлення рядки, що змістилися, на 0,45 с не клікаються (`inert`) — щоб клік не влучив
  в іншого покупця.
- Етапи рахує сервер — [rules/order-stages.md](../rules/order-stages.md).
- *Задумано (17.09.2026, ще не зроблено):* четверта вкладка з машинкою (друкарня відправила, в Etsy
  ще не позначено), статус друкарні (англійською, як є) замість імені дитини праворуч, ім'я — жирно в сірому рядку після часу, чип трек-номера з
  перевізником (клік — копіювати). Деталі — [plans/roadmap.md](../plans/roadmap.md).

## Картка (`#/orders/<номер чека>`)

Шапка: ім'я покупця, номер чека, час, етап; праворуч чип «Printify · 24 стор.» / «Gelato · 28 або 30 стор.»
(після розстановки файлів — точне число, напр. «Gelato · 28 стор.») або, якщо тип обкладинки невідомий,
перемикач друкарні (варіанти сторінок — `pageOptions` замовлення). Для «В роботі»/«Відправлених» — попередження
«друкуйте ще раз лише для передруку». Esc — назад до черги.

**Розкладка** (з 16.09.2026, за проханням власника): ліворуч — робота, праворуч — дані; права колонка
«липка» (лишається на екрані, коли гортаєш звірку). На вузькому вікні (< 1100 px) — одна колонка.

### Праворуч — дані (`#oc-data`, `renderLeft()`)
- **Книга**: обкладинка й назва з бібліотеки (посилання на паспорт), кнопка «Відкрити шаблон у Canva».
  Немає посилання на Canva → «Додати посилання на Canva» (у паспорт); немає книги → «До бібліотеки».
- **Персоналізація**: усі поля рівно так, як їх повертає Etsy (`dl.ord-fields`), значення жирні,
  біля кожного — копіювання. Поле з ім'ям дитини — більшим (`.is-name`). Поле формату обкладинки
  (`isFormatField()`) — без копіювання: воно лише вибирає друкарню. Присвята не `DEFAULT` →
  позначка «свій текст» (`isCustomText()`). Кілька книг у замовленні → перемикач «Книга 1 / Книга 2»,
  кожна проходить шлях окремо.
- **Повідомлення покупця**, якщо є.
- **Доставка**: адреса з Etsy.

### Ліворуч — робота (`#oc-flow`, `renderRight()`)
1. **Файли з Canva** (`filesCard()`): перетягнути ZIP/папку або обрати папку. Сервер розставляє сторінки
   (`arrange_pages()`: обкладинка + 24 сторінки для Printify, 28 або 30 для Gelato — скільки скачано,
   див. [rules/file-naming.md](../rules/file-naming.md)), показує, що перейменував («сторінки 2–25 → 1–24»),
   далі — повна перевірка, як в Order Creator. Для Gelato сервер одразу питає каталог, чи друкує він
   стільки сторінок у форматі замовлення; ні → помилка в цьому ж блоці
   ([integrations/gelato.md](../integrations/gelato.md)).
2. **Звірка** (`proofCard()`, з'являється після успішної перевірки; сторінка сама прокручується до неї):
   - обкладинка на всю ширину;
   - під нею перший розворот на всю ширину: ліва (у друці порожня) половина — **записка**: ім'я дитини
     великим (`.proof-name`) і поля покупця жирно, розміри масштабуються з розворотом (одиниці `cqw`);
     формату обкладинки й поля з іменем у записці немає; права половина — справжня сторінка 1;
   - **стрічка** всіх розворотів (`#oc-strip`): колесо миші гортає її плавно (`smoothWheel()`,
     без «примагнічування»), до останнього розвороту; мініатюри 360 px сервер готує заздалегідь
     (`STRIP_THUMB` = `STRIP_PREVIEW`);
   - клік по будь-чому — переглядач розворотами (`folderViewerItems()`).
3. **Друк** (`printCard()`): «До друку в Printify/Gelato» → Order Creator, заповнений назвою
   `номер чека - ім'я`, адресою, форматом і файлами (`print()` → `give('creator', …)`).
   Картка Printify — у салатовому акценті.

## Що віддає сервер

- `GET /api/orders` → `{orders, syncedAt}`; кожне замовлення з `picker_orders()`, доповнене
  `enrich()`: для кожної книги `book` (з бібліотеки за номером лістингу), `plan` (правило друкарні;
  `plan.pages` — список дозволених довжин: `[24]` або `[28, 30]`), `childName`; для замовлення —
  `pageOptions` (довжини для кожної друкарні, коли її обирають вручну).
- `GET /api/orders/<чек>` → те саме для одного + `buyerMessage`.
- `POST /api/orders/<чек>/files` `{folder, provider, format}` → `{path, note, renumbered, pageCount}`.

## Де в коді

- [app/web/js/pages/orders.js](../../app/web/js/pages/orders.js) — `mountQueue()`, `mountCard()`, `renderPlan()`, `renderLeft()`, `renderRight()`, `filesCard()`, `proofCard()`, `printCard()`, `arrange()`, `takeDrop()`, `takeFolder()`, `print()`, `isFormatField()`, `isCustomText()`, `isNameField()`, `STRIP_THUMB`
- [app/studio/orders.py](../../app/studio/orders.py) — `plan_for()`, `books_by_listing()`, `book_brief()`, `enrich()`, `arrange_pages()`, `page_options()`, `pages_word()`, `_list()`, `_one()`, `_files()`
- [app/studio/profit.py](../../app/studio/profit.py) — `picker_orders()`, `order_stage()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `STAGES`, `STAGE_EMPTY`, `planText()`, `pagesText()`, `addressFromEtsy()`, `syncOrders()`, `runningSync()`, `watchSync()`, `spreadsOf()`, `folderViewerItems()`, `receiveDrop()`, `wireFolderDrop()`, `smoothWheel()`
- [app/web/js/handoff.js](../../app/web/js/handoff.js) — `give()`
- [app/studio/creator.py](../../app/studio/creator.py) — `STRIP_PREVIEW`, `_warm_previews()`, `guess_child_name()`, `gelato_pages_problem()`
- [app/web/css/app.css](../../app/web/css/app.css) — `.ord-grid`, `.ord-side`, `.proof`, `.proof-note`, `.strip`
- Тести: [app/tests/test_orders.py](../../app/tests/test_orders.py) (у т. ч. `GelatoLength`), [app/tests/test_states.py](../../app/tests/test_states.py) (`PickerStages`)

## Пов'язане

- [Шлях замовлення до друку](../flows/order-to-print.md) · [Правило друкарні](../rules/printer-rule.md) · [Етапи](../rules/order-stages.md)
- [Order Creator](order-creator.md) · [Canva](../integrations/canva.md) · [Відкриті питання](../plans/open-questions.md)
