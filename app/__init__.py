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

    from .models import Users

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Users, int(user_id))

    from .catalog import catalog_bp

    app.register_blueprint(catalog_bp)

    return app
