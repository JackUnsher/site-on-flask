# Руководство по деплою Flask-приложения

## Содержание
1. [Подготовка сервера](#подготовка-сервера)
2. [Установка приложения](#установка-приложения)
3. [Настройка базы данных](#настройка-базы-данных)
4. [Настройка Gunicorn](#настройка-gunicorn)
5. [Настройка Nginx](#настройка-nginx)
6. [Настройка SSL с Let's Encrypt](#настройка-ssl)
7. [Запуск и мониторинг приложения](#запуск-и-мониторинг)
8. [Автоматизация деплоя с помощью CI/CD](#автоматизация-деплоя)
9. [Масштабирование](#масштабирование)

## Подготовка сервера <a name="подготовка-сервера"></a>

### Обновление системы
```bash
sudo apt update
sudo apt upgrade -y
```

### Установка необходимых пакетов
```bash
sudo apt install -y python3 python3-venv python3-dev build-essential libpq-dev postgresql postgresql-contrib nginx git
```

### Настройка брандмауэра
```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Установка приложения <a name="установка-приложения"></a>

### Создание пользователя для приложения (опционально)
```bash
sudo adduser flask_user
sudo usermod -aG sudo flask_user
```

### Клонирование репозитория
```bash
sudo mkdir -p /var/www/flask_app
sudo chown -R $USER:$USER /var/www/flask_app
git clone https://github.com/your-username/your-repo.git /var/www/flask_app
```

### Создание виртуального окружения и установка зависимостей
```bash
cd /var/www/flask_app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Настройка переменных окружения
```bash
nano .env
```

Содержание файла `.env`:
```
FLASK_APP=app.py
FLASK_CONFIG=production
SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgresql://username:password@localhost/flask_db
```

## Настройка базы данных <a name="настройка-базы-данных"></a>

### Создание базы данных и пользователя PostgreSQL
```bash
sudo -u postgres psql
```

В интерактивной оболочке PostgreSQL:
```sql
CREATE DATABASE flask_db;
CREATE USER flask_user WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE flask_db TO flask_user;
\q
```

### Применение миграций
```bash
cd /var/www/flask_app
source venv/bin/activate
flask db upgrade
```

## Настройка Gunicorn <a name="настройка-gunicorn"></a>

### Копирование файла конфигурации
```bash
cp /var/www/flask_app/gunicorn_config.py /var/www/flask_app/
```

### Создание systemd сервиса
```bash
sudo cp /var/www/flask_app/flask_app.service /etc/systemd/system/
sudo nano /etc/systemd/system/flask_app.service
```

Отредактируйте пути и настройки окружения в файле сервиса при необходимости.

### Запуск и включение сервиса
```bash
sudo systemctl daemon-reload
sudo systemctl start flask_app
sudo systemctl enable flask_app
sudo systemctl status flask_app
```

## Настройка Nginx <a name="настройка-nginx"></a>

### Копирование файла конфигурации
```bash
sudo cp /var/www/flask_app/nginx_flask_app.conf /etc/nginx/sites-available/flask_app
```

### Редактирование файла конфигурации
```bash
sudo nano /etc/nginx/sites-available/flask_app
```

Измените `server_name` на ваш домен или IP-адрес сервера.

### Активация конфигурации
```bash
sudo ln -s /etc/nginx/sites-available/flask_app /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## Настройка SSL с Let's Encrypt <a name="настройка-ssl"></a>

### Установка Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Получение SSL-сертификата
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Следуйте инструкциям на экране для завершения настройки.

### Проверка автоматического обновления
```bash
sudo systemctl status certbot.timer
```

## Запуск и мониторинг приложения <a name="запуск-и-мониторинг"></a>

### Проверка статуса сервисов
```bash
sudo systemctl status flask_app
sudo systemctl status nginx
```

### Просмотр логов
```bash
sudo journalctl -u flask_app
sudo tail -f /var/log/nginx/flask_app_access.log
sudo tail -f /var/log/nginx/flask_app_error.log
```

### Перезапуск приложения при обновлении
```bash
cd /var/www/flask_app
git pull origin master
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart flask_app
```

## Автоматизация деплоя с помощью CI/CD <a name="автоматизация-деплоя"></a>

### Настройка GitHub Actions

Репозиторий уже содержит файлы конфигурации GitHub Actions в директории `.github/workflows`:
- `tests.yml` - для автоматического тестирования
- `deploy.yml` - для автоматического деплоя

Для настройки автоматического деплоя необходимо добавить секреты в настройках репозитория GitHub:
1. `SSH_PRIVATE_KEY` - приватный SSH-ключ для подключения к серверу
2. `SERVER_HOST` - адрес сервера
3. `SERVER_USER` - пользователь для подключения к серверу
4. `SERVER_PATH` - путь к каталогу приложения на сервере

### Настройка SSH-ключа на сервере

```bash
# На локальной машине
ssh-keygen -t rsa -b 4096 -C "github-actions"
# Скопируйте содержимое публичного ключа ~/.ssh/id_rsa.pub

# На сервере
nano ~/.ssh/authorized_keys
# Вставьте публичный ключ в этот файл
```

## Масштабирование <a name="масштабирование"></a>

### Горизонтальное масштабирование с помощью Docker

Проект уже содержит файлы для контейнеризации:
- `Dockerfile` - для создания образа приложения
- `docker-compose.yml` - для запуска приложения с базой данных и Redis

Для запуска в Docker:
```bash
cd /var/www/flask_app
docker-compose up -d
```

### Использование балансировщика нагрузки

Для больших нагрузок рекомендуется использовать балансировщик нагрузки, например, Nginx Plus или HAProxy.

Пример конфигурации Nginx в качестве балансировщика нагрузки:
```
upstream flask_app {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://flask_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
``` 