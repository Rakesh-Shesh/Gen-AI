from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'user'

    # Relationship to Submission
    submissions = db.relationship('Submission', backref='user', lazy=True)


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    photo_filename = db.Column(db.String(120), nullable=True)

    # Relationship to User (already defined in User model)
    user = db.relationship('User', backref=db.backref('submissions', lazy=True))

