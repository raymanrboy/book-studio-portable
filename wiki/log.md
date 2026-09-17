# Журнал змін вікі

Нові записи — вгорі. Формат заголовка: `## [РРРР-ММ-ДД] вид | що сталося`
(вид: `setup`, `ingest`, `update`, `query`, `lint`, `decision`). Правила — [dev/wiki-rules.md](dev/wiki-rules.md).

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
