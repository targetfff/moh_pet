import random
import time
from datetime import datetime

from flask import current_app, render_template, request, session
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.extensions import db
from app.models import (
    Advertisement,
    CartItem,
    Categories,
    Offers,
    Products,
    RecentView,
    Vendors,
    product_categories,
)

from . import catalog_bp
from .utils import chunks


CATALOG_PAGE_SIZE = 12
RECENT_LIMIT = 14


def _liked_product_ids():
    if not current_user.is_authenticated:
        return []

    return [
        item.product_id
        for item in current_user.cart_items
    ]


def _parse_vendor_ids():
    vendor_ids = []

    for raw_value in request.args.getlist("vendor"):
        try:
            vendor_id = int(raw_value)
        except (TypeError, ValueError):
            continue

        if vendor_id > 0:
            vendor_ids.append(vendor_id)

    return list(
        dict.fromkeys(vendor_ids)
    )


def _catalog_filters():
    category_id = request.args.get(
        "category",
        type=int,
    )

    if (
        category_id is not None
        and category_id <= 0
    ):
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
        min_price = max(
            0.0,
            min_price,
        )

    if max_price is not None:
        max_price = max(
            0.0,
            max_price,
        )

    return {
        "category_id": category_id,
        "vendor_ids": _parse_vendor_ids(),
        "min_price": min_price,
        "max_price": max_price,
    }


def _category_descendants_cte(
        category_id,
):
    descendants = (
        select(
            Categories.id.label("id")
        )
        .where(
            Categories.id
            == category_id
        )
        .cte(
            "category_descendants",
            recursive=True,
        )
    )

    child = aliased(Categories)

    descendants = (
        descendants.union_all(
            select(
                child.id
            ).where(
                child.parent
                == descendants.c.id
            )
        )
    )

    return descendants


def _catalog_products_query(filters):
    query = Products.query

    category_id = filters[
        "category_id"
    ]
    vendor_ids = filters[
        "vendor_ids"
    ]
    min_price = filters[
        "min_price"
    ]
    max_price = filters[
        "max_price"
    ]

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
                Offers.product_id
                == Products.id,
            )
            .filter(
                Offers.vendor_id.in_(
                    vendor_ids
                )
            )
            .distinct()
        )

    if min_price is not None:
        query = query.filter(
            Products.price
            >= min_price
        )

    if max_price is not None:
        query = query.filter(
            Products.price
            <= max_price
        )

    return query.order_by(
        Products.date.desc(),
        Products.id.desc(),
    )


def _load_catalog_page(
        filters,
        offset=0,
):
    offset = max(
        0,
        offset,
    )

    rows = (
        _catalog_products_query(
            filters
        )
        .offset(offset)
        .limit(
            CATALOG_PAGE_SIZE + 1
        )
        .all()
    )

    has_more = (
        len(rows)
        > CATALOG_PAGE_SIZE
    )

    return (
        rows[:CATALOG_PAGE_SIZE],
        has_more,
    )


def _catalog_vendors():
    vendors = (
        Vendors.query
        .join(
            Offers,
            Offers.vendor_id
            == Vendors.id,
        )
        .distinct()
        .all()
    )

    return sorted(
        vendors,
        key=lambda vendor: (
            (
                vendor.title
                or ""
            ).lower(),
            vendor.name.lower(),
            vendor.surname.lower(),
        ),
    )


def _pick_advertisement():
    ad_interval = (
        current_app.config[
            "AD_INTERVAL_SECONDS"
        ]
    )

    now = time.time()

    last_ad_time = session.get(
        "last_ad_time",
        0,
    )

    if (
        now - last_ad_time
        < ad_interval
    ):
        return None

    ads = Advertisement.query.all()

    if not ads:
        return None

    last_ad_id = session.get(
        "last_ad_id"
    )

    if (
        len(ads) > 1
        and last_ad_id is not None
    ):
        available_ads = [
            advertisement
            for advertisement
            in ads
            if (
                advertisement.id
                != last_ad_id
            )
        ]
    else:
        available_ads = ads

    ad = random.choice(
        available_ads
    )

    session[
        "last_ad_time"
    ] = now

    session[
        "last_ad_id"
    ] = ad.id

    return ad


