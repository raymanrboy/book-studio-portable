# Журнал змін вікі

Нові записи — вгорі. Формат заголовка: `## [РРРР-ММ-ДД] вид | що сталося`
(вид: `setup`, `ingest`, `update`, `query`, `lint`, `decision`). Правила — [dev/wiki-rules.md](dev/wiki-rules.md).

## [2026-09-19] update | Підказки не обрізаються; меню не лишається після переходу

- Зауваження власника: довгі підказки вилазили за плашку. Автоскан усіх сторінок (1480 і 1100 px): решта
  тексту вміщується, вада лише в підказках (5 різних) — тепер переносяться. Заодно: меню закривається при
  переході, Alt+1…5 не діють під діалогом чи переглядачем. [architecture/frontend.md](architecture/frontend.md),
  [owner/ui-principles.md](owner/ui-principles.md).

## [2026-09-19] update | Черга пам'ятає вкладку, пошук і прокрутку

- Зауваження власника: з картки «назад» вело на «Нові», а не у вкладку, звідки прийшов. Тепер повертає
  туди ж. [features/orders.md](features/orders.md), [owner/ui-principles.md](owner/ui-principles.md).

## [2026-09-19] update | Плавність: виправлення після огляду коду

- Модель звільняє відеокарту одразу після перевірки; перевірка зупиняється, коли вже не потрібна (новий
  маршрут `…/textcheck/cancel`); картки без роботи — не більше трьох; кеш прев'ю чиститься (21 день);
  дрібні виправлення з [plans/open-questions.md](plans/open-questions.md). Рішення — [decisions.md](decisions.md).
- Оновлено: [features/text-check.md](features/text-check.md), [features/orders.md](features/orders.md),
  [features/settings.md](features/settings.md), [features/library.md](features/library.md),
  [architecture/api-routes.md](architecture/api-routes.md), [architecture/frontend.md](architecture/frontend.md),
  [architecture/data.md](architecture/data.md), [architecture/runtime.md](architecture/runtime.md),
  [code-map.md](code-map.md), [dev/testing.md](dev/testing.md), [index.md](index.md).

## [2026-09-19] query | Огляд коду: чому стало менш плавно, знайдені вади

- На прохання власника — аналіз якості коду й плавності (без змін коду): сервер швидкий, головна
  підозра — модель у відеокарті під час і після перевірки тексту; список вад і черговість виправлень —
  [plans/open-questions.md](plans/open-questions.md).

## [2026-09-19] update | Перевірка тексту локальною моделлю — збудовано

- Картка замовлення, крок «Звірка»: Gemma в Ollama читає сторінки, програма звіряє з паспортом книги
  й даними Etsy; значок, список проблем, рамки на сторінках, питання перед друком, «Оновити паспорт»;
  блок у Налаштуваннях. Нова сторінка [features/text-check.md](features/text-check.md).
- Перевірено на трьох справжніх книгах з архіву і на 24-сторінковій книзі із закладеними помилками
  (усі знайдено, хибних тривог немає); виявлено, що паспорти двох книг розходяться з шаблонами Canva.
- Оновлено: [features/orders.md](features/orders.md), [flows/order-to-print.md](flows/order-to-print.md),
  [features/settings.md](features/settings.md), [features/library.md](features/library.md),
  [architecture/api-routes.md](architecture/api-routes.md), [architecture/data.md](architecture/data.md),
  [architecture/frontend.md](architecture/frontend.md), [security.md](security.md),
  [code-map.md](code-map.md), [glossary.md](glossary.md), [decisions.md](decisions.md),
  [plans/roadmap.md](plans/roadmap.md), [dev/testing.md](dev/testing.md), [dev/preview.md](dev/preview.md),
  [overview.md](overview.md), [index.md](index.md).

## [2026-09-19] decision | Ідеї: сторінки без Canva, мокапи для лістингу скриптом Photoshop

- Записано на прохання власника («потім реалізуємо»): програма сама малює сторінки й присвяти (з
  допомогою Gemma), спершу як «лабораторія»; дослідження інструментів для Linux; мокапи для лістингу —
  скрипт Photoshop CC 2019 заповнює сторінки в шаблонах, обкладинки власник робить сам.
  [plans/roadmap.md](plans/roadmap.md). Код не змінювався.

## [2026-09-19] query | Думки: перевірка тексту як функція програми

- На прохання власника («поки рано думати, просто запиши») — як могла б виглядати кнопка перевірки в
  картці замовлення, з чим звіряти, кроки і відкриті питання: [plans/roadmap.md](plans/roadmap.md).

