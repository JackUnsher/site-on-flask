"""
Конфигурация Gunicorn для Flask приложения на Amvera.
"""
import os
import sys
import logging
import multiprocessing

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Количество рабочих процессов
# Автоматический расчет на основе доступных ядер процессора
workers = multiprocessing.cpu_count() * 2 + 1
logger.info(f"Настройка Gunicorn с {workers} рабочими процессами")

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
logger.info(f"Настройка привязки Gunicorn к порту {port}")

# Демонизация процесса
daemon = False

# Preload приложения
preload_app = True

# Название процесса
proc_name = 'flask_app'

# Не показывать баннер при запуске
capture_output = True

# Функция для обработки критических ошибок
def on_starting(server):
    """
    Запускается перед инициализацией воркеров.
    Можно выполнять предварительную настройку.
    """
    logger.info("Starting Gunicorn server for Flask application on Amvera...")
    
    # Проверяем наличие директории данных
    data_dir = '/data'
    if not os.path.exists(data_dir):
        try:
            logger.warning(f"Директория данных не существует: {data_dir}")
            os.makedirs(data_dir, exist_ok=True, mode=0o777)
            logger.info(f"Создана директория для данных: {data_dir}")
        except Exception as e:
            logger.error(f"Ошибка при создании директории данных: {str(e)}")
            
            # Пробуем создать в /tmp
            tmp_dir = '/tmp/data'
            try:
                os.makedirs(tmp_dir, exist_ok=True)
                logger.info(f"Создана временная директория для данных: {tmp_dir}")
            except Exception as e:
                logger.critical(f"Невозможно создать директорию данных: {str(e)}")

def on_exit(server):
    """
    Запускается при завершении работы сервера.
    """
    logger.info("Gunicorn server shutting down...")

def worker_exit(server, worker):
    """
    Вызывается при завершении работы worker'а.
    """
    logger.info(f"Worker {worker.pid} exiting")

def worker_abort(worker):
    """
    Вызывается, когда worker завершается аварийно.
    """
    logger.error(f"Worker {worker.pid} aborted unexpectedly") 