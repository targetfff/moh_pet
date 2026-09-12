import random
import time

from flask import current_app, render_template, request, session
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.extensions import db
from app.models import (
    Advertisement,
    Categories,
    Offers,
    Products,
    Vendors,
    product_categories,
)

from . import catalog_bp
from .utils import chunks


CATALOG_PAGE_SIZE = 12


def _liked_product_ids():
    """Возвращает id товаров из корзины текущего пользователя."""
    if (
        not current_user.is_authenticated
        or not current_user.cart
    ):
        return []

    liked = []

    for item in current_user.cart.strip(", ").split(", "):
        parts = item.split()

        if not parts:
            continue

        try:
            liked.append(int(parts[0]))
        except (TypeError, ValueError):
            continue

    return liked


def _parse_vendor_ids():
    """
    GET-параметр vendor может присутствовать несколько раз:

        ?vendor=1&vendor=5

    Возвращаем уникальные положительные id.
    """
    vendor_ids = []

    for raw_value in request.args.getlist("vendor"):
        try:
            vendor_id = int(raw_value)
        except (TypeError, ValueError):
            continue

        if vendor_id > 0:
            vendor_ids.append(vendor_id)

    return list(dict.fromkeys(vendor_ids))


def _catalog_filters():
    """Читает и нормализует фильтры каталога из query string."""
    category_id = request.args.get(
        "category",
        type=int,
    )

    if category_id is not None and category_id <= 0:
        category_id = None

    min_price = request.args.get(
        "min_price",
        type=float,
    )

    max_price = request.args.get(
        "max_price",
        type=float,
    )

    if min_price is not None:
        min_price = max(0.0, min_price)

    if max_price is not None:
        max_price = max(0.0, max_price)

    return {
        "category_id": category_id,
        "vendor_ids": _parse_vendor_ids(),
        "min_price": min_price,
        "max_price": max_price,
    }


def _category_descendants_cte(category_id):
    """
    Recursive CTE: выбранная категория + все её потомки.

    Это часть ТОГО ЖЕ SQL-запроса, который получает товары.
    Отдельного SELECT к Categories больше нет.
    """
    descendants = (
        select(
            Categories.id.label("id")
        )
        .where(
            Categories.id == category_id
        )
        .cte(
            "category_descendants",
            recursive=True,
        )
    )

    child = aliased(Categories)

    descendants = descendants.union_all(
        select(
            child.id
        ).where(
            child.parent
            == descendants.c.id
        )
    )

    return descendants


def _catalog_products_query(filters):
    """
    Строит SQL-запрос каталога.

    Семантика фильтров совпадает со старой главной:
    - категория: товар содержит выбранную категорию;
    - продавцы: товар продаёт хотя бы один выбранный продавец;
    - цена: фильтруем по Products.price, то есть по отображаемой
      минимальной цене товара.
    """
    query = Products.query

    category_id = filters["category_id"]
    vendor_ids = filters["vendor_ids"]
    min_price = filters["min_price"]
    max_price = filters["max_price"]

    if category_id is not None:
        descendants = (
            _category_descendants_cte(
                category_id
            )
        )

        query = (
            query
            .join(
                product_categories,
                product_categories.c.product_id
                == Products.id,
            )
            .filter(
                product_categories.c.category_id.in_(
                    select(
                        descendants.c.id
                    )
                )
            )
            .distinct()
        )

    if vendor_ids:
        query = (
            query
            .join(
                Offers,
                Offers.product_id == Products.id,
            )
            .filter(
                Offers.vendor_id.in_(vendor_ids)
            )
            .distinct()
        )

    if min_price is not None:
        query = query.filter(
            Products.price >= min_price
        )

    if max_price is not None:
        query = query.filter(
            Products.price <= max_price
        )

    return query.order_by(
        Products.date.desc(),
        Products.id.desc(),
    )


def _load_catalog_page(filters, offset=0):
    """
    Загружаем PAGE_SIZE + 1 строку.

    Отдельный COUNT(*) не нужен:
    13-й товар означает, что после первых 12 есть следующая пачка.
    """
    offset = max(0, offset)

    rows = (
        _catalog_products_query(filters)
        .offset(offset)
        .limit(CATALOG_PAGE_SIZE + 1)
        .all()
    )

    has_more = len(rows) > CATALOG_PAGE_SIZE

    return (
        rows[:CATALOG_PAGE_SIZE],
        has_more,
    )


def _catalog_vendors():
    """
    Только продавцы, у которых существует хотя бы один Offer.

    Один SQL-запрос, без N+1.
    """
    vendors = (
        Vendors.query
        .join(
            Offers,
            Offers.vendor_id == Vendors.id,
        )
        .distinct()
        .all()
    )

    return sorted(
        vendors,
        key=lambda vendor: (
            (vendor.title or "").lower(),
            vendor.name.lower(),
            vendor.surname.lower(),
        ),
    )


