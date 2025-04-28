from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timedelta
import pyotp
import secrets
from flask import current_app
import time
import uuid
import jwt


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    phone = db.Column(db.String(20))
    country = db.Column(db.String(2))
    avatar = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 2FA fields
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))
    two_factor_method = db.Column(db.String(20), default='app')  # 'app' или 'sms'
    
    # Google OAuth fields
    google_id = db.Column(db.String(64), unique=True, nullable=True)
    
    # Password reset
    reset_token = db.Column(db.String(36), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
    # Дополнительные поля для ЛК
    language = db.Column(db.String(2), default='en')  # Язык интерфейса
    notification_preferences = db.Column(db.JSON, default={
        'email_enabled': True,
        'payment_notifications': True,
        'contract_notifications': True,
        'security_notifications': True,
        'marketing_notifications': False
    })
    
    # Связи с другими моделями - используем back_populates
    contracts = db.relationship('Contract', back_populates='user', foreign_keys="Contract.user_id", lazy='dynamic')
    earnings = db.relationship('Earning', back_populates='user', foreign_keys="Earning.user_id", lazy='dynamic')
    transactions = db.relationship('Transaction', back_populates='user', foreign_keys="Transaction.user_id", lazy='dynamic')
    withdrawals = db.relationship('Withdrawal', back_populates='user', foreign_keys="Withdrawal.user_id", lazy='dynamic')
    processed_withdrawals = db.relationship('Withdrawal', back_populates='admin', foreign_keys="Withdrawal.processed_by_id", lazy='dynamic')
    support_chats = db.relationship('SupportChat', back_populates='user', foreign_keys="SupportChat.user_id", lazy='dynamic')
    support_messages = db.relationship('SupportMessage', back_populates='user', foreign_keys="SupportMessage.user_id", lazy='dynamic')
    wallets = db.relationship('Wallet', back_populates='user', foreign_keys="Wallet.user_id", lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=3600):
        """Создает JWT токен для сброса пароля"""
        return jwt.encode(
            {
                'reset_password': self.id,
                'exp': time.time() + expires_in
            },
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_password_token(token):
        """Проверяет токен сброса пароля и возвращает пользователя"""
        try:
            id = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )['reset_password']
        except:
            return None
        return User.query.get(id)
    
    def generate_otp_secret(self):
        self.otp_secret = pyotp.random_base32()
        return self.otp_secret
    
    def get_totp_uri(self):
        if not self.otp_secret:
            self.generate_otp_secret()
        
        service_name = "Mining Platform"
        return pyotp.totp.TOTP(self.otp_secret).provisioning_uri(
            name=self.email, issuer_name=service_name)
    
    def verify_totp(self, token):
        if not self.otp_secret:
            return False
        
        totp = pyotp.TOTP(self.otp_secret)
        return totp.verify(token)
    
    def generate_reset_token(self):
        self.reset_token = str(uuid.uuid4())
        self.reset_token_expiry = datetime.utcnow() + datetime.timedelta(hours=1)
        return self.reset_token
    
    def verify_reset_token(self, token):
        if self.reset_token != token:
            return False
        
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        
        return True
    
    def clear_reset_token(self):
        self.reset_token = None
        self.reset_token_expiry = None
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    def get_total_hashrate(self):
        """Возвращает общий хешрейт для активных контрактов"""
        from app.models.contract import Contract
        total = 0
        active_contracts = Contract.query.filter_by(user_id=self.id, status='active').all()
        for contract in active_contracts:
            total += contract.hashrate
        return total
    
    def get_total_profit(self):
        """Возвращает общую прибыль пользователя от всех заработков"""
        from app.models.transaction import Earning
        earnings = Earning.query.filter_by(user_id=self.id).all()
        total_profit = sum(earning.amount_btc for earning in earnings)
        return total_profit
    
    def get_total_earnings(self):
        """Возвращает общую сумму заработков пользователя"""
        return self.get_total_profit()
    
    def get_total_balance(self):
        """Возвращает общий баланс пользователя (доступный для вывода)"""
        from app.models.transaction import Earning, Withdrawal
        # Получаем сумму всех заработков
        earnings = Earning.query.filter_by(user_id=self.id).all()
        total_earnings = sum(earning.amount_btc for earning in earnings)
        
        # Получаем сумму всех успешных выводов
        withdrawals = Withdrawal.query.filter_by(user_id=self.id, status='success').all()
        total_withdrawals = sum(withdrawal.amount_btc for withdrawal in withdrawals)
        
        # Баланс = заработки - выводы
        return total_earnings - total_withdrawals
    
    def __repr__(self):
        return f'<User {self.username}>'


class Setting(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get(key, default=None):
        setting = Setting.query.filter_by(key=key).first()
        if setting is None:
            return default
        return setting.value
    
    @staticmethod
    def set(key, value, description=None):
        setting = Setting.query.filter_by(key=key).first()
        if setting is None:
            setting = Setting(key=key)
        setting.value = value
        if description:
            setting.description = description
        db.session.add(setting)
        db.session.commit()
    
    def __repr__(self):
        return f'<Setting {self.key}>'


class Wallet(db.Model):
    __tablename__ = 'wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    currency = db.Column(db.String(10), nullable=False)  # BTC, ETH, LTC, etc.
    address = db.Column(db.String(255), nullable=False)
    label = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Обратная ссылка на пользователя
    user = db.relationship('User', back_populates='wallets', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<Wallet {self.id}>' 