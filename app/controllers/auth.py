"""
Контроллер аутентификации
"""
from flask import Blueprint, request, flash, redirect, url_for, render_template
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse

from app import db, cache
from app.models import User, Role
from app.views.auth_forms import LoginForm, RegistrationForm

# Создание блюпринта для аутентификации
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Обработчик входа в систему
    """
    # Если пользователь уже аутентифицирован, перенаправляем на главную
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Поиск пользователя в базе данных
        user = User.query.filter_by(username=form.username.data).first()
        
        # Проверка пользователя и пароля
        if user is None or not user.verify_password(form.password.data):
            flash('Неверное имя пользователя или пароль', 'danger')
            return render_template('auth/login.html', form=form)
        
        # Вход пользователя в систему
        login_user(user, remember=form.remember_me.data)
        
        # Обновление времени последнего входа
        user.update_last_seen()
        
        # Перенаправление на запрошенную страницу или на главную
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        
        flash('Вы успешно вошли в систему', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """
    Обработчик выхода из системы
    """
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Обработчик регистрации нового пользователя
    """
    # Если пользователь уже аутентифицирован, перенаправляем на главную
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Создание нового пользователя
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        
        # Получение или создание роли пользователя
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(name='user', description='Обычный пользователь')
            db.session.add(user_role)
        
        # Присвоение роли пользователю
        user.add_role(user_role)
        
        # Сохранение пользователя в базе данных
        db.session.add(user)
        db.session.commit()
        
        flash('Поздравляем! Вы успешно зарегистрировались и можете войти в систему', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/profile')
@login_required
def profile():
    """
    Профиль пользователя
    """
    return render_template('auth/profile.html') 