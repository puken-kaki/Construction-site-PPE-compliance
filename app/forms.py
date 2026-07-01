from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, SelectMultipleField, DateField, TextAreaField, IntegerField, URLField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Электронный адрес', validators=[DataRequired(), Email()])
    chat_id = IntegerField('Telegram chat ID', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Потвердить пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    email = StringField('Электронный адрес', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Войти')