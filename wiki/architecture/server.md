---
title: Server — routes, jobs, errors
type: architecture
updated: 2026-09-27
code:
  - app/studio/server.py
  - app/studio/jobs.py
  - app/studio/httpc.py
  - app/studio/core.py
---
# Server

> A small HTTP server of its own, on the Python standard library. Every module declares its own routes
> with the `@route` decorator; long-running actions run as background jobs whose progress the interface
> polls.

## Routes

- `@route("POST", "/api/...", auth=...)` adds a function to the `ROUTES` list. The pattern is a regular
  expression; groups land in `req.groups`.
- `auth`:
  - `token` (default) — the `X-Studio-Token` header must equal `SESSION_TOKEN` (new on every launch,
    embedded into `index.html` when it's served);
  - `media` — the token in the `?t=` parameter (for `<img src>`);
  - `none` — `/api/ping`, `/api/app/bye`, `/etsy/callback`.
- The function returns a `dict` (becomes JSON), `None` (becomes `{"ok": true}`), or a `Response`
  (`file_response()`, `html_response()`, `redirect()`).
- `Request`: `req.json` (up to 25 MB), `req.param(name)`, `req.int_param(name, default, lo, hi)` (a number
  from the query — a preview's width, a page; missing or not a number, it is the default, never an error page;
  since 2026-09-26), `req.body_to_file(path, max)` for uploads.
- Static files: `/css`, `/js`, `/img`, `/fonts` from `app/web`, `/` — `index.html`.
- `state.app` — what `/api/ping` answers ("Book Studio"), so a second launch recognises the running copy
  and only opens another window. (From 2026-09-23 to 24 the [mockups](../features/mockups.md) were a second
  program on the same server code, with its own `state.page` and answer; now their routes are Book
  Studio's own.)
- The full table — [api-routes.md](api-routes.md).

## Errors

| Exception | Response code | What the user sees |
|---|---|---|
| `ApiError` (and subclasses `EtsyError`, `PrintifyError`, `GelatoError`) | its own (usually 400) | the error text in Ukrainian; `extra` is added to the JSON (e.g. `code`) |
| `JobError` | 409 | text |
| `HttpError` (external service) | 502 | text |
| anything else | 500 | "Внутрішня помилка…" (Internal error…), the full trace in `data/logs/app.log` |

Rule: the message for the user is in Ukrainian, specific, saying what happened and what to do.

## Background jobs

- `jobs.start(kind, fn, exclusive=...)` starts a thread and returns a `Job` with an `id`. `exclusive`
  stops two identical actions from running at once (`profit-sync`, `printify-create`, `gelato-create`,
  `library-<book id>`).
- Inside `fn(job)` — `job.progress(step, percent, detail)`, and `job.share(data)` hands over what's
  already known before the job finishes (since 2026-09-20): in the snapshot this is the `partial`
  field, and the page draws it while the job is still running — this is how the text check shows
  findings while it's still working ([features/text-check.md](../features/text-check.md)).
- Interface: the route returns `{"jobId"}`, `runJob()` polls `/api/jobs/<id>` roughly every 0.4 s until
  `done`/`error`; intermediate snapshots go to `onProgress`. The fourth argument, `keepGoing()`: a page
  that no longer needs the result (the card was closed, the files changed) stops polling (the text check
  and the file checks in the card and the Order Creator).
- `UserError` in a job → `status: error` with the text; anything else → "Несподівана помилка"
  (Unexpected error) + a trace in the log. An error's `extra` (`ApiError`, e.g.
  `{"code": "printify_token"}`) goes into the snapshot as `errorExtra`, and `runJob()` puts it in
  `err.data` — just like a normal request (since 2026-09-23; it used to get lost).
- Finished jobs are kept for an hour.

## External requests

- `httpc.request()` retries on 429/5xx and a dropped connection (with a pause, `Retry-After` for 429) —
  but a request that **creates something** (POST) is only retried when it certainly did nothing: the
  connection was refused, the address wasn't found, or it got a 429 or 503. After a timeout, a
  connection dropped mid-response, or 500/502/504 — no: a second attempt could create a second image,
  product, or order (the 2026-09-22 audit). A POST that only reads (searching Gelato orders, a new Etsy
  token) is marked `idempotent=True`.
- `HttpError.ambiguous = True` means: the request may have done its work on the service (timeout, drop,
  a reply cut short while it was read — `IncompleteRead`, an SSL error — or 500/502/504; until the
  2026-09-26 audit a cut-short reply escaped as a plain crash, without the "don't resend" warning). For creating a product/order/draft, that's a signal to **not retry**, and to ask the
  owner to check the service instead.
- Printify's and Gelato's errors are read by one shared function (`httpc.human()`): the same wording for
  401/403/404/429/4xx/5xx, and `extra` carries `upstream` (the printer's status) and `ambiguous`.
  Printer call logs — `httpc.audit_log()`.
- Long lists (Etsy, Printify, Gelato orders) come back as `httpc.Listing`: `complete = False` when the
  list stopped at its own cap — then the sync warns, and the archive doesn't treat that list as fresh.

## Settings and files

- `core.settings` — non-secret settings in `data/settings.json`, merged with `DEFAULT_SETTINGS`
  (`get()`, `section()`, `update()`, `replace_section()`, `drop_section()`).
- `write_json()` writes atomically (a temp file → fsync → replace) and keeps a `.bak` copy; if the copy
  fails, the write still goes through, with a warning in the log (`.bak` is now older).
  `replace_file()` — the move over a file Windows may hold for a moment (antivirus, the indexer, a picture
  open in a viewer), tried a few times; the Workshop's pictures are written through it too.
- `read_json()` reads `.bak` only on a **damaged** file; a file that's **missing** stays missing — the
  `.bak` of a deleted file is never read (since 2026-09-23: it used to bring back a state the program or
  a test had cleared).
- Logs: `data/logs/app.log`, `printify.log`, `gelato.log` (rotated every 2 MB). `setup_logging()` only
  makes the `logs` folder (since 2026-09-23; the other data folders are made by `ensure_dirs()` in
  Book Studio's `main()`), so the mockups' data folder holds nothing of Book Studio's.
- Two switches from the environment: `core.SAMPLE` (the preview server: no key is stored or offered) and
  `core.SANDBOX` (the preview and the tests, since 2026-09-26: the [Workshop](../features/workshop.md) touches
  nothing of the owner's — its books, Downloads, clipboard and Recycle Bin are folders in the data folder, F8 isn't
  taken, no window opens). `core.PIPELINE_DIR` / `core.WORKSHOP_BOOKS` — the book pipeline and its books.

## Where in the code

- [app/studio/server.py](../../app/studio/server.py) — `route()`, `ROUTES`, `Request`, `Request.int_param()`, `Response`, `_Handler`, `ApiError`, `_index_html()`, `_State`, `_ping()`, `json_response()`, `file_response()`, `html_response()`
- [app/studio/jobs.py](../../app/studio/jobs.py) — `Jobs`, `Job`, `Job.progress()`, `Job.share()`, `Job.snapshot()` (`errorExtra`), `UserError`, `JobError`
- [app/studio/httpc.py](../../app/studio/httpc.py) — `request()`, `request_json()`, `human()`, `audit_log()`, `HttpError`, `Listing`, `RETRY_STATUSES`, `_NOT_SENT`
- [app/studio/core.py](../../app/studio/core.py) — `Settings`, `DEFAULT_SETTINGS`, `write_json()`, `replace_file()`, `read_json()`, `setup_logging()`, `data_path()`, `SAMPLE`, `SANDBOX`, `PIPELINE_DIR`, `WORKSHOP_BOOKS`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `api()`, `runJob()`, `upload()`, `media()`

## Related

- [Routes](api-routes.md) · [Data](data.md) · [Launch](runtime.md) · [Security](../security.md)
