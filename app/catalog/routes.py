import random
import time
from .utils import chunks

from flask import current_app, render_template, request, session
from flask_login import current_user, login_required

from app.extensions import db
from app.models import (
    Advertisement,
    Categories,
    Offers,
    Products,
    Vendors,
)

from . import catalog_bp
from .utils import chunks, tree_find


@catalog_bp.route("/")
def index():
    prices = Offers.query.with_entities(
        Offers.price
    ).all()

    prices = [
        price[0]
        for price in prices
    ]

    products = Products.query.order_by(
        Products.date.desc()
    ).all()

    # Получаем всех продавцов, у которых есть хотя бы один Offer,
    # одним SQL-запросом вместо запроса на каждого продавца.
    vendors = (
        Vendors.query
        .join(
            Offers,
            Offers.vendor_id == Vendors.id,
            )
        .distinct()
        .all()
    )

    vendors = sorted(
        vendors,
        key=lambda vendor: (
            vendor.title or "",
            vendor.name,
            vendor.surname,
        ),
    )

    # Все категории получаем одним запросом.
    all_categories = Categories.query.all()

    # Строим дерево уже в Python.
    children_by_parent = {}

    for category in all_categories:
        children_by_parent.setdefault(
            category.parent,
            [],
        ).append(category)

    def build_category_tree(parent_id):
        return {
            category: build_category_tree(
                category.id
            )
            for category in children_by_parent.get(
                parent_id,
                [],
            )
        }

    tree = build_category_tree(0)

    if (
            current_user.is_authenticated
            and current_user.cart
    ):
        liked = [
            int(item.split()[0])
            for item in current_user.cart
            .strip(", ")
            .split(", ")
        ]
    else:
        liked = []

    data = list(
        chunks(products, 3)
    )

    # Advertisement
    ad = None

    ad_interval = current_app.config[
        "AD_INTERVAL_SECONDS"
    ]

    now = time.time()

    last_ad_time = session.get(
        "last_ad_time",
        0,
    )

    last_ad_id = session.get(
        "last_ad_id"
    )

    if now - last_ad_time >= ad_interval:
        ads = Advertisement.query.all()

        if ads:
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

            ad = random.choice(
                available_ads
            )

            session["last_ad_time"] = now
            session["last_ad_id"] = ad.id

    return render_template(
        "index.html",
        cats=[],
        data=data,
        ad=ad,
        vendors=vendors,
        tree=tree,
        all_prices=prices,
        liked=liked,
    )


@catalog_bp.route("/product/<int:id>")
def product(id):
    product = Products.query.filter(
        Products.id == id
    ).first_or_404()

    recent_changed = False

    if current_user.is_authenticated:
        if current_user.cart:
            liked = [
                int(item.split()[0])
                for item in current_user.cart
                .strip(", ")
                .split(", ")
            ]
        else:
            liked = []

        if current_user.status == "client":
            recent = current_user.recent

            if recent:
                recent_ids = recent.split()
                product_id = str(id)

                if product_id in recent_ids:
                    recent_ids.remove(product_id)

                recent_ids.append(product_id)

                if len(recent_ids) > 14:
                    recent_ids.pop(0)

                new_recent = " ".join(
                    recent_ids
                )

                if new_recent != current_user.recent:
                    current_user.recent = new_recent
                    recent_changed = True

            else:
                current_user.recent = str(id)
                recent_changed = True

    else:
        liked = []

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
        product_id, price, quantity = item.split()

        product_id = int(product_id)
        price = float(price)
        quantity = int(quantity)

        if price == -1:
            price = 0

        parsed_items.append(
            (
                product_id,
                price,
                quantity,
            )
        )

        product_ids.append(
            product_id
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


@catalog_bp.route("/amount", methods=["POST"])
@login_required
def amount():
    amount_id = request.form.get(
        "amount_id",
        type=int,
    )
    action = request.form.get("action")

    if amount_id is None:
        return {"error": "Product id is required"}, 400

    if action not in {"plus", "minus"}:
        return {"error": "Unknown action"}, 400

    if not current_user.cart:
        return {"error": "Cart is empty"}, 400

    updated_cart = []
    new_quantity = None

    for item in current_user.cart.split(", "):
        product_id, price, quantity = item.split()

        quantity = int(quantity)

        if int(product_id) == amount_id:
            if action == "plus":
                quantity += 1

            elif action == "minus" and quantity > 1:
                quantity -= 1

            new_quantity = quantity

        updated_cart.append(
            f"{product_id} {price} {quantity}"
        )

    if new_quantity is None:
        return {"error": "Product not found"}, 404

    current_user.cart = ", ".join(updated_cart)

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

            liked[int(item_data[0])] = [
                float(item_data[1]),
                int(item_data[2]),
            ]

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


@catalog_bp.route("/get_cat_html", methods=["POST"])
def get_cat_html():
    category_id = int(
        request.form["cat_id"].lstrip("cat")
    )

    categories = Categories.query.filter(
        Categories.parent == category_id
    ).all()

    result = []

    for category in categories:
        children = Categories.query.filter(
            Categories.parent == category.id
        ).all()

        result.append((
            category,
            int(bool(children)),
        ))

    return render_template(
        "get_cat_html.html",
        cats=result,
    )


@catalog_bp.route("/buy/<int:cart_id>")
def buy(cart_id):
    return render_template(
        "buy.html",
        cart_id=cart_id,
    )
