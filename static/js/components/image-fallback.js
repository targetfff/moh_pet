(function () {
  document.addEventListener(
    "error",
    (event) => {
      const image = event.target;

      if (
        !(image instanceof HTMLImageElement)
        || !image.dataset.fallbackSrc
      ) {
        return;
      }

      const fallbackSrc = image.dataset.fallbackSrc;
      delete image.dataset.fallbackSrc;
      image.src = fallbackSrc;
    },
    true
  );
})();
