@echo off
chcp 65001 >nul
title Book Studio (діагностика)
cd /d "%~dp0"
echo Запуск Book Studio з консоллю — тут буде видно помилки, якщо щось піде не так.
echo.
python "Book Studio.pyw"
echo.
pause
