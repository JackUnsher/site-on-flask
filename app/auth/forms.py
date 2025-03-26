from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from app.models.user import User


class LoginForm(FlaskForm):
    """Форма входа в систему"""
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    """Форма регистрации нового пользователя"""
    username = StringField('Имя пользователя', validators=[
        DataRequired(),
        Length(min=2, max=64)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(),
        Length(min=8, message='Пароль должен содержать не менее 8 символов')
    ])
    password2 = PasswordField(
        'Повторите пароль', 
        validators=[
            DataRequired(), 
            EqualTo('password', message='Пароли должны совпадать')
        ]
    )
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        """Проверка уникальности имени пользователя"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Это имя пользователя уже занято. Пожалуйста, используйте другое.')

    def validate_email(self, email):
        """Проверка уникальности email"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Этот email уже зарегистрирован. Пожалуйста, используйте другой.') 