import random

from app.extensions import db
from app.models import Offers, Products, Vendors


def refresh_catalog_products():
    products = Products.query.all()

    for product in products:
        offers = Offers.query.filter_by(
            product_id=product.id
        ).all()

        if not offers:
            continue

        best_offer = min(
            offers,
            key=lambda offer: offer.price,
        )

        main_vendor = db.session.get(
            Vendors,
            best_offer.vendor_id,
        )

        if not main_vendor:
            continue

        vendor_ids = list(dict.fromkeys(
            offer.vendor_id
            for offer in offers
        ))

        product.price = best_offer.price
        product.vendor = (
                main_vendor.title
                or main_vendor.name
        )

        if main_vendor.logo:
            product.main_logo = main_vendor.logo

        product.vendors = str(vendor_ids)

        other_vendor_ids = [
            vendor_id
            for vendor_id in vendor_ids
            if vendor_id != main_vendor.id
        ]

        random.shuffle(other_vendor_ids)

        logos = []

        for vendor_id in other_vendor_ids[:4]:
            vendor = db.session.get(
                Vendors,
                vendor_id,
            )

            if vendor and vendor.logo:
                logos.append(vendor.logo)

        product.logos = str(logos)