from datetime import datetime

from app.extensions import db


class Favorite(db.Model):
    __tablename__ = "favorites"

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "product_id",
            name="ux_favorites_user_product",
        ),
        db.Index(
            "ix_favorites_user_id",
            "user_id",
        ),
        db.Index(
            "ix_favorites_product_id",
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

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
    )

    user = db.relationship(
        "Users",
        back_populates="favorites",
    )

    product = db.relationship(
        "Products",
    )


class CartItem(db.Model):
    __tablename__ = "cart_items"

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "offer_id",
            name="ux_cart_items_user_offer",
        ),
        db.Index(
            "ix_cart_items_user_id",
            "user_id",
        ),
        db.Index(
            "ix_cart_items_offer_id",
            "offer_id",
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

    offer_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "offers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
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

    offer = db.relationship(
        "Offers",
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
