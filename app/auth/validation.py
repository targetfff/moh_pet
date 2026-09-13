import re

from email_validator import EmailNotValidError, validate_email


COMMON_PASSWORDS = {
    "123456",
    "12345678",
    "111111",
    "qwerty",
    "qwerty123",
    "password",
    "abc123",
}

NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 50
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 60


def normalize_email(value):
    email = (value or "").strip()

    if not email:
        raise ValueError(
            "Укажите адрес электронной почты."
        )

    try:
        result = validate_email(
            email,
            check_deliverability=False,
        )
    except EmailNotValidError as exc:
        raise ValueError(
            "Некорректный адрес электронной почты."
        ) from exc

    return result.normalized.lower()


def normalize_person_name(value, field_label):
    text = " ".join(
        (value or "").strip().split()
    )

    if not (
        NAME_MIN_LENGTH
        <= len(text)
        <= NAME_MAX_LENGTH
    ):
        raise ValueError(
            f"{field_label} должно содержать "
            f"от {NAME_MIN_LENGTH} до "
            f"{NAME_MAX_LENGTH} символов."
        )

    if not all(
        char.isalpha()
        or char in {" ", "-", "'"}
        for char in text
    ):
        raise ValueError(
            f"{field_label} может содержать только "
            "буквы, пробел, дефис и апостроф."
        )

    if (
        not text[0].isalpha()
        or not text[-1].isalpha()
    ):
        raise ValueError(
            f"{field_label} должно начинаться "
            "и заканчиваться буквой."
        )

    if re.search(
        r"[\s\-']{2,}",
        text,
    ):
        raise ValueError(
            f"{field_label} содержит некорректную "
            "последовательность разделителей."
        )

    return text


def normalize_phone(value):
    raw = (value or "").strip()
    digits = "".join(
        char
        for char in raw
        if char.isdigit()
    )

    if len(digits) == 10:
        digits = "7" + digits

    elif (
        len(digits) == 11
        and digits.startswith("8")
    ):
        digits = "7" + digits[1:]

    if (
        len(digits) != 11
        or not digits.startswith("7")
    ):
        raise ValueError(
            "Введите российский номер телефона "
            "в формате +7 (999) 999-99-99."
        )

    return (
        f"+7 ({digits[1:4]}) "
        f"{digits[4:7]}-"
        f"{digits[7:9]}-"
        f"{digits[9:11]}"
    )


def validate_password(
    password,
    *,
    email=None,
    phone=None,
    name=None,
    surname=None,
):
    password = password or ""

    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(
            "Пароль должен содержать не менее "
            f"{PASSWORD_MIN_LENGTH} символов."
        )

    if len(password) > PASSWORD_MAX_LENGTH:
        raise ValueError(
            "Пароль слишком длинный."
        )

    if (
        password != password.strip()
    ):
        raise ValueError(
            "Пароль не должен начинаться "
            "или заканчиваться пробелом."
        )

    folded = password.casefold()

    if folded in COMMON_PASSWORDS:
        raise ValueError(
            "Этот пароль слишком очевидный. "
            "Выберите другой."
        )

    identity_values = set()

    for value in (
        email,
        name,
        surname,
    ):
        if value:
            normalized = str(value).strip().casefold()

            if normalized:
                identity_values.add(
                    normalized
                )

    if email and "@" in email:
        identity_values.add(
            email.split("@", 1)[0]
            .strip()
            .casefold()
        )

    if phone:
        phone_digits = "".join(
            char
            for char in str(phone)
            if char.isdigit()
        )

        if phone_digits:
            identity_values.add(
                phone_digits.casefold()
            )

    comparable_password = "".join(
        char
        for char in folded
        if not char.isspace()
    )

    for identity in identity_values:
        comparable_identity = "".join(
            char
            for char in identity
            if not char.isspace()
        )

        if (
            comparable_identity
            and comparable_password
            == comparable_identity
        ):
            raise ValueError(
                "Пароль не должен совпадать "
                "с вашими персональными данными."
            )

    return password
