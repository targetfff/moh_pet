(() => {
    window.MOH = window.MOH || {};

    function getCsrfToken() {
        return document
            .querySelector('meta[name="csrf-token"]')
            ?.getAttribute("content") || "";
    }

    function csrfFetch(input, init = {}) {
        const options = {
            ...init
        };

        const method = (
            options.method || "GET"
        ).toUpperCase();

        const unsafeMethods = new Set([
            "POST",
            "PUT",
            "PATCH",
            "DELETE"
        ]);

        if (unsafeMethods.has(method)) {
            const rawUrl = (
                typeof input === "string"
                    ? input
                    : input.url
            );

            const url = new URL(
                rawUrl,
                window.location.href
            );

            if (
                url.origin === window.location.origin
            ) {
                const headers = new Headers(
                    options.headers || {}
                );

                headers.set(
                    "X-CSRFToken",
                    getCsrfToken()
                );

                options.headers = headers;
            }
        }

        return window.fetch(
            input,
            options
        );
    }

    window.MOH.getCsrfToken =
        getCsrfToken;

    window.MOH.csrfFetch =
        csrfFetch;
})();