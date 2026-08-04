from app.exceptions.base import (
    AuthenticationException,
    ConflictException,
    ResourceNotFoundException,
)


class UserAlreadyExistsError(ConflictException):
    def __init__(self) -> None:
        super().__init__("An account with this email already exists.")


class InvalidCredentialsError(AuthenticationException):
    def __init__(self) -> None:
        super().__init__("Invalid email or password.")


class InvalidOrExpiredTokenError(AuthenticationException):
    def __init__(self, message: str = "Token is invalid or has expired.") -> None:
        super().__init__(message)


class UserNotFoundError(ResourceNotFoundException):
    def __init__(self) -> None:
        super().__init__("User not found.")


class EmailNotVerifiedError(AuthenticationException):
    def __init__(self) -> None:
        super().__init__("Please verify your email before logging in.")


class AccountInactiveError(AuthenticationException):
    def __init__(self) -> None:
        super().__init__("This account has been deactivated.")
