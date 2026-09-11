import random

from app.extensions import db
from app.models import Offers, Products, Vendors


def _reset_catalog_product(product: Products) -> None:
    """Сбрасывает агрегированные данные товара, если активных офферов нет."""
    product.price = -1
    product.vendor = ""
    product.vendors = "[]"
    product.main_logo = ""
    product.logos = "[]"


def _apply_catalog_rows(product: Products, rows) -> None:
    """
    Обновляет агрегированные поля Products на основе:
    [(Offer, Vendor), ...]
    """
    if not rows:
        _reset_catalog_product(product)
        return

    # Самый дешёвый оффер — основной продавец товара.
    best_offer, main_vendor = min(
        rows,
        key=lambda pair: pair[0].price,
    )

    vendor_ids = list(
        dict.fromkeys(
            offer.vendor_id
            for offer, _vendor in rows
        )
    )

    product.price = best_offer.price
    product.vendor = main_vendor.title or main_vendor.name
    product.main_logo = main_vendor.logo or ""
    product.vendors = str(vendor_ids)

    # Остальные логотипы.
    vendors_by_id = {
        vendor.id: vendor
        for _offer, vendor in rows
    }

    other_vendor_ids = [
        vendor_id
        for vendor_id in vendor_ids
        if vendor_id != main_vendor.id
    ]

    random.shuffle(other_vendor_ids)

    logos = []

    for vendor_id in other_vendor_ids[:4]:
        vendor = vendors_by_id.get(vendor_id)

        if vendor and vendor.logo:
            logos.append(vendor.logo)

    product.logos = str(logos)


def refresh_catalog_product(product: Products) -> None:
    """
    Пересчитывает один конкретный товар.

    Commit здесь специально не делаем:
    транзакцией управляет вызывающий route/service.
    """
    rows = (
        db.session.query(Offers, Vendors)
        .join(
            Vendors,
            Vendors.id == Offers.vendor_id,
            )
        .filter(
            Offers.product_id == product.id,
            )
        .all()
    )

    _apply_catalog_rows(product, rows)


def refresh_catalog_products(product_ids=None) -> None:
    """
    Пересчитывает несколько товаров либо весь каталог.

    product_ids=None -> весь каталог.
    product_ids=[...] -> только указанные товары.
    """
    query = Products.query

    if product_ids is not None:
        product_ids = list(set(product_ids))

        if not product_ids:
            return

        query = query.filter(
            Products.id.in_(product_ids)
        )

    products = query.all()

    if not products:
        return

    ids = [
        product.id
        for product in products
    ]

    rows = (
        db.session.query(Offers, Vendors)
        .join(
            Vendors,
            Vendors.id == Offers.vendor_id,
            )
        .filter(
            Offers.product_id.in_(ids)
        )
        .all()
    )

    rows_by_product = {}

    for offer, vendor in rows:
        rows_by_product.setdefault(
            offer.product_id,
            [],
        ).append(
            (offer, vendor)
        )

    for product in products:
        _apply_catalog_rows(
            product,
            rows_by_product.get(
                product.id,
                [],
            ),
        )


def refresh_vendor_products(vendor_id: int) -> None:
    """
    Пересчитывает только товары, которые продаёт конкретный продавец.

    Используется после изменения title/logo продавца.
    """
    product_ids = (
        db.session.query(Offers.product_id)
        .filter(
            Offers.vendor_id == vendor_id,
            )
        .distinct()
        .all()
    )

    product_ids = [
        product_id
        for (product_id,) in product_ids
    ]

    if not product_ids:
        return

    refresh_catalog_products(product_ids)