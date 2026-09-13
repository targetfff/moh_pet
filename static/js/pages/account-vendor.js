(function () {
  const form = document.getElementById(
    "vendor_change"
  );

  if (!form) {
    return;
  }

  const titleInput = form.querySelector(
    '[name="new_title"]'
  );

  const logoInput = form.querySelector(
    '[name="new_logo"]'
  );

  const submitButton = form.querySelector(
    'button[type="submit"]'
  );

  const initialTitle = (
    titleInput?.value || ""
  ).trim();

  function hasChanges() {
    const currentTitle = (
      titleInput?.value || ""
    ).trim();

    const hasNewLogo = Boolean(
      logoInput?.files?.length
    );

    return (
      currentTitle !== initialTitle
      || hasNewLogo
    );
  }

  function updateSubmitState() {
    if (submitButton) {
      submitButton.disabled =
        !hasChanges();
    }
  }

  titleInput?.addEventListener(
    "input",
    updateSubmitState
  );

  logoInput?.addEventListener(
    "change",
    updateSubmitState
  );

  form.addEventListener(
    "submit",
    (event) => {
      if (!hasChanges()) {
        event.preventDefault();
      }
    }
  );

  updateSubmitState();
})();
