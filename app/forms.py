from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, SelectMultipleField, DateField, TextAreaField, IntegerField, URLField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    chat_id = IntegerField('Telegram chat ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_chat_id(self, chat_id):
        existing_user = User.query.filter_by(chat_id=chat_id.data).first()
        if existing_user:
            raise ValidationError('This Telegram chat ID is already taken.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Log In')

class CameraForm(FlaskForm):
    name = StringField('Camera name', validators=[DataRequired(), Length(min=2, max=100)])
    video_source = StringField('Live video source (RTSP URL)', validators=[DataRequired()])
    submit = SubmitField('Add camera')