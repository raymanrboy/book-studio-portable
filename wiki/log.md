# Журнал змін вікі

Нові записи — вгорі. Формат заголовка: `## [РРРР-ММ-ДД] вид | що сталося`
(вид: `setup`, `ingest`, `update`, `query`, `lint`, `decision`). Правила — [dev/wiki-rules.md](dev/wiki-rules.md).

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
