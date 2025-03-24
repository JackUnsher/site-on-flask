"""
Формы для аутентификации
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

from app.models import User

class LoginForm(FlaskForm):
    """
    Форма входа в систему
    """
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Это поле обязательно'),
        Length(min=3, max=64, message='Имя пользователя должно быть от 3 до 64 символов')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Это поле обязательно')
    ])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    """
    Форма регистрации нового пользователя
    """
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Это поле обязательно'),
        Length(min=3, max=64, message='Имя пользователя должно быть от 3 до 64 символов')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Это поле обязательно'),
        Email(message='Введите корректный email адрес'),
        Length(max=120, message='Email не должен превышать 120 символов')
    ])
    first_name = StringField('Имя', validators=[
        Length(max=64, message='Имя не должно превышать 64 символа')
    ])
    last_name = StringField('Фамилия', validators=[
        Length(max=64, message='Фамилия не должна превышать 64 символа')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Это поле обязательно'),
        Length(min=8, message='Пароль должен содержать не менее 8 символов')
    ])
    password2 = PasswordField('Повторите пароль', validators=[
        DataRequired(message='Это поле обязательно'),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    submit = SubmitField('Зарегистрироваться')
    
    def validate_username(self, username):
        """
        Проверка уникальности имени пользователя
        """
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Это имя пользователя уже занято. Пожалуйста, выберите другое.')
    
    def validate_email(self, email):
        """
        Проверка уникальности email
        """
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Этот email уже используется. Пожалуйста, выберите другой.') 