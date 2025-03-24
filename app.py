"""
Точка входа для запуска Flask-приложения.
"""
import os
from datetime import datetime
from flask import g, Flask, jsonify
from dotenv import load_dotenv
from app import create_app
import waitress

# Загрузка переменных окружения из .env файла
load_dotenv()

# Точка входа приложения
app = create_app()

@app.route('/')
def root():
    """Тестовый маршрут для проверки работоспособности приложения."""
    return jsonify({
        'status': 'ok',
        'message': 'Flask приложение работает!',
        'time': str(datetime.now())
    })

@app.route('/health')
def health_check():
    """Маршрут для проверки состояния приложения и окружения."""
    import sys
    import platform
    
    # Проверяем наличие и права на директорию данных
    data_dir = '/data'
    data_dir_exists = os.path.exists(data_dir)
    data_dir_writable = os.access(data_dir, os.W_OK) if data_dir_exists else False
    
    # Получаем информацию о переменных окружения
    env_vars = {
        'DATABASE_URL': os.environ.get('DATABASE_URL', 'не установлено'),
        'FLASK_APP': os.environ.get('FLASK_APP', 'не установлено'),
        'PORT': os.environ.get('PORT', 'не установлено')
    }
    
    return jsonify({
        'status': 'ok',
        'python_version': sys.version,
        'platform': platform.platform(),
        'environment': os.environ.get('FLASK_ENV', 'production'),
        'data_directory': {
            'path': data_dir,
            'exists': data_dir_exists,
            'writable': data_dir_writable,
        },
        'env_vars': env_vars,
        'time': str(datetime.now())
    })

@app.context_processor
def inject_now():
    """
    Добавляет текущий год в контекст шаблонов.
    """
    return {'year': datetime.now().year}

if __name__ == '__main__':
    # Получаем порт из переменной окружения PORT или используем 5000 по умолчанию
    port = int(os.environ.get('PORT', 5000))
    
    # В режиме отладки используем встроенный сервер Flask
    if os.environ.get('DEBUG', 'False') == 'True':
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        # В производственном режиме используем Waitress
        print(f"Запуск производственного сервера Waitress на порту {port}")
        # Устанавливаем таймаут побольше
        waitress.serve(app, host='0.0.0.0', port=port, threads=4, clear_untrusted_proxy_headers=True) 