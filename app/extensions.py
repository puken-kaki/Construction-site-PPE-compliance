from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, current_user, login_required, logout_user

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'