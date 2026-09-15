from __future__ import annotations

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from PIL import Image, ImageDraw
from werkzeug.security import generate_password_hash


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app import create_app
from app.extensions import db
from app.models import (
    Advertisement,
    Categories,
    Offers,
    Products,
    Requests,
    Suggestions,
    Users,
    Vendors,
)
from app.services.catalog import refresh_catalog_products
from app.services.images import ensure_product_thumbnail


DEMO_PASSWORD = "Demo12345!"

IMAGE_DIR = PROJECT_ROOT / "static" / "img"
ADS_DIR = PROJECT_ROOT / "static" / "ads"

NO_PRICE = Decimal("-1.00")

HOODIE_PRICE = Decimal("7990.00")
TSHIRT_STORE_ONE_PRICE = Decimal("3990.00")
TSHIRT_STORE_TWO_PRICE = Decimal("3790.00")
SNEAKERS_PRICE = Decimal("12990.00")
BAG_PRICE = Decimal("6490.00")

SNEAKERS_REQUEST_PRICE = Decimal("12490.00")
HOODIE_REQUEST_PRICE = Decimal("7690.00")


def create_demo_image(
        filename: str,
        title: str,
        subtitle: str,
        *,
        size: int = 1200,
):
    IMAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = IMAGE_DIR / filename

    image = Image.new(
        "RGB",
        (size, size),
        "#f2f5ef",
    )

    draw = ImageDraw.Draw(
        image
    )

    margin = 90

    draw.rounded_rectangle(
        (
            margin,
            margin,
            size - margin,
            size - margin,
        ),
        radius=70,
        fill="#ffffff",
        outline="#202820",
        width=10,
    )

    draw.rectangle(
        (
            margin,
            size // 2 - 18,
            size - margin,
            size // 2 + 18,
        ),
        fill="#202820",
    )

    draw.text(
        (
            margin + 60,
            180,
        ),
        title,
        fill="#202820",
    )

    draw.text(
        (
            margin + 60,
            240,
        ),
        subtitle,
        fill="#556055",
    )

    draw.text(
        (
            margin + 60,
            size - 240,
        ),
        "MOH DEMO",
        fill="#202820",
    )

    image.save(
        path,
        "JPEG",
        quality=90,
    )

    return filename


def create_vendor_logo(
        filename: str,
        label: str,
):
    IMAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = IMAGE_DIR / filename

    image = Image.new(
        "RGB",
        (512, 512),
        "#202820",
    )

    draw = ImageDraw.Draw(
        image
    )

    draw.rounded_rectangle(
        (
            40,
            40,
            472,
            472,
        ),
        radius=80,
        outline="#f2f5ef",
        width=12,
    )

    draw.text(
        (
            90,
            210,
        ),
        label,
        fill="#ffffff",
    )

    image.save(
        path,
        "PNG",
    )

    return filename


def create_demo_ad():
    ADS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = "demo_ad.jpg"
    path = ADS_DIR / filename

    image = Image.new(
        "RGB",
        (1400, 800),
        "#202820",
    )

    draw = ImageDraw.Draw(
        image
    )

    draw.rounded_rectangle(
        (
            80,
            80,
            1320,
            720,
        ),
        radius=60,
        outline="#f2f5ef",
        width=12,
    )

    draw.text(
        (
            160,
            250,
        ),
        "MOH",
        fill="#ffffff",
    )

    draw.text(
        (
            160,
            330,
        ),
        "DEMO ADVERTISEMENT",
        fill="#d7e2d7",
    )

    draw.text(
        (
            160,
            410,
        ),
        "Marketplace demo media",
        fill="#ffffff",
    )

    image.save(
        path,
        "JPEG",
        quality=90,
    )

    return filename


