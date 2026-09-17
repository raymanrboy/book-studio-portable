---
name: wiki-update
description: Bring the Book Studio wiki up to date after code changes. Use at the end of every task that changed files in app/, or when the wiki check or test_wiki fails.
---

# Актуалізація вікі після змін у коді

1. Подивись, що змінилось: `python app/tools/wiki_check.py --changed` (з кореня репозиторію,
   `PYTHONIOENCODING=utf-8`). Він перелічить сторінки вікі, які описують змінені файли, і файли без опису.
2. Для кожної сторінки зі списку:
   - перечитай її і змінений код;
   - виправ зміст, розділ «Де в коді» (файл + назви функцій/констант після посилання), шапку `code:`;
   - постав `updated:` на сьогоднішню дату.
3. Додатково, якщо стосується:
   - новий файл → рядок у `wiki/code-map.md` і шлях у `code:` найближчої за темою сторінки;
   - новий/змінений/видалений маршрут `@route` → `wiki/architecture/api-routes.md` (метод, шаблон як у коді, `|` екранувати);
   - рішення власника або важливий технічний вибір → запис угорі `wiki/decisions.md` (дата, рішення, чому);
   - нове слово власника → `wiki/glossary.md`;
   - нова ідея «на потім» чи невирішене питання → `wiki/plans/`;
   - нова сторінка → посилання в `wiki/index.md`.
4. Запис угорі `wiki/log.md`: `## [РРРР-ММ-ДД] update | що змінилось` і 1–5 пунктів.
5. `python app/tools/wiki_check.py` — має бути «Вікі в порядку». Потім тести
   (`cd app && python -m unittest discover -s tests`).
6. У звіті власнику — одним рядком, які сторінки вікі оновлено.

Формат і правила — `wiki/dev/wiki-rules.md`. Не переказуй код; пиши *що* і *чому*, і де шукати.
