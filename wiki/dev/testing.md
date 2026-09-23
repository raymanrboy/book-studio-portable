---
title: Тести
type: dev
updated: 2026-09-23
code:
  - app/tests/
---
# Тести

> 209 тестів на стандартному `unittest`. Жодних справжніх запитів і акаунтів: сервіси підмінені,
> дані — **завжди** у новій тимчасовій папці (набір тестів забирає `BOOK_STUDIO_DATA` собі, хай там
> що було), покупці — вигадані. Запускати після кожної зміни.

## Запуск

З папки `app`:
```
python -m unittest discover -s tests
```
З кореня репозиторію:
```
python -m unittest discover -s app/tests -t app
```
Змінна `PYTHONDONTWRITEBYTECODE=1` не дає засмічувати папки `__pycache__`.
Перевірка вікі входить у тести (`test_wiki.py`), але її можна запускати й окремо:
`python app/tools/wiki_check.py`.

## Як влаштовано

- `tests/__init__.py` до будь-якого імпорту ставить `BOOK_STUDIO_DATA` у нову тимчасову папку і стирає
  її після тестів — справжня `app/data` не зачіпається. Кожен тестовий модуль починає з
  `from tests import __init__`.
  **Безумовно** (з 22.09.2026): раніше вже задану `BOOK_STUDIO_DATA` тести приймали як є — а вони
  чистять цілі папки (`shutil.rmtree(archive.ROOT)`), тож запуск з налаштованої оболонки міг стерти
  справжній архів. Знайшов аудит; перевіряє `TestsNeverRunOnRealData` у `test_orders.py`.
