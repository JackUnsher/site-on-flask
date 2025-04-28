from app import create_app, db
from app.models.user import User, Setting
from app.models.content import Content, FaqItem
from app.models.contract import Contract, ContractPlan
from app.models.transaction import Transaction, Earning, Withdrawal
from app.models.support import SupportChat, SupportMessage
from app.models.notification import Notification
from datetime import datetime
from config import config

# Создаем приложение и контекст
app = create_app(config['production'])
with app.app_context():
    print('Создание таблиц базы данных...')
    try:
        db.create_all()
        print('Таблицы успешно созданы.')
        
        # Создаем администратора, если его нет
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            print('Создание пользователя-администратора...')
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Создаем базовые тарифные планы
        if ContractPlan.query.count() == 0:
            print('Создание базовых тарифных планов...')
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
        
        # Создаем базовые страницы контента
        if Content.query.count() == 0:
            print('Создание базовых страниц контента...')
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
            print('Создание базовых FAQ...')
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
        print('База данных успешно инициализирована!')
    except Exception as e:
        print(f'Ошибка при инициализации базы данных: {str(e)}')
        raise 