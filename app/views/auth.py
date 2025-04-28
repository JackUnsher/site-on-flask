from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_babel import _
from urllib.parse import urlparse
from app import db
from app.models.user import User
from app.forms.auth import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, TwoFactorForm
from app.utils.google_auth import get_google_auth_url, get_google_user_info
from app.utils.email import send_password_reset_email, send_two_factor_code
from datetime import datetime
import secrets
import pyotp
import random

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid email or password'))
            return redirect(url_for('auth.login'))
        
        # Если у пользователя включена двухфакторная аутентификация
        if user.two_factor_enabled:
            # Сохраняем ID пользователя в сессии
            session['user_id'] = user.id
            
            # Генерируем и отправляем код, если используется метод email
            if user.two_factor_method == 'email':
                # Генерируем 6-значный код
                code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                # Сохраняем код в сессии для проверки
                session['two_factor_code'] = code
                # Отправляем код по email
                send_two_factor_code(user, code)
                
            return redirect(url_for('auth.two_factor'))
            
        # Если двухфакторная аутентификация не включена - сразу авторизуем
        login_user(user, remember=form.remember_me.data)
        
        # Обновляем дату последнего входа
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
        
    # Получаем URL для Google OAuth
    google_auth_url = get_google_auth_url()
        
    return render_template('auth/login.html', title=_('Login'), form=form, google_auth_url=google_auth_url)


@auth_bp.route('/two-factor', methods=['GET', 'POST'])
def two_factor():
    """Обработка двухфакторной аутентификации"""
    # Проверяем, есть ли в сессии ID пользователя
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('auth.login'))
        
    form = TwoFactorForm()
    if form.validate_on_submit():
        verified = False
        
        # Проверка кода в зависимости от метода
        if user.two_factor_method == 'email':
            # Проверяем код из сессии
            if session.get('two_factor_code') == form.code.data:
                verified = True
        else:  # authenticator
            # Проверяем через TOTP
            verified = user.verify_two_factor(form.code.data)
            
        if verified:
            # Очищаем данные двухфакторной аутентификации из сессии
            session.pop('user_id', None)
            session.pop('two_factor_code', None)
            
            # Авторизуем пользователя
            login_user(user, remember=True)
            
            # Обновляем дату последнего входа
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = session.get('next') or url_for('main.index')
            session.pop('next', None)
            
            return redirect(next_page)
        else:
            flash(_('Invalid verification code'), 'error')
            
    return render_template('auth/two_factor.html', form=form)


@auth_bp.route('/resend-code')
def resend_code():
    """Повторная отправка кода двухфакторной аутентификации"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user = User.query.get(session['user_id'])
    if not user or user.two_factor_method != 'email':
        return redirect(url_for('auth.login'))
        
    # Генерируем новый код и отправляем
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    session['two_factor_code'] = code
    send_two_factor_code(user, code)
    
    flash(_('A new verification code has been sent'), 'success')
    return redirect(url_for('auth.two_factor'))


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now registered!'))
        return redirect(url_for('auth.login'))
    
    # Получаем URL для Google OAuth
    google_auth_url = get_google_auth_url()
        
    return render_template('auth/register.html', title=_('Register'), form=form, google_auth_url=google_auth_url)


@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        # Сообщаем пользователю, что письмо отправлено, 
        # даже если пользователь не найден, чтобы не раскрывать информацию о наличии пользователя
        flash(_('Check your email for the instructions to reset your password'))
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password_request.html', 
                          title=_('Reset Password'), 
                          form=form)


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    user = User.verify_reset_password_token(token)
    if not user:
        flash(_('Invalid or expired token'))
        return redirect(url_for('auth.reset_password_request'))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form, token=token)


@auth_bp.route('/google/login')
def google_login():
    """Инициирует вход через Google"""
    # Получаем URL для аутентификации
    google_auth_url = get_google_auth_url()
    if not google_auth_url:
        flash(_('Error setting up Google Authentication'), 'error')
        return redirect(url_for('auth.login'))
    
    return redirect(google_auth_url)


@auth_bp.route('/google/callback')
def google_callback():
    """Обрабатывает callback после аутентификации Google"""
    # Проверяем state для защиты от CSRF
    state = request.args.get('state')
    stored_state = session.pop('google_oauth_state', None)
    
    if not state or state != stored_state:
        flash(_('Authentication failed: Invalid state'), 'error')
        return redirect(url_for('auth.login'))
    
    # Получаем код авторизации от Google
    code = request.args.get('code')
    if not code:
        flash(_('Authentication failed'), 'error')
        return redirect(url_for('auth.login'))
    
    # Получаем информацию о пользователе
    user_info = get_google_user_info(code)
    if not user_info:
        flash(_('Failed to get user info from Google'), 'error')
        return redirect(url_for('auth.login'))
    
    # Проверяем, существует ли пользователь с таким email
    user = User.query.filter_by(email=user_info['email']).first()
    
    # Если пользователя нет - регистрируем
    if user is None:
        # Создаем случайное имя пользователя, если оно не указано или уже занято
        username = user_info.get('name', '').replace(' ', '_').lower()
        if not username or User.query.filter_by(username=username).first():
            username = f"user_{secrets.token_hex(4)}"
        
        # Создаем пользователя
        user = User(
            username=username,
            email=user_info['email']
        )
        # Устанавливаем случайный пароль (пользователь не будет им пользоваться)
        user.set_password(secrets.token_urlsafe(16))
        db.session.add(user)
        db.session.commit()
        
        flash(_('Your account has been created with Google'), 'success')
    
    # Если у пользователя включена двухфакторная аутентификация
    if user.two_factor_enabled:
        # Сохраняем ID пользователя в сессии
        session['user_id'] = user.id
        
        # Генерируем и отправляем код, если используется метод email
        if user.two_factor_method == 'email':
            # Генерируем 6-значный код
            code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            # Сохраняем код в сессии для проверки
            session['two_factor_code'] = code
            # Отправляем код по email
            send_two_factor_code(user, code)
        
        # Перенаправляем на страницу с двухфакторной аутентификацией
        return redirect(url_for('auth.two_factor'))
    
    # Авторизуем пользователя
    login_user(user, remember=True)
    
    # Обновляем дату последнего входа
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Перенаправляем на главную страницу или запрошенную страницу
    next_page = session.get('next') or url_for('main.index')
    session.pop('next', None)
    
    return redirect(next_page) 