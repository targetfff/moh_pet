from flask import (
    Flask,
    redirect,
    request,
    url_for,
)
from flask_login import current_user
from sqlalchemy.orm import joinedload

from config import Config

from .extensions import (
    db,
    migrate,
    csrf,
    limiter,
    login_manager,
    mail,
)


def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config.from_object(Config)

    if test_config:
        app.config.update(
            test_config
        )

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY is not configured."
        )

    if not app.config.get(
        "SECURITY_PASSWORD_SALT"
    ):
        raise RuntimeError(
            "SECURITY_PASSWORD_SALT is not configured."
        )

    db.init_app(app)
    migrate.init_app(app, db)

    mail.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = (
        "Войдите в аккаунт, чтобы продолжить."
    )
    login_manager.session_protection = "strong"

    from .performance import (
        init_performance_logging,
    )

    init_performance_logging(app)

    from .models import Users

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return None

        return (
            Users.query
            .options(
                joinedload(
                    Users.cart_items
                )
            )
            .filter(
                Users.id == user_id
            )
            .first()
        )

    @app.before_request
    def require_confirmed_email():
        if (
            not current_user.is_authenticated
            or current_user.confirmed is True
        ):
            return None

        allowed_endpoints = {
            "auth.confirm_email",
            "auth.logout",
            "auth.resend_confirmation",
            "auth.reset_password",
            "auth.unconfirmed",
            "static",
        }

        if request.endpoint in allowed_endpoints:
            return None

        return redirect(
            url_for("auth.unconfirmed")
        )

    @app.context_processor
    def inject_cart_helpers():
        def get_cart_count():
            if not current_user.is_authenticated:
                return 0

            return len(
                current_user.cart_items
            )

        return {
            "get_cart_count": get_cart_count,
        }

    from .account import account_bp
    from .admin import admin_bp
    from .auth import auth_bp
    from .catalog import catalog_bp
    from .legit import legit_bp
    from .seller import seller_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(legit_bp)
    app.register_blueprint(seller_bp)

    return app