def _pick_advertisement():
    """
    Сохраняем существующую логику показа рекламы:
    не чаще AD_INTERVAL_SECONDS и по возможности
    не повторяем предыдущую рекламу.
    """
    ad_interval = current_app.config[
        "AD_INTERVAL_SECONDS"
    ]

    now = time.time()

    last_ad_time = session.get(
        "last_ad_time",
        0,
    )

    if now - last_ad_time < ad_interval:
        return None

    ads = Advertisement.query.all()

    if not ads:
        return None

    last_ad_id = session.get("last_ad_id")

    if (
        len(ads) > 1
        and last_ad_id is not None
    ):
        available_ads = [
            advertisement
            for advertisement in ads
            if advertisement.id != last_ad_id
        ]
    else:
        available_ads = ads

    ad = random.choice(available_ads)

    session["last_ad_time"] = now
    session["last_ad_id"] = ad.id

    return ad


def _category_tree_payload():
    """
    Строит всё дерево категорий из ОДНОГО SQL-запроса.

    Формат:
    [
        {
            "id": 1,
            "title": "Игрушки",
            "children": [...]
        }
    ]
    """
    categories = Categories.query.order_by(
        Categories.title.asc()
    ).all()

    if not categories:
        return []

    ids = {
        category.id
        for category in categories
    }

    children_by_parent = {}

    for category in categories:
        children_by_parent.setdefault(
            category.parent,
            [],
        ).append(category)

    roots = [
        category
        for category in categories
        if (
            category.parent in (None, 0)
            or category.parent not in ids
        )
    ]

    def serialize(category, parents):
        # Защита от случайного цикла в данных.
        if category.id in parents:
            return {
                "id": category.id,
                "title": category.title or "",
                "children": [],
            }

        next_parents = parents | {category.id}

        return {
            "id": category.id,
            "title": category.title or "",
            "children": [
                serialize(child, next_parents)
                for child in children_by_parent.get(
                    category.id,
                    [],
                )
            ],
        }

    return [
        serialize(category, set())
        for category in roots
    ]


@catalog_bp.route("/")
def index():
    filters = _catalog_filters()

    products, has_more = _load_catalog_page(
        filters,
        offset=0,
    )

    vendors = _catalog_vendors()
    liked = _liked_product_ids()
    ad = _pick_advertisement()

    return render_template(
        "index.html",
        data=list(chunks(products, 3)),
        ad=ad,
        vendors=vendors,
        liked=liked,
        has_more=has_more,
    )


@catalog_bp.get("/products/load-more")
def load_more_products():
    """
    AJAX endpoint для:
    - кнопки "Загрузить ещё";
    - смены цены;
    - смены продавца;
    - выбора категории.

    Возвращает готовые карточки, чтобы initial render
    и AJAX использовали один и тот же Jinja partial.
    """
    filters = _catalog_filters()

    offset = request.args.get(
        "offset",
        0,
        type=int,
    )

    if offset is None:
        offset = 0

    products, has_more = _load_catalog_page(
        filters,
        offset=offset,
    )

    html = render_template(
        "catalog/_product_cards.html",
        products=products,
        liked=_liked_product_ids(),
        eager_count=0,
    )

    return {
        "html": html,
        "has_more": has_more,
        "loaded": len(products),
        "next_offset": (
            max(0, offset)
            + len(products)
        ),
    }


@catalog_bp.get("/categories/tree")
def categories_tree():
    """
    Меню категорий загружается только при первом открытии.
    Сам endpoint делает один SELECT по Categories.
    """
    return {
        "categories": _category_tree_payload(),
    }


@catalog_bp.route("/product/<int:id>")
def product(id):
    product = Products.query.filter(
        Products.id == id
    ).first_or_404()

    recent_changed = False
    liked = _liked_product_ids()

    if (
        current_user.is_authenticated
        and current_user.status == "client"
    ):
        recent = current_user.recent

        if recent:
            recent_ids = recent.split()
            product_id = str(id)

            if product_id in recent_ids:
                recent_ids.remove(product_id)

            recent_ids.append(product_id)

            if len(recent_ids) > 14:
                recent_ids.pop(0)

            new_recent = " ".join(recent_ids)

            if new_recent != current_user.recent:
                current_user.recent = new_recent
                recent_changed = True

        else:
            current_user.recent = str(id)
            recent_changed = True

    offers_with_vendors = (
        db.session.query(
            Offers,
            Vendors,
        )
        .join(
            Vendors,
            Vendors.id == Offers.vendor_id,
        )
        .filter(
            Offers.product_id == id
        )
        .order_by(
            Offers.price.asc()
        )
        .all()
    )

    vendors = []
    vendor_prices = {}

    for offer, vendor in offers_with_vendors:
        vendors.append(vendor)
        vendor_prices[vendor.id] = offer.price

    response = render_template(
        "product.html",
        liked=liked,
        product=product,
        vendors=vendors,
        ven_prices=vendor_prices.items(),
    )

    # Commit после render, чтобы SQLAlchemy не протухал
    # product/offers до формирования HTML.
    if recent_changed:
        db.session.commit()

    return response


