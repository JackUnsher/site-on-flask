"""
Файл конфигурации для Flask приложения.
"""
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Путь к корневой директории проекта
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Базовая конфигурация, от которой наследуются остальные конфигурации.
    """
    # Секретный ключ для сессий и CSRF защиты
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Настройка директории для SQLite
    INSTANCE_PATH = os.path.join(BASE_DIR, 'instance')
    os.makedirs(INSTANCE_PATH, exist_ok=True)
    
    # Конфигурация базы данных
    # Используем DATABASE_URL если установлен, иначе используем SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(INSTANCE_PATH, 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Конфигурация почтового сервера
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Настройки кэширования
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'simple'
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT') or 300)  # 5 минут
    
    # Настройки загрузки файлов
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app/static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 МБ максимальный размер загружаемого файла
    
    # Количество записей на страницу при пагинации
    POSTS_PER_PAGE = 10
    
    # Локализация
    LANGUAGES = ['ru', 'en']
    DEFAULT_LANGUAGE = 'ru'
    
    # Логирование
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')


class DevelopmentConfig(Config):
    """
    Конфигурация для разработки.
    """
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    # При разработке используем SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(Config.INSTANCE_PATH, 'app-dev.db')}"
    # Включаем миграции для разработки
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class TestConfig(Config):
    """
    Конфигурация для тестирования.
    """
    TESTING = True
    WTF_CSRF_ENABLED = False  # Отключаем CSRF защиту для тестов
    
    # Используем базу данных в памяти для тестов
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Устанавливаем серверные переменные для тестирования
    SERVER_NAME = 'localhost'  


class ProductionConfig(Config):
    """
    Конфигурация для продакшена.
    """
    # В продакшене SECRET_KEY должен быть установлен через переменную окружения
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Настройки для SQLite в продакшене
    # Используем переданный DATABASE_URL или стандартный путь в instance директории
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(Config.INSTANCE_PATH, 'app.db')}"
    
    # Настройки SSL
    SSL_REDIRECT = True if os.environ.get('SSL_REDIRECT') else False
    
    # Настройки безопасности
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    
    # Настройки кэширования
    # Используем простой кэш вместо Redis для облегчения деплоя
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'simple'
    

# Словарь доступных конфигураций
config = {
    'development': DevelopmentConfig,
    'testing': TestConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Получение активной конфигурации из переменной окружения
def get_config():
    """
    Получает активную конфигурацию на основе переменной окружения FLASK_CONFIG.
    По умолчанию возвращает конфигурацию для разработки.
    """
    config_name = os.environ.get('FLASK_CONFIG') or 'default'
    return config.get(config_name, DevelopmentConfig) 