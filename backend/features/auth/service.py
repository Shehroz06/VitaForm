import uuid

from app.config.settings import get_settings
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_opaque_token,
    refresh_token_expiry,
)
from features.auth.exceptions import InvalidOrExpiredTokenError
from features.auth.models import User
from features.auth.repository import AuthRepository
from features.auth.schemas import TokenResponse

settings = get_settings()


class AuthService:
    """Reusable session/token issuance logic shared across the register, login,
    and refresh use cases."""

    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def issue_token_pair(
        self,
        user: User,
        device_info: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        session = await self._repository.create_session(
            user_id=user.id,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self._issue_tokens_for_session(user, session.id)

    async def rotate_refresh_token(self, raw_refresh_token: str) -> TokenResponse:
        token_hash = hash_opaque_token(raw_refresh_token)
        existing_token = await self._repository.get_valid_refresh_token(token_hash)
        if existing_token is None:
            raise InvalidOrExpiredTokenError("Refresh token is invalid or has expired.")

        session = await self._repository.get_active_session(existing_token.session_id)
        if session is None:
            raise InvalidOrExpiredTokenError("Session has been revoked.")

        user = await self._repository.get_user_by_id(existing_token.user_id)
        if user is None:
            raise InvalidOrExpiredTokenError("User no longer exists.")

        await self._repository.revoke_refresh_token(existing_token)
        return await self._issue_tokens_for_session(user, session.id)

    async def _issue_tokens_for_session(self, user: User, session_id: uuid.UUID) -> TokenResponse:
        raw_refresh_token = generate_opaque_token()
        await self._repository.create_refresh_token(
            session_id=session_id,
            user_id=user.id,
            token_hash=hash_opaque_token(raw_refresh_token),
            expires_at=refresh_token_expiry(),
        )
        access_token = create_access_token(user.id, [role.name for role in user.roles])
        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            expires_in=settings.jwt_access_token_expires_minutes * 60,
        )
