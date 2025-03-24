.PHONY: test coverage clean

# Запуск всех тестов
test:
	pytest

# Запуск тестов с отчётом о покрытии
coverage:
	pytest --cov=app --cov-report=html tests/

# Запуск конкретного теста
test-file:
	pytest $(file)

# Очистка кэшированных файлов
clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete

# Установка зависимостей
install:
	pip install -r requirements.txt

# Создание файла requirements.txt
requirements:
	pip freeze > requirements.txt

# Запуск приложения в режиме разработки
run:
	export FLASK_APP=app.py
	export FLASK_ENV=development
	flask run

# Запуск миграций
migrate:
	flask db migrate -m "$(message)"

# Применение миграций
upgrade:
	flask db upgrade

# Откат миграций
downgrade:
	flask db downgrade 