from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from flask_babel import lazy_gettext as _l
from app.models.user import User


class LoginForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember me'))
    submit = SubmitField(_l('Login'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[
        DataRequired(), 
        Length(min=8, message=_l('Password must be at least 8 characters long'))
    ])
    password2 = PasswordField(_l('Repeat Password'), validators=[
        DataRequired(), 
        EqualTo('password', message=_l('Passwords do not match'))
    ])
    submit = SubmitField(_l('Register'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_l('Please use a different username.'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_l('Please use a different email address.'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[
        DataRequired(), 
        Length(min=8, message=_l('Password must be at least 8 characters long'))
    ])
    password2 = PasswordField(_l('Repeat Password'), validators=[
        DataRequired(), 
        EqualTo('password', message=_l('Passwords do not match'))
    ])
    submit = SubmitField(_l('Reset Password'))


class TwoFactorForm(FlaskForm):
    code = StringField(_l('Verification Code'), validators=[
        DataRequired(), 
        Length(min=6, max=6, message=_l('Verification code must be 6 digits'))
    ])
    submit = SubmitField(_l('Verify')) 