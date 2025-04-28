import sqlite3
import os
import datetime

# Путь к базе данных
DB_PATH = 'instance/app.db'

def create_notification_templates_table():
    """Создает таблицу notification_templates напрямую через SQLite"""
    # Проверяем существование базы данных
    if not os.path.exists(DB_PATH):
        print(f"Файл базы данных не найден: {DB_PATH}")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем, существует ли таблица
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notification_templates'")
        if cursor.fetchone():
            print("Таблица notification_templates уже существует")
            conn.close()
            return True
        
        # Создаем таблицу notification_templates
        print("Создаю таблицу notification_templates...")
        cursor.execute('''
        CREATE TABLE notification_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key VARCHAR(100) NOT NULL UNIQUE,
            content TEXT NOT NULL,
            created_at DATETIME,
            updated_at DATETIME
        )
        ''')
        
        # Добавляем примеры шаблонов
        now = datetime.datetime.utcnow().isoformat()
        templates = [
            ("welcome", "Добро пожаловать на нашу платформу, {username}! Мы рады приветствовать вас.", now, now),
            ("withdrawal_approved", "Ваша заявка на вывод средств #{id} успешно обработана. Сумма {amount} BTC отправлена на ваш кошелек {wallet}.", now, now),
            ("withdrawal_rejected", "Ваша заявка на вывод средств #{id} была отклонена. Причина: {reason}. Пожалуйста, свяжитесь с поддержкой для получения дополнительной информации.", now, now),
            ("earnings", "Поздравляем! Вы получили {amount} BTC от вашего контракта #{contract_id}.", now, now)
        ]
        
        cursor.executemany(
            "INSERT INTO notification_templates (key, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
            templates
        )
        
        # Фиксируем изменения
        conn.commit()
        print(f"Таблица notification_templates создана и заполнена {len(templates)} шаблонами")
        
        # Закрываем соединение
        conn.close()
        return True
    
    except Exception as e:
        print(f"Ошибка при создании таблицы notification_templates: {str(e)}")
        return False

if __name__ == "__main__":
    if create_notification_templates_table():
        print("Инициализация завершена успешно!")
    else:
        print("Не удалось инициализировать таблицу notification_templates") 