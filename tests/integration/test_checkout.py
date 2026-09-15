from decimal import Decimal

from app.extensions import db
from app.models import (
    CartItem,
    Offers,
    Order,
    Payment,
    Products,
    Vendors,
)


PASSWORD = "Correct horse battery 42"


def _login(
    client,
    *,
    email,
    password=PASSWORD,
):
    response = client.post(
        "/login",
        data={
            "email": email,
            "password": password,
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    return response


def _create_cart_item(
    app,
    *,
    user_id,
    quantity=2,
    price=Decimal("3990.00"),
    suffix="1",
):
    with app.app_context():
        product = Products(
            title=f"Checkout Product {suffix}",
            main_logo=f"logo-{suffix}.png",
            main_image=f"image-{suffix}.png",
            price=price,
            description="Checkout test product",
        )

        vendor = Vendors(
            surname="Seller",
            name="Checkout",
            patronymic="Test",
            title=f"Checkout Store {suffix}",
            phone=f"+7 (999) 000-00-{suffix.zfill(2)}",
            email=f"seller-{suffix}@example.com",
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
            "offer_id": offer.id,
            "cart_item_id": cart_item.id,
        }


def test_checkout_requires_authentication(
    client,
):
    response = client.post(
        "/checkout",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/login" in response.headers[
        "Location"
    ]


def test_checkout_creates_pending_order_and_redirects_to_payment(
    app,
    client,
    make_user,
):
    email = "checkout@example.com"

    user_id = make_user(
        email=email,
        password=PASSWORD,
    )

    _create_cart_item(
        app,
        user_id=user_id,
        quantity=2,
    )

    _login(
        client,
        email=email,
    )

    response = client.post(
        "/checkout",
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        order = (
            Order.query
            .filter_by(
                user_id=user_id
            )
            .one()
        )

        payment = (
            Payment.query
            .filter_by(
                order_id=order.id
            )
            .one()
        )

        assert (
            response.headers["Location"]
            .endswith(
                f"/orders/{order.id}/payment"
            )
        )

        assert (
            order.status
            == "pending_payment"
        )
        assert (
            payment.status
            == "pending"
        )
        assert (
            order.total
            == Decimal("11080.00")
        )


def test_successful_checkout_marks_order_paid_and_updates_cart(
    app,
    client,
    make_user,
):
    email = "paid@example.com"

    user_id = make_user(
        email=email,
        password=PASSWORD,
    )

    ids = _create_cart_item(
        app,
        user_id=user_id,
        quantity=2,
    )

    _login(
        client,
        email=email,
    )

    checkout_response = client.post(
        "/checkout",
        follow_redirects=False,
    )

    assert (
        checkout_response.status_code
        == 302
    )

    with app.app_context():
        order = (
            Order.query
            .filter_by(
                user_id=user_id
            )
            .one()
        )
        order_id = order.id

        # Cart changes after order snapshot.
        cart_item = db.session.get(
            CartItem,
            ids["cart_item_id"],
        )
        cart_item.quantity = 3
        db.session.commit()

    payment_response = client.post(
        f"/orders/{order_id}/payment/success",
        follow_redirects=False,
    )

    assert (
        payment_response.status_code
        == 302
    )
    assert (
        payment_response.headers[
            "Location"
        ].endswith(
            f"/orders/{order_id}"
        )
    )

    with app.app_context():
        order = db.session.get(
            Order,
            order_id,
        )

        payment = (
            Payment.query
            .filter_by(
                order_id=order_id
            )
            .one()
        )

        cart_item = (
            CartItem.query
            .filter_by(
                user_id=user_id,
                offer_id=ids["offer_id"],
            )
            .one()
        )

        assert order.status == "paid"
        assert order.paid_at is not None
        assert payment.status == "succeeded"
        assert (
            payment.completed_at
            is not None
        )

        # Order snapshot stays at 2,
        # only the extra cart item remains.
        assert order.items[0].quantity == 2
        assert cart_item.quantity == 1

    # Repeating success for an already
    # paid order must not decrement again.
    duplicate_response = client.post(
        f"/orders/{order_id}/payment/success",
        follow_redirects=False,
    )

    assert (
        duplicate_response.status_code
        == 302
    )

    with app.app_context():
        cart_item = (
            CartItem.query
            .filter_by(
                user_id=user_id,
                offer_id=ids["offer_id"],
            )
            .one()
        )

        assert cart_item.quantity == 1


def test_failed_checkout_keeps_cart(
    app,
    client,
    make_user,
):
    email = "payment-fail@example.com"

    user_id = make_user(
        email=email,
        password=PASSWORD,
    )

    ids = _create_cart_item(
        app,
        user_id=user_id,
        quantity=2,
    )

    _login(
        client,
        email=email,
    )

    client.post(
        "/checkout",
        follow_redirects=False,
    )

    with app.app_context():
        order = (
            Order.query
            .filter_by(
                user_id=user_id
            )
            .one()
        )
        order_id = order.id

    response = client.post(
        f"/orders/{order_id}/payment/fail",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers[
        "Location"
    ].endswith("/cart")

    with app.app_context():
        order = db.session.get(
            Order,
            order_id,
        )

        payment = (
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
            order.status
            == "payment_failed"
        )
        assert (
            payment.status
            == "failed"
        )
        assert cart_item is not None
        assert cart_item.quantity == 2


def test_user_cannot_open_another_users_order(
    app,
    client,
    make_user,
):
    owner_email = "owner@example.com"
    stranger_email = "stranger@example.com"

    owner_id = make_user(
        email=owner_email,
        phone="+7 (999) 111-22-31",
        password=PASSWORD,
    )

    make_user(
        email=stranger_email,
        phone="+7 (999) 111-22-32",
        password=PASSWORD,
    )

    _create_cart_item(
        app,
        user_id=owner_id,
        quantity=1,
    )

    _login(
        client,
        email=owner_email,
    )

    client.post(
        "/checkout",
        follow_redirects=False,
    )

    with app.app_context():
        order = (
            Order.query
            .filter_by(
                user_id=owner_id
            )
            .one()
        )
        order_id = order.id

    client.post(
        "/logout",
        follow_redirects=False,
    )

    _login(
        client,
        email=stranger_email,
    )

    response = client.get(
        f"/orders/{order_id}"
    )

    assert response.status_code == 404


def test_paid_payment_page_redirects_to_order_detail(
    app,
    client,
    make_user,
):
    email = "paid-page@example.com"

    user_id = make_user(
        email=email,
        password=PASSWORD,
    )

    _create_cart_item(
        app,
        user_id=user_id,
        quantity=1,
    )

    _login(
        client,
        email=email,
    )

    client.post(
        "/checkout",
        follow_redirects=False,
    )

    with app.app_context():
        order = (
            Order.query
            .filter_by(
                user_id=user_id
            )
            .one()
        )
        order_id = order.id

    client.post(
        f"/orders/{order_id}/payment/success",
        follow_redirects=False,
    )

    response = client.get(
        f"/orders/{order_id}/payment",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers[
        "Location"
    ].endswith(
        f"/orders/{order_id}"
    )
