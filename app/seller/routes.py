from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import (
    Products,
    Requests,
    Suggestions,
    Vendors,
    Offers,
)
from app.services.catalog import refresh_vendor_products
from app.services.images import save_square_image

from . import seller_bp


def get_current_vendor():
    return Vendors.query.filter_by(
        email=current_user.email
    ).first()


@seller_bp.route(
    "/become_a_seller",
    methods=["GET", "POST"],
)
@login_required
def become_a_seller():
    if current_user.status != "client":
        return redirect(
            url_for("account.account")
        )

    if request.method == "GET":
        return render_template(
            "seller/become_a_seller.html"
        )

    if not request.form.get("user_agreement"):
        flash(
            "Для регистрации продавца необходимо принять условия договора."
        )
        return render_template(
            "seller/become_a_seller.html"
        )

    existing_vendor = Vendors.query.filter_by(
        email=current_user.email
    ).first()

    if existing_vendor:
        flash(
            "Продавец с таким аккаунтом уже существует."
        )
        return redirect(
            url_for("account.account")
        )

    patronymic = request.form.get(
        "patronymic",
        "",
    ).strip()

    title = request.form.get(
        "title",
        "",
    ).strip() or None

    if not patronymic:
        flash("Укажите отчество.")
        return render_template(
            "seller/become_a_seller.html"
        )

    logo = save_square_image(
        request.files.get("logo"),
        "vendor",
    )

    vendor = Vendors(
        surname=current_user.surname,
        name=current_user.name,
        patronymic=patronymic,
        title=title,
        phone=current_user.phone,
        email=current_user.email,
        logo=logo,
    )

    try:
        db.session.add(vendor)
        current_user.status = "vendor"
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        flash(
            "Не удалось зарегистрировать продавца."
        )
        return render_template(
            "seller/become_a_seller.html"
        )

    return redirect(
        url_for("account.account")
    )


@seller_bp.post("/seller/profile")
@login_required
def update_profile():
    if current_user.status != "vendor":
        return redirect(
            url_for("catalog.index")
        )

    vendor = get_current_vendor()

    if not vendor:
        return redirect(
            url_for("catalog.index")
        )

    new_title = request.form.get(
        "new_title",
        "",
    ).strip() or None

    catalog_changed = (
        new_title != vendor.title
    )

    vendor.title = new_title

    new_logo = request.files.get(
        "new_logo"
    )

    if new_logo and new_logo.filename:
        saved_logo = save_square_image(
            new_logo,
            "vendor",
        )

        if saved_logo:
            catalog_changed = (
                catalog_changed
                or saved_logo != vendor.logo
            )

            vendor.logo = saved_logo

    if catalog_changed:
        refresh_vendor_products(
            vendor.id
        )

    db.session.commit()

    return redirect(
        url_for("account.account")
    )


@seller_bp.post("/seller/trade-request")
@login_required
def create_trade_request():
    if current_user.status != "vendor":
        return redirect(
            url_for("catalog.index")
        )

    vendor = get_current_vendor()

    if not vendor:
        return redirect(
            url_for("catalog.index")
        )

    product_id = request.form.get(
        "product_to_request",
        type=int,
    )

    product = db.session.get(
        Products,
        product_id,
    )

    if not product:
        flash("Товар не найден.")

        return redirect(
            url_for("account.account")
        )

    existing_offer = Offers.query.filter_by(
        vendor_id=vendor.id,
        product_id=product.id,
    ).first()

    if existing_offer:
        flash(
            "Вы уже торгуете этим товаром."
        )

        return redirect(
            url_for("account.account")
        )

    existing_request = Requests.query.filter_by(
        vendor_id=vendor.id,
        product_id=product.id,
    ).first()

    if existing_request:
        flash(
            "У вас уже есть заявка "
            "на торговлю этим товаром."
        )

        return redirect(
            url_for("account.account")
        )

    try:
        raw_price = (
            request.form["price"]
            .strip()
            .replace(",", ".")
        )

        price = Decimal(
            raw_price
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    except (
        KeyError,
        InvalidOperation,
    ):
        flash("Некорректная цена.")

        return redirect(
            url_for("account.account")
        )

    if (
        not price.is_finite()
        or price <= Decimal("0.00")
    ):
        flash(
            "Цена должна быть больше нуля."
        )

        return redirect(
            url_for("account.account")
        )

    if price > Decimal("9999999999.99"):
        flash(
            "Указана слишком большая цена."
        )

        return redirect(
            url_for("account.account")
        )

    filenames = []

    for image in request.files.getlist(
            "images[]"
    ):
        filename = save_square_image(
            image,
            "request",
        )

        if filename:
            filenames.append(
                filename
            )

    trade_request = Requests(
        product_id=product.id,
        vendor_id=vendor.id,
        price=price,
        photos=str(filenames),
        date=datetime.now(),
    )

    db.session.add(
        trade_request
    )

    db.session.commit()

    return redirect(
        url_for("account.account")
    )


@seller_bp.post("/seller/product-suggestion")
@login_required
def suggest_product():
    if current_user.status != "vendor":
        return redirect(
            url_for("catalog.index")
        )

    vendor = get_current_vendor()

    if not vendor:
        return redirect(
            url_for("catalog.index")
        )

    title = request.form.get(
        "product_title",
        "",
    ).strip()

    if not title:
        flash("Введите название товара.")
        return redirect(
            url_for("account.account")
        )

    filenames = []

    for image in request.files.getlist("images2[]"):
        filename = save_square_image(
            image,
            "suggest",
        )

        if filename:
            filenames.append(filename)

    suggestion = Suggestions(
        vendor_id=vendor.id,
        title=title,
        photos=str(filenames),
        date=datetime.now(),
        accepted=False,
    )

    db.session.add(suggestion)
    db.session.commit()

    return redirect(
        url_for("account.account")
    )
