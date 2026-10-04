@echo off
rem Book Studio Portable: starts the program with the Python that travels in runtime\ (nothing to install).
set "BS=%~dp0"
set "PY=%BS%runtime\python\pythonw.exe"
if not exist "%PY%" (
  echo runtime\python is missing - the portable folder is incomplete.
  pause
  exit /b 1
)
start "" "%PY%" "%BS%Book Studio\app\Book Studio.pyw"
rem The first start: the "Book Studio" shortcut is made here and on the desktop, then these launchers are hidden (only the shortcut stays in view).
if not exist "%BS%Book Studio.lnk" "%BS%runtime\python\python.exe" "%BS%Book Studio\app\tools\make_shortcut.py" --tidy
