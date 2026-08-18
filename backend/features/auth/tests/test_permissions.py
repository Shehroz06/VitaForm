from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from features.auth.models import Role, User
from features.auth.tests.conftest import register_and_verify_user


async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


async def test_me_with_valid_token_returns_current_user(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    await register_and_verify_user(client, captured_emails, "me@example.com")
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": "me@example.com", "password": "password123"}
    )
    access_token = login_response.json()["data"]["access_token"]

    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assert response.json()["data"]["email"] == "me@example.com"


async def test_admin_check_without_admin_role_returns_403(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    await register_and_verify_user(client, captured_emails, "regular@example.com")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "regular@example.com", "password": "password123"},
    )
    access_token = login_response.json()["data"]["access_token"]

    response = await client.get(
        "/api/v1/auth/admin-check", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 403


async def test_admin_check_with_admin_role_returns_200(
    client: AsyncClient, captured_emails: list[dict[str, str]], db_session: AsyncSession
) -> None:
    await register_and_verify_user(client, captured_emails, "admin@example.com")

    user = (
        await db_session.execute(
            select(User)
            .where(User.email == "admin@example.com")
            .options(selectinload(User.roles))
        )
    ).scalar_one()
    admin_role = (await db_session.execute(select(Role).where(Role.name == "admin"))).scalar_one()
    user.roles.append(admin_role)
    await db_session.commit()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "password123"},
    )
    access_token = login_response.json()["data"]["access_token"]

    response = await client.get(
        "/api/v1/auth/admin-check", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200


async def _promote_to_admin(db_session: AsyncSession, email: str) -> None:
    user = (
        await db_session.execute(
            select(User).where(User.email == email).options(selectinload(User.roles))
        )
    ).scalar_one()
    admin_role = (await db_session.execute(select(Role).where(Role.name == "admin"))).scalar_one()
    user.roles.append(admin_role)
    await db_session.commit()


async def test_admin_reset_password_without_admin_role_returns_403(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    await register_and_verify_user(client, captured_emails, "notadmin@example.com")
    await register_and_verify_user(client, captured_emails, "victim1@example.com")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "notadmin@example.com", "password": "password123"},
    )
    access_token = login_response.json()["data"]["access_token"]

    response = await client.post(
        "/api/v1/auth/admin/reset-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"email": "victim1@example.com", "new_password": "newpassword123"},
    )

    assert response.status_code == 403


async def test_admin_reset_password_lets_target_user_log_in_with_new_password(
    client: AsyncClient, captured_emails: list[dict[str, str]], db_session: AsyncSession
) -> None:
    await register_and_verify_user(client, captured_emails, "admin2@example.com")
    await _promote_to_admin(db_session, "admin2@example.com")
    await register_and_verify_user(client, captured_emails, "victim2@example.com")

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin2@example.com", "password": "password123"},
    )
    admin_token = admin_login.json()["data"]["access_token"]

    reset_response = await client.post(
        "/api/v1/auth/admin/reset-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": "victim2@example.com", "new_password": "brandnewpassword123"},
    )
    assert reset_response.status_code == 200
    assert reset_response.json()["data"]["email"] == "victim2@example.com"

    old_password_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "victim2@example.com", "password": "password123"},
    )
    assert old_password_login.status_code == 401

    new_password_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "victim2@example.com", "password": "brandnewpassword123"},
    )
    assert new_password_login.status_code == 200


async def test_admin_reset_password_for_unknown_email_returns_404(
    client: AsyncClient, captured_emails: list[dict[str, str]], db_session: AsyncSession
) -> None:
    await register_and_verify_user(client, captured_emails, "admin3@example.com")
    await _promote_to_admin(db_session, "admin3@example.com")

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin3@example.com", "password": "password123"},
    )
    access_token = login_response.json()["data"]["access_token"]

    response = await client.post(
        "/api/v1/auth/admin/reset-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"email": "nobody@example.com", "new_password": "newpassword123"},
    )

    assert response.status_code == 404
