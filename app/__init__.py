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
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URI', 'sqlite:///instance/app.db'),
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
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Регистрация blueprints
    from app.controllers.auth import auth_bp
    from app.controllers.main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Командная строка для инициализации базы данных
    @app.cli.command('init-db')
    def init_db_command():
        """Очистка существующих данных и создание новых таблиц."""
        db.create_all()
        print('Initialized the database.')

    return app 