from httpx import AsyncClient

from tests.support import auth_headers, create_verified_user_and_login

_PNG_CONTENT = b"\x89PNG\r\n\x1a\n" + b"fake-png-bytes"
_PDF_CONTENT = b"%PDF-1.4\n" + b"fake-pdf-bytes"


async def _auth(
    client: AsyncClient, captured_emails: list[dict[str, str]], email: str
) -> dict[str, str]:
    token = await create_verified_user_and_login(client, captured_emails, email)
    return auth_headers(token)


async def test_upload_avatar_sets_profile_avatar_url(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "filesAvatar1@example.com")

    response = await client.post(
        "/api/v1/files/avatar",
        headers=headers,
        files={"file": ("avatar.png", _PNG_CONTENT, "image/png")},
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["purpose"] == "avatar"
    assert body["url"].endswith(f"/files/{body['id']}")

    profile_response = await client.get("/api/v1/profiles/me", headers=headers)
    assert profile_response.json()["data"]["avatar_url"] == body["url"]


async def test_upload_avatar_rejects_disallowed_extension(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "filesAvatar2@example.com")

    response = await client.post(
        "/api/v1/files/avatar",
        headers=headers,
        files={"file": ("avatar.exe", b"not-an-image", "application/octet-stream")},
    )

    assert response.status_code == 422


async def test_upload_avatar_rejects_oversized_file(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "filesAvatar3@example.com")
    oversized = b"0" * (6 * 1024 * 1024)

    response = await client.post(
        "/api/v1/files/avatar",
        headers=headers,
        files={"file": ("avatar.png", oversized, "image/png")},
    )

    assert response.status_code == 422


async def test_replacing_avatar_removes_the_previous_file(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "filesAvatar4@example.com")

    first = await client.post(
        "/api/v1/files/avatar",
        headers=headers,
        files={"file": ("avatar1.png", _PNG_CONTENT, "image/png")},
    )
    first_id = first.json()["data"]["id"]

    second = await client.post(
        "/api/v1/files/avatar",
        headers=headers,
        files={"file": ("avatar2.png", _PNG_CONTENT, "image/png")},
    )
    assert second.status_code == 201

    stale_lookup = await client.get(f"/api/v1/files/{first_id}", headers=headers)
    assert stale_lookup.status_code == 404


async def test_delete_avatar_clears_profile_avatar_url(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "filesAvatar5@example.com")
    await client.post(
        "/api/v1/files/avatar",
        headers=headers,
        files={"file": ("avatar.png", _PNG_CONTENT, "image/png")},
    )

    delete_response = await client.delete("/api/v1/files/avatar", headers=headers)
    assert delete_response.status_code == 204

    profile_response = await client.get("/api/v1/profiles/me", headers=headers)
    assert profile_response.json()["data"]["avatar_url"] is None


async def test_uploaded_file_is_retrievable_by_its_owner_with_correct_bytes(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "filesRetrieve1@example.com")
    upload = await client.post(
        "/api/v1/files/avatar",
        headers=headers,
        files={"file": ("avatar.png", _PNG_CONTENT, "image/png")},
    )
    file_id = upload.json()["data"]["id"]

    retrieve_response = await client.get(f"/api/v1/files/{file_id}", headers=headers)

    assert retrieve_response.status_code == 200
    assert retrieve_response.content == _PNG_CONTENT
    assert retrieve_response.headers["content-type"] == "image/png"


async def test_retrieve_file_without_auth_is_rejected(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "filesRetrieveNoAuth@example.com")
    upload = await client.post(
        "/api/v1/files/avatar",
        headers=headers,
        files={"file": ("avatar.png", _PNG_CONTENT, "image/png")},
    )
    file_id = upload.json()["data"]["id"]

    response = await client.get(f"/api/v1/files/{file_id}")
    assert response.status_code == 401


async def test_retrieve_nonexistent_file_returns_404(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "filesRetrieveMissing@example.com")
    response = await client.get(
        "/api/v1/files/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404


async def test_users_cannot_retrieve_each_others_files(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "filesRetrieveIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "filesRetrieveIsoB@example.com")

    upload = await client.post(
        "/api/v1/files/avatar",
        headers=headers_a,
        files={"file": ("avatar.png", _PNG_CONTENT, "image/png")},
    )
    file_id = upload.json()["data"]["id"]

    response = await client.get(f"/api/v1/files/{file_id}", headers=headers_b)
    assert response.status_code == 404


async def test_users_cannot_delete_each_others_files(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers_a = await _auth(client, captured_emails, "filesIsoA@example.com")
    headers_b = await _auth(client, captured_emails, "filesIsoB@example.com")

    upload = await client.post(
        "/api/v1/files/avatar",
        headers=headers_a,
        files={"file": ("avatar.png", _PNG_CONTENT, "image/png")},
    )
    file_id = upload.json()["data"]["id"]

    response = await client.delete(f"/api/v1/files/{file_id}", headers=headers_b)
    assert response.status_code == 404


async def test_certification_attachment_upload_and_delete_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "filesCert1@example.com")
    cert_response = await client.post(
        "/api/v1/certifications",
        headers=headers,
        json={"name": "Cert", "issuing_organization": "Org"},
    )
    certification_id = cert_response.json()["data"]["id"]

    upload_response = await client.post(
        f"/api/v1/certifications/{certification_id}/attachment",
        headers=headers,
        files={"file": ("credential.pdf", _PDF_CONTENT, "application/pdf")},
    )
    assert upload_response.status_code == 200
    file_id = upload_response.json()["data"]["file_id"]
    assert file_id is not None

    retrieve_response = await client.get(f"/api/v1/files/{file_id}", headers=headers)
    assert retrieve_response.status_code == 200
    assert retrieve_response.content == _PDF_CONTENT

    delete_response = await client.delete(
        f"/api/v1/certifications/{certification_id}/attachment", headers=headers
    )
    assert delete_response.status_code == 204

    get_response = await client.get(
        f"/api/v1/certifications/{certification_id}", headers=headers
    )
    assert get_response.json()["data"]["file_id"] is None

    stale_lookup = await client.get(f"/api/v1/files/{file_id}", headers=headers)
    assert stale_lookup.status_code == 404


async def test_certification_attachment_rejects_disallowed_extension(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "filesCert2@example.com")
    cert_response = await client.post(
        "/api/v1/certifications",
        headers=headers,
        json={"name": "Cert", "issuing_organization": "Org"},
    )
    certification_id = cert_response.json()["data"]["id"]

    response = await client.post(
        f"/api/v1/certifications/{certification_id}/attachment",
        headers=headers,
        files={"file": ("credential.exe", b"payload", "application/octet-stream")},
    )
    assert response.status_code == 422


async def test_achievement_attachment_upload_and_delete_flow(
    client: AsyncClient, captured_emails: list[dict[str, str]]
) -> None:
    headers = await _auth(client, captured_emails, "filesAch1@example.com")
    achievement_response = await client.post(
        "/api/v1/achievements", headers=headers, json={"title": "Dean's List"}
    )
    achievement_id = achievement_response.json()["data"]["id"]

    upload_response = await client.post(
        f"/api/v1/achievements/{achievement_id}/attachment",
        headers=headers,
        files={"file": ("proof.jpg", _PNG_CONTENT, "image/jpeg")},
    )
    assert upload_response.status_code == 200
    assert upload_response.json()["data"]["file_id"] is not None

    delete_response = await client.delete(
        f"/api/v1/achievements/{achievement_id}/attachment", headers=headers
    )
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/achievements/{achievement_id}", headers=headers)
    assert get_response.json()["data"]["file_id"] is None
