from flask import current_app, render_template, url_for
from flask_mail import Message
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.extensions import mail


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    return serializer.dumps(
        email,
        salt=current_app.config["SECURITY_PASSWORD_SALT"],
    )


def get_email_from_confirmation_token(
        confirmation_token,
        max_age=86400,
):
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    try:
        return serializer.loads(
            confirmation_token,
            salt=current_app.config["SECURITY_PASSWORD_SALT"],
            max_age=max_age,
        )
    except (SignatureExpired, BadSignature):
        return None


def send_confirmation_email(email):
    token = generate_confirmation_token(email)

    confirm_url = url_for(
        "auth.confirm_email",
        confirmation_token=token,
        _external=True,
    )

    message = Message(
        "Подтверждение адреса электронной почты",
        recipients=[email],
        html=render_template(
            "email/confirm.html",
            confirm_url=confirm_url,
        ),
        sender=current_app.config.get("MAIL_USERNAME"),
    )

    mail.send(message)
