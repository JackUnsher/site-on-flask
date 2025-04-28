@echo off
echo Запуск WebSocket сервера для Cursor MCP...
echo Для прекращения работы нажмите Ctrl+C

REM Проверка наличия Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Ошибка: Node.js не установлен. Пожалуйста, установите Node.js.
    echo Скачать Node.js можно здесь: https://nodejs.org/
    pause
    exit /b 1
)

REM Проверка наличия модуля ws
node -e "try { require('ws'); console.log('OK'); } catch(e) { console.log('ERROR'); process.exit(1); }" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Установка модуля ws...
    npm install ws --no-fund
    if %ERRORLEVEL% NEQ 0 (
        echo Ошибка установки модуля ws.
        pause
        exit /b 1
    )
)

echo Сервер запускается на http://localhost:8080
echo Для подключения Figma плагина используйте websocket URL: ws://localhost:8080

node mcp/figma/socket.js

pause 