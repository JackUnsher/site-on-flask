"""
Тесты для маршрутов приложения.
"""
import unittest
from app import create_app, db
from app.models import User, Role, Post, Category
from config import TestConfig

class RoutesTestCase(unittest.TestCase):
    """
    Тесты для маршрутов приложения.
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
        
        # Создание ролей
        self.role_user = Role(name='user', description='Обычный пользователь')
        self.role_admin = Role(name='admin', description='Администратор')
        db.session.add_all([self.role_user, self.role_admin])
        
        # Создание тестового пользователя
        self.user = User(username='testuser', email='test@example.com', 
                         first_name='Test', last_name='User')
        self.user.set_password('password123')
        self.user.add_role(self.role_user)
        
        # Создание администратора
        self.admin = User(username='admin', email='admin@example.com', 
                          first_name='Admin', last_name='User')
        self.admin.set_password('adminpass')
        self.admin.add_role(self.role_admin)
        
        # Создание категории
        self.category = Category(name='Тест', slug='test', 
                                 description='Тестовая категория')
        
        db.session.add_all([self.user, self.admin, self.category])
        db.session.commit()
        
        # Создание тестовых постов
        self.post1 = Post(
            title='Первый пост',
            slug='first-post',
            content='Содержание первого поста',
            summary='Краткое описание',
            published=True,
            user_id=self.user.id,
            category_id=self.category.id
        )
        
        self.post2 = Post(
            title='Второй пост',
            slug='second-post',
            content='Содержание второго поста',
            summary='Краткое описание второго',
            published=True,
            user_id=self.admin.id,
            category_id=self.category.id
        )
        
        self.draft = Post(
            title='Черновик',
            slug='draft-post',
            content='Содержание черновика',
            published=False,
            user_id=self.user.id,
            category_id=self.category.id
        )
        
        db.session.add_all([self.post1, self.post2, self.draft])
        db.session.commit()
    
    def tearDown(self):
        """
        Очистка после каждого теста.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self, username, password):
        """
        Вспомогательный метод для авторизации пользователя.
        """
        return self.client.post('/auth/login', data={
            'username': username,
            'password': password,
            'remember_me': False
        }, follow_redirects=True)
    
    def test_home_page(self):
        """
        Тест домашней страницы.
        """
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Первый пост', response.data)
        self.assertIn(b'Второй пост', response.data)
        self.assertNotIn(b'Черновик', response.data)  # Черновики не отображаются
    
    def test_post_detail(self):
        """
        Тест страницы деталей поста.
        """
        # Проверка опубликованного поста
        response = self.client.get('/posts/first-post', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Первый пост', response.data)
        self.assertIn(b'Содержание первого поста', response.data)
        
        # Проверка черновика (должен вернуть 404, если пользователь не автор)
        response = self.client.get('/posts/draft-post', follow_redirects=True)
        self.assertEqual(response.status_code, 404)
        
        # Авторизация автора
        self.login('testuser', 'password123')
        
        # Теперь автор должен видеть свой черновик
        response = self.client.get('/posts/draft-post', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Черновик', response.data)
    
    def test_category_page(self):
        """
        Тест страницы категории.
        """
        response = self.client.get('/category/test', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Тест', response.data)  # Название категории
        self.assertIn(b'Первый пост', response.data)
        self.assertIn(b'Второй пост', response.data)
        self.assertNotIn(b'Черновик', response.data)  # Черновики не отображаются
    
    def test_user_profile(self):
        """
        Тест просмотра профиля пользователя.
        """
        response = self.client.get('/users/testuser', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test User', response.data)
        self.assertIn(b'Первый пост', response.data)
        self.assertNotIn(b'Черновик', response.data)  # Черновики не отображаются публично
    
    def test_dashboard_access(self):
        """
        Тест доступа к панели управления.
        """
        # Без авторизации - редирект на логин
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Пожалуйста, войдите, чтобы получить доступ', response.data)
        
        # После авторизации - доступ разрешен
        self.login('testuser', 'password123')
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Панель управления', response.data)
        self.assertIn(b'Первый пост', response.data)
        self.assertIn(b'Черновик', response.data)  # Пользователь видит свои черновики
    
    def test_admin_access(self):
        """
        Тест доступа к административной панели.
        """
        # Авторизация обычного пользователя
        self.login('testuser', 'password123')
        
        # Попытка доступа к админ-панели
        response = self.client.get('/admin', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'У вас нет доступа к этой странице', response.data)
        
        # Выход пользователя
        self.client.get('/auth/logout', follow_redirects=True)
        
        # Авторизация администратора
        self.login('admin', 'adminpass')
        
        # Теперь доступ к админ-панели должен быть разрешен
        response = self.client.get('/admin', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Административная панель', response.data)
    
    def test_create_post(self):
        """
        Тест создания поста.
        """
        # Авторизация пользователя
        self.login('testuser', 'password123')
        
        # Отправка формы создания поста
        response = self.client.post('/dashboard/posts/create', data={
            'title': 'Новый пост',
            'slug': 'new-post',
            'content': 'Содержание нового поста',
            'summary': 'Краткое описание',
            'category_id': self.category.id,
            'published': True
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Пост успешно создан', response.data)
        
        # Проверка, что пост появился в БД
        post = Post.query.filter_by(slug='new-post').first()
        self.assertIsNotNone(post)
        self.assertEqual(post.title, 'Новый пост')
        self.assertEqual(post.author.username, 'testuser')
    
    def test_edit_post(self):
        """
        Тест редактирования поста.
        """
        # Авторизация пользователя
        self.login('testuser', 'password123')
        
        # Отправка формы редактирования поста
        response = self.client.post(f'/dashboard/posts/edit/{self.post1.id}', data={
            'title': 'Обновленный пост',
            'slug': 'first-post',  # slug остается прежним
            'content': 'Обновленное содержание',
            'summary': 'Новое краткое описание',
            'category_id': self.category.id,
            'published': True
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Пост успешно обновлен', response.data)
        
        # Проверка, что данные обновились в БД
        post = Post.query.get(self.post1.id)
        self.assertEqual(post.title, 'Обновленный пост')
        self.assertEqual(post.content, 'Обновленное содержание')
    
    def test_delete_post(self):
        """
        Тест удаления поста.
        """
        # Авторизация пользователя
        self.login('testuser', 'password123')
        
        # Отправка запроса на удаление поста
        response = self.client.post(f'/dashboard/posts/delete/{self.post1.id}', 
                                  follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Пост успешно удален', response.data)
        
        # Проверка, что пост удален из БД
        post = Post.query.get(self.post1.id)
        self.assertIsNone(post)
        
        # Попытка удалить чужой пост (должно быть запрещено)
        response = self.client.post(f'/dashboard/posts/delete/{self.post2.id}', 
                                  follow_redirects=True)
        
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Проверка, что чужой пост не был удален
        post = Post.query.get(self.post2.id)
        self.assertIsNotNone(post)


if __name__ == '__main__':
    unittest.main() 