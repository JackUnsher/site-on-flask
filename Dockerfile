# Базовый образ Python
FROM python:3.11-slim

# Установка рабочей директории
WORKDIR /app

# Копирование файла requirements.txt
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода проекта
COPY . .

# Создание директории для постоянных данных
RUN mkdir -p /app/instance

# Установка переменных окружения
ENV FLASK_APP=app.py \
    FLASK_CONFIG=production

# Определение порта
EXPOSE $PORT

# Точка входа
ENTRYPOINT ["./docker-entrypoint.sh"]

# Запуск приложения
CMD gunicorn app:app -b 0.0.0.0:$PORT -w 4 