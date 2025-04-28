import os
import sys
import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from app import create_app, db
from app.models.user import User, Setting
from app.models.content import Content, FaqItem
from app.models.contract import Contract, ContractPlan
from app.models.transaction import Transaction, Earning, Withdrawal
from app.models.support import SupportChat, SupportMessage
from app.models.notification import Notification
from app.models.system_setting import SystemSetting

app = create_app()

@click.group()
def cli():
    """Команды управления приложением"""
    pass

@cli.command()
@with_appcontext
def create_tables():
    """Создает все таблицы в базе данных"""
    click.echo('Создание таблиц базы данных...')
    db.create_all()
    click.echo('Таблицы успешно созданы.')

@cli.command()
@with_appcontext
def init_db():
    """Инициализирует базу данных с базовыми данными"""
    click.echo('Создание таблиц базы данных...')
    db.create_all()
    click.echo('Таблицы успешно созданы.')
    
    # Создаем администратора, если его нет
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        click.echo('Создание пользователя-администратора...')
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
    
    # Создаем базовые настройки системы
    if not SystemSetting.get_by_key('site_name'):
        click.echo('Создание базовых настроек системы...')
        SystemSetting.set_value('site_name', 'Mining Platform', 'Название сайта')
        SystemSetting.set_value('maintenance_mode', '0', 'Режим обслуживания (1 - включен, 0 - выключен)', True)
        SystemSetting.set_value('registration_enabled', '1', 'Возможность регистрации (1 - включена, 0 - выключена)', True)
    
    # Создаем базовые тарифные планы
    if ContractPlan.query.count() == 0:
        click.echo('Создание базовых тарифных планов...')
        plans = [
            {
                'name': 'Starter',
                'type': 'standard',
                'hashrate': 10.0,
                'duration': 30,
                'price_usd': 99.0,
                'price_btc': 0.0025,
                'maintenance_fee': 10.0,
                'description': 'Basic mining plan for beginners'
            },
            {
                'name': 'Professional',
                'type': 'premium',
                'hashrate': 50.0,
                'duration': 180,
                'price_usd': 499.0,
                'price_btc': 0.012,
                'maintenance_fee': 8.0,
                'description': 'Advanced mining plan for professionals'
            },
            {
                'name': 'Enterprise',
                'type': 'lifetime',
                'hashrate': 100.0,
                'duration': None,
                'price_usd': 999.0,
                'price_btc': 0.025,
                'maintenance_fee': 7.0,
                'description': 'Lifetime mining solution for enterprises'
            }
        ]
        
        for plan_data in plans:
            plan = ContractPlan(**plan_data)
            db.session.add(plan)
    
    # Создаем базовые страницы контента
    if Content.query.count() == 0:
        click.echo('Создание базовых страниц контента...')
        contents = [
            {
                'type': 'about',
                'title': 'О нас',
                'content': 'Мы предоставляем высококачественные решения для майнинга криптовалют.',
                'is_html': False
            },
            {
                'type': 'terms',
                'title': 'Условия использования',
                'content': 'Условия использования нашего сервиса.',
                'is_html': False
            },
            {
                'type': 'privacy',
                'title': 'Политика конфиденциальности',
                'content': 'Наша политика конфиденциальности и обработки данных.',
                'is_html': False
            },
            {
                'type': 'contact',
                'title': 'Контактная информация',
                'content': 'Email: support@example.com\nТелефон: +1 234 567 890',
                'is_html': False
            },
            {
                'type': 'faq',
                'title': 'Часто задаваемые вопросы',
                'content': 'Ответы на часто задаваемые вопросы.',
                'is_html': False
            }
        ]
        
        for content_data in contents:
            content = Content(**content_data)
            db.session.add(content)
    
    # Создаем базовые FAQ
    if FaqItem.query.count() == 0:
        click.echo('Создание базовых FAQ...')
        faqs = [
            {
                'question': 'Что такое биткоин-майнинг?',
                'answer': 'Биткоин-майнинг - это процесс создания новых биткоинов путем решения сложных математических задач.',
                'category': 'general',
                'order': 1
            },
            {
                'question': 'Как рассчитывается доход от майнинга?',
                'answer': 'Доход рассчитывается на основе вашего хешрейта, текущей цены биткоина и сложности сети.',
                'category': 'earnings',
                'order': 1
            },
            {
                'question': 'Какова минимальная сумма для вывода?',
                'answer': 'Минимальная сумма для вывода составляет 0.001 BTC.',
                'category': 'withdrawals',
                'order': 1
            }
        ]
        
        for faq_data in faqs:
            faq = FaqItem(**faq_data)
            db.session.add(faq)
    
    # Сохраняем изменения
    db.session.commit()
    click.echo('База данных успешно инициализирована!')

@cli.command()
@with_appcontext
def drop_tables():
    """Удаляет все таблицы из базы данных"""
    if click.confirm('Вы уверены, что хотите удалить все таблицы? Это действие невозможно отменить!'):
        click.echo('Удаление всех таблиц...')
        db.drop_all()
        click.echo('Все таблицы удалены.')
    else:
        click.echo('Операция отменена.')

if __name__ == '__main__':
    cli() 