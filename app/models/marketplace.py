from app.extensions import db


class Offers(db.Model):
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
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    parent = db.Column(db.Integer, nullable=True)


class Requests(db.Model):
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
