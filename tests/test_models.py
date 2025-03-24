"""
Тесты для моделей данных.
"""
import unittest
from datetime import datetime
from app import create_app, db
from app.models import User, Role, Post, Category
from config import TestConfig

class ModelsTestCase(unittest.TestCase):
    """
    Тесты для моделей данных.
    """
    def setUp(self):
        """
        Настройка перед каждым тестом.
        """
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Создаем тестовые роли
        self.role_user = Role(name='user', description='Обычный пользователь')
        self.role_admin = Role(name='admin', description='Администратор')
        db.session.add_all([self.role_user, self.role_admin])
        db.session.commit()
    
    def tearDown(self):
        """
        Очистка после каждого теста.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_user_model(self):
        """
        Тестирование модели пользователя.
        """
        # Создание пользователя
        user = User(username='testuser', email='test@example.com', 
                    first_name='Test', last_name='User')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Проверка атрибутов
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.full_name, 'Test User')
        self.assertNotEqual(user.password_hash, 'password123')
        
        # Проверка методов
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.check_password('wrongpassword'))
        
        # Проверка отношений с ролями
        user.add_role(self.role_user)
        db.session.commit()
        self.assertEqual(len(user.roles), 1)
        self.assertTrue(user.has_role('user'))
        self.assertFalse(user.has_role('admin'))
        
        # Добавление второй роли
        user.add_role(self.role_admin)
        db.session.commit()
        self.assertEqual(len(user.roles), 2)
        self.assertTrue(user.has_role('admin'))
    
    def test_role_model(self):
        """
        Тестирование модели роли.
        """
        # Проверка существующих ролей
        user_role = Role.query.filter_by(name='user').first()
        admin_role = Role.query.filter_by(name='admin').first()
        
        self.assertEqual(user_role.name, 'user')
        self.assertEqual(user_role.description, 'Обычный пользователь')
        self.assertEqual(admin_role.name, 'admin')
        self.assertEqual(admin_role.description, 'Администратор')
        
        # Создание пользователей с разными ролями
        user1 = User(username='user1', email='user1@example.com')
        user1.add_role(user_role)
        
        user2 = User(username='admin1', email='admin1@example.com')
        user2.add_role(admin_role)
        
        db.session.add_all([user1, user2])
        db.session.commit()
        
        # Проверка отношений
        self.assertEqual(len(user_role.users), 1)
        self.assertEqual(len(admin_role.users), 1)
        self.assertIn(user1, user_role.users)
        self.assertIn(user2, admin_role.users)
    
    def test_post_model(self):
        """
        Тестирование модели поста.
        """
        # Создание пользователя
        user = User(username='blogger', email='blogger@example.com')
        user.add_role(self.role_user)
        db.session.add(user)
        
        # Создание категории
        category = Category(name='Test Category', slug='test-category', 
                           description='Тестовая категория для постов')
        db.session.add(category)
        db.session.commit()
        
        # Создание поста
        post = Post(
            title='Тестовый пост',
            slug='test-post',
            content='Содержание тестового поста',
            summary='Краткое описание',
            published=True,
            user_id=user.id,
            category_id=category.id
        )
        db.session.add(post)
        db.session.commit()
        
        # Проверка атрибутов
        self.assertEqual(post.title, 'Тестовый пост')
        self.assertEqual(post.slug, 'test-post')
        self.assertEqual(post.content, 'Содержание тестового поста')
        self.assertEqual(post.summary, 'Краткое описание')
        self.assertTrue(post.published)
        self.assertIsInstance(post.created_at, datetime)
        self.assertIsInstance(post.updated_at, datetime)
        
        # Проверка отношений
        self.assertEqual(post.author, user)
        self.assertEqual(post.category, category)
        self.assertEqual(len(user.posts), 1)
        self.assertEqual(len(category.posts), 1)
        
        # Проверка на уникальность slug
        duplicate_post = Post(
            title='Другой пост',
            slug='test-post',  # дублирующийся slug
            content='Другое содержание',
            user_id=user.id,
            category_id=category.id
        )
        db.session.add(duplicate_post)
        with self.assertRaises(Exception):
            db.session.commit()
        db.session.rollback()
    
    def test_category_model(self):
        """
        Тестирование модели категории.
        """
        # Создание категории
        category = Category(name='Технологии', slug='tech', 
                            description='Всё о технологиях')
        db.session.add(category)
        db.session.commit()
        
        # Проверка атрибутов
        self.assertEqual(category.name, 'Технологии')
        self.assertEqual(category.slug, 'tech')
        self.assertEqual(category.description, 'Всё о технологиях')
        
        # Создание постов в категории
        user = User(username='tech_blogger', email='tech@example.com')
        db.session.add(user)
        db.session.commit()
        
        for i in range(3):
            post = Post(
                title=f'Пост о технологиях {i+1}',
                slug=f'tech-post-{i+1}',
                content=f'Содержание поста {i+1}',
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(post)
        
        db.session.commit()
        
        # Проверка отношений
        self.assertEqual(len(category.posts), 3)
        self.assertEqual(category.posts[0].title, 'Пост о технологиях 1')
        
        # Проверка на уникальность slug
        duplicate_category = Category(name='Другая категория', slug='tech')
        db.session.add(duplicate_category)
        with self.assertRaises(Exception):
            db.session.commit()


if __name__ == '__main__':
    unittest.main() 