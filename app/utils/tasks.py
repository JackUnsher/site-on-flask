from app import db, logger
from app.models.support import SupportChat, SupportMessage
from app.utils.settings import SettingsManager
from app.utils.telegram_bot import send_telegram_notification_to_admin
from datetime import datetime, timedelta
from flask import current_app
import logging
from app.models.notification import NotificationTemplate
from app.models.transaction import Earning
from app.models.contract import Contract
from app.models.user import User
from app.utils.notifications import send_notification_with_template
from app.utils.format import format_btc
from flask_babel import _
import random
import traceback

# Настройка логгера
logger = logging.getLogger(__name__)

def close_inactive_chats():
    """
    Автоматически закрывает неактивные чаты поддержки.
    """
    try:
        # Получаем настройку "максимальное время неактивности" из системных настроек
        days_to_close = int(SettingsManager.get_setting('support.auto_close_days', default=5))
        
        # Если настройка равна 0, отключаем автоматическое закрытие
        if days_to_close <= 0:
            logger.info("Automatic chat closing is disabled")
            return
        
        # Вычисляем дату, после которой чаты считаются неактивными
        inactive_date = datetime.utcnow() - timedelta(days=days_to_close)
        
        # Получаем все открытые чаты с последним сообщением старше указанной даты
        open_chats = SupportChat.query.filter(
            SupportChat.is_closed == False,
            SupportChat.updated_at < inactive_date
        ).all()
        
        if not open_chats:
            logger.info("No inactive chats to close")
            return
        
        closed_count = 0
        # Закрываем неактивные чаты
        for chat in open_chats:
            # Проверяем, было ли последнее сообщение отправлено давно
            last_message = SupportMessage.query.filter_by(
                chat_id=chat.id
            ).order_by(SupportMessage.timestamp.desc()).first()
            
            # Если последнее сообщение старше указанного срока
            if last_message and last_message.timestamp < inactive_date:
                # Добавляем системное сообщение о закрытии чата
                system_message = SupportMessage(
                    chat_id=chat.id,
                    user_id=None,  # Системное сообщение
                    content=f"Этот чат был автоматически закрыт системой после {days_to_close} дней неактивности",
                    is_from_user=False,
                    is_read=True,
                    is_system=True
                )
                db.session.add(system_message)
                
                # Закрываем чат
                chat.is_closed = True
                closed_count += 1
                
                logger.info(f"Automatically closed inactive chat #{chat.id} for user #{chat.user_id}")
                
        if closed_count > 0:
            # Сохраняем изменения в базе данных
            db.session.commit()
            
            # Отправляем уведомление администратору
            send_telegram_notification_to_admin(
                f"Автоматически закрыто {closed_count} неактивных чатов поддержки"
            )
            
            logger.info(f"Closed {closed_count} inactive support chats automatically")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in automatic chat closing task: {str(e)}")


def process_daily_earnings():
    """
    Обрабатывает ежедневные начисления для всех активных контрактов
    и отправляет уведомления пользователям.
    """
    try:
        # Текущая дата и время для логов
        now = datetime.utcnow()
        logger.info(f"Начало обработки ежедневных начислений: {now}")

        # Получаем все активные контракты
        active_contracts = Contract.query.filter_by(status='active').all()
        logger.info(f"Найдено {len(active_contracts)} активных контрактов")

        # Статистика для логов
        total_contracts_processed = 0
        total_amount_btc = 0
        total_notifications_sent = 0
        failed_notifications = 0

        # Словарь для группировки начислений по пользователям
        user_earnings = {}

        # Обрабатываем каждый контракт
        for contract in active_contracts:
            try:
                # Проверяем, не истек ли контракт
                if contract.check_expiration():
                    logger.info(f"Контракт #{contract.id} истек и был помечен как expired")
                    continue

                # Рассчитываем дневной заработок
                daily_earning = contract.daily_earning_estimate
                
                # Добавляем немного случайности для реализма (±10%)
                variation = random.uniform(-0.1, 0.1)
                daily_earning = daily_earning * (1 + variation)
                
                # Создаем запись о начислении
                earning = Earning(
                    user_id=contract.user_id,
                    contract_id=contract.id,
                    amount_btc=daily_earning,
                    amount_usd=daily_earning * 40000,  # Примерная стоимость BTC, лучше получать из API
                    electricity_fee=daily_earning * 0.1,  # 10% на электричество
                    date=now
                )
                
                db.session.add(earning)
                
                # Группируем начисления по пользователям для отправки общего уведомления
                if contract.user_id not in user_earnings:
                    user_earnings[contract.user_id] = []
                
                user_earnings[contract.user_id].append({
                    'contract_id': contract.id,
                    'amount_btc': daily_earning
                })
                
                total_contracts_processed += 1
                total_amount_btc += daily_earning
            
            except Exception as e:
                logger.error(f"Ошибка при обработке контракта #{contract.id}: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Сохраняем начисления в базу данных
        db.session.commit()
        logger.info(f"Обработано {total_contracts_processed} контрактов, начислено {format_btc(total_amount_btc)} BTC")
        
        # Отправляем уведомления пользователям об их начислениях
        for user_id, earnings in user_earnings.items():
            try:
                # Если у пользователя только один контракт
                if len(earnings) == 1:
                    earning_data = earnings[0]
                    context = {
                        'contract_id': earning_data['contract_id'],
                        'amount': format_btc(earning_data['amount_btc'])
                    }
                    
                    # Отправляем уведомление с использованием шаблона
                    result = send_notification_with_template(
                        user_id=user_id,
                        template_key='earnings',
                        title=_('Новое начисление'),
                        context=context,
                        notification_type='contract'
                    )
                    
                    if result:
                        total_notifications_sent += 1
                    else:
                        failed_notifications += 1
                
                # Если у пользователя несколько контрактов
                else:
                    total_amount = sum(item['amount_btc'] for item in earnings)
                    contracts_count = len(earnings)
                    
                    # Создаем персонализированное сообщение
                    title = _('Ежедневные начисления')
                    message = _('Вы получили %(amount)s BTC от %(count)d ваших контрактов.', 
                                amount=format_btc(total_amount), 
                                count=contracts_count)
                    
                    # Отправляем обычное уведомление (не используя шаблон)
                    from app.utils.notifications import send_notification
                    result = send_notification(
                        user_id=user_id,
                        title=title,
                        message=message,
                        notification_type='contract'
                    )
                    
                    if result:
                        total_notifications_sent += 1
                    else:
                        failed_notifications += 1
            
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю #{user_id}: {str(e)}")
                logger.error(traceback.format_exc())
                failed_notifications += 1
        
        logger.info(f"Отправлено {total_notifications_sent} уведомлений, не удалось отправить {failed_notifications}")
        logger.info(f"Завершение обработки ежедневных начислений: {datetime.utcnow()}")
        
        return {
            'success': True,
            'contracts_processed': total_contracts_processed,
            'total_amount_btc': total_amount_btc,
            'notifications_sent': total_notifications_sent,
            'failed_notifications': failed_notifications
        }
    
    except Exception as e:
        logger.error(f"Критическая ошибка при обработке ежедневных начислений: {str(e)}")
        logger.error(traceback.format_exc())
        
        db.session.rollback()
        
        return {
            'success': False,
            'error': str(e)
        } 