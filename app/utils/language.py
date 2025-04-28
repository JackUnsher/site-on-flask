from flask import request, session, current_app, redirect, url_for, g
from flask_babel import refresh
from flask_login import current_user


def get_locale():
    """
    Получение текущего языка из сессии или запроса
    """
    # Если в сессии уже есть выбранный язык, используем его
    if 'language' in session:
        return session['language']
    
    # Иначе пытаемся определить язык из заголовков запроса
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


def change_language(lang_code):
    """
    Изменяет язык интерфейса и сохраняет его в сессии
    
    :param lang_code: Код языка (например, 'en', 'ru')
    :return: Редирект на предыдущую страницу
    """
    # Проверяем, поддерживается ли выбранный язык
    supported_languages = current_app.config.get('LANGUAGES', ['ru', 'en'])
    if lang_code not in supported_languages:
        lang_code = 'ru'  # Язык по умолчанию
    
    # Сохраняем выбранный язык в сессии
    session['language'] = lang_code
    g.lang_code = lang_code
    
    # Если пользователь авторизован, сохраняем выбранный язык в его профиле
    if current_user.is_authenticated:
        current_user.language = lang_code
        from app import db
        db.session.commit()
    
    # Получаем URL для редиректа
    next_url = request.referrer or '/'
    
    return redirect(next_url) 