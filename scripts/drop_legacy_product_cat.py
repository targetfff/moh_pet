from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from sqlalchemy import inspect, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app import create_app
from app.extensions import db


MIN_SQLITE = (3, 35, 0)


def parse_version(value: str) -> tuple[int, int, int]:
    parts = value.split(".")
    nums = [int(part) for part in parts[:3]]

    while len(nums) < 3:
        nums.append(0)

    return tuple(nums)


def main() -> None:
    app = create_app()

    with app.app_context():
        engine = db.engine
        inspector = inspect(engine)

        columns = {
            column["name"]
            for column in inspector.get_columns("products")
        }

        if "cat" not in columns:
            print("Колонка products.cat уже отсутствует.")
            return

        with engine.connect() as conn:
            sqlite_version = conn.execute(
                text("SELECT sqlite_version()")
            ).scalar_one()

        print(f"SQLite: {sqlite_version}")

        if parse_version(sqlite_version) < MIN_SQLITE:
            raise RuntimeError(
                "SQLite < 3.35.0 не поддерживает "
                "ALTER TABLE ... DROP COLUMN. "
                "Нужна миграция через пересоздание таблицы."
            )

        print("Удаляю legacy-колонку products.cat...")

        # ALTER TABLE выполняется в транзакции.
        # Если cat участвует в индексе/триггере/ограничении,
        # SQLite сам отклонит операцию и транзакция откатится.
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE products "
                    "DROP COLUMN cat"
                )
            )

        remaining_columns = {
            column["name"]
            for column in inspect(engine).get_columns("products")
        }

        if "cat" in remaining_columns:
            raise RuntimeError(
                "Колонка products.cat всё ещё существует."
            )

        with engine.connect() as conn:
            products_count = conn.execute(
                text("SELECT COUNT(*) FROM products")
            ).scalar_one()

            links_count = conn.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM product_categories"
                )
            ).scalar_one()

        print("Готово.")
        print(f"Products: {products_count}")
        print(f"Product↔Category связей: {links_count}")
        print("Legacy products.cat удалена.")


if __name__ == "__main__":
    main()