def _category_tree_payload():
    categories = (
        Categories.query
        .order_by(
            Categories.title.asc()
        )
        .all()
    )

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
            category.parent
            in (None, 0)
            or category.parent
            not in ids
        )
    ]

    def serialize(
            category,
            parents,
    ):
        if category.id in parents:
            return {
                "id": category.id,
                "title": (
                    category.title
                    or ""
                ),
                "children": [],
            }

        next_parents = (
            parents
            | {category.id}
        )

        return {
            "id": category.id,
            "title": (
                category.title
                or ""
            ),
            "children": [
                serialize(
                    child,
                    next_parents,
                )
                for child
                in children_by_parent.get(
                    category.id,
                    [],
                )
            ],
        }

    return [
        serialize(
            category,
            set(),
        )
        for category in roots
    ]


def _record_recent_view(
        product_id,
):
    if (
        not current_user.is_authenticated
        or current_user.status
        != "client"
    ):
        return False

    recent_rows = (
        RecentView.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            RecentView.viewed_at.desc(),
            RecentView.id.desc(),
        )
        .limit(RECENT_LIMIT)
        .all()
    )

    if (
        recent_rows
        and recent_rows[0].product_id
        == product_id
    ):
        # Уже самый свежий товар:
        # порядок истории не меняется,
        # поэтому лишний UPDATE не нужен.
        return False

    now = datetime.now()

    existing = next(
        (
            row
            for row in recent_rows
            if (
                row.product_id
                == product_id
            )
        ),
        None,
    )

    if existing is not None:
        existing.viewed_at = now
        return True

    db.session.add(
        RecentView(
            user_id=current_user.id,
            product_id=product_id,
            viewed_at=now,
        )
    )

    if (
        len(recent_rows)
        >= RECENT_LIMIT
    ):
        db.session.delete(
            recent_rows[-1]
        )

    return True


@catalog_bp.route("/")
def index():
    filters = _catalog_filters()

    products, has_more = (
        _load_catalog_page(
            filters,
            offset=0,
        )
    )

    vendors = _catalog_vendors()
    liked = _liked_product_ids()
    ad = _pick_advertisement()

    selected_category = None

    if filters["category_id"] is not None:
        selected_category = db.session.get(
            Categories,
            filters["category_id"],
        )

    return render_template(
        "catalog/index.html",
        data=list(
            chunks(
                products,
                3,
            )
        ),
        ad=ad,
        vendors=vendors,
        liked=liked,
        has_more=has_more,
        selected_category=selected_category,
    )


@catalog_bp.get(
    "/products/load-more"
)
def load_more_products():
    filters = _catalog_filters()

    offset = request.args.get(
        "offset",
        0,
        type=int,
    )

    if offset is None:
        offset = 0

    products, has_more = (
        _load_catalog_page(
            filters,
            offset=offset,
        )
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
            max(
                0,
                offset,
            )
            + len(products)
        ),
    }


@catalog_bp.get(
    "/categories/tree"
)
def categories_tree():
    return {
        "categories":
            _category_tree_payload(),
    }


@catalog_bp.route(
    "/product/<int:id>"
)
def product(id):
    product = (
        Products.query
        .filter(
            Products.id == id
        )
        .first_or_404()
    )

    liked = _liked_product_ids()

    recent_changed = (
        _record_recent_view(
            product.id
        )
    )

    offers_with_vendors = (
        db.session.query(
            Offers,
            Vendors,
        )
        .join(
            Vendors,
            Vendors.id
            == Offers.vendor_id,
        )
        .filter(
            Offers.product_id
            == id
        )
        .order_by(
            Offers.price.asc()
        )
        .all()
    )

    vendors = []
    vendor_prices = {}

    for (
        offer,
        vendor,
    ) in offers_with_vendors:
        vendors.append(
            vendor
        )

        vendor_prices[
            vendor.id
        ] = offer.price

    response = render_template(
        "catalog/product.html",
        liked=liked,
        product=product,
        vendors=vendors,
        ven_prices=(
            vendor_prices.items()
        ),
    )

    if recent_changed:
        db.session.commit()

    return response


