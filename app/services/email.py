from concurrent.futures import ThreadPoolExecutor
import hashlib
import uuid

from flask import (
    current_app,
    render_template,
    url_for,
)
from flask_mail import Message
from itsdangerous import (
    BadSignature,
    SignatureExpired,
    URLSafeTimedSerializer,
)

from app.extensions import mail


_email_executor = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="moh-mail",
)


def _send_message_in_background(
        app,
        message,
        mail_id,
):
    with app.app_context():
        app.logger.info(
            "[MAIL] id=%s status=SENDING recipient=%s",
            mail_id,
            message.recipients,
        )

        try:
            mail.send(message)

        except Exception:
            app.logger.exception(
                "[MAIL] id=%s status=SMTP_FAILED recipient=%s",
                mail_id,
                message.recipients,
            )

        else:
            app.logger.info(
                "[MAIL] id=%s status=SMTP_ACCEPTED recipient=%s",
                mail_id,
                message.recipients,
            )


def _send_message(message):
    app = current_app._get_current_object()

    mail_id = uuid.uuid4().hex[:12]

    app.logger.info(
        "[MAIL] id=%s status=QUEUED recipient=%s subject=%s",
        mail_id,
        message.recipients,
        message.subject,
    )

    if (
            app.testing
            or app.config.get("MAIL_SUPPRESS_SEND")
    ):
        mail.send(message)

        app.logger.info(
            "[MAIL] id=%s status=SMTP_ACCEPTED recipient=%s",
            mail_id,
            message.recipients,
        )

        return

    _email_executor.submit(
        _send_message_in_background,
        app,
        message,
        mail_id,
    )


def _serializer():
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )


# ----------------------------------------------------------------------
# Email confirmation tokens
# ----------------------------------------------------------------------


def generate_confirmation_token(email):
    return _serializer().dumps(
        email,
        salt=current_app.config[
            "SECURITY_PASSWORD_SALT"
        ],
    )


def get_email_from_confirmation_token(
        confirmation_token,
        max_age=None,
):
    if max_age is None:
        max_age = current_app.config[
            "EMAIL_CONFIRMATION_MAX_AGE"
        ]

    try:
        return _serializer().loads(
            confirmation_token,
            salt=current_app.config[
                "SECURITY_PASSWORD_SALT"
            ],
            max_age=max_age,
        )

    except (
            SignatureExpired,
            BadSignature,
    ):
        return None


# ----------------------------------------------------------------------
# Password reset tokens
# ----------------------------------------------------------------------


def _password_fingerprint(
        password_hash,
):
    return hashlib.sha256(
        password_hash.encode("utf-8")
    ).hexdigest()


def generate_password_reset_token(user):
    payload = {
        "user_id": user.id,
        "password_fingerprint":
            _password_fingerprint(
                user.password
            ),
    }

    return _serializer().dumps(
        payload,
        salt=current_app.config[
            "SECURITY_PASSWORD_RESET_SALT"
        ],
    )


def get_password_reset_payload(
        reset_token,
        max_age=None,
):
    if max_age is None:
        max_age = current_app.config[
            "PASSWORD_RESET_MAX_AGE"
        ]

    try:
        payload = _serializer().loads(
            reset_token,
            salt=current_app.config[
                "SECURITY_PASSWORD_RESET_SALT"
            ],
            max_age=max_age,
        )

    except (
            SignatureExpired,
            BadSignature,
    ):
        return None

    if not isinstance(payload, dict):
        return None

    if (
            "user_id" not in payload
            or "password_fingerprint"
            not in payload
    ):
        return None

    return payload


def password_reset_payload_matches_user(
        payload,
        user,
):
    if not payload or not user:
        return False

    try:
        payload_user_id = int(
            payload["user_id"]
        )

    except (
            KeyError,
            TypeError,
            ValueError,
    ):
        return False

    if payload_user_id != user.id:
        return False

    expected = _password_fingerprint(
        user.password
    )

    return (
            payload.get(
                "password_fingerprint"
            )
            == expected
    )


# ----------------------------------------------------------------------
# Emails
# ----------------------------------------------------------------------


def send_confirmation_email(email):
    token = generate_confirmation_token(
        email
    )

    confirm_url = url_for(
        "auth.confirm_email",
        confirmation_token=token,
        _external=True,
    )

    message = Message(
        subject=(
            "Подтверждение электронной "
            "почты — MOH"
        ),
        sender=(
            "MOH",
            current_app.config[
                "MAIL_DEFAULT_SENDER"
            ],
        ),
        recipients=[email],
    )

    message.body = (
        "Подтверждение регистрации в MOH\n\n"
        "Вы получили это письмо, потому что "
        "зарегистрировались в MOH.\n\n"
        "Для подтверждения электронной почты "
        "перейдите по ссылке:\n"
        f"{confirm_url}\n\n"
        "Если вы не регистрировались в MOH, "
        "просто проигнорируйте это письмо."
    )

    message.html = render_template(
        "email/confirm.html",
        confirm_url=confirm_url,
    )

    _send_message(message)


def send_password_reset_email(user):
    token = generate_password_reset_token(
        user
    )

    reset_url = url_for(
        "auth.reset_password",
        reset_token=token,
        _external=True,
    )

    message = Message(
        subject="Восстановление пароля — MOH",
        sender=(
            "MOH",
            current_app.config[
                "MAIL_DEFAULT_SENDER"
            ],
        ),
        recipients=[user.email],
    )

    message.body = (
        "Восстановление пароля MOH\n\n"
        "Для установки нового пароля "
        "перейдите по ссылке:\n"
        f"{reset_url}\n\n"
        "Если вы не запрашивали сброс "
        "пароля, просто проигнорируйте "
        "это письмо."
    )

    message.html = render_template(
        "email/reset_password.html",
        reset_url=reset_url,
    )

    _send_message(message)