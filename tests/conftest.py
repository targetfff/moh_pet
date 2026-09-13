import pytest
from werkzeug.security import (
    generate_password_hash,
)

from app import create_app
from app.extensions import db
from app.models import Users


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "SECURITY_PASSWORD_SALT":
                "test-confirmation-salt",
            "SECURITY_PASSWORD_RESET_SALT":
                "test-reset-salt",
            "SQLALCHEMY_DATABASE_URI":
                "sqlite://",
            "MAIL_SUPPRESS_SEND": True,
            "MAIL_USERNAME":
                "noreply@example.com",
            "RATELIMIT_ENABLED": False,
            "PERFORMANCE_LOGGING": False,
        }
    )

    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def make_user(app):
    def factory(
        *,
        email="user@example.com",
        phone="+7 (999) 111-22-33",
        password="Correct horse battery 42",
        confirmed=True,
        name="Иван",
        surname="Иванов",
        status="client",
    ):
        user = Users(
            phone=phone,
            email=email,
            password=generate_password_hash(
                password
            ),
            name=name,
            surname=surname,
            status=status,
            confirmed=confirmed,
        )

        with app.app_context():
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        return user_id

    return factory
