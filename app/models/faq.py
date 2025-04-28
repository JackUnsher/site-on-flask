from datetime import datetime
from app import db

class FAQ(db.Model):
    """Модель для часто задаваемых вопросов."""
    __tablename__ = 'faqs'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, question, answer):
        """Инициализация нового FAQ."""
        self.question = question
        self.answer = answer

    def to_dict(self):
        """Преобразование FAQ в словарь."""
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        """Строковое представление FAQ."""
        return f"<FAQ {self.id}: '{self.question[:30]}...'>" 