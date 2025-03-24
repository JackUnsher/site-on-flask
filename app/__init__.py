"""
Модуль инициализации Flask-приложения.
"""
import os
import sys
import logging
from flask import Flask

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Создание и настройка приложения
app = Flask(__name__)

# Проверяем, какая переменная окружения доступна: DATABASE_URL или DATABASE_URI
database_uri = os.environ.get('DATABASE_URL', 'sqlite:////data/app.db')
logger.info(f"Настройка приложения с DATABASE_URI={database_uri}")

app.config.from_mapping(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
    SQLALCHEMY_DATABASE_URI=database_uri,
)

# Создание директории данных, если требуется
data_dir = '/data'
try:
    if not os.path.exists(data_dir):
        logger.warning(f"Директория данных не существует: {data_dir}")
        try:
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
    else:
        logger.info(f"Директория данных существует: {data_dir}")
except Exception as e:
    logger.error(f"Непредвиденная ошибка при работе с директорией данных: {str(e)}")

@app.route('/debug')
def debug():
    return {
        'status': 'ok',
        'config': {k: str(v) for k, v in app.config.items() if k != 'SECRET_KEY'}
    }

# Регистрация маршрутов
from app import routes 