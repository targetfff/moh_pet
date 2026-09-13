(() => {
    const form = document.querySelector(
        "[data-resend-confirmation-form]"
    );

    if (!form) {
        return;
    }

    const button = form.querySelector(
        "[data-resend-confirmation-button]"
    );

    const status = document.querySelector(
        "[data-resend-confirmation-status]"
    );

    if (!button || !status) {
        return;
    }

    const userId =
        form.dataset.userId || "anonymous";

    const storageKey =
        `moh:resend-confirmation:${userId}`;

    const cooldownMs = 60_000;

    let memoryCooldownUntil = 0;
    let timerId = null;

    function getCooldownUntil() {
        try {
            const value =
                window.localStorage.getItem(
                    storageKey
                );

            const parsed = Number(value);

            if (Number.isFinite(parsed)) {
                return parsed;
            }
        } catch (error) {
            // localStorage может быть недоступен.
        }

        return memoryCooldownUntil;
    }

    function setCooldownUntil(value) {
        memoryCooldownUntil = value;

        try {
            window.localStorage.setItem(
                storageKey,
                String(value)
            );
        } catch (error) {
            // Используем fallback в памяти.
        }
    }

    function clearCooldown() {
        memoryCooldownUntil = 0;

        try {
            window.localStorage.removeItem(
                storageKey
            );
        } catch (error) {
            // Ничего страшного.
        }
    }

    function secondsWord(seconds) {
        const mod10 = seconds % 10;
        const mod100 = seconds % 100;

        if (
            mod10 === 1
            && mod100 !== 11
        ) {
            return "секунду";
        }

        if (
            mod10 >= 2
            && mod10 <= 4
            && (
                mod100 < 12
                || mod100 > 14
            )
        ) {
            return "секунды";
        }

        return "секунд";
    }

    function renderCooldown() {
        const cooldownUntil =
            getCooldownUntil();

        const remainingMs =
            cooldownUntil - Date.now();

        if (remainingMs <= 0) {
            clearCooldown();

            button.disabled = false;
            button.removeAttribute(
                "aria-disabled"
            );

            status.hidden = true;
            status.textContent = "";

            if (timerId !== null) {
                window.clearInterval(
                    timerId
                );

                timerId = null;
            }

            return;
        }

        const seconds = Math.ceil(
            remainingMs / 1000
        );

        button.disabled = true;

        button.setAttribute(
            "aria-disabled",
            "true"
        );

        status.hidden = false;

        status.textContent =
            "Повторная отправка будет "
            + `доступна через ${seconds} `
            + secondsWord(seconds);
    }

    function startTimer() {
        renderCooldown();

        if (timerId !== null) {
            return;
        }

        timerId = window.setInterval(
            renderCooldown,
            250
        );
    }

    form.addEventListener(
        "submit",
        () => {
            const cooldownUntil =
                Date.now() + cooldownMs;

            setCooldownUntil(
                cooldownUntil
            );

            startTimer();
        }
    );

    if (getCooldownUntil() > Date.now()) {
        startTimer();
    }
})();
