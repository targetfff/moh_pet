from datetime import datetime
from uuid import uuid4

from app.extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    __table_args__ = (
        db.Index(
            "ix_orders_user_created_at",
            "user_id",
            "created_at",
        ),
        db.Index(
            "ix_orders_status_created_at",
            "status",
            "created_at",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # Заказ сохраняем даже если когда-нибудь
    # пользователь будет удалён.
    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    status = db.Column(
        db.String(32),
        nullable=False,
        default="pending_payment",
    )

    # Snapshot покупателя.
    customer_email = db.Column(
        db.String(100),
        nullable=False,
    )

    customer_name = db.Column(
        db.String(201),
        nullable=False,
    )

    # Только стоимость товаров.
    subtotal = db.Column(
        db.Numeric(12, 2),
        nullable=False,
    )

    # Сумма всех Legit Check fee.
    legit_fee_total = db.Column(
        db.Numeric(12, 2),
        nullable=False,
    )

    # subtotal + legit_fee_total
    total = db.Column(
        db.Numeric(12, 2),
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
    )

    paid_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    user = db.relationship(
        "Users",
        back_populates="orders",
    )

    items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select",
    )

    payments = db.relationship(
        "Payment",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select",
    )


class OrderItem(db.Model):
    __tablename__ = "order_items"

    __table_args__ = (
        db.UniqueConstraint(
            "order_id",
            "offer_id",
            name="ux_order_items_order_offer",
        ),
        db.Index(
            "ix_order_items_order_id",
            "order_id",
        ),
        db.Index(
            "ix_order_items_offer_id",
            "offer_id",
        ),
        db.Index(
            "ix_order_items_product_id",
            "product_id",
        ),
        db.Index(
            "ix_order_items_vendor_id",
            "vendor_id",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # Эти три FK нужны для связи с текущими сущностями,
    # но snapshot заказа от них не зависит.
    offer_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "offers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "products.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    vendor_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "vendors.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    # Snapshot данных на момент оформления.
    product_title = db.Column(
        db.String(100),
        nullable=False,
    )

    vendor_title = db.Column(
        db.String(100),
        nullable=False,
    )

    unit_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
    )

    quantity = db.Column(
        db.Integer,
        nullable=False,
    )

    legit_fee = db.Column(
        db.Numeric(12, 2),
        nullable=False,
    )

    line_total = db.Column(
        db.Numeric(12, 2),
        nullable=False,
    )

    order = db.relationship(
        "Order",
        back_populates="items",
    )

    offer = db.relationship(
        "Offers",
    )

    product = db.relationship(
        "Products",
    )

    vendor = db.relationship(
        "Vendors",
    )


class Payment(db.Model):
    __tablename__ = "payments"

    __table_args__ = (
        db.Index(
            "ix_payments_order_id",
            "order_id",
        ),
        db.Index(
            "ix_payments_status_created_at",
            "status",
            "created_at",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    provider = db.Column(
        db.String(32),
        nullable=False,
        default="mock",
    )

    status = db.Column(
        db.String(32),
        nullable=False,
        default="pending",
    )

    amount = db.Column(
        db.Numeric(12, 2),
        nullable=False,
    )

    # Аналог id транзакции платёжной системы.
    external_id = db.Column(
        db.String(64),
        nullable=False,
        unique=True,
        default=lambda: uuid4().hex,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    order = db.relationship(
        "Order",
        back_populates="payments",
    )