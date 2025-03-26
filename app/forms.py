from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, FloatField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

class ClientForm(FlaskForm):
    name = StringField('Имя клиента', validators=[DataRequired(), Length(max=100)])
    company = StringField('Компания', validators=[Optional(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])
    address = StringField('Адрес', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Сохранить')

class OrderForm(FlaskForm):
    title = StringField('Название заявки', validators=[DataRequired(), Length(max=200)])
    client_id = SelectField('Клиент', coerce=int, validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[Optional()])
    status = SelectField('Статус', choices=[
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена')
    ])
    priority = SelectField('Приоритет', choices=[
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий')
    ])
    deadline = DateField('Срок выполнения', validators=[Optional()])
    amount = FloatField('Сумма', validators=[Optional()])
    profit = FloatField('Прибыль', validators=[Optional()])
    submit = SubmitField('Сохранить')

class ProfileForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Сохранить изменения')

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Текущий пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), Length(min=6)])
    new_password2 = PasswordField('Повторите новый пароль', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Изменить пароль')

class FeedbackForm(FlaskForm):
    name = StringField('Ваше имя', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Сообщение', validators=[DataRequired()])
    submit = SubmitField('Отправить') 