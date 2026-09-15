"""separate favorites and cart offers

Revision ID: ebb86d5e3e83
Revises: 6095ddec2a50
Create Date: 2026-09-14 19:53:02.192165
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ebb86d5e3e83"
down_revision = "6095ddec2a50"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Создаём настоящую таблицу избранного.
    op.create_table(
        "favorites",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "product_id",
            name="ux_favorites_user_product",
        ),
    )

    with op.batch_alter_table(
            "favorites",
            schema=None,
    ) as batch_op:
        batch_op.create_index(
            "ix_favorites_product_id",
            ["product_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_favorites_user_id",
            ["user_id"],
            unique=False,
        )

    # 2. Старые cart_items на самом деле использовались как избранное.
    # Переносим их в новую таблицу ДО удаления product_id.
    op.execute(
        sa.text(
            """
            INSERT INTO favorites (
                user_id,
                product_id,
                created_at
            )
            SELECT
                user_id,
                product_id,
                created_at
            FROM cart_items
            """
        )
    )

    # 3. После переноса старые строки cart_items больше не являются
    # настоящей корзиной и должны быть удалены.
    op.execute(
        sa.text(
            """
            DELETE FROM cart_items
            """
        )
    )

    # 4. Перестраиваем cart_items:
    # Product -> Offer.
    with op.batch_alter_table(
            "cart_items",
            schema=None,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "offer_id",
                sa.Integer(),
                nullable=False,
            )
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_cart_items_product_id"
            )
        )

        batch_op.drop_constraint(
            batch_op.f(
                "ux_cart_items_user_product"
            ),
            type_="unique",
        )

        batch_op.drop_constraint(
            batch_op.f(
                "cart_items_product_id_fkey"
            ),
            type_="foreignkey",
        )

        batch_op.create_index(
            "ix_cart_items_offer_id",
            ["offer_id"],
            unique=False,
        )

        batch_op.create_unique_constraint(
            "ux_cart_items_user_offer",
            ["user_id", "offer_id"],
        )

        batch_op.create_foreign_key(
            "fk_cart_items_offer_id_offers",
            "offers",
            ["offer_id"],
            ["id"],
            ondelete="CASCADE",
        )

        batch_op.drop_column(
            "product_id"
        )

        batch_op.drop_column(
            "price"
        )


def downgrade():
    # Сначала возвращаем старые поля.
    # Они nullable=True временно, потому что текущая корзина
    # может уже содержать строки.
    with op.batch_alter_table(
            "cart_items",
            schema=None,
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "product_id",
                sa.Integer(),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "price",
                sa.Float(),
                nullable=True,
            )
        )

    # Восстанавливаем product_id и price у элементов
    # современной корзины через Offer.
    op.execute(
        sa.text(
            """
            UPDATE cart_items
            SET
                product_id = (
                    SELECT offers.product_id
                    FROM offers
                    WHERE offers.id = cart_items.offer_id
                ),
                price = (
                    SELECT offers.price
                    FROM offers
                    WHERE offers.id = cart_items.offer_id
                )
            """
        )
    )

    with op.batch_alter_table(
            "cart_items",
            schema=None,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_cart_items_offer_id_offers",
            type_="foreignkey",
        )

        batch_op.drop_constraint(
            "ux_cart_items_user_offer",
            type_="unique",
        )

        batch_op.drop_index(
            "ix_cart_items_offer_id"
        )

        batch_op.drop_column(
            "offer_id"
        )

        batch_op.alter_column(
            "product_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

        batch_op.alter_column(
            "price",
            existing_type=sa.Float(),
            nullable=False,
        )

        batch_op.create_foreign_key(
            "cart_items_product_id_fkey",
            "products",
            ["product_id"],
            ["id"],
            ondelete="CASCADE",
        )

        batch_op.create_unique_constraint(
            "ux_cart_items_user_product",
            ["user_id", "product_id"],
        )

        batch_op.create_index(
            "ix_cart_items_product_id",
            ["product_id"],
            unique=False,
        )

    # Старое приложение считало избранное строками cart_items.
    # Возвращаем favorites обратно туда.
    #
    # NOT EXISTS нужен на случай, если в новой корзине уже был
    # тот же user + product.
    op.execute(
        sa.text(
            """
            INSERT INTO cart_items (
                user_id,
                product_id,
                price,
                quantity,
                created_at
            )
            SELECT
                favorites.user_id,
                favorites.product_id,
                0.0,
                1,
                favorites.created_at
            FROM favorites
            WHERE NOT EXISTS (
                SELECT 1
                FROM cart_items
                WHERE
                    cart_items.user_id
                        = favorites.user_id
                  AND cart_items.product_id
                    = favorites.product_id
            )
            """
        )
    )

    with op.batch_alter_table(
            "favorites",
            schema=None,
    ) as batch_op:
        batch_op.drop_index(
            "ix_favorites_user_id"
        )
        batch_op.drop_index(
            "ix_favorites_product_id"
        )

    op.drop_table(
        "favorites"
    )