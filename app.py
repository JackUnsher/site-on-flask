"""
Точка входа для запуска Flask-приложения.
"""
import os
import sys
import logging
from datetime import datetime
from flask import Flask, jsonify

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

logger.info("Запуск минимального Flask-приложения для диагностики")

# Создаем базовое приложение Flask
app = Flask(__name__)

@app.route('/')
def root():
    """Тестовый маршрут для проверки работоспособности приложения."""
    logger.info("Запрос к корневому маршруту")
    return jsonify({
        'status': 'ok',
        'message': 'Минимальное Flask приложение работает!',
        'time': str(datetime.now())
    })

@app.route('/health')
def health_check():
    """Маршрут для проверки состояния приложения и окружения."""
    import platform
    
    # Проверяем наличие и права на директорию данных
    data_dir = '/data'
    data_dir_exists = os.path.exists(data_dir)
    data_dir_writable = os.access(data_dir, os.W_OK) if data_dir_exists else False
    
    # Создадим тестовый файл для проверки возможности записи
    test_write = False
    if data_dir_exists and data_dir_writable:
        try:
            test_file = os.path.join(data_dir, 'test_write.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            test_write = True
            os.remove(test_file)
            logger.info("Тест записи в директорию данных успешен")
        except Exception as e:
            logger.error(f"Ошибка при тестировании записи в директорию данных: {str(e)}")
    
    # Получаем информацию о переменных окружения
    env_vars = {k: v for k, v in os.environ.items() if not k.startswith('_')}
    
    return jsonify({
        'status': 'ok',
        'python_version': sys.version,
        'platform': platform.platform(),
        'environment': os.environ.get('FLASK_ENV', 'production'),
        'data_directory': {
            'path': data_dir,
            'exists': data_dir_exists,
            'writable': data_dir_writable,
            'test_write_success': test_write
        },
        'env_vars': env_vars,
        'app_config': {k: str(v) for k, v in app.config.items() if not k.startswith('_') and k != 'SECRET_KEY'},
        'time': str(datetime.now())
    })

if __name__ == '__main__':
    try:
        # Получаем порт из переменной окружения PORT или используем 5000 по умолчанию
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Запуск приложения на порту {port}")
        
        # В режиме отладки используем встроенный сервер Flask
        if os.environ.get('DEBUG', 'False') == 'True':
            logger.info("Запуск в режиме отладки")
            app.run(debug=True, host='0.0.0.0', port=port)
        else:
            logger.info(f"Запуск производственного сервера на порту {port}")
            app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске приложения: {str(e)}", exc_info=True) 