@catalog_bp.route("/cart")
@login_required
def cart():
    if not current_user.cart:
        return render_template(
            "cart.html",
            total=0,
            prods=[],
            liked=[],
        )

    raw_items = (
        current_user.cart
        .strip(", ")
        .split(", ")
    )

    parsed_items = []
    product_ids = []

    for item in raw_items:
        parts = item.split()

        if len(parts) != 3:
            continue

        try:
            product_id = int(parts[0])
            price = float(parts[1])
            quantity = int(parts[2])
        except (TypeError, ValueError):
            continue

        if price == -1:
            price = 0

        parsed_items.append(
            (
                product_id,
                price,
                quantity,
            )
        )

        product_ids.append(product_id)

    if not product_ids:
        return render_template(
            "cart.html",
            total=0,
            prods=[],
            liked=[],
        )

    products = Products.query.filter(
        Products.id.in_(product_ids)
    ).all()

    products_by_id = {
        product.id: product
        for product in products
    }

    cart_items = []
    total = 0

    for (
        product_id,
        price,
        quantity,
    ) in parsed_items:
        product = products_by_id.get(
            product_id
        )

        if not product:
            continue

        cart_items.append([
            product,
            price,
            quantity,
        ])

        total += (
            price * quantity
            + 3100
        )

    return render_template(
        "cart.html",
        total=total,
        prods=cart_items,
        liked=product_ids,
    )


@catalog_bp.route(
    "/amount",
    methods=["POST"],
)
@login_required
def amount():
    amount_id = request.form.get(
        "amount_id",
        type=int,
    )

    action = request.form.get("action")

    if amount_id is None:
        return {
            "error": "Product id is required"
        }, 400

    if action not in {"plus", "minus"}:
        return {
            "error": "Unknown action"
        }, 400

    if not current_user.cart:
        return {
            "error": "Cart is empty"
        }, 400

    updated_cart = []
    new_quantity = None

    for item in current_user.cart.split(", "):
        parts = item.split()

        if len(parts) != 3:
            continue

        product_id, price, quantity = parts

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        if int(product_id) == amount_id:
            if action == "plus":
                quantity += 1

            elif (
                action == "minus"
                and quantity > 1
            ):
                quantity -= 1

            new_quantity = quantity

        updated_cart.append(
            f"{product_id} {price} {quantity}"
        )

    if new_quantity is None:
        return {
            "error": "Product not found"
        }, 404

    current_user.cart = ", ".join(
        updated_cart
    )

    db.session.commit()

    return {
        "quantity": new_quantity,
    }


@catalog_bp.route(
    "/favorites/toggle",
    methods=["POST"],
)
@login_required
def toggle_favorite():
    product_id = request.form.get(
        "liked_id",
        type=int,
    )

    if product_id is None:
        return {
            "error": "liked_id is required"
        }, 400

    price = request.form.get(
        "liked_price",
        "",
    ).rstrip(" руб.")

    if price and price != "undefined":
        try:
            price = float(price)
        except ValueError:
            price = 0.0
    else:
        price = 0.0

    liked = {}

    if current_user.cart:
        items = (
            current_user.cart
            .strip(", ")
            .split(", ")
        )

        for item in items:
            item_data = item.split()

            if len(item_data) != 3:
                continue

            try:
                liked[int(item_data[0])] = [
                    float(item_data[1]),
                    int(item_data[2]),
                ]
            except (TypeError, ValueError):
                continue

    if product_id not in liked:
        liked[product_id] = [
            price,
            1,
        ]

        is_liked = True

    else:
        liked.pop(product_id)
        is_liked = False

    current_user.cart = ", ".join(
        f"{item_id} {data[0]} {data[1]}"
        for item_id, data in liked.items()
    )

    db.session.commit()

    return {
        "liked": is_liked,
        "cart_count": len(liked),
    }


@catalog_bp.route("/buy/<int:cart_id>")
def buy(cart_id):
    return render_template(
        "buy.html",
        cart_id=cart_id,
    )
