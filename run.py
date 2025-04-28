from app import create_app, db
from app.models import (
    User, Setting, Wallet,
    Contract, ContractPlan,
    Transaction, Earning, Withdrawal,
    SupportChat, SupportMessage,
    Content, FaqItem,
    Notification, NotificationTemplate,
    SystemSetting,
    FAQ
)
from app.utils.settings import SettingsManager
from datetime import datetime
import click
from flask.cli import with_appcontext
from config import config
import sys
import argparse

print("Запуск приложения...")
print(f"Python version: {sys.version}")
print(f"Текущая директория: {sys.path}")

try:
    app = create_app(config['development'])
    print("Приложение успешно создано!")
except Exception as e:
    print(f"Ошибка при создании приложения: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Setting': Setting,
        'Wallet': Wallet,
        'Contract': Contract,
        'ContractPlan': ContractPlan,
        'Transaction': Transaction,
        'Earning': Earning,
        'Withdrawal': Withdrawal,
        'SupportChat': SupportChat,
        'SupportMessage': SupportMessage,
        'Content': Content,
        'FaqItem': FaqItem,
        'Notification': Notification,
        'NotificationTemplate': NotificationTemplate,
        'SystemSetting': SystemSetting,
        'FAQ': FAQ,
        'SettingsManager': SettingsManager
    }


@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


# Инициализация настроек будет происходить при создании приложения в app/__init__.py


@click.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@with_appcontext
def create_admin(username, email, password):
    """Создает админа с указанными данными."""
    try:
        user = User(username=username, email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f'Администратор {username} успешно создан.')
    except Exception as e:
        click.echo(f'Ошибка: {str(e)}')


@click.command('init-settings')
@with_appcontext
def init_settings():
    """Инициализирует настройки системы."""
    try:
        SettingsManager.init_settings()
        click.echo('Настройки системы успешно инициализированы.')
    except Exception as e:
        click.echo(f'Ошибка при инициализации настроек: {str(e)}')


app.cli.add_command(create_admin)
app.cli.add_command(init_settings)


if __name__ == '__main__':
    print("Запуск веб-сервера...")
    
    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    
    # Инициализируем настройки при запуске в режиме разработки
    try:
        with app.app_context():
            SettingsManager.init_settings()
            print("Настройки инициализированы успешно!")
            
            # Добавляем планы майнинга, если их еще нет
            if ContractPlan.query.filter_by(name='Minimum').first() is None:
                print("Добавление новых тарифных планов...")
                plans = [
                    {
                        'name': 'Minimum',
                        'type': 'standard',
                        'hashrate': 5,
                        'duration': 365,  # 1 год
                        'price_usd': 500,
                        'price_btc': 0.01,
                        'maintenance_fee': 10,
                        'is_active': True,
                        'description': 'Contract duration: 1 year. Minimum BTC withdrawal amount to an external wallet. Annual electricity fee is included in the plan.'
                    },
                    {
                        'name': 'Basic',
                        'type': 'standard',
                        'hashrate': 25,
                        'duration': 365,  # 1 год
                        'price_usd': 2000,
                        'price_btc': 0.04,
                        'maintenance_fee': 10,
                        'is_active': True,
                        'description': 'Contract duration: 1 year. Minimum BTC withdrawal amount to an external wallet. Annual electricity fee is included in the plan.'
                    },
                    {
                        'name': 'Optimal',
                        'type': 'premium',
                        'hashrate': 50,
                        'duration': 365,  # 1 год
                        'price_usd': 4000,
                        'price_btc': 0.08,
                        'maintenance_fee': 10,
                        'is_active': True,
                        'description': 'Contract duration: 1 year. Minimum BTC withdrawal amount to an external wallet. Annual electricity fee is included in the plan.'
                    },
                    {
                        'name': 'Premium',
                        'type': 'premium',
                        'hashrate': 100,
                        'duration': 365,  # 1 год
                        'price_usd': 7500,
                        'price_btc': 0.15,
                        'maintenance_fee': 10,
                        'is_active': True,
                        'description': 'Contract duration: 1 year. Minimum BTC withdrawal amount to an external wallet. Annual electricity fee is included in the plan.'
                    }
                ]
                
                for plan_data in plans:
                    plan = ContractPlan(**plan_data)
                    db.session.add(plan)
                
                db.session.commit()
                print("Новые тарифные планы успешно добавлены!")
            else:
                print("Планы майнинга уже существуют")
    except Exception as e:
        print(f"Ошибка при инициализации настроек: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Запускаем приложение на указанном порту
    app.run(host='0.0.0.0', port=args.port, debug=False) 