def prepare_demo_media():
    media = {
        "hoodie": create_demo_image(
            "demo_product_hoodie.jpg",
            "MOH HOODIE",
            "Demo product",
        ),
        "hoodie_extra": create_demo_image(
            "demo_product_hoodie_extra.jpg",
            "MOH HOODIE",
            "Additional photo",
        ),
        "tshirt": create_demo_image(
            "demo_product_tshirt.jpg",
            "MOH T-SHIRT",
            "Demo product",
        ),
        "tshirt_extra": create_demo_image(
            "demo_product_tshirt_extra.jpg",
            "MOH T-SHIRT",
            "Additional photo",
        ),
        "sneakers": create_demo_image(
            "demo_product_sneakers.jpg",
            "MOH SNEAKERS",
            "Demo product",
        ),
        "sneakers_extra": create_demo_image(
            "demo_product_sneakers_extra.jpg",
            "MOH SNEAKERS",
            "Additional photo",
        ),
        "bag": create_demo_image(
            "demo_product_bag.jpg",
            "MOH BAG",
            "Demo product",
        ),
        "bag_extra": create_demo_image(
            "demo_product_bag_extra.jpg",
            "MOH BAG",
            "Additional photo",
        ),
        "request_1": create_demo_image(
            "demo_request_1.jpg",
            "TRADE REQUEST",
            "Seller One",
        ),
        "request_2": create_demo_image(
            "demo_request_2.jpg",
            "TRADE REQUEST",
            "Seller Two",
        ),
        "suggest_1": create_demo_image(
            "demo_suggest_1.jpg",
            "PRODUCT IDEA",
            "MOH Cap",
        ),
        "suggest_2": create_demo_image(
            "demo_suggest_2.jpg",
            "PRODUCT IDEA",
            "MOH Backpack",
        ),
    }

    media["vendor_1"] = (
        create_vendor_logo(
            "demo_vendor_1.png",
            "MOH ONE",
        )
    )

    media["vendor_2"] = (
        create_vendor_logo(
            "demo_vendor_2.png",
            "MOH TWO",
        )
    )

    for key in (
            "hoodie",
            "tshirt",
            "sneakers",
            "bag",
    ):
        thumbnail = (
            ensure_product_thumbnail(
                media[key],
                overwrite=True,
            )
        )

        if not thumbnail:
            raise RuntimeError(
                "Could not create thumbnail for "
                f"{media[key]}"
            )

    media["advertisement"] = (
        create_demo_ad()
    )

    return media


def upsert_user(
        *,
        email,
        aliases,
        phone,
        name,
        surname,
        status,
):
    emails = [
        email,
        *aliases,
    ]

    user = (
        Users.query
        .filter(
            Users.email.in_(
                emails
            )
        )
        .first()
    )

    if user is None:
        user = Users()
        db.session.add(
            user
        )

    user.email = email
    user.phone = phone
    user.password = (
        generate_password_hash(
            DEMO_PASSWORD
        )
    )
    user.name = name
    user.surname = surname
    user.status = status
    user.confirmed = True

    db.session.flush()

    return user


def upsert_vendor(
        *,
        user,
        aliases,
        patronymic,
        title,
        logo,
):
    emails = [
        user.email,
        *aliases,
    ]

    vendor = (
        Vendors.query
        .filter(
            Vendors.email.in_(
                emails
            )
        )
        .first()
    )

    if vendor is None:
        vendor = Vendors()
        db.session.add(
            vendor
        )

    vendor.surname = user.surname
    vendor.name = user.name
    vendor.patronymic = patronymic
    vendor.title = title
    vendor.phone = user.phone
    vendor.email = user.email
    vendor.logo = logo

    db.session.flush()

    return vendor


def upsert_category(
        title,
        parent=None,
):
    parent_id = (
        parent.id
        if parent
        else None
    )

    category = (
        Categories.query
        .filter_by(
            title=title,
            parent=parent_id,
        )
        .first()
    )

    if category is None:
        category = Categories(
            title=title,
            parent=parent_id,
        )

        db.session.add(
            category
        )
        db.session.flush()

    return category


