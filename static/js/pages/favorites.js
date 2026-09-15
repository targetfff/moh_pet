(function () {
    const config =
        document.getElementById(
            "favorites-page-config"
        );

    if (!config) {
        return;
    }

    const favoriteUrl =
        config.dataset.favoriteUrl;

    const grid =
        document.getElementById(
            "favorites-grid"
        );

    const empty =
        document.getElementById(
            "favorites-empty"
        );

    const countTarget =
        document.getElementById(
            "favorites-page-count"
        );

    async function removeFavorite(
        productId
    ) {
        const response =
            await window.MOH.csrfFetch(
                favoriteUrl,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/x-www-form-urlencoded;charset=UTF-8",

                        "X-Requested-With":
                            "XMLHttpRequest"
                    },

                    body:
                        new URLSearchParams({
                            liked_id:
                            productId,

                            action:
                                "dislike"
                        })
                }
            );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        return response.json();
    }

    function updateEmptyState() {
        const cards =
            grid.querySelectorAll(
                ".product-card"
            );

        if (countTarget) {
            countTarget.textContent =
                String(cards.length);
        }

        if (empty) {
            empty.classList.toggle(
                "d-none",
                cards.length > 0
            );
        }
    }

    document.addEventListener(
        "click",
        async (event) => {
            const toggle =
                event.target.closest(
                    ".favorite-toggle"
                );

            if (toggle) {
                event.preventDefault();
                event.stopPropagation();

                const card =
                    toggle.closest(
                        ".product-card"
                    );

                const productId =
                    toggle.dataset.like;

                if (!card || !productId) {
                    return;
                }

                try {
                    const result =
                        await removeFavorite(
                            productId
                        );

                    if (
                        typeof window
                            .update_favorite_badge
                        === "function"
                    ) {
                        window
                            .update_favorite_badge(
                                result.favorite_count
                            );
                    }

                    card.style.opacity = "0";

                    card.style.transform =
                        "scale(.96)";

                    window.setTimeout(
                        () => {
                            card.remove();

                            updateEmptyState();
                        },
                        200
                    );

                } catch (error) {
                    console.error(
                        "Favorite remove error:",
                        error
                    );
                }

                return;
            }

            const card =
                event.target.closest(
                    ".product-card"
                );

            if (
                card
                && card.dataset.url
            ) {
                window.location.href =
                    card.dataset.url;
            }
        }
    );
})();