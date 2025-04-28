from app import db
from datetime import datetime


class SystemSetting(db.Model):
    """Модель для хранения системных настроек"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    is_numeric = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<SystemSetting {self.key}>'
    
    def get_value(self, default=None):
        """Возвращает значение настройки с учетом типа"""
        if self.is_numeric:
            try:
                if '.' in self.value:
                    return float(self.value)
                return int(self.value)
            except (ValueError, TypeError):
                return default
        return self.value
    
    @classmethod
    def get_by_key(cls, key):
        """Получает настройку по ключу"""
        return cls.query.filter_by(key=key).first()
    
    @classmethod
    def get_value(cls, key, default=None):
        """Получает значение настройки по ключу"""
        setting = cls.get_by_key(key)
        if setting:
            return setting.get_value(default)
        return default
    
    @classmethod
    def set_value(cls, key, value, description=None, is_numeric=None):
        """Устанавливает значение настройки"""
        setting = cls.get_by_key(key)
        if setting:
            setting.value = str(value)
            if description is not None:
                setting.description = description
            if is_numeric is not None:
                setting.is_numeric = is_numeric
        else:
            setting = cls(
                key=key,
                value=str(value),
                description=description,
                is_numeric=bool(is_numeric)
            )
            db.session.add(setting)
        return setting 