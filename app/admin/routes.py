import ast
from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from sqlalchemy import and_, func

from app.extensions import db
from app.models import (
    Advertisement,
    Categories,
    Offers,
    Products,
    Requests,
    Suggestions,
    Users,
    product_categories,
)

from app.services.catalog import refresh_catalog_product


from app.services.images import (
    ensure_product_thumbnail,
    save_square_image,
)

from . import admin_bp


def is_admin():
    return current_user.status == "admin"


def parse_images(value):
    if not value:
        return []

    try:
        result = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return []

    if not isinstance(result, list):
        return []

    return [
        str(filename)
        for filename in result
        if filename
    ]


def resolve_categories(
        all_categories,
        raw_category_ids,
):
    selected_ids = set()

    for raw_id in raw_category_ids:
        try:
            selected_ids.add(
                int(raw_id)
            )
        except (TypeError, ValueError):
            continue

    return [
        category
        for category in all_categories
        if category.id in selected_ids
    ]


def remove_product_from_user_data(product_id):
    product_id_str = str(product_id)

    for user in Users.query.all():
        if user.cart:
            new_cart = []

            for item in user.cart.strip(", ").split(", "):
                parts = item.split()

                if not parts:
                    continue

                if parts[0] != product_id_str:
                    new_cart.append(item)

            user.cart = ", ".join(new_cart) or None

        if user.recent:
            recent_ids = [
                item
                for item in user.recent.split()
                if item != product_id_str
            ]

            user.recent = " ".join(recent_ids) or None


# ----------------------------------------------------------------------
# Seller request moderation
# ----------------------------------------------------------------------


@admin_bp.post(
    "/admin/trade-requests/<int:request_id>/accept"
)
@login_required
def accept_trade_request(request_id):
    if not is_admin():
        return {
            "error": "Forbidden"
        }, 403

    row = (
        db.session.query(
            Requests,
            Products,
            Offers,
        )
        .outerjoin(
            Products,
            Products.id == Requests.product_id,
            )
        .outerjoin(
            Offers,
            and_(
                Offers.vendor_id
                == Requests.vendor_id,

                Offers.product_id
                == Requests.product_id,
                ),
        )
        .filter(
            Requests.id == request_id
        )
        .first()
    )

    if not row:
        return {
            "error": "Trade request not found"
        }, 404

    trade_request, product, offer = row

    if not product:
        return {
            "error": "Product not found"
        }, 404

    if offer:
        offer.price = (
            trade_request.price
        )

    else:
        offer = Offers(
            vendor_id=trade_request.vendor_id,
            product_id=trade_request.product_id,
            price=trade_request.price,
        )

        db.session.add(
            offer
        )

    db.session.delete(
        trade_request
    )

    refresh_catalog_product(
        product
    )

    db.session.commit()

    return {
        "status": "accepted",
        "request_id": request_id,
    }


@admin_bp.post("/admin/trade-requests/<int:request_id>/reject")
@login_required
def reject_trade_request(request_id):
    if not is_admin():
        return {"error": "Forbidden"}, 403

    trade_request = db.session.get(
        Requests,
        request_id,
    )

    if not trade_request:
        return {
            "error": "Trade request not found"
        }, 404

    db.session.delete(trade_request)
    db.session.commit()

    return {
        "status": "rejected",
        "request_id": request_id,
    }


@admin_bp.post("/admin/product-suggestions/<int:suggestion_id>/accept")
@login_required
def accept_product_suggestion(suggestion_id):
    if not is_admin():
        return {"error": "Forbidden"}, 403

    suggestion = db.session.get(
        Suggestions,
        suggestion_id,
    )

    if not suggestion:
        return {
            "error": "Product suggestion not found"
        }, 404

    suggestion.accepted = True
    db.session.commit()

    return {
        "status": "accepted",
        "suggestion_id": suggestion_id,
    }


@admin_bp.post("/admin/product-suggestions/<int:suggestion_id>/reject")
@login_required
def reject_product_suggestion(suggestion_id):
    if not is_admin():
        return {"error": "Forbidden"}, 403

    suggestion = db.session.get(
        Suggestions,
        suggestion_id,
    )

    if not suggestion:
        return {
            "error": "Product suggestion not found"
        }, 404

    db.session.delete(suggestion)
    db.session.commit()

    return {
        "status": "rejected",
        "suggestion_id": suggestion_id,
    }


# ----------------------------------------------------------------------
# Products CRUD
# ----------------------------------------------------------------------


