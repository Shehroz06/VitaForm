import uuid

import pytest

from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)


def test_hash_password_produces_verifiable_hash() -> None:
    password = "correct-horse-battery-staple1"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password("correct-password1")

    assert verify_password("wrong-password1", hashed) is False


def test_access_token_round_trip() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id, ["student"])

    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["roles"] == ["student"]
    assert payload["type"] == "access"


def test_decode_access_token_rejects_garbage() -> None:
    with pytest.raises(InvalidTokenError):
        decode_access_token("not-a-real-token")


def test_generate_opaque_token_is_unique_and_hashable() -> None:
    token_a = generate_opaque_token()
    token_b = generate_opaque_token()

    assert token_a != token_b
    assert hash_opaque_token(token_a) == hash_opaque_token(token_a)
    assert hash_opaque_token(token_a) != hash_opaque_token(token_b)
