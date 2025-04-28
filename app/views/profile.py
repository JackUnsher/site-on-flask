from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, g
from flask_login import login_required, current_user
from flask_babel import _
from app import db
from app.models import (
    User, Contract, ContractPlan, Transaction,
    Earning, Withdrawal, SupportChat, SupportMessage,
    Wallet, Content, FaqItem
)
from app.forms.profile import EditProfileForm, TwoFactorSettingsForm, ChangePasswordForm
import qrcode
import io
import base64
import pyotp
from datetime import datetime, timedelta
import json
import os
import time
import secrets
from werkzeug.utils import secure_filename
from app.utils.telegram_bot import send_telegram_notification_to_admin, send_support_chat_notification
from app.utils.settings import SettingsManager

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/dashboard')
@login_required
def dashboard():
    """Отображает панель управления пользователя"""
    user = current_user
    
    # Получаем статистику пользователя
    hashrate = user.get_total_hashrate()
    balance = user.get_total_balance()
    profit = user.get_total_profit()
    
    # Получаем активные контракты
    active_contracts = Contract.query.filter_by(
        user_id=user.id, 
        status='active'
    ).order_by(Contract.created_at.desc()).limit(5).all()
    
    # Получаем открытые тикеты поддержки
    support_tickets = SupportChat.query.filter_by(
        user_id=user.id, 
        is_closed=False
    ).order_by(SupportChat.created_at.desc()).limit(3).all()
    
    # Получаем последние транзакции
    recent_transactions = Transaction.query.filter_by(
        user_id=user.id
    ).order_by(Transaction.created_at.desc()).limit(5).all()
    
    # Получаем последний заработок
    recent_earnings = Earning.query.filter_by(
        user_id=user.id
    ).order_by(Earning.created_at.desc()).limit(5).all()
    
    # Добавляем переменные для шаблона dashboard.html
    total_hashrate = hashrate # Используем вместо hashrate
    total_profit = profit # Используем вместо profit
    btc_price = 65000 # Текущая цена BTC в долларах
    btc_change = 2.35 # Процентное изменение курса BTC (можно получать из API)
    current_balance = balance # Используем вместо balance
    current_balance_usd = balance * btc_price # Баланс в долларах
    
    # Данные о прибыли за последний день
    last_day = datetime.now().strftime('%d.%m.%Y')
    last_day_profit_btc = 0.00045 # Прибыль за последний день в BTC
    last_day_profit_usd = last_day_profit_btc * btc_price # Прибыль за последний день в USD
    
    # Данные о балансе электричества и контрактах
    electricity_balance = 120 # Баланс электричества в USD
    total_contract_value = 2500 # Общая стоимость контрактов в USD
    contracts_count = len(active_contracts) # Количество контрактов
    user_contracts = active_contracts # Контракты для выпадающего списка
    
    # Добавляем данные для графика
    # Дни текущего месяца для отображения в графике
    today = datetime.now()
    chart_labels = [
        (today - timedelta(days=6)).strftime('%d.%m'),
        (today - timedelta(days=5)).strftime('%d.%m'),
        (today - timedelta(days=4)).strftime('%d.%m'),
        (today - timedelta(days=3)).strftime('%d.%m'),
        (today - timedelta(days=2)).strftime('%d.%m'),
        (today - timedelta(days=1)).strftime('%d.%m'),
        today.strftime('%d.%m')
    ]
    # Примерные значения доходов за последние 7 дней
    chart_data = [0.00014, 0.00016, 0.00018, 0.00021, 0.00025, 0.00029, 0.00035]
    
    return render_template('profile/dashboard.html', 
        user=user,
        hashrate=hashrate,
        balance=balance,
        profit=profit,
        active_contracts=active_contracts,
        support_tickets=support_tickets,
        recent_transactions=recent_transactions,
        recent_earnings=recent_earnings,
        timedelta=timedelta,
        btc_change=btc_change,
        # Добавляем новые переменные
        total_hashrate=total_hashrate,
        total_profit=total_profit,
        btc_price=btc_price,
        current_balance=current_balance,
        current_balance_usd=current_balance_usd,
        last_day=last_day,
        last_day_profit_btc=last_day_profit_btc,
        last_day_profit_usd=last_day_profit_usd,
        electricity_balance=electricity_balance,
        total_contract_value=total_contract_value,
        contracts_count=contracts_count,
        user_contracts=user_contracts,
        # Добавляем данные для графика
        chart_labels=chart_labels,
        chart_data=chart_data
    )


