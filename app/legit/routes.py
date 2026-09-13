from flask import render_template

from . import legit_bp


@legit_bp.route("/legit_check")
def legit_check():
    return render_template("legit/check.html")