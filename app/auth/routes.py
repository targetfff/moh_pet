from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from app.extensions import (
    db,
    limiter,
)
from app.models import Users
from app.services.email import (
    get_email_from_confirmation_token,
    get_password_reset_payload,
    password_reset_payload_matches_user,
    send_confirmation_email,
    send_password_reset_email,
)

from . import auth_bp
from .validation import (
    normalize_email,
    normalize_person_name,
    normalize_phone,
    validate_password,
)


def _find_user_by_email(email):
    return (
        Users.query
        .filter(
            func.lower(
                Users.email
            )
            == email.lower()
        )
        .first()
    )


def _safe_next_url():
    next_page = request.args.get(
        "next"
    )

    if (
        next_page
        and next_page.startswith("/")
        and not next_page.startswith("//")
    ):
        return next_page

    return None


@auth_bp.route(
    "/login",
    methods=["GET", "POST"],
)
@limiter.limit(
    "10 per minute",
    methods=["POST"],
)
def login():
    if current_user.is_authenticated:
        if current_user.confirmed is not True:
            return redirect(
                url_for("auth.unconfirmed")
            )

        return redirect(
            url_for("catalog.index")
        )

    if request.method == "POST":
        raw_email = request.form.get(
            "email",
            "",
        )
        password = request.form.get(
            "password",
            "",
        )
        remember_me = bool(
            request.form.get(
                "remember_me"
            )
        )

        try:
            email = normalize_email(
                raw_email
            )
        except ValueError:
            email = None

        user = (
            _find_user_by_email(email)
            if email
            else None
        )

        credentials_valid = (
            user is not None
            and check_password_hash(
                user.password,
                password,
            )
        )

        if credentials_valid:
            login_user(
                user,
                remember=remember_me,
            )

            if user.confirmed is not True:
                return redirect(
                    url_for(
                        "auth.unconfirmed"
                    )
                )

            next_page = _safe_next_url()

            if next_page:
                return redirect(
                    next_page
                )

            return redirect(
                url_for(
                    "catalog.index"
                )
            )

        flash(
            "Адрес электронной почты "
            "и/или пароль введены неверно."
        )

    return render_template(
        "auth/login.html"
    )


@auth_bp.route(
    "/register",
    methods=["GET", "POST"],
)
@limiter.limit(
    "5 per hour",
    methods=["POST"],
)
def register():
    if current_user.is_authenticated:
        return redirect(
            url_for("catalog.index")
        )

    form_data = {
        "name": "",
        "surname": "",
        "phone": "",
        "email": "",
    }

    if request.method == "POST":
        form_data = {
            "name": request.form.get(
                "name",
                "",
            ),
            "surname": request.form.get(
                "surname",
                "",
            ),
            "phone": request.form.get(
                "phone",
                "",
            ),
            "email": request.form.get(
                "email",
                "",
            ),
        }

        password = request.form.get(
            "password",
            "",
        )
        password2 = request.form.get(
            "password2",
            "",
        )

        try:
            name = normalize_person_name(
                form_data["name"],
                "Имя",
            )
            surname = normalize_person_name(
                form_data["surname"],
                "Фамилия",
            )
            phone = normalize_phone(
                form_data["phone"]
            )
            email = normalize_email(
                form_data["email"]
            )

            if password != password2:
                raise ValueError(
                    "Пароли не совпадают."
                )

            validate_password(
                password,
                email=email,
                phone=phone,
                name=name,
                surname=surname,
            )

        except ValueError as exc:
            flash(str(exc))

            return render_template(
                "auth/register.html",
                form_data=form_data,
            )

        if _find_user_by_email(email):
            flash(
                "Пользователь с таким адресом "
                "электронной почты уже зарегистрирован."
            )

            return render_template(
                "auth/register.html",
                form_data=form_data,
            )

        if Users.query.filter_by(
            phone=phone
        ).first():
            flash(
                "Пользователь с таким номером "
                "телефона уже зарегистрирован."
            )

            return render_template(
                "auth/register.html",
                form_data=form_data,
            )

        user = Users(
            phone=phone,
            email=email,
            password=generate_password_hash(
                password
            ),
            surname=surname,
            name=name,
            status="client",
            confirmed=False,
        )

        try:
            db.session.add(user)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()

            flash(
                "Не удалось зарегистрировать "
                "аккаунт. Проверьте введённые данные."
            )

            return render_template(
                "auth/register.html",
                form_data=form_data,
            )

        try:
            send_confirmation_email(
                user.email
            )

            flash(
                "Аккаунт создан. Мы отправили "
                "ссылку подтверждения на вашу почту."
            )

        except Exception:
            current_app.logger.exception(
                "Failed to send confirmation "
                "email for user_id=%s",
                user.id,
            )

            flash(
                "Аккаунт создан, но письмо "
                "подтверждения отправить не удалось. "
                "Войдите в аккаунт и запросите "
                "письмо повторно."
            )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/register.html",
        form_data=form_data,
    )


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()

    return redirect(
        url_for("catalog.index")
    )


