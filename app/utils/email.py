from flask import current_app, render_template
from flask_mail import Message
from threading import Thread
from app import mail
from datetime import datetime


def send_async_email(app, msg):
    """Отправляет email асинхронно в отдельном потоке"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Error sending email: {str(e)}")


def send_email(subject, sender, recipients, text_body, html_body):
    """Отправляет электронное письмо"""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()


def send_password_reset_email(user):
    """Отправляет электронное письмо для сброса пароля"""
    token = user.get_reset_password_token()
    send_email(
        subject=current_app.config['APP_NAME'] + ' - ' + 'Сброс пароля',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt', user=user, token=token, now=datetime.now()),
        html_body=render_template('email/reset_password.html', user=user, token=token, now=datetime.now())
    )


def send_two_factor_code(user, code):
    """Отправляет код двухфакторной аутентификации"""
    send_email(
        subject=current_app.config['APP_NAME'] + ' - ' + 'Код подтверждения',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=render_template('email/two_factor_code.txt', user=user, code=code, now=datetime.now()),
        html_body=render_template('email/two_factor_code.html', user=user, code=code, now=datetime.now())
    ) 