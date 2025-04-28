# Cloud Mining Platform

Платформа для облачного майнинга с личным кабинетом пользователя и административной панелью.

## Содержание

- [Требования](#требования)
- [Установка](#установка)
- [Запуск](#запуск)
- [Структура проекта](#структура-проекта)
- [Технологии](#технологии)
- [Функциональность](#функциональность)
- [Дизайн](#дизайн)
- [Тестирование](#тестирование)
- [Разработка](#разработка)

## Требования

- Python 3.9+
- Flask 2.0+
- SQLAlchemy
- Node.js 14+ (для работы с Figma MCP)
- Postgres/SQLite

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd site-on-flask
```

### 2. Настройка виртуального окружения

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корневой директории:

```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///app.db
UPLOAD_FOLDER=app/static/uploads
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-password
MAIL_USE_TLS=True
MAIL_DEFAULT_SENDER=your-email@example.com
```

### 5. Инициализация базы данных

```bash
flask db init
flask db migrate
flask db upgrade
```

### 6. Создание административного пользователя

```bash
flask create-admin
```

## Запуск

### Запуск в режиме разработки

```bash
flask run
```

Приложение будет доступно по адресу [http://127.0.0.1:5000](http://127.0.0.1:5000)

### Запуск с помощью Gunicorn (для production)

```bash
gunicorn wsgi:app
```

## Структура проекта

```
site-on-flask/
├── app/
│   ├── __init__.py          # Инициализация приложения
│   ├── models/              # Модели данных
│   ├── forms/               # Формы
│   ├── views/               # Представления (маршруты)
│   ├── static/              # Статические файлы (CSS, JS, изображения)
│   │   ├── css/
│   │   ├── js/
│   │   └── assets/
│   ├── templates/           # HTML-шаблоны
│   │   ├── main/
│   │   ├── admin/
│   │   ├── auth/
│   │   └── profile/
│   └── utils/               # Вспомогательные функции
├── migrations/              # Миграции базы данных
├── docs/                    # Документация
├── tests/                   # Тесты
├── mcp/                     # Интеграция с Figma MCP
├── app.py                   # Точка входа
├── config.py                # Конфигурация
├── requirements.txt         # Зависимости Python
└── README.md                # Документация
```

## Технологии

- **Backend**: Flask, SQLAlchemy, Alembic
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **База данных**: SQLite (разработка), PostgreSQL (продакшн)
- **Дизайн**: Figma + MCP (Material Component Plugin)
- **Деплой**: Docker, Gunicorn, Nginx

## Функциональность

### Публичная часть

- Главная страница с информацией о сервисе
- Страница с тарифами
- Регистрация и авторизация
- FAQ и контактная информация

### Личный кабинет пользователя

- Дашборд с основной информацией и статистикой
- Управление контрактами на майнинг
- Просмотр транзакций и заработка
- Вывод средств
- Просмотр камер майнинг-фермы
- Настройки профиля и безопасности
- Система поддержки (тикеты)

### Административная панель

- Управление пользователями
- Управление контрактами
- Управление выплатами
- Статистика и аналитика
- Настройка параметров системы

## Дизайн

Проект использует единую дизайн-систему, основанную на Figma. Для работы с дизайном используется плагин MCP (Cursor MCP Plugin).

### Запуск интеграции с Figma

```bash
# Запуск WebSocket сервера для MCP
cd mcp/figma
npm install
node socket.js
```

Подробнее о работе с дизайном можно узнать в документации [docs/css_guidelines.md](./css_guidelines.md).

## Тестирование

### Запуск unit-тестов

```bash
pytest
```

### Запуск интеграционных тестов

```bash
pytest tests/integration/
```

## Разработка

### Запуск с отладкой

```bash
flask run --debug
```

### Добавление новых зависимостей

```bash
pip install <package>
pip freeze > requirements.txt
```

### Создание миграций базы данных

После изменения моделей данных:

```bash
flask db migrate -m "Описание изменений"
flask db upgrade
```

### Локализация

Для работы с переводами:

```bash
pybabel extract -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d app/translations
pybabel compile -d app/translations
```

## Лицензия

[MIT](LICENSE) 