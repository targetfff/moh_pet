(function () {
  document.addEventListener(
    "click",
    async (event) => {
      const button = event.target.closest(
        ".admin-request-action"
      );

      if (!button) {
        return;
      }

      const card = button.closest(
        ".grid-item"
      );

      if (!card) {
        return;
      }

      const buttons = Array.from(
        card.querySelectorAll(
          ".admin-request-action"
        )
      );

      buttons.forEach(
        (item) => {
          item.disabled = true;
        }
      );

      try {
          const response =
              await window.MOH.csrfFetch(
          button.dataset.url,
          {
            method: "POST",
            headers: {
              "X-Requested-With":
                "XMLHttpRequest"
            }
          }
        );

        if (!response.ok) {
          throw new Error(
            `HTTP ${response.status}`
          );
        }

        card.classList.add(
          "admin-request-card--removed"
        );

        window.setTimeout(
          () => card.remove(),
          300
        );

      } catch (error) {
        console.error(
          "Admin request error:",
          error
        );

        buttons.forEach(
          (item) => {
            item.disabled = false;
          }
        );
      }
    }
  );
})();
