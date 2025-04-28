from app import create_app, db
from app.models.user import User
from config import config

app = create_app(config['development'])

with app.app_context():
    # Проверяем, существует ли уже администратор
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print('Администратор уже существует')
    else:
        # Создаем нового администратора
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('Admin123!')
        db.session.add(admin)
        db.session.commit()
        print('Администратор успешно создан')

print('Логин: admin')
print('Пароль: Admin123!') 