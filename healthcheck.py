"""
Модуль для проверки работоспособности приложения на Amvera.
"""
import os
import sys
import sqlite3
import requests
from datetime import datetime

def check_database():
    """Проверка доступности и состояния базы данных."""
    db_path = os.path.join('instance', 'app.db')
    try:
        if not os.path.exists('instance'):
            print(f"ERROR: Директория 'instance' не существует")
            return False
            
        if not os.path.exists(db_path):
            print(f"ERROR: База данных {db_path} не существует")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Проверяем, есть ли таблицы в базе данных
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Таблицы в базе данных: {tables}")
        conn.close()
        return True
    except Exception as e:
        print(f"ERROR при проверке базы данных: {e}")
        return False

def check_flask_app(base_url="http://localhost:5000"):
    """Проверка доступности Flask приложения."""
    try:
        response = requests.get(f"{base_url}/")
        print(f"Статус код: {response.status_code}")
        print(f"Заголовки ответа: {response.headers}")
        if response.status_code == 200:
            return True
        else:
            print(f"ERROR: Код ответа {response.status_code} от {base_url}/")
            return False
    except Exception as e:
        print(f"ERROR при проверке Flask приложения: {e}")
        return False

def check_environment():
    """Проверка переменных окружения."""
    required_vars = ['FLASK_APP', 'FLASK_CONFIG', 'SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"WARNING: Отсутствуют переменные окружения: {', '.join(missing_vars)}")
    
    print("Переменные окружения:")
    for var in os.environ:
        if var in ['FLASK_APP', 'FLASK_CONFIG', 'SECRET_KEY', 'DATABASE_URL']:
            # Не показываем значение SECRET_KEY
            if var == 'SECRET_KEY':
                print(f"  {var}: ***скрыто***")
            else:
                print(f"  {var}: {os.environ[var]}")
    
    # Проверяем путь к Python и версию
    print(f"Путь к Python: {sys.executable}")
    print(f"Версия Python: {sys.version}")
    
    # Проверяем директорию приложения
    print(f"Текущая директория: {os.getcwd()}")
    print(f"Содержимое текущей директории: {os.listdir('.')}")
    
    return True

def main():
    """Основная функция проверки работоспособности."""
    print(f"--- Проверка работоспособности начата {datetime.now()} ---")
    
    check_environment()
    db_status = check_database()
    
    if len(sys.argv) > 1:
        # Если передан URL для проверки
        app_status = check_flask_app(sys.argv[1])
    else:
        app_status = "Skipped"
        print("Проверка приложения пропущена (не указан URL)")
    
    print(f"--- Результаты проверки ---")
    print(f"Переменные окружения: OK")
    print(f"База данных: {'OK' if db_status else 'FAIL'}")
    print(f"Flask приложение: {app_status}")
    print(f"--- Проверка работоспособности завершена {datetime.now()} ---")
    
    return 0 if db_status and (app_status is True or app_status == "Skipped") else 1

if __name__ == "__main__":
    sys.exit(main()) 