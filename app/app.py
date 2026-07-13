from flask import Flask, render_template, redirect, url_for, Response, flash, request
from extensions import db, login_manager, login_user, current_user, login_required, logout_user
from forms import RegistrationForm, LoginForm, CameraForm
from video_processor import CameraStreamWorker, global_frames, active_violations_event_list
from dotenv import load_dotenv
from pathlib import Path
from flask_bcrypt import Bcrypt
import time
import os

app = Flask(__name__)

current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
dotenv_path = root_dir / '.env'
load_dotenv(dotenv_path)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

APP_DIR = os.path.abspath(os.path.dirname(__file__))
app.instance_path = os.path.join(APP_DIR, 'instance')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'site.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager.init_app(app)
bcrypt = Bcrypt(app)
from models import User, Violation, Camera

camera_threads = {}

def start_all_cameras():
    with app.app_context():
        active_cameras = Camera.query.filter_by(is_active=True).all()
        for cam in active_cameras:
            if cam.id not in camera_threads:
                bot_token = os.getenv("BOT_TOKEN")
                chat_id = cam.owner.chat_id

                worker=CameraStreamWorker(
                    camera_id=cam.id,
                    video_path=cam.video_source,
                    bot_token=bot_token,
                    chat_id=chat_id,
                    app_context=app.app_context()
                )
                worker.start()
                camera_threads[cam.id] = worker

def gen_frames(camera_id):
    while True:
        frame = global_frames.get(camera_id)
        if frame is not None:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)

        
@app.route('/video_feed/<int:camera_id>')
@login_required
def video_feed(camera_id):
    camera = Camera.query.get_or_404(camera_id)
    return Response(gen_frames(camera.id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
@login_required
def index():
    user_cameras = Camera.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('index.html', cameras=user_cameras)

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
            return redirect(url_for('index'))    
    return render_template("login.html", title="Login", form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/settings', methods=["GET", "POST"])
@login_required
def settings():
    form = CameraForm()

    if form.validate_on_submit():
        new_cam = Camera(
            name=form.name.data,
            video_source=form.video_source.data,
            user_id=current_user.id
        )
        db.session.add(new_cam)
        db.session.commit()

        bot_token = os.getenv("BOT_TOKEN")
        worker = CameraStreamWorker(
            camera_id=new_cam.id,
            video_path=new_cam.video_source,
            bot_token=bot_token,
            chat_id=current_user.chat_id,
            app_context=app.app_context()
        )
        worker.start()
        camera_threads[new_cam.id] = worker

        flash(f"New camera '{new_cam.name}' added successfully")
        return redirect(url_for('settings'))
    
    my_cameras = Camera.query.filter_by(user_id=current_user.id).all()
    return render_template('settings.html', form=form, cameras=my_cameras)

@app.route('/violation_logs')
@login_required
def violation_logs():
    query = Violation.query.filter_by(user_id=current_user.id)
    
    camera_id = request.args.get('camera_id', type=int)
    selected_date = request.args.get('date', type=str)

    if camera_id:
        query = query.filter_by(camera_id=camera_id)
    if selected_date:
        query = query.filter(db.func.date(Violation.violation_time) == selected_date)
        
    violations = query.order_by(Violation.violation_time.desc()).all()
    user_cameras = Camera.query.filter_by(user_id=current_user.id).all()

    if request.headers.get('HX-Request'):
        return render_template('_violation_table_rows.html', violations=violations)
    return render_template('violation_logs.html', violations=violations, cameras=user_cameras)

@app.route('/camera/delete/<int:camera_id>', methods=['POST'])
@login_required
def delete_camera(camera_id):
    camera = Camera.query.get_or_404(camera_id)
    if camera.user_id == current_user.id:
        if camera_id in camera_threads:
            camera_threads[camera_id].stop()
            camera_threads[camera_id].join()
            del camera_threads[camera_id]

        if camera_id in global_frames:
            del global_frames[camera_id]

        db.session.delete(camera)
        db.session.commit()

    return '', 200

@app.route('/api/live_violations')
@login_required
def live_violations():
    events = list(reversed(active_violations_event_list))[:20]
    return render_template('_violation_row.html', events=events)


@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    start_all_cameras()
    app.run(debug=True, use_reloader=False)