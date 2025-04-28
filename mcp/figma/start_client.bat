@echo off
echo Запуск Python клиента для Cursor MCP...
echo Для прекращения работы нажмите Ctrl+C

REM Проверка наличия Python
where py >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Ошибка: Python не установлен. Пожалуйста, установите Python.
    echo Скачать Python можно здесь: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Проверка наличия модуля websocket-client
py -c "import websocket" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Установка модуля websocket-client...
    py -m pip install websocket-client --user
    if %ERRORLEVEL% NEQ 0 (
        echo Ошибка установки модуля websocket-client.
        pause
        exit /b 1
    )
)

echo Клиент запускается...
echo Подключение к ws://localhost:8080 с каналом cursor_mcp
echo.

py mcp/figma/cursor_handler.py %*

pause 