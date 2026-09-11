from app.extensions import db


class Vendors(db.Model):
    __table_args__ = (
        db.Index(
            "ux_vendors_email",
            "email",
            unique=True,
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    logo = db.Column(db.Text, nullable=True)
