"""
Фикстуры для тестирования с использованием pytest.
"""
import pytest
from app import create_app, db
from app.models import User, Role, Post, Category
from config import TestConfig

@pytest.fixture
def app():
    """
    Фикстура, создающая экземпляр приложения для тестирования.
    """
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        
        # Создание тестовых ролей
        role_user = Role(name='user', description='Обычный пользователь')
        role_admin = Role(name='admin', description='Администратор')
        db.session.add_all([role_user, role_admin])
        
        # Создание тестовых пользователей
        user = User(username='testuser', email='test@example.com', 
                    first_name='Test', last_name='User')
        user.set_password('password123')
        user.add_role(role_user)
        
        admin = User(username='admin', email='admin@example.com', 
                     first_name='Admin', last_name='User')
        admin.set_password('adminpass')
        admin.add_role(role_admin)
        
        db.session.add_all([user, admin])
        
        # Создание тестовой категории
        category = Category(name='Тестовая категория', 
                           slug='test-category', 
                           description='Описание тестовой категории')
        db.session.add(category)
        
        # Создание тестовых постов
        post1 = Post(
            title='Тестовый пост 1',
            slug='test-post-1',
            content='Содержание тестового поста 1',
            summary='Краткое описание',
            published=True,
            user_id=user.id,
            category_id=category.id
        )
        
        post2 = Post(
            title='Тестовый пост 2',
            slug='test-post-2',
            content='Содержание тестового поста 2',
            summary='Краткое описание второго поста',
            published=True,
            user_id=admin.id,
            category_id=category.id
        )
        
        db.session.add_all([post1, post2])
        db.session.commit()
        
        yield app
        
        # Очистка после тестов
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """
    Фикстура, создающая тестовый клиент.
    """
    return app.test_client()

@pytest.fixture
def runner(app):
    """
    Фикстура, создающая тестовый CLI runner.
    """
    return app.test_cli_runner()

@pytest.fixture
def user_data():
    """
    Фикстура с тестовыми данными пользователя.
    """
    return {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'newpass123',
        'password2': 'newpass123',
        'first_name': 'New',
        'last_name': 'User'
    }

@pytest.fixture
def post_data():
    """
    Фикстура с тестовыми данными для поста.
    """
    return {
        'title': 'Новый тестовый пост',
        'slug': 'new-test-post',
        'content': 'Содержание нового тестового поста',
        'summary': 'Краткое описание нового поста',
        'published': True
    }

class AuthActions:
    """
    Вспомогательный класс для тестирования аутентификации.
    """
    def __init__(self, client):
        self._client = client
    
    def login(self, username='testuser', password='password123'):
        """
        Вход пользователя.
        """
        return self._client.post('/auth/login', data={
            'username': username,
            'password': password,
            'remember_me': False
        }, follow_redirects=True)
    
    def logout(self):
        """
        Выход пользователя.
        """
        return self._client.get('/auth/logout', follow_redirects=True)

@pytest.fixture
def auth(client):
    """
    Фикстура для действий аутентификации.
    """
    return AuthActions(client) 