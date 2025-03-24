"""
Базовая конфигурация Gunicorn для Flask приложения на Amvera.
"""
import os
import multiprocessing

# Количество рабочих процессов
workers = 1

# Тип рабочих процессов
worker_class = 'sync'

# Тайм-ауты
timeout = 120
keepalive = 5

# Лог-файлы
errorlog = '-'  # stderr
accesslog = '-'  # stdout
loglevel = 'debug'

# Привязка к сокету
port = os.environ.get('PORT', '5000')
bind = f"0.0.0.0:{port}"

# Демонизация процесса
daemon = False

# Название процесса
proc_name = 'flask_app'

# Не показывать баннер при запуске
capture_output = True 