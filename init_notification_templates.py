from flask.cli import with_appcontext
from app import create_app, db
from app.models.notification import NotificationTemplate
import click
import datetime

app = create_app()

@click.command('init-notification-templates')
@with_appcontext
def init_notification_templates():
    """Инициализирует таблицу notification_templates и добавляет примеры шаблонов."""
    try:
        # Пытаемся создать все таблицы (включая notification_templates)
        db.create_all()
        click.echo('База данных проинициализирована')
        
        # Проверяем, есть ли уже шаблоны в базе
        count = NotificationTemplate.query.count()
        if count > 0:
            click.echo(f'В базе уже есть {count} шаблонов уведомлений')
            return
        
        # Добавляем базовые шаблоны
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
        
        # Устанавливаем даты создания и обновления
        now = datetime.datetime.utcnow()
        for template in templates:
            template.created_at = now
            template.updated_at = now
            db.session.add(template)
        
        db.session.commit()
        click.echo(f'Добавлено {len(templates)} шаблонов уведомлений')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'Ошибка при инициализации шаблонов уведомлений: {str(e)}')

app.cli.add_command(init_notification_templates)

if __name__ == '__main__':
    with app.app_context():
        init_notification_templates() 