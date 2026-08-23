from typing import Any

from pydantic import BaseModel


class SuccessResponse[T](BaseModel):
    success: bool = True
    message: str
    data: T
    meta: dict[str, Any] = {}


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: list[ErrorDetail] = []
    # Populated only for unexpected (500) errors -- lets a user quote one
    # id when reporting a problem, and that id is exactly what's attached
    # to the corresponding server-side log line (see RequestIdMiddleware).
    request_id: str | None = None


class MessageResponse(BaseModel):
    message: str
