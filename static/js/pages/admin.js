(function () {
  document.addEventListener(
    "submit",
    (event) => {
      const form = event.target.closest(
        "form[data-confirm]"
      );

      if (!form) {
        return;
      }

      const message = form.dataset.confirm;

      if (
        message
        && !window.confirm(message)
      ) {
        event.preventDefault();
      }
    }
  );

  const productFormPage =
    document.querySelector(
      ".admin-product-form-page"
    );

  const suggestionSelect =
    document.getElementById(
      "suggestion_id"
    );

  if (
    productFormPage
    && suggestionSelect
    && productFormPage.dataset.createProductUrl
  ) {
    suggestionSelect.addEventListener(
      "change",
      () => {
        const baseUrl =
          productFormPage.dataset.createProductUrl;

        const suggestionId =
          Number(suggestionSelect.value);

        const url = new URL(
          baseUrl,
          window.location.origin
        );

        if (suggestionId > 0) {
          url.searchParams.set(
            "suggestion_id",
            String(suggestionId)
          );
        }

        window.location.assign(
          url.toString()
        );
      }
    );
  }
})();
