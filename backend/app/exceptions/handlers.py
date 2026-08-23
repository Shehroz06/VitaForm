import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.exceptions.base import AppException
from app.middleware.request_id import REQUEST_ID_HEADER
from app.middleware.security_headers import security_headers
from app.schemas.response import ErrorDetail, ErrorResponse

logger = logging.getLogger("app.errors")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(message=exc.message, errors=exc.errors).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            ErrorDetail(field=".".join(str(loc) for loc in err["loc"]), message=err["msg"])
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(message="Validation failed.", errors=errors).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Reads from request.state, not the request_id_var contextvar: a
        # contextvar set before an exception is raised deep in the route
        # doesn't reliably survive propagation up through FastAPI/
        # Starlette's nested exception-handling wrappers (confirmed by
        # direct testing -- the var was present in the route and absent by
        # the time this handler ran, despite no task boundary in between).
        # request.state is backed by a plain dict on the ASGI scope, so
        # it's immune to that: RequestIdMiddleware writes into the same
        # scope["state"] dict this Request was built from.
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled exception on %s", request.url.path)
        response = JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message="An unexpected error occurred.", request_id=request_id
            ).model_dump(),
        )
        # Set directly rather than relying on RequestIdMiddleware/
        # SecurityHeadersMiddleware's own header injection: confirmed by
        # testing that responses built for this specific catch-all
        # Exception handler (unlike AppException's) don't reliably pass
        # back through those middlewares' header-mutating send wrapper.
        if request_id is not None:
            response.headers[REQUEST_ID_HEADER] = request_id
        settings = get_settings()
        for key, value in security_headers(secure=settings.environment == "production").items():
            response.headers[key] = value
        return response
