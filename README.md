# Сайт на Flask с админ-панелью

Этот проект представляет собой базовый шаблон для создания сайта на Flask с админ-панелью и интеграцией с Figma через MCP плагин.

## Структура проекта

```
site-on-flask/
├── app/                        # Основная папка приложения
│   ├── admin/                  # Модуль администратора
│   ├── forms/                  # Формы для сайта
│   ├── models/                 # Модели базы данных
│   ├── static/                 # Статические файлы (CSS, JS, изображения)
│   ├── templates/              # Шаблоны Jinja2
│   ├── utils/                  # Утилиты и вспомогательные функции
│   ├── views/                  # Представления (маршруты) сайта
│   └── __init__.py             # Инициализатор приложения
├── figma-plugin/               # Плагин для Figma
│   ├── manifest.json           # Манифест плагина
│   ├── code.js                 # Код плагина
│   └── ui.html                 # Интерфейс плагина
├── venv/                       # Виртуальное окружение (не включено в репозиторий)
├── .env                        # Файл переменных окружения
├── .gitignore                  # Файл для игнорирования в Git
├── config.py                   # Конфигурация приложения
├── requirements.txt            # Зависимости проекта
├── run.py                      # Скрипт запуска приложения
└── socket_server.py            # Сервер WebSocket для интеграции с Figma
```

## Установка и запуск

### Подготовка окружения

1. Клонируйте репозиторий:
   ```
   git clone <url-репозитория>
   cd site-on-flask
   ```

2. Создайте и активируйте виртуальное окружение:
   ```
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

4. Настройте переменные окружения (или отредактируйте файл .env):
   ```
   # Секретный ключ для Flask
   SECRET_KEY=your-secret-key-here
   
   # URL для базы данных
   DATABASE_URL=sqlite:///app.db
   
   # Настройки для WebSocket сервера
   WEBSOCKET_HOST=localhost
   WEBSOCKET_PORT=8765
   
   # Настройки для Figma канала
   FIGMA_CHANNEL=figma-channel
   ```

### Инициализация базы данных

1. Инициализируйте базу данных:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

2. Создайте администратора:
   ```
   flask create-admin username admin@example.com password
   ```

### Запуск приложения

1. Запустите WebSocket сервер для интеграции с Figma:
   ```
   python socket_server.py
   ```

2. В отдельном терминале запустите основное приложение:
   ```
   python run.py
   ```

3. Откройте сайт в браузере по адресу: http://localhost:5000

## Интеграция с Figma через MCP

### Установка плагина в Figma

1. Откройте Figma и перейдите в меню плагинов
2. Выберите "Плагины" -> "Разработка" -> "Новый плагин"
3. Выберите "Связать существующий плагин"
4. Выберите файл `figma-plugin/manifest.json` из этого проекта

### Использование плагина

1. Откройте документ Figma
2. Запустите плагин "Cursor MCP Plugin" из меню плагинов
3. Введите адрес WebSocket сервера (по умолчанию `ws://localhost:8765`)
4. Введите ID канала (по умолчанию `figma-channel`)
5. Нажмите "Connect"

Теперь вы можете использовать Cursor с MCP интеграцией для доступа к вашему дизайну Figma через API.

## Расширение проекта

### Добавление новых моделей

1. Создайте новую модель в директории `app/models/`
2. Импортируйте ее в `app/models/__init__.py`
3. Добавьте представления в админ-панель в `app/admin/views.py`

### Добавление новых страниц

1. Создайте Blueprint в директории `app/views/`
2. Зарегистрируйте Blueprint в `app/__init__.py`
3. Создайте соответствующие шаблоны в `app/templates/`

## Лицензия

[MIT License](LICENSE)

# мелкое изменение 
# ещё одно мелкое изменение 