from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file, g, Response, abort, make_response
from flask_login import login_required, current_user
from flask_babel import _
from app.decorators import admin_required
from app.models import (
    User, Contract, ContractPlan, Transaction,
    Earning, Withdrawal, SystemSetting, NotificationTemplate, FAQ, SupportChat, SupportMessage
)
from app import db
from datetime import datetime, timedelta
import json
import os
from werkzeug.utils import secure_filename
from app.utils.telegram_bot import send_telegram_notification_to_admin
from app.utils.settings import SettingsManager
from sqlalchemy import func, or_, and_, case, desc
from io import StringIO
import csv
from io import BytesIO
import logging
import traceback
# from app.utils.format import format_btc  # Закомментируем импорт, чтобы избежать ошибки
from app.utils.notifications import send_notification, send_notification_with_template
from functools import wraps

admin_bp = Blueprint('admin', __name__)

logger = logging.getLogger(__name__)

# Определяем локальную функцию format_btc
def format_btc(amount, precision=8):
    """
    Форматирует значение Bitcoin с заданной точностью
    """
    if amount is None:
        return "0.00000000"
    
    formatted = f"{float(amount):.{precision}f}"
    
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".") if "." in formatted else formatted
        
    if "." not in formatted:
        formatted += ".0"
    
    parts = formatted.split(".")
    if len(parts) > 1 and len(parts[1]) < 2:
        formatted = parts[0] + "." + parts[1].ljust(2, "0")
        
    return formatted

@admin_bp.before_request
@login_required
def before_admin_request():
    if not current_user.is_admin:
        flash(_('Access denied. You do not have admin privileges.'), 'danger')
        return redirect(url_for('main.index'))

@admin_bp.route('/')
@admin_required
def index():
    """Главная страница админ-панели"""
    # Получаем статистику
    total_users = User.query.count()
    active_contracts = Contract.query.filter_by(status='active').count()
    pending_withdrawals = Withdrawal.query.filter_by(status='pending').count()
    
    return render_template('admin/index.html',
                         total_users=total_users,
                         active_contracts=active_contracts,
                         pending_withdrawals=pending_withdrawals)

@admin_bp.route('/users')
@admin_required
def users():
    """Страница управления пользователями"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:id>')
@admin_required
def user_detail(id):
    """Страница с детальной информацией о пользователе"""
    user = User.query.get_or_404(id)
    contracts = Contract.query.filter_by(user_id=user.id).order_by(Contract.created_at.desc()).all()
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.date.desc()).all()
    withdrawals = Withdrawal.query.filter_by(user_id=user.id).order_by(Withdrawal.date.desc()).all()
    
    return render_template('admin/user_detail.html', user=user, contracts=contracts, 
                           transactions=transactions, withdrawals=withdrawals)

@admin_bp.route('/withdrawals')
@admin_required
def withdrawals():
    """Страница управления выводами средств"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    search = request.args.get('search', '')
    per_page = 10
    
    # Формируем базовый запрос
    query = Withdrawal.query
    
    # Фильтруем по статусу, если указан
    if status != 'all':
        query = query.filter(Withdrawal.status == status)
    
    # Фильтруем по поисковому запросу, если указан
    if search:
        query = query.join(User).filter(
            or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                Withdrawal.wallet_address.ilike(f'%{search}%')
            )
        )
    
    # Статистика для отображения на странице
    withdrawal_stats = {
        'total': Withdrawal.query.count(),
        'pending': Withdrawal.query.filter_by(status='pending').count(),
        'success': Withdrawal.query.filter_by(status='success').count(),
        'error': Withdrawal.query.filter_by(status='error').count(),
        'cancelled': Withdrawal.query.filter_by(status='cancelled').count(),
    }
    
    # Получаем общее количество записей и разбиваем на страницы
    total_items = query.count()
    total_pages = (total_items + per_page - 1) // per_page
    
    # Применяем сортировку и пагинацию
    withdrawals = query.order_by(Withdrawal.date.desc()).paginate(page=page, per_page=per_page, error_out=False).items
    
    return render_template('admin/withdrawals.html', 
                          withdrawals=withdrawals,
                          page=page,
                          per_page=per_page,
                          total_items=total_items,
                          total_pages=total_pages,
                          status=status,
                          search=search,
                          withdrawal_stats=withdrawal_stats)

@admin_bp.route('/settings')
@admin_required
def settings():
    """Страница настроек системы"""
    settings_list = SystemSetting.query.all()
    settings = {}
    for setting in settings_list:
        settings[setting.key] = setting.value
    return render_template('admin/settings.html', settings=settings)

@admin_bp.route('/contracts')
@admin_required
def contracts():
    """Страница управления контрактами"""
    contracts = Contract.query.order_by(Contract.created_at.desc()).all()
    return render_template('admin/contracts.html', contracts=contracts)

@admin_bp.route('/support')
@admin_required
def support():
    """Страница поддержки - чаты с пользователями"""
    chats = SupportChat.query.order_by(SupportChat.updated_at.desc()).all()
    return render_template('admin/support.html', chats=chats)

@admin_bp.route('/content')
@admin_required
def content():
    """Страница управления контентом сайта"""
    return render_template('admin/content.html')

@admin_bp.route('/approve-withdrawal', methods=['POST'])
@admin_required
def approve_withdrawal():
    """Подтверждение заявки на вывод средств"""
    withdrawal_id = request.form.get('withdrawal_id')
    tx_hash = request.form.get('tx_hash')
    notes = request.form.get('notes')
    
    if not withdrawal_id:
        flash(_('Invalid withdrawal request'), 'danger')
        return redirect(url_for('admin.withdrawals'))
    
    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    
    # Проверяем, что заявка в статусе ожидания
    if withdrawal.status != 'pending':
        flash(_('This withdrawal request has already been processed'), 'warning')
        return redirect(url_for('admin.withdrawals'))
    
    # Подтверждаем заявку
    withdrawal.status = 'success'
    withdrawal.processed_at = datetime.utcnow()
    withdrawal.processed_by_id = current_user.id
    
    if tx_hash:
        withdrawal.tx_hash = tx_hash
    
    if notes:
        withdrawal.notes = notes
    
    db.session.commit()
    
    # Отправляем уведомление администратору через Telegram
    send_telegram_notification_to_admin(
        _('Withdrawal Request Approved'),
        _('Administrator %(admin)s has approved withdrawal request #%(id)s from user %(username)s for %(amount)s BTC.', 
           admin=current_user.username, id=withdrawal.id, username=withdrawal.user.username, amount=withdrawal.amount_btc)
    )
    
    flash(_('Withdrawal request approved successfully'), 'success')
    return redirect(url_for('admin.withdrawals'))

