from flask import Blueprint, request, redirect, session, url_for, g

lang_bp = Blueprint('lang', __name__)

@lang_bp.route('/set_language')
def set_language():
    """Устанавливает язык интерфейса"""
    lang = request.args.get('lang', 'en')
    next_url = request.args.get('next', '/')
    
    # Проверяем, является ли язык поддерживаемым
    if lang in ['en', 'ru']:
        session['lang'] = lang
        g.lang_code = lang
    
    return redirect(next_url) 