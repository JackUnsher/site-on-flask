import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    # Общие настройки приложения
    APP_NAME = 'Майнинг-Платформа'
    
    # Секретный ключ для сессий Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'вы-никогда-не-угадаете-мой-секретный-ключ'
    
    # Конфигурация базы данных
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:////data/app.db'  # Изменено для Amvera
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Конфигурация Flask-Admin
    FLASK_ADMIN_SWATCH = 'cerulean'
    
    # Конфигурация для загрузки файлов
    UPLOAD_FOLDER = '/data/uploads'  # Изменено для Amvera
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB максимальный размер файла
    
    # Конфигурация для многоязычности
    LANGUAGES = ['en', 'ru']  # Поддерживаемые языки: английский и русский
    BABEL_DEFAULT_LOCALE = 'en'  # Язык по умолчанию - английский
    BABEL_TRANSLATION_DIRECTORIES = os.path.join(basedir, 'app/translations')
    
    # Google OAuth настройки
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = os.environ.get('GOOGLE_DISCOVERY_URL') or 'https://accounts.google.com/.well-known/openid-configuration'
    
    # Настройки почтового сервера
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.googlemail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@example.com'
    
    # Настройки тайм-аута сессии (20 минут = 1200 секунд)
    PERMANENT_SESSION_LIFETIME = 1200
    
    # Настройки логов
    LOG_FOLDER = '/data/logs'  # Добавлено для Amvera


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    # Продакшн-специфичные настройки
    DEBUG = False
    TESTING = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 