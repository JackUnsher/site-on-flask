from app import db
from datetime import datetime

class SupportChat(db.Model):
    __tablename__ = 'support_chats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=True)
    is_closed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения с использованием back_populates
    user = db.relationship('User', back_populates='support_chats', foreign_keys=[user_id])
    messages = db.relationship('SupportMessage', back_populates='chat', 
                              cascade='all, delete-orphan', order_by='SupportMessage.timestamp')
    
    def __repr__(self):
        return f'<SupportChat {self.id} - User: {self.user_id}>'
    
    @property
    def unread_count(self):
        """Возвращает количество непрочитанных сообщений от пользователя."""
        return SupportMessage.query.filter_by(
            chat_id=self.id,
            is_read=False,
            is_from_user=True
        ).count()
    
    @property
    def last_message(self):
        """Возвращает последнее сообщение в чате."""
        return SupportMessage.query.filter_by(
            chat_id=self.id
        ).order_by(SupportMessage.timestamp.desc()).first()

class SupportMessage(db.Model):
    __tablename__ = 'support_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('support_chats.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_from_user = db.Column(db.Boolean, default=True)  # True если от пользователя, False если от администратора
    is_read = db.Column(db.Boolean, default=False)
    is_system = db.Column(db.Boolean, default=False)  # Системное сообщение (уведомление)
    attachment_path = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения с использованием back_populates
    user = db.relationship('User', back_populates='support_messages', foreign_keys=[user_id])
    chat = db.relationship('SupportChat', back_populates='messages', foreign_keys=[chat_id])
    
    def __repr__(self):
        return f'<SupportMessage {self.id} - Chat: {self.chat_id} - From User: {self.is_from_user}>' 