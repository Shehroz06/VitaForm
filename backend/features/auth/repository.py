import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from features.auth.models import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    Role,
    Session,
    User,
)


def _normalize_email(email: str) -> str:
    """Email is case-insensitive in practice everywhere (RFC 5321 leaves
    the local part technically case-sensitive, but no mail provider
    actually enforces that, and every real system -- including this one's
    own login form -- treats "User@Example.com" and "user@example.com" as
    the same address). Normalizing at both write time (create_user) and
    read time (get_user_by_email) is what makes that true here: without
    it, a user who types a different case at login than at signup gets a
    false "invalid credentials", and the "unique" email constraint doesn't
    actually stop two case-variant registrations of the same address."""
    return email.strip().lower()


class AuthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self._db.execute(
            select(User)
            .where(User.email == _normalize_email(email))
            .options(selectinload(User.roles))
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._db.execute(
            select(User).where(User.id == user_id).options(selectinload(User.roles))
        )
        return result.scalar_one_or_none()

    async def get_role_by_name(self, name: str) -> Role | None:
        result = await self._db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password_hash: str,
        first_name: str | None,
        last_name: str | None,
        roles: list[Role],
    ) -> User:
        user = User(
            email=_normalize_email(email),
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            roles=roles,
        )
        self._db.add(user)
        await self._db.flush()
        return user

    async def update_user_name(
        self, user: User, first_name: str | None, last_name: str | None
    ) -> None:
        user.first_name = first_name
        user.last_name = last_name
        await self._db.flush()

    async def update_user_password(self, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        await self._db.flush()

    async def mark_user_email_verified(self, user: User) -> None:
        user.is_email_verified = True
        await self._db.flush()

    async def create_session(
        self,
        user_id: uuid.UUID,
        device_info: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Session:
        session = Session(
            user_id=user_id,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._db.add(session)
        await self._db.flush()
        return session

    async def get_active_session(self, session_id: uuid.UUID) -> Session | None:
        result = await self._db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if session is None or session.revoked_at is not None:
            return None
        return session

    async def revoke_session(self, session: Session) -> None:
        session.revoked_at = datetime.now(UTC)
        await self._db.flush()

    async def revoke_all_sessions_for_user(self, user_id: uuid.UUID) -> None:
        result = await self._db.execute(
            select(Session).where(Session.user_id == user_id, Session.revoked_at.is_(None))
        )
        now = datetime.now(UTC)
        for session in result.scalars():
            session.revoked_at = now
        await self._db.flush()

    async def create_refresh_token(
        self, session_id: uuid.UUID, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        token = RefreshToken(
            session_id=session_id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._db.add(token)
        await self._db.flush()
        return token

    async def get_valid_refresh_token(self, token_hash: str) -> RefreshToken | None:
        result = await self._db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        token = result.scalar_one_or_none()
        if token is None or token.revoked_at is not None:
            return None
        if token.expires_at < datetime.now(UTC):
            return None
        return token

    async def revoke_refresh_token(self, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(UTC)
        await self._db.flush()

    async def create_email_verification_token(
        self, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> EmailVerificationToken:
        token = EmailVerificationToken(
            user_id=user_id, token_hash=token_hash, expires_at=expires_at
        )
        self._db.add(token)
        await self._db.flush()
        return token

    async def get_valid_email_verification_token(
        self, token_hash: str
    ) -> EmailVerificationToken | None:
        result = await self._db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash
            )
        )
        token = result.scalar_one_or_none()
        if token is None or token.used_at is not None:
            return None
        if token.expires_at < datetime.now(UTC):
            return None
        return token

    async def mark_email_verification_token_used(self, token: EmailVerificationToken) -> None:
        token.used_at = datetime.now(UTC)
        await self._db.flush()

    async def create_password_reset_token(
        self, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> PasswordResetToken:
        token = PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self._db.add(token)
        await self._db.flush()
        return token

    async def get_valid_password_reset_token(self, token_hash: str) -> PasswordResetToken | None:
        result = await self._db.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        token = result.scalar_one_or_none()
        if token is None or token.used_at is not None:
            return None
        if token.expires_at < datetime.now(UTC):
            return None
        return token

    async def mark_password_reset_token_used(self, token: PasswordResetToken) -> None:
        token.used_at = datetime.now(UTC)
        await self._db.flush()
