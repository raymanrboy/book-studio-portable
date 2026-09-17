@AGENTS.md

# Доповнення для Claude Code

- **Навички проєкту** (`.claude/skills/`):
  - `/wiki-update` — актуалізувати вікі після змін у коді (виконувати наприкінці кожної задачі);
  - `/wiki-ingest` — додати у вікі матеріал від власника (текст, скриншот, документ);
  - `/wiki-lint` — огляд здоров'я вікі.
- **Перегляд інтерфейсу**: `preview_start("book-studio-dev")` (`.claude/launch.json`, порт 47890,
  вигадані дані). Прихована панель браузера не запускає `requestAnimationFrame` — перевіряти DOM і
  підміняти rAF на `setTimeout`; після `resize_window` повернути `preset: "desktop"`; наприкінці
  `preview_stop`. Деталі — `wiki/dev/preview.md`.
- **GitHub CLI** на цьому ПК не в PATH: `C:\Users\Roman\AppData\Local\Programs\GitHubCLI\bin\gh.exe`
  (акаунт `raymanrboy`, репозиторій `raymanrboy/book-studio`). Push — командою з `wiki/dev/setup.md`.
- **Оболонки**: у Bash краще абсолютні шляхи (`cd` змінює робочу папку сесії); кирилиця у виводі
  Python — з `PYTHONIOENCODING=utf-8`; тести — з `PYTHONDONTWRITEBYTECODE=1`.
- **Пам'ять агента** — лише для особистих нотаток; усе про проєкт — у вікі.
