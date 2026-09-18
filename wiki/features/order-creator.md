---
title: Order Creator — книга в Printify, чернетка в Gelato
type: feature
updated: 2026-09-18
code:
  - app/studio/creator.py
  - app/web/js/pages/creator.js
---
# Order Creator

> Остання ланка: з папки PNG (`Cover.png` + сторінки) створює в **Printify** неопубліковану книгу
> (і, якщо заповнена адреса, замовлення «On hold»), а в **Gelato** — чернетку замовлення з PDF.
> Нічого не публікується і не йде у виробництво. Відкривається порожнім — крім роботи над новим
> замовленням, яка зберігається, поки замовлення в «Нових» (див. нижче).

## Екран (`#/creator`)

- Шапка: назва сервісу, піктограма **«Журнал відправок»** ([send-journal.md](send-journal.md)) і
  перемикач **Printify / Gelato** (у режимі Printify акцент салатовий, у Gelato — синій). Під ним — рядок лише коли чогось бракує (ключа, шаблону, `cloudflared.exe`),
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
- **Адреса**: іконка-гумка очищує. Штат обов'язковий для US, CA, AU. Для Gelato порожній телефон →
  вигаданий `+1 555 555 0100` (без телефону Gelato не дає оформити замовлення).
- **Кнопка** змінює підпис: Gelato — «Створити чернетку»; Printify з адресою — «Створити чернетку
  замовлення», без адреси — «Створити книгу без замовлення».
- **Результат**: картка з ID, перевірками, попередженнями; Printify — «Замовлення в Printify» або
  «Відкрити в Printify»; Gelato — будова PDF, таймер тимчасового посилання і
  «Gelato Dashboard». В обох — піктограма «Журнал відправки» (`sendLogButton()`); у картці помилки
  вона відкриває папку журналу ([send-journal.md](send-journal.md)).

## Вибір замовлення Etsy

Діалог `fromEtsy()`: пошук, етапи «Нові / В роботі / Відправлені», персоналізація згорнута (стрілка
розгортає список «поле: значення»). Відкриття діалогу не запускає синхронізацію, лише дочікується
запущеної; кнопка оновлення — запускає. Вибір заповнює назву й адресу (`addressFromEtsy()`).

## Передача з картки замовлення

`take('creator')` один раз забирає дані з картки (номер чека, режим, папка, назва, формат, адреса) — і
перевірка запускається одразу. Якщо зайти на сторінку напряму без такої роботи, вона порожня.

**Робота над замовленням зберігається** (з 18.09.2026, прохання власника): Order Creator, заповнений
з картки або вибором нового замовлення Etsy, пам'ятає своє замовлення (`st.receiptId`). Перейшовши на
іншу вкладку, власник повертається до тієї ж форми або до сторінки результату (з відліком посилання
Gelato), поки замовлення в «Нових»; потім — порожня сторінка. Після успіху картка замовлення показує
«Чернетку … створено» (`markSent()`, `sentText()`). Нова передача з картки чи з архіву замінює
збережене. Передрук з архіву не зберігається (замовлення вже не нове). Як влаштовано —
[architecture/frontend.md](../architecture/frontend.md).

## Передрук з архіву замовлень (з 18.09.2026)

