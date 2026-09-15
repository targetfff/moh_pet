from decimal import Decimal

from app.extensions import db
from app.models import (
    CartItem,
    Offers,
    Order,
    Payment,
    Products,
    Users,
    Vendors,
)
from app.services.orders import (
    complete_mock_payment,
    create_order_from_cart,
    fail_mock_payment,
)


def _create_cart_item(
    app,
    *,
    user_id,
    quantity=2,
    price=Decimal("3990.00"),
    product_title="Test T-Shirt",
    vendor_title="Test Store",
):
    with app.app_context():
        product = Products(
            title=product_title,
            main_logo="test-logo.png",
            main_image="test-image.png",
            price=price,
            description="Test product",
        )

        vendor = Vendors(
            surname="Seller",
            name="Test",
            patronymic="User",
            title=vendor_title,
            phone="+7 (999) 000-00-01",
            email="seller@example.com",
        )

        db.session.add_all([
            product,
            vendor,
        ])
        db.session.flush()

        offer = Offers(
            vendor_id=vendor.id,
            product_id=product.id,
            price=price,
        )
        db.session.add(offer)
        db.session.flush()

        cart_item = CartItem(
            user_id=user_id,
            offer_id=offer.id,
            quantity=quantity,
        )
        db.session.add(cart_item)
        db.session.commit()

        return {
            "product_id": product.id,
            "vendor_id": vendor.id,
            "offer_id": offer.id,
            "cart_item_id": cart_item.id,
        }


def test_create_order_from_cart_creates_snapshot_and_payment(
    app,
    make_user,
):
    user_id = make_user(
        email="buyer@example.com",
    )

    ids = _create_cart_item(
        app,
        user_id=user_id,
        quantity=2,
        price=Decimal("3990.00"),
    )

    with app.app_context():
        user = db.session.get(
            Users,
            user_id,
        )

        order = create_order_from_cart(
            user
        )

        assert order is not None
        assert order.status == (
            "pending_payment"
        )
        assert order.user_id == user_id

        assert order.subtotal == (
            Decimal("7980.00")
        )
        assert order.legit_fee_total == (
            Decimal("3100.00")
        )
        assert order.total == (
            Decimal("11080.00")
        )

        assert len(order.items) == 1

        item = order.items[0]

        assert item.offer_id == (
            ids["offer_id"]
        )
        assert item.product_id == (
            ids["product_id"]
        )
        assert item.vendor_id == (
            ids["vendor_id"]
        )
        assert item.product_title == (
            "Test T-Shirt"
        )
        assert item.vendor_title == (
            "Test Store"
        )
        assert item.unit_price == (
            Decimal("3990.00")
        )
        assert item.quantity == 2
        assert item.legit_fee == (
            Decimal("3100.00")
        )
        assert item.line_total == (
            Decimal("11080.00")
        )

        payment = (
            Payment.query
            .filter_by(
                order_id=order.id
            )
            .one()
        )

        assert payment.provider == "mock"
        assert payment.status == "pending"
        assert payment.amount == (
            Decimal("11080.00")
        )
        assert payment.external_id

        cart_item = db.session.get(
            CartItem,
            ids["cart_item_id"],
        )

        # Checkout creates a snapshot,
        # but does not touch the cart yet.
        assert cart_item is not None
        assert cart_item.quantity == 2


def test_create_order_from_empty_cart_returns_none(
    app,
    make_user,
):
    user_id = make_user(
        email="empty@example.com",
    )

    with app.app_context():
        user = db.session.get(
            Users,
            user_id,
        )

        order = create_order_from_cart(
            user
        )

        assert order is None
        assert (
            Order.query
            .filter_by(user_id=user_id)
            .count()
            == 0
        )
        assert Payment.query.count() == 0


def test_successful_payment_removes_only_ordered_quantity(
    app,
    make_user,
):
    user_id = make_user(
        email="success@example.com",
    )

    ids = _create_cart_item(
        app,
        user_id=user_id,
        quantity=2,
    )

    with app.app_context():
        user = db.session.get(
            Users,
            user_id,
        )

        order = create_order_from_cart(
            user
        )

        order_id = order.id

        # User changes the cart after checkout:
        # order snapshot must still contain 2,
        # while cart now contains 3.
        cart_item = db.session.get(
            CartItem,
            ids["cart_item_id"],
        )
        cart_item.quantity = 3
        db.session.commit()

        payment = (
            Payment.query
            .filter_by(
                order_id=order_id,
                status="pending",
            )
            .one()
        )

        complete_mock_payment(
            order,
            payment,
        )

        db.session.expire_all()

        saved_order = db.session.get(
            Order,
            order_id,
        )
        saved_payment = (
            Payment.query
            .filter_by(
                order_id=order_id
            )
            .one()
        )
        remaining_cart_item = (
            CartItem.query
            .filter_by(
                user_id=user_id,
                offer_id=ids["offer_id"],
            )
            .one()
        )

        assert saved_order.status == "paid"
        assert saved_order.paid_at is not None

        assert (
            saved_payment.status
            == "succeeded"
        )
        assert (
            saved_payment.completed_at
            is not None
        )

        assert saved_order.items[0].quantity == 2
        assert remaining_cart_item.quantity == 1


def test_successful_payment_removes_cart_row_when_fully_purchased(
    app,
    make_user,
):
    user_id = make_user(
        email="full@example.com",
    )

    ids = _create_cart_item(
        app,
        user_id=user_id,
        quantity=2,
    )

    with app.app_context():
        user = db.session.get(
            Users,
            user_id,
        )

        order = create_order_from_cart(
            user
        )

        payment = (
            Payment.query
            .filter_by(
                order_id=order.id,
                status="pending",
            )
            .one()
        )

        complete_mock_payment(
            order,
            payment,
        )

        remaining = (
            CartItem.query
            .filter_by(
                user_id=user_id,
                offer_id=ids["offer_id"],
            )
            .first()
        )

        assert remaining is None


def test_failed_payment_keeps_cart_unchanged(
    app,
    make_user,
):
    user_id = make_user(
        email="failed@example.com",
    )

    ids = _create_cart_item(
        app,
        user_id=user_id,
        quantity=2,
    )

    with app.app_context():
        user = db.session.get(
            Users,
            user_id,
        )

        order = create_order_from_cart(
            user
        )
        order_id = order.id

        payment = (
            Payment.query
            .filter_by(
                order_id=order_id,
                status="pending",
            )
            .one()
        )

        fail_mock_payment(
            order,
            payment,
        )

        db.session.expire_all()

        saved_order = db.session.get(
            Order,
            order_id,
        )
        saved_payment = (
            Payment.query
            .filter_by(
                order_id=order_id
            )
            .one()
        )
        cart_item = db.session.get(
            CartItem,
            ids["cart_item_id"],
        )

        assert (
            saved_order.status
            == "payment_failed"
        )
        assert (
            saved_payment.status
            == "failed"
        )
        assert (
            saved_payment.completed_at
            is not None
        )

        assert cart_item is not None
        assert cart_item.quantity == 2
