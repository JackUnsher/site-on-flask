"""
WSGI точка входа для Flask-приложения
"""
import os
import sys
import logging
from app import app

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

logger.info("Инициализация WSGI точки входа")

# Для прямого запуска файла
if __name__ == "__main__":
    logger.info("Запуск через WSGI файл напрямую")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
