"""add orders and payments

Revision ID: e5a7d53335bf
Revises: 59700ddb255e
Create Date: 2026-09-14 22:24:24.901461
"""

from alembic import op
import sqlalchemy as sa


revision = "e5a7d53335bf"
down_revision = "59700ddb255e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("customer_email", sa.String(length=100), nullable=False),
        sa.Column("customer_name", sa.String(length=201), nullable=False),
        sa.Column("subtotal", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("legit_fee_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.create_index(
            "ix_orders_status_created_at",
            ["status", "created_at"],
            unique=False,
        )
        batch_op.create_index(
            "ix_orders_user_created_at",
            ["user_id", "created_at"],
            unique=False,
        )

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("vendor_id", sa.Integer(), nullable=True),
        sa.Column("product_title", sa.String(length=100), nullable=False),
        sa.Column("vendor_title", sa.String(length=100), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("legit_fee", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("line_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "order_id",
            "offer_id",
            name="ux_order_items_order_offer",
        ),
    )

    with op.batch_alter_table("order_items", schema=None) as batch_op:
        batch_op.create_index(
            "ix_order_items_offer_id",
            ["offer_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_order_items_order_id",
            ["order_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_order_items_product_id",
            ["product_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_order_items_vendor_id",
            ["vendor_id"],
            unique=False,
        )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
    )

    with op.batch_alter_table("payments", schema=None) as batch_op:
        batch_op.create_index(
            "ix_payments_order_id",
            ["order_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_payments_status_created_at",
            ["status", "created_at"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("payments", schema=None) as batch_op:
        batch_op.drop_index("ix_payments_status_created_at")
        batch_op.drop_index("ix_payments_order_id")

    op.drop_table("payments")

    with op.batch_alter_table("order_items", schema=None) as batch_op:
        batch_op.drop_index("ix_order_items_vendor_id")
        batch_op.drop_index("ix_order_items_product_id")
        batch_op.drop_index("ix_order_items_order_id")
        batch_op.drop_index("ix_order_items_offer_id")

    op.drop_table("order_items")

    with op.batch_alter_table("orders", schema=None) as batch_op:
        batch_op.drop_index("ix_orders_user_created_at")
        batch_op.drop_index("ix_orders_status_created_at")

    op.drop_table("orders")
