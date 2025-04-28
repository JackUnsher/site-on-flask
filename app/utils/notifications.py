from app import db
from app.models.notification import Notification, NotificationTemplate


def send_notification(user_id, title, message, notification_type='system'):
    """
    Отправляет уведомление пользователю
    
    :param user_id: ID пользователя
    :param title: Заголовок уведомления
    :param message: Текст уведомления
    :param notification_type: Тип уведомления (system, contract, payment, security)
    :return: Объект уведомления
    """
    # Создаем новое уведомление
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        is_read=False
    )
    
    # Добавляем в базу данных
    db.session.add(notification)
    db.session.commit()
    
    return notification


def send_notification_with_template(user_id, template_key, title, context=None, notification_type='system'):
    """
    Отправляет уведомление пользователю, используя шаблон
    
    :param user_id: ID пользователя
    :param template_key: Ключ шаблона уведомления
    :param title: Заголовок уведомления
    :param context: Словарь с переменными для подстановки в шаблон
    :param notification_type: Тип уведомления (system, contract, payment, security)
    :return: Объект уведомления или None в случае ошибки
    """
    try:
        # Получаем шаблон по ключу
        template = NotificationTemplate.get_by_key(template_key)
        if not template:
            return None
        
        # Подготавливаем контекст
        if context is None:
            context = {}
        
        # Форматируем сообщение, подставляя переменные из контекста
        try:
            message = template.content.format(**context)
        except KeyError as e:
            # Если в шаблоне используются переменные, которых нет в контексте
            message = f"Ошибка в шаблоне уведомления: отсутствует переменная {str(e)}"
        
        # Отправляем уведомление
        return send_notification(user_id, title, message, notification_type)
    except Exception as e:
        print(f"Ошибка при отправке уведомления с шаблоном: {str(e)}")
        return None


def send_bulk_notification(user_ids, title, message, notification_type='system'):
    """
    Отправляет уведомление нескольким пользователям
    
    :param user_ids: Список ID пользователей
    :param title: Заголовок уведомления
    :param message: Текст уведомления
    :param notification_type: Тип уведомления (system, contract, payment, security)
    :return: Количество отправленных уведомлений
    """
    # Создаем список объектов уведомлений
    notifications = []
    
    for user_id in user_ids:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            is_read=False
        )
        notifications.append(notification)
    
    # Добавляем все уведомления в базу данных
    db.session.add_all(notifications)
    db.session.commit()
    
    return len(notifications)


def send_bulk_notification_with_template(user_ids, template_key, title, context=None, notification_type='system'):
    """
    Отправляет уведомление нескольким пользователям, используя шаблон
    
    :param user_ids: Список ID пользователей
    :param template_key: Ключ шаблона уведомления
    :param title: Заголовок уведомления
    :param context: Словарь с переменными для подстановки в шаблон
    :param notification_type: Тип уведомления (system, contract, payment, security)
    :return: Количество отправленных уведомлений
    """
    try:
        # Получаем шаблон по ключу
        template = NotificationTemplate.get_by_key(template_key)
        if not template:
            return 0
        
        # Подготавливаем контекст
        if context is None:
            context = {}
        
        # Форматируем сообщение, подставляя переменные из контекста
        try:
            message = template.content.format(**context)
        except KeyError as e:
            # Если в шаблоне используются переменные, которых нет в контексте
            message = f"Ошибка в шаблоне уведомления: отсутствует переменная {str(e)}"
        
        # Отправляем уведомления
        return send_bulk_notification(user_ids, title, message, notification_type)
    except Exception as e:
        print(f"Ошибка при отправке массовых уведомлений с шаблоном: {str(e)}")
        return 0


def mark_notification_as_read(notification_id):
    """
    Помечает уведомление как прочитанное
    
    :param notification_id: ID уведомления
    :return: Объект уведомления или None, если уведомление не найдено
    """
    notification = Notification.query.get(notification_id)
    if notification:
        notification.is_read = True
        db.session.commit()
    return notification


def mark_all_notifications_as_read(user_id):
    """
    Помечает все уведомления пользователя как прочитанные
    
    :param user_id: ID пользователя
    :return: Количество обновленных уведомлений
    """
    # Находим все непрочитанные уведомления пользователя
    unread_notifications = Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).all()
    
    # Помечаем их как прочитанные
    for notification in unread_notifications:
        notification.is_read = True
    
    db.session.commit()
    
    return len(unread_notifications) 