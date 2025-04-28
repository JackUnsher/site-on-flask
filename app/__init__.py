from flask import Flask, request, g, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_babel import Babel, _
from flask_mail import Mail
from config import Config
import os
from flask_wtf.csrf import CSRFProtect
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
babel = Babel()
mail = Mail()
csrf = CSRFProtect()
scheduler = APScheduler()

def get_locale():
    """Определяет текущую локаль"""
    # Приоритет: параметр URL > значение в сессии > язык браузера > значение по умолчанию
    if 'lang' in session:
        return session['lang']
    if current_user.is_authenticated and hasattr(current_user, 'language'):
        return current_user.language
    return request.accept_languages.best_match(['en', 'ru']) or 'en'

def track_user_activity():
    # Отслеживаем активность пользователя, если он авторизован
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализация расширений с приложением
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Настройка login_manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = _('Please login to access this page.')
    
    # Настройка логирования
    if not app.debug and not app.testing:
        log_folder = app.config['LOG_FOLDER']
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        file_handler = RotatingFileHandler(os.path.join(log_folder, 'app.log'), maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')
    
    # Регистрация blueprints
    from app.views.main import main_bp
    app.register_blueprint(main_bp)
    
    from app.views.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.views.profile import profile_bp
    app.register_blueprint(profile_bp, url_prefix='/profile')
    
    from app.views.lang import lang_bp
    app.register_blueprint(lang_bp, url_prefix='/lang')
    
    try:
        from app.views.camera import camera_bp
        app.register_blueprint(camera_bp, url_prefix='/camera')
    except Exception as e:
        app.logger.error(f"Ошибка при регистрации camera_bp: {str(e)}")
    
    # Регистрация административного интерфейса
    try:
        from app.views.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
    except Exception as e:
        app.logger.error(f"Ошибка при регистрации admin_bp: {str(e)}")
    
    # Создание директории для загрузок
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Импорт моделей
    from app.models.user import User, Setting
    from app.models.contract import Contract, ContractPlan
    from app.models.transaction import Transaction, Earning, Withdrawal
    from app.models.support import SupportChat, SupportMessage
    
    # Инициализация Babel
    babel.init_app(app)
    
    @app.before_request
    def before_request():
        track_user_activity()
        g.locale = str(get_locale())
        g.lang_code = session.get('lang', get_locale())
    
    @app.after_request
    def after_request(response):
        if not getattr(app, '_got_first_request', False):
            with app.app_context():
                try:
                    from app.utils.settings import SettingsManager
                    SettingsManager.init_settings()
                    
                    # Убедимся, что таблица notification_templates существует
                    from app.models import NotificationTemplate
                    NotificationTemplate.ensure_table_exists()
                    
                    app._got_first_request = True
                except Exception as e:
                    app.logger.error(f"Error initializing settings: {str(e)}")
        return response
    
    # Регистрация обработчиков ошибок
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    # Инициализация планировщика
    try:
        scheduler.init_app(app)
        
        @scheduler.task('cron', id='close_inactive_chats', hour=3, minute=0)
        def scheduled_close_inactive_chats():
            with app.app_context():
                try:
                    from app.utils.tasks import close_inactive_chats
                    app.logger.info("Running scheduled task: close_inactive_chats")
                    close_inactive_chats()
                except Exception as e:
                    app.logger.error(f"Error in scheduled task: {str(e)}")
        
        @scheduler.task('cron', id='process_daily_earnings', hour=0, minute=15)
        def scheduled_process_daily_earnings():
            with app.app_context():
                try:
                    from app.utils.tasks import process_daily_earnings
                    app.logger.info("Running scheduled task: process_daily_earnings")
                    result = process_daily_earnings()
                    app.logger.info(f"Результат ежедневных начислений: {result}")
                except Exception as e:
                    app.logger.error(f"Error in scheduled task process_daily_earnings: {str(e)}")
        
        scheduler.start()
    except Exception as e:
        app.logger.error(f"Error initializing scheduler: {str(e)}")
    
    return app 