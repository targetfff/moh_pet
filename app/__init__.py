from flask import Flask

from config import Config

from .extensions import db, login_manager, mail


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config.from_object(Config)

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    from .performance import init_performance_logging
    init_performance_logging(app)

    from .models import Users

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Users, int(user_id))

    from .account import account_bp
    from .auth import auth_bp
    from .catalog import catalog_bp
    from .legit import legit_bp
    from .seller import seller_bp
    from .admin import admin_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(legit_bp)
    app.register_blueprint(seller_bp)

    return app

