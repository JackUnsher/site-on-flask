# Используем официальный минимальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все исходные файлы приложения
COPY . .

# Создаем необходимые директории для хранения данных и логов
RUN mkdir -p /data/uploads /data/logs

# Устанавливаем переменные окружения
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PORT=80

# Открываем порт 80 (стандартный порт Amvera)
EXPOSE 80

# Создаем скрипт для запуска
RUN echo '#!/bin/bash\n\
echo "Initializing database..."\n\
python init_db.py\n\
echo "Applying migrations..."\n\
python run_migrations.py\n\
echo "Adding mining plans..."\n\
python add_mining_plans.py\n\
echo "Starting application..."\n\
python run.py --port=80\n\
' > /app/start.sh && chmod +x /app/start.sh

# Запускаем приложение
CMD ["/app/start.sh"] 