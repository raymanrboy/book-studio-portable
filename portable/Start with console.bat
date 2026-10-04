@echo off
rem The same start, but with a console window: errors stay on the screen.
set "BS=%~dp0"
"%BS%runtime\python\python.exe" "%BS%Book Studio\app\Book Studio.pyw"
pause
