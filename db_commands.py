"""
Команды для выполнения в Flask shell:

from app import db
from app.models.notification import NotificationTemplate
import datetime

# Создаем все таблицы
db.create_all()

# Добавляем шаблоны уведомлений
templates = [
    NotificationTemplate(
        key="welcome",
        content="Добро пожаловать на нашу платформу, {username}! Мы рады приветствовать вас."
    ),
    NotificationTemplate(
        key="withdrawal_approved",
        content="Ваша заявка на вывод средств #{id} успешно обработана. Сумма {amount} BTC отправлена на ваш кошелек {wallet}."
    ),
    NotificationTemplate(
        key="withdrawal_rejected",
        content="Ваша заявка на вывод средств #{id} была отклонена. Причина: {reason}. Пожалуйста, свяжитесь с поддержкой для получения дополнительной информации."
    ),
    NotificationTemplate(
        key="earnings",
        content="Поздравляем! Вы получили {amount} BTC от вашего контракта #{contract_id}."
    )
]

# Устанавливаем даты
now = datetime.datetime.utcnow()
for template in templates:
    template.created_at = now
    template.updated_at = now
    db.session.add(template)

# Сохраняем изменения
db.session.commit()

# Проверяем, что шаблоны созданы
count = NotificationTemplate.query.count()
print(f"В базе {count} шаблонов уведомлений")

# Выводим список шаблонов
for template in NotificationTemplate.query.all():
    print(f"ID: {template.id}, Key: {template.key}")
""" 