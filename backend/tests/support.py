import re

from httpx import AsyncClient


def extract_token(body: str) -> str:
    match = re.search(r"token=(\S+)", body)
    assert match is not None, f"No token found in email body: {body}"
    return match.group(1)


async def create_verified_user_and_login(
    client: AsyncClient,
    captured_emails: list[dict[str, str]],
    email: str = "user@example.com",
    password: str = "password123",
) -> str:
    """Registers, verifies, and logs in a fresh user. Returns the access token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "first_name": "Test"},
    )
    assert response.status_code == 201

    verification_email = next(e for e in captured_emails if e["to"] == email)
    token = extract_token(verification_email["body"])
    verify_response = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verify_response.status_code == 200

    login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    access_token: str = login_response.json()["data"]["access_token"]
    return access_token


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}