def upsert_product(
        *,
        title,
        category,
        main_image,
        extra_images,
        description,
):
    product = (
        Products.query
        .filter_by(
            title=title
        )
        .first()
    )

    if product is None:
        product = Products(
            title=title,
        )

        db.session.add(
            product
        )

    product.vendor = ""
    product.vendors = "[]"

    product.main_logo = ""
    product.logos = "[]"

    product.price = NO_PRICE

    product.description = (
        description
    )

    product.full_description = (
        "Демонстрационный товар MOH. "
        "Создан scripts/bootstrap_db.py "
        "для локальной разработки."
    )

    product.main_image = (
        main_image
    )

    product.images = str(
        [
            main_image,
            *extra_images,
        ]
    )

    if product.date is None:
        product.date = (
            datetime.now()
        )

    product.categories = [
        category
    ]

    db.session.flush()

    return product


def upsert_offer(
        *,
        vendor,
        product,
        price,
):
    offer = (
        Offers.query
        .filter_by(
            vendor_id=vendor.id,
            product_id=product.id,
        )
        .first()
    )

    if offer is None:
        offer = Offers(
            vendor_id=vendor.id,
            product_id=product.id,
        )

        db.session.add(
            offer
        )

    offer.price = price

    db.session.flush()

    return offer


def upsert_trade_request(
        *,
        vendor,
        product,
        price,
        photo,
):
    trade_request = (
        Requests.query
        .filter_by(
            vendor_id=vendor.id,
            product_id=product.id,
        )
        .first()
    )

    if trade_request is None:
        trade_request = Requests(
            vendor_id=vendor.id,
            product_id=product.id,
        )

        db.session.add(
            trade_request
        )

    trade_request.price = price
    trade_request.photos = str(
        [photo]
    )
    trade_request.date = (
        datetime.now()
    )

    db.session.flush()

    return trade_request


def upsert_suggestion(
        *,
        vendor,
        title,
        photo,
):
    suggestion = (
        Suggestions.query
        .filter_by(
            vendor_id=vendor.id,
            title=title,
        )
        .first()
    )

    if suggestion is None:
        suggestion = Suggestions(
            vendor_id=vendor.id,
            title=title,
        )

        db.session.add(
            suggestion
        )

    suggestion.photos = str(
        [photo]
    )
    suggestion.date = (
        datetime.now()
    )
    suggestion.accepted = False

    db.session.flush()

    return suggestion


def upsert_advertisement(
        filename,
):
    title = (
        "[DEMO] MOH Advertisement"
    )

    advertisement = (
        Advertisement.query
        .filter_by(
            title=title
        )
        .first()
    )

    if advertisement is None:
        advertisement = (
            Advertisement()
        )

        db.session.add(
            advertisement
        )

    advertisement.title = title
    advertisement.filename = (
        filename
    )
    advertisement.format = "image"
    advertisement.frame = (
        filename
    )

    db.session.flush()

    return advertisement


