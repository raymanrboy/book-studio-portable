---
title: Etsy — лише читання
type: integration
updated: 2026-09-23
code:
  - app/studio/etsy.py
---
# Etsy

> Etsy Open API v3, **лише читання** (`shops_r transactions_r`): чеки магазину і лістинги.
> Вхід в Etsy — тільки на київському комп'ютері ([безпека](../security.md)).

## Ключі й вхід

- **Ключі застосунку**: Keystring і Shared Secret (Etsy Developers → Your apps). Заголовок
  `x-api-key: <keystring>:<secret>`. Лише з ключами вже можна перевіряти лістинги (без входу).
- **Вхід (OAuth 2.0 + PKCE)**, два шляхи в Налаштуваннях після підтвердження «я на київському ПК»:
  1. програма запущена на київському ПК — сторінка входу відкривається там, Etsy повертає на
     `http://localhost:47821/etsy/callback` (власник так не робить: на київському ПК програми немає);
  2. **основний шлях:** програма тут — посилання копіюється і відкривається на київському ПК; браузер там перейде на
     `localhost…` (сторінка не відкриється — так і має бути), повну адресу вставляють назад.
  Адреса повернення має бути додана в Etsy Developers → Callback URLs. Посилання дійсне годину.
- **Лінк доступу** (`…?sync=<iv:tag:cipher>`) з Etsy Profit Calculator: сесія, зашифрована AES-GCM
  ключем із Shared Secret (запасний секрет — як у Profit Calculator). Найпростіший спосіб підключитися.
  Працює і навпаки: «Копіювати ключ сесії» для іншого ПК.
- **Токени** зберігаються у сховищі (`etsy_tokens`), оновлюються самі за 5 хв до закінчення.
  Etsy видає **одноразові** ключі оновлення: якщо ту саму сесію оновила інша програма (Profit
  Calculator), тут вона перестає працювати → «перенесіть сесію знову».

## Дані

- `fetch_all_receipts()` — усі оплачені чеки (включно зі скасованими/поверненими), новіші першими,
  по 100, пауза 0,12 с; з `min_last_modified` — лише змінені (інкрементна синхронізація). Не більше
  `MAX_RECEIPTS` = 20 000; більше — список позначається неповним (`httpc.Listing`) і синхронізація
  попереджає.
- `normalize_receipt()` ([profit.py](../../app/studio/profit.py)) перетворює чек: комісії, товари з
  варіаціями (персоналізація), адреса, повернення. Текст Etsy приходить з HTML-екрануванням
  (`&quot;`, `&amp;`) — `plain()` розекрановує.
- **Немає в API**: власні вкладки продавця (наприклад, «In Production»). Тому етап замовлення
  виводиться з того, чи є замовлення друку ([rules/order-stages.md](../rules/order-stages.md)).
- `fetch_listing()` — назва, стан, магазин, головне фото (одним запитом `includes=Images`).

## Помилки

`_human()` перетворює відповіді Etsy на зрозумілі повідомлення з `code: etsy_auth`, коли треба
заново підключитися. 401 при запиті → одне примусове оновлення токена і повтор. Оновлення токена —
POST, що лише читає, тож після обриву його можна повторити (`idempotent=True`).

## Де в коді

- [app/studio/etsy.py](../../app/studio/etsy.py) — `SCOPES`, `keys()`, `api_key_header()`, `start_oauth()`, `complete_oauth()`, `refresh_tokens()`, `get()`, `ensure_shop()`, `decode_session_key()`, `encode_session_key()`, `import_session()`, `fetch_listing()`, `fetch_all_receipts()`, `MAX_RECEIPTS`, `parse_listing_ref()`, `_oauth_callback()`, `port_warning()`, `_human()`
- [app/studio/profit.py](../../app/studio/profit.py) — `normalize_receipt()`, `plain()`
- [app/web/js/pages/settings.js](../../app/web/js/pages/settings.js) — `oauthFlow()`, `etsyCard()`
- Тести: [app/tests/test_flows.py](../../app/tests/test_flows.py) (`EtsyOAuth`, `OpenUrlGuard`)

## Пов'язане

- [Безпека](../security.md) · [Синхронізація](../rules/sync-policy.md) · [Налаштування](../features/settings.md)
