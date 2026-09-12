from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import argparse

from sqlalchemy import select

from app import create_app
from app.extensions import db
from app.models import Products
from app.services.images import ensure_product_thumbnail


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Создать WebP thumbnails для текущих "
            "main_image товаров."
        )
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Перегенерировать уже существующие thumbnails.",
    )

    args = parser.parse_args()

    app = create_app()

    with app.app_context():
        filenames = (
            db.session.execute(
                select(
                    Products.main_image
                )
                .where(
                    Products.main_image.is_not(
                        None
                    )
                )
                .distinct()
            )
            .scalars()
            .all()
        )

        created = 0
        missing = []

        for filename in filenames:
            thumbnail = ensure_product_thumbnail(
                filename,
                overwrite=args.force,
            )

            if thumbnail:
                created += 1
            else:
                missing.append(filename)

        print(
            f"Обработано main_image: "
            f"{len(filenames)}"
        )
        print(
            f"Thumbnail доступен: "
            f"{created}"
        )

        if missing:
            print(
                "Не найдены исходные изображения:"
            )

            for filename in missing:
                print(
                    f"  {filename}"
                )


if __name__ == "__main__":
    main()
