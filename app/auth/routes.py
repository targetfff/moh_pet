from email_validator import EmailNotValidError, validate_email
from flask import flash, redirect, render_template, request, url_for
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import Users
from app.services.email import (
    get_email_from_confirmation_token,
    send_confirmation_email,
)

from . import auth_bp


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("catalog.index"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember_me = request.form.get("remember_me")

        user = Users.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(
                user,
                remember=bool(remember_me),
            )

            next_page = request.args.get("next")

            if (
                    next_page
                    and next_page.startswith("/")
                    and not next_page.startswith("//")
            ):
                return redirect(next_page)

            return redirect(url_for("catalog.index"))

        flash(
            "Адрес электронной почты и/или пароль "
            "введены неверно"
        )

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("catalog.index"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        password2 = request.form.get("password2")
        name = request.form.get("name")
        surname = request.form.get("surname")
        phone = request.form.get("phone")

        try:
            email_info = validate_email(
                email,
                check_deliverability=False,
            )
            email = email_info.normalized
        except EmailNotValidError:
            flash("Некорректный адрес электронной почты")
            return render_template("register.html")

        if password != password2:
            flash("Пароли не совпадают")

        elif Users.query.filter_by(email=email).first():
            flash(
                "Пользователь с таким адресом "
                "электронной почты уже зарегистрирован"
            )

        elif Users.query.filter_by(phone=phone).first():
            flash(
                "Пользователь с таким номером телефона "
                "уже зарегистрирован"
            )

        else:
            user = Users(
                phone=phone,
                email=email,
                password=generate_password_hash(password),
                surname=surname,
                name=name,
                status="client",
                confirmed=False,
            )

            db.session.add(user)
            db.session.commit()

            return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("catalog.index"))


@auth_bp.route("/resend-confirmation")
@login_required
def resend_confirmation():
    if current_user.confirmed:
        return redirect(url_for("catalog.index"))

    send_confirmation_email(current_user.email)

    flash(
        "Новое письмо с подтверждением "
        "отправлено на вашу электронную почту."
    )

    return redirect(url_for("auth.unconfirmed"))


@auth_bp.route("/confirm/<confirmation_token>")
def confirm_email(confirmation_token):
    email = get_email_from_confirmation_token(
        confirmation_token
    )

    if email is None:
        return render_template(
            "invalid_token.html"
        ), 400

    user = Users.query.filter_by(
        email=email
    ).first_or_404()

    if user.confirmed:
        flash(
            "Адрес электронной почты уже подтвержден."
        )
        return redirect(url_for("catalog.index"))

    user.confirmed = True
    db.session.commit()

    flash(
        "Адрес электронной почты подтвержден."
    )

    return redirect(url_for("auth.login"))


@auth_bp.route("/unconfirmed")
def unconfirmed():
    if current_user.is_anonymous:
        return redirect(url_for("auth.login"))

    if current_user.confirmed:
        return redirect(url_for("catalog.index"))

    return render_template("unconfirmed.html")
