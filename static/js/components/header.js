(function () {
  const header = document.querySelector(".header");

  if (!header) {
    return;
  }

  let previousScroll = window.scrollY;
  let ticking = false;

  function setHeaderHidden(hidden) {
    header.classList.toggle(
      "header_hidden",
      hidden
    );

    document.body.classList.toggle(
      "header-is-hidden",
      hidden
    );
  }

  function forceHeaderVisible() {
    setHeaderHidden(false);
    previousScroll = window.scrollY;
  }

  window.addEventListener(
    "scroll",
    () => {
      if (
        document.body.classList.contains(
          "catalog-menu-open"
        )
      ) {
        forceHeaderVisible();
        return;
      }

      if (ticking) {
        return;
      }

      ticking = true;

      window.requestAnimationFrame(() => {
        if (
          document.body.classList.contains(
            "catalog-menu-open"
          )
        ) {
          forceHeaderVisible();
          ticking = false;
          return;
        }

        const currentScroll = window.scrollY;

        if (
          currentScroll > previousScroll
          && currentScroll > 1
        ) {
          setHeaderHidden(true);
        } else if (
          currentScroll < previousScroll
        ) {
          setHeaderHidden(false);
        }

        previousScroll = currentScroll;
        ticking = false;
      });
    },
    { passive: true }
  );

  window.MOH = window.MOH || {};
  window.MOH.setHeaderHidden = setHeaderHidden;
  window.MOH.forceHeaderVisible = forceHeaderVisible;
})();
