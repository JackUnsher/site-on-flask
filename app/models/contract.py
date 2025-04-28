from app import db
from datetime import datetime

class ContractPlan(db.Model):
    __tablename__ = 'contract_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # standard, premium, lifetime
    hashrate = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=True)  # в днях, NULL для бессрочных
    price_usd = db.Column(db.Float, nullable=False)
    price_btc = db.Column(db.Float, nullable=False)
    maintenance_fee = db.Column(db.Float, nullable=False)  # в процентах
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    contracts = db.relationship('Contract', back_populates='plan')
    
    def __repr__(self):
        return f'<ContractPlan {self.name} - {self.hashrate} TH/s>'

class Contract(db.Model):
    __tablename__ = 'contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('contract_plans.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # standard, premium, lifetime
    hashrate = db.Column(db.Float, nullable=False)
    price_usd = db.Column(db.Float, nullable=False)
    price_btc = db.Column(db.Float, nullable=False)
    maintenance_fee = db.Column(db.Float, nullable=False)  # в процентах
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)  # NULL для бессрочных
    status = db.Column(db.String(20), nullable=False, default='active')  # active, expired, terminated
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения с использованием back_populates
    user = db.relationship('User', back_populates='contracts', foreign_keys=[user_id])
    plan = db.relationship('ContractPlan', back_populates='contracts')
    earnings = db.relationship('Earning', back_populates='contract', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Contract {self.name} - {self.hashrate} TH/s - {self.status}>'
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def is_expired(self):
        return self.status == 'expired'
    
    @property
    def is_terminated(self):
        return self.status == 'terminated'
    
    @property
    def days_remaining(self):
        if not self.end_date:
            return float('inf')  # бессрочный контракт
        
        now = datetime.utcnow()
        if now > self.end_date:
            return 0
        
        delta = self.end_date - now
        return delta.days
    
    @property
    def total_earnings(self):
        return sum(earning.amount_btc for earning in self.earnings)
    
    @property
    def daily_earning_estimate(self):
        """
        Примерная оценка дневного заработка на основе текущего хешрейта
        и сложности сети (упрощенная формула).
        """
        # Примерная формула для расчета дневного заработка
        btc_per_th_per_day = 0.00001  # Условное значение BTC за 1 TH/s в день
        
        # Учитываем плату за обслуживание
        maintenance_fee_multiplier = 1 - (self.maintenance_fee / 100)
        
        # Итоговый расчет с учетом хешрейта и комиссии
        return self.hashrate * btc_per_th_per_day * maintenance_fee_multiplier
    
    def check_expiration(self):
        """
        Проверяет, истек ли контракт, и при необходимости обновляет его статус.
        Возвращает True, если статус был изменен.
        """
        if self.end_date and datetime.utcnow() > self.end_date and self.status != 'expired':
            self.status = 'expired'
            return True
        return False
    
    def terminate(self):
        """
        Прекращает действие контракта.
        """
        if self.status == 'active':
            self.status = 'terminated'
            return True
        return False
    
    def renew(self, days=None):
        """
        Продлевает контракт на указанное количество дней или на стандартный период,
        если количество дней не указано.
        """
        if self.status != 'active':
            self.status = 'active'
            
            if days is None and self.plan and self.plan.duration:
                days = self.plan.duration
            
            if days:
                if not self.end_date or self.end_date < datetime.utcnow():
                    # Если контракт уже истек или бессрочный, начинаем отсчет от текущей даты
                    self.end_date = datetime.utcnow()
                
                # Добавляем указанное количество дней
                delta = datetime.utcnow() + datetime.timedelta(days=days)
                self.end_date = delta
            else:
                # Если дни не указаны и у плана нет продолжительности, делаем контракт бессрочным
                self.end_date = None
            
            return True
        return False 