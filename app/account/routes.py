from flask import render_template
from flask_login import current_user, login_required

from app.extensions import db
from app.models import (
    Products,
    Requests,
    Suggestions,
    Vendors,
)

from . import account_bp


@account_bp.route("/account")
@login_required
def account():
    # -------------------------------------------------
    # Vendor
    # -------------------------------------------------

    if current_user.status == "vendor":
        vendor = Vendors.query.filter_by(
            email=current_user.email
        ).first()

        products = Products.query.order_by(
            Products.date.desc()
        ).all()

        return render_template(
            "account.html",
            user=current_user,
            data=products,
            vendor=vendor,
        )

    # -------------------------------------------------
    # Admin
    # -------------------------------------------------

    if current_user.status == "admin":
        requests_data = (
            db.session.query(
                Vendors,
                Products,
                Requests,
            )
            .join(
                Vendors,
                Vendors.id == Requests.vendor_id,
                )
            .join(
                Products,
                Products.id == Requests.product_id,
                )
            .order_by(
                Requests.date.desc()
            )
            .all()
        )

        suggestions_data = (
            db.session.query(
                Vendors,
                Suggestions,
            )
            .join(
                Vendors,
                Vendors.id == Suggestions.vendor_id,
                )
            .filter(
                Suggestions.accepted.is_(False)
            )
            .order_by(
                Suggestions.date.desc()
            )
            .all()
        )

        return render_template(
            "account.html",
            user=current_user,
            data=[],
            reqs_data=requests_data,
            sug_data=suggestions_data,
        )

    # -------------------------------------------------
    # Client
    # -------------------------------------------------

    liked = []

    if current_user.cart:
        liked = [
            int(item.split()[0])
            for item in current_user.cart
            .strip(", ")
            .split(", ")
        ]

    recent = []

    if current_user.recent:
        recent_ids = [
            int(product_id)
            for product_id
            in current_user.recent.split()
        ]

        products = Products.query.filter(
            Products.id.in_(recent_ids)
        ).all()

        products_by_id = {
            product.id: product
            for product in products
        }

        # recent хранится от старого к новому,
        # а на странице показываем наоборот.
        recent = [
            products_by_id[product_id]
            for product_id in reversed(
                recent_ids
            )
            if product_id in products_by_id
        ]

    return render_template(
        "account.html",
        user=current_user,
        data=[],
        liked=liked,
        recent=recent,
    )