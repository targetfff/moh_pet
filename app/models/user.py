from flask_login import UserMixin

from app.extensions import db


class Users(db.Model, UserMixin):
    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    phone = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
    )

    email = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.String(255),
        nullable=False,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
    )

    surname = db.Column(
        db.String(100),
        nullable=False,
    )

    status = db.Column(
        db.String(100),
        nullable=False,
    )

    confirmed = db.Column(
        db.Boolean,
        nullable=True,
    )

    cart_items = db.relationship(
        "CartItem",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select",
    )

    recent_views = db.relationship(
        "RecentView",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select",
    )

    favorites = db.relationship(
        "Favorite",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select",
    )

    orders = db.relationship(
        "Order",
        back_populates="user",
        lazy="select",
    )
