---
name: wiki-lint
description: Health-check the Book Studio wiki against the code and itself - contradictions, stale claims, gaps, orphan pages. Use when the owner asks to review the wiki or periodically before large tasks.
---

# Огляд здоров'я вікі

1. `python app/tools/wiki_check.py` і `--map` — механічні проблеми (посилання, функції, маршрути,
   непокриті файли). Виправ їх.
2. Прочитай сторінки по черзі разом із кодом, на який вони посилаються. Шукай:
   - твердження, які код уже не підтверджує (числа, назви, поведінка, дати «з …»);
   - суперечності між сторінками (наприклад, `rules/` проти `features/`);
   - поняття, згадані в кількох місцях без власної сторінки;
   - сторінки без вхідних посилань, крім `index.md`;
   - місця, де опис переказує код замість пояснювати *що* і *чому*;
   - застарілі пункти в `plans/` (вже збудовано → перенести в `decisions.md` / відповідну сторінку).
3. Виправ очевидне; спірне — список питань власнику (у `plans/open-questions.md` і у звіті).
4. Запропонуй 1–3 нові питання чи джерела, яких бракує вікі.
5. Запис угорі `wiki/log.md`: `## [РРРР-ММ-ДД] lint | підсумок`.
6. `python app/tools/wiki_check.py` і тести — без помилок.
