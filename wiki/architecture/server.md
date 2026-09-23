---
title: Сервер — маршрути, задачі, помилки
type: architecture
updated: 2026-09-23
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
- Усередині `fn(job)` — `job.progress(step, percent, detail)`, а `job.share(дані)` віддає те, що вже
  відоме, до кінця задачі (з 20.09.2026): у знімку це поле `partial`, і сторінка малює його, поки
  задача триває — так перевірка тексту показує знайдені помилки, ще працюючи
  ([features/text-check.md](../features/text-check.md)).
- Інтерфейс: маршрут повертає `{"jobId"}`, `runJob()` опитує `/api/jobs/<id>` кожні ~0,4 с до
  `done`/`error`; проміжні знімки йдуть у `onProgress`. Четвертий аргумент — `keepGoing()`: сторінка,
  якій результат уже не потрібен (картку закрили, файли змінились), перестає опитувати (перевірка тексту
  і перевірки файлів у картці й Order Creator).
- `UserError` у задачі → `status: error` з текстом; інше → «Несподівана помилка» + trace у журналі.
  `extra` помилки (`ApiError`, напр. `{"code": "printify_token"}`) іде в знімок як `errorExtra`, і
  `runJob()` кладе його в `err.data` — як у звичайного запиту (з 23.09.2026; раніше губився).
- Завершені задачі зберігаються годину.

## Зовнішні запити

- `httpc.request()` повторює при 429/5xx і обриві зв'язку (з паузою, `Retry-After` для 429) — але
  запит, що **щось створює** (POST), повторює лише тоді, коли він точно нічого не зробив: з'єднання
  відхилено, адресу не знайдено, 429 чи 503. Після тайм-ауту, обриву посеред відповіді чи 500/502/504 —
  ні: друга спроба зробила б друге зображення, продукт чи замовлення (аудит 22.09.2026). POST, що лише
  читає (пошук замовлень Gelato, новий токен Etsy), позначається `idempotent=True`.
- `HttpError.ambiguous = True` означає: запит міг зробити своє на сервісі (тайм-аут, обрив, 500/502/504).
  Для створення продукту/замовлення/чернетки це сигнал **не повторювати**, а попросити перевірити сервіс.
- Помилку Printify і Gelato читає одна функція (`httpc.human()`): однакові слова на 401/403/404/429/4xx/5xx,
  а в `extra` — `upstream` (статус друкарні) і `ambiguous`. Журнали викликів друкарень — `httpc.audit_log()`.
- Довгі списки (замовлення Etsy, Printify, Gelato) приходять як `httpc.Listing`: `complete = False`, коли
  список зупинився на своїй межі, — тоді синхронізація попереджає, а архів не вважає цей список свіжим.

## Налаштування і файли

- `core.settings` — несекретні налаштування в `data/settings.json`, злиті з `DEFAULT_SETTINGS`
  (`get()`, `section()`, `update()`, `replace_section()`, `drop_section()`).
- `write_json()` пише атомарно (тимчасовий файл → fsync → заміна) і тримає копію `.bak`; не вдалося
  зробити копію — запис однаково відбувається, а в журналі попередження (`.bak` тепер старший).
- `read_json()` при **пошкодженні** читає `.bak`; файлу, якого **немає**, немає — `.bak` видаленого
  файлу не читається (з 23.09.2026: він повертав стан, який програма чи тест прибрали).
- Журнали: `data/logs/app.log`, `printify.log`, `gelato.log` (ротація по 2 МБ).

## Де в коді

- [app/studio/server.py](../../app/studio/server.py) — `route()`, `ROUTES`, `Request`, `Response`, `_Handler`, `ApiError`, `_index_html()`, `json_response()`, `file_response()`, `html_response()`, `redirect()`
- [app/studio/jobs.py](../../app/studio/jobs.py) — `Jobs`, `Job`, `Job.progress()`, `Job.share()`, `Job.snapshot()` (`errorExtra`), `UserError`, `JobError`
- [app/studio/httpc.py](../../app/studio/httpc.py) — `request()`, `request_json()`, `human()`, `audit_log()`, `HttpError`, `Listing`, `RETRY_STATUSES`, `_NOT_SENT`
- [app/studio/core.py](../../app/studio/core.py) — `Settings`, `DEFAULT_SETTINGS`, `write_json()`, `read_json()`, `setup_logging()`, `data_path()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `api()`, `runJob()`, `upload()`, `media()`

## Пов'язане

- [Маршрути](api-routes.md) · [Дані](data.md) · [Запуск](runtime.md) · [Безпека](../security.md)
