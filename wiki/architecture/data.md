---
title: Дані програми — папка app/data
type: architecture
updated: 2026-09-19
code:
  - app/studio/core.py
  - app/studio/vault.py
  - app/studio/images.py
---
# Дані програми

> Усе, що програма пам'ятає, лежить у `app/data/` (≈1,4 ГБ, не в git). Для резервної копії достатньо
> скопіювати цю папку. Змінна середовища `BOOK_STUDIO_DATA` підміняє папку (тести, перегляд).

## Що де лежить

| Шлях у `app/data/` | Що це | Хто пише |
|---|---|---|
| `settings.json` (+`.bak`) | Несекретні налаштування: тема, Etsy (магазин, адреса повернення), Printify (магазин, Master, розміри, `manualApprovalConfirmedAt`), Gelato (формати, курс EUR→USD, `pageCounts` 28 і 30; при запуску `_upgrade()` прибирає старе `pageCount` і міняє «дюймові» товари Gelato на метричні), `textcheck` (увімкнено, модель, адреса Ollama — лише 127.0.0.1) | `core.settings` |
| `vault.json` (+`.bak`) | Ключі Etsy/Printify/Gelato, токени Etsy і ключ Gemini (`gemini_api_key`, для запланованої перевірки тексту — поки не використовується), зашифровані DPAPI. **Не читати й не друкувати** | `Vault` |
| `library/books/<id>/book.json` | Модель книги ([features/library.md](../features/library.md)) | `library.save()` |
| `library/books/<id>/assets/<uuid>.png` | Ілюстрації книги (оригінали) | `library._store_asset()` |
| `library/trash/` | Видалені книги (можна повернути вручну) | `library._delete()` |
| `profit/snapshot.json` | Знімок останньої синхронізації: чеки Etsy, замовлення Printify і Gelato (скорочені), курсор синхронізації | `profit._sync()` |
| `profit/links.json` | Ручні зв'язки «чек → замовлення друку» або «без собівартості» | `profit._set_link()` |
| `profit/states.json` | Ручні стани: скасування, повернення, заміна (сюди ж — передруки з архіву замовлень) | `profit._set_state()`, `profit.mark_reprint()` |
| `creator/upload-cache.json` | SHA-256 файлу → ID зображення в Printify (щоб не завантажувати двічі) | `creator._remember_upload()` |
| `creator/master-snapshots/` | Знімки Master-продукту перед кожним створенням книги | `create_printify_draft()` |
| `cache/thumbs/` | JPEG-прев'ю (ключ — шлях, час зміни, розмір, розмір прев'ю); не потрібні 21 день — видаляються при запуску (з 19.09.2026; прев'ю в роботі раз на добу оновлює дату) | `images.preview()`, `images.prune_cache()` |
| `tmp/dropped/` | Копії перетягнутих папок і ZIP; стирається при запуску | `creator._drop_file()` |
| `tmp/gelato/<сеанс>/` | PDF для Gelato, поки працює тимчасове посилання | `create_gelato_draft()` |
| `logs/` | `app.log`, `printify.log`, `gelato.log`, `startup-error.txt` | журнали |
| `logs/sends/` | по одному JSON на кожну відправку в Printify/Gelato (останні 400; з адресами, без ключів) | [журнал відправок](../features/send-journal.md) |
| `logs/checks/` | по одному JSON на кожну перевірку тексту: що прочитала модель, що мало бути, проблеми (останні 400; з іменами дітей) | [перевірка тексту](../features/text-check.md) |
| `archive/<id>/` | Архів замовлень: `Cover.png` + сторінки, що пішли в друк, і `entry.json` (що, куди, коли, адреса). **Видаляється сама** через 14 днів після «Відправлених» (30 — якщо замовлення не простежити), крім «Не видаляти» | [архів замовлень](../features/archive.md) |
| `window-profile/` | Профіль вікна Edge (≈0,5 ГБ) | Edge |

## Правила

- Запис лише через `core.write_json()` (атомарно, з копією `.bak`).
- Кеш прев'ю прив'язаний до повного шляху файлу: після перенесення папки даних прев'ю один раз
  створюються заново (старі файли кешу просто лишаються без діла).
- Order Creator нічого не пам'ятає між відкриттями (рішення власника): `forget_old_form()` прибирає
  залишки старих версій (`settings.creator`, `creator/history.json`).
- Папка тестів створюється в системній тимчасовій теці й видаляється після тестів.

## Де в коді

- [app/studio/core.py](../../app/studio/core.py) — `DATA_DIR`, `data_path()`, `ensure_dirs()`, `write_json()`, `read_json()`, `Settings`
- [app/studio/vault.py](../../app/studio/vault.py) — `Vault`, `SECRET_NAMES`
- [app/studio/images.py](../../app/studio/images.py) — `preview()`, `_cached()`
- [app/studio/library.py](../../app/studio/library.py) — `BOOKS_DIR`, `TRASH_DIR`
- [app/studio/profit.py](../../app/studio/profit.py) — `SNAPSHOT`, `LINKS`, `STATES`
- [app/studio/creator.py](../../app/studio/creator.py) — `UPLOAD_CACHE`, `DROPS`, `forget_old_form()`
- [app/studio/archive.py](../../app/studio/archive.py) — `ROOT`, `store()`, `refresh()`
- [app/tests/__init__.py](../../app/tests/__init__.py) — `BOOK_STUDIO_DATA` для тестів

## Пов'язане

- [Сервер](server.md) · [Безпека](../security.md) · [Бібліотека](../features/library.md)
