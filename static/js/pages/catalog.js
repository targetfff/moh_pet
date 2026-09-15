(function () {
  const config = document.getElementById("catalog-page-config");

  if (!config) {
    return;
  }

  const productEndpoint = config.dataset.productsUrl;
  const favoriteEndpoint = config.dataset.favoriteUrl;

  const grid = document.getElementById("product-grid");
  const loadMoreWrap = document.getElementById("load-more-wrap");
  const loadMoreButton = document.getElementById("load-more-button");
  const loading = document.getElementById("catalog-loading");
  const emptyState = document.getElementById("catalog-empty");

  const categoryChip = document.getElementById(
    "catalog-category-chip"
  );
  const clearCategoryButton = document.getElementById(
    "clear-category-button"
  );

  const priceMin = document.getElementById("price-min");
  const priceMax = document.getElementById("price-max");

  const vendorInputs = Array.from(
    document.querySelectorAll(".vendor-filter")
  );

  const resetButton = document.getElementById("filter-reset");

  let activeCategoryId = null;
  let filterTimer = null;
  let requestController = null;

  const initialUrl = new URL(window.location.href);
  const initialCategory = initialUrl.searchParams.get("category");
  const initialMinPrice = initialUrl.searchParams.get("min_price");
  const initialMaxPrice = initialUrl.searchParams.get("max_price");
  const initialVendors = initialUrl.searchParams.getAll("vendor");

  if (initialCategory) {
    activeCategoryId = Number(initialCategory);
  }

  if (initialMinPrice !== null) {
    priceMin.value = initialMinPrice;
  }

  if (initialMaxPrice !== null) {
    priceMax.value = initialMaxPrice;
  }

  if (initialVendors.length) {
    const selected = new Set(
      initialVendors.map(String)
    );

    vendorInputs.forEach((input) => {
      input.checked = selected.has(input.value);
    });
  }

  function setLoading(isLoading) {
    loading.classList.toggle(
      "is-visible",
      isLoading
    );

    if (loadMoreButton) {
      loadMoreButton.disabled = isLoading;
      loadMoreButton.textContent = isLoading
        ? "Загрузка..."
        : "Загрузить ещё";
    }
  }

  function validatePrices() {
    const minValue = priceMin.value.trim();
    const maxValue = priceMax.value.trim();

    const min = minValue === ""
      ? null
      : Number(minValue);

    const max = maxValue === ""
      ? null
      : Number(maxValue);

    const invalid = (
      (min !== null && min < 0)
      || (max !== null && max < 0)
      || (
        min !== null
        && max !== null
        && min > max
      )
    );

    priceMin.classList.toggle(
      "is-invalid",
      invalid
    );

    priceMax.classList.toggle(
      "is-invalid",
      invalid
    );

    return !invalid;
  }

  function selectedVendorIds() {
    return vendorInputs
      .filter((input) => input.checked)
      .map((input) => input.value);
  }

  function buildProductParams(offset) {
    const params = new URLSearchParams();

    params.set("offset", String(offset));

    if (activeCategoryId !== null) {
      params.set(
        "category",
        String(activeCategoryId)
      );
    }

    if (priceMin.value.trim() !== "") {
      params.set(
        "min_price",
        priceMin.value.trim()
      );
    }

    if (priceMax.value.trim() !== "") {
      params.set(
        "max_price",
        priceMax.value.trim()
      );
    }

    selectedVendorIds().forEach((vendorId) => {
      params.append("vendor", vendorId);
    });

    return params;
  }

  function syncUrl() {
    const url = new URL(window.location.href);
    url.search = "";

    if (activeCategoryId !== null) {
      url.searchParams.set(
        "category",
        String(activeCategoryId)
      );
    }

    if (priceMin.value.trim() !== "") {
      url.searchParams.set(
        "min_price",
        priceMin.value.trim()
      );
    }

    if (priceMax.value.trim() !== "") {
      url.searchParams.set(
        "max_price",
        priceMax.value.trim()
      );
    }

    selectedVendorIds().forEach((vendorId) => {
      url.searchParams.append(
        "vendor",
        vendorId
      );
    });

    window.history.replaceState({}, "", url);
  }

  function setHasMore(hasMore) {
    if (loadMoreWrap) {
      loadMoreWrap.hidden = !hasMore;
    }
  }

  function updateEmptyState() {
    const hasCards = Boolean(
      grid.querySelector(".product-card")
    );

    emptyState.classList.toggle(
      "is-visible",
      !hasCards
    );
  }

  async function loadProducts({ append }) {
    if (!validatePrices()) {
      return;
    }

    if (requestController) {
      requestController.abort();
    }

    requestController = new AbortController();

    const offset = append
      ? grid.querySelectorAll(".product-card").length
      : 0;

    const params = buildProductParams(offset);

    setLoading(true);

    try {
      const response = await fetch(
        `${productEndpoint}?${params.toString()}`,
        {
          headers: {
            "X-Requested-With": "XMLHttpRequest"
          },
          signal: requestController.signal
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();

      if (typeof result.html !== "string") {
        throw new Error(
          "Некорректный ответ сервера: нет html."
        );
      }

      if (append) {
        emptyState.insertAdjacentHTML(
          "beforebegin",
          result.html
        );
      } else {
        grid
          .querySelectorAll(".product-card")
          .forEach((card) => card.remove());

        emptyState.insertAdjacentHTML(
          "beforebegin",
          result.html
        );
      }

      setHasMore(Boolean(result.has_more));
      updateEmptyState();
      syncUrl();

    } catch (error) {
      if (error.name !== "AbortError") {
        console.error(
          "Ошибка загрузки каталога:",
          error
        );
      }
    } finally {
      setLoading(false);
    }
  }

  function scheduleFilterReload() {
    clearTimeout(filterTimer);

    filterTimer = setTimeout(
      () => loadProducts({
        append: false
      }),
      350
    );
  }

  priceMin.addEventListener(
    "input",
    scheduleFilterReload
  );

  priceMax.addEventListener(
    "input",
    scheduleFilterReload
  );

  vendorInputs.forEach((input) => {
    input.addEventListener(
      "change",
      () => loadProducts({
        append: false
      })
    );
  });

  if (loadMoreButton) {
    loadMoreButton.addEventListener(
      "click",
      () => loadProducts({
        append: true
      })
    );
  }

  if (clearCategoryButton) {
    clearCategoryButton.addEventListener(
      "click",
      () => {
        activeCategoryId = null;

        if (categoryChip) {
          categoryChip.remove();
        }

        loadProducts({
          append: false
        });
      }
    );
  }

  resetButton.addEventListener(
    "click",
    () => {
      priceMin.value = "";
      priceMax.value = "";

      vendorInputs.forEach((input) => {
        input.checked = false;
      });

      activeCategoryId = null;

      if (categoryChip) {
        categoryChip.remove();
      }

      validatePrices();

      loadProducts({
        append: false
      });
    }
  );

  document.addEventListener(
    "click",
    (event) => {
      if (
        event.target.closest(
          ".favorite-toggle"
        )
      ) {
        return;
      }

      const card = event.target.closest(
        ".product-card"
      );

      if (
        card
        && !event.target.closest(
          "button, a, input, label, select, textarea"
        )
      ) {
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

      const productId = toggle.dataset.like;
      const isLiked = (
        Number(toggle.dataset.liked) === 1
      );

      try {
        const response =
            await window.MOH.csrfFetch(
          favoriteEndpoint,
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

        const result = await response.json();

        if (
            typeof window.update_favorite_badge
            === "function"
        ) {
          window.update_favorite_badge(
              result.favorite_count
          );
        }

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

      } catch (error) {
        console.error(
          "Favorite error:",
          error
        );
      }
    }
  );

  updateEmptyState();

  const adModalTrigger = document.getElementById(
    "ad-modal-trigger"
  );

  if (adModalTrigger) {
    adModalTrigger.click();
  }
})();
