@echo off
echo Запуск WebSocket сервера для Cursor MCP...
echo Для прекращения работы нажмите Ctrl+C

REM Проверка директорий
if not exist "logs" mkdir logs

REM Проверка наличия Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Ошибка: Node.js не установлен. Пожалуйста, установите Node.js.
    echo Скачать Node.js можно здесь: https://nodejs.org/
    echo Запись ошибки в лог...
    echo %date% %time% - Node.js не установлен >> logs\mcp_error.log
    pause
    exit /b 1
)

echo Node.js найден: 
node --version

REM Проверка наличия модуля ws
node -e "try { require('ws'); console.log('Модуль ws установлен'); } catch(e) { console.log('Модуль ws не найден'); process.exit(1); }"
if %ERRORLEVEL% NEQ 0 (
    echo Установка модуля ws...
    echo %date% %time% - Установка модуля ws >> logs\mcp_install.log
    npm install ws --no-fund
    if %ERRORLEVEL% NEQ 0 (
        echo Ошибка установки модуля ws.
        echo %date% %time% - Ошибка установки модуля ws >> logs\mcp_error.log
        pause
        exit /b 1
    )
)

REM Проверка наличия директории assets
if not exist "app\static\assets" mkdir app\static\assets
echo Директория для ассетов проверена: app\static\assets

REM Проверка конфигурации MCP
if not exist "mcp\figma\mcp_config.json" (
    echo Ошибка: Файл mcp_config.json не найден.
    echo %date% %time% - Файл mcp_config.json не найден >> logs\mcp_error.log
    pause
    exit /b 1
)

echo Все проверки пройдены успешно.
echo Сервер запускается на http://localhost:8080
echo Для подключения Figma плагина используйте websocket URL: ws://localhost:8080
echo Детали логирования доступны в: logs\mcp.log

echo %date% %time% - Запуск MCP WebSocket сервера >> logs\mcp.log
node mcp/figma/socket.js 2>> logs\mcp_error.log

pause 