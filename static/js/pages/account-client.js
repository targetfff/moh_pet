(function () {
  const config = document.getElementById(
    "client-account-config"
  );

  if (!config) {
    return;
  }

  const favoriteUrl =
    config.dataset.favoriteUrl;

  const nextButton = document.querySelector(
    ".itc-slider-btn-next"
  );

  if (
    nextButton
    && document.querySelectorAll(
      ".itc-slider-item"
    ).length < 5
  ) {
    nextButton.hidden = true;
  }

  document.addEventListener(
    "click",
    (event) => {
      if (
        event.target.closest(
          ".favorite-toggle, a, button, input"
        )
      ) {
        return;
      }

      const card = event.target.closest(
        ".recent-product-card"
      );

      if (card) {
        window.location.href =
          card.dataset.url;
      }
    }
  );

  document.addEventListener(
    "click",
    async (event) => {
      const toggle = event.target.closest(
        ".favorite-toggle"
      );

      if (!toggle) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();

      const productId =
        toggle.dataset.like;
      const price =
        toggle.dataset.price;
      const isLiked = (
        Number(toggle.dataset.liked) === 1
      );

      try {
        const response = await fetch(
          favoriteUrl,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/x-www-form-urlencoded;charset=UTF-8",
              "X-Requested-With":
                "XMLHttpRequest"
            },
            body: new URLSearchParams({
              liked_id: productId,
              liked_price: price,
              action: isLiked
                ? "dislike"
                : "like"
            })
          }
        );

        if (!response.ok) {
          throw new Error(
            `HTTP ${response.status}`
          );
        }

        const result =
          await response.json();

        toggle.dataset.liked =
          result.liked ? "1" : "0";

        toggle.classList.toggle(
          "is-liked",
          Boolean(result.liked)
        );

        toggle.setAttribute(
          "aria-label",
          result.liked
            ? "Убрать из избранного"
            : "Добавить в избранное"
        );

        toggle.classList.remove("pop");
        void toggle.offsetWidth;
        toggle.classList.add("pop");

        if (
          typeof window.update_cart_badge
            === "function"
        ) {
          window.update_cart_badge(
            result.cart_count
          );
        }

      } catch (error) {
        console.error(
          "Favorite error:",
          error
        );
      }
    }
  );
})();
