# Заметки по развертыванию

## Системные требования
- Python 3.8 или выше
- SQLite (разработка) или PostgreSQL (продакшн)
- Современный веб-браузер

## Установка и настройка

### 1. Клонирование репозитория
```
git clone <repository-url>
cd site-on-flask
```

### 2. Создание виртуального окружения
```
python -m venv venv
```

#### Активация виртуального окружения
- Windows:
```
venv\Scripts\activate
```
- Linux/macOS:
```
source venv/bin/activate
```

### 3. Установка зависимостей
```
pip install -r requirements.txt
```

### 4. Создание .env файла
Создайте файл `.env` в корневой директории проекта со следующими переменными:
```
SECRET_KEY=<your-secret-key>
DATABASE_URL=sqlite:///app.db

# Google OAuth (опционально)
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>

# Email настройки
MAIL_SERVER=smtp.googlemail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<your-email>
MAIL_PASSWORD=<your-email-password>
MAIL_DEFAULT_SENDER=<your-default-sender-email>

# Telegram Bot настройки
TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
TELEGRAM_ADMIN_CHAT_ID=<your-telegram-chat-id>
```

### 5. Инициализация базы данных
```
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6. Запуск сервера разработки
```
flask run
```

## Настройка Telegram-бота для уведомлений администратора

Для настройки уведомлений администратора через Telegram необходимо выполнить следующие шаги:

### 1. Создание Telegram бота

1. Откройте Telegram и найдите бота @BotFather
2. Отправьте команду `/newbot`
3. Следуйте инструкциям, чтобы создать нового бота:
   - Укажите имя бота (например, "Mining Platform Admin")
   - Укажите username бота (должен заканчиваться на "bot", например "mining_platform_admin_bot")
4. BotFather пришлет вам токен бота. Сохраните его для использования в настройках приложения.

### 2. Определение ID чата администратора

1. Откройте Telegram и найдите бота @userinfobot
2. Отправьте боту любое сообщение
3. Бот пришлет вам ваш ID. Сохраните его для использования в настройках приложения.

### 3. Настройка переменных окружения

Добавьте полученные значения в ваш файл `.env`:
```
TELEGRAM_BOT_TOKEN=<полученный_токен_бота>
TELEGRAM_ADMIN_CHAT_ID=<ваш_ID_чата>
```

### 4. Тестирование бота

1. Запустите приложение
2. При запуске приложения, если настройки правильные, вы должны получить приветственное сообщение от бота
3. Для проверки работы уведомлений, создайте новую заявку на вывод средств или чат поддержки

## Настройка для продакшн-окружения

### 1. Использование WSGI сервера
Для продакшн-окружения рекомендуется использовать WSGI сервер, например Gunicorn:

```
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 'app:create_app()'
```

### 2. Настройка базы данных
Для продакшн-окружения рекомендуется PostgreSQL вместо SQLite:

```
pip install psycopg2-binary
```

Обновите переменную `DATABASE_URL` в файле `.env`:
```
DATABASE_URL=postgresql://username:password@localhost/dbname
```

### 3. Настройка веб-сервера
Для продакшн-окружения рекомендуется использовать Nginx в качестве обратного прокси-сервера перед Gunicorn. 

### 4. Настройка HTTPS
Для защиты данных пользователей обязательно настройте HTTPS с действительным SSL-сертификатом (например, используя Let's Encrypt).

## Обновление приложения

Для обновления приложения до новой версии:

1. Остановите сервер
2. Сделайте резервную копию базы данных
3. Обновите исходный код:
   ```
   git pull origin main
   ```
4. Обновите зависимости:
   ```
   pip install -r requirements.txt
   ```
5. Примените миграции базы данных:
   ```
   flask db upgrade
   ```
6. Перезапустите сервер 