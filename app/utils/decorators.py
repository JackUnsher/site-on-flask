"""
Декораторы и утилиты для проверки ролей и других функций.
"""
from functools import wraps
from flask import flash, redirect, url_for, request, abort
from flask_login import current_user
from flask_wtf.csrf import validate_csrf

def role_required(role_name):
    """
    Декоратор для проверки роли пользователя.
    Перенаправляет на страницу входа, если пользователь не авторизован
    или у него нет указанной роли.
    
    Args:
        role_name (str): Название роли
        
    Returns:
        function: Декоратор
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Проверка, авторизован ли пользователь
            if not current_user.is_authenticated:
                flash('Пожалуйста, войдите для доступа к этой странице.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Проверка роли
            if not current_user.has_role(role_name):
                flash('У вас нет доступа к этой странице.', 'danger')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Декоратор для проверки роли администратора.
    Сокращенная версия декоратора role_required.
    
    Args:
        f (function): Декорируемая функция
        
    Returns:
        function: Декорированная функция
    """
    return role_required('admin')(f)


def csrf_protect():
    """
    Декоратор для защиты API от CSRF-атак.
    Предполагается использование вместе с Flask-WTF.
    
    Returns:
        function: Декоратор
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Проверка CSRF-токена только для небезопасных методов
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                csrf_token = request.headers.get('X-CSRFToken')
                if not csrf_token or not validate_csrf(csrf_token):
                    abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator 