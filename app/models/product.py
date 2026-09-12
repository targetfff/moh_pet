from app.extensions import db

from .associations import product_categories


class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)

    # Старое поле cat намеренно больше не описываем в ORM.
    # В существующей SQLite БД колонка пока может оставаться:
    # миграционный скрипт перенесёт данные в product_categories.
    categories = db.relationship(
        "Categories",
        secondary=product_categories,
        back_populates="products",
        lazy="select",
        passive_deletes=True,
    )

    vendor = db.Column(db.Text, nullable=True)
    vendors = db.Column(db.Text, nullable=True)
    main_logo = db.Column(db.Text, nullable=False)
    logos = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=True)
    description = db.Column(db.String(100), nullable=True)
    full_description = db.Column(db.Text, nullable=True)
    images = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=True)
    main_image = db.Column(db.Text, nullable=False)