@catalog_bp.route("/cart")
@login_required
def cart():
    items = sorted(
        current_user.cart_items,
        key=lambda item: (
            item.created_at,
            item.id,
        ),
    )

    if not items:
        return render_template(
            "catalog/cart.html",
            total=0.0,
            prods=[],
            liked=[],
        )

    product_ids = [
        item.product_id
        for item in items
    ]

    products = (
        Products.query
        .filter(
            Products.id.in_(
                product_ids
            )
        )
        .all()
    )

    products_by_id = {
        product.id: product
        for product in products
    }

    cart_items = []
    liked = []
    total = 0.0

    for item in items:
        product = (
            products_by_id.get(
                item.product_id
            )
        )

        if product is None:
            continue

        price = item.price

        if price == -1:
            price = 0

        price = round(
            float(price),
            2,
        )

        quantity = max(
            1,
            item.quantity,
        )

        cart_items.append([
            product,
            price,
            quantity,
        ])

        liked.append(
            product.id
        )

        line_total = round(
            price * quantity
            + 3100,
            2,
        )

        total = round(
            total + line_total,
            2,
        )

    return render_template(
        "catalog/cart.html",
        total=total,
        prods=cart_items,
        liked=liked,
    )


@catalog_bp.post("/amount")
@login_required
def amount():
    amount_id = request.form.get(
        "amount_id",
        type=int,
    )

    action = request.form.get(
        "action"
    )

    if amount_id is None:
        return {
            "error":
                "Product id is required"
        }, 400

    if action not in {
        "plus",
        "minus",
    }:
        return {
            "error":
                "Unknown action"
        }, 400

    item = next(
        (
            cart_item
            for cart_item
            in current_user.cart_items
            if (
                cart_item.product_id
                == amount_id
            )
        ),
        None,
    )

    if item is None:
        return {
            "error":
                "Product not found"
        }, 404

    if action == "plus":
        item.quantity += 1

    elif (
        action == "minus"
        and item.quantity > 1
    ):
        item.quantity -= 1

    new_quantity = (
        item.quantity
    )

    db.session.commit()

    return {
        "quantity":
            new_quantity,
    }


@catalog_bp.post(
    "/favorites/toggle"
)
@login_required
def toggle_favorite():
    product_id = request.form.get(
        "liked_id",
        type=int,
    )

    if product_id is None:
        return {
            "error":
                "liked_id is required"
        }, 400

    raw_price = (
        request.form.get(
            "liked_price",
            "",
        )
        .replace(
            "руб.",
            "",
        )
        .strip()
    )

    try:
        price = (
            float(raw_price)
            if (
                raw_price
                and raw_price
                != "undefined"
            )
            else 0.0
        )
    except ValueError:
        price = 0.0

    existing = next(
        (
            item
            for item
            in current_user.cart_items
            if (
                item.product_id
                == product_id
            )
        ),
        None,
    )

    if existing is None:
        item = CartItem(
            product_id=product_id,
            price=price,
            quantity=1,
            created_at=datetime.now(),
        )

        current_user.cart_items.append(
            item
        )

        is_liked = True

    else:
        current_user.cart_items.remove(
            existing
        )

        is_liked = False

    cart_count = len(
        current_user.cart_items
    )

    db.session.commit()

    return {
        "liked": is_liked,
        "cart_count": cart_count,
    }


@catalog_bp.route(
    "/buy/<int:cart_id>"
)
def buy(cart_id):
    return render_template(
        "catalog/buy.html",
        cart_id=cart_id,
    )
