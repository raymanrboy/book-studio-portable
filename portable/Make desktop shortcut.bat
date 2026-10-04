@echo off
rem Puts a "Book Studio Portable" shortcut on the desktop (pointing to this folder, wherever it is now).
set "BS=%~dp0"
"%BS%runtime\python\python.exe" "%BS%Book Studio\app\tools\make_shortcut.py"
pause
