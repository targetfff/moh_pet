from datetime import datetime

from app.extensions import db


class CartItem(db.Model):
    __tablename__ = "cart_items"

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "product_id",
            name="ux_cart_items_user_product",
        ),
        db.Index(
            "ix_cart_items_user_id",
            "user_id",
        ),
        db.Index(
            "ix_cart_items_product_id",
            "product_id",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    price = db.Column(
        db.Float,
        nullable=False,
        default=0.0,
    )

    quantity = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
    )

    user = db.relationship(
        "Users",
        back_populates="cart_items",
    )


class RecentView(db.Model):
    __tablename__ = "recent_views"

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "product_id",
            name="ux_recent_views_user_product",
        ),
        db.Index(
            "ix_recent_views_user_viewed_at",
            "user_id",
            "viewed_at",
        ),
        db.Index(
            "ix_recent_views_product_id",
            "product_id",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    viewed_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
    )

    user = db.relationship(
        "Users",
        back_populates="recent_views",
    )