@admin_bp.route('/reject-withdrawal', methods=['POST'])
@admin_required
def reject_withdrawal():
    """Отклонение заявки на вывод средств"""
    withdrawal_id = request.form.get('withdrawal_id')
    reason = request.form.get('reason')
    
    if not withdrawal_id:
        flash(_('Invalid withdrawal request'), 'danger')
        return redirect(url_for('admin.withdrawals'))
    
    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    
    # Проверяем, что заявка в статусе ожидания
    if withdrawal.status != 'pending':
        flash(_('This withdrawal request has already been processed'), 'warning')
        return redirect(url_for('admin.withdrawals'))
    
    # Отклоняем заявку
    withdrawal.status = 'cancelled'
    withdrawal.processed_at = datetime.utcnow()
    withdrawal.processed_by_id = current_user.id
    withdrawal.notes = reason
    
    db.session.commit()
    
    # Отправляем уведомление администратору через Telegram
    send_telegram_notification_to_admin(
        _('Withdrawal Request Rejected'),
        _('Administrator %(admin)s has rejected withdrawal request #%(id)s from user %(username)s for %(amount)s BTC.\nReason: %(reason)s', 
           admin=current_user.username, id=withdrawal.id, username=withdrawal.user.username, amount=withdrawal.amount_btc, reason=reason)
    )
    
    flash(_('Withdrawal request rejected successfully'), 'success')
    return redirect(url_for('admin.withdrawals'))