def bootstrap():
    media = prepare_demo_media()

    upsert_user(
        email="admin@moh-demo.com",
        aliases=[
            "admin@moh.local",
        ],
        phone="+7 (900) 000-00-01",
        name="Moh",
        surname="Admin",
        status="admin",
    )

    upsert_user(
        email="client@moh-demo.com",
        aliases=[
            "client@moh.local",
        ],
        phone="+7 (900) 000-00-02",
        name="Demo",
        surname="Client",
        status="client",
    )

    seller_user_1 = upsert_user(
        email="seller1@moh-demo.com",
        aliases=[
            "vendor@moh.local",
            "vendor@moh-demo.com",
        ],
        phone="+7 (900) 000-00-03",
        name="Alex",
        surname="Seller",
        status="vendor",
    )

    seller_user_2 = upsert_user(
        email="seller2@moh-demo.com",
        aliases=[],
        phone="+7 (900) 000-00-04",
        name="Max",
        surname="Vendor",
        status="vendor",
    )

    seller_1 = upsert_vendor(
        user=seller_user_1,
        aliases=[
            "vendor@moh.local",
            "vendor@moh-demo.com",
        ],
        patronymic="Demo",
        title="MOH Store One",
        logo=media["vendor_1"],
    )

    seller_2 = upsert_vendor(
        user=seller_user_2,
        aliases=[],
        patronymic="Demo",
        title="MOH Store Two",
        logo=media["vendor_2"],
    )

    clothes = upsert_category(
        "Одежда"
    )

    hoodies = upsert_category(
        "Худи",
        clothes,
    )

    tshirts = upsert_category(
        "Футболки",
        clothes,
    )

    shoes = upsert_category(
        "Обувь"
    )

    sneakers = upsert_category(
        "Кроссовки",
        shoes,
    )

    accessories = upsert_category(
        "Аксессуары"
    )

    bags = upsert_category(
        "Сумки",
        accessories,
    )

    hoodie = upsert_product(
        title="[DEMO] MOH Hoodie",
        category=hoodies,
        main_image=media["hoodie"],
        extra_images=[
            media["hoodie_extra"],
        ],
        description="Демо-худи MOH.",
    )

    tshirt = upsert_product(
        title="[DEMO] MOH T-Shirt",
        category=tshirts,
        main_image=media["tshirt"],
        extra_images=[
            media["tshirt_extra"],
        ],
        description="Демо-футболка MOH.",
    )

    sneakers_product = (
        upsert_product(
            title="[DEMO] MOH Sneakers",
            category=sneakers,
            main_image=media[
                "sneakers"
            ],
            extra_images=[
                media[
                    "sneakers_extra"
                ],
            ],
            description=(
                "Демо-кроссовки MOH."
            ),
        )
    )

    bag = upsert_product(
        title="[DEMO] MOH Bag",
        category=bags,
        main_image=media["bag"],
        extra_images=[
            media["bag_extra"],
        ],
        description="Демо-сумка MOH.",
    )

    upsert_offer(
        vendor=seller_1,
        product=hoodie,
        price=HOODIE_PRICE,
    )

    upsert_offer(
        vendor=seller_1,
        product=tshirt,
        price=TSHIRT_STORE_ONE_PRICE,
    )

    upsert_offer(
        vendor=seller_2,
        product=tshirt,
        price=TSHIRT_STORE_TWO_PRICE,
    )

    upsert_offer(
        vendor=seller_2,
        product=sneakers_product,
        price=SNEAKERS_PRICE,
    )

    upsert_offer(
        vendor=seller_2,
        product=bag,
        price=BAG_PRICE,
    )

    upsert_trade_request(
        vendor=seller_1,
        product=sneakers_product,
        price=SNEAKERS_REQUEST_PRICE,
        photo=media["request_1"],
    )

    upsert_trade_request(
        vendor=seller_2,
        product=hoodie,
        price=HOODIE_REQUEST_PRICE,
        photo=media["request_2"],
    )

    upsert_suggestion(
        vendor=seller_1,
        title="[DEMO] MOH Cap",
        photo=media["suggest_1"],
    )

    upsert_suggestion(
        vendor=seller_2,
        title="[DEMO] MOH Backpack",
        photo=media["suggest_2"],
    )

    upsert_advertisement(
        media["advertisement"]
    )

    refresh_catalog_products(
        [
            hoodie.id,
            tshirt.id,
            sneakers_product.id,
            bag.id,
        ]
    )

    db.session.commit()

    print()
    print(
        "MOH bootstrap completed."
    )
    print()

    print("Demo accounts:")
    print(
        "  admin@moh-demo.com"
        f" / {DEMO_PASSWORD}"
    )
    print(
        "  client@moh-demo.com"
        f" / {DEMO_PASSWORD}"
    )
    print(
        "  seller1@moh-demo.com"
        f" / {DEMO_PASSWORD}"
    )
    print(
        "  seller2@moh-demo.com"
        f" / {DEMO_PASSWORD}"
    )

    print()
    print("Created/updated:")
    print("  - 1 admin")
    print("  - 1 client")
    print("  - 2 vendors")
    print("  - 4 products")
    print("  - 5 offers")
    print("  - 2 trade requests")
    print("  - 2 product suggestions")
    print("  - 1 advertisement")
    print("  - product thumbnails")
    print()


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        try:
            bootstrap()

        except Exception:
            db.session.rollback()
            raise
