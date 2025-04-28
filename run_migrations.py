from app import create_app, db
from flask_migrate import upgrade
from config import config

app = create_app(config['production'])
with app.app_context():
    print("Applying database migrations...")
    try:
        upgrade()
        print("Migrations applied successfully!")
    except Exception as e:
        print(f"Error applying migrations: {str(e)}")
        raise 