from flask import render_template
from flask_login import current_user, login_required

from app.extensions import db
from app.models import (
    Favorite,
    Order,
    Products,
    RecentView,
    Requests,
    Suggestions,
    Vendors,
)

from app.orders.statuses import (
    order_status_class,
    order_status_label,
)

from sqlalchemy.orm import selectinload

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
        favorite.product_id
        for favorite in current_user.favorites
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

    recent_orders = (
        Order.query
        .options(
            selectinload(
                Order.items
            )
        )
        .filter(
            Order.user_id
            == current_user.id
        )
        .order_by(
            Order.created_at.desc(),
            Order.id.desc(),
        )
        .limit(3)
        .all()
    )

    favorite_products = (
        Products.query
        .join(
            Favorite,
            Favorite.product_id
            == Products.id,
            )
        .filter(
            Favorite.user_id
            == current_user.id
        )
        .order_by(
            Favorite.created_at.desc(),
            Favorite.id.desc(),
        )
        .limit(4)
        .all()
    )

    return render_template(
        "account/client.html",
        user=current_user,
        data=[],
        liked=liked,
        recent=recent,
        account_tab="overview",
        favorite_products=favorite_products,
        recent_orders=recent_orders,
        order_status_label=order_status_label,
        order_status_class=order_status_class,
    )

@account_bp.get("/account/orders")
@login_required
def orders():
    orders_data = (
        Order.query
        .options(
            selectinload(
                Order.items
            )
        )
        .filter(
            Order.user_id
            == current_user.id
        )
        .order_by(
            Order.created_at.desc(),
            Order.id.desc(),
        )
        .all()
    )

    return render_template(
        "account/orders.html",
        orders=orders_data,
        order_status_label=order_status_label,
        order_status_class=order_status_class,
        account_tab="orders",
    )


@account_bp.get(
    "/notifications"
)
@login_required
def notifications():
    return render_template(
        "account/notifications.html"
    )


@account_bp.get("/account/favorites")
@login_required
def favorites():
    products = (
        Products.query
        .join(
            Favorite,
            Favorite.product_id
            == Products.id,
            )
        .filter(
            Favorite.user_id
            == current_user.id
        )
        .order_by(
            Favorite.created_at.desc(),
            Favorite.id.desc(),
        )
        .all()
    )

    liked = {
        product.id
        for product in products
    }

    return render_template(
        "account/favorites.html",
        products=products,
        liked=liked,
        account_tab="favorites",
    )