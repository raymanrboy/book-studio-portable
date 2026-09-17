---
title: Встановлення, запуск, GitHub
type: dev
updated: 2026-09-17
code:
  - app/tools/make_shortcut.py
  - app/requirements.txt
---
# Встановлення, запуск, GitHub

## Що потрібно

- Windows 10/11, Microsoft Edge (або Chrome).
- Python 3.11+ (на вроцлавському ПК — 3.14, `C:\Users\Roman\AppData\Local\Programs\Python\Python314`).
- Пакети: `python -m pip install -r app/requirements.txt` (Pillow, img2pdf, cryptography).
- `app/bin/cloudflared.exe` — для тимчасових посилань Gelato; **не в git**, на новому ПК його треба
  покласти вручну (офіційний реліз Cloudflare).

## Запуск

- Ярлик **Book Studio** на робочому столі. Немає ярлика або програму перенесли —
  `python app/tools/make_shortcut.py`.
- Не запускається — `app/Запуск з консоллю.bat` покаже помилку; також `app/data/logs/startup-error.txt`.
- Докладно — [architecture/runtime.md](../architecture/runtime.md).

## Інший комп'ютер

- Код — з GitHub (див. нижче). Дані — скопіювати `app/data`.
- Ключі у `vault.json` зашифровані DPAPI для конкретного користувача Windows: на іншому ПК вони не
  розшифруються → ввести ключі заново в Налаштуваннях, Etsy підключити «лінком доступу».
- **Після перенесення 17.09.2026** (код переїхав у `app/`): у старій копії проєкту перенести `data/` і
  `bin/` у `app/` і заново створити ярлик.

## GitHub

- Приватний репозиторій **raymanrboy/book-studio**, гілка `main`, remote `origin`.
- GitHub CLI на вроцлавському ПК розпакований без інсталятора і **не в PATH**:
  `C:\Users\Roman\AppData\Local\Programs\GitHubCLI\bin\gh.exe` (вхід — `raymanrboy`).
- Git не налаштований глобально на gh; push з Git Bash:
  ```
  git -c credential.helper= -c "credential.helper=!'/c/Users/Roman/AppData/Local/Programs/GitHubCLI/bin/gh.exe' auth git-credential" push
  ```
  (без цього відкриється вікно Git Credential Manager).
- Комітити й пушити — **лише коли власник попросить**. Повідомлення комітів — англійською.
- **Коли просить — комітити все, що є в робочій папці, разом** (і зміни інших сесій), без розділення
  на «свої / чужі»: власнику так простіше, а історія версій однаково в git (прохання 17.09.2026).
  Перед комітом лише перевірити, що не потрапляють ключі й справжні дані покупців.
- У репозиторій не потрапляють `app/data/`, `app/bin/`, `__pycache__`, `.obsidian/`, локальні
  налаштування Claude Code.

## Obsidian (необов'язково)

Вікі — звичайні Markdown-файли. Якщо відкрити папку `wiki` як сховище Obsidian, працюють посилання між
сторінками і граф; посилання на код (`../app/...`) Obsidian не відкриває — вони для агентів.

## Де в коді

- [app/tools/make_shortcut.py](../../app/tools/make_shortcut.py) — `main()`
- [app/studio/desktop.py](../../app/studio/desktop.py) — `find_browser()`
- [app/studio/tunnel.py](../../app/studio/tunnel.py) — `CLOUDFLARED`

## Пов'язане

- [Запуск](../architecture/runtime.md) · [Тести](testing.md) · [Дані](../architecture/data.md)
