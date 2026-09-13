(function () {
  function updateCartBadge(cartCount) {
    const badge = document.getElementById(
      "sticky-cart-badge"
    );
    const text = document.getElementById(
      "sticky_cart_span"
    );

    if (!badge || !text) {
      return;
    }

    const count = Number(cartCount) || 0;

    if (count <= 0) {
      badge.classList.remove("is-visible");
      text.classList.remove("is-double-digit");
      text.textContent = "";
      return;
    }

    badge.classList.add("is-visible");

    if (count > 9) {
      text.textContent = "9+";
      text.classList.add("is-double-digit");
      return;
    }

    text.textContent = String(count);
    text.classList.remove("is-double-digit");
  }

  window.update_cart_badge = updateCartBadge;
  window.MOH = window.MOH || {};
  window.MOH.updateCartBadge = updateCartBadge;
})();
