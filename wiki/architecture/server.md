---
title: Server — routes, auth, jobs, errors
type: architecture
updated: 2026-11-12
code:
  - app/studio/server.py
  - app/studio/jobs.py
  - app/studio/httpc.py
  - app/studio/core.py
  - app/studio/settings_api.py
  - app/studio/__init__.py
---
# Server

> A small HTTP server on the Python standard library, bound to `127.0.0.1`. Every module declares its routes with `@route`; long actions run as background jobs the page polls. The route table is printed on demand: `python app/tools/wiki_check.py --routes`.

## Routes and auth

- `@route(method, pattern, auth=...)` appends to `ROUTES`; the pattern is a regex, groups land in `req.groups`.
- Auth modes (the only home of this list):
  - `token` (default) — header `X-Studio-Token` equals `SESSION_TOKEN`, new on every launch and embedded into `index.html` when it is served;
  - `media` — `?t=` in the link (for `<img src>`): `MEDIA_TOKEN` (`_media_key()`, kept in `data/media-key.txt`, so the window keeps pictures cached across restarts) or the session token; opens `/media/` routes only, never the API;
  - `none` — `/api/ping`, `/api/app/bye`, `/etsy/callback` (the OAuth return).
- A request whose `Host` is not `127.0.0.1:<port>` / `localhost:<port>` is refused with 403 (`_host_ok()`).
- A route returns a `dict` (JSON), `None` (`{"ok": true}`) or a `Response` (`file_response()`, `html_response()`).
- `Request`: `req.json` (up to 25 MB), `req.param()`, `req.int_param(name, default, lo, hi)` (missing or not a number gives the default, never an error page), `req.body_to_file(path, max_bytes)` for uploads.
- Static files: `/css`, `/js`, `/img`, `/fonts`, `/slides` from `app/web`; `/` is `index.html`, served with an import map and every script/style address carrying `?v=<time and size>` (`_versions()`, `_index_html()`). A file asked with `?v=` is cached for good (`immutable`); without it, asked again each time.
- `_ping()` answers with the app name, version and `data` (`core.data_id()`), so a second launch recognises a running copy of the same data only. Every reply carries `X-Frame-Options: DENY` and `frame-ancestors 'none'`.

## Routes that refuse (403)

- Creating or reprinting a Printify book (`/api/creator/printify/create`, `/api/creator/printify/reprint`) when `printify.retired()`: `RETIRED_TEXT` — see [Printify](../integrations/printify.md).
- `/api/app/open-url` (`settings_api._open_url()`) refuses `etsy.com` / `etsy.me` while `core.etsy_kyiv_only()` is on, except the Etsy sign-in page (`/oauth/connect`) after the owner confirms he is on the Kyiv PC — see [Etsy](../integrations/etsy.md).
- Printify and Gelato clients refuse anything outside their allow-lists (`printify._check()`, `gelato._allowed()`): [security](../security.md).

## Errors

| Exception | Code | The user sees |
|---|---|---|
| `ApiError` (and `EtsyError`, `PrintifyError`, `GelatoError`) | its own, usually 400 | its Ukrainian text; `extra` joins the JSON (e.g. `code`) |
| `JobError` | 409 | text |
| `HttpError` (external service) | 502 | text |
| anything else | 500 | "Внутрішня помилка…", full trace in `data/logs/app.log` |

A message for the user is Ukrainian, specific: what happened and what to do.

## Background jobs

- `jobs.start(kind, fn, exclusive=...)` runs a thread and returns a `Job`. `exclusive` stops two identical actions at once (`profit-sync`, `gelato-create`, `library-<book id>`).
- In `fn(job)`: `job.progress(step, percent, detail)`; `job.share(data)` hands over partial results before the end (the snapshot's `partial`; the text check shows findings this way).
- The route returns `{"jobId"}`; `runJob()` polls `/api/jobs/<id>` until `done`/`error`. Its fourth argument `keepGoing()` stops polling when the page no longer needs the result.
- `UserError` in a job gives `status: error` with its text; anything else "Несподівана помилка" plus a trace in the log. An error's `extra` goes into the snapshot as `errorExtra` and `runJob()` puts it in `err.data`.
- Finished jobs are purged after an hour.

## External requests

- `httpc.request()` retries on 429/5xx and dropped connections (`RETRY_STATUSES`; `Retry-After` for 429). A request that creates something (POST) is retried only when it certainly did nothing: connection refused, address not found, 429 or 503. After a timeout, a connection cut mid-reply or 500/502/504 it is not retried — a second attempt could create a second image, product or order.
- `HttpError.ambiguous` marks that case: do not retry, ask the owner to check the service. A POST that only reads (searching Gelato orders, a token refresh) is passed `idempotent=True`.
- Printer errors are worded by one function (`httpc.human()`); `extra` carries `upstream` and `ambiguous`. Printer call logs: `httpc.audit_log()`.
- Long lists come back as `httpc.Listing`; `complete = False` when the list stopped at its cap — the sync warns and the archive does not treat that list as fresh.

## Settings and modes

- `core.settings` holds non-secret settings (`data/settings.json`) merged with `DEFAULT_SETTINGS`: `get()`, `section()`, `update()`, `replace_section()`, `drop_section()`. File writing: [data](data.md).
- Environment switches: `core.SAMPLE` (preview server: made-up data, no key stored or offered) and `core.SANDBOX` (preview and tests: the [Workshop](../features/workshop.md) touches none of the owner's books, Downloads, clipboard or Recycle Bin — they are folders in the data folder, no window opens). Details: [preview](../dev/preview.md).

## Why
- POST is never retried blindly: a duplicate image, product or order costs money.
- `media` tokens are separate from the session token and persistent so cached pictures survive a restart; they open nothing but `/media/`.

## Where in the code
- [app/studio/server.py](../../app/studio/server.py) — `route()`, `ROUTES`, `Request`, `ApiError`, `_host_ok()`, `_index_html()`, `_ping()`, `file_response()`, `html_response()`
- [app/studio/jobs.py](../../app/studio/jobs.py) — `Job`, `Job.progress()`, `Job.share()`, `UserError`, `JobError`
- [app/studio/httpc.py](../../app/studio/httpc.py) — `request()`, `human()`, `audit_log()`, `HttpError`, `Listing`, `RETRY_STATUSES`
- [app/studio/core.py](../../app/studio/core.py) — `Settings`, `DEFAULT_SETTINGS`, `SAMPLE`, `SANDBOX`, `etsy_kyiv_only()`
- [app/studio/settings_api.py](../../app/studio/settings_api.py) — `_open_url()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `api()`, `runJob()`, `upload()`, `media()`

## Related
- [Data](data.md) · [Runtime](runtime.md) · [Frontend](frontend.md) · [Security](../security.md)
