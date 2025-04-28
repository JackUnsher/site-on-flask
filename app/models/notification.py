from app import db
from datetime import datetime


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # system, contract, payment, security
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Обратная ссылка на пользователя
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Notification {self.id}>'


class NotificationTemplate(db.Model):
    __tablename__ = 'notification_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, key=None, content=None):
        self.key = key
        self.content = content
    
    @classmethod
    def get_by_key(cls, key):
        """Получает шаблон по ключу"""
        return cls.query.filter_by(key=key).first()
    
    @classmethod
    def ensure_table_exists(cls):
        """Проверяет существование таблицы и создает ее если нужно"""
        from app import db
        import datetime
        
        try:
            # Проверяем если таблица существует, запросив один элемент
            cls.query.first()
            return True
        except Exception:
            # Таблица не существует, создаем
            try:
                db.create_all()
                
                # Добавляем базовые шаблоны
                templates = [
                    cls(
                        key="welcome",
                        content="Добро пожаловать на нашу платформу, {username}! Мы рады приветствовать вас."
                    ),
                    cls(
                        key="withdrawal_approved",
                        content="Ваша заявка на вывод средств #{id} успешно обработана. Сумма {amount} BTC отправлена на ваш кошелек {wallet}."
                    ),
                    cls(
                        key="withdrawal_rejected",
                        content="Ваша заявка на вывод средств #{id} была отклонена. Причина: {reason}. Пожалуйста, свяжитесь с поддержкой для получения дополнительной информации."
                    ),
                    cls(
                        key="earnings",
                        content="Поздравляем! Вы получили {amount} BTC от вашего контракта #{contract_id}."
                    )
                ]
                
                # Устанавливаем даты
                now = datetime.datetime.utcnow()
                for template in templates:
                    template.created_at = now
                    template.updated_at = now
                    db.session.add(template)
                
                db.session.commit()
                return True
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка при создании таблицы notification_templates: {str(e)}")
                return False
    
    def to_dict(self):
        """Преобразует объект в словарь для API"""
        return {
            'id': self.id,
            'key': self.key,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<NotificationTemplate {self.key}>' 