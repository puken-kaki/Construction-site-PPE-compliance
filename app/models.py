from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from extensions import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    chat_id = db.Column(db.Integer, unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    violations = db.relationship('Violation', backref='owner', lazy=True)


class Violation(db.Model):
    __tablename__ = 'violations'

    id = db.Column(db.Integer, primary_key=True)
    violation_time = db.Column(db.DateTime, default=func.now(), nullable=False)
    camera_id = db.Column(db.String(50), default="Cam_01", nullable=False)
    person_id = db.Column(db.Integer, nullable=False)
    violation_type = db.Column(db.String(50), default="No Helmet", nullable=False)
    cropped_path = db.Column(db.String(255), nullable=False)
    full_frame_path = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)