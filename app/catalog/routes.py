from flask import render_template

from app.models import Products
from . import catalog_bp


@catalog_bp.route('/')
def index():
    return "Catalog blueprint works!"