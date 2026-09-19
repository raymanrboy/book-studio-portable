---
title: Запуск і завершення програми
type: architecture
updated: 2026-09-19
code:
  - app/Book Studio.pyw
  - app/Запуск з консоллю.bat
  - app/studio/main.py
  - app/studio/desktop.py
  - app/tools/make_shortcut.py
---
# Запуск і завершення програми

> Ярлик на робочому столі → `app/Book Studio.pyw` → сервер на `127.0.0.1:47821` → окреме вікно Edge.
> Коли вікно закрите, програма дочікується фонових робіт і сама завершується.

## Послідовність запуску

1. **`Book Studio.pyw`** (без консолі, `pythonw.exe`): перевіряє пакети Pillow, img2pdf, cryptography.
   Бракує — показує вікно з командою `pip install`. Падіння під час старту записується в
   `app/data/logs/startup-error.txt` і показується вікном.
2. **`main()`**: створює папки даних, вмикає журнал (`data/logs/app.log`).
3. Якщо програма вже запущена (відповідає `/api/ping`) — просто відкриває ще одне вікно і виходить.
4. Імпортує всі модулі з маршрутами (`archive`, `creator`, `etsy`, `gelato`, `library`, `orders`,
   `printify`, `profit`, `sendlog`, `settings_api`, `textcheck`, `tunnel`) — саме імпорт реєструє маршрути.
5. Прибирання: старі тимчасові папки Gelato (`cleanup_stale()`), залишки старої форми Order Creator
   (`forget_old_form()`), перетягнуті файли минулого сеансу (`clear_drops()`).
6. **Сервер** на порту 47821 (`DEFAULT_PORT`). Порт зайнятий → випадковий вільний порт і попередження
   в Налаштуваннях Etsy (адреса повернення OAuth містить порт).
7. **Одна автоматична синхронізація замовлень** — `startup_sync()` (далі лише кнопкою,
   див. [правило](../rules/sync-policy.md)). Паралельно у фоні — перевірка
   [архіву замовлень](../features/archive.md) (`archive.refresh_quietly()`: книги, чиї 14 днів минули,
   видаляються); вона ж повторюється після кожної синхронізації. Ще у фоні — прибирання кешу прев'ю
   (`images.prune_cache_quietly()`: не потрібні 21 день).
8. **Вікно**: Edge або Chrome з `--app=<адреса>`, окремим профілем `data/window-profile`, розміром
   1480×940. Немає ні Edge, ні Chrome — відкривається звичайний браузер.

## Як програма розуміє, що вікно закрите

- Сторінка кожні 20 с шле `/api/app/heartbeat`, а при закритті — `sendBeacon` на `/api/app/bye`.
- Цикл у `main()` вважає вікно закритим, коли:
  - було «bye» і за 6 с не прийшло нове серцебиття (перезавантаження сторінки — не закриття);
  - процес вікна завершився і 12 с не було серцебиття;
  - запасний браузер без процесу мовчить 10 хвилин.
- Перед виходом чекає завершення фонових задач (`jobs.any_running()`; перевірку тексту — ні, вона лише читає) і тимчасових посилань Gelato
  (`tunnel.registry.active()`), потім закриває посилання й сервер.

## Режим без вікна (розробка)

`main(["--no-window", "--port", "47890"])` — лише сервер; так працює
[app/tools/dev_server.py](../../app/tools/dev_server.py) ([dev/preview.md](../dev/preview.md)).

## Ярлик

[make_shortcut.py](../../app/tools/make_shortcut.py) створює `Book Studio.lnk` на справжньому робочому
столі (шлях питає у Windows): `pythonw.exe "…\app\Book Studio.pyw"`, робоча папка `app`, іконка
`app/web/img/icon.ico`. Після перенесення програми ярлик треба створити заново.

## Де в коді

- [app/Book Studio.pyw](<../../app/Book Studio.pyw>) — `_message()`
- [app/studio/main.py](../../app/studio/main.py) — `main()`, `_running_instance()`
- [app/studio/desktop.py](../../app/studio/desktop.py) — `open_app_window()`, `find_browser()`
- [app/studio/server.py](../../app/studio/server.py) — `start()`, `_heartbeat()`, `_bye()`, `_State`
- [app/studio/tunnel.py](../../app/studio/tunnel.py) — `cleanup_stale()`
- [app/studio/creator.py](../../app/studio/creator.py) — `forget_old_form()`, `clear_drops()`
- [app/studio/profit.py](../../app/studio/profit.py) — `startup_sync()`
- [app/studio/archive.py](../../app/studio/archive.py) — `refresh_quietly()`
- [app/studio/images.py](../../app/studio/images.py) — `prune_cache_quietly()`, `prune_cache()`
- [app/web/js/app.js](../../app/web/js/app.js) — `heartbeat()`, `boot()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `markOffline()`
- [app/tools/make_shortcut.py](../../app/tools/make_shortcut.py) — `main()`

## Пов'язане

- [Сервер](server.md) · [Інтерфейс](frontend.md) · [Встановлення](../dev/setup.md)