@profile_bp.route('/contracts')
@login_required
def contracts():
    """Страница со всеми контрактами пользователя"""
    # Получаем все контракты
    user_contracts = current_user.contracts.order_by(Contract.created_at.desc()).all()
    
    # Разделяем на активные и неактивные
    active_contracts = [c for c in user_contracts if c.is_active]
    inactive_contracts = [c for c in user_contracts if not c.is_active]
    
    return render_template('profile/contracts.html', 
                          title=_('Contracts'),
                          active_contracts=active_contracts,
                          inactive_contracts=inactive_contracts)


@profile_bp.route('/transactions')
@login_required
def transactions():
    """Показывает страницу транзакций пользователя."""
    # Получаем все заработки пользователя
    earnings = Earning.query.filter_by(user_id=current_user.id).order_by(Earning.date.desc()).all()
    
    # Получаем все выводы средств пользователя
    withdrawals = Withdrawal.query.filter_by(user_id=current_user.id).order_by(Withdrawal.date.desc()).all()
    
    # Получаем все активные контракты пользователя для опции выбора при выводе
    active_contracts = Contract.query.filter_by(
        user_id=current_user.id, 
        status='active'
    ).all()
    
    # Рассчитываем общий баланс пользователя
    total_balance = sum(contract.current_profit for contract in active_contracts)
    
    return render_template(
        'profile/transactions.html',
        earnings=earnings,
        withdrawals=withdrawals,
        active_contracts=active_contracts,
        total_balance=total_balance
    )


@profile_bp.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    """Создает заявку на вывод средств"""
    amount_btc = request.form.get('amount', type=float)
    wallet_id = request.form.get('wallet_id')
    contract_id = request.form.get('contract_id')
    
    if not amount_btc:
        flash(_('Please provide amount for withdrawal.'), 'danger')
        return redirect(url_for('profile.transactions'))
    
    # Проверка минимальной и максимальной суммы вывода из настроек
    min_withdrawal = SettingsManager.get_setting('withdrawal.min_amount', 0.0005)
    max_withdrawal = SettingsManager.get_setting('withdrawal.max_amount', 1000)
    
    if amount_btc < min_withdrawal:
        flash(_('Minimum withdrawal amount is %(min)s BTC.', min=min_withdrawal), 'danger')
        return redirect(url_for('profile.transactions'))
    
    if amount_btc > max_withdrawal:
        flash(_('Maximum withdrawal amount is %(max)s BTC.', max=max_withdrawal), 'danger')
        return redirect(url_for('profile.transactions'))
    
    # Получаем кошелек
    wallet = None
    if wallet_id:
        wallet = Wallet.query.filter_by(id=wallet_id, user_id=current_user.id).first()
    
    # Если кошелек не указан, проверяем наличие адреса в форме
    wallet_address = request.form.get('wallet_address')
    if not wallet and not wallet_address:
        flash(_('Please provide a wallet for withdrawal.'), 'danger')
        return redirect(url_for('profile.transactions'))
    
    # Используем адрес из кошелька, если кошелек указан
    if wallet:
        wallet_address = wallet.address
    
    # Определяем источник средств
    contract = None
    if contract_id and contract_id != 'all':
        contract = Contract.query.filter_by(id=contract_id, user_id=current_user.id, is_active=True).first()
        if not contract:
            flash(_('Selected contract not found or inactive.'), 'danger')
            return redirect(url_for('profile.transactions'))
        
        # Проверка доступных средств на конкретном контракте
        if amount_btc > contract.profit_btc:
            flash(_('Insufficient balance on the selected contract. Available: %(balance)s BTC', balance=contract.profit_btc), 'danger')
            return redirect(url_for('profile.transactions'))
    else:
        # Проверка общего баланса
        active_contracts = Contract.query.filter_by(user_id=current_user.id, is_active=True).all()
        total_balance = sum(c.profit_btc for c in active_contracts)
        
        if amount_btc > total_balance:
            flash(_('Insufficient balance. Your available balance is %(balance)s BTC.', balance=total_balance), 'danger')
            return redirect(url_for('profile.transactions'))
    
    # Валидация адреса кошелька (простая проверка)
    if not wallet_address.startswith('1') and not wallet_address.startswith('3') and not wallet_address.startswith('bc'):
        flash(_('Invalid Bitcoin wallet address.'), 'danger')
        return redirect(url_for('profile.transactions'))
    
    # Получаем комиссию из настроек (в процентах)
    fee_percent = SettingsManager.get_setting('withdrawal.fee_percent', 2.5)
    fee_amount = amount_btc * (fee_percent / 100)
    final_amount = amount_btc - fee_amount
    
    # Создаем заявку на вывод
    withdrawal = Withdrawal(
        user_id=current_user.id,
        amount_btc=amount_btc,
        fee_btc=fee_amount,
        final_amount_btc=final_amount,
        wallet_address=wallet_address,
        status='pending',
        contract_id=contract.id if contract else None,
        date=datetime.utcnow()
    )
    
    db.session.add(withdrawal)
    
    # Если вывод с конкретного контракта, уменьшаем его баланс
    if contract:
        contract.profit_btc -= amount_btc
    
    db.session.commit()
    
    # Отправляем уведомление администратору
    send_telegram_notification_to_admin(
        f"Новая заявка на вывод:\n"
        f"Пользователь: {current_user.username}\n"
        f"Сумма: {amount_btc} BTC\n"
        f"Комиссия: {fee_amount:.8f} BTC ({fee_percent}%)\n"
        f"К выплате: {final_amount:.8f} BTC\n"
        f"Кошелек: {wallet_address}\n"
        f"Контракт: {contract.contract_number if contract else 'Все контракты'}"
    )
    
    flash(_('Your withdrawal request has been submitted and is pending approval.'), 'success')
    return redirect(url_for('profile.transactions'))


