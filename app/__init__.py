"""
Модуль инициализации Flask-приложения.
"""
import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения из .env файла
load_dotenv()

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
cache = Cache()

def create_app(test_config=None):
    """
    Фабрика приложений - создает экземпляр приложения Flask.
    
    Args:
        test_config: Конфигурация для тестирования (если нужно)
        
    Returns:
        Экземпляр приложения Flask
    """
    try:
        # Создание и настройка приложения
        app = Flask(__name__, instance_relative_config=True)
        
        # Проверяем, какая переменная окружения доступна: DATABASE_URL или DATABASE_URI
        database_uri = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_URI', 'sqlite:////data/app.db')
        
        logger.info(f"Настройка приложения с DATABASE_URI={database_uri}")
        
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
            SQLALCHEMY_DATABASE_URI=database_uri,
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            CACHE_TYPE=os.environ.get('CACHE_TYPE', 'SimpleCache')
        )

        if test_config is None:
            # Загрузка конфигурации из файла, если не в режиме тестирования
            app.config.from_pyfile('config.py', silent=True)
        else:
            # Загрузка тестовой конфигурации
            app.config.from_mapping(test_config)

        # Инициализация расширений с приложением
        db.init_app(app)
        migrate.init_app(app, db)
        login_manager.init_app(app)
        csrf.init_app(app)
        cache.init_app(app)

        # Настройка login_manager
        login_manager.login_view = 'auth.login'
        login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
        login_manager.login_message_category = 'info'

        # Создание папки instance, если она не существует
        try:
            os.makedirs(app.instance_path, exist_ok=True)
            logger.info(f"Создана директория instance: {app.instance_path}")
        except OSError as e:
            logger.error(f"Ошибка при создании директории instance: {str(e)}")
        
        # Создание директории данных, если требуется
        data_dir = '/data'
        try:
            if not os.path.exists(data_dir):
                logger.warning(f"Директория данных не существует: {data_dir}")
                # Пробуем создать директорию с различными правами
                try:
                    os.makedirs(data_dir, exist_ok=True, mode=0o777)
                    logger.info(f"Создана директория для данных: {data_dir}")
                except:
                    logger.error(f"Невозможно создать директорию {data_dir}, пробуем альтернативные пути")
                    
                    # Пробуем создать в /tmp
                    tmp_dir = '/tmp/data'
                    try:
                        os.makedirs(tmp_dir, exist_ok=True)
                        logger.info(f"Создана временная директория для данных: {tmp_dir}")
                        # Меняем конфигурацию URI базы данных
                        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('/data/', '/tmp/data/')
                        logger.info(f"База данных перенаправлена в {app.config['SQLALCHEMY_DATABASE_URI']}")
                    except:
                        logger.critical("Не удалось создать ни /data, ни /tmp/data для хранения базы данных")
            else:
                # Проверяем права на запись
                if os.access(data_dir, os.W_OK):
                    logger.info(f"Директория данных существует и доступна для записи: {data_dir}")
                    # Создаем тестовый файл для проверки
                    try:
                        test_file = os.path.join(data_dir, 'test_write.txt')
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                        logger.info("Тест записи в директорию данных успешен")
                    except Exception as e:
                        logger.error(f"Ошибка при тестировании записи в директорию данных: {str(e)}")
                else:
                    logger.error(f"Директория данных существует, но недоступна для записи: {data_dir}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при работе с директорией данных: {str(e)}")

        # Регистрация blueprints
        try:
            from app.controllers.auth import auth_bp
            from app.controllers.main import main_bp

            app.register_blueprint(auth_bp)
            app.register_blueprint(main_bp)
            logger.info("Blueprints успешно зарегистрированы")
        except Exception as e:
            logger.error(f"Ошибка при регистрации blueprints: {str(e)}")
            
            # Создаем простой маршрут для диагностики
            @app.route('/debug')
            def debug():
                return {
                    'status': 'ok',
                    'config': {k: str(v) for k, v in app.config.items() if k != 'SECRET_KEY'}
                }

        # Командная строка для инициализации базы данных
        @app.cli.command('init-db')
        def init_db_command():
            """Очистка существующих данных и создание новых таблиц."""
            db.create_all()
            logger.info('База данных инициализирована.')

        return app
    except Exception as e:
        logger.critical(f"Критическая ошибка при создании приложения: {str(e)}", exc_info=True)
        # Создаем минимальное приложение для диагностики
        app = Flask(__name__)
        
        @app.route('/')
        def emergency():
            return {
                'status': 'error',
                'message': f'Критическая ошибка при инициализации приложения: {str(e)}'
            }
        
        return app 