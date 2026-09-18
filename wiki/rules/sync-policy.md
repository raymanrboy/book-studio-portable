---
title: Коли оновлюються замовлення
type: rule
updated: 2026-09-18
code:
  - app/studio/profit.py
  - app/web/js/order-bits.js
---
# Коли оновлюються замовлення

> **Лише двічі: один раз автоматично при запуску програми і далі тільки кнопкою оновлення.**
> Сторінки самі нічого не завантажують (вимога власника, 15.09.2026).

## Як це працює

- При запуску `main()` викликає `startup_sync()`: якщо є Etsy або Printify, запускається фонова
  задача `profit-sync`.
- Сторінка «Замовлення» і вибір замовлення в Order Creator при відкритті питають `GET /api/profit/sync`:
  якщо синхронізація йде — показують її кроки й оновлюють список, коли вона закінчиться.
- Кнопка «Оновити замовлення» → `POST /api/profit/sync`; якщо синхронізація вже йде, сервер повертає
  її ж (`jobId`), а не запускає другу.
- Між запусками показується останній знімок (`data/profit/snapshot.json`) з часом «Оновлено … тому».

## Що робить синхронізація (`_sync()`)

1. **Etsy**: лише змінені чеки з часу попередньої синхронізації (з перекриттям 1 год); повне
   перечитування — на першій синхронізації, раз на тиждень, за іншого магазину або на вимогу (`full`).
   Помилка Etsy = помилка всієї синхронізації.
2. **Printify**: усі замовлення магазину (разом із трек-номерами). Помилка → попередження, лишаються
   попередні дані.
3. **Gelato**: усі замовлення (замовлення й чернетки). Пошук Gelato трек-номерів не віддає, тож для
   відправлених замовлень програма читає кожне окреме замовлення (`attach_shipments()`): **один раз**
   на замовлення, повторно — лише поки трек-номера немає і статус змінився; знайдені трек-номери
   переносяться з попереднього знімка; не більше 60 читань за одне оновлення. Не вдалося прочитати →
   попередження, спроба при наступному оновленні. Помилка пошуку → попередження, попередні дані.
4. Збереження знімка і перерахунок кешу подання (`cached_view()`).
5. Перевірка [архіву замовлень](../features/archive.md) (`archive.refresh_quietly()`): з новими
   етапами й статусами друкарень видаляються книги, чиї 14 днів минули. Сама по собі нічого не
   завантажує — лише читає щойно збережений знімок.

Кеш подання оновлюється за лічильником записів `_writes` (плюс час зміни файлів): два записи в один
«тік» годинника Windows мають однаковий час зміни — баг, виправлений 16.09.2026.

## Де в коді

- [app/studio/profit.py](../../app/studio/profit.py) — `startup_sync()`, `_start_sync()`, `_sync_state()`, `_sync()`, `merge_receipts()`, `cached_view()`, `_save()`, `FULL_SYNC_EVERY`, `SYNC_OVERLAP`
- [app/studio/gelato.py](../../app/studio/gelato.py) — `attach_shipments()`, `TRACKING_READS`
- [app/web/js/order-bits.js](../../app/web/js/order-bits.js) — `syncOrders()`, `runningSync()`, `watchSync()`
- [app/web/js/pages/orders.js](../../app/web/js/pages/orders.js) — `refresh()`
- [app/web/js/pages/creator.js](../../app/web/js/pages/creator.js) — `refresh()`
- [app/studio/main.py](../../app/studio/main.py) — `main()`
- [app/studio/archive.py](../../app/studio/archive.py) — `refresh_quietly()`
- Тести: [app/tests/test_orders.py](../../app/tests/test_orders.py) (`SyncOnlyAtStartOrByHand`), [app/tests/test_states.py](../../app/tests/test_states.py) (`IncrementalSync`)

## Пов'язане

- [Етапи](order-stages.md) · [Etsy](../integrations/etsy.md) · [Рішення](../decisions.md)
