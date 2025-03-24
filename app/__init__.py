"""
Модуль инициализации Flask-приложения.
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
from dotenv import load_dotenv

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
    # Создание и настройка приложения
    app = Flask(__name__, instance_relative_config=True)
    
    # Проверяем, какая переменная окружения доступна: DATABASE_URL или DATABASE_URI
    database_uri = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_URI', 'sqlite:////data/app.db')
    
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=database_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CACHE_TYPE=os.environ.get('CACHE_TYPE', 'SimpleCache')
    )

    print(f"Настройка приложения: DATABASE_URI={database_uri}")

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
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Создание директории данных, если требуется
    data_dir = '/data'
    try:
        os.makedirs(data_dir, exist_ok=True)
        print(f"Создана директория для данных: {data_dir}")
    except OSError as e:
        print(f"Ошибка при создании директории для данных: {str(e)}")

    # Регистрация blueprints
    try:
        from app.controllers.auth import auth_bp
        from app.controllers.main import main_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
    except Exception as e:
        print(f"Ошибка при регистрации blueprints: {str(e)}")
        
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
        print('Initialized the database.')

    return app 