@profile_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Страница с настройками профиля"""
    form = EditProfileForm()
    password_form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Обработка загрузки аватара
        if form.avatar.data:
            filename = secure_filename(form.avatar.data.filename)
            avatar_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
            
            # Создаем директорию, если она не существует
            if not os.path.exists(avatar_dir):
                os.makedirs(avatar_dir)
                
            # Генерируем уникальное имя файла с префиксом user_id
            avatar_filename = f"user_{current_user.id}_{int(time.time())}_{filename}"
            file_path = os.path.join(avatar_dir, avatar_filename)
            
            # Сохраняем файл
            form.avatar.data.save(file_path)
            
            # Обновляем путь к аватару в профиле пользователя
            current_user.avatar = os.path.join('avatars', avatar_filename)
        
        # Обновляем данные пользователя
        current_user.username = form.username.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        
        # Проверяем изменения email
        if form.email.data != current_user.email:
            current_user.email = form.email.data
            # Здесь можно добавить отправку письма для подтверждения email
        
        current_user.phone = form.phone.data
        current_user.country = form.country.data
        current_user.language = form.language.data
        
        db.session.commit()
        flash(_('Your profile has been updated.'), 'success')
        return redirect(url_for('profile.settings'))
        
    elif request.method == 'GET':
        # Заполняем форму текущими данными пользователя
        form.username.data = current_user.username
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email.data = current_user.email
        form.phone.data = current_user.phone
        form.country.data = current_user.country
        form.language.data = current_user.language
    
    # Получаем криптовалютные кошельки пользователя, если они есть
    wallets = []
    if hasattr(current_user, 'wallets'):
        wallets = current_user.wallets.all()
    
    # Проверяем, настроена ли двухфакторная аутентификация
    has_2fa = False
    qr_code = None
    secret_key = None
    
    if current_user.two_factor_enabled:
        has_2fa = True
    elif request.args.get('setup_2fa'):
        # Генерируем QR-код для настройки 2FA
        secret_key = pyotp.random_base32()
        totp = pyotp.TOTP(secret_key)
        provisioning_uri = totp.provisioning_uri(
            name=current_user.email,
            issuer_name=current_app.config['SITE_NAME']
        )
        
        # Создаем QR-код с URI
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer)
        qr_code = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
    
    return render_template('profile/settings.html', 
                          title=_('Settings'),
                          form=form,
                          password_form=password_form,
                          wallets=wallets,
                          has_2fa=has_2fa,
                          qr_code=qr_code,
                          secret_key=secret_key)


@profile_bp.route('/add_wallet', methods=['POST'])
@login_required
def add_wallet():
    """Добавляет новый криптовалютный кошелек"""
    currency = request.form.get('currency')
    address = request.form.get('address')
    label = request.form.get('label', '')
    
    if not currency or not address:
        flash(_('Please provide both currency and wallet address.'), 'danger')
        return redirect(url_for('profile.settings'))
    
    # Базовая валидация адреса в зависимости от валюты
    is_valid = True
    error_message = None
    
    if currency == 'BTC' and not (address.startswith('1') or address.startswith('3') or address.startswith('bc')):
        is_valid = False
        error_message = _('Invalid Bitcoin address format.')
    elif currency == 'ETH' and not address.startswith('0x'):
        is_valid = False
        error_message = _('Invalid Ethereum address format.')
    
    if not is_valid:
        flash(error_message, 'danger')
        return redirect(url_for('profile.settings'))
    
    # Проверяем, не существует ли уже такой кошелек
    existing_wallet = Wallet.query.filter_by(
        user_id=current_user.id,
        currency=currency,
        address=address
    ).first()
    
    if existing_wallet:
        flash(_('This wallet address already exists in your account.'), 'warning')
        return redirect(url_for('profile.settings'))
    
    # Создаем новый кошелек
    wallet = Wallet(
        user_id=current_user.id,
        currency=currency,
        address=address,
        label=label
    )
    
    db.session.add(wallet)
    db.session.commit()
    
    flash(_('Wallet address added successfully.'), 'success')
    return redirect(url_for('profile.settings'))


@profile_bp.route('/delete_wallet/<int:wallet_id>', methods=['POST'])
@login_required
def delete_wallet(wallet_id):
    """Удаляет криптовалютный кошелек"""
    wallet = Wallet.query.filter_by(id=wallet_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(wallet)
    db.session.commit()
    
    flash(_('Wallet address has been removed.'), 'success')
    return redirect(url_for('profile.settings'))


@profile_bp.route('/update_notifications', methods=['POST'])
@login_required
def update_notifications():
    """Обновляет настройки уведомлений"""
    email_enabled = 'email_notifications' in request.form
    payment_notifications = 'payment_notifications' in request.form
    contract_notifications = 'contract_notifications' in request.form
    security_notifications = 'security_notifications' in request.form
    marketing_notifications = 'marketing_notifications' in request.form
    
    # Обновляем настройки в модели пользователя
    notification_preferences = {
        'email_enabled': email_enabled,
        'payment_notifications': payment_notifications,
        'contract_notifications': contract_notifications,
        'security_notifications': security_notifications,
        'marketing_notifications': marketing_notifications
    }
    
    current_user.notification_preferences = notification_preferences
    db.session.commit()
    
    flash(_('Notification settings have been updated.'), 'success')
    return redirect(url_for('profile.settings'))


@profile_bp.route('/enable_2fa', methods=['POST'])
@login_required
def enable_2fa():
    """Включает двухфакторную аутентификацию"""
    verification_code = request.form.get('verification_code')
    secret_key = request.form.get('secret_key')
    
    if not verification_code or not secret_key:
        flash(_('Please provide the verification code.'), 'danger')
        return redirect(url_for('profile.settings'))
    
    # Проверяем код
    totp = pyotp.TOTP(secret_key)
    if totp.verify(verification_code):
        # Код верный, включаем 2FA
        current_user.two_factor_secret = secret_key
        current_user.two_factor_enabled = True
        db.session.commit()
        
        flash(_('Two-factor authentication has been enabled successfully.'), 'success')
        return redirect(url_for('profile.settings'))
    else:
        # Код неверный
        flash(_('Invalid verification code. Please try again.'), 'danger')
        return redirect(url_for('profile.settings', setup_2fa=1))


@profile_bp.route('/disable_2fa', methods=['POST'])
@login_required
def disable_2fa():
    """Отключает двухфакторную аутентификацию"""
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    db.session.commit()
    
    flash(_('Two-factor authentication has been disabled.'), 'warning')
    return redirect(url_for('profile.settings'))


@profile_bp.route('/security', methods=['GET', 'POST'])
@login_required
def security():
    """Страница с настройками безопасности (пароль и 2FA)"""
    password_form = ChangePasswordForm()
    two_factor_form = TwoFactorSettingsForm()
    
    # Генерируем QR-код для 2FA, если еще не настроено
    qr_code_img = None
    secret_key = None
    
    if not current_user.two_factor_secret:
        # Генерируем новый секретный ключ
        secret_key = pyotp.random_base32()
        # Создаем OTP-объект для QR-кода
        totp = pyotp.TOTP(secret_key)
        # Создаем URI для приложения аутентификации
        provisioning_uri = totp.provisioning_uri(
            name=current_user.email,
            issuer_name=current_app.config['APP_NAME']
        )
        # Генерируем QR-код
        img = qrcode.make(provisioning_uri)
        buffered = io.BytesIO()
        img.save(buffered)
        qr_code_img = base64.b64encode(buffered.getvalue()).decode('utf-8')
    else:
        # Если 2FA уже настроено, показываем существующий ключ
        secret_key = current_user.two_factor_secret
    
    # Обработка формы изменения пароля
    if password_form.validate_on_submit() and 'change_password' in request.form:
        if current_user.check_password(password_form.current_password.data):
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash(_('Your password has been updated.'), 'success')
            return redirect(url_for('profile.security'))
        else:
            flash(_('Current password is incorrect.'), 'danger')
    
    # Обработка формы настройки 2FA
    if two_factor_form.validate_on_submit() and 'setup_2fa' in request.form:
        if two_factor_form.code.data and two_factor_form.secret_key.data:
            # Проверяем код
            totp = pyotp.TOTP(two_factor_form.secret_key.data)
            if totp.verify(two_factor_form.code.data):
                # Сохраняем настройки 2FA
                current_user.two_factor_secret = two_factor_form.secret_key.data
                current_user.two_factor_method = two_factor_form.method.data
                current_user.two_factor_enabled = True
                db.session.commit()
                flash(_('Two-factor authentication has been enabled.'), 'success')
                return redirect(url_for('profile.security'))
            else:
                flash(_('Invalid verification code.'), 'danger')
    
    # Обработка отключения 2FA
    if 'disable_2fa' in request.form:
        current_user.two_factor_enabled = False
        db.session.commit()
        flash(_('Two-factor authentication has been disabled.'), 'success')
        return redirect(url_for('profile.security'))
        
    return render_template('profile/security.html', 
                          title=_('Security Settings'),
                          password_form=password_form,
                          two_factor_form=two_factor_form,
                          qr_code_img=qr_code_img,
                          secret_key=secret_key)


@profile_bp.route('/help', methods=['GET', 'POST'])
@login_required
def help():
    """Показывает страницу помощи и FAQ"""
    # Получаем все опубликованные вопросы FAQ
    faqs = FaqItem.get_published()
    
    # Группируем вопросы по категориям
    faq_by_category = {}
    for faq in faqs:
        if faq.category not in faq_by_category:
            faq_by_category[faq.category] = []
        faq_by_category[faq.category].append(faq)
    
    # Получаем содержимое страницы помощи, если оно есть
    help_content = Content.get_by_type('help_page')
    
    if request.method == 'POST':
        # Обработка отправки тикета поддержки
        subject = request.form.get('subject')
        category = request.form.get('category')
        message = request.form.get('message')
        
        # Создаем новый чат поддержки
        chat = SupportChat(
            user_id=current_user.id,
            subject=subject,
            status='open'
        )
        db.session.add(chat)
        db.session.commit()
        
        # Создаем первое сообщение
        initial_message = SupportMessage(
            user_id=current_user.id,
            chat_id=chat.id,
            message=message,
            is_from_user=True,
            is_read=False
        )
        db.session.add(initial_message)
        
        # Обновляем время последнего сообщения
        chat.last_message_at = datetime.utcnow()
        db.session.commit()
        
        flash(_('Your support ticket has been submitted. We will respond shortly.'), 'success')
        return redirect(url_for('profile.support', chat_id=chat.id))
        
    return render_template(
        'profile/help.html', 
        title=_('Help & FAQ'),
        faqs=faqs,
        faq_by_category=faq_by_category,
        help_content=help_content
    )


@profile_bp.route('/cameras')
@login_required
def cameras():
    """Показывает страницу с камерами наблюдения за майнинг-фермой"""
    # В реальном приложении здесь мы бы получали данные о камерах и их статусе
    # Для демонстрации создадим фиктивные данные
    camera_data = [
        {
            'id': 1,
            'name': 'Зал А - Общий вид',
            'status': 'online',
            'url': 'https://example.com/stream/camera1',
            'thumbnail': 'https://via.placeholder.com/300x200.png?text=Camera+1',
            'last_updated': datetime.now()
        },
        {
            'id': 2,
            'name': 'Зал Б - Линия 1-10',
            'status': 'online',
            'url': 'https://example.com/stream/camera2',
            'thumbnail': 'https://via.placeholder.com/300x200.png?text=Camera+2',
            'last_updated': datetime.now() - timedelta(minutes=5)
        },
        {
            'id': 3,
            'name': 'Зал Б - Линия 11-20',
            'status': 'offline',
            'url': 'https://example.com/stream/camera3',
            'thumbnail': 'https://via.placeholder.com/300x200.png?text=Camera+3',
            'last_updated': datetime.now() - timedelta(hours=2)
        },
        {
            'id': 4,
            'name': 'Серверная - Стойки 1-4',
            'status': 'online',
            'url': 'https://example.com/stream/camera4',
            'thumbnail': 'https://via.placeholder.com/300x200.png?text=Camera+4',
            'last_updated': datetime.now() - timedelta(minutes=15)
        },
        {
            'id': 5,
            'name': 'Серверная - Стойки 5-8',
            'status': 'maintenance',
            'url': 'https://example.com/stream/camera5',
            'thumbnail': 'https://via.placeholder.com/300x200.png?text=Camera+5',
            'last_updated': datetime.now() - timedelta(days=1)
        },
        {
            'id': 6,
            'name': 'Зал В - Общий вид',
            'status': 'online',
            'url': 'https://example.com/stream/camera6',
            'thumbnail': 'https://via.placeholder.com/300x200.png?text=Camera+6',
            'last_updated': datetime.now() - timedelta(minutes=30)
        }
    ]
    
    return render_template(
        'profile/cameras.html',
        title=_('Camera Views'),
        cameras=camera_data
    )


@profile_bp.route('/support', methods=['GET'])
@login_required
def support():
    """Показывает страницу с чатом поддержки"""
    # Получаем все чаты пользователя
    chats = SupportChat.query.filter_by(user_id=current_user.id).order_by(SupportChat.updated_at.desc()).all()
    
    # Добавляем счетчик непрочитанных сообщений для каждого чата
    for chat in chats:
        chat.unread_count = SupportMessage.query.filter_by(
            chat_id=chat.id, 
            is_read=False,
            is_from_user=False  # Только сообщения от администратора
        ).count()
    
    # Передаем параметр active_chat_id, если указан
    active_chat_id = request.args.get('chat_id', None)
    
    return render_template(
        'profile/support.html',
        title=_('Support Chat'),
        chats=chats,
        active_chat_id=active_chat_id
    )


@profile_bp.route('/support/create_chat', methods=['POST'])
@login_required
def create_support_chat():
    """Создание нового чата поддержки"""
    form = SupportForm()
    
    if form.validate_on_submit():
        # Создаем новый чат
        chat = SupportChat(
            user_id=current_user.id,
            subject=form.subject.data,
            is_closed=False
        )
        db.session.add(chat)
        db.session.flush()  # Получаем ID без коммита
        
        # Создаем первое сообщение
        message = SupportMessage(
            chat_id=chat.id,
            sender_id=current_user.id,
            content=form.message.data,
            is_from_user=True,
            is_read=False
        )
        
        # Обработка вложенного файла, если есть
        if form.attachment.data:
            file = form.attachment.data
            filename = secure_filename(file.filename)
            
            # Создаем директорию для вложений чата
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'support', str(chat.id))
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            # Сохраняем относительный путь к файлу
            message.attachment = os.path.join('support', str(chat.id), filename)
        
        db.session.add(message)
        db.session.commit()
        
        # Отправка уведомления администратору через Telegram
        message_preview = form.message.data[:100] + ('...' if len(form.message.data) > 100 else '')
        send_support_chat_notification(
            chat_id=chat.id,
            username=current_user.username,
            message_preview=message_preview,
            is_new_chat=True
        )
        
        flash('Ваше обращение отправлено! Мы ответим вам в ближайшее время.', 'success')
        return redirect(url_for('profile.support', chat_id=chat.id))
    
    return redirect(url_for('profile.support'))


@profile_bp.route('/support/send_message', methods=['POST'])
@login_required
def send_support_message():
    """Отправка сообщения в чат поддержки"""
    chat_id = request.form.get('chat_id')
    content = request.form.get('content')
    
    if not chat_id or not content:
        return jsonify({'status': 'error', 'message': 'Не указан ID чата или текст сообщения'}), 400
    
    chat = SupportChat.query.filter_by(id=chat_id, user_id=current_user.id).first()
    if not chat:
        return jsonify({'status': 'error', 'message': 'Чат не найден'}), 404
    
    if chat.is_closed:
        return jsonify({'status': 'error', 'message': 'Чат закрыт, отправка сообщений невозможна'}), 400
    
    # Создаем новое сообщение
    message = SupportMessage(
        chat_id=chat.id,
        sender_id=current_user.id,
        content=content,
        is_from_user=True,
        is_read=False
    )
    
    # Обработка вложенных файлов
    if 'attachment' in request.files and request.files['attachment'].filename:
        file = request.files['attachment']
        filename = secure_filename(file.filename)
        # Создаем директорию, если не существует
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'support', str(chat.id))
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Сохраняем относительный путь к файлу
        message.attachment = os.path.join('support', str(chat.id), filename)
    
    db.session.add(message)
    db.session.commit()
    
    # Отправка уведомления администратору через Telegram
    # Отправляем превью сообщения (первые 100 символов)
    message_preview = content[:100] + ('...' if len(content) > 100 else '')
    send_support_chat_notification(
        chat_id=chat.id, 
        username=current_user.username, 
        message_preview=message_preview
    )
    
    # Подготавливаем данные сообщения для ответа
    message_data = {
        'id': message.id,
        'content': message.content,
        'timestamp': message.timestamp.strftime('%d.%m.%Y %H:%M'),
        'is_from_user': message.is_from_user,
        'attachment': url_for('static', filename=f'uploads/{message.attachment}') if message.attachment else None
    }
    
    return jsonify({'status': 'success', 'message': 'Сообщение отправлено', 'data': message_data})


@profile_bp.route('/support/chat/<int:chat_id>/messages', methods=['GET'])
@login_required
def get_chat_messages(chat_id):
    """Получает сообщения из конкретного чата"""
    chat = SupportChat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    
    # Получаем сообщения и отмечаем непрочитанные как прочитанные (только для пользователя)
    messages = SupportMessage.query.filter_by(chat_id=chat.id).order_by(SupportMessage.date).all()
    
    unread_messages = SupportMessage.query.filter_by(
        chat_id=chat.id, 
        is_read=False,
        is_from_user=False  # Только сообщения от администратора
    ).all()
    
    for message in unread_messages:
        message.is_read = True
    
    db.session.commit()
    
    # Преобразуем сообщения в формат для JSON
    messages_data = []
    for message in messages:
        message_data = {
            'id': message.id,
            'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
            'message': message.message,
            'is_from_user': message.is_from_user,
            'has_attachment': message.has_attachment,
            'attachment_path': message.attachment_path if message.has_attachment else None
        }
        messages_data.append(message_data)
    
    return jsonify({
        'chat_id': chat.id,
        'subject': chat.subject,
        'is_closed': chat.is_closed,
        'messages': messages_data
    })


@profile_bp.route('/support/chat/<int:chat_id>/close', methods=['POST'])
@login_required
def close_chat(chat_id):
    """Закрывает чат"""
    chat = SupportChat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    
    chat.is_closed = True
    db.session.commit()
    
    flash(_('Chat has been closed'), 'success')
    return redirect(url_for('profile.support'))


@profile_bp.route('/support/check_unread', methods=['GET'])
@login_required
def check_unread_messages():
    """Проверяет наличие непрочитанных сообщений от администратора"""
    unread_count = SupportMessage.query.join(
        SupportChat, SupportMessage.chat_id == SupportChat.id
    ).filter(
        SupportChat.user_id == current_user.id,
        SupportMessage.is_from_user == False,  # От администратора
        SupportMessage.is_read == False
    ).count()
    
    return jsonify({
        'unread_count': unread_count
    })


@profile_bp.before_request
@login_required
def before_profile_request():
    """Выполняется перед каждым запросом к blueprint профиля"""
    # Подсчет непрочитанных сообщений для отображения в боковой панели
    unread_count = SupportMessage.query.join(
        SupportChat, SupportMessage.chat_id == SupportChat.id
    ).filter(
        SupportChat.user_id == current_user.id,
        SupportMessage.is_from_user == False,  # От администратора
        SupportMessage.is_read == False
    ).count()
    
    g.unread_messages_count = unread_count


@profile_bp.context_processor
def inject_profile_context():
    """Добавляет переменные в контекст для всех шаблонов blueprint профиля"""
    return {
        'unread_messages_count': getattr(g, 'unread_messages_count', 0)
    }


@profile_bp.route('/buy_contracts')
@login_required
def buy_contracts():
    """Страница с доступными контрактами для покупки"""
    # Получаем все активные планы контрактов
    active_plans = ContractPlan.query.filter_by(is_active=True).all()
    
    return render_template('profile/buy_contracts.html', 
                          title=_('Buy Mining Contract'),
                          plans=active_plans)


@profile_bp.route('/purchase_contract/<int:plan_id>', methods=['POST'])
@login_required
def purchase_contract(plan_id):
    """Процесс покупки контракта"""
    # Получаем план контракта
    plan = ContractPlan.query.get_or_404(plan_id)
    
    if not plan.is_active:
        flash(_('This contract plan is no longer available'), 'danger')
        return redirect(url_for('profile.buy_contracts'))
    
    # Создаем новый контракт
    contract = Contract()
    contract.user_id = current_user.id
    contract.contract_number = Contract.generate_contract_number()
    contract.hash_power = plan.hashrate
    contract.price = plan.price_usd
    contract.price_per_th = plan.price_usd / plan.hashrate if plan.hashrate > 0 else 0
    contract.electricity_balance = plan.price_usd * 0.1  # 10% от стоимости на электричество
    
    # Временно помечаем как оплаченный для демонстрации
    # В реальности здесь должна быть интеграция с платежной системой
    contract.is_paid = True
    contract.is_active = True
    contract.paid_at = datetime.utcnow()
    
    # Устанавливаем сроки контракта
    contract.start_date = datetime.utcnow()
    if plan.duration:
        contract.end_date = contract.start_date + timedelta(days=plan.duration)
    
    # Сохраняем в базу данных
    db.session.add(contract)
    db.session.commit()
    
    # Отправляем уведомление администратору
    send_telegram_notification_to_admin(
        f"Новый контракт куплен: #{contract.contract_number}\n"
        f"Пользователь: {current_user.username}\n"
        f"План: {plan.name}\n"
        f"Хешрейт: {plan.hashrate} TH/s\n"
        f"Стоимость: ${plan.price_usd}"
    )
    
    flash(_('Contract purchased successfully! It is now active and mining.'), 'success')
    return redirect(url_for('profile.contracts'))


@profile_bp.route('/withdrawals')
@login_required
def withdrawals():
    """Показывает страницу вывода средств"""
    # Получаем все выводы средств пользователя
    withdrawals = Withdrawal.query.filter_by(user_id=current_user.id).order_by(Withdrawal.date.desc()).all()
    
    # Получаем все активные контракты пользователя для опции выбора при выводе
    active_contracts = Contract.query.filter_by(
        user_id=current_user.id, 
        is_active=True
    ).all()
    
    # Рассчитываем общий баланс пользователя
    total_balance = sum(contract.profit_btc for contract in active_contracts)
    
    # Получаем кошельки пользователя для выбора в форме вывода
    wallets = Wallet.query.filter_by(user_id=current_user.id, currency='BTC').all()
    
    # Минимальная сумма для вывода из настроек
    min_withdrawal_amount = SettingsManager.get_setting('withdrawal.min_amount', 0.0005)
    
    # Получаем процент комиссии для информации в шаблоне
    fee_percent = SettingsManager.get_setting('withdrawal.fee_percent', 2.5)
    
    return render_template(
        'profile/withdrawals.html',
        title=_('Withdrawals'),
        withdrawals=withdrawals,
        active_contracts=active_contracts,
        total_balance=total_balance,
        wallets=wallets,
        min_withdrawal_amount=min_withdrawal_amount,
        fee_percent=fee_percent
    )


@profile_bp.route('/support/chat/<int:chat_id>/reopen', methods=['POST'])
@login_required
def reopen_chat(chat_id):
    """Повторно открывает закрытый чат"""
    chat = SupportChat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    
    if not chat.is_closed:
        return jsonify({'status': 'error', 'message': _('Chat is already open')}), 400
    
    chat.is_closed = False
    db.session.commit()
    
    # Отправляем уведомление администратору
    send_telegram_notification_to_admin(
        f"Чат #{chat.id} повторно открыт пользователем {current_user.username}"
    )
    
    return jsonify({'status': 'success', 'message': _('Chat reopened successfully')}) 