@admin_bp.route('/upload_legal_document/<doc_type>', methods=['POST'])
@admin_required
def upload_legal_document(doc_type):
    """Загрузка юридических документов (Terms of Use и Privacy Policy)"""
    if doc_type not in ['terms', 'privacy']:
        flash(_('Недопустимый тип документа'), 'error')
        return redirect(url_for('admin.content_manager'))
    
    # Проверяем, загружен ли файл
    if 'file' not in request.files:
        flash(_('Файл не был передан'), 'error')
        return redirect(url_for('admin.content_manager'))
    
    file = request.files['file']
    
    # Если файл не выбран
    if file.filename == '':
        flash(_('Файл не выбран'), 'error')
        return redirect(url_for('admin.content_manager'))
    
    # Проверяем расширение файла
    allowed_extensions = {'html', 'pdf', 'txt'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        flash(_('Разрешенные типы файлов: html, pdf, txt'), 'error')
        return redirect(url_for('admin.content_manager'))
    
    try:
        # Определяем имя файла на основе типа документа
        filename = f"{doc_type}.{file_ext}"
        
        # Путь для сохранения файла
        upload_folder = os.path.join(current_app.static_folder, 'docs')
        
        # Создаем папку, если она не существует
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # Сохраняем файл
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        flash(_('Документ успешно загружен'), 'success')
        return redirect(url_for('admin.settings'))
    
    except Exception as e:
        current_app.logger.error(f"Ошибка при загрузке документа: {str(e)}")
        flash(_('Произошла ошибка при загрузке документа: %(error)s', error=str(e)), 'error')
        return redirect(url_for('admin.settings'))

@admin_bp.route('/api/settings/contract', methods=['POST'])
@admin_required
def update_contract_settings():
    """Обновление настроек контрактов"""
    try:
        data = request.get_json()
        
        settings_map = {
            'contract.min_amount': float,
            'contract.max_amount': float,
            'contract.th_price': float,
            'contract.electricity_cost': float,
            'contract.maintenance_cost': float,
            'contract.min_hashpower': float,
            'contract.max_hashpower': float,
            'contract.daily_profit': float
        }
        
        with db.session.begin():
            for key, type_cast in settings_map.items():
                if key in data:
                    try:
                        value = type_cast(data[key])
                        SystemSetting.set_value(key, value, is_numeric=True)
                    except ValueError as e:
                        logger.error(f"Error updating {key}: {str(e)}")
                        return jsonify({'error': f'Invalid value for {key}'}), 400
                        
        return jsonify({'message': 'Contract settings updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error in update_contract_settings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/export/users', methods=['GET'])
@admin_required
def export_users():
    """Экспорт данных пользователей в CSV"""
    try:
        output = StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        headers = ['ID', 'Username', 'Email', 'Registration Date', 'Status',
                  'Total Contracts', 'Active Contracts', 'Total Earnings', 
                  'Pending Withdrawals', 'Completed Withdrawals']
        writer.writerow(headers)
        
        users = User.query.all()
        for user in users:
            contracts = Contract.query.filter_by(user_id=user.id).all()
            active_contracts = sum(1 for c in contracts if c.is_active)
            
            # Получаем общий заработок пользователя
            total_earnings = Earning.query.filter_by(user_id=user.id).with_entities(
                db.func.sum(Earning.amount_btc)).scalar() or 0
            
            pending_withdrawals = Withdrawal.query.filter_by(
                user_id=user.id, 
                status='pending'
            ).with_entities(db.func.sum(Withdrawal.amount_btc)).scalar() or 0
            
            completed_withdrawals = Withdrawal.query.filter_by(
                user_id=user.id,
                status='success'
            ).with_entities(db.func.sum(Withdrawal.amount_btc)).scalar() or 0
            
            row = [
                user.id,
                user.username,
                user.email,
                user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Active' if user.is_active else 'Inactive',
                len(contracts),
                active_contracts,
                f"{total_earnings:.8f}",
                f"{pending_withdrawals:.8f}",
                f"{completed_withdrawals:.8f}"
            ]
            writer.writerow(row)
            
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'users_export_{timestamp}.csv'
        )
        
    except Exception as e:
        logger.error(f"Error in export_users: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/notifications', methods=['GET'])
@login_required
@admin_required
def notifications():
    # Убеждаемся, что таблица существует
    NotificationTemplate.ensure_table_exists()
    
    # Теперь безопасно запрашиваем шаблоны
    templates = NotificationTemplate.query.all()
    return render_template('admin/notifications.html', templates=templates)

@admin_bp.route('/api/notifications/template', methods=['POST', 'PUT'])
@login_required
@admin_required
def notification_template():
    """API для работы с шаблонами уведомлений"""
    try:
        # Обработка POST запроса (создание нового шаблона)
        if request.method == 'POST':
            data = request.json
            if not data or not data.get('key') or not data.get('content'):
                return jsonify({'success': False, 'message': 'Необходимо указать ключ и содержимое шаблона'}), 400
                
            key = data.get('key')
            content = data.get('content')
            
            existing = NotificationTemplate.query.filter_by(key=key).first()
            if existing:
                return jsonify({'success': False, 'message': 'Шаблон с таким ключом уже существует'}), 400
                
            new_template = NotificationTemplate(key=key, content=content)
            db.session.add(new_template)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Шаблон успешно добавлен'})
            
        # Обработка PUT запроса (обновление существующего шаблона)
        elif request.method == 'PUT':
            data = request.json
            if not data or not data.get('id') or not data.get('key') or not data.get('content'):
                return jsonify({'success': False, 'message': 'Неверные данные для обновления шаблона'}), 400
                
            template_id = data.get('id')
            key = data.get('key')
            content = data.get('content')
            
            template = NotificationTemplate.query.get(template_id)
            if not template:
                return jsonify({'success': False, 'message': 'Шаблон не найден'}), 404
                
            # Проверка уникальности ключа, если он изменился
            if template.key != key:
                existing = NotificationTemplate.query.filter_by(key=key).first()
                if existing and existing.id != int(template_id):
                    return jsonify({'success': False, 'message': 'Шаблон с таким ключом уже существует'}), 400
            
            template.key = key
            template.content = content
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Шаблон успешно обновлен'})
        
        else:
            return jsonify({'success': False, 'message': 'Метод не поддерживается'}), 405
            
    except Exception as e:
        db.session.rollback()
        error_trace = traceback.format_exc()
        logger.error(f"Ошибка при работе с шаблонами уведомлений: {str(e)}\n{error_trace}")
        return jsonify({'success': False, 'message': f'Произошла ошибка при обработке запроса: {str(e)}'}), 500

@admin_bp.route('/api/notifications/template/<int:template_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_notification_template(template_id):
    try:
        template = NotificationTemplate.query.get(template_id)
        if not template:
            return jsonify({"success": False, "message": "Шаблон не найден"}), 404
        
        db.session.delete(template)
        db.session.commit()
        return jsonify({"success": True, "message": "Шаблон успешно удален"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении шаблона уведомления: {str(e)}")
        return jsonify({"success": False, "message": "Произошла ошибка при удалении шаблона"}), 500

@admin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Переключение статуса пользователя"""
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({'success': True, 'is_active': user.is_active})

@admin_bp.route('/api/withdrawals/<int:withdrawal_id>/process', methods=['POST'])
@admin_required
def process_withdrawal(withdrawal_id):
    """Обработка вывода средств"""
    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    data = request.get_json()
    
    if data.get('action') == 'approve':
        withdrawal.status = 'success'
        withdrawal.processed_at = db.func.now()
        withdrawal.processed_by_id = current_user.id
        if data.get('transaction_id'):
            withdrawal.tx_hash = data.get('transaction_id')
        db.session.commit()
        return jsonify({'success': True, 'status': 'success'})
    elif data.get('action') == 'reject':
        withdrawal.status = 'cancelled'
        withdrawal.notes = data.get('reason')
        withdrawal.processed_at = db.func.now()
        withdrawal.processed_by_id = current_user.id
        db.session.commit()
        return jsonify({'success': True, 'status': 'cancelled'})
    
    return jsonify({'success': False, 'error': 'Invalid action'}), 400

@admin_bp.route('/api/process-withdrawal', methods=['POST'])
@admin_required
def api_process_withdrawal():
    """API для обработки запросов на вывод средств через AJAX"""
    try:
        data = request.get_json()
        
        if not data or 'withdrawal_id' not in data or 'action' not in data:
            return jsonify({'success': False, 'message': _('Недостаточно данных для обработки запроса')}), 400
        
        withdrawal_id = data.get('withdrawal_id')
        action = data.get('action')
        reason = data.get('reason', '')
        transaction_id = data.get('transaction_id', '')
        
        withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
        
        # Проверяем, что заявка в статусе ожидания
        if withdrawal.status != 'pending':
            return jsonify({'success': False, 'message': _('Эта заявка уже была обработана')}), 400
        
        if action == 'approve':
            # Подтверждаем заявку
            withdrawal.approve(current_user.id, transaction_id)
            
            # Добавляем примечание если есть
            if reason:
                withdrawal.notes = reason
            
            db.session.commit()
            
            # Отправляем уведомление пользователю
            try:
                # Подготавливаем контекст для шаблона
                context = {
                    'id': withdrawal.id,
                    'amount': format_btc(withdrawal.amount_btc),
                    'wallet': withdrawal.wallet_address
                }
                
                # Отправляем уведомление с использованием шаблона
                send_notification_with_template(
                    user_id=withdrawal.user_id,
                    template_key='withdrawal_approved',
                    title=_('Заявка на вывод средств одобрена'),
                    context=context,
                    notification_type='payment'
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю: {str(e)}")
            
            # Отправляем уведомление администратору через Telegram (если функция существует)
            if 'send_telegram_notification_to_admin' in globals():
                send_telegram_notification_to_admin(
                    _('Withdrawal Request Approved'),
                    _('Administrator %(admin)s has approved withdrawal request #%(id)s from user %(username)s for %(amount)s BTC.', 
                    admin=current_user.username, id=withdrawal.id, username=withdrawal.user.username, amount=withdrawal.amount_btc)
                )
            
            return jsonify({'success': True, 'message': _('Заявка на вывод средств успешно подтверждена')})
            
        elif action == 'reject':
            # Отклоняем заявку
            withdrawal.reject(current_user.id, reason)
            
            db.session.commit()
            
            # Отправляем уведомление пользователю
            try:
                # Подготавливаем контекст для шаблона
                context = {
                    'id': withdrawal.id,
                    'amount': format_btc(withdrawal.amount_btc),
                    'wallet': withdrawal.wallet_address,
                    'reason': reason or _('Причина не указана')
                }
                
                # Отправляем уведомление с использованием шаблона
                send_notification_with_template(
                    user_id=withdrawal.user_id,
                    template_key='withdrawal_rejected',
                    title=_('Заявка на вывод средств отклонена'),
                    context=context,
                    notification_type='payment'
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю: {str(e)}")
            
            # Отправляем уведомление администратору через Telegram (если функция существует)
            if 'send_telegram_notification_to_admin' in globals():
                send_telegram_notification_to_admin(
                    _('Withdrawal Request Rejected'),
                    _('Administrator %(admin)s has rejected withdrawal request #%(id)s from user %(username)s for %(amount)s BTC.\nReason: %(reason)s', 
                    admin=current_user.username, id=withdrawal.id, username=withdrawal.user.username, amount=withdrawal.amount_btc, reason=reason or 'Not provided')
                )
            
            return jsonify({'success': True, 'message': _('Заявка на вывод средств отклонена')})
        
        return jsonify({'success': False, 'message': _('Некорректное действие')}), 400
        
    except Exception as e:
        logger.error(f"Error processing withdrawal: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': _('Произошла ошибка при обработке запроса')}), 500

@admin_bp.route('/withdrawal/<int:id>')
@admin_required
def withdrawal_detail(id):
    """Страница с детальной информацией о выводе средств"""
    withdrawal = Withdrawal.query.get_or_404(id)
    
    # Получаем информацию о пользователе и его контрактах
    user = withdrawal.user
    contracts = Contract.query.filter_by(user_id=user.id).all()
    
    # Получаем информацию о балансе пользователя и его выводах
    total_earnings = sum(earning.amount_btc for earning in Earning.query.filter_by(user_id=user.id).all())
    total_withdrawals = sum(w.amount_btc for w in Withdrawal.query.filter_by(user_id=user.id, status='success').all())
    current_balance = total_earnings - total_withdrawals
    
    # Получаем историю выводов пользователя
    withdrawal_history = Withdrawal.query.filter_by(user_id=user.id).order_by(Withdrawal.date.desc()).all()
    
    return render_template('admin/withdrawal_detail.html', 
                          withdrawal=withdrawal,
                          user=user,
                          contracts=contracts,
                          total_earnings=total_earnings,
                          total_withdrawals=total_withdrawals,
                          current_balance=current_balance,
                          withdrawal_history=withdrawal_history)

@admin_bp.route('/api/settings/update', methods=['POST'])
@admin_required
def update_settings():
    """Обновление системных настроек"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    try:
        for key, value in data.items():
            setting = SystemSetting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = SystemSetting(key=key, value=value)
                db.session.add(setting)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/analytics', methods=['GET'])
@login_required
@admin_required
def analytics():
    # Получаем фильтры из запроса
    from_date_str = request.args.get('from_date', '')
    to_date_str = request.args.get('to_date', '')
    
    # Преобразуем строки в даты или используем значения по умолчанию
    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d') if from_date_str else datetime.now() - timedelta(days=30)
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d') if to_date_str else datetime.now()
        # Убедимся, что to_date включает весь день
        to_date = to_date.replace(hour=23, minute=59, second=59)
    except ValueError:
        from_date = datetime.now() - timedelta(days=30)
        to_date = datetime.now()
    
    # Получаем метрики для аналитики
    metrics = get_analytics_metrics(from_date, to_date)
    
    # Получаем данные для графиков
    users_growth_data = get_users_growth_data(from_date, to_date)
    earnings_data = get_earnings_data(from_date, to_date)
    countries_data = get_countries_data()
    contracts_data = get_contracts_data()
    
    return render_template(
        'admin/analytics.html', 
        metrics=metrics,
        users_growth_data=json.dumps(users_growth_data),
        earnings_data=json.dumps(earnings_data),
        countries_data=json.dumps(countries_data),
        contracts_data=json.dumps(contracts_data),
        from_date=from_date.strftime('%Y-%m-%d'),
        to_date=to_date.strftime('%Y-%m-%d')
    )

@admin_bp.route('/export/<data_type>', methods=['GET'])
@login_required
@admin_required
def export_data(data_type):
    from_date_str = request.args.get('from_date', '')
    to_date_str = request.args.get('to_date', '')
    
    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d') if from_date_str else datetime.now() - timedelta(days=30)
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d') if to_date_str else datetime.now()
        to_date = to_date.replace(hour=23, minute=59, second=59)
    except ValueError:
        from_date = datetime.now() - timedelta(days=30)
        to_date = datetime.now()
    
    if data_type == 'users':
        # Экспорт пользователей
        users = User.query.filter(User.created_at.between(from_date, to_date)).all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Username', 'Email', 'Registration Date', 'Status', 'Contracts', 'Total Earnings (BTC)', 'Total Withdrawals (BTC)'])
        
        for user in users:
            contracts_count = Contract.query.filter_by(user_id=user.id).count()
            total_earnings = sum(earning.amount for earning in user.earnings)
            total_withdrawals = sum(withdrawal.amount for withdrawal in user.withdrawals if withdrawal.status == 'completed')
            
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Active' if user.is_active else 'Inactive',
                contracts_count,
                format_btc(total_earnings),
                format_btc(total_withdrawals)
            ])
        
        output.seek(0)
        filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
    
    elif data_type == 'contracts':
        # Экспорт контрактов
        contracts = Contract.query.filter(Contract.created_at.between(from_date, to_date)).all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'User', 'Email', 'Plan', 'Amount (BTC)', 'Hash Rate (TH/s)', 'Status', 'Created Date'])
        
        for contract in contracts:
            user = User.query.get(contract.user_id)
            plan = ContractPlan.query.get(contract.plan_id) if contract.plan_id else None
            
            writer.writerow([
                contract.id,
                user.username if user else 'Unknown',
                user.email if user else 'Unknown',
                plan.name if plan else 'Custom',
                format_btc(contract.amount),
                contract.hash_rate,
                contract.status,
                contract.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        filename = f"contracts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
    
    elif data_type == 'transactions':
        # Экспорт транзакций
        transactions = Transaction.query.filter(Transaction.created_at.between(from_date, to_date)).all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'User', 'Email', 'Type', 'Amount (BTC)', 'Status', 'Description', 'Created Date'])
        
        for transaction in transactions:
            user = User.query.get(transaction.user_id)
            
            writer.writerow([
                transaction.id,
                user.username if user else 'Unknown',
                user.email if user else 'Unknown',
                transaction.type,
                format_btc(transaction.amount),
                transaction.status,
                transaction.description,
                transaction.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        filename = f"transactions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
    
    elif data_type == 'withdrawals':
        # Экспорт выводов средств
        withdrawals = Withdrawal.query.filter(Withdrawal.created_at.between(from_date, to_date)).all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'User', 'Email', 'Amount (BTC)', 'Wallet Address', 'Status', 'Created Date', 'Completed Date'])
        
        for withdrawal in withdrawals:
            user = User.query.get(withdrawal.user_id)
            
            writer.writerow([
                withdrawal.id,
                user.username if user else 'Unknown',
                user.email if user else 'Unknown',
                format_btc(withdrawal.amount),
                withdrawal.wallet_address,
                withdrawal.status,
                withdrawal.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                withdrawal.updated_at.strftime('%Y-%m-%d %H:%M:%S') if withdrawal.status == 'completed' else 'N/A'
            ])
        
        output.seek(0)
        filename = f"withdrawals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
    
    else:
        abort(404)

@admin_bp.route('/export_contracts')
@admin_required
def export_contracts():
    """Экспорт контрактов в CSV"""
    # Реализация экспорта контрактов в CSV
    pass

@admin_bp.route('/export_withdrawals')
@admin_required
def export_withdrawals():
    """Экспорт выводов средств в CSV"""
    status = request.args.get('status', 'all')
    search = request.args.get('search', '')
    period = request.args.get('period', 'all')
    
    # Формируем базовый запрос
    query = Withdrawal.query
    
    # Фильтруем по статусу, если указан
    if status != 'all':
        query = query.filter(Withdrawal.status == status)
    
    # Фильтруем по поисковому запросу, если указан
    if search:
        query = query.join(User).filter(
            or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                Withdrawal.wallet_address.ilike(f'%{search}%')
            )
        )
    
    # Фильтруем по периоду
    if period != 'all':
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if period == 'today':
            query = query.filter(Withdrawal.date >= today)
        elif period == 'week':
            start_of_week = today - timedelta(days=today.weekday())
            query = query.filter(Withdrawal.date >= start_of_week)
        elif period == 'month':
            start_of_month = today.replace(day=1)
            query = query.filter(Withdrawal.date >= start_of_month)
        elif period == 'year':
            start_of_year = today.replace(month=1, day=1)
            query = query.filter(Withdrawal.date >= start_of_year)
    
    # Получаем данные
    withdrawals = query.order_by(Withdrawal.date.desc()).all()
    
    # Создаем CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        'ID', 
        _('User'), 
        _('Email'), 
        _('Amount (BTC)'), 
        _('Fee (BTC)'), 
        _('Final Amount (BTC)'), 
        _('Wallet Address'), 
        _('Status'), 
        _('Transaction Hash'), 
        _('Notes'), 
        _('Request Date'), 
        _('Processed Date'), 
        _('Processed By')
    ])
    
    # Данные
    for withdrawal in withdrawals:
        writer.writerow([
            withdrawal.id,
            withdrawal.user.username,
            withdrawal.user.email,
            withdrawal.amount_btc,
            withdrawal.fee_btc if withdrawal.fee_btc else '0.0000',
            withdrawal.final_amount_btc if withdrawal.final_amount_btc else withdrawal.amount_btc,
            withdrawal.wallet_address,
            _(withdrawal.status.capitalize()),
            withdrawal.tx_hash if withdrawal.tx_hash else '',
            withdrawal.notes if withdrawal.notes else '',
            withdrawal.date.strftime('%Y-%m-%d %H:%M:%S'),
            withdrawal.processed_at.strftime('%Y-%m-%d %H:%M:%S') if withdrawal.processed_at else '',
            withdrawal.admin.username if withdrawal.admin else ''
        ])
    
    # Готовим ответ
    output.seek(0)
    filename = f"withdrawals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

