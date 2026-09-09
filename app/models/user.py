from flask_login import UserMixin

from app.extensions import db


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    cart = db.Column(db.Text, nullable=True)
    recent = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(100), nullable=False)
    confirmed = db.Column(db.Boolean, nullable=True)
