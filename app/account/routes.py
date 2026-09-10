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
    products = Products.query.order_by(
        Products.date.desc()
    ).all()

    if current_user.status == "vendor":
        vendor = Vendors.query.filter_by(
            email=current_user.email
        ).first()

        return render_template(
            "account.html",
            user=current_user,
            data=products,
            vendor=vendor,
        )

    if current_user.status == "admin":
        requests = Requests.query.order_by(
            Requests.date.desc()
        ).all()

        requests_data = []

        for trade_request in requests:
            vendor = db.session.get(
                Vendors,
                trade_request.vendor_id,
            )

            product = db.session.get(
                Products,
                trade_request.product_id,
            )

            if vendor and product:
                requests_data.append(
                    [
                        vendor,
                        product,
                        trade_request,
                    ]
                )

        suggestions = (
            Suggestions.query
            .filter(
                Suggestions.accepted.is_(False)
            )
            .order_by(
                Suggestions.date.desc()
            )
            .all()
        )

        suggestions_data = []

        for suggestion in suggestions:
            vendor = db.session.get(
                Vendors,
                suggestion.vendor_id,
            )

            if vendor:
                suggestions_data.append(
                    [
                        vendor,
                        suggestion,
                    ]
                )

        return render_template(
            "account.html",
            user=current_user,
            data=products,
            reqs_data=requests_data,
            sug_data=suggestions_data,
        )

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
        for product_id in current_user.recent.split():
            product = db.session.get(
                Products,
                int(product_id),
            )

            if product:
                recent.append(product)

    return render_template(
        "account.html",
        user=current_user,
        data=products,
        liked=liked,
        recent=recent[::-1],
    )