# Вспомогательные функции для аналитики
def get_analytics_metrics(from_date, to_date):
    # Общая статистика
    total_users = User.query.count()
    new_users = User.query.filter(User.created_at.between(from_date, to_date)).count()
    previous_period = from_date - (to_date - from_date)
    previous_users = User.query.filter(User.created_at.between(previous_period, from_date)).count()
    users_change = calculate_percentage_change(previous_users, new_users)
    
    # Контракты
    active_contracts = Contract.query.filter_by(status='active').count()
    total_contracts = Contract.query.count()
    new_contracts = Contract.query.filter(Contract.created_at.between(from_date, to_date)).count()
    previous_contracts = Contract.query.filter(Contract.created_at.between(previous_period, from_date)).count()
    contracts_change = calculate_percentage_change(previous_contracts, new_contracts)
    
    # Доход и вывод средств
    total_earnings = db.session.query(func.sum(Earning.amount)).scalar() or 0
    period_earnings = db.session.query(func.sum(Earning.amount)).filter(
        Earning.created_at.between(from_date, to_date)
    ).scalar() or 0
    previous_earnings = db.session.query(func.sum(Earning.amount)).filter(
        Earning.created_at.between(previous_period, from_date)
    ).scalar() or 0
    earnings_change = calculate_percentage_change(previous_earnings, period_earnings)
    
    total_withdrawals = db.session.query(func.sum(Withdrawal.amount)).filter(
        Withdrawal.status == 'completed'
    ).scalar() or 0
    period_withdrawals = db.session.query(func.sum(Withdrawal.amount)).filter(
        Withdrawal.status == 'completed',
        Withdrawal.updated_at.between(from_date, to_date)
    ).scalar() or 0
    
    # Активные выводы средств
    pending_withdrawals = Withdrawal.query.filter_by(status='pending').count()
    pending_withdrawals_amount = db.session.query(func.sum(Withdrawal.amount)).filter(
        Withdrawal.status == 'pending'
    ).scalar() or 0
    
    return {
        'total_users': total_users,
        'new_users': new_users,
        'users_change': users_change,
        'active_contracts': active_contracts,
        'total_contracts': total_contracts,
        'new_contracts': new_contracts,
        'contracts_change': contracts_change,
        'total_earnings': format_btc(total_earnings),
        'period_earnings': format_btc(period_earnings),
        'earnings_change': earnings_change,
        'total_withdrawals': format_btc(total_withdrawals),
        'period_withdrawals': format_btc(period_withdrawals),
        'pending_withdrawals': pending_withdrawals,
        'pending_withdrawals_amount': format_btc(pending_withdrawals_amount)
    }

