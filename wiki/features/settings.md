---
title: Налаштування
type: feature
updated: 2026-09-19
code:
  - app/studio/settings_api.py
  - app/web/js/pages/settings.js
---
# Налаштування

> Мінімальна сторінка: ключі сервісів, підключення Etsy, шаблон Printify, перевірка тексту, папка даних.
> Кожен блок згорнутий в один рядок зі станом; блок, якому щось потрібно, відкривається сам.
> Тема — не тут, а в меню внизу бокової панелі.

## Блоки (`#/settings[/<блок>]`)

- **Знайдено ключі з попередніх програм** (лише якщо є що переносити) — «Перенести»: ключі з
  Order Creator Printify (`.local/*.dpapi`) і Etsy Profit Calculator (`.env.local`/`.env`), кеш
  завантажень Printify. Шукаються на робочому столі поруч із папкою Book Studio.
- **Etsy**: бракує ключа → поля Keystring / Shared Secret. Не підключено → «лінк доступу» з Profit
  Calculator (`…/?sync=…`) або «Увійти в Etsy (лише з київського ПК)» — див. [integrations/etsy.md](../integrations/etsy.md).
  Підключено → назва магазину і «Відключити». «Подробиці»: збережені ключі, адреса повернення
  (Callback URL), копіювання ключа сесії для іншого ПК.
- **Printify**: токен; шаблон (Master) і «24 стор.»; кнопка вибору шаблону — лише коли його ще немає;
  перевірка зв'язку.
- **Gelato**: ключ; три формати і «28 або 30 стор.»; перевірка зв'язку.
- **Перевірка тексту** (з 19.09.2026): вмикач «Перевіряти текст сторінок у картці замовлення», модель
  (іконка вибору — коли в Ollama їх кілька, що бачать картинки), «у відеокарті», «Перевірити зв'язок»;
  Ollama не запущена → «Запустити» (програма й сама запускає її перед перевіркою). Блок малюється
  одразу з налаштувань («перевірка стану…»), стан Ollama дотягується окремим запитом — Налаштування
  не чекають її (на Windows вимкнена Ollama відповідає «ні» лише через 2 с).
  Докладно — [text-check.md](text-check.md).
- **Дані програми**: шлях до `app/data` і кнопка «Відкрити».

Технічні значення (позиції Master, розміри artwork, product UID, курс EUR→USD, час життя посилання)
навмисно не показуються і не редагуються з інтерфейсу — рішення власника. Маршрути
`/api/settings/gelato` і `/api/settings/printify` лишилися, але інтерфейс їх не викликає.

## Ключі

Поле пароля → `POST /api/secrets` → `Vault` (DPAPI). Назад приходить лише «збережено» і останні
4 символи. Імена: `etsy_keystring`, `etsy_shared_secret`, `printify_token`, `gelato_api_key`.

## Вибір Master (Printify)

`pickMaster()`: магазин → список продуктів або ID/посилання → аналіз (`analyze_master()`: позиції
cover і page_1…page_N, варіанти, розміри) → «Зробити Master» (підтвердження). Master лише читається.

## Де в коді

- [app/web/js/pages/settings.js](../../app/web/js/pages/settings.js) — `mount()`, `card()`, `details()`, `secretField()`, `legacyCard()`, `etsyCard()`, `printifyCard()`, `gelatoCard()`, `dataCard()`, `textcheckCard()`, `loadTextcheck()`, `saveTextcheck()`, `oauthFlow()`, `pickMaster()`, `SECRET_LABELS`
- [app/studio/settings_api.py](../../app/studio/settings_api.py) — `integrations()`, `_settings()`, `_secret()`, `_open_url()`, `_legacy_values()`, `legacy_sources()`, `_legacy_import()`, `EDITABLE_SECRETS`, `DESKTOP`
- [app/studio/printify.py](../../app/studio/printify.py) — `analyze_master()`, `_save_master()`
- [app/studio/etsy.py](../../app/studio/etsy.py) — `status()`, `import_session()`
- [app/studio/textcheck.py](../../app/studio/textcheck.py) — `status()`, `start_ollama()`, `_save_settings()`, `_start()`

## Пов'язане

- [Безпека](../security.md) · [Etsy](../integrations/etsy.md) · [Printify](../integrations/printify.md) · [Gelato](../integrations/gelato.md)
