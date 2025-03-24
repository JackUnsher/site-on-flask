"""
Модель пользователя
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager

# Таблица связи пользователей и ролей (многие-ко-многим)
user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """
    Модель пользователя с поддержкой безопасности паролей и ролей.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношение с таблицей ролей
    roles = db.relationship('Role', secondary=user_roles, 
                           backref=db.backref('users', lazy='dynamic'), 
                           lazy='dynamic')

    def __init__(self, username, email, password, first_name=None, last_name=None):
        self.username = username
        self.email = email
        self.password = password  # Будет автоматически хешироваться при установке
        self.first_name = first_name
        self.last_name = last_name

    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def password(self):
        """
        Запрещает чтение пароля
        """
        raise AttributeError('Пароль не является читаемым атрибутом')
    
    @password.setter
    def password(self, password):
        """
        Устанавливает хеш пароля
        """
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """
        Проверяет пароль
        """
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role_name):
        """
        Проверяет, имеет ли пользователь указанную роль
        """
        return self.roles.filter_by(name=role_name).first() is not None
    
    def add_role(self, role):
        """
        Добавляет роль пользователю
        """
        if not self.has_role(role.name):
            self.roles.append(role)
            return True
        return False
    
    def remove_role(self, role):
        """
        Удаляет роль у пользователя
        """
        if self.has_role(role.name):
            self.roles.remove(role)
            return True
        return False
    
    def get_full_name(self):
        """
        Возвращает полное имя пользователя
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def update_last_seen(self):
        """
        Обновляет время последнего посещения пользователя
        """
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()


class Role(db.Model):
    """
    Модель роли для системы авторизации
    """
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255))
    
    def __init__(self, name, description=None):
        self.name = name
        self.description = description
    
    def __repr__(self):
        return f'<Role {self.name}>'


@login_manager.user_loader
def load_user(user_id):
    """
    Функция для загрузки пользователя по ID для Flask-Login
    """
    return User.query.get(int(user_id)) 