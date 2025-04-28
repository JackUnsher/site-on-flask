from app import create_app, db
from app.models.notification import NotificationTemplate
from app.models import SystemSetting
import os
import datetime

app = create_app()

with app.app_context():
    try:
        # Проверяем существование таблицы
        db.session.execute("SELECT 1 FROM notification_templates LIMIT 1")
        print("Таблица notification_templates уже существует")
    except Exception as e:
        print(f"Таблица notification_templates не найдена: {str(e)}")
        print("Создаю таблицу notification_templates...")
        
        # Создаем таблицу
        db.create_all()
        
        # Добавляем несколько примеров шаблонов уведомлений
        templates = [
            NotificationTemplate(
                key="welcome",
                content="Добро пожаловать на нашу платформу, {username}! Мы рады приветствовать вас."
            ),
            NotificationTemplate(
                key="withdrawal_approved",
                content="Ваша заявка на вывод средств #{id} успешно обработана. Сумма {amount} BTC отправлена на ваш кошелек {wallet}."
            ),
            NotificationTemplate(
                key="withdrawal_rejected",
                content="Ваша заявка на вывод средств #{id} была отклонена. Причина: {reason}. Пожалуйста, свяжитесь с поддержкой для получения дополнительной информации."
            ),
            NotificationTemplate(
                key="earnings",
                content="Поздравляем! Вы получили {amount} BTC от вашего контракта #{contract_id}."
            )
        ]
        
        # Добавляем шаблоны в базу данных
        for template in templates:
            template.created_at = datetime.datetime.utcnow()
            template.updated_at = datetime.datetime.utcnow()
            db.session.add(template)
        
        # Создаем директорию для загрузок, если она отсутствует
        uploads_dir = os.path.join(app.root_path, 'static/uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            print(f"Создана директория для загрузок: {uploads_dir}")
        
        # Сохраняем изменения
        db.session.commit()
        print("Таблица notification_templates успешно создана и заполнена!")
        
        # Проверяем, что всё создалось правильно
        count = db.session.query(NotificationTemplate).count()
        print(f"Создано {count} шаблонов уведомлений")
        
        print("Инициализация завершена успешно!")
    except Exception as e:
        print(f"Ошибка при создании таблицы: {str(e)}")
        db.session.rollback() 