@admin_bp.get("/admin/products")
@login_required
def products():
    if not is_admin():
        return redirect(
            url_for("catalog.index")
        )

    all_products = Products.query.order_by(
        Products.date.desc()
    ).all()

    approved_suggestions = (
        Suggestions.query
        .filter(Suggestions.accepted.is_(True))
        .order_by(Suggestions.date.desc())
        .all()
    )

    return render_template(
        "admin/products.html",
        products=all_products,
        approved_suggestions=approved_suggestions,
    )


@admin_bp.route(
    "/admin/products/create",
    methods=["GET", "POST"],
)
@login_required
def create_product():
    if not is_admin():
        return redirect(
            url_for("catalog.index")
        )

    categories = Categories.query.order_by(
        Categories.title.asc()
    ).all()

    approved_suggestions = (
        Suggestions.query
        .filter(Suggestions.accepted.is_(True))
        .order_by(Suggestions.date.desc())
        .all()
    )

    selected_suggestion_id = request.args.get(
        "suggestion_id",
        type=int,
    )

    selected_suggestion = None

    if selected_suggestion_id:
        selected_suggestion = db.session.get(
            Suggestions,
            selected_suggestion_id,
        )

        if (
                not selected_suggestion
                or not selected_suggestion.accepted
        ):
            selected_suggestion = None

    if request.method == "GET":
        return render_template(
            "admin/product_form.html",
            mode="create",
            product=None,
            categories=categories,
            selected_categories=[],
            existing_images=[],
            approved_suggestions=approved_suggestions,
            selected_suggestion=selected_suggestion,
        )

    title = request.form.get(
        "title",
        "",
    ).strip()

    description = request.form.get(
        "description",
        "",
    ).strip()

    full_description = request.form.get(
        "full_description",
        "",
    ).strip()

    category_ids = request.form.getlist(
        "categories"
    )

    selected_category_objects = (
        resolve_categories(
            categories,
            category_ids,
        )
    )

    suggestion_id = request.form.get(
        "suggestion_id",
        type=int,
    )

    suggestion = None
    suggestion_images = []

    if suggestion_id:
        suggestion = db.session.get(
            Suggestions,
            suggestion_id,
        )

        if not suggestion or not suggestion.accepted:
            flash(
                "Выбранное предложение не найдено "
                "или ещё не одобрено."
            )

            return redirect(
                url_for("admin.create_product")
            )

        suggestion_images = parse_images(
            suggestion.photos
        )

    if not title:
        flash("Введите название товара.")

        return redirect(
            url_for(
                "admin.create_product",
                suggestion_id=suggestion_id,
            )
        )

    if not description:
        flash("Введите краткое описание товара.")

        return redirect(
            url_for(
                "admin.create_product",
                suggestion_id=suggestion_id,
            )
        )

    uploaded_images = []

    for image in request.files.getlist(
            "images[]"
    ):
        filename = save_square_image(
            image,
            "product",
        )

        if filename:
            uploaded_images.append(
                filename
            )

    new_main_image = save_square_image(
        request.files.get("main_image"),
        "product",
    )

    images = []

    for filename in (
            suggestion_images
            + uploaded_images
    ):
        if filename not in images:
            images.append(filename)

    if new_main_image:
        if new_main_image not in images:
            images.append(new_main_image)

        main_image = new_main_image

    elif suggestion_images:
        main_image = suggestion_images[0]

    elif uploaded_images:
        main_image = uploaded_images[0]

    else:
        flash(
            "Добавьте хотя бы одно изображение товара."
        )

        return redirect(
            url_for(
                "admin.create_product",
                suggestion_id=suggestion_id,
            )
        )

    product = Products(
        title=title,
        vendor=None,
        vendors=None,
        main_logo="",
        logos=None,
        price=-1,
        description=description,
        full_description=full_description,
        images=str(images),
        date=datetime.now(),
        main_image=main_image,
    )

    product.categories = (
        selected_category_objects
    )

    ensure_product_thumbnail(
        main_image
    )

    db.session.add(product)

    if suggestion:
        db.session.delete(suggestion)

    db.session.commit()

    flash("Товар создан.")

    return redirect(
        url_for("admin.products")
    )


