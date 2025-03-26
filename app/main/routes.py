from flask import render_template, current_app
from flask_login import login_required

from app.main import bp


@bp.route('/')
@bp.route('/index')
def index():
    """Главная страница"""
    return render_template('main/index.html', title='Главная')


@bp.route('/profile')
@login_required
def profile():
    """Страница профиля пользователя"""
    return render_template('main/profile.html', title='Личный кабинет')


@bp.route('/clients')
@login_required
def clients():
    """Страница клиентов"""
    return render_template('main/clients.html', title='Клиенты')


@bp.route('/orders')
@login_required
def orders():
    """Страница заявок"""
    return render_template('main/orders.html', title='Заявки')


@bp.route('/history')
@login_required
def history():
    """История заявок"""
    return render_template('main/history.html', title='История заявок')


@bp.route('/statistics')
@login_required
def statistics():
    """Статистика"""
    return render_template('main/statistics.html', title='Статистика')


@bp.route('/feedback')
def feedback():
    """Форма обратной связи"""
    return render_template('main/feedback.html', title='Обратная связь')


@bp.route('/terms')
def terms():
    """Пользовательское соглашение"""
    return render_template('main/terms.html', title='Пользовательское соглашение') 