from app.extensions import db

from .associations import product_categories


class Offers(db.Model):
    __table_args__ = (
        db.Index(
            "ux_offers_vendor_product",
            "vendor_id",
            "product_id",
            unique=True,
        ),
        db.Index(
            "ix_offers_product_id",
            "product_id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(
        db.Integer,
        db.ForeignKey("vendors.id"),
        nullable=False,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
    )
    price = db.Column(db.Float, nullable=False)


class Categories(db.Model):
    __table_args__ = (
        db.Index(
            "ix_categories_parent",
            "parent",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    parent = db.Column(db.Integer, nullable=True)

    products = db.relationship(
        "Products",
        secondary=product_categories,
        back_populates="categories",
        lazy="select",
        passive_deletes=True,
    )


class Requests(db.Model):
    __table_args__ = (
        db.Index(
            "ux_requests_vendor_product",
            "vendor_id",
            "product_id",
            unique=True,
        ),
        db.Index(
            "ix_requests_product_id",
            "product_id",
        ),
        db.Index(
            "ix_requests_date",
            "date",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(
        db.Integer,
        db.ForeignKey("vendors.id"),
        nullable=False,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
    )
    price = db.Column(db.Float, nullable=False)
    photos = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=True)


class Suggestions(db.Model):
    __table_args__ = (
        db.Index(
            "ix_suggestions_accepted_date",
            "accepted",
            "date",
        ),
        db.Index(
            "ix_suggestions_vendor_id",
            "vendor_id",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(
        db.Integer,
        db.ForeignKey("vendors.id"),
        nullable=False,
    )
    title = db.Column(db.String(100), nullable=False)
    photos = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=True)
    accepted = db.Column(db.Boolean, nullable=True)
