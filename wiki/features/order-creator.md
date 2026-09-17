---
title: Order Creator — книга в Printify, чернетка в Gelato
type: feature
updated: 2026-09-17
code:
  - app/studio/creator.py
  - app/web/js/pages/creator.js
---
# Order Creator

> Остання ланка: з папки PNG (`Cover.png` + сторінки) створює в **Printify** неопубліковану книгу
> (і, якщо заповнена адреса, замовлення «On hold»), а в **Gelato** — чернетку замовлення з PDF.
> Нічого не публікується і не йде у виробництво. Відкривається завжди порожнім.

## Екран (`#/creator`)

- Шапка: назва сервісу і перемикач **Printify / Gelato** (у режимі Printify акцент салатовий,
  у Gelato — синій). Під ним — рядок лише коли чогось бракує (ключа, шаблону, `cloudflared.exe`),
  з посиланням у Налаштування. Для Gelato — активні тимчасові посилання, якщо є.
- Ліва колонка — кроки:
  - **Printify**: 1 Папка з файлами → 2 Назва → 3 Адреса отримувача → 4 Чернетка.
  - **Gelato**: 1 Формат (Hardcover 8×8, Softcover 8×8, Softcover 5.5×5.5) → 2 Папка → 3 Назва →
    4 Адреса → 5 Чернетка. Кнопки форматів: підказка, скільки сторінок друкує Gelato («28–200 стор.»,
    з каталогу — `loadPageCounts()`, лише коли є ключ); якщо папка має 28 сторінок, а формат їх не
    приймає — кнопка жовта, під нею одне речення, «Створити» не пускає (`formatProblem()`).
- Права колонка — **структура**: обкладинка і всі розвороти з мініатюрами; зелені/червоні назви файлів
  за результатом перевірки; клік — переглядач. Для Gelato до вибору папки — «28 або 30 стор.»,
  після перевірки — точне число з папки (`pageCount` у відповіді перевірки).
- **Папка**: вибрати, вставити шлях або **перетягнути папку чи ZIP** на блок (поле підсвічується;
  показується власна назва папки, а шлях — копії в програмі). Перевірка запускається сама.
- **Назва**: `номер чека - ім'я дитини` (кнопка-чек заповнює назву й адресу із замовлення Etsy).
- **Адреса**: іконка-гумка очищує. Штат обов'язковий для US, CA, AU.
- **Кнопка** змінює підпис: Gelato — «Створити чернетку»; Printify з адресою — «Створити чернетку
  замовлення», без адреси — «Створити книгу без замовлення».
- **Результат**: картка з ID, перевірками, попередженнями; Printify — «Замовлення в Printify» або
  «Відкрити в Printify»; Gelato — таймер тимчасового посилання і «Gelato Dashboard».

## Вибір замовлення Etsy

Діалог `fromEtsy()`: пошук, етапи «Нові / В роботі / Відправлені», персоналізація згорнута (стрілка
розгортає список «поле: значення»). Відкриття діалогу не запускає синхронізацію, лише дочікується
запущеної; кнопка оновлення — запускає. Вибір заповнює назву й адресу (`addressFromEtsy()`).

## Передача з картки замовлення

`take('creator')` один раз забирає дані з картки (режим, папка, назва, формат, адреса) — і перевірка
запускається одразу. Якщо зайти на сторінку напряму, вона порожня.

## Printify: що відбувається на сервері

`create_printify_draft(folder, title, job, address)`:
1. Якщо є адреса — **спершу** перевіряє все про замовлення: адресу (`validate_address()`),
   підтвердження ручного затвердження, наявність матового варіанту в Master (`matte_variant()`).
2. Повна перевірка файлів (`validate("printify")`): рівно `Cover.png` 4672×2464 і `1…24.png`
   4000×4000, справжні PNG, повне декодування, без анімації; дублікати — попередження.
3. Читає Master, перевіряє blueprint/постачальника, зберігає знімок.
4. Завантажує зображення по 3 одночасно; вже завантажені (кеш SHA-256 і перевірка, що вони є в
   Printify) не дублюються. Збій → нічого не створюється, повтор продовжить з місця.
