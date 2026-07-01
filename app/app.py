from flask import Flask, render_template, redirect, url_for
from extensions import db, login_manager, login_user, current_user, login_required, logout_user
from forms import RegistrationForm, LoginForm
from dotenv import load_dotenv
from pathlib import Path
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)

current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
dotenv_path = root_dir / '.env'

APP_DIR = os.path.abspath(os.path.dirname(__file__))
app.instance_path = os.path.join(APP_DIR, 'instance')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'site.db')}"

load_dotenv(dotenv_path)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db.init_app(app)
login_manager.init_app(app)
bcrypt = Bcrypt(app)
from models import User, Violation

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User (
            name = form.username.data,
            email = form.email.data,
            chat_id = form.chat_id.data,
            password_hash = hashed_password
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('opportunities'))    
    return render_template("login.html", title="Login", form=form)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

if __name__ == '__main__':
    app.run(debug=True)