(function () {
  const config = document.getElementById(
    "cart-page-config"
  );

  if (!config) {
    return;
  }

  const amountUrl = config.dataset.amountUrl;
  const favoriteUrl =
    config.dataset.favoriteUrl;

  function formatMoney(value) {
    return Number(value).toFixed(2);
  }

  function cartRows() {
    return Array.from(
      document.querySelectorAll(
        ".cart_div:not(.not_include)"
      )
    );
  }

  function countTotal() {
    let total = 0;

    cartRows().forEach((product) => {
      const price = Number(
        product.dataset.price
      );

      const quantity = Number(
        product.dataset.quantity
      );

      total += (
        price * quantity
        + 3100
      );
    });

    const target = document.querySelector(
      ".order_total_amount"
    );

    if (target) {
      target.textContent =
        `${formatMoney(total)} руб.`;
    }
  }

  function countProductTotal(product) {
    const price = Number(
      product.dataset.price
    );

    const quantity = Number(
      product.dataset.quantity
    );

    const total = (
      price * quantity
      + 3100
    );

    const target = product.querySelector(
      ".prod_total"
    );

    if (target) {
      target.textContent =
        `${formatMoney(total)} руб.`;
    }
  }

  function updateCartCount(count) {
    let text;

    if (count === 0) {
      text = "нет товаров";

    } else if (
      count % 10 === 1
      && count % 100 !== 11
    ) {
      text = `${count} товар`;

    } else if (
      [2, 3, 4].includes(count % 10)
      && ![12, 13, 14].includes(
        count % 100
      )
    ) {
      text = `${count} товара`;

    } else {
      text = `${count} товаров`;
    }

    const countElement =
      document.getElementById(
        "cart-page-count"
      );

    if (countElement) {
      countElement.textContent = text;
    }
  }

  async function postForm(url, data) {
    const response = await fetch(
      url,
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/x-www-form-urlencoded;charset=UTF-8",
          "X-Requested-With":
            "XMLHttpRequest"
        },
        body: new URLSearchParams(data)
      }
    );

    if (!response.ok) {
      throw new Error(
        `HTTP ${response.status}`
      );
    }

    return response.json();
  }

  document.addEventListener(
    "click",
    async (event) => {
      const quantityButton =
        event.target.closest(
          ".none_plus, .none_minus"
        );

      if (quantityButton) {
        event.preventDefault();

        const product =
          quantityButton.closest(
            ".cart_div"
          );

        if (!product) {
          return;
        }

        const action =
          quantityButton.classList.contains(
            "none_plus"
          )
            ? "plus"
            : "minus";

        try {
          const result = await postForm(
            amountUrl,
            {
              amount_id:
                product.dataset.product,
              action
            }
          );

          const quantity = Number(
            result.quantity
          );

          product.dataset.quantity =
            String(quantity);

          const quantityTarget =
            product.querySelector(
              ".quantity"
            );

          if (quantityTarget) {
            quantityTarget.textContent =
              String(quantity);
          }

          countProductTotal(product);
          countTotal();

        } catch (error) {
          console.error(
            "Amount error:",
            error
          );
        }

        return;
      }

      const removeButton =
        event.target.closest(
          ".cart-remove-button"
        );

      if (!removeButton) {
        return;
      }

      event.preventDefault();

      const product = removeButton.closest(
        ".cart_div"
      );

      if (!product) {
        return;
      }

      try {
        const result = await postForm(
          favoriteUrl,
          {
            liked_id:
              product.dataset.product,
            liked_price: 0,
            action: "dislike"
          }
        );

        updateCartCount(
          result.cart_count
        );

        if (
          typeof window.update_cart_badge
            === "function"
        ) {
          window.update_cart_badge(
            result.cart_count
          );
        }

        product.classList.add(
          "not_include",
          "is-removing"
        );

        countTotal();

        window.setTimeout(
          () => {
            product.remove();
          },
          500
        );

      } catch (error) {
        console.error(
          "Delete error:",
          error
        );
      }
    }
  );
})();
