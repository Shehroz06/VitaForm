from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_creating_a_resource_writes_an_audit_log_entry(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "audit1@example.com")

    create_response = await client.post(
        "/api/v1/skills", headers=headers, json={"name": "Python", "category": "technical"}
    )
    skill_id = create_response.json()["data"]["id"]

    log_response = await client.get("/api/v1/audit-log", headers=headers)
    assert log_response.status_code == 200
    entries = log_response.json()["data"]
    matching = [e for e in entries if e["resource_id"] == skill_id]
    assert len(matching) == 1
    assert matching[0]["action"] == "created"
    assert matching[0]["resource_type"] == "skills"


async def test_updating_a_resource_writes_an_updated_entry(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "audit2@example.com")

    create_response = await client.post(
        "/api/v1/awards", headers=headers, json={"title": "Dean's List"}
    )
    award_id = create_response.json()["data"]["id"]

    await client.patch(
        f"/api/v1/awards/{award_id}", headers=headers, json={"title": "Dean's List 2024"}
    )

    log_response = await client.get(
        "/api/v1/audit-log?sort=created_at", headers=headers
    )
    matching = [e for e in log_response.json()["data"] if e["resource_id"] == award_id]
    assert [e["action"] for e in matching] == ["created", "updated"]


async def test_deleting_a_resource_writes_a_deleted_entry_not_updated(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "audit3@example.com")

    create_response = await client.post(
        "/api/v1/awards", headers=headers, json={"title": "Dean's List"}
    )
    award_id = create_response.json()["data"]["id"]

    await client.delete(f"/api/v1/awards/{award_id}", headers=headers)

    log_response = await client.get(
        "/api/v1/audit-log?sort=created_at", headers=headers
    )
    matching = [e for e in log_response.json()["data"] if e["resource_id"] == award_id]
    assert [e["action"] for e in matching] == ["created", "deleted"]


async def test_audit_log_is_isolated_per_profile(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "auditIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "auditIsoB@example.com")

    create_response = await client.post(
        "/api/v1/skills", headers=headers_a, json={"name": "Rust", "category": "technical"}
    )
    skill_id = create_response.json()["data"]["id"]

    log_response = await client.get("/api/v1/audit-log", headers=headers_b)
    resource_ids = [e["resource_id"] for e in log_response.json()["data"]]
    assert skill_id not in resource_ids


async def test_audit_log_rejects_invalid_sort_field(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "auditSortBad@example.com")

    response = await client.get("/api/v1/audit-log?sort=not_a_field", headers=headers)
    assert response.status_code == 422
