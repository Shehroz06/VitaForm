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


class MessageResponse(BaseModel):
    message: str
