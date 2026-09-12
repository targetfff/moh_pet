from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from sqlalchemy import inspect, select, text

from app import create_app
from app.extensions import db
from app.models import Categories, product_categories


def main():
    app = create_app()

    with app.app_context():
        # Создаём только новую association table.
        product_categories.create(
            bind=db.engine,
            checkfirst=True,
        )

        columns = {
            column["name"]
            for column in inspect(
                db.engine
            ).get_columns("products")
        }

        if "cat" not in columns:
            print(
                "Legacy products.cat не найден. "
                "product_categories уже готова."
            )
            return

        valid_category_ids = set(
            db.session.execute(
                select(Categories.id)
            ).scalars()
        )

        legacy_products = db.session.execute(
            text(
                """
                SELECT id, cat
                FROM products
                WHERE cat IS NOT NULL
                  AND TRIM(cat) <> ''
                """
            )
        ).all()

        existing_pairs = set(
            db.session.execute(
                select(
                    product_categories.c.product_id,
                    product_categories.c.category_id,
                )
            ).all()
        )

        rows_to_insert = []
        skipped_values = []

        for product_id, raw_categories in legacy_products:
            product_category_ids = set()

            for raw_id in str(raw_categories).split():
                try:
                    category_id = int(raw_id)
                except ValueError:
                    skipped_values.append(
                        (product_id, raw_id)
                    )
                    continue

                if category_id not in valid_category_ids:
                    skipped_values.append(
                        (product_id, raw_id)
                    )
                    continue

                product_category_ids.add(
                    category_id
                )

            for category_id in product_category_ids:
                pair = (
                    product_id,
                    category_id,
                )

                if pair in existing_pairs:
                    continue

                existing_pairs.add(pair)

                rows_to_insert.append({
                    "product_id": product_id,
                    "category_id": category_id,
                })

        if rows_to_insert:
            db.session.execute(
                product_categories.insert(),
                rows_to_insert,
            )

        db.session.commit()

        total_links = db.session.execute(
            select(
                db.func.count()
            ).select_from(
                product_categories
            )
        ).scalar_one()

        print(
            f"Добавлено связей: "
            f"{len(rows_to_insert)}"
        )
        print(
            f"Всего Product↔Category связей: "
            f"{total_links}"
        )

        if skipped_values:
            print(
                "Пропущены некорректные legacy значения:"
            )

            for product_id, raw_id in skipped_values:
                print(
                    f"  product={product_id}, "
                    f"category={raw_id}"
                )


if __name__ == "__main__":
    main()
