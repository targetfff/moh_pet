"""use numeric for monetary values

Revision ID: 59700ddb255e
Revises: ebb86d5e3e83
Create Date: 2026-09-14 21:24:32.244441
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "59700ddb255e"
down_revision = "ebb86d5e3e83"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
            "offers",
            schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.DOUBLE_PRECISION(
                precision=53
            ),
            type_=sa.Numeric(
                precision=12,
                scale=2,
            ),
            existing_nullable=False,
            postgresql_using=(
                "price::numeric(12, 2)"
            ),
        )

    with op.batch_alter_table(
            "products",
            schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.DOUBLE_PRECISION(
                precision=53
            ),
            type_=sa.Numeric(
                precision=12,
                scale=2,
            ),
            existing_nullable=True,
            postgresql_using=(
                "price::numeric(12, 2)"
            ),
        )

    with op.batch_alter_table(
            "requests",
            schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.DOUBLE_PRECISION(
                precision=53
            ),
            type_=sa.Numeric(
                precision=12,
                scale=2,
            ),
            existing_nullable=False,
            postgresql_using=(
                "price::numeric(12, 2)"
            ),
        )


def downgrade():
    with op.batch_alter_table(
            "requests",
            schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.Numeric(
                precision=12,
                scale=2,
            ),
            type_=sa.DOUBLE_PRECISION(
                precision=53
            ),
            existing_nullable=False,
            postgresql_using=(
                "price::double precision"
            ),
        )

    with op.batch_alter_table(
            "products",
            schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.Numeric(
                precision=12,
                scale=2,
            ),
            type_=sa.DOUBLE_PRECISION(
                precision=53
            ),
            existing_nullable=True,
            postgresql_using=(
                "price::double precision"
            ),
        )

    with op.batch_alter_table(
            "offers",
            schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "price",
            existing_type=sa.Numeric(
                precision=12,
                scale=2,
            ),
            type_=sa.DOUBLE_PRECISION(
                precision=53
            ),
            existing_nullable=False,
            postgresql_using=(
                "price::double precision"
            ),
        )