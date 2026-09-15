from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import (
    CartItem,
    Offers,
    Order,
    OrderItem,
    Payment,
)


LEGIT_CHECK_FEE = Decimal("3100.00")
MONEY_ZERO = Decimal("0.00")


def create_order_from_cart(user):
    cart_items = (
        CartItem.query
        .options(
            joinedload(
                CartItem.offer
            ).joinedload(
                Offers.product
            ),
            joinedload(
                CartItem.offer
            ).joinedload(
                Offers.vendor
            ),
        )
        .filter(
            CartItem.user_id
            == user.id
        )
        .order_by(
            CartItem.id.asc()
        )
        .all()
    )

    if not cart_items:
        return None

    subtotal = MONEY_ZERO
    legit_fee_total = MONEY_ZERO

    snapshots = []

    for cart_item in cart_items:
        offer = cart_item.offer

        if offer is None:
            continue

        product = offer.product
        vendor = offer.vendor

        if (
                product is None
                or vendor is None
        ):
            continue

        quantity = max(
            1,
            cart_item.quantity,
        )

        unit_price = (
            offer.price
        ).quantize(
            Decimal("0.01")
        )

        item_subtotal = (
                unit_price
                * quantity
        )

        legit_fee = LEGIT_CHECK_FEE

        line_total = (
                item_subtotal
                + legit_fee
        ).quantize(
            Decimal("0.01")
        )

        subtotal += item_subtotal
        legit_fee_total += legit_fee

        vendor_title = (
                vendor.title
                or (
                    f"{vendor.name} "
                    f"{vendor.surname}"
                ).strip()
        )

        snapshots.append(
            {
                "offer_id":
                    offer.id,
                "product_id":
                    product.id,
                "vendor_id":
                    vendor.id,
                "product_title":
                    product.title,
                "vendor_title":
                    vendor_title,
                "unit_price":
                    unit_price,
                "quantity":
                    quantity,
                "legit_fee":
                    legit_fee,
                "line_total":
                    line_total,
            }
        )

    if not snapshots:
        return None

    subtotal = subtotal.quantize(
        Decimal("0.01")
    )

    legit_fee_total = (
        legit_fee_total.quantize(
            Decimal("0.01")
        )
    )

    total = (
            subtotal
            + legit_fee_total
    ).quantize(
        Decimal("0.01")
    )

    customer_name = (
        f"{user.name} "
        f"{user.surname}"
    ).strip()

    order = Order(
        user_id=user.id,
        status="pending_payment",
        customer_email=user.email,
        customer_name=customer_name,
        subtotal=subtotal,
        legit_fee_total=legit_fee_total,
        total=total,
        created_at=datetime.now(),
    )

    db.session.add(order)
    db.session.flush()

    for snapshot in snapshots:
        db.session.add(
            OrderItem(
                order_id=order.id,
                **snapshot,
            )
        )

    payment = Payment(
        order_id=order.id,
        provider="mock",
        status="pending",
        amount=total,
        created_at=datetime.now(),
    )

    db.session.add(payment)
    db.session.commit()

    return order


def complete_mock_payment(
        order,
        payment,
):
    if order.status == "paid":
        return

    if payment.status != "pending":
        raise ValueError(
            "Payment is not pending."
        )

    now = datetime.now()

    payment.status = "succeeded"
    payment.completed_at = now

    order.status = "paid"
    order.paid_at = now

    order_items = (
        OrderItem.query
        .filter(
            OrderItem.order_id
            == order.id
        )
        .all()
    )

    for order_item in order_items:
        if order_item.offer_id is None:
            continue

        cart_item = (
            CartItem.query
            .filter_by(
                user_id=order.user_id,
                offer_id=order_item.offer_id,
            )
            .first()
        )

        if cart_item is None:
            continue

        if (
                cart_item.quantity
                <= order_item.quantity
        ):
            db.session.delete(
                cart_item
            )

        else:
            cart_item.quantity -= (
                order_item.quantity
            )

    db.session.commit()


def fail_mock_payment(
        order,
        payment,
):
    if payment.status != "pending":
        raise ValueError(
            "Payment is not pending."
        )

    payment.status = "failed"
    payment.completed_at = (
        datetime.now()
    )

    order.status = "payment_failed"

    db.session.commit()