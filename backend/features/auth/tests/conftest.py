import re

from httpx import AsyncClient


def extract_token(body: str) -> str:
    match = re.search(r"token=(\S+)", body)
    assert match is not None, f"No token found in email body: {body}"
    return match.group(1)


async def register_and_verify_user(
    client: AsyncClient,
    captured_emails: list[dict[str, str]],
    email: str = "user@example.com",
    password: str = "password123",
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "first_name": "Test"},
    )
    assert response.status_code == 201

    verification_email = next(e for e in captured_emails if e["to"] == email)
    token = extract_token(verification_email["body"])

    verify_response = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verify_response.status_code == 200
