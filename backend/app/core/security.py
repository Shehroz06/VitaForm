import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import ExpiredSignatureError, JWTError, jwt

from app.config.settings import get_settings

settings = get_settings()
_password_hasher = PasswordHasher()


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class InvalidTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def create_access_token(user_id: uuid.UUID, roles: list[str]) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.jwt_access_token_expires_minutes
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "roles": roles,
        "type": TokenType.ACCESS,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError as exc:
        raise InvalidTokenError("Access token has expired.") from exc
    except JWTError as exc:
        raise InvalidTokenError("Access token is invalid.") from exc

    if payload.get("type") != TokenType.ACCESS:
        raise InvalidTokenError("Token is not an access token.")

    return payload


def generate_opaque_token() -> str:
    """Random token for refresh/reset/verification flows (revocable via hash lookup)."""
    return secrets.token_urlsafe(48)


def hash_opaque_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_token_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expires_days)
