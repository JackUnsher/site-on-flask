from flask import current_app, url_for, redirect, session, request
from authlib.integrations.flask_client import OAuth
from authlib.integrations.requests_client import OAuth2Session
import requests
import json
from urllib.parse import urlencode
import secrets

oauth = OAuth()


def get_google_provider_cfg():
    """Получает конфигурацию провайдера Google OAuth"""
    try:
        return requests.get(current_app.config['GOOGLE_DISCOVERY_URL']).json()
    except Exception as e:
        current_app.logger.error(f"Error fetching Google OAuth provider config: {str(e)}")
        return None


def get_google_client():
    """Инициализирует и возвращает клиент Google OAuth"""
    # Проверяем наличие всех необходимых конфигурационных параметров
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        current_app.logger.error("Missing Google OAuth client ID or secret")
        return None
    
    # Получаем конфигурацию провайдера
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        return None
    
    # Создаем OAuth сессию
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    return OAuth2Session(
        client_id,
        client_secret,
        scope="openid email profile"
    )


def get_google_auth_url():
    """Создает и возвращает URL для аутентификации через Google"""
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    if not client_id:
        return None
    
    # Получаем конфигурацию провайдера
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        return None
    
    # Создаем URL для Google логина
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    # Определяем URL для редиректа
    redirect_uri = url_for('auth.google_callback', _external=True)
    
    # Генерируем state для защиты от CSRF
    state = generate_state()
    session['google_oauth_state'] = state
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'openid email profile',
        'response_type': 'code',
        'access_type': 'offline',
        'state': state
    }
    
    return f"{authorization_endpoint}?{urlencode(params)}"


def generate_state():
    """Генерирует случайную строку для защиты от CSRF"""
    return secrets.token_urlsafe(32)


def get_google_user_info(code, is_register=False):
    """Получает информацию о пользователе из Google после авторизации"""
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        current_app.logger.error("Missing Google OAuth client ID or secret")
        return None
    
    # Получаем конфигурацию провайдера
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        current_app.logger.error("Could not get Google provider config")
        return None
    
    # Определяем URL для редиректа
    redirect_uri = url_for('auth.google_callback', _external=True)
    
    # Обмениваем код на токен
    token_endpoint = google_provider_cfg["token_endpoint"]
    token_data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        token_response = requests.post(
            token_endpoint,
            data=token_data,
            headers={'Accept': 'application/json'}
        )
        token_response.raise_for_status()
        tokens = token_response.json()
    except Exception as e:
        current_app.logger.error(f"Error exchanging Google auth code for token: {str(e)}")
        return None
    
    # Получаем информацию о пользователе
    try:
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        user_response = requests.get(
            userinfo_endpoint,
            headers={'Authorization': f'Bearer {tokens["access_token"]}'}
        )
        user_response.raise_for_status()
        user_info = user_response.json()
        return user_info
    except Exception as e:
        current_app.logger.error(f"Error fetching Google user info: {str(e)}")
        return None 