(function () {
    function updateFavoriteBadge(
        favoriteCount
    ) {
        const badge =
            document.getElementById(
                "sticky-favorite-badge"
            );

        const text =
            document.getElementById(
                "sticky_favorite_span"
            );

        if (!badge || !text) {
            return;
        }

        const count =
            Number(favoriteCount) || 0;

        if (count <= 0) {
            badge.classList.remove(
                "is-visible"
            );

            text.classList.remove(
                "is-double-digit"
            );

            text.textContent = "";

            return;
        }

        badge.classList.add(
            "is-visible"
        );

        if (count > 9) {
            text.textContent = "9+";

            text.classList.add(
                "is-double-digit"
            );

            return;
        }

        text.textContent =
            String(count);

        text.classList.remove(
            "is-double-digit"
        );
    }

    window.update_favorite_badge =
        updateFavoriteBadge;

    window.MOH =
        window.MOH || {};

    window.MOH.updateFavoriteBadge =
        updateFavoriteBadge;
})();