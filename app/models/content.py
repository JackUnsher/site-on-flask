from app import db
from datetime import datetime
import json

class Content(db.Model):
    """Модель для хранения содержимого страниц сайта"""
    __tablename__ = 'contents'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False, unique=True)  # terms, privacy, homepage
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_html = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Content {self.type}>'
    
    @property
    def content_json(self):
        """Возвращает содержимое как JSON-объект, если содержимое хранится в формате JSON"""
        if not self.is_html:
            try:
                return json.loads(self.content)
            except:
                return {}
        return None
    
    @classmethod
    def get_by_type(cls, type):
        """Получает контент по типу"""
        return cls.query.filter_by(type=type).first()
    
    @classmethod
    def update_or_create(cls, type, title, content, is_html=False):
        """Обновляет существующий контент или создает новый"""
        item = cls.query.filter_by(type=type).first()
        
        if item:
            item.title = title
            item.content = content
            item.is_html = is_html
        else:
            item = cls(
                type=type,
                title=title,
                content=content,
                is_html=is_html
            )
            db.session.add(item)
        
        return item

class FaqItem(db.Model):
    """Модель для хранения вопросов и ответов FAQ"""
    __tablename__ = 'faq_items'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False, default='general')
    order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FaqItem {self.question[:30]}>'
    
    @classmethod
    def get_published(cls):
        """Возвращает все опубликованные элементы FAQ, отсортированные по категории и порядку"""
        return cls.query.filter_by(is_published=True).order_by(cls.category, cls.order).all()
    
    @classmethod
    def get_by_category(cls, category):
        """Возвращает все опубликованные элементы FAQ для указанной категории"""
        return cls.query.filter_by(
            category=category, 
            is_published=True
        ).order_by(cls.order).all()
    
    @classmethod
    def get_categories(cls):
        """Возвращает список уникальных категорий FAQ"""
        categories = db.session.query(cls.category).distinct().all()
        return [c[0] for c in categories] 