5. Створює продукт за конфігурацією Master (`build_printify_payload()`), без автоповтору.
6. Перечитує книгу (позиції зображень) і Master (не змінився).
7. З адресою — `create_order_on_hold()`: `external_id` = `<чек>-<8 символів>`, `label` = назва,
   матовий варіант, стандартна доставка, без Express і сповіщень. Помилка тут не скасовує книгу:
   `orderError` пояснює, що зробити.

Перед першим замовленням інтерфейс показує діалог «Ручне затвердження замовлень у Printify»
(`confirmManualApproval()`), і сервер запам'ятовує `manualApprovalConfirmedAt`.

## Gelato: що відбувається на сервері

`create_gelato_draft(folder, title, format_key, address, job)`:
1. Адреса, легка перевірка файлів (`Cover.png` + `1…30.png` або `1…28.png`, без вимог до розміру).
   Довжину книги визначає папка (`_gelato_page_count()`): найкоротша дозволена, що вміщає найбільший
   номер сторінки — `1…27` → бракує `28`; `1…29` → бракує `30`.
2. Чи друкує Gelato стільки сторінок у цьому форматі (`gelato_pages_problem()`, каталог) і розміри
   книги (`photobook_geometry()` з тією ж кількістю). Не друкує → помилка, нічого не створено.
3. Один PDF (`build_photobook_pdf()`): обкладинка, порожній форзац, 28 або 30 сторінок, порожній нахзац;
   зображення без перестиснення (PNG Canva склеюється в один IDAT — `_one_idat()`), підгонка з
   обрізанням країв; попередження, якщо обкладинка іншої пропорції.
4. Тимчасове посилання Cloudflare на цей PDF ([integrations/gelato.md](../integrations/gelato.md)).
5. `create_draft_order()`: `orderReferenceId` = `<чек>-<сеанс>` (щоб після синхронізації замовлення
   перейшло в «В роботі»), `files: [{type: "default", url}]`, метадані.
6. Посилання живе 15 хв (`tunnelKeepAliveSeconds`): Gelato забирає файл, коли відкрити чернетку в Dashboard.

## Де в коді

- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — `mount()`, `renderStatus()`, `folderCard()`, `titleCard()`, `formatCard()`, `addressCard()`, `createCard()`, `resultHtml()`, `renderRight()`, `validate()`, `create()`, `confirmManualApproval()`, `startCountdown()`, `fromEtsy()`, `dropFolder()`, `createLabel()`, `withOrder()`, `pageTotal()`, `loadPageCounts()`, `formatProblem()`
- [app/studio/creator.py](../../app/studio/creator.py) — `expected_files()`, `validate()`, `gelato_page_options()`, `_gelato_page_count()`, `gelato_page_counts()`, `gelato_pages_problem()`, `create_printify_draft()`, `build_printify_payload()`, `matte_variant()`, `printify_order_payload()`, `validate_address()`, `create_gelato_draft()`, `build_photobook_pdf()`, `_one_idat()`, `_status()`, `_gelato_page_counts()`, `_etsy_orders()`, `_folder_media()`, `_folder_spread()`
- [app/studio/printify.py](../../app/studio/printify.py) — `create_order_on_hold()`, `upload_exists()`
- [app/studio/gelato.py](../../app/studio/gelato.py) — `page_counts()`, `photobook_geometry()`, `create_draft_order()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `pagesText()`
- [app/web/css/app.css](../../app/web/css/app.css) — `.fmt-pill.bad`
- [app/web/js/handoff.js](../../app/web/js/handoff.js) — `take()`
- Тести: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`PrintifyDraftFlow`, `GelatoDraftFlow`, `CreatorStartsEmpty`, `DroppedFolders`), [app/tests/test_library_creator.py](../../app/tests/test_library_creator.py) (`PrintifyValidation`, `GelatoValidation`)

## Пов'язане

- [Printify](../integrations/printify.md) · [Gelato](../integrations/gelato.md) · [Безпека](../security.md) · [Перетягування файлів](../flows/dropped-files.md) · [Замовлення](orders.md)
