from flask import render_template
from flask_login import current_user, login_required

from app.extensions import db
from app.models import (
    Products,
    RecentView,
    Requests,
    Suggestions,
    Vendors,
)

from . import account_bp


@account_bp.route("/account")
@login_required
def account():
    if current_user.status == "vendor":
        vendor = (
            Vendors.query
            .filter_by(
                email=current_user.email
            )
            .first()
        )

        products = (
            Products.query
            .order_by(
                Products.date.desc()
            )
            .all()
        )

        return render_template(
            "account/vendor.html",
            user=current_user,
            data=products,
            vendor=vendor,
        )

    if current_user.status == "admin":
        requests_data = (
            db.session.query(
                Vendors,
                Products,
                Requests,
            )
            .join(
                Vendors,
                Vendors.id
                == Requests.vendor_id,
            )
            .join(
                Products,
                Products.id
                == Requests.product_id,
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
                Vendors.id
                == Suggestions.vendor_id,
            )
            .filter(
                Suggestions.accepted.is_(
                    False
                )
            )
            .order_by(
                Suggestions.date.desc()
            )
            .all()
        )

        return render_template(
            "account/admin.html",
            user=current_user,
            data=[],
            reqs_data=requests_data,
            sug_data=suggestions_data,
        )

    liked = {
        item.product_id
        for item in current_user.cart_items
    }

    recent = (
        db.session.query(
            Products
        )
        .join(
            RecentView,
            RecentView.product_id
            == Products.id,
        )
        .filter(
            RecentView.user_id
            == current_user.id
        )
        .order_by(
            RecentView.viewed_at.desc(),
            RecentView.id.desc(),
        )
        .limit(14)
        .all()
    )

    return render_template(
        "account/client.html",
        user=current_user,
        data=[],
        liked=liked,
        recent=recent,
    )
