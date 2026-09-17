# Book Studio

Локальна Windows-програма для магазину персоналізованих дитячих книг на Etsy: черга замовлень,
бібліотека книг і створення книг/чернеток у Printify та Gelato.

- **Як користуватися** — [app/README.md](app/README.md)
- **Як усе влаштовано** — вікі проєкту: [wiki/index.md](wiki/index.md)
- **Правила для агентів** — [AGENTS.md](AGENTS.md) (Claude Code читає [CLAUDE.md](CLAUDE.md))

```
app/    програма (запуск: ярлик «Book Studio» або app/Book Studio.pyw)
wiki/   база знань
```

Тести: `cd app && python -m unittest discover -s tests` · перевірка вікі: `python app/tools/wiki_check.py`
