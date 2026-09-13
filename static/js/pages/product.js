(function () {
  const config = document.getElementById(
    "product-page-config"
  );

  if (!config) {
    return;
  }

  const productId = config.dataset.productId;
  const favoriteUrl = config.dataset.favoriteUrl;
  const cartUrl = config.dataset.cartUrl;

  const mainImage = document.querySelector(
    ".main-image"
  );
  const thumbnails = Array.from(
    document.querySelectorAll(".thumbnail")
  );
  const prevButton = document.querySelector(
    ".prev-button"
  );
  const nextButton = document.querySelector(
    ".next-button"
  );
  const controls = Array.from(
    document.querySelectorAll(".control-button")
  );
  const thumbnailsContainer =
    document.querySelector(
      ".carousel-thumbnails"
    );

  const images = thumbnails.map(
    (thumbnail) => thumbnail.src
  );

  let currentIndex = 0;

  function showImage(index) {
    if (!images.length || !mainImage) {
      return;
    }

    currentIndex = (
      index + images.length
    ) % images.length;

    mainImage.src = images[currentIndex];
  }

  if (images.length) {
    showImage(0);
  }

  if (prevButton) {
    prevButton.addEventListener(
      "click",
      () => showImage(
        currentIndex - 1
      )
    );
  }

  if (nextButton) {
    nextButton.addEventListener(
      "click",
      () => showImage(
        currentIndex + 1
      )
    );
  }

  thumbnails.forEach(
    (thumbnail, index) => {
      thumbnail.addEventListener(
        "click",
        () => showImage(index)
      );
    }
  );

  if (images.length <= 1) {
    controls.forEach(
      (control) => control.classList.add(
        "none"
      )
    );

    if (thumbnailsContainer) {
      thumbnailsContainer.classList.add(
        "none"
      );
    }
  }

  const vendorOptions = Array.from(
    document.querySelectorAll(
      ".product-vendor-option"
    )
  );

  const vendorPrices = new Map(
    Array.from(
      document.querySelectorAll(
        ".product-vendor-price"
      )
    ).map((input) => [
      String(input.dataset.vendorId),
      input.value
    ])
  );

  const selectElement = document.getElementById(
    "example-select"
  );
  const priceElement = document.getElementById(
    "price"
  );

  const options = vendorOptions.map(
    (input) => ({
      value: String(
        input.dataset.vendorId
      ),
      label: input.value
    })
  );

  function updatePrice(vendorId) {
    if (!priceElement) {
      return;
    }

    const price = vendorPrices.get(
      String(vendorId)
    );

    priceElement.textContent = price
      ? `${price} руб.`
      : "";
  }

  if (
    selectElement
    && typeof VirtualSelect !== "undefined"
  ) {
    const selectConfig = {
      ele: "#example-select",
      hasOptionDescription: false,
      options,
      search: true,
      name: "vendor",
      placeholder: "Выберите продавца",
      multiple: false,
      optionsCount: 4,
      optionHeight: "40%",
      hideClearButton: true,
      required: true,
      maxWidth: "80%",
      dropboxWidth: "100%",
      noOptionsText:
        "Для данного товара пока нет продавцов",
      noSearchResultsText:
        "Ничего не найдено",
      searchPlaceholderText: "Поиск..."
    };

    if (options.length) {
      selectConfig.selectedValue =
        options[0].value;
    }

    VirtualSelect.init(selectConfig);

    selectElement.addEventListener(
      "change",
      () => {
        updatePrice(
          selectElement.value
        );
      }
    );

    if (options.length) {
      updatePrice(options[0].value);
    }
  }

  const likeButton = document.getElementById(
    "like"
  );
  const likeText = likeButton
    ? likeButton.querySelector(".span2")
    : null;

  function setLikeText(isLiked) {
    if (!likeText) {
      return;
    }

    likeText.classList.add(
      "opacity_span"
    );

    window.setTimeout(
      () => {
        likeText.textContent = isLiked
          ? "Удалить из избранного"
          : "В избранное";

        likeText.classList.remove(
          "opacity_span"
        );
      },
      200
    );
  }

  if (likeButton) {
    likeButton.addEventListener(
      "click",
      async () => {
        const isLiked = (
          Number(
            likeButton.dataset.liked
          ) === 1
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
                liked_price:
                  priceElement
                    ? priceElement.textContent
                    : "",
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

          const newLiked = Boolean(
            result.liked
          );

          likeButton.dataset.liked =
            newLiked ? "1" : "0";

          setLikeText(newLiked);

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
  }

  const goToCart = document.getElementById(
    "go_to_cart"
  );

  if (goToCart) {
    goToCart.addEventListener(
      "click",
      () => {
        window.location.href = cartUrl;
      }
    );
  }
})();
