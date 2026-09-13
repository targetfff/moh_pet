from werkzeug.security import (
    check_password_hash,
)

from app.extensions import db
from app.models import Users
from app.services.email import (
    generate_password_reset_token,
)


def test_register_creates_unconfirmed_user(
    app,
    client,
):
    response = client.post(
        "/register",
        data={
            "name": "Иван",
            "surname": "Иванов",
            "phone": "8 999 222 33 44",
            "email": "USER@Example.COM",
            "password":
                "Long safe passphrase 42",
            "password2":
                "Long safe passphrase 42",
        },
    )

    assert response.status_code == 302
    assert response.headers[
        "Location"
    ].endswith("/login")

    with app.app_context():
        user = Users.query.one()

        assert user.email == (
            "user@example.com"
        )
        assert user.phone == (
            "+7 (999) 222-33-44"
        )
        assert user.confirmed is False


def test_register_rejects_short_password(
    app,
    client,
):
    response = client.post(
        "/register",
        data={
            "name": "Иван",
            "surname": "Иванов",
            "phone":
                "+7 (999) 222-33-44",
            "email":
                "user@example.com",
            "password": "123",
            "password2": "123",
        },
    )

    assert response.status_code == 200
    assert (
        "не менее 6"
        in response.get_data(
            as_text=True
        )
    )

    with app.app_context():
        assert Users.query.count() == 0


def test_login_normalizes_email(
    client,
    make_user,
):
    make_user(
        email="user@example.com",
        password="Correct horse battery 42",
        confirmed=True,
    )

    response = client.post(
        "/login",
        data={
            "email":
                "  USER@EXAMPLE.COM ",
            "password":
                "Correct horse battery 42",
        },
    )

    assert response.status_code == 302
    assert response.headers[
        "Location"
    ].endswith("/")


def test_unconfirmed_login_is_restricted(
    client,
    make_user,
):
    make_user(
        confirmed=False,
        password="Correct horse battery 42",
    )

    response = client.post(
        "/login",
        data={
            "email":
                "user@example.com",
            "password":
                "Correct horse battery 42",
        },
    )

    assert response.status_code == 302
    assert response.headers[
        "Location"
    ].endswith("/unconfirmed")

    protected = client.get(
        "/account"
    )

    assert protected.status_code == 302
    assert protected.headers[
        "Location"
    ].endswith("/unconfirmed")


def test_forgot_password_does_not_enumerate(
    client,
):
    response = client.post(
        "/forgot-password",
        data={
            "email":
                "missing@example.com",
        },
        follow_redirects=True,
    )

    text = response.get_data(
        as_text=True
    )

    assert response.status_code == 200
    assert (
        "Если аккаунт с таким адресом"
        in text
    )


def test_password_reset_changes_password_and_invalidates_token(
    app,
    client,
    make_user,
):
    user_id = make_user(
        password="Old secure password 42",
        confirmed=True,
    )

    with app.app_context():
        user = db.session.get(
            Users,
            user_id,
        )

        token = (
            generate_password_reset_token(
                user
            )
        )

    response = client.post(
        f"/reset-password/{token}",
        data={
            "password":
                "New secure password 84",
            "password2":
                "New secure password 84",
        },
    )

    assert response.status_code == 302
    assert response.headers[
        "Location"
    ].endswith("/login")

    with app.app_context():
        user = db.session.get(
            Users,
            user_id,
        )

        assert check_password_hash(
            user.password,
            "New secure password 84",
        )

    stale_token_response = client.get(
        f"/reset-password/{token}"
    )

    assert (
        stale_token_response.status_code
        == 400
    )


def test_reset_rejects_identity_password(
    app,
    client,
    make_user,
):
    user_id = make_user(
        email="person@example.com",
        confirmed=True,
    )

    with app.app_context():
        user = db.session.get(
            Users,
            user_id,
        )

        token = (
            generate_password_reset_token(
                user
            )
        )

    response = client.post(
        f"/reset-password/{token}",
        data={
            "password":
                "person",
            "password2":
                "person",
        },
    )

    assert response.status_code == 200

    text = response.get_data(
        as_text=True
    )

    assert (
        "не менее 6"
        in text
        or "персональными данными"
        in text
    )
