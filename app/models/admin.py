from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for

from app.models import User, Contract, ContractPlan, Transaction, Earning, Withdrawal, SupportChat, SupportMessage, Content, FaqItem, Setting, SystemSetting
from app import db

# Базовый класс для защищенных моделей админки
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

# Представления для моделей админки
class UserAdminView(SecureModelView):
    column_exclude_list = ['password_hash']
    column_searchable_list = ['username', 'email']
    column_filters = ['is_admin', 'created_at']

class ContractAdminView(SecureModelView):
    column_searchable_list = ['user.username']
    column_filters = ['status', 'created_at']

class TransactionAdminView(SecureModelView):
    column_searchable_list = ['user.username']
    column_filters = ['type', 'status', 'created_at']

class SystemSettingAdminView(SecureModelView):
    column_searchable_list = ['key']
    column_filters = ['key']

def setup_admin(app, admin):
    """Настройка и регистрация моделей в админке Flask-Admin"""
    
    # Добавляем представления моделей
    admin.add_view(UserAdminView(User, db.session, name='Пользователи', category='Управление'))
    admin.add_view(ContractAdminView(Contract, db.session, name='Контракты', category='Управление'))
    admin.add_view(TransactionAdminView(Transaction, db.session, name='Транзакции', category='Финансы'))
    admin.add_view(SecureModelView(Earning, db.session, name='Начисления', category='Финансы'))
    admin.add_view(SecureModelView(Withdrawal, db.session, name='Выводы', category='Финансы'))
    admin.add_view(SecureModelView(ContractPlan, db.session, name='Планы', category='Управление'))
    admin.add_view(SecureModelView(SupportChat, db.session, name='Чаты', category='Поддержка'))
    admin.add_view(SecureModelView(SupportMessage, db.session, name='Сообщения', category='Поддержка'))
    admin.add_view(SecureModelView(Content, db.session, name='Контент', category='Содержимое'))
    admin.add_view(SecureModelView(FaqItem, db.session, name='FAQ', category='Содержимое'))
    admin.add_view(SecureModelView(Setting, db.session, name='Настройки пользователей', category='Настройки'))
    admin.add_view(SystemSettingAdminView(SystemSetting, db.session, name='Системные настройки', category='Настройки')) 