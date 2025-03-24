"""
Точка входа для запуска Flask-приложения.
"""
import os
from datetime import datetime
from flask import g
from dotenv import load_dotenv
from app import create_app

# Загрузка переменных окружения из .env файла
load_dotenv()

# Точка входа приложения
app = create_app()

@app.context_processor
def inject_now():
    """
    Добавляет текущий год в контекст шаблонов.
    """
    return {'year': datetime.now().year}

if __name__ == '__main__':
    # Получаем порт из переменной окружения PORT или используем 5000 по умолчанию
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=os.environ.get('DEBUG', 'False') == 'True', host='0.0.0.0', port=port) 