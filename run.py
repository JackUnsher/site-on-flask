from app import create_app, db
from app.models.user import User

app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Создает контекст оболочки Flask"""
    return {'db': db, 'User': User}


if __name__ == '__main__':
    app.run(debug=True) 