def calculate_percentage_change(old_value, new_value):
    if old_value == 0:
        return 100 if new_value > 0 else 0
    return ((new_value - old_value) / old_value) * 100

def get_users_growth_data(from_date, to_date):
    delta = to_date - from_date
    if delta.days <= 31:
        # По дням
        labels = []
        data = []
        current_date = from_date
        while current_date <= to_date:
            next_date = current_date + timedelta(days=1)
            count = User.query.filter(User.created_at.between(current_date, next_date)).count()
            labels.append(current_date.strftime('%d %b'))
            data.append(count)
            current_date = next_date
        return {'labels': labels, 'data': data}
    else:
        # По неделям
        labels = []
        data = []
        current_date = from_date
        while current_date <= to_date:
            next_date = current_date + timedelta(days=7)
            count = User.query.filter(User.created_at.between(current_date, next_date)).count()
            labels.append(f"{current_date.strftime('%d %b')} - {(next_date - timedelta(days=1)).strftime('%d %b')}")
            data.append(count)
            current_date = next_date
        return {'labels': labels, 'data': data}

def get_earnings_data(from_date, to_date):
    delta = to_date - from_date
    
    if delta.days <= 31:
        # По дням
        labels = []
        earnings_data = []
        withdrawals_data = []
        
        current_date = from_date
        while current_date <= to_date:
            next_date = current_date + timedelta(days=1)
            
            # Доходы
            earnings_sum = db.session.query(func.sum(Earning.amount)).filter(
                Earning.created_at.between(current_date, next_date)
            ).scalar() or 0
            
            # Выводы средств
            withdrawals_sum = db.session.query(func.sum(Withdrawal.amount)).filter(
                Withdrawal.status == 'completed',
                Withdrawal.updated_at.between(current_date, next_date)
            ).scalar() or 0
            
            labels.append(current_date.strftime('%d %b'))
            earnings_data.append(float(format_btc(earnings_sum)))
            withdrawals_data.append(float(format_btc(withdrawals_sum)))
            
            current_date = next_date
            
        return {
            'labels': labels, 
            'earnings': earnings_data, 
            'withdrawals': withdrawals_data
        }
    else:
        # По неделям
        labels = []
        earnings_data = []
        withdrawals_data = []
        
        current_date = from_date
        while current_date <= to_date:
            next_date = current_date + timedelta(days=7)
            
            # Доходы
            earnings_sum = db.session.query(func.sum(Earning.amount)).filter(
                Earning.created_at.between(current_date, next_date)
            ).scalar() or 0
            
            # Выводы средств
            withdrawals_sum = db.session.query(func.sum(Withdrawal.amount)).filter(
                Withdrawal.status == 'completed',
                Withdrawal.updated_at.between(current_date, next_date)
            ).scalar() or 0
            
            labels.append(f"{current_date.strftime('%d %b')} - {(next_date - timedelta(days=1)).strftime('%d %b')}")
            earnings_data.append(float(format_btc(earnings_sum)))
            withdrawals_data.append(float(format_btc(withdrawals_sum)))
            
            current_date = next_date
            
        return {
            'labels': labels, 
            'earnings': earnings_data, 
            'withdrawals': withdrawals_data
        }