Кнопка «Передрук» в [архіві замовлень](archive.md) передає ще й `reprint: {archiveId, productId}`:
- у блоці папки — рядок «Передрук з архіву: …», кнопка — «Створити замовлення-передрук» (Printify,
  адреса обов'язкова — `withOrder()`) або «Створити чернетку-передрук» (Gelato);
- Printify іде на `POST /api/creator/printify/reprint`: **нове замовлення «On hold» на ту саму книгу**,
  файли не відправляються, тож перевірка файлів кнопку не блокує; Gelato — звичайне створення з
  `reprintOf` (сервер сам бере файли з архіву);
- інша папка (вибір, перетягування, введений шлях) — режим передруку знімається;
- картка результату: «Передрук: замовлення створено в Printify!» (для тієї самої книги — «нічого не
  завантажувалось») / «Передрук: чернетку створено в Gelato!».

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
3. Один PDF (`build_photobook_pdf()`): обкладинка, порожній форзац, 28 або 30 сторінок, порожній
   нахзац — порожні обов'язкові ([integrations/gelato.md](../integrations/gelato.md)); зображення без
   перестиснення (PNG Canva склеюється в один IDAT — `_one_idat()`), підгонка з обрізанням країв;
   попередження лише коли обкладинка обрізається більш ніж на 10 мм.
4. Тимчасове посилання Cloudflare на цей PDF (перевірка доступності — і через публічний DNS).
5. `create_draft_order()`: `orderReferenceId` = назва книги `<чек> - <ім'я>` (щоб після підтвердження й оплати в Gelato
   і синхронізації замовлення перейшло в «В роботі»), `files: [{type: "default", url}]`, метадані; потім чернетка перечитується
   для журналу (`_journal_readback()`).
6. Посилання живе 15 хв (`tunnelKeepAliveSeconds`); Gelato забирає файл сам, приблизно за хвилину.

Обидві відправки (Printify і Gelato) пишуть [журнал відправок](send-journal.md): обгортки
`create_printify_draft()` / `create_gelato_draft()` кличуть `_printify_draft()` / `_gelato_draft()`
усередині `sendlog.attempt()`; `_journaled()` дописує назву запису журналу в результат і в архів.

Після **успішної** відправки файли йдуть в [архів замовлень](archive.md) (`_to_archive()`): Printify —
щойно книга створена (з замовленням чи без), Gelato — щойно створено чернетку; у списку архіву книга
з'являється, коли замовлення в друкарні оформлене й оплачене. Передрук — лише з книги, що справді
пішла в друк (`archive.reprintable()`). Збій архівування
відправку не скасовує — у картці результату з'являється попередження. Передрук позначається як
заміна чека (`_mark_reprint()` → `profit.mark_reprint()`), крім випадку, коли перше замовлення
скасоване в друкарні.

PDF для Gelato: обкладинка · порожня · сторінки · порожня; порожні — білі 300 dpi (`BLANK_DPI`), чому
саме так — [Gelato](../integrations/gelato.md).

## Де в коді

- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — `mount()`, `renderStatus()`, `folderCard()`, `titleCard()`, `formatCard()`, `addressCard()`, `createCard()`, `resultHtml()`, `renderRight()`, `validate()`, `create()`, `confirmManualApproval()`, `startCountdown()`, `fromEtsy()`, `dropFolder()`, `createLabel()`, `withOrder()`, `pageTotal()`, `loadPageCounts()`, `formatProblem()`, `sendLogButton()`, `sentText()`
- [app/studio/creator.py](../../app/studio/creator.py) — `expected_files()`, `validate()`, `gelato_page_options()`, `_gelato_page_count()`, `gelato_page_counts()`, `gelato_pages_problem()`, `create_printify_draft()`, `_printify_draft()`, `create_printify_reprint()`, `_printify_reprint()`, `_to_archive()`, `_mark_reprint()`, `_journaled()`, `build_printify_payload()`, `matte_variant()`, `printify_order_payload()`, `validate_address()`, `create_gelato_draft()`, `_gelato_draft()`, `_journal_readback()`, `build_photobook_pdf()`, `_one_idat()`, `_status()`, `_gelato_page_counts()`, `_etsy_orders()`, `_folder_media()`, `_folder_spread()`
- [app/studio/printify.py](../../app/studio/printify.py) — `create_order_on_hold()`, `upload_exists()`
- [app/studio/gelato.py](../../app/studio/gelato.py) — `page_counts()`, `photobook_geometry()`, `create_draft_order()`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `pagesText()`
- [app/studio/sendlog.py](../../app/studio/sendlog.py) — `attempt()`, `step()`
- [app/studio/archive.py](../../app/studio/archive.py) — `store()`, `update()`, `get()`
- [app/web/css/app.css](../../app/web/css/app.css) — `.fmt-pill.bad`, `.cr-reprint`
- [app/web/js/handoff.js](../../app/web/js/handoff.js) — `take()`
- Тести: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`PrintifyDraftFlow`, `GelatoDraftFlow`, `CreatorStartsEmpty`, `DroppedFolders`), [app/tests/test_library_creator.py](../../app/tests/test_library_creator.py) (`PrintifyValidation`, `GelatoValidation`), [app/tests/test_archive.py](../../app/tests/test_archive.py) (`PrintifyReprint`, `GelatoReprint`)

## Пов'язане

- [Printify](../integrations/printify.md) · [Gelato](../integrations/gelato.md) · [Безпека](../security.md) · [Перетягування файлів](../flows/dropped-files.md) · [Замовлення](orders.md)
