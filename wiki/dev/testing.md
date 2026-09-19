---
title: Тести
type: dev
updated: 2026-09-19
code:
  - app/tests/
---
# Тести

> 117 тестів на стандартному `unittest`. Жодних справжніх запитів і акаунтів: сервіси підмінені,
> дані — у тимчасовій папці, покупці — вигадані. Запускати після кожної зміни.

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

- `tests/__init__.py` до будь-якого імпорту ставить `BOOK_STUDIO_DATA` у тимчасову папку і стирає її
  після тестів — справжня `app/data` не зачіпається. Кожен тестовий модуль починає з
  `from tests import __init__`.
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
- Порядок тестів не має значення; стан налаштувань відновлюється в `tearDown`.

## Набори

| Файл | Класи |
|---|---|
| [test_profit.py](../../app/tests/test_profit.py) | `ProfitParity`, `FeeRules`, `NameMatching` |
| [test_states.py](../../app/tests/test_states.py) | `NormalOrdersUnchanged`, `EtsyStates`, `Replacement`, `ProviderCancellations`, `PickerStages`, `SentStage`, `GelatoTracking`, `IncrementalSync`, `StateApi` |
| [test_library_creator.py](../../app/tests/test_library_creator.py) | `TextJson`, `FolderScan`, `PrintifyValidation`, `GelatoValidation`, `SafetyRails` |
| [test_flows.py](../../app/tests/test_flows.py) | `PrintifyDraftFlow`, `GelatoDraftFlow`, `CreatorStartsEmpty`, `DroppedFolders`, `OpenUrlGuard`, `ProfitSyncFlow`, `EtsyOAuth` |
| [test_orders.py](../../app/tests/test_orders.py) | `PrinterRule`, `ArrangePages`, `GelatoLength`, `PreparationGuide`, `PartialBookImport`, `SyncOnlyAtStartOrByHand` |
| [test_archive.py](../../app/tests/test_archive.py) | `Storing`, `Removing`, `OnlyWhatWentToPrint`, `ReprintMark`, `PrintifyReprint`, `GelatoReprint` |
| [test_textcheck.py](../../app/tests/test_textcheck.py) | `Words`, `BuyerFields`, `NameRules`, `Assign`, `PageIssues`, `WholeCheck` (модель — імітація: «читає» те, що тест «надрукував»), `Passport`, `OllamaAndRoutes` |
| [test_wiki.py](../../app/tests/test_wiki.py) | `WikiMatchesCode` |

## Де в коді

- [app/tests/__init__.py](../../app/tests/__init__.py) — тимчасова папка даних
- [app/tests/test_flows.py](../../app/tests/test_flows.py) — `FakePrintify`, `png()`
- [app/tools/wiki_check.py](../../app/tools/wiki_check.py) — `check()`

## Пов'язане

- [Безпека](../security.md) · [Перегляд інтерфейсу](preview.md) · [Правила вікі](wiki-rules.md)
