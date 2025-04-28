from app import create_app, db
from app.models.user import User
from app.models.system_setting import SystemSetting
from config import config

def init_db():
    app = create_app(config['development'])
    with app.app_context():
        # Создаем таблицы
        db.create_all()
        
        # Создаем администратора, если его нет
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Создаем базовые настройки системы
        if not SystemSetting.get_by_key('site_name'):
            SystemSetting.set_value('site_name', 'Mining Platform', 'Название сайта')
            SystemSetting.set_value('maintenance_mode', '0', 'Режим обслуживания (1 - включен, 0 - выключен)', True)
            SystemSetting.set_value('registration_enabled', '1', 'Возможность регистрации (1 - включена, 0 - выключена)', True)
        
        db.session.commit()
        print("База данных успешно инициализирована!")

if __name__ == '__main__':
    init_db() 