@auth_bp.post(
    "/resend-confirmation"
)
@login_required
@limiter.limit("1 per minute")
@limiter.limit("3 per hour")
def resend_confirmation():
    if current_user.confirmed is True:
        return redirect(
            url_for("catalog.index")
        )

    try:
        send_confirmation_email(
            current_user.email
        )

        flash(
            "Новое письмо с подтверждением "
            "отправлено на вашу электронную почту."
        )

    except Exception:
        current_app.logger.exception(
            "Failed to resend confirmation "
            "email for user_id=%s",
            current_user.id,
        )

        flash(
            "Не удалось отправить письмо. "
            "Попробуйте ещё раз позже."
        )

    return redirect(
        url_for("auth.unconfirmed")
    )


@auth_bp.route(
    "/confirm/<confirmation_token>"
)
def confirm_email(
    confirmation_token,
):
    email = (
        get_email_from_confirmation_token(
            confirmation_token
        )
    )

    if email is None:
        return render_template(
            "auth/invalid_token.html"
        ), 400

    user = _find_user_by_email(
        email
    )

    if user is None:
        return render_template(
            "auth/invalid_token.html"
        ), 400

    if user.confirmed is True:
        flash(
            "Адрес электронной почты "
            "уже подтверждён."
        )

        return redirect(
            url_for("catalog.index")
        )

    user.confirmed = True
    db.session.commit()

    flash(
        "Адрес электронной почты подтверждён."
    )

    if (
        current_user.is_authenticated
        and current_user.id == user.id
    ):
        return redirect(
            url_for("catalog.index")
        )

    return redirect(
        url_for("auth.login")
    )


@auth_bp.route(
    "/unconfirmed"
)
def unconfirmed():
    if current_user.is_anonymous:
        return redirect(
            url_for("auth.login")
        )

    if current_user.confirmed is True:
        return redirect(
            url_for("catalog.index")
        )

    return render_template(
        "auth/unconfirmed.html"
    )


@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"],
)
@limiter.limit(
    "5 per hour",
    methods=["POST"],
)
def forgot_password():
    if request.method == "POST":
        raw_email = request.form.get(
            "email",
            "",
        )

        try:
            email = normalize_email(
                raw_email
            )
        except ValueError:
            email = None

        user = (
            _find_user_by_email(email)
            if email
            else None
        )

        if user is not None:
            try:
                send_password_reset_email(
                    user
                )

            except Exception:
                current_app.logger.exception(
                    "Failed to send password "
                    "reset email for user_id=%s",
                    user.id,
                )

        flash(
            "Если аккаунт с таким адресом "
            "существует, мы отправили письмо "
            "для восстановления пароля."
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/forgot_password.html"
    )


@auth_bp.route(
    "/reset-password/<reset_token>",
    methods=["GET", "POST"],
)
@limiter.limit(
    "10 per hour",
    methods=["POST"],
)
def reset_password(
    reset_token,
):
    payload = (
        get_password_reset_payload(
            reset_token
        )
    )

    if payload is None:
        return render_template(
            "auth/invalid_token.html"
        ), 400

    try:
        user_id = int(
            payload["user_id"]
        )
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        return render_template(
            "auth/invalid_token.html"
        ), 400

    user = db.session.get(
        Users,
        user_id,
    )

    if not (
        user
        and password_reset_payload_matches_user(
            payload,
            user,
        )
    ):
        return render_template(
            "auth/invalid_token.html"
        ), 400

    if request.method == "POST":
        password = request.form.get(
            "password",
            "",
        )
        password2 = request.form.get(
            "password2",
            "",
        )

        try:
            if password != password2:
                raise ValueError(
                    "Пароли не совпадают."
                )

            validate_password(
                password,
                email=user.email,
                phone=user.phone,
                name=user.name,
                surname=user.surname,
            )

        except ValueError as exc:
            flash(str(exc))

            return render_template(
                "auth/reset_password.html",
                reset_token=reset_token,
            )

        user.password = (
            generate_password_hash(
                password
            )
        )

        db.session.commit()

        if (
            current_user.is_authenticated
            and current_user.id == user.id
        ):
            logout_user()

        flash(
            "Пароль изменён. "
            "Теперь можно войти."
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/reset_password.html",
        reset_token=reset_token,
    )