- **Printify** підмінюється `FakePrintify` (у пам'яті: завантаження, продукти, Master, замовлення) через
  `mock.patch.object(printify, "call", …)`; справжній `_check()` при цьому працює — тест ловить
  заборонені шляхи.
- **Gelato** — підміна `gelato.call`, тунель — `FileTunnel.start`, `registry.keep`.
- **Etsy** — підміна `etsy.tokens`, `etsy.fetch_all_receipts`, `httpc.request_json`.
- **Архів замовлень** — час підставляється параметром `now` у `archive.refresh()`, факти про
  замовлення — підміною `archive._facts`; фонове готування прев'ю (`_warm_previews`) вимкнене, щоб
  не тримало файли відкритими під час видалення.
- Відкриття браузера — `mock.patch("webbrowser.open")`.
- `golden_profit.json` — вигадані чеки й замовлення з результатами оригінального Profit Calculator
  (паритет до цента).
- Зображення створюються на льоту (Pillow, маленькі розміри), розміри Printify у тестах підмінено.

## Правила

- Нова поведінка — новий тест; назва тесту описує поведінку англійською
  (`test_dropped_copies_are_moved_not_copied`).
- Лише вигадані імена, адреси, номери чеків (формат `41000000xx`). Справжні дані покупців у репозиторій
  не потрапляють (одного разу справжню адресу знайшли й замінили до першого push).
- Тест не повинен мережитись; якщо з'явився новий зовнішній виклик — підмініть його.
- Порядок тестів не має значення; стан налаштувань відновлюється в `tearDown`. Щоб скинути файл
  стану, досить видалити сам файл: `.bak` видаленого файлу більше не читається (з 23.09.2026).
- Кроки журналу відправки перевіряються «ці кроки в такому порядку» (`assert_steps()`), а не точним
  списком: новий крок не ламає десяток тестів. Реальних пауз (`time.sleep`) для різного часу немає —
  час запису підставляється.
- Порядок шарів інтерфейсу й розміри прев'ю перевіряються прямо з файлів сторінок (`SharedNumbers`):
  тестів у браузері немає, тож поведінку сторінок перевіряє людина чи агент на
  [сервері перегляду](preview.md).

## Набори

| Файл | Класи |
|---|---|
| [test_profit.py](../../app/tests/test_profit.py) | `ProfitParity`, `FeeRules`, `NameMatching` |
| [test_states.py](../../app/tests/test_states.py) | `NormalOrdersUnchanged`, `EtsyStates`, `Replacement`, `ProviderCancellations`, `PickerStages`, `SeveralPrintOrdersForOneReceipt` (чек з двома замовленнями друку), `SentStage`, `GelatoTracking`, `IncrementalSync`, `StateApi` |
| [test_library_creator.py](../../app/tests/test_library_creator.py) | `TextJson`, `FolderScan`, `PrintifyValidation` (у т. ч. новіша перевірка папки зупиняє старішу), `GelatoValidation`, `ReplacePage` (заміна однієї сторінки, «Повернути» після перезапуску, дві заміни за секунду, заборона заміни під час відправки — і коли папку відправляють у дві друкарні одразу, що саме дозволено записувати), `NothingIsLostWhenAWriteFails`, `JsonFiles` (`.bak` і видалений файл), `SafetyRails` (у т. ч. POST, що міг дійти, не повторюється; обидві друкарні читають помилку однаково) |
| [test_flows.py](../../app/tests/test_flows.py) | `PrintifyDraftFlow` (у т. ч. дві книги — одне замовлення з двома позиціями; номер чека окремим полем; незаписаний облік — попередження), `GelatoDraftFlow` (у т. ч. дві книги — одна чернетка з двома товарами; невідомий результат лишає посилання; текст про довжину — один), `CreatorStartsEmpty`, `DroppedFolders` (у т. ч. папка для бібліотеки, кожна книга — своя дитина), `OpenUrlGuard`, `ProfitSyncFlow`, `EtsyOAuth` |
| [test_orders.py](../../app/tests/test_orders.py) | `PrinterRule`, `ArrangePages`, `GelatoLength`, `PreparationGuide`, `PartialBookImport`, `SyncOnlyAtStartOrByHand`, `DevToolsKeepOffRealData` (сервер перегляду не пише у справжню папку й не бере ключів), `TestsNeverRunOnRealData`, `SharedNumbers` (шари інтерфейсу, розміри прев'ю) |
| [test_archive.py](../../app/tests/test_archive.py) | `Storing`, `Removing` (у т. ч. застарілий список друкарні нічого не доводить), `OnlyWhatWentToPrint` (у т. ч. «вже в друкарні» після перезапуску), `ReprintMark`, `PrintifyReprint`, `GelatoReprint` (у т. ч. попередження, коли друкарня прийняла, а облік не записався), `PreviewCache` (прибирання кешу, замки, зум) |
| [test_textcheck.py](../../app/tests/test_textcheck.py) | `Words`, `BuyerFields`, `NameRules`, `Assign`, `PageIssues`, `WholeCheck` (модель — імітація: «читає» те, що тест «надрукував»), `WhileItRuns` (розворот іде на звірку, не чекаючи останнього читання; знахідки віддаються під час перевірки), `Prescan` (швидкий огляд сторінок: намальований текст проти намальованої ілюстрації, сторінки-малюнки до моделі не потрапляють, помилка ознаки — перевіряється друга половина розвороту), `Passport` (ім'я лише цілим словом і лише там, де паспорт мав `{Name}`; попередній показ), `BooksOfOneOrder` (дві книги одного чека не глушать перевірок одна одної), `OllamaAndRoutes` |
| [test_wiki.py](../../app/tests/test_wiki.py) | `WikiMatchesCode` |

## Де в коді

- [app/tests/__init__.py](../../app/tests/__init__.py) — тимчасова папка даних
- [app/tests/test_flows.py](../../app/tests/test_flows.py) — `FakePrintify`, `png()`, `assert_steps()`
- [app/tools/wiki_check.py](../../app/tools/wiki_check.py) — `check()`

## Пов'язане

- [Безпека](../security.md) · [Перегляд інтерфейсу](preview.md) · [Правила вікі](wiki-rules.md)
