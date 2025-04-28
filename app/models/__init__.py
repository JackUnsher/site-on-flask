from app.models.user import User, Setting, Wallet
from app.models.contract import Contract, ContractPlan
from app.models.transaction import Transaction, Earning, Withdrawal
from app.models.support import SupportChat, SupportMessage
from app.models.content import Content, FaqItem
from app.models.notification import Notification, NotificationTemplate
from app.models.system_setting import SystemSetting
from app.models.faq import FAQ

__all__ = [
    'User', 'Setting', 'Wallet',
    'Contract', 'ContractPlan',
    'Transaction', 'Earning', 'Withdrawal',
    'SupportChat', 'SupportMessage',
    'Content', 'FaqItem',
    'Notification', 'NotificationTemplate',
    'SystemSetting',
    'FAQ'
]

# Добавляйте здесь импорты других моделей по мере их создания 