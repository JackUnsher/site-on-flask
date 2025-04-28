from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, HiddenField, TextAreaField, FileField, validators
from wtforms.validators import ValidationError
from flask_babel import lazy_gettext as _l
from flask import current_app
from app.models import User
from flask_login import current_user


class EditProfileForm(FlaskForm):
    """Форма редактирования профиля"""
    username = StringField(_l('Username'), validators=[validators.DataRequired(), validators.Length(min=2, max=64)])
    first_name = StringField(_l('First Name'), validators=[validators.Optional(), validators.Length(max=50)])
    last_name = StringField(_l('Last Name'), validators=[validators.Optional(), validators.Length(max=50)])
    email = StringField(_l('Email'), validators=[validators.DataRequired(), validators.Email()])
    phone = StringField(_l('Phone Number'), validators=[validators.Optional(), validators.Length(max=20)])
    country = SelectField(_l('Country'), choices=[
        ('', _l('Select Country')),
        ('US', _l('United States')),
        ('UK', _l('United Kingdom')),
        ('RU', _l('Russia')),
        ('DE', _l('Germany')),
        ('FR', _l('France')),
        ('CN', _l('China')),
        ('JP', _l('Japan')),
        ('KR', _l('South Korea')),
        ('BR', _l('Brazil')),
        ('IN', _l('India')),
        ('CA', _l('Canada')),
        ('AU', _l('Australia')),
        ('OTHER', _l('Other'))
    ])
    language = SelectField(_l('Language'), choices=[('en', 'English'), ('ru', 'Русский')])
    avatar = FileField(_l('Avatar'), validators=[validators.Optional()])
    submit = SubmitField(_l('Save changes'))
    
    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError(_l('Please use a different username.'))
    
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError(_l('Please use a different email address.'))
    
    def validate_avatar(self, avatar):
        if avatar.data:
            filename = avatar.data.filename.lower()
            if not (filename.endswith('.jpg') or filename.endswith('.jpeg') or filename.endswith('.png')):
                raise ValidationError(_l('Only JPG and PNG images are allowed'))


class ChangePasswordForm(FlaskForm):
    """Форма изменения пароля"""
    current_password = PasswordField(_l('Current Password'), validators=[validators.DataRequired()])
    new_password = PasswordField(_l('New Password'), validators=[
        validators.DataRequired(), 
        validators.Length(min=8, message=_l('Password must be at least 8 characters long'))
    ])
    confirm_password = PasswordField(_l('Confirm New Password'), validators=[
        validators.DataRequired(), 
        validators.EqualTo('new_password', message=_l('Passwords do not match'))
    ])
    submit = SubmitField(_l('Change Password'))


class TwoFactorSettingsForm(FlaskForm):
    """Форма настройки двухфакторной аутентификации"""
    method = SelectField(_l('Authentication Method'), choices=[
        ('email', _l('Email')), 
        ('authenticator', _l('Authenticator App'))
    ])
    code = StringField(_l('Verification Code'), validators=[
        validators.DataRequired(), 
        validators.Length(min=6, max=6, message=_l('Verification code must be 6 digits'))
    ])
    secret_key = HiddenField()
    submit = SubmitField(_l('Enable Two-Factor Authentication'))


class WithdrawalForm(FlaskForm):
    """Форма для создания заявки на вывод средств"""
    amount = StringField(_l('Amount (BTC)'), validators=[validators.DataRequired()])
    wallet_address = StringField(_l('Bitcoin Wallet Address'), validators=[
        validators.DataRequired(), 
        validators.Length(min=26, max=35, message=_l('Invalid Bitcoin wallet address'))
    ])
    contract = SelectField(_l('Select Contract'), coerce=int)
    all_contracts = BooleanField(_l('Withdraw from all contracts'))
    submit = SubmitField(_l('Request Withdrawal'))


class SupportMessageForm(FlaskForm):
    """Форма для отправки сообщения в поддержку"""
    message = TextAreaField(_l('Message'), validators=[
        validators.DataRequired(), 
        validators.Length(min=10, message=_l('Message is too short'))
    ])
    submit = SubmitField(_l('Send Message')) 