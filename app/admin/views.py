from flask import redirect, url_for
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from wtforms import PasswordField

from app.models.user import User


# Базовый класс для защищенных административных представлений
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))


# Настраиваемое представление для модели User
class UserAdminView(SecureModelView):
    # Явно указываем имя для представления
    name = 'Users Panel'
    endpoint = 'admin_users'
    menu_icon_type = 'fa'
    menu_icon_value = 'fa-user'
    category = 'Пользователи'
    
    column_exclude_list = ['password_hash']
    column_searchable_list = ['username', 'email']
    column_filters = ['is_admin']
    form_columns = ['username', 'email', 'is_admin', 'password']
    
    # Добавляем поле пароля в форму создания/редактирования
    form_extra_fields = {
        'password': PasswordField('Пароль')
    }
    
    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.set_password(form.password.data) 