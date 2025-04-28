from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_babel import _


def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash(_('Please log in to access this page.'), 'warning')
            return redirect(url_for('auth.login'))
            
        if not current_user.is_admin:
            flash(_('You do not have permission to access this page.'), 'danger')
            return redirect(url_for('main.index'))
            
        return f(*args, **kwargs)
    return decorated_function


def admin_or_self_required(f):
    """Декоратор для проверки прав администратора или владельца ресурса"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash(_('Please log in to access this page.'), 'warning')
            return redirect(url_for('auth.login'))
            
        # Если пользователь - администратор, разрешаем доступ
        if current_user.is_admin:
            return f(*args, **kwargs)
            
        # Проверяем, является ли пользователь владельцем ресурса
        user_id = kwargs.get('user_id')
        if user_id and current_user.id != user_id:
            flash(_('You do not have permission to access this resource.'), 'danger')
            return redirect(url_for('main.index'))
            
        return f(*args, **kwargs)
    return decorated_function


def check_confirmed(f):
    """Декоратор, который проверяет, подтвержден ли аккаунт пользователя"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.confirmed:
            flash(_('Please confirm your account before accessing this page.'), 'warning')
            return redirect(url_for('auth.unconfirmed'))
        return f(*args, **kwargs)
    return decorated_function 