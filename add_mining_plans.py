from app import create_app, db
from app.models.contract import ContractPlan
from config import config

def add_mining_plans():
    app = create_app(config['development'])
    with app.app_context():
        # Проверяем, есть ли уже планы
        if ContractPlan.query.first() is None:
            plans = [
                {
                    'name': 'Minimum',
                    'type': 'standard',
                    'hashrate': 5,
                    'duration': 365,
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
                    'duration': 365,
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
                    'duration': 365,
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
                    'duration': 365,
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
            print("Планы майнинга успешно добавлены!")
        else:
            print("Планы майнинга уже существуют")

if __name__ == '__main__':
    add_mining_plans() 