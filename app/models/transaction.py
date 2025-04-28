from app import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal, earning
    amount_btc = db.Column(db.Float, nullable=False)
    amount_usd = db.Column(db.Float, nullable=True)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='completed')  # pending, completed, failed
    tx_hash = db.Column(db.String(100), nullable=True)  # Хеш транзакции в блокчейне
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения с использованием back_populates
    user = db.relationship('User', back_populates='transactions', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<Transaction {self.id} - {self.type} - {self.amount_btc} BTC>'

class Earning(db.Model):
    __tablename__ = 'earnings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    amount_btc = db.Column(db.Float, nullable=False)
    amount_usd = db.Column(db.Float, nullable=True)
    electricity_fee = db.Column(db.Float, nullable=True)  # Плата за электричество
    date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения с использованием back_populates
    user = db.relationship('User', back_populates='earnings', foreign_keys=[user_id])
    contract = db.relationship('Contract', back_populates='earnings', foreign_keys=[contract_id])
    
    def __repr__(self):
        return f'<Earning {self.id} - {self.amount_btc} BTC>'

class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount_btc = db.Column(db.Float, nullable=False)
    fee_btc = db.Column(db.Float, nullable=True)  # Комиссия за вывод
    final_amount_btc = db.Column(db.Float, nullable=True)  # Итоговая сумма к выплате
    wallet_address = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, success, error, cancelled
    tx_hash = db.Column(db.String(100), nullable=True)  # Хеш транзакции в блокчейне
    notes = db.Column(db.Text, nullable=True)
    processed_at = db.Column(db.DateTime, nullable=True)
    processed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения с использованием back_populates
    user = db.relationship('User', back_populates='withdrawals', foreign_keys=[user_id])
    admin = db.relationship('User', back_populates='processed_withdrawals', foreign_keys=[processed_by_id])
    
    def __repr__(self):
        return f'<Withdrawal {self.id} - {self.amount_btc} BTC - {self.status}>'
    
    def approve(self, admin_id, tx_hash=None):
        """Подтверждает запрос на вывод средств."""
        if self.status == 'pending':
            self.status = 'success'
            self.processed_at = datetime.utcnow()
            self.processed_by_id = admin_id
            self.tx_hash = tx_hash
            return True
        return False
    
    def reject(self, admin_id, reason=None):
        """Отклоняет запрос на вывод средств."""
        if self.status == 'pending':
            self.status = 'cancelled'
            self.processed_at = datetime.utcnow()
            self.processed_by_id = admin_id
            if reason:
                self.notes = reason
            return True
        return False 