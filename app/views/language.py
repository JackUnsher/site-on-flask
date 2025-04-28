from flask import Blueprint
from app.utils.language import change_language

lang_bp = Blueprint('lang', __name__)

@lang_bp.route('/set/<lang_code>')
def set_language(lang_code):
    """
    Маршрут для установки языка
    
    :param lang_code: Код языка (например, 'en', 'ru')
    :return: Редирект на предыдущую страницу
    """
    return change_language(lang_code) 