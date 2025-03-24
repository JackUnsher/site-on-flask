"""
Основной контроллер приложения
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app import cache
from app.utils.decorators import role_required

# Создание блюпринта для основных страниц
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
@cache.cached(timeout=60)
def index():
    """
    Главная страница
    """
    return render_template('main/index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Панель управления, доступна только авторизованным пользователям
    """
    return render_template('main/dashboard.html')

@main_bp.route('/admin')
@login_required
@role_required('admin')
def admin():
    """
    Админ-панель, доступна только пользователям с ролью admin
    """
    return render_template('main/admin.html') 