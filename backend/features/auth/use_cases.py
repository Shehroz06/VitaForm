from datetime import UTC, datetime, timedelta

from app.config.settings import get_settings
from app.core.email import EmailSender
from app.core.security import (
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from features.auth.exceptions import (
    AccountInactiveError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidOrExpiredTokenError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from features.auth.models import User
from features.auth.repository import AuthRepository
from features.auth.schemas import (
    AdminResetPasswordRequest,
    DeleteAccountRequest,
    ForgotPasswordRequest,
    IssuedTokenPair,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from features.auth.service import AuthService

settings = get_settings()

# A precomputed hash of a value nobody will ever type, verified against on
# login when the email doesn't match a real account -- so that path still
# pays Argon2's cost instead of returning near-instantly, which would
# otherwise let a timing difference reveal whether an email is registered
# (forgot-password already gets this right; login previously didn't).
_DUMMY_PASSWORD_HASH = hash_password("no-such-account-timing-safety-padding")

# Every self-registered user starts as a "student" -- the role constants'
# own description names it as the default (see DEFAULT_ROLES). Recruiter,
# researcher, moderator, and admin are all granted out-of-band, never
# self-selected at signup.
_DEFAULT_REGISTRATION_ROLE = "student"


class RequestContext:
    """Client metadata captured for session/device tracking."""

    def __init__(
        self, ip_address: str | None = None, user_agent: str | None = None
    ) -> None:
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.device_info = user_agent


class RegisterUser:
    def __init__(
        self, repository: AuthRepository, email_sender: EmailSender
    ) -> None:
        self._repository = repository
        self._email_sender = email_sender

    async def execute(self, data: RegisterRequest) -> User:
        existing = await self._repository.get_user_by_email(data.email)
        if existing is not None:
            raise UserAlreadyExistsError

        default_role = await self._repository.get_role_by_name(_DEFAULT_REGISTRATION_ROLE)
        user = await self._repository.create_user(
            email=data.email,
            password_hash=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            roles=[default_role] if default_role is not None else [],
        )

        raw_token = generate_opaque_token()
        expires_at = datetime.now(UTC) + timedelta(
            hours=settings.email_verification_token_expires_hours
        )
        await self._repository.create_email_verification_token(
            user_id=user.id, token_hash=hash_opaque_token(raw_token), expires_at=expires_at
        )
        verify_link = f"{settings.frontend_base_url}/verify-email?token={raw_token}"
        await self._email_sender.send(
            to=user.email,
            subject="Verify your email",
            body=f"Verify your account: {verify_link}",
        )
        return user


class LoginUser:
    def __init__(self, repository: AuthRepository, service: AuthService) -> None:
        self._repository = repository
        self._service = service

    async def execute(
        self, data: LoginRequest, context: RequestContext
    ) -> tuple[User, IssuedTokenPair]:
        user = await self._repository.get_user_by_email(data.email)
        password_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
        password_is_valid = verify_password(data.password, password_hash)
        if user is None or not password_is_valid:
            raise InvalidCredentialsError

        if not user.is_active:
            raise AccountInactiveError

        if not user.is_email_verified:
            raise EmailNotVerifiedError

        tokens = await self._service.issue_token_pair(
            user,
            device_info=context.device_info,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )
        return user, tokens


class RefreshAccessToken:
    def __init__(self, service: AuthService) -> None:
        self._service = service

    async def execute(self, raw_refresh_token: str) -> IssuedTokenPair:
        return await self._service.rotate_refresh_token(raw_refresh_token)


class LogoutUser:
    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def execute(self, raw_refresh_token: str) -> None:
        token_hash = hash_opaque_token(raw_refresh_token)
        token = await self._repository.get_valid_refresh_token(token_hash)
        if token is None:
            return

        await self._repository.revoke_refresh_token(token)
        session = await self._repository.get_active_session(token.session_id)
        if session is not None:
            await self._repository.revoke_session(session)


class VerifyEmail:
    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def execute(self, data: VerifyEmailRequest) -> User:
        token_hash = hash_opaque_token(data.token)
        token = await self._repository.get_valid_email_verification_token(token_hash)
        if token is None:
            raise InvalidOrExpiredTokenError("Verification link is invalid or has expired.")

        user = await self._repository.get_user_by_id(token.user_id)
        if user is None:
            raise InvalidOrExpiredTokenError("User no longer exists.")

        await self._repository.mark_email_verification_token_used(token)
        await self._repository.mark_user_email_verified(user)
        return user


class RequestPasswordReset:
    def __init__(
        self, repository: AuthRepository, email_sender: EmailSender
    ) -> None:
        self._repository = repository
        self._email_sender = email_sender

    async def execute(self, data: ForgotPasswordRequest) -> None:
        user = await self._repository.get_user_by_email(data.email)
        if user is None:
            # Don't reveal whether the email is registered.
            return

        raw_token = generate_opaque_token()
        expires_at = datetime.now(UTC) + timedelta(
            hours=settings.password_reset_token_expires_hours
        )
        await self._repository.create_password_reset_token(
            user_id=user.id, token_hash=hash_opaque_token(raw_token), expires_at=expires_at
        )
        reset_link = f"{settings.frontend_base_url}/reset-password?token={raw_token}"
        await self._email_sender.send(
            to=user.email,
            subject="Reset your password",
            body=f"Reset your password: {reset_link}",
        )


class ResetPassword:
    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def execute(self, data: ResetPasswordRequest) -> None:
        token_hash = hash_opaque_token(data.token)
        token = await self._repository.get_valid_password_reset_token(token_hash)
        if token is None:
            raise InvalidOrExpiredTokenError("Reset link is invalid or has expired.")

        user = await self._repository.get_user_by_id(token.user_id)
        if user is None:
            raise InvalidOrExpiredTokenError("User no longer exists.")

        await self._repository.update_user_password(user, hash_password(data.new_password))
        await self._repository.mark_password_reset_token_used(token)
        await self._repository.revoke_all_sessions_for_user(user.id)


class AdminResetPassword:
    """Sets a user's password directly, on an admin's authority -- no reset
    token, no email round-trip. Same end state as a normal token-based
    reset (new hash, every existing session revoked) minus the token."""

    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def execute(self, data: AdminResetPasswordRequest) -> User:
        user = await self._repository.get_user_by_email(data.email)
        if user is None:
            raise UserNotFoundError

        await self._repository.update_user_password(user, hash_password(data.new_password))
        await self._repository.revoke_all_sessions_for_user(user.id)
        return user


class DeleteAccount:
    """Soft-deletes the calling user's own account. Password-confirmed --
    a bearer token alone shouldn't be enough to trigger something this
    destructive -- and revokes every session so no outstanding access or
    refresh token keeps working past this point."""

    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def execute(self, user: User, data: DeleteAccountRequest) -> None:
        if not verify_password(data.password, user.password_hash):
            raise InvalidCredentialsError

        await self._repository.soft_delete_user(user)
        await self._repository.revoke_all_sessions_for_user(user.id)
