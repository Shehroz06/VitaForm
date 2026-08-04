from app.schemas.response import ErrorDetail


class AppException(Exception):
    status_code: int = 500

    def __init__(self, message: str, errors: list[ErrorDetail] | None = None) -> None:
        self.message = message
        self.errors = errors or []
        super().__init__(message)


class ValidationException(AppException):
    status_code = 422


class AuthenticationException(AppException):
    status_code = 401


class AuthorizationException(AppException):
    status_code = 403


class ResourceNotFoundException(AppException):
    status_code = 404


class ConflictException(AppException):
    status_code = 409


class BusinessRuleException(AppException):
    status_code = 400
