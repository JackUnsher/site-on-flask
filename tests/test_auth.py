"""
Тесты для модуля аутентификации.
"""
import unittest
from app import create_app, db
from app.models import User, Role
from config import TestConfig

class AuthTestCase(unittest.TestCase):
    """
    Тесты для модуля аутентификации.
    """
    def setUp(self):
        """
        Настройка перед каждым тестом.
        """
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        
        # Создание тестовой роли
        role = Role(name='user', description='Тестовая роль пользователя')
        db.session.add(role)
        db.session.commit()
    
    def tearDown(self):
        """
        Очистка после каждого теста.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_register_and_login(self):
        """
        Тест регистрации и входа пользователя.
        """
        # Регистрация нового пользователя
        response = self.client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'password2': 'password123',
            'first_name': 'Test',
            'last_name': 'User'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Проверка, что пользователь был создан
        user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@example.com')
        
        # Выход пользователя
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Вход пользователя
        response = self.client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123',
            'remember_me': False
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_incorrect_password(self):
        """
        Тест входа с неправильным паролем.
        """
        # Создание пользователя
        user = User(username='testuser', email='test@example.com', password='password123')
        role = Role.query.filter_by(name='user').first()
        user.add_role(role)
        db.session.add(user)
        db.session.commit()
        
        # Попытка входа с неправильным паролем
        response = self.client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'wrongpassword',
            'remember_me': False
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Неверное имя пользователя или пароль', response.data)
    
    def test_role_required(self):
        """
        Тест доступа к защищенным страницам.
        """
        # Создание пользователя
        user = User(username='testuser', email='test@example.com', password='password123')
        role = Role.query.filter_by(name='user').first()
        user.add_role(role)
        db.session.add(user)
        db.session.commit()
        
        # Вход пользователя
        response = self.client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123',
            'remember_me': False
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Доступ к панели управления (требуется авторизация)
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Доступ к админ-панели (требуется роль admin)
        response = self.client.get('/admin', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'У вас нет доступа к этой странице', response.data)


if __name__ == '__main__':
    unittest.main() 