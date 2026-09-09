from app.extensions import db


class Advertisement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    filename = db.Column(db.Text, nullable=True)
    format = db.Column(db.Text, nullable=True)
    frame = db.Column(db.String(100), nullable=True)