def get_countries_data():
    # Получаем распределение пользователей по странам
    countries = db.session.query(
        User.country, 
        func.count(User.id).label('count')
    ).group_by(User.country).order_by(desc('count')).limit(10).all()
    
    labels = [country.country if country.country else 'Unknown' for country in countries]
    data = [country.count for country in countries]
    
    return {'labels': labels, 'data': data}

def get_contracts_data():
    # Получаем распределение контрактов по типам
    plans = db.session.query(
        ContractPlan.name,
        func.count(Contract.id).label('count')
    ).join(
        ContractPlan, 
        Contract.plan_id == ContractPlan.id
    ).group_by(ContractPlan.name).all()
    
    # Добавляем кастомные контракты (без плана)
    custom_contracts = Contract.query.filter(Contract.plan_id.is_(None)).count()
    
    labels = [plan.name for plan in plans]
    data = [plan.count for plan in plans]
    
    if custom_contracts > 0:
        labels.append('Custom')
        data.append(custom_contracts)
    
    return {'labels': labels, 'data': data}

@admin_bp.route('/api/settings/content/terms', methods=['POST'])
@admin_required
def update_terms():
    """Обновление условий использования."""
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'success': False, 'message': 'Содержимое не может быть пустым'}), 400
        
        # Сохраняем контент в системные настройки
        terms_setting = SystemSetting.get_by_key('terms_of_use')
        if terms_setting:
            terms_setting.value = content
        else:
            terms_setting = SystemSetting('terms_of_use', content)
            db.session.add(terms_setting)
        
        db.session.commit()
        current_app.logger.info(f"Условия использования обновлены администратором: {current_user.email}")
        
        return jsonify({'success': True, 'message': 'Условия использования успешно обновлены'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при обновлении условий использования: {str(e)}")
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

@admin_bp.route('/api/settings/content/privacy', methods=['POST'])
@admin_required
def update_privacy():
    """Обновление политики конфиденциальности."""
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'success': False, 'message': 'Содержимое не может быть пустым'}), 400
        
        # Сохраняем контент в системные настройки
        privacy_setting = SystemSetting.get_by_key('privacy_policy')
        if privacy_setting:
            privacy_setting.value = content
        else:
            privacy_setting = SystemSetting('privacy_policy', content)
            db.session.add(privacy_setting)
        
        db.session.commit()
        current_app.logger.info(f"Политика конфиденциальности обновлена администратором: {current_user.email}")
        
        return jsonify({'success': True, 'message': 'Политика конфиденциальности успешно обновлена'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при обновлении политики конфиденциальности: {str(e)}")
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

@admin_bp.route('/api/content/faq', methods=['GET'])
@admin_required
def get_faqs():
    """Получение списка FAQ."""
    try:
        faqs = FAQ.query.order_by(FAQ.id).all()
        return jsonify({
            'success': True,
            'faqs': [faq.to_dict() for faq in faqs]
        })
    except Exception as e:
        current_app.logger.error(f"Ошибка при получении FAQ: {str(e)}")
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

@admin_bp.route('/api/content/faq', methods=['POST'])
@admin_required
def add_faq():
    """Добавление нового FAQ."""
    try:
        data = request.get_json()
        question = data.get('question')
        answer = data.get('answer')
        
        if not question or not answer:
            return jsonify({'success': False, 'message': 'Вопрос и ответ обязательны'}), 400
        
        faq = FAQ(question=question, answer=answer)
        db.session.add(faq)
        db.session.commit()
        
        current_app.logger.info(f"Новый FAQ добавлен администратором: {current_user.email}")
        
        return jsonify({'success': True, 'message': 'FAQ успешно добавлен', 'faq': faq.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при добавлении FAQ: {str(e)}")
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

@admin_bp.route('/api/content/faq/<int:faq_id>', methods=['PUT'])
@admin_required
def update_faq(faq_id):
    """Обновление FAQ."""
    try:
        faq = FAQ.query.get(faq_id)
        if not faq:
            return jsonify({'success': False, 'message': 'FAQ не найден'}), 404
    
        data = request.get_json()
        question = data.get('question')
        answer = data.get('answer')
        
        if not question or not answer:
            return jsonify({'success': False, 'message': 'Вопрос и ответ обязательны'}), 400
        
        faq.question = question
        faq.answer = answer
        faq.updated_at = datetime.utcnow()
        
        db.session.commit()
        current_app.logger.info(f"FAQ #{faq_id} обновлен администратором: {current_user.email}")
        
        return jsonify({'success': True, 'message': 'FAQ успешно обновлен', 'faq': faq.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при обновлении FAQ: {str(e)}")
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

@admin_bp.route('/api/content/faq/<int:faq_id>', methods=['DELETE'])
@admin_required
def delete_faq(faq_id):
    """Удаление FAQ."""
    try:
        faq = FAQ.query.get(faq_id)
        if not faq:
            return jsonify({'success': False, 'message': 'FAQ не найден'}), 404
        
        db.session.delete(faq)
        db.session.commit()
        
        current_app.logger.info(f"FAQ #{faq_id} удален администратором: {current_user.email}")
        
        return jsonify({'success': True, 'message': 'FAQ успешно удален'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при удалении FAQ: {str(e)}")
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

@admin_bp.route('/api/admin/add_user', methods=['POST'])
@admin_required
def add_user():
    """API для добавления нового пользователя"""
    try:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form
        
        # Валидация
        if not username or not email or not password:
            flash(_('All fields are required'), 'danger')
            return redirect(url_for('admin.users'))
        
        # Проверка уникальности username и email
        existing_user = User.query.filter(or_(
            User.username == username,
            User.email == email
        )).first()
    
        if existing_user:
            flash(_('Username or email already exists'), 'danger')
            return redirect(url_for('admin.users'))
        
        # Создание нового пользователя
        new_user = User(
            username=username,
            email=email,
            is_admin=is_admin,
            is_active=True,
            created_at=datetime.utcnow()
        )
        new_user.set_password(password)
    
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"Admin {current_user.username} created new user: {username}")
        flash(_('User has been added successfully'), 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding user: {str(e)}")
        flash(_('An error occurred while adding user'), 'danger')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/api/admin/update_user', methods=['POST'])
@admin_required
def update_user():
    """API для обновления данных пользователя"""
    try:
        user_id = request.form.get('user_id')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_active = 'is_active' in request.form
        is_admin = 'is_admin' in request.form
        
        user = User.query.get_or_404(user_id)
        
        # Проверка уникальности username и email
        existing_user = User.query.filter(and_(
            or_(User.username == username, User.email == email),
            User.id != user.id
        )).first()
        
        if existing_user:
            flash(_('Username or email already exists'), 'danger')
            return redirect(url_for('admin.users'))
    
        # Обновляем данные пользователя
        user.username = username
        user.email = email
        user.is_active = is_active
        user.is_admin = is_admin
        
        # Обновляем пароль только если он был предоставлен
        if password:
            user.set_password(password)
        
        db.session.commit()
        
        logger.info(f"Admin {current_user.username} updated user: {username}")
        flash(_('User has been updated successfully'), 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user: {str(e)}")
        flash(_('An error occurred while updating user'), 'danger')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/api/admin/delete_user', methods=['POST'])
@admin_required
def delete_user():
    """API для удаления пользователя"""
    try:
        user_id = request.form.get('user_id')
        user = User.query.get_or_404(user_id)
        
        # Предотвращаем удаление самого себя
        if user.id == current_user.id:
            flash(_('You cannot delete your own account'), 'danger')
            return redirect(url_for('admin.users'))
        
        username = user.username
        
        # Удаляем связанные данные
        Withdrawal.query.filter_by(user_id=user.id).delete()
        Earning.query.filter_by(user_id=user.id).delete()
        Transaction.query.filter_by(user_id=user.id).delete()
        Contract.query.filter_by(user_id=user.id).delete()
        
        # Удаляем пользователя
        db.session.delete(user)
        db.session.commit()
        
        logger.info(f"Admin {current_user.username} deleted user: {username}")
        flash(_('User has been deleted successfully'), 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user: {str(e)}")
        flash(_('An error occurred while deleting user'), 'danger')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/api/content/settings', methods=['POST'])
@admin_required
def content_settings():
    """Обновление настроек контента (Terms of Use, Privacy Policy)"""
    try:
        # Проверяем, есть ли файлы
        terms_file = request.files.get('terms_file')
        privacy_file = request.files.get('privacy_file')
        
        # Обрабатываем загрузку Terms of Use файла, если он есть
        if terms_file and terms_file.filename:
            filename = secure_filename(terms_file.filename)
            file_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            terms_file.save(file_path)
            
            # Обновляем настройку с путем к файлу
            SystemSetting.set_value('terms_file', f'/static/uploads/{filename}', 'Файл с условиями использования')
        
        # Обрабатываем загрузку Privacy Policy файла, если он есть
        if privacy_file and privacy_file.filename:
            filename = secure_filename(privacy_file.filename)
            file_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            privacy_file.save(file_path)
            
            # Обновляем настройку с путем к файлу
            SystemSetting.set_value('privacy_file', f'/static/uploads/{filename}', 'Файл с политикой конфиденциальности')
        
        # Обрабатываем текстовый контент
        terms_content = request.form.get('terms_content')
        if terms_content:
            SystemSetting.set_value('terms_content', terms_content, 'Контент условий использования')
        
        privacy_content = request.form.get('privacy_content')
        if privacy_content:
            SystemSetting.set_value('privacy_content', privacy_content, 'Контент политики конфиденциальности')
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating content settings: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/earnings/process', methods=['POST'])
@login_required
@admin_required
def manual_process_earnings():
    """Ручной запуск процесса ежедневных начислений"""
    try:
        from app.utils.tasks import process_daily_earnings
        
        # Запускаем процесс начислений
        result = process_daily_earnings()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': _('Ежедневные начисления успешно обработаны'),
                'data': {
                    'contracts_processed': result['contracts_processed'],
                    'total_amount_btc': format_btc(result['total_amount_btc']),
                    'notifications_sent': result['notifications_sent']
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': _('Ошибка при обработке начислений: %(error)s', error=result['error'])
            }), 500 

    except Exception as e:
        logger.error(f"Ошибка при ручном запуске начислений: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/plans')
@login_required
@admin_required
def plans():
    """Страница управления тарифными планами"""
    plans = ContractPlan.query.order_by(ContractPlan.hashrate).all()
    return render_template('admin/plans.html', plans=plans, active_page='plans')

@admin_bp.route('/api/plans/create', methods=['POST'])
@login_required
@admin_required
def create_plan():
    """API для создания нового тарифного плана"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': _('No data provided')}), 400
        
        # Проверка наличия всех необходимых полей
        required_fields = ['name', 'type', 'hashrate', 'price_usd', 'price_btc', 'maintenance_fee']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': _(f'Field {field} is required')}), 400
        
        # Создание нового плана
        plan = ContractPlan(
            name=data['name'],
            type=data['type'],
            hashrate=float(data['hashrate']),
            duration=int(data['duration']) if data.get('duration') else None,
            price_usd=float(data['price_usd']),
            price_btc=float(data['price_btc']),
            maintenance_fee=float(data['maintenance_fee']),
            is_active=data.get('is_active', True),
            description=data.get('description', '')
        )
        
        db.session.add(plan)
        db.session.commit()
    
        current_app.logger.info(f"Admin {current_user.email} created new mining plan: {plan.name}")
        
        return jsonify({
            'success': True,
            'message': _('Mining plan created successfully'),
            'plan_id': plan.id
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating mining plan: {str(e)}")
        return jsonify({'success': False, 'message': _('An error occurred while creating the mining plan')}), 500

@admin_bp.route('/api/plans/update', methods=['POST'])
@login_required
@admin_required
def update_plan():
    """API для обновления настроек тарифного плана"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': _('No data provided')}), 400
        
        # Проверка наличия ID и всех необходимых полей
        if 'id' not in data:
            return jsonify({'success': False, 'message': _('Plan ID is required')}), 400
        
        required_fields = ['name', 'type', 'hashrate', 'price_usd', 'price_btc', 'maintenance_fee']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': _(f'Field {field} is required')}), 400
        
        # Поиск плана по ID
        plan = ContractPlan.query.get(data['id'])
        if not plan:
            return jsonify({'success': False, 'message': _('Mining plan not found')}), 404
        
        # Обновление данных плана
        plan.name = data['name']
        plan.type = data['type']
        plan.hashrate = float(data['hashrate'])
        plan.duration = int(data['duration']) if data.get('duration') else None
        plan.price_usd = float(data['price_usd'])
        plan.price_btc = float(data['price_btc'])
        plan.maintenance_fee = float(data['maintenance_fee'])
        plan.is_active = data.get('is_active', True)
        plan.description = data.get('description', '')
    
        db.session.commit()
    
        current_app.logger.info(f"Admin {current_user.email} updated mining plan: {plan.name} (ID: {plan.id})")
    
        return jsonify({
            'success': True,
            'message': _('Mining plan updated successfully')
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating mining plan: {str(e)}")
        return jsonify({'success': False, 'message': _('An error occurred while updating the mining plan')}), 500

@admin_bp.route('/api/plans/<int:plan_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_plan(plan_id):
    """API для удаления тарифного плана"""
    try:
        # Поиск плана по ID
        plan = ContractPlan.query.get(plan_id)
        if not plan:
            return jsonify({'success': False, 'message': _('Mining plan not found')}), 404
        
        # Проверка наличия активных контрактов с этим планом
        contracts = Contract.query.filter_by(plan_id=plan.id, status='active').first()
        if contracts:
            return jsonify({'success': False, 'message': _('Cannot delete plan with active contracts')}), 400
        
        plan_name = plan.name
        plan_id = plan.id
        
        # Удаляем план
        db.session.delete(plan)
        db.session.commit()
        
        current_app.logger.info(f"Admin {current_user.email} deleted mining plan: {plan_name} (ID: {plan_id})")
        
        return jsonify({
            'success': True, 
            'message': _('Mining plan deleted successfully')
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting mining plan: {str(e)}")
        return jsonify({'success': False, 'message': _('An error occurred while deleting the mining plan')}), 500