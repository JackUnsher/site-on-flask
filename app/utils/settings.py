from app import db
from app.models import SystemSetting
from flask import current_app
import logging
from sqlalchemy.exc import SQLAlchemyError

# Настройка логгера
logger = logging.getLogger(__name__)

class SettingsManager:
    """Класс для управления системными настройками"""
    
    # Дефолтные настройки с префиксами
    DEFAULT_SETTINGS = {
        # Настройки безопасности
        'security.session_timeout': {'value': '30', 'description': 'Время жизни сессии в минутах', 'is_numeric': True},
        'security.login_attempts': {'value': '3', 'description': 'Максимальное количество попыток входа', 'is_numeric': True},
        'security.password_min_length': {'value': '8', 'description': 'Минимальная длина пароля', 'is_numeric': True},
        'security.require_2fa': {'value': 'False', 'description': 'Требовать 2FA для всех пользователей'},
        
        # Настройки уведомлений
        'notification.telegram_enabled': {'value': 'True', 'description': 'Включить уведомления Telegram'},
        'notification.email_enabled': {'value': 'True', 'description': 'Включить уведомления по email'},
        
        # Настройки контента
        'content.articles_per_page': {'value': '10', 'description': 'Количество статей на странице', 'is_numeric': True},
        'content.show_social_links': {'value': 'True', 'description': 'Показывать ссылки на соцсети'},
        
        # Настройки вывода средств
        'withdrawal.min_amount': {'value': '10', 'description': 'Минимальная сумма для вывода', 'is_numeric': True},
        'withdrawal.max_amount': {'value': '1000', 'description': 'Максимальная сумма для вывода', 'is_numeric': True},
        'withdrawal.fee_percent': {'value': '2.5', 'description': 'Комиссия за вывод в процентах', 'is_numeric': True},
        
        # Настройки поддержки
        'support.auto_close_days': {'value': '5', 'description': 'Автоматическое закрытие обращений через дней', 'is_numeric': True},

        # Настройки контрактов
        'contract.min_amount': {'value': '100', 'description': 'Минимальная сумма контракта в USD', 'is_numeric': True},
        'contract.max_amount': {'value': '50000', 'description': 'Максимальная сумма контракта в USD', 'is_numeric': True},
        'contract.hashrate_cost': {'value': '50', 'description': 'Стоимость 1 TH/s в USD', 'is_numeric': True},
        'contract.electricity_cost': {'value': '0.1', 'description': 'Стоимость электричества за 1 TH/s в день в USD', 'is_numeric': True},
        'contract.maintenance_cost': {'value': '0.05', 'description': 'Стоимость обслуживания за 1 TH/s в день в USD', 'is_numeric': True},
        'contract.min_hashrate': {'value': '1', 'description': 'Минимальный хешрейт контракта в TH/s', 'is_numeric': True},
        'contract.max_hashrate': {'value': '1000', 'description': 'Максимальный хешрейт контракта в TH/s', 'is_numeric': True},
        'contract.daily_yield': {'value': '0.5', 'description': 'Ежедневная доходность в процентах', 'is_numeric': True},
        'contract.duration': {'value': '365', 'description': 'Длительность контракта в днях', 'is_numeric': True},
    }
    
    @classmethod
    def init_settings(cls):
        """Инициализация настроек по умолчанию при запуске приложения"""
        try:
            for key, options in cls.DEFAULT_SETTINGS.items():
                # Проверяем, существует ли настройка
                setting = SystemSetting.get_by_key(key)
                if not setting:
                    # Создаем новую настройку
                    SystemSetting.set_value(
                        key=key,
                        value=options['value'],
                        description=options.get('description'),
                        is_numeric=options.get('is_numeric', False)
                    )
            
            # Фиксируем транзакцию
            db.session.commit()
            current_app.logger.info("System settings initialized successfully")
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error initializing settings: {str(e)}")
        except Exception as e:
            current_app.logger.error(f"Unexpected error initializing settings: {str(e)}")
    
    @classmethod
    def get(cls, key, default=None):
        """Получение значения настройки"""
        try:
            value = SystemSetting.get_value(key, default)
            return value
        except Exception as e:
            current_app.logger.error(f"Error getting setting {key}: {str(e)}")
            return default
    
    @classmethod
    def set(cls, key, value, description=None, is_numeric=None):
        """Обновление значения настройки"""
        try:
            setting = SystemSetting.set_value(key, value, description, is_numeric)
            db.session.commit()
            current_app.logger.info(f"Setting updated: {key} = {value}")
            return setting
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error updating setting {key}: {str(e)}")
            return None
        except Exception as e:
            current_app.logger.error(f"Error updating setting {key}: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, key):
        """Удаление настройки"""
        try:
            setting = SystemSetting.get_by_key(key)
            if setting:
                db.session.delete(setting)
                db.session.commit()
                current_app.logger.info(f"Setting deleted: {key}")
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error deleting setting {key}: {str(e)}")
            return False
        except Exception as e:
            current_app.logger.error(f"Error deleting setting {key}: {str(e)}")
            return False
    
    @classmethod
    def get_all(cls):
        """Получение всех настроек"""
        try:
            settings = SystemSetting.query.all()
            return settings
        except Exception as e:
            current_app.logger.error(f"Error getting all settings: {str(e)}")
            return []
    
    @classmethod
    def get_by_prefix(cls, prefix):
        """Получение настроек по префиксу"""
        try:
            settings = SystemSetting.query.filter(SystemSetting.key.like(f"{prefix}%")).all()
            return settings
        except Exception as e:
            current_app.logger.error(f"Error getting settings by prefix {prefix}: {str(e)}")
            return []
    
    @classmethod
    def get_prefixes(cls):
        """Получение списка уникальных префиксов"""
        try:
            settings = SystemSetting.query.all()
            prefixes = set()
            
            for setting in settings:
                if '.' in setting.key:
                    prefix = setting.key.split('.')[0]
                    prefixes.add(prefix)
            
            return sorted(list(prefixes))
        except Exception as e:
            current_app.logger.error(f"Error getting setting prefixes: {str(e)}")
            return []
    
    # Алиасы для более понятного именования
    set_setting = set
    get_setting = get
    get_all_settings = get_all
    get_settings_by_prefix = get_by_prefix
    delete_setting = delete 