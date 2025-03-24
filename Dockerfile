# Базовый образ Python
FROM python:3.11-slim-bullseye

# Установка рабочей директории
WORKDIR /app

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_CONFIG=production \
    DATABASE_URL=sqlite:///data/app.db

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование файла requirements.txt
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода проекта
COPY . .

# Создание директории для постоянных данных
RUN mkdir -p /data

# Выполнение миграций при запуске контейнера
RUN chmod +x ./docker-entrypoint.sh

# Определение порта
EXPOSE 8080

# Точка входа
ENTRYPOINT ["./docker-entrypoint.sh"]

# Запуск приложения
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"] 