"""
Точка входа для запуска Flask-приложения.
"""
import os
from datetime import datetime
from flask import g
from app import create_app

# Точка входа приложения
app = create_app()

@app.context_processor
def inject_now():
    """
    Добавляет текущий год в контекст шаблонов.
    """
    return {'year': datetime.now().year}

if __name__ == '__main__':
    app.run(debug=os.environ.get('DEBUG', 'False') == 'True', host='0.0.0.0') 