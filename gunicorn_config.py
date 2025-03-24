"""
Конфигурация Gunicorn для Flask приложения на Amvera.
"""
import os
import multiprocessing

# Количество рабочих процессов
# Автоматический расчет на основе доступных ядер процессора
workers = multiprocessing.cpu_count() * 2 + 1

# Тип рабочих процессов
worker_class = 'sync'

# Тайм-ауты
timeout = 120
keepalive = 5

# Максимальное количество одновременных запросов
# которые рабочий процесс будет обрабатывать
max_requests = 1000
max_requests_jitter = 50

# Лог-файлы
errorlog = '-'  # stderr
accesslog = '-'  # stdout
loglevel = 'debug'  # Изменено на debug для лучшей отладки на Amvera

# Формат логов доступа
access_log_format = '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Включаем статус и статистику
enable_static_serving = True

# Привязка к сокету
# Amvera использует переменную окружения PORT, которую нужно получить
port = os.environ.get('PORT', '5000')
bind = f"0.0.0.0:{port}"

# Демонизация процесса
daemon = False

# Preload приложения
preload_app = True

# Название процесса
proc_name = 'flask_app'

# Не показывать баннер при запуске
capture_output = True

# Функция для инициализации приложения перед запуском воркеров
def on_starting(server):
    """
    Запускается перед инициализацией воркеров.
    Можно выполнять предварительную настройку.
    """
    print("Starting Gunicorn server for Flask application on Amvera...") 