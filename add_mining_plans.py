from flask import Flask
from app import create_app, db
from app.models import ContractPlan
from datetime import datetime

# Создаем контекст приложения
app = create_app()
app.app_context().push()

print("Добавление новых тарифных планов...")

# Создаем базовые тарифные планы, если их еще нет
if ContractPlan.query.filter_by(name='Minimum').first() is None:
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
    print("Планы с такими именами уже существуют")

# Выводим все планы
all_plans = ContractPlan.query.all()
print(f"Всего планов в базе данных: {len(all_plans)}")
for plan in all_plans:
    print(f"- {plan.name}: {plan.hashrate} TH/s, ${plan.price_usd:.2f}, {plan.price_btc:.8f} BTC") 