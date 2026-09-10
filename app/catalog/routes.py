import random
import time

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
    prices = Offers.query.with_entities(Offers.price).all()
    prices = [price[0] for price in prices]

    products = Products.query.order_by(
        Products.date.desc()
    ).all()

    vendor_ids = Offers.query.with_entities(
        Offers.vendor_id
    ).all()

    vendors = set()

    for vendor_id in vendor_ids:
        vendor = Vendors.query.filter(
            Vendors.id == vendor_id[0]
        ).first()

        if vendor:
            vendors.add(vendor)

    vendors = sorted(
        vendors,
        key=lambda vendor: (
            vendor.title or "",
            vendor.name,
            vendor.surname,
        ),
    )

    all_categories = Categories.query.all()

    parent_categories = Categories.query.filter(
        Categories.parent == 0
    ).all()

    categories = {
        category: []
        for category in parent_categories
    }

    for category in all_categories:
        if category.parent == 0:
            continue

        parent = Categories.query.filter(
            Categories.id == category.parent
        ).first()

        if parent in categories:
            categories[parent].append(category)
        else:
            categories[parent] = [category]

    tree = {}

    for parent, children in categories.items():
        node = tree_find(parent, tree)

        if node:
            node[parent] = {
                child: {}
                for child in children
            }
        else:
            tree[parent] = {
                child: {}
                for child in children
            }

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

    # -------------------------------------------------
    # Advertisement
    # -------------------------------------------------

    ad = None

    ad_interval = current_app.config["AD_INTERVAL_SECONDS"]

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
            # Если реклам несколько, не показываем
            # ту же самую два раза подряд.
            if len(ads) > 1 and last_ad_id is not None:
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
    if current_user.is_authenticated:
        if current_user.cart:
            liked = [
                int(item.split()[0])
                for item in current_user.cart.strip(", ").split(", ")
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

                current_user.recent = " ".join(recent_ids)
            else:
                current_user.recent = str(id)

            db.session.commit()
    else:
        liked = []

    product = Products.query.filter(
        Products.id == id
    ).first_or_404()

    if product.vendors:
        vendor_ids = (
            str(product.vendors)
            .lstrip("[")
            .rstrip("]")
            .split(", ")
        )
    else:
        vendor_ids = []

    vendors = []
    vendor_prices = {}

    for vendor_id in vendor_ids:
        vendor_id = int(vendor_id)

        vendor = Vendors.query.filter(
            Vendors.id == vendor_id
        ).first()

        offer = Offers.query.filter(
            Offers.vendor_id == vendor_id,
            Offers.product_id == id,
        ).first()

        if vendor and offer:
            vendors.append(vendor)
            vendor_prices[vendor_id] = offer.price

    vendors.sort(
        key=lambda vendor: vendor_prices[vendor.id]
    )

    return render_template(
        "product.html",
        liked=liked,
        product=product,
        vendors=vendors,
        ven_prices=vendor_prices.items(),
    )


@catalog_bp.route("/cart")
@login_required
def cart():
    cart_items = []
    total = 0

    if current_user.cart:
        cart_products = current_user.cart.strip(", ").split(", ")

        liked = [
            int(item.split()[0])
            for item in cart_products
        ]

        for item in cart_products:
            product_id, price, amount = item.split()

            price = float(price)

            if price == -1:
                price = 0

            product = Products.query.filter(
                Products.id == int(product_id)
            ).first()

            cart_items.append([
                product,
                price,
                int(amount),
            ])

            total += price * int(amount) + 3100
    else:
        liked = []

    return render_template(
        "cart.html",
        total=total,
        prods=cart_items,
        liked=liked,
    )


@catalog_bp.route("/sticky_cart_span", methods=["GET", "POST"])
def sticky_cart_span():
    if not current_user.is_authenticated:
        return "0"

    if not current_user.cart:
        return "0"

    cart_items = current_user.cart.strip(", ").split(", ")

    return str(len(cart_items))


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


@catalog_bp.route("/favorites/toggle", methods=["POST"])
@login_required
def toggle_favorite():
    product_id = request.form.get(
        "liked_id",
        type=int,
    )

    if product_id is None:
        return {"error": "liked_id is required"}, 400

    price = request.form.get(
        "liked_price",
        "",
    ).rstrip(" руб.")

    if price and price != "undefined":
        price = float(price)
    else:
        price = 0.0

    liked = {}

    if current_user.cart:
        items = current_user.cart.strip(", ").split(", ")

        for item in items:
            item_data = item.split()

            liked[int(item_data[0])] = [
                float(item_data[1]),
                int(item_data[2]),
            ]

    if product_id not in liked:
        liked[product_id] = [price, 1]
    else:
        liked.pop(product_id)

    current_user.cart = ", ".join(
        f"{item_id} {data[0]} {data[1]}"
        for item_id, data in liked.items()
    )

    db.session.commit()

    length = len(liked)

    if length == 0:
        return (
            '<div class="mb-4 cart_title">'
            "Избранное"
            "<small> (нет товаров) </small>"
            "</div>"
        )

    if str(length)[-1] == "1":
        word = "товар"
    else:
        word = "товара(-ов)"

    return (
        '<div class="mb-4 cart_title">'
        f"Избранное<small> ({length} {word}) </small>"
        "</div>"
    )


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
