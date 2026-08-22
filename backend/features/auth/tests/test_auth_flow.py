from httpx import AsyncClient

from features.auth.tests.conftest import extract_token, register_and_verify_user


async def test_register_returns_created_user(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "password123", "first_name": "New"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "new@example.com"
    assert body["data"]["is_email_verified"] is False
    assert body["data"]["roles"] == []


async def test_register_sends_verification_email(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "verifyme@example.com", "password": "password123"},
    )

    assert len(captured_emails) == 1
    assert captured_emails[0]["to"] == "verifyme@example.com"
    assert "token=" in captured_emails[0]["body"]


async def test_duplicate_registration_returns_409(client: AsyncClient) -> None:
    payload = {"email": "dupe@example.com", "password": "password123"}
    await client.post("/api/v1/auth/register", json=payload)

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409


async def test_weak_password_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={"email": "weak@example.com", "password": "short"}
    )

    assert response.status_code == 422


async def test_login_before_verification_returns_401(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "unverified@example.com", "password": "password123"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "unverified@example.com", "password": "password123"},
    )

    assert response.status_code == 401


async def test_verify_email_with_invalid_token_returns_401(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/verify-email", json={"token": "bogus-token"})

    assert response.status_code == 401


async def test_full_login_flow_returns_token_pair(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    await register_and_verify_user(client, captured_emails, "login@example.com")

    response = await client.post(
        "/api/v1/auth/login", json={"email": "login@example.com", "password": "password123"}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900


async def test_login_with_wrong_password_returns_401(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    await register_and_verify_user(client, captured_emails, "wrongpw@example.com")

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@example.com", "password": "totally-wrong-password"},
    )

    assert response.status_code == 401


async def test_refresh_rotates_token_and_invalidates_old_one(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    await register_and_verify_user(client, captured_emails, "refresh@example.com")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "password123"},
    )
    old_refresh_token = login_response.json()["data"]["refresh_token"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
    )
    assert refresh_response.status_code == 200
    new_refresh_token = refresh_response.json()["data"]["refresh_token"]
    assert new_refresh_token != old_refresh_token

    reuse_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
    )
    assert reuse_response.status_code == 401


async def test_logout_revokes_refresh_token(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    await register_and_verify_user(client, captured_emails, "logout@example.com")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "logout@example.com", "password": "password123"},
    )
    refresh_token = login_response.json()["data"]["refresh_token"]

    logout_response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": refresh_token}
    )
    assert logout_response.status_code == 200

    refresh_after_logout = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_after_logout.status_code == 401


async def test_forgot_and_reset_password_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    await register_and_verify_user(client, captured_emails, "reset@example.com")

    forgot_response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "reset@example.com"}
    )
    assert forgot_response.status_code == 200

    reset_email = next(e for e in captured_emails if "reset-password" in e["body"])
    token = extract_token(reset_email["body"])

    reset_response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "newpassword456"},
    )
    assert reset_response.status_code == 200

    old_password_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset@example.com", "password": "password123"},
    )
    assert old_password_login.status_code == 401

    new_password_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset@example.com", "password": "newpassword456"},
    )
    assert new_password_login.status_code == 200


async def test_forgot_password_for_unknown_email_still_returns_200(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "doesnotexist@example.com"}
    )

    assert response.status_code == 200


async def test_register_normalizes_email_to_lowercase(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "MixedCase@Example.com", "password": "password123"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["email"] == "mixedcase@example.com"


async def test_duplicate_registration_is_case_insensitive(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "CaseDupe@Example.com", "password": "password123"},
    )

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "casedupe@example.com", "password": "password123"},
    )

    assert response.status_code == 409


async def test_login_is_case_insensitive_for_email(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "CaseLogin@Example.com", "password": "password123"},
    )
    assert register_response.status_code == 201

    # The email was normalized to lowercase at registration, so it's what
    # the verification email actually goes to -- confirms the same
    # normalization AuthRepository does isn't just a login-time coincidence.
    verification_email = next(
        e for e in captured_emails if e["to"] == "caselogin@example.com"
    )
    token = extract_token(verification_email["body"])
    verify_response = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verify_response.status_code == 200

    # Logging in with different casing than either the original submission
    # or the stored (lowercase) value must still succeed.
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "CASELOGIN@EXAMPLE.COM", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["access_token"]
