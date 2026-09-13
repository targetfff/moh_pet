(function () {
  const phone = $("#phone");

  if (!phone.length) {
    return;
  }

  phone.mask("+7 (999) 999-99-99");

  phone.on(
    "click",
    function () {
      const input = this;

      if (
        typeof input.setSelectionRange
          === "function"
      ) {
        input.setSelectionRange(4, 4);
      }
    }
  );
})();
