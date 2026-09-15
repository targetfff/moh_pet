from flask import (
    abort,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
)

from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import (
    Order,
    OrderItem,
    Payment,
)
from app.services.orders import (
    complete_mock_payment,
    create_order_from_cart,
    fail_mock_payment,
)
from .statuses import (
    order_status_class,
    order_status_label,
)
from . import orders_bp


def _get_user_order_or_404(
        order_id,
):
    order = (
        Order.query
        .options(
            selectinload(
                Order.items
            ),
            selectinload(
                Order.payments
            ),
        )
        .filter(
            Order.id == order_id,
            Order.user_id
            == current_user.id,
            )
        .first()
    )

    if order is None:
        abort(404)

    return order


def _pending_payment(order):
    return (
        Payment.query
        .filter(
            Payment.order_id
            == order.id,
            Payment.status
            == "pending",
            )
        .order_by(
            Payment.id.desc()
        )
        .first()
    )


@orders_bp.post("/checkout")
@login_required
def checkout():
    order = create_order_from_cart(
        current_user
    )

    if order is None:
        flash(
            "Корзина пуста."
        )

        return redirect(
            url_for(
                "catalog.cart"
            )
        )

    return redirect(
        url_for(
            "orders.payment",
            order_id=order.id,
        )
    )


@orders_bp.get(
    "/orders/<int:order_id>/payment"
)
@login_required
def payment(order_id):
    order = _get_user_order_or_404(
        order_id
    )

    payment = _pending_payment(
        order
    )

    if order.status == "paid":
        return redirect(
            url_for(
                "orders.order_detail",
                order_id=order.id,
            )
        )

    return render_template(
        "orders/payment.html",
        order=order,
        payment=payment,
    )


@orders_bp.post(
    "/orders/<int:order_id>/payment/success"
)
@login_required
def payment_success(order_id):
    order = _get_user_order_or_404(
        order_id
    )

    if order.status == "paid":
        return redirect(
            url_for(
                "orders.order_detail",
                order_id=order.id,
            )
        )

    payment = _pending_payment(
        order
    )

    if payment is None:
        abort(409)

    try:
        complete_mock_payment(
            order,
            payment,
        )

    except ValueError:
        db.session.rollback()
        abort(409)

    return redirect(
        url_for(
            "orders.order_detail",
            order_id=order.id,
        )
    )


@orders_bp.post(
    "/orders/<int:order_id>/payment/fail"
)
@login_required
def payment_fail(order_id):
    order = _get_user_order_or_404(
        order_id
    )

    payment = _pending_payment(
        order
    )

    if payment is None:
        abort(409)

    try:
        fail_mock_payment(
            order,
            payment,
        )

    except ValueError:
        db.session.rollback()
        abort(409)

    flash(
        "Оплата не прошла. "
        "Корзина сохранена."
    )

    return redirect(
        url_for(
            "catalog.cart"
        )
    )


@orders_bp.get(
    "/orders/<int:order_id>"
)
@login_required
def order_detail(order_id):
    order = _get_user_order_or_404(
        order_id
    )

    return render_template(
        "orders/order.html",
        order=order,
        status_label=(
            order_status_label(
                order.status
            )
        ),
        status_class=(
            order_status_class(
                order.status
            )
        ),
    )