@admin_bp.route(
    "/admin/products/<int:product_id>/edit",
    methods=["GET", "POST"],
)
@login_required
def edit_product(product_id):
    if not is_admin():
        return redirect(
            url_for("catalog.index")
        )

    product = db.session.get(
        Products,
        product_id,
    )

    if not product:
        return {
            "error": "Product not found"
        }, 404

    categories = Categories.query.order_by(
        Categories.title.asc()
    ).all()

    existing_images = parse_images(
        product.images
    )

    if (
            product.main_image
            and product.main_image not in existing_images
    ):
        existing_images.insert(
            0,
            product.main_image,
        )

    selected_categories = [
        str(category.id)
        for category in product.categories
    ]

    if request.method == "GET":
        return render_template(
            "admin/product_form.html",
            mode="edit",
            product=product,
            categories=categories,
            selected_categories=selected_categories,
            existing_images=existing_images,
            approved_suggestions=[],
            selected_suggestion=None,
        )

    title = request.form.get(
        "title",
        "",
    ).strip()

    description = request.form.get(
        "description",
        "",
    ).strip()

    full_description = request.form.get(
        "full_description",
        "",
    ).strip()

    category_ids = request.form.getlist(
        "categories"
    )

    selected_category_objects = (
        resolve_categories(
            categories,
            category_ids,
        )
    )

    if not title:
        flash("Введите название товара.")

        return redirect(
            url_for(
                "admin.edit_product",
                product_id=product.id,
            )
        )

    if not description:
        flash("Введите краткое описание товара.")

        return redirect(
            url_for(
                "admin.edit_product",
                product_id=product.id,
            )
        )

    delete_images = set(
        request.form.getlist(
            "delete_images"
        )
    )

    images = [
        filename
        for filename in existing_images
        if filename not in delete_images
    ]

    selected_main_image = request.form.get(
        "main_existing"
    )

    for image in request.files.getlist(
            "images[]"
    ):
        filename = save_square_image(
            image,
            "product",
        )

        if filename and filename not in images:
            images.append(filename)

    new_main_image = save_square_image(
        request.files.get("main_image"),
        "product",
    )

    if new_main_image:
        if new_main_image not in images:
            images.append(new_main_image)

        main_image = new_main_image

    elif (
            selected_main_image
            and selected_main_image in images
    ):
        main_image = selected_main_image

    elif product.main_image in images:
        main_image = product.main_image

    elif images:
        main_image = images[0]

    else:
        flash(
            "У товара должно остаться "
            "хотя бы одно изображение."
        )

        return redirect(
            url_for(
                "admin.edit_product",
                product_id=product.id,
            )
        )

    product.title = title
    product.categories = (
        selected_category_objects
    )
    product.description = description
    product.full_description = full_description
    product.images = str(images)
    product.main_image = main_image

    ensure_product_thumbnail(
        main_image
    )

    db.session.commit()

    flash("Товар обновлён.")

    return redirect(
        url_for("admin.products")
    )


@admin_bp.post(
    "/admin/products/<int:product_id>/delete"
)
@login_required
def delete_product(product_id):
    if not is_admin():
        return {"error": "Forbidden"}, 403

    product = db.session.get(
        Products,
        product_id,
    )

    if not product:
        return {
            "error": "Product not found"
        }, 404

    Offers.query.filter_by(
        product_id=product_id
    ).delete(
        synchronize_session=False
    )

    Requests.query.filter_by(
        product_id=product_id
    ).delete(
        synchronize_session=False
    )

    db.session.execute(
        product_categories.delete().where(
            product_categories.c.product_id
            == product_id
        )
    )

    remove_product_from_user_data(
        product_id
    )

    db.session.delete(product)
    db.session.commit()

    flash("Товар удалён.")

    return redirect(
        url_for("admin.products")
    )


# ----------------------------------------------------------------------
# Categories CRUD
# ----------------------------------------------------------------------


def get_descendant_category_ids(category_id):
    categories = Categories.query.all()

    children = {}

    for category in categories:
        children.setdefault(
            category.parent,
            [],
        ).append(category.id)

    descendants = set()
    stack = list(
        children.get(category_id, [])
    )

    while stack:
        child_id = stack.pop()

        if child_id in descendants:
            continue

        descendants.add(child_id)

        stack.extend(
            children.get(child_id, [])
        )

    return descendants


@admin_bp.get("/admin/categories")
@login_required
def categories():
    if not is_admin():
        return redirect(
            url_for("catalog.index")
        )

    all_categories = Categories.query.order_by(
        Categories.title.asc()
    ).all()

    parent_titles = {
        0: "Корневая категория",
        None: "Корневая категория",
    }

    for category in all_categories:
        parent_titles[category.id] = category.title

    product_counts = {
        category.id: 0
        for category in all_categories
    }

    count_rows = (
        db.session.query(
            product_categories.c.category_id,
            func.count(
                product_categories.c.product_id
            ),
        )
        .group_by(
            product_categories.c.category_id
        )
        .all()
    )

    for category_id, count in count_rows:
        product_counts[category_id] = count

    return render_template(
        "admin/categories.html",
        categories=all_categories,
        parent_titles=parent_titles,
        product_counts=product_counts,
    )


@admin_bp.route(
    "/admin/categories/create",
    methods=["GET", "POST"],
)
@login_required
def create_category():
    if not is_admin():
        return redirect(
            url_for("catalog.index")
        )

    all_categories = Categories.query.order_by(
        Categories.title.asc()
    ).all()

    if request.method == "GET":
        return render_template(
            "admin/category_form.html",
            mode="create",
            category=None,
            categories=all_categories,
        )

    title = request.form.get(
        "title",
        "",
    ).strip()

    parent_id = request.form.get(
        "parent",
        type=int,
    )

    if parent_id is None:
        parent_id = 0

    if not title:
        flash("Введите название категории.")

        return render_template(
            "admin/category_form.html",
            mode="create",
            category=None,
            categories=all_categories,
        )

    if parent_id != 0:
        parent = db.session.get(
            Categories,
            parent_id,
        )

        if not parent:
            flash(
                "Родительская категория не найдена."
            )

            return render_template(
                "admin/category_form.html",
                mode="create",
                category=None,
                categories=all_categories,
            )

    duplicate = Categories.query.filter_by(
        title=title,
        parent=parent_id,
    ).first()

    if duplicate:
        flash(
            "Категория с таким названием "
            "уже существует на этом уровне."
        )

        return render_template(
            "admin/category_form.html",
            mode="create",
            category=None,
            categories=all_categories,
        )

    category = Categories(
        title=title,
        parent=parent_id,
    )

    db.session.add(category)
    db.session.commit()

    flash("Категория создана.")

    return redirect(
        url_for("admin.categories")
    )


@admin_bp.route(
    "/admin/categories/<int:category_id>/edit",
    methods=["GET", "POST"],
)
@login_required
def edit_category(category_id):
    if not is_admin():
        return redirect(
            url_for("catalog.index")
        )

    category = db.session.get(
        Categories,
        category_id,
    )

    if not category:
        return {
            "error": "Category not found"
        }, 404

    all_categories = Categories.query.order_by(
        Categories.title.asc()
    ).all()

    descendants = get_descendant_category_ids(
        category.id
    )

    available_parents = [
        item
        for item in all_categories
        if (
                item.id != category.id
                and item.id not in descendants
        )
    ]

    if request.method == "GET":
        return render_template(
            "admin/category_form.html",
            mode="edit",
            category=category,
            categories=available_parents,
        )

    title = request.form.get(
        "title",
        "",
    ).strip()

    parent_id = request.form.get(
        "parent",
        type=int,
    )

    if parent_id is None:
        parent_id = 0

    if not title:
        flash("Введите название категории.")

        return render_template(
            "admin/category_form.html",
            mode="edit",
            category=category,
            categories=available_parents,
        )

    if (
            parent_id == category.id
            or parent_id in descendants
    ):
        flash(
            "Категорию нельзя вложить "
            "саму в себя или в её подкатегорию."
        )

        return render_template(
            "admin/category_form.html",
            mode="edit",
            category=category,
            categories=available_parents,
        )

    if parent_id != 0:
        parent = db.session.get(
            Categories,
            parent_id,
        )

        if not parent:
            flash(
                "Родительская категория не найдена."
            )

            return render_template(
                "admin/category_form.html",
                mode="edit",
                category=category,
                categories=available_parents,
            )

    duplicate = Categories.query.filter(
        Categories.id != category.id,
        Categories.title == title,
        Categories.parent == parent_id,
        ).first()

    if duplicate:
        flash(
            "Категория с таким названием "
            "уже существует на этом уровне."
        )

        return render_template(
            "admin/category_form.html",
            mode="edit",
            category=category,
            categories=available_parents,
        )

    category.title = title
    category.parent = parent_id

    db.session.commit()

    flash("Категория обновлена.")

    return redirect(
        url_for("admin.categories")
    )


@admin_bp.post(
    "/admin/categories/<int:category_id>/delete"
)
@login_required
def delete_category(category_id):
    if not is_admin():
        return {"error": "Forbidden"}, 403

    category = db.session.get(
        Categories,
        category_id,
    )

    if not category:
        return {
            "error": "Category not found"
        }, 404

    old_parent_id = (
        category.parent
        if category.parent is not None
        else 0
    )

    children = Categories.query.filter_by(
        parent=category.id
    ).all()

    for child in children:
        child.parent = old_parent_id

    db.session.execute(
        product_categories.delete().where(
            product_categories.c.category_id
            == category.id
        )
    )

    db.session.delete(category)
    db.session.commit()

    flash(
        "Категория удалена. "
        "Её подкатегории перенесены уровнем выше."
    )

    return redirect(
        url_for("admin.categories")
    )


# ----------------------------------------------------------------------
# Advertisement CRUD
# ----------------------------------------------------------------------


@admin_bp.get("/admin/ads")
@login_required
def ads():
    if not is_admin():
        return redirect(
            url_for("catalog.index")
        )

    advertisements = Advertisement.query.order_by(
        Advertisement.id.desc()
    ).all()

    return render_template(
        "admin/ads.html",
        ads=advertisements,
    )


@admin_bp.route(
    "/admin/ads/create",
    methods=["GET", "POST"],
)
@login_required
def create_ad():
    if not is_admin():
        return redirect(
            url_for("catalog.index")
        )

    if request.method == "GET":
        return render_template(
            "admin/ad_form.html",
            mode="create",
            ad=None,
        )

    title = request.form.get(
        "title",
        "",
    ).strip()

    media = request.files.get(
        "media"
    )

    if not title:
        flash("Введите название рекламы.")

        return render_template(
            "admin/ad_form.html",
            mode="create",
            ad=None,
        )

    if not media or not media.filename:
        flash("Добавьте изображение или видео.")

        return render_template(
            "admin/ad_form.html",
            mode="create",
            ad=None,
        )

    try:
        from app.services.ads import save_ad_media

        filename, media_type, frame = (
            save_ad_media(media)
        )

    except ValueError as exc:
        flash(str(exc))

        return render_template(
            "admin/ad_form.html",
            mode="create",
            ad=None,
        )

    ad = Advertisement(
        title=title,
        filename=filename,
        format=media_type,
        frame=frame,
    )

    db.session.add(ad)
    db.session.commit()

    flash("Реклама добавлена.")

    return redirect(
        url_for("admin.ads")
    )


@admin_bp.route(
    "/admin/ads/<int:ad_id>/edit",
    methods=["GET", "POST"],
)
@login_required
def edit_ad(ad_id):
    if not is_admin():
        return redirect(
            url_for("catalog.index")
        )

    ad = db.session.get(
        Advertisement,
        ad_id,
    )

    if not ad:
        return {
            "error": "Advertisement not found"
        }, 404

    if request.method == "GET":
        return render_template(
            "admin/ad_form.html",
            mode="edit",
            ad=ad,
        )

    title = request.form.get(
        "title",
        "",
    ).strip()

    if not title:
        flash("Введите название рекламы.")

        return render_template(
            "admin/ad_form.html",
            mode="edit",
            ad=ad,
        )

    old_filename = ad.filename
    old_frame = ad.frame

    media = request.files.get(
        "media"
    )

    if media and media.filename:
        try:
            from app.services.ads import (
                delete_ad_files,
                save_ad_media,
            )

            filename, media_type, frame = (
                save_ad_media(media)
            )

        except ValueError as exc:
            flash(str(exc))

            return render_template(
                "admin/ad_form.html",
                mode="edit",
                ad=ad,
            )

        ad.filename = filename
        ad.format = media_type
        ad.frame = frame

    ad.title = title

    db.session.commit()

    if (
            media
            and media.filename
            and old_filename
    ):
        delete_ad_files(
            old_filename,
            old_frame,
        )

    flash("Реклама обновлена.")

    return redirect(
        url_for("admin.ads")
    )


@admin_bp.post(
    "/admin/ads/<int:ad_id>/delete"
)
@login_required
def delete_ad(ad_id):
    if not is_admin():
        return {"error": "Forbidden"}, 403

    ad = db.session.get(
        Advertisement,
        ad_id,
    )

    if not ad:
        return {
            "error": "Advertisement not found"
        }, 404

    filename = ad.filename
    frame = ad.frame

    db.session.delete(ad)
    db.session.commit()

    from app.services.ads import delete_ad_files

    delete_ad_files(
        filename,
        frame,
    )

    flash("Реклама удалена.")

    return redirect(
        url_for("admin.ads")
    )
