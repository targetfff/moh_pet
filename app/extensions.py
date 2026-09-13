from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
)