## [2026-09-19] update | Обрізаний текст: Gemma знаходить завжди

- Дві сторінки з текстом за краєм (зокрема зникле ім'я) — знайдено в усіх варіантах.
  [plans/roadmap.md](plans/roadmap.md).

## [2026-09-19] update | Злиплі слова: сліпе переписування може «додати» пробіл; Qwen — прибрати

- Сторінка «Isabellawalked»: Gemma без підказки на 1024 px пропустила, з підказкою — знайшла завжди.
  Схема для майбутньої функції — підказка + звірка програмою (6/6 на всіх розмірах). Власник вирішив
  прибрати Qwen. [plans/roadmap.md](plans/roadmap.md).

## [2026-09-19] update | Відеокарта: моделі вже на повну, паралельна обробка — удвічі швидше

- Обидві моделі 100% на відеокарті; Qwen гучніша, бо читає картинку в повній роздільності. Власник
  увімкнув `OLLAMA_NUM_PARALLEL=4`: жорсткий тест по 4 сторінки одночасно — 10,3 с, результат той самий.
  Оновлено [plans/roadmap.md](plans/roadmap.md), [owner/working-with-owner.md](owner/working-with-owner.md).

## [2026-09-19] update | Жорсткий тест на сторінках власника: Gemma 5/5 без хибних тривог

- 12 сторінок зі справжніх шаблонів Canva (5 з помилками, 7 чистих, з них 2 — справжня книга, яку
  підклав власник). Gemma 4 12B QAT: сліпе переписування + порівняння програмою — усі помилки, жодної
  хибної тривоги, навіть на 768 px, ~1,5 с на сторінку; Qwen 3.5 9B слабша. Код не змінювався.
  Результати — [plans/roadmap.md](plans/roadmap.md).

## [2026-09-19] update | Gemma 4 12B QAT: тест перевірки тексту пройдено повністю

- На прохання власника встановлено `gemma4:12b-it-qat` (на D). Той самий тест: обидва способи без
  помилок (з підказкою імені — як Gemini; сліпе переписування 3 з 3), ~1–3 с на сторінку. Тепер вона —
  основна кандидатка. Код не змінювався. Оновлено [plans/roadmap.md](plans/roadmap.md).

## [2026-09-19] update | Встановлено локальну модель (Ollama + qwen3.5:9b) і перевірено

- На прохання власника: Ollama у `D:\Programs\Regular\Ollama`, модель `qwen3.5:9b` на диску D. Тест на
  тих самих сторінках, що для Gemini: з підказкою імені модель «виправляє» помилку в імені; сліпе
  переписування + порівняння програмою — усі помилки знайдено, ~2,5 с на сторінку. Код не змінювався.
- Оновлено [plans/roadmap.md](plans/roadmap.md), [owner/working-with-owner.md](owner/working-with-owner.md)
  (програми лише на D).

## [2026-09-18] update | Картка замовлення: довга присвята в записці прокручується

- Записка на першому розвороті обрізала довгий текст (7 рядків) — тепер він видний повністю, записка
  прокручується всередині (`.proof-note`). Оновлено [features/orders.md](features/orders.md); пастку
  прихованої панелі з переходами записано в [dev/preview.md](dev/preview.md).

## [2026-09-18] update | Gelato: назва «номер - ім'я», вигаданий телефон, формат 5" × 5"

- За зауваженнями власника: `orderReferenceId` = назва книги; порожній телефон → `+1 555 555 0100`;
  малий софткавер з Etsy (`5" × 5"`) тепер одразу обирає Softcover 5.5×5.5. Оновлено
  [integrations/gelato.md](integrations/gelato.md), [features/order-creator.md](features/order-creator.md),
  [rules/printer-rule.md](rules/printer-rule.md), [decisions.md](decisions.md), [glossary.md](glossary.md).

## [2026-09-18] update | Рахується лише оформлене й оплачене замовлення в друкарні

- Бажання власника: чернетки, неоплачені й скасовані замовлення не переводять замовлення «в роботу»,
  не кладуть книгу в архів і не роблять наступну відправку передруком (`is_placed()`). У «Нових» чип
  статусу чернетки; у картці — «Взяти файли минулої відправки»; передрук лише з надрукованої книги.
- Оновлено: [rules/order-stages.md](rules/order-stages.md), [features/archive.md](features/archive.md),
  [features/orders.md](features/orders.md), [features/order-creator.md](features/order-creator.md),
  [features/profit.md](features/profit.md), [flows/order-to-print.md](flows/order-to-print.md),
  [architecture/api-routes.md](architecture/api-routes.md), [decisions.md](decisions.md),
  [glossary.md](glossary.md), [dev/preview.md](dev/preview.md), [dev/testing.md](dev/testing.md).

## [2026-09-18] update | Gelato: звідки «Page 0»; порожні сторінки 300 dpi; передрук скасованого

- З'ясовано (читання двох замовлень з API, журнал старого Order Creator, PDF від 17.09): «правильне»
  замовлення без Page 0 пройшло через редактор Gelato; надрукований PDF має ту саму будову, що й наш.
- Порожні сторінки PDF — білі 300 dpi замість 16×16 px (через них Gelato оцінював книгу в 3 dpi).
- Передрук, коли перше замовлення скасоване в друкарні, не позначається заміною.
- Тестова чернетка старим Order Creator (обкладинка й сторінки окремо): обкладинка на всіх сторінках —
  лишаємо один PDF, Page 0 — нормально.
- Оновлено: [integrations/gelato.md](integrations/gelato.md), [decisions.md](decisions.md),
  [features/archive.md](features/archive.md), [rules/order-stages.md](rules/order-stages.md),
  [rules/book-structure.md](rules/book-structure.md), [dev/testing.md](dev/testing.md).

## [2026-09-18] update | Робота над новим замовленням пам'ятається при переході на іншу вкладку

- Бажання власника: повертатися до того самого кроку замовлення (файли, звірка, Order Creator, навіть
  сторінка успішного створення), поки замовлення не зникне з «Нових». Сторінки тепер ховаються й
  повертаються (`keep.js`, `navigate()`); іконка «Замовлення» веде в останню відкриту картку; після
  успіху крок «Друк» каже «чернетку створено». Order Creator, відкритий вручну, — і далі порожній.
- Оновлено: [architecture/frontend.md](architecture/frontend.md), [features/orders.md](features/orders.md),
  [features/order-creator.md](features/order-creator.md), [flows/order-to-print.md](flows/order-to-print.md),
  [owner/ui-principles.md](owner/ui-principles.md), [owner/working-with-owner.md](owner/working-with-owner.md),
  [decisions.md](decisions.md), [glossary.md](glossary.md), [code-map.md](code-map.md).

## [2026-09-18] update | Бокове меню: іконка не зникає під квадратиком

- Під час зміни сторінки квадратик активного пункту був окремим знімком поверх іконок і накривав
  іконку, до якої їхав. Тепер панель лишається живою над переходом: квадратик їде під іконками, іконка
  плавно змінює колір. Оновлено [architecture/frontend.md](architecture/frontend.md),
  [owner/ui-principles.md](owner/ui-principles.md).

## [2026-09-18] update | Архів замовлень збудовано: файли, що пішли в друк, 14 днів і передрук

- Нове меню «Архів замовлень» (Alt+4, Налаштування тепер Alt+5): кожна відправка в Printify чи Gelato
  кладе копію файлів книги в `data/archive/`; сторінка книги — звірка, дані замовлення, адреса, «Не
  видаляти», передрук. Файли видаляються самі через 14 днів після «Відправлених»; без відомостей про
  замовлення — нічого не видаляється. Опис — [features/archive.md](features/archive.md).
- Передрук: Printify — нове замовлення On hold з тієї ж книги (нічого не завантажується; зникла книга
  — створюється заново з архіву); Gelato — нова чернетка з тих самих файлів. Чек позначається
  заміною, етап у черзі не змінюється.
- Оновлено: [architecture/api-routes.md](architecture/api-routes.md), [architecture/data.md](architecture/data.md),
  [architecture/frontend.md](architecture/frontend.md), [architecture/runtime.md](architecture/runtime.md),
  [features/order-creator.md](features/order-creator.md), [features/profit.md](features/profit.md),
  [rules/order-stages.md](rules/order-stages.md), [rules/sync-policy.md](rules/sync-policy.md),
  [flows/order-to-print.md](flows/order-to-print.md), [security.md](security.md), [decisions.md](decisions.md),
  [glossary.md](glossary.md), [code-map.md](code-map.md), [plans/roadmap.md](plans/roadmap.md),
  [dev/preview.md](dev/preview.md), [dev/testing.md](dev/testing.md), [index.md](index.md).

## [2026-09-18] decision | План «Архів замовлень»; програма лише на вроцлавському ПК

- Узгоджено з власником (код не змінювався): окреме меню «Архів замовлень» з файлами книг, що пішли в
  друк, звіркою і передруком; автовидалення через 14 днів після «Відправлених», кнопка «Не видаляти»,
  лише нові замовлення — [plans/roadmap.md](plans/roadmap.md), [decisions.md](decisions.md),
  [glossary.md](glossary.md).
- Власник не запускає Book Studio на київському ПК: уточнено [overview.md](overview.md),
  [owner/working-with-owner.md](owner/working-with-owner.md), [integrations/etsy.md](integrations/etsy.md);
  прибрано питання про копію на київському ПК з [plans/open-questions.md](plans/open-questions.md).

## [2026-09-17] decision | Перевірка тексту через Gemini — у плани

- Обговорено й перевірено тестом на вигаданих сторінках (3.6 / 3.5 Flash знайшли всі закладені
  помилки; 3.8 / 3.7 Flash були перевантажені). Код не змінювався; власник зберіг ключ
  `gemini_api_key` у сховищі програми.
- Власник відклав збудовування; безкоштовний рівень, лише сторінки з текстом (до 17). План —
  [plans/roadmap.md](plans/roadmap.md), рішення й умови Google для ЄЕЗ — [decisions.md](decisions.md).

## [2026-09-17] update | Черга: один тон, копіювання номера замовлення, статус біля імені

- За зауваженнями власника на справжніх даних: назва друкарні, перевізник і номер — одного м'якого
  тону; номер замовлення Etsy копіюється кліком (черга й картка); у картці статус друкарні — біля
  імені, по центру. Оновлено [features/orders.md](features/orders.md),
  [owner/ui-principles.md](owner/ui-principles.md), [glossary.md](glossary.md), [decisions.md](decisions.md).

## [2026-09-17] update | Черга: вкладка «машинка», статус друкарні, трек-номери

- Збудовано ідею власника: четвертий етап `sent` (друкарня відправила, в Etsy не позначено), статус
  Printify/Gelato праворуч (англійською, по-людськи, з кольоровою крапкою), ім'я дитини жирно в сірому
  рядку, чип трек-номера (перевізник | номер, клік копіює) — у черзі й шапці картки.
- Синхронізація: Printify зберігає `shipments`; Gelato дочитує трек-номери відправлених замовлень
  по одному (`attach_shipments()`, лише читання). Чип «Gelato · 28 або 30 стор.» — одним шрифтом;
  тексти чипів на одній лінії.
- Оновлено: [rules/order-stages.md](rules/order-stages.md), [features/orders.md](features/orders.md),
  [integrations/printify.md](integrations/printify.md), [integrations/gelato.md](integrations/gelato.md),
  [rules/sync-policy.md](rules/sync-policy.md), [flows/order-to-print.md](flows/order-to-print.md),
  [architecture/frontend.md](architecture/frontend.md), [owner/ui-principles.md](owner/ui-principles.md),
  [security.md](security.md), [dev/preview.md](dev/preview.md), [dev/testing.md](dev/testing.md),
  [glossary.md](glossary.md), [decisions.md](decisions.md); ідею прибрано з [plans/roadmap.md](plans/roadmap.md).

## [2026-09-17] update | Журнал відправок — кнопка в шапці Order Creator

- Власник не знайшов піктограму журналу (вона була лише в картках результату й помилки). Тепер вона
  завжди в шапці поруч із перемикачем Printify/Gelato і відкриває найновіший запис —
  [features/send-journal.md](features/send-journal.md), [features/order-creator.md](features/order-creator.md).
- Власник вирішив не міняти ключ Gelato, вставлений у чат ([decisions.md](decisions.md)).

## [2026-09-17] decision | Git: комітити все разом

- Власник просить не ділити зміни на «свої / інших сесій» і не ускладнювати гілками — усе разом, історія
  версій однаково є. Записано в [dev/setup.md](dev/setup.md) і [owner/working-with-owner.md](owner/working-with-owner.md).

## [2026-09-17] update | Gelato: стандарти з реальних замовлень, журнал відправок

- Прочитано (лише читання) ручне замовлення власника на 28 сторінок і старе API-замовлення на 30,
  розібрано їхні друкарські PDF; зроблено дві тестові чернетки з пронумерованими сторінками.
- Висновки — у [integrations/gelato.md](integrations/gelato.md) і [decisions.md](decisions.md):
  метричні товари 20×20 / 14×14 см; PDF «обкладинка · порожня · сторінки · порожня» лишається
  (без порожніх книга зсувається — перевірено); Page 0 у чернетці — форзац; 28 сторінок — без зсуву.
- Нове: [features/send-journal.md](features/send-journal.md) (журнал відправок, маршрут
  `POST /api/sends/open`), перевірка посилання через публічний DNS, попередження про обкладинку лише
  понад 10 мм.
- Оновлено також: [features/order-creator.md](features/order-creator.md), [rules/book-structure.md](rules/book-structure.md),
  [architecture/data.md](architecture/data.md), [security.md](security.md), [plans/open-questions.md](plans/open-questions.md),
  [glossary.md](glossary.md), [code-map.md](code-map.md), [recipes.md](recipes.md), [index.md](index.md).

## [2026-09-17] ingest | Відповіді власника про вкладку з машинкою і статуси

- Машинка — четверта вкладка між «В роботі» і «Відправлені»: друкарня відправила, в Etsy ще не
  позначено; після позначки в Etsy замовлення йде в «Відправлені». Статус праворуч — як віддає
  Printify/Gelato, англійською; окремих позначок для чернеток не треба.
- Оновлено [plans/roadmap.md](plans/roadmap.md), [glossary.md](glossary.md) (машинка, бокс, годинник),
  [rules/order-stages.md](rules/order-stages.md), [features/orders.md](features/orders.md); два питання
  прибрано з [plans/open-questions.md](plans/open-questions.md). Код не змінювався.

## [2026-09-17] update | Gelato: книга на 28 або 30 сторінок

- Реалізовано ідею з планів: довжину книги Gelato визначає кількість скачаних сторінок (28 або 30);
  рішення — у [decisions.md](decisions.md), пункт прибрано з [plans/roadmap.md](plans/roadmap.md).
- Програма читає з каталогу Gelato, скільки сторінок друкує кожен формат; новий маршрут
  `GET /api/creator/gelato/page-counts` ([architecture/api-routes.md](architecture/api-routes.md)).
- Софткавер на 28 сторінок — не перевірено (довідка Gelato: «від 30»); відповідь покаже програма
  після перезапуску — [plans/open-questions.md](plans/open-questions.md).
- Оновлено: [integrations/gelato.md](integrations/gelato.md), [features/order-creator.md](features/order-creator.md),
  [features/orders.md](features/orders.md), [rules/printer-rule.md](rules/printer-rule.md),
  [rules/book-structure.md](rules/book-structure.md), [rules/file-naming.md](rules/file-naming.md), та ін.

## [2026-09-17] ingest | Ідея: відправлені, статус і трек-номер у черзі

- Джерело: [raw/2026-09-17-vidpravleni-i-trek-nomery.md](raw/2026-09-17-vidpravleni-i-trek-nomery.md)
  (текст власника; скриншот не збережено — на ньому справжні імена покупців).
- Записано в [plans/roadmap.md](plans/roadmap.md) (вкладка з машинкою, статус праворуч, ім'я в сірому
  рядку, чип трек-номера), питання — у [plans/open-questions.md](plans/open-questions.md), нові слова —
  у [glossary.md](glossary.md), позначки «задумано» — у [features/orders.md](features/orders.md) і
  [rules/order-stages.md](rules/order-stages.md). Код не змінювався.

## [2026-09-17] decision | Файл ключів .secrets.txt тепер у корені Book Studio

- На прохання власника файл скопійовано з Etsy OS без відкриття (побайтово однаковий); git його
  ігнорує. Оригінал лишився в Etsy OS. Оновлено [security.md](security.md) і `AGENTS.md`.
- Власник відключає папку Etsy OS від роботи з агентом (там видалено `.gitignore`, і кнопка
  «Commit changes» могла б зберегти ключі в історії git).

## [2026-09-17] setup | Створено вікі, програму перенесено в app/

- Власник запропонував базу знань за шаблоном «LLM Wiki»; домовились: `app/` + `wiki/` +
  `AGENTS.md`/`CLAUDE.md`, детальні посилання на код, актуалізація після кожної задачі.
- Програму перенесено в `app/` (`git mv`), `data/` і `bin/` — туди ж; виправлено шлях до старих програм
  у `settings_api.py`; ярлик створено заново; тести й запуск сервера перевірено.
- Прочитано весь код; створено 37 сторінок (плюс зміст і журнал): огляд, словник, карта коду, безпека, будова (5), розділи (5),
  сервіси (4), правила (6), шляхи (3), власник (2), розробка (4), рішення, рецепти, плани (2).
- `docs/order-pipeline.md` перетворено на [flows/order-to-print.md](flows/order-to-print.md), решту його
  змісту рознесено по правилах, рішеннях і планах.
- Факти з пам'яті агента перенесено у [decisions.md](decisions.md), [owner/](owner/working-with-owner.md),
  [security.md](security.md).
- Додано `app/tools/wiki_check.py`, тест `test_wiki.py`, `app/tools/dev_server.py`, навички Claude Code
  для вікі.
