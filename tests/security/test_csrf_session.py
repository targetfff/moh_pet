import re


def extract_csrf_token(response):
    html = response.get_data(
        as_text=True
    )

    match = re.search(
        r'name="csrf_token"'
        r'[^>]*'
        r'value="([^"]+)"',
        html,
        re.DOTALL,
    )

    assert match is not None, (
        "CSRF token was not found "
        "in response HTML."
    )

    return match.group(1)


def enable_csrf(app):
    app.config[
        "WTF_CSRF_ENABLED"
    ] = True


def test_post_without_csrf_token_returns_400(
        app,
        client,
):
    enable_csrf(app)

    response = client.post(
        "/login",
        data={
            "email":
                "user@example.com",
            "password":
                "password",
        },
    )

    assert response.status_code == 400


def test_post_with_csrf_token_passes_csrf_check(
        app,
        client,
):
    enable_csrf(app)

    login_page = client.get(
        "/login"
    )

    assert login_page.status_code == 200

    csrf_token = extract_csrf_token(
        login_page
    )

    response = client.post(
        "/login",
        data={
            "email":
                "missing@example.com",
            "password":
                "wrong-password",
            "csrf_token":
                csrf_token,
        },
    )

    # Credentials invalid, but request
    # successfully passed CSRF validation.
    assert response.status_code == 200
    assert response.status_code != 400


def test_get_logout_is_not_allowed(
        client,
):
    response = client.get(
        "/logout"
    )

    assert response.status_code == 405


def test_post_logout_logs_user_out(
        app,
        client,
        make_user,
):
    enable_csrf(app)

    password = (
        "Correct horse battery 42"
    )

    user_id = make_user(
        email="logout@example.com",
        password=password,
        confirmed=True,
    )

    login_page = client.get(
        "/login"
    )

    login_csrf = extract_csrf_token(
        login_page
    )

    login_response = client.post(
        "/login",
        data={
            "email":
                "logout@example.com",
            "password":
                password,
            "csrf_token":
                login_csrf,
        },
        follow_redirects=False,
    )

    assert login_response.status_code == 302

    with client.session_transaction() as session:
        assert session.get(
            "_user_id"
        ) == str(user_id)

    # Получаем новый HTML после login,
    # чтобы использовать актуальный
    # подписанный CSRF token.
    page = client.get("/")

    assert page.status_code == 200

    logout_csrf = extract_csrf_token(
        page
    )

    logout_response = client.post(
        "/logout",
        data={
            "csrf_token":
                logout_csrf,
        },
        follow_redirects=False,
    )

    assert logout_response.status_code == 302

    with client.session_transaction() as session:
        assert "_user_id" not in session


def test_session_cookie_is_httponly_and_lax(
        app,
        client,
):
    enable_csrf(app)

    response = client.get(
        "/login"
    )

    assert response.status_code == 200

    cookie_name = app.config.get(
        "SESSION_COOKIE_NAME",
        "session",
    )

    cookies = (
        response.headers.getlist(
            "Set-Cookie"
        )
    )

    session_cookie = next(
        (
            cookie
            for cookie in cookies
            if cookie.startswith(
            f"{cookie_name}="
        )
        ),
        None,
    )

    assert session_cookie is not None

    assert (
            "HttpOnly"
            in session_cookie
    )

    assert (
            "SameSite=Lax"
            in session_cookie
    )

    # В unit tests мы работаем без HTTPS.
    assert (
            "Secure"
            not in session_cookie
    )