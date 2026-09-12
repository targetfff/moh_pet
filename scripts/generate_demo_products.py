from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app import create_app
from app.extensions import db
from app.models import (
    Categories,
    Offers,
    Products,
    Vendors,
    product_categories,
)
from app.services.catalog import refresh_catalog_products


DEMO_PREFIX = "[DEMO]"

TITLE_SUFFIXES = (
    "Nova",
    "Prime",
    "Core",
    "Air",
    "Pro",
    "Lite",
    "Max",
    "Plus",
    "One",
    "X",
    "S",
    "Ultra",
)

DESCRIPTIONS = (
    "Демо-товар для проверки каталога и фильтров.",
    "Тестовая карточка товара для нагрузочной проверки.",
    "Демо-позиция для проверки продавцов и категорий.",
    "Товар создан автоматически для тестирования каталога.",
)


def leaf_categories(categories):
    parent_ids = {
        category.parent
        for category in categories
        if category.parent not in (None, 0)
    }

    leaves = [
        category
        for category in categories
        if category.id not in parent_ids
    ]

    return leaves or categories


def existing_product_images():
    rows = (
        Products.query
        .filter(
            Products.main_image.isnot(None),
            Products.main_image != "",
            )
        .all()
    )

    result = []

    for product in rows:
        if not product.main_image:
            continue

        result.append(
            {
                "main_image": product.main_image,
                "images": (
                    product.images
                    if product.images
                    else str([product.main_image])
                ),
            }
        )

    return result


def build_title(category, index, rng):
    suffix = rng.choice(TITLE_SUFFIXES)

    # Ограничение Products.title = String(100)
    title = (
        f"{DEMO_PREFIX} "
        f"{category.title or 'Товар'} "
        f"{suffix} {index:02d}"
    )

    return title[:100]


def generate_products(count, seed):
    rng = random.Random(seed)

    vendors = Vendors.query.order_by(
        Vendors.id.asc()
    ).all()

    categories = Categories.query.order_by(
        Categories.id.asc()
    ).all()

    images = existing_product_images()

    if not vendors:
        raise RuntimeError(
            "В базе нет продавцов. "
            "Нужен хотя бы один Vendors."
        )

    if not categories:
        raise RuntimeError(
            "В базе нет категорий."
        )

    if not images:
        raise RuntimeError(
            "Не найдено ни одного существующего "
            "Products.main_image."
        )

    target_categories = leaf_categories(
        categories
    )

    existing_demo_count = (
        Products.query
        .filter(
            Products.title.like(
                f"{DEMO_PREFIX}%"
            )
        )
        .count()
    )

    start_number = existing_demo_count + 1
    created_products = []

    for offset in range(count):
        number = start_number + offset

        category = target_categories[
            offset % len(target_categories)
            ]

        image_data = rng.choice(images)

        product = Products(
            title=build_title(
                category,
                number,
                rng,
            ),
            vendor=None,
            vendors=None,
            main_logo="",
            logos=None,
            price=-1,
            description=rng.choice(
                DESCRIPTIONS
            )[:100],
            full_description=(
                "Автоматически созданный демо-товар. "
                "Используется только для локального "
                "тестирования каталога, фильтрации, "
                "пагинации и офферов продавцов."
            ),
            images=image_data["images"],
            date=(
                    datetime.now()
                    - timedelta(
                minutes=rng.randint(
                    0,
                    60 * 24 * 30,
                    )
            )
            ),
            main_image=(
                image_data["main_image"]
            ),
        )

        product.categories = [category]

        db.session.add(product)
        created_products.append(product)

    # Получаем id всех новых товаров до создания Offers.
    db.session.flush()

    created_ids = []

    for product in created_products:
        created_ids.append(product.id)

        offer_count = rng.randint(
            1,
            min(3, len(vendors)),
        )

        selected_vendors = rng.sample(
            vendors,
            offer_count,
        )

        # Базовая цена товара.
        base_price = rng.randint(
            5,
            300,
        ) * 100

        for vendor in selected_vendors:
            deviation = rng.uniform(
                0.90,
                1.18,
            )

            price = round(
                base_price * deviation,
                2,
                )

            db.session.add(
                Offers(
                    vendor_id=vendor.id,
                    product_id=product.id,
                    price=price,
                )
            )

    # Нужен flush, чтобы bulk refresh увидел новые Offers.
    db.session.flush()

    # Одним Products SELECT + одним Offers/Vendors JOIN
    # пересчитываем cached price/vendor/logo поля.
    refresh_catalog_products(
        created_ids
    )

    db.session.commit()

    return created_products


def clean_demo_products():
    demo_products = (
        Products.query
        .filter(
            Products.title.like(
                f"{DEMO_PREFIX}%"
            )
        )
        .all()
    )

    if not demo_products:
        print(
            "Демо-товары не найдены."
        )
        return

    demo_ids = [
        product.id
        for product in demo_products
    ]

    Offers.query.filter(
        Offers.product_id.in_(demo_ids)
    ).delete(
        synchronize_session=False
    )

    db.session.execute(
        product_categories.delete().where(
            product_categories.c.product_id.in_(
                demo_ids
            )
        )
    )

    Products.query.filter(
        Products.id.in_(demo_ids)
    ).delete(
        synchronize_session=False
    )

    db.session.commit()

    print(
        f"Удалено демо-товаров: "
        f"{len(demo_ids)}"
    )


def print_summary(products):
    ids = [
        product.id
        for product in products
    ]

    offer_count = (
        Offers.query
        .filter(
            Offers.product_id.in_(ids)
        )
        .count()
    )

    category_link_count = (
        db.session.query(
            product_categories
        )
        .filter(
            product_categories.c.product_id.in_(
                ids
            )
        )
        .count()
    )

    print()
    print(
        f"Создано товаров: "
        f"{len(products)}"
    )
    print(
        f"Создано офферов: "
        f"{offer_count}"
    )
    print(
        f"Product↔Category связей: "
        f"{category_link_count}"
    )
    print(
        f"ID новых товаров: "
        f"{min(ids)}..{max(ids)}"
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Добавляет демо-товары с офферами "
            "существующих продавцов."
        )
    )

    parser.add_argument(
        "--count",
        type=int,
        default=40,
        help=(
            "Сколько товаров создать "
            "(по умолчанию: 40)."
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help=(
            "Seed генератора "
            "(по умолчанию: 42)."
        ),
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help=(
            "Удалить все товары, "
            "созданные этим скриптом."
        ),
    )

    args = parser.parse_args()

    if args.count < 1:
        parser.error(
            "--count должен быть >= 1"
        )

    app = create_app()

    with app.app_context():
        try:
            if args.clean:
                clean_demo_products()
                return

            products = generate_products(
                args.count,
                args.seed,
            )

            print_summary(products)

        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    main()
