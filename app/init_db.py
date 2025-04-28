from flask import Flask
from app import create_app, db
from app.models import User, Content, SystemSetting, ContractPlan, FAQ
from datetime import datetime

# Создаем контекст приложения
app = create_app()
app.app_context().push()

print("Инициализация базы данных...")

# Создаем админа, если его еще нет
admin_username = 'admin'
admin_email = 'admin@example.com'
admin_password = 'adminpassword'

if User.query.filter_by(username=admin_username).first() is None:
    admin = User(
        username=admin_username,
        email=admin_email,
        is_admin=True,
        created_at=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )
    admin.set_password(admin_password)
    
    db.session.add(admin)
    db.session.commit()
    print(f"Создан администратор: {admin_username}")

# Создаем базовые тарифные планы, если их еще нет
if ContractPlan.query.count() == 0:
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
    print("Тарифные планы успешно созданы")

# Создаем основные страницы контента, если их нет
if Content.query.count() == 0:
    content_items = [
        {
            'slug': 'about',
            'title': 'About Us',
            'content': 'This is the about page content.',
            'is_published': True
        },
        {
            'slug': 'terms',
            'title': 'Terms of Use',
            'content': 'These are the terms of use for our platform.',
            'is_published': True
        },
        {
            'slug': 'privacy',
            'title': 'Privacy Policy',
            'content': 'This is our privacy policy.',
            'is_published': True
        },
        {
            'slug': 'contact',
            'title': 'Contact Information',
            'content': 'Our contact information.',
            'is_published': True
        }
    ]
    
    for item_data in content_items:
        content_item = Content(**item_data)
        db.session.add(content_item)
    
    db.session.commit()
    print("Созданы базовые страницы контента")

# Создаем FAQ, если их нет
if FAQ.query.count() == 0:
    faq_items = [
        {
            'question': 'How does Bitcoin mining work?',
            'answer': 'Bitcoin mining involves solving complex mathematical problems to verify transactions and add them to the blockchain.',
            'category': 'general',
            'is_published': True
        },
        {
            'question': 'What are mining contracts?',
            'answer': 'Mining contracts allow you to purchase mining power without owning physical hardware.',
            'category': 'contracts',
            'is_published': True
        },
        {
            'question': 'How do I withdraw my earnings?',
            'answer': 'You can withdraw your earnings to your Bitcoin wallet once you reach the minimum withdrawal amount.',
            'category': 'payments',
            'is_published': True
        }
    ]
    
    for faq_data in faq_items:
        faq = FAQ(**faq_data)
        db.session.add(faq)
    
    db.session.commit()
    print("Созданы базовые FAQ")

print("База данных успешно инициализирована!") 