from flask import Blueprint


legit_bp = Blueprint("legit", __name__)


from . import routes