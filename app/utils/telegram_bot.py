import requests
import logging
from flask import current_app
from functools import wraps

# Настройка логирования
logger = logging.getLogger(__name__)

class TelegramBot:
    """Класс для работы с Telegram API"""
    
    def __init__(self, token=None, admin_chat_id=None):
        """
        Инициализация бота
        :param token: Токен Telegram бота
        :param admin_chat_id: ID чата администратора
        """
        self.token = token
        self.admin_chat_id = admin_chat_id
        self.api_url = f"https://api.telegram.org/bot{token}/" if token else None
    
    def set_token(self, token):
        """Установить токен бота"""
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}/"
    
    def set_admin_chat_id(self, chat_id):
        """Установить ID чата администратора"""
        self.admin_chat_id = chat_id
    
    def send_message(self, chat_id, text, parse_mode="HTML", disable_web_page_preview=True):
        """
        Отправить сообщение
        :param chat_id: ID чата, куда отправить сообщение
        :param text: Текст сообщения
        :param parse_mode: Формат текста (HTML, Markdown)
        :param disable_web_page_preview: Отключить превью ссылок
        :return: Результат запроса
        """
        if not self.token or not self.api_url:
            logger.warning("Telegram bot token not set")
            return False
        
        # Ограничение на длину сообщения в Telegram - 4096 символов
        if len(text) > 4096:
            text = text[:4093] + "..."
        
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        try:
            response = requests.post(f"{self.api_url}sendMessage", data=data)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error sending Telegram message: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exception sending Telegram message: {str(e)}")
            return False
    
    def send_to_admin(self, text, parse_mode="HTML", disable_web_page_preview=True):
        """
        Отправить сообщение администратору
        :param text: Текст сообщения
        :param parse_mode: Формат текста (HTML, Markdown)
        :param disable_web_page_preview: Отключить превью ссылок
        :return: Результат запроса
        """
        if not self.admin_chat_id:
            logger.warning("Admin chat ID not set")
            return False
        
        return self.send_message(
            chat_id=self.admin_chat_id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview
        )

# Создаем глобальный экземпляр бота
telegram_bot = TelegramBot()

def init_telegram_bot(app):
    """
    Инициализация Telegram бота из конфигурации приложения
    :param app: Экземпляр Flask приложения
    """
    bot_token = app.config.get('TELEGRAM_BOT_TOKEN')
    admin_chat_id = app.config.get('TELEGRAM_ADMIN_CHAT_ID')
    
    if bot_token and admin_chat_id:
        telegram_bot.set_token(bot_token)
        telegram_bot.set_admin_chat_id(admin_chat_id)
        logger.info("Telegram bot initialized")
    else:
        logger.warning("Telegram bot not initialized: missing token or admin chat ID")

def send_telegram_notification_to_admin(subject, message, include_url=None):
    """
    Отправляет уведомление администратору через Telegram
    :param subject: Тема уведомления
    :param message: Текст сообщения
    :param include_url: URL для включения в сообщение (опционально)
    """
    text = f"<b>{subject}</b>\n\n{message}"
    
    if include_url:
        text += f"\n\n<a href='{include_url}'>Перейти на сайт</a>"
    
    return telegram_bot.send_to_admin(text)

def send_support_chat_notification(chat_id, username, message_preview, is_new_chat=False):
    """
    Отправляет уведомление администратору о новом сообщении в чате поддержки
    :param chat_id: ID чата поддержки
    :param username: Имя пользователя
    :param message_preview: Предпросмотр сообщения (первые 100 символов)
    :param is_new_chat: Флаг, указывающий что это новый чат
    """
    if is_new_chat:
        subject = "Новый чат поддержки"
        message = f"Пользователь <b>{username}</b> создал новый чат поддержки.\n\nПервое сообщение: \"{message_preview}\""
    else:
        subject = "Новое сообщение в чате поддержки"
        message = f"Пользователь <b>{username}</b> отправил новое сообщение в чат #{chat_id}.\n\nСообщение: \"{message_preview}\""
    
    # Формируем URL для перехода к чату
    include_url = f"/admin/support?chat_id={chat_id}"
    
    return send_telegram_notification_to_admin(subject, message, include_url)

# Декоратор для отправки уведомлений при исключениях
def notify_admin_on_error(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_message = f"Ошибка в функции {f.__name__}: {str(e)}"
            send_telegram_notification_to_admin("Ошибка в приложении", error_message)
            # Пробрасываем исключение дальше
            raise
    return decorated_function 