---
title: Сервер — маршрути, задачі, помилки
type: architecture
updated: 2026-09-17
code:
  - app/studio/server.py
  - app/studio/jobs.py
  - app/studio/httpc.py
  - app/studio/core.py
---
# Сервер

> Власний маленький HTTP-сервер на стандартній бібліотеці Python. Кожен модуль оголошує свої
> маршрути декоратором `@route`; довгі дії йдуть фоновими задачами, прогрес яких опитує інтерфейс.

## Маршрути

- `@route("POST", "/api/...", auth=...)` додає функцію в список `ROUTES`. Шаблон — регулярний
  вираз; групи потрапляють у `req.groups`.
- `auth`:
  - `token` (типово) — заголовок `X-Studio-Token` має дорівнювати `SESSION_TOKEN` (новий на кожен запуск,
    вбудовується в `index.html` при віддачі);
  - `media` — токен у параметрі `?t=` (для `<img src>`);
  - `none` — `/api/ping`, `/api/app/bye`, `/etsy/callback`.
- Функція повертає `dict` (стане JSON), `None` (стане `{"ok": true}`) або `Response`
  (`file_response()`, `html_response()`, `redirect()`).
- `Request`: `req.json` (до 25 МБ), `req.param(name)`, `req.body_to_file(path, max)` для завантажень.
- Статика: `/css`, `/js`, `/img`, `/fonts` з `app/web`, `/` — `index.html`.
- Повна таблиця — [api-routes.md](api-routes.md).

## Помилки

| Виняток | Код відповіді | Що бачить користувач |
|---|---|---|
| `ApiError` (і нащадки `EtsyError`, `PrintifyError`, `GelatoError`) | свій (типово 400) | текст помилки українською; `extra` додається в JSON (наприклад `code`) |
| `JobError` | 409 | текст |
| `HttpError` (зовнішній сервіс) | 502 | текст |
| будь-що інше | 500 | «Внутрішня помилка…», повний trace у `data/logs/app.log` |

Правило: повідомлення для користувача — українською, конкретно, що сталося і що робити.

## Фонові задачі

- `jobs.start(kind, fn, exclusive=...)` запускає потік і повертає `Job` з `id`.
  `exclusive` не дає запустити дві однакові дії (`profit-sync`, `printify-create`, `gelato-create`,
  `library-<id книги>`).
- Усередині `fn(job)` — `job.progress(step, percent, detail)`.
- Інтерфейс: маршрут повертає `{"jobId"}`, `runJob()` опитує `/api/jobs/<id>` кожні ~0,4 с до
  `done`/`error`.
- `UserError` у задачі → `status: error` з текстом; інше → «Несподівана помилка» + trace у журналі.
- Завершені задачі зберігаються годину.

## Зовнішні запити

- `httpc.request()` повторює при 429/5xx і обриві зв'язку (з паузою, `Retry-After` для 429).
- `HttpError.ambiguous = True` означає: запит міг дійти до сервісу. Для створення продукту/замовлення
  це сигнал **не повторювати**, а попросити перевірити сервіс.

## Налаштування і файли

- `core.settings` — несекретні налаштування в `data/settings.json`, злиті з `DEFAULT_SETTINGS`
  (`get()`, `section()`, `update()`, `replace_section()`, `drop_section()`).
- `write_json()` пише атомарно (тимчасовий файл → fsync → заміна) і тримає копію `.bak`;
  `read_json()` при пошкодженні читає `.bak`.
- Журнали: `data/logs/app.log`, `printify.log`, `gelato.log` (ротація по 2 МБ).

## Де в коді

- [app/studio/server.py](../../app/studio/server.py) — `route()`, `ROUTES`, `Request`, `Response`, `_Handler`, `ApiError`, `_index_html()`, `json_response()`, `file_response()`, `html_response()`, `redirect()`
- [app/studio/jobs.py](../../app/studio/jobs.py) — `Jobs`, `Job`, `UserError`, `JobError`
- [app/studio/httpc.py](../../app/studio/httpc.py) — `request()`, `request_json()`, `HttpError`, `RETRY_STATUSES`
- [app/studio/core.py](../../app/studio/core.py) — `Settings`, `DEFAULT_SETTINGS`, `write_json()`, `read_json()`, `setup_logging()`, `data_path()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `api()`, `runJob()`, `upload()`, `media()`

## Пов'язане

- [Маршрути](api-routes.md) · [Дані](data.md) · [Запуск](runtime.md) · [Безпека](../security.md)
