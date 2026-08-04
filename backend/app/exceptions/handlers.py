import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.base import AppException
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
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(message="An unexpected error occurred.").model_dump(),
        )
