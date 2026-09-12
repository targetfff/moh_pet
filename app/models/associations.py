from app.extensions import db


product_categories = db.Table(
    "product_categories",
    db.Column(
        "product_id",
        db.Integer,
        db.ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    db.Column(
        "category_id",
        db.Integer,
        db.ForeignKey(
            "categories.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    db.Index(
        "ix_product_categories_category_id",
        "category_id",
    ),
)
