import os

from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = "sqlite:///shop.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECURITY_PASSWORD_SALT = os.getenv(
        "SECURITY_PASSWORD_SALT"
    )

    SECURITY_PASSWORD_RESET_SALT = os.getenv(
        "SECURITY_PASSWORD_RESET_SALT",
        "moh-password-reset-v1",
    )

    PASSWORD_RESET_MAX_AGE = int(
        os.getenv(
            "PASSWORD_RESET_MAX_AGE",
            3600,
        )
    )

    EMAIL_CONFIRMATION_MAX_AGE = int(
        os.getenv(
            "EMAIL_CONFIRMATION_MAX_AGE",
            86400,
        )
    )

    UPLOAD_FOLDER = "static/img"

    MAIL_SERVER = os.getenv(
        "MAIL_SERVER",
        "smtp.gmail.com",
    )
    MAIL_PORT = int(
        os.getenv(
            "MAIL_PORT",
            587,
        )
    )
    MAIL_USE_TLS = (
            os.getenv(
                "MAIL_USE_TLS",
                "false",
            ).lower()
            == "true"
    )
    MAIL_USE_SSL = (
        os.getenv(
            "MAIL_USE_SSL",
            "true",
        ).lower()
        == "true"
    )
    MAIL_USERNAME = os.getenv(
        "MAIL_USERNAME"
    )
    MAIL_PASSWORD = os.getenv(
        "MAIL_PASSWORD"
    )
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER",
        MAIL_USERNAME,
    )

    RATELIMIT_STORAGE_URI = os.getenv(
        "RATELIMIT_STORAGE_URI",
        "memory://",
    )
    RATELIMIT_HEADERS_ENABLED = True

    AD_INTERVAL_SECONDS = int(
        os.getenv(
            "AD_INTERVAL_SECONDS",
            1800,
        )
    )

    PERFORMANCE_LOGGING = (
        os.getenv(
            "PERFORMANCE_LOGGING",
            "false",
        ).lower()
        == "true"
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    SESSION_COOKIE_SECURE = (
        os.getenv(
            "COOKIE_SECURE",
            "false",
        ).lower()
        == "true"
    )

    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    REMEMBER_COOKIE_SECURE = (
        SESSION_COOKIE_SECURE
    )

    REMEMBER_COOKIE_DURATION = timedelta